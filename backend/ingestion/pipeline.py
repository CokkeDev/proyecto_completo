"""
IngestionPipeline: orquesta el flujo completo de ingesta.

ETL:
  1. Fetch  → SenadoAPIFetcher
  2. Normalize → ProjectNormalizer
  3. Classify  → HybridClassifier
  4. Chunk     → TextChunker
  5. Encode    → BGEEncoder
  6. Store     → QdrantManager

Soporta re-ejecución idempotente: verifica si el boletín ya existe en Qdrant
antes de reinsertarlo.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.ingestion.fetcher import SenadoAPIFetcher
from backend.ingestion.normalizer import ProjectNormalizer, NormalizedProject
from backend.ingestion.chunker import TextChunker
from backend.classification.hybrid_classifier import HybridClassifier
from backend.classification.models import ClassificationInput
from backend.embeddings.encoder import BGEEncoder
from backend.qdrant.client import QdrantManager

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    fetched: int = 0
    normalized: int = 0
    skipped: int = 0
    classified: int = 0
    encoded: int = 0
    stored: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)


class IngestionPipeline:
    """
    Pipeline completo de ingesta de proyectos de ley.

    Uso:
        pipeline = IngestionPipeline()
        stats = pipeline.run()
    """

    def __init__(
        self,
        fetcher: Optional[SenadoAPIFetcher] = None,
        normalizer: Optional[ProjectNormalizer] = None,
        classifier: Optional[HybridClassifier] = None,
        chunker: Optional[TextChunker] = None,
        encoder: Optional[BGEEncoder] = None,
        qdrant: Optional[QdrantManager] = None,
        batch_size: int = 32,
        skip_existing: bool = True,
    ):
        self.fetcher = fetcher or SenadoAPIFetcher()
        self.normalizer = normalizer or ProjectNormalizer()
        self.classifier = classifier or HybridClassifier()
        self.chunker = chunker or TextChunker()
        self.encoder = encoder or BGEEncoder.get_instance()
        self.qdrant = qdrant or QdrantManager()
        self.batch_size = batch_size
        self.skip_existing = skip_existing

    # ── Pipeline principal ────────────────────────────────────────────────────
    def run(self) -> IngestionStats:
        stats = IngestionStats()
        logger.info("Iniciando pipeline de ingesta...")

        try:
            raw_projects = self.fetcher.fetch_all()
        except Exception as e:
            logger.error(f"Error en fetch: {e}")
            stats.errors += 1
            return stats

        stats.fetched = len(raw_projects)
        logger.info(f"Fetch completado: {stats.fetched} proyectos raw.")

        # Procesar en lotes
        for i in range(0, len(raw_projects), self.batch_size):
            batch_raw = raw_projects[i: i + self.batch_size]
            self._process_batch(batch_raw, stats)
            logger.info(
                f"Progreso: {min(i + self.batch_size, len(raw_projects))}/{stats.fetched} "
                f"| stored={stats.stored} | errors={stats.errors}"
            )

        logger.info(
            f"Pipeline completado: fetched={stats.fetched}, "
            f"classified={stats.classified}, stored={stats.stored}, "
            f"skipped={stats.skipped}, errors={stats.errors}"
        )
        return stats

    # ── Procesamiento de lote ─────────────────────────────────────────────────
    def _process_batch(self, batch_raw: list[dict], stats: IngestionStats):
        # Normalizar
        normalized = self.normalizer.normalize_batch(batch_raw)
        stats.normalized += len(normalized)

        to_process: list[NormalizedProject] = []
        for proj in normalized:
            if not proj.boletin or not proj.suma_clean:
                continue
            if self.skip_existing and self._already_exists(proj.boletin):
                stats.skipped += 1
                continue
            to_process.append(proj)

        if not to_process:
            return

        # Clasificar
        for proj in to_process:
            try:
                inp = ClassificationInput(
                    boletin=proj.boletin,
                    suma=proj.suma_clean,
                    materias="/".join(proj.materias) if proj.materias else None,
                )
                result = self.classifier.classify(inp)
                proj._classification = result
                stats.classified += 1
            except Exception as e:
                logger.error(f"Error clasificando {proj.boletin}: {e}")
                proj._classification = None
                stats.errors += 1

        # Chunking + Encoding + Storage
        for proj in to_process:
            try:
                cls_result = getattr(proj, "_classification", None)
                self._encode_and_store(proj, cls_result, stats)
            except Exception as e:
                logger.error(f"Error procesando {proj.boletin}: {e}")
                stats.error_details.append(f"{proj.boletin}: {e}")
                stats.errors += 1

    def _encode_and_store(self, proj: NormalizedProject, cls_result, stats: IngestionStats):
        chunks = self.chunker.chunk(proj.texto_clasificacion)
        texts = [c.text for c in chunks]
        vectors = self.encoder.encode(texts, batch_size=16)  # (N_chunks, 1024)
        stats.encoded += len(chunks)

        payloads = []
        for idx, chunk in enumerate(chunks):
            payload = self._build_payload(proj, cls_result, chunk.text, idx)
            payloads.append(payload)

        self.qdrant.upsert_batch(
            vectors=list(vectors),
            payloads=payloads,
        )
        stats.stored += len(chunks)

    def _build_payload(self, proj: NormalizedProject, cls_result, chunk_text: str, chunk_idx: int) -> dict:
        base = {
            "id_proyecto": proj.id_proyecto,
            "boletin": proj.boletin,
            "suma": proj.suma,
            "suma_clean": proj.suma_clean,
            "texto_chunk": chunk_text,
            "chunk_index": chunk_idx,
            "fecha_ingreso": proj.fecha_ingreso,
            "year": proj.year,
            "month": proj.month,
            "iniciativa": proj.iniciativa,
            "tipo": proj.tipo,
            "camara_origen": proj.camara_origen,
            "autores": proj.autores,
            "materias_raw": proj.materias,
            "etapa": proj.etapa,
            "link_proyecto": proj.link_proyecto,
            "documento_url": proj.documento_url,
        }

        if cls_result:
            base.update({
                "categoria_principal": cls_result.primary_category,
                "categorias": [cls_result.primary_category],
                "subcategorias": cls_result.subcategories,
                "etiquetas": cls_result.labels,
                "score_clasificacion": cls_result.confidence,
                "origen_clasificacion": cls_result.origin,
                "explicacion": cls_result.explanation,
            })
        else:
            base.update({
                "categoria_principal": "SIN_CLASIFICAR",
                "categorias": [],
                "subcategorias": [],
                "etiquetas": [],
                "score_clasificacion": 0.0,
                "origen_clasificacion": "none",
                "explicacion": "Sin clasificación disponible.",
            })

        return base

    def _already_exists(self, boletin: str) -> bool:
        try:
            results = self.qdrant.get_by_boletin(boletin)
            return len(results) > 0
        except Exception:
            return False
