"""
IngestionPipeline: orquesta el flujo completo de ingesta.

ETL estándar:
  1. Fetch        → SenadoAPIFetcher
  2. Normalize    → ProjectNormalizer
  3. Classify     → ClosedSetClassifier
  4. Chunk        → TextChunker
  5. Encode       → BGEEncoder
  6. Store        → QdrantManager

Modo texto completo (use_full_text=True):
  Entre Normalize y Classify se descarga el PDF del campo DOCUMENTO.
  Si el PDF no está disponible, se cae a SUMA + MATERIAS.

Soporta re-ejecución idempotente: verifica si el boletín ya existe en Qdrant.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.ingestion.fetcher import SenadoAPIFetcher
from backend.ingestion.normalizer import ProjectNormalizer, NormalizedProject
from backend.ingestion.chunker import TextChunker
from backend.classification.closed_set_classifier import ClosedSetClassifier
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
    por_clasificar: int = 0
    encoded: int = 0
    stored: int = 0
    errors: int = 0
    pdf_ok: int = 0
    pdf_failed: int = 0
    error_details: list[str] = field(default_factory=list)


class IngestionPipeline:
    """
    Pipeline completo de ingesta de proyectos de ley.

    Parámetros:
      use_full_text   : descarga el PDF del proyecto para clasificar con texto completo
      limit           : si se especifica, procesa solo los N proyectos más recientes
      skip_existing   : no re-procesa boletines ya en Qdrant
    """

    def __init__(
        self,
        fetcher: Optional[SenadoAPIFetcher] = None,
        normalizer: Optional[ProjectNormalizer] = None,
        chunker: Optional[TextChunker] = None,
        encoder: Optional[BGEEncoder] = None,
        qdrant: Optional[QdrantManager] = None,
        batch_size: int = 32,
        skip_existing: bool = True,
        use_full_text: bool = False,
        limit: Optional[int] = None,
    ):
        self.fetcher = fetcher or SenadoAPIFetcher()
        self.normalizer = normalizer or ProjectNormalizer()
        self.chunker = chunker or TextChunker()
        self.encoder = encoder or BGEEncoder.get_instance()
        self.qdrant = qdrant or QdrantManager()
        self.batch_size = batch_size
        self.skip_existing = skip_existing
        self.use_full_text = use_full_text
        self.limit = limit

        # Clasificador principal del sistema
        self._closed_clf = ClosedSetClassifier()

        if use_full_text:
            from backend.ingestion.document_fetcher import DocumentFetcher
            self._doc_fetcher: Optional[DocumentFetcher] = DocumentFetcher()
        else:
            self._doc_fetcher = None

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

        # Si se solicita un límite, tomar los N más recientes (últimos en la lista)
        if self.limit and self.limit < len(raw_projects):
            raw_projects = raw_projects[-self.limit:]
            logger.info(f"Modo limitado: procesando los últimos {self.limit} proyectos.")

        logger.info(f"Fetch completado: {stats.fetched} proyectos raw, procesando {len(raw_projects)}.")

        for i in range(0, len(raw_projects), self.batch_size):
            batch_raw = raw_projects[i: i + self.batch_size]
            self._process_batch(batch_raw, stats)
            processed = min(i + self.batch_size, len(raw_projects))
            logger.info(
                f"Progreso: {processed}/{len(raw_projects)} "
                f"| stored={stats.stored} | por_clasificar={stats.por_clasificar} | errors={stats.errors}"
            )

        logger.info(
            f"Pipeline completado: fetched={stats.fetched}, classified={stats.classified}, "
            f"por_clasificar={stats.por_clasificar}, stored={stats.stored}, "
            f"pdf_ok={stats.pdf_ok}, pdf_failed={stats.pdf_failed}, "
            f"skipped={stats.skipped}, errors={stats.errors}"
        )
        return stats

    # ── Procesamiento de lote ─────────────────────────────────────────────────

    def _process_batch(self, batch_raw: list[dict], stats: IngestionStats):
        normalized = self.normalizer.normalize_batch(batch_raw)
        stats.normalized += len(normalized)

        to_process: list[tuple[NormalizedProject, Optional[str]]] = []

        for proj in normalized:
            if not proj.boletin or not proj.suma_clean:
                continue
            if self.skip_existing and self._already_exists(proj.boletin):
                stats.skipped += 1
                continue

            # Descarga de documento PDF (opcional)
            doc_text: Optional[str] = None
            if self._doc_fetcher and proj.documento_url:
                doc_text = self._doc_fetcher.fetch_text(proj.documento_url)
                if doc_text:
                    stats.pdf_ok += 1
                    logger.debug(f"PDF descargado para {proj.boletin} ({len(doc_text.split())} palabras)")
                else:
                    stats.pdf_failed += 1
                    logger.debug(f"PDF no disponible para {proj.boletin}, usando SUMA+MATERIAS")

            to_process.append((proj, doc_text))

        if not to_process:
            return

        # Clasificar
        for proj, doc_text in to_process:
            try:
                inp = ClassificationInput(
                    boletin=proj.boletin,
                    suma=proj.suma_clean,
                    materias="/".join(proj.materias) if proj.materias else None,
                )

                closed_result = self._closed_clf.classify(inp, texto_completo=doc_text)
                cls_result = self._closed_clf.to_legacy_result(closed_result)

                # Guardamos ambos resultados para enriquecer el payload
                proj._closed_result = closed_result
                proj._classification = cls_result

                stats.classified += 1

                if closed_result.estado == "POR_CLASIFICAR":
                    stats.por_clasificar += 1

            except Exception as e:
                logger.error(f"Error clasificando {proj.boletin}: {e}")
                proj._classification = None
                proj._closed_result = None
                stats.errors += 1

        # Chunk + Encode + Store
        for proj, doc_text in to_process:
            try:
                # Para los chunks de Qdrant usamos el texto completo si está disponible
                if doc_text:
                    texto_para_chunks = self.normalizer._clean_text(doc_text)
                else:
                    texto_para_chunks = proj.texto_clasificacion
                cls_result = getattr(proj, "_classification", None)
                closed_result = getattr(proj, "_closed_result", None)
                self._encode_and_store(proj, cls_result, closed_result, texto_para_chunks, stats)
            except Exception as e:
                logger.error(f"Error procesando {proj.boletin}: {e}")
                stats.error_details.append(f"{proj.boletin}: {e}")
                stats.errors += 1

    def _encode_and_store(
        self,
        proj: NormalizedProject,
        cls_result,
        closed_result,
        texto_para_chunks: str,
        stats: IngestionStats,
    ):
        # ─────────────────────────────
        # 1. VECTOR DEL PROYECTO
        # ─────────────────────────────
        if texto_para_chunks:
            # usar PDF pero recortado por palabras (no caracteres)
            project_text = " ".join(texto_para_chunks.split()[:1500])
        else:
            # fallback limpio
            project_text = proj.texto_clasificacion

        project_vector = self.encoder.encode([project_text])[0]

        project_payload = self._build_project_payload(
            proj, cls_result, closed_result
        )

        self.qdrant.upsert_project(project_vector, project_payload)

        # ─────────────────────────────
        # 2. CHUNKS (para búsqueda semántica)
        # ─────────────────────────────
        chunks = self.chunker.chunk(texto_para_chunks)
        texts = [c.text for c in chunks]

        chunk_vectors = self.encoder.encode(texts, batch_size=16)

        chunk_payloads = [
            self._build_chunk_payload(proj, chunk.text, idx, cls_result)
            for idx, chunk in enumerate(chunks)
        ]

        self.qdrant.upsert_chunks(chunk_vectors, chunk_payloads)

        # ─────────────────────────────
        # 3. METRICS
        # ─────────────────────────────
        stats.encoded += len(chunks)
        stats.stored += 1 + len(chunks)  # 1 proyecto + N chunks

    def _build_project_payload(self, proj, cls_result, closed_result):
        return {
            # Identificación
            "id_proyecto": proj.id_proyecto,
            "boletin": proj.boletin,

            # Texto
            "suma": proj.suma,
            "suma_clean": proj.suma_clean,

            # Metadata legislativa (la que aparece en el detalle del proyecto)
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

            # Clasificación
            "categoria_principal": cls_result.primary_category if cls_result else None,
            "subcategorias": cls_result.subcategories if cls_result else [],
            "etiquetas": getattr(cls_result, "labels", []) if cls_result else [],
            "score_clasificacion": getattr(cls_result, "confidence", None) if cls_result else None,
            "explicacion": getattr(cls_result, "explanation", None) if cls_result else None,
            "estado_clasificacion": closed_result.estado if closed_result else None,
            "texto_fuente": closed_result.texto_fuente if closed_result else None,
        }

    def _build_chunk_payload(self, proj, chunk_text, idx, cls_result):
        # Denormalizamos los campos por los que el endpoint /search/hybrid
        # permite filtrar (categoria, fecha, iniciativa, camara, etapa) para
        # que los filtros funcionen sobre chunks_collection sin un join.
        return {
            "id_proyecto": proj.id_proyecto,
            "boletin": proj.boletin,
            "chunk_index": idx,
            "texto_chunk": chunk_text,
        }

    def _already_exists(self, boletin: str) -> bool:
        try:
            return len(self.qdrant.get_by_boletin(boletin)) > 0
        except Exception:
            return False