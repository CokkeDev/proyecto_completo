"""
SearchEngine: motor de búsqueda semántica, estructurada e híbrida.

Encapsula toda la lógica de búsqueda expuesta por las API routes.
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.embeddings.encoder import BGEEncoder
from backend.qdrant.client import QdrantManager

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Motor de búsqueda con tres modos:
      1. Semántica: consulta en lenguaje natural → embedding → Qdrant ANN
      2. Estructurada: filtros por categoría, fecha, etapa → Qdrant scroll
      3. Híbrida: semántica + filtros combinados
    """

    def __init__(
        self,
        encoder: Optional[BGEEncoder] = None,
        qdrant: Optional[QdrantManager] = None,
    ):
        self.encoder = encoder or BGEEncoder.get_instance()
        self.qdrant = qdrant or QdrantManager()

    # ── Búsqueda semántica ────────────────────────────────────────────────────
    def search_semantic(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.40,
    ) -> list[dict]:
        """
        Busca proyectos por similitud semántica con la consulta.

        El prefijo de recuperación mejora la calidad de resultados con BGE-M3.
        """
        query_vec = self.encoder.encode_for_query(query)
        results = self.qdrant.search_semantic(
            query_vector=query_vec,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        return self._deduplicate_by_boletin(results, top_k)

    # ── Búsqueda híbrida ──────────────────────────────────────────────────────
    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.35,
        categoria: Optional[str] = None,
        subcategorias: Optional[list[str]] = None,
        etiquetas: Optional[list[str]] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        etapa: Optional[str] = None,
        iniciativa: Optional[str] = None,
        camara_origen: Optional[str] = None,
    ) -> list[dict]:
        """Búsqueda semántica con filtros estructurados aplicados en Qdrant."""
        query_vec = self.encoder.encode_for_query(query)
        results = self.qdrant.search_hybrid(
            query_vector=query_vec,
            top_k=top_k * 2,  # pedimos más para compensar deduplicación
            score_threshold=score_threshold,
            categoria=categoria,
            subcategorias=subcategorias,
            etiquetas=etiquetas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            etapa=etapa,
            iniciativa=iniciativa,
            camara_origen=camara_origen,
        )
        return self._deduplicate_by_boletin(results, top_k)

    # ── Búsqueda estructurada ─────────────────────────────────────────────────
    def search_structured(
        self,
        categoria: Optional[str] = None,
        subcategorias: Optional[list[str]] = None,
        etiquetas: Optional[list[str]] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        etapa: Optional[str] = None,
        limit: int = 20,
        offset: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        """Búsqueda sin vector — solo por filtros."""
        return self.qdrant.scroll_structured(
            categoria=categoria,
            subcategorias=subcategorias,
            etiquetas=etiquetas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            etapa=etapa,
            limit=limit,
            offset=offset,
        )

    # ── Detalle por boletín ───────────────────────────────────────────────────
    def get_detail(self, boletin: str) -> Optional[dict]:
        chunks = self.qdrant.get_by_boletin(boletin)
        if not chunks:
            return None
        # Tomar el chunk 0 (o el primero disponible)
        primary = next((c for c in chunks if c.get("chunk_index", 0) == 0), chunks[0])
        primary["total_chunks"] = len(chunks)
        return primary

    # ── Proyectos similares ───────────────────────────────────────────────────
    def get_similar(self, boletin: str, top_k: int = 5) -> list[dict]:
        """Proyectos similares al dado (usando su texto como query)."""
        detail = self.get_detail(boletin)
        if not detail:
            return []
        texto = detail.get("suma_clean") or detail.get("suma", "")
        if not texto:
            return []
        results = self.search_semantic(query=texto, top_k=top_k + 5)
        # Excluir el propio boletín
        return [r for r in results if r.get("boletin") != boletin][:top_k]

    # ── Deduplicación ─────────────────────────────────────────────────────────
    @staticmethod
    def _deduplicate_by_boletin(results: list[dict], top_k: int) -> list[dict]:
        """
        Cuando un doc tiene múltiples chunks, conservar solo el de mayor score.
        """
        seen: dict[str, dict] = {}
        for r in results:
            boletin = r.get("boletin", r.get("id", ""))
            if boletin not in seen or r.get("score", 0) > seen[boletin].get("score", 0):
                seen[boletin] = r
        return list(seen.values())[:top_k]
