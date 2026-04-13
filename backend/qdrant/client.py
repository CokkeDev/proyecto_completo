"""
QdrantManager: gestión de la colección Qdrant.

Responsabilidades:
  - Crear/verificar colección con schema correcto
  - Upsert de puntos (con payload completo)
  - Búsqueda semántica pura
  - Búsqueda híbrida (semántica + filtros)
  - Búsqueda estructurada por filtros
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
)

from backend.config import settings
from .schemas import COLLECTION_NAME, VECTOR_DIM, VECTOR_DISTANCE

logger = logging.getLogger(__name__)


class QdrantManager:
    """Wrapper sobre qdrant_client con helpers específicos para proyectos de ley."""

    def __init__(self):
        if settings.qdrant_in_memory:
            self.client = QdrantClient(":memory:")
            logger.info("Qdrant en modo in-memory (testing).")
        else:
            kwargs = {
                "host": settings.qdrant_host,
                "port": settings.qdrant_port,
            }
            if settings.qdrant_api_key:
                kwargs["api_key"] = settings.qdrant_api_key
            self.client = QdrantClient(**kwargs)
            logger.info(
                f"Conectado a Qdrant en {settings.qdrant_host}:{settings.qdrant_port}."
            )

    # ── Colección ─────────────────────────────────────────────────────────────
    def ensure_collection(self):
        """Crea la colección si no existe; no la modifica si ya existe."""
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=VECTOR_DISTANCE),
            )
            logger.info(f"Colección '{COLLECTION_NAME}' creada (dim={VECTOR_DIM}).")
        else:
            logger.info(f"Colección '{COLLECTION_NAME}' ya existe.")

    def collection_info(self) -> dict:
        """Obtiene información de la colección de forma robusta."""
        info = self.client.get_collection(COLLECTION_NAME)

        status = getattr(info, "status", None)
        if hasattr(status, "value"):
            status = status.value

        return {
            "name": COLLECTION_NAME,
            "points_count": getattr(info, "points_count", 0),
            "vectors_count": getattr(info, "vectors_count", 0),
            "indexed_vectors_count": getattr(info, "indexed_vectors_count", 0),
            "status": status or "unknown",
        }

    # ── Upsert ────────────────────────────────────────────────────────────────
    def upsert_point(
        self, vector: np.ndarray, payload: dict, point_id: Optional[str] = None
    ) -> str:
        """Inserta o actualiza un punto."""
        pid = point_id or str(uuid.uuid4())
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=pid,
                    vector=vector.tolist(),
                    payload=payload,
                )
            ],
        )
        return pid

    def upsert_batch(
        self,
        vectors: list[np.ndarray],
        payloads: list[dict],
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        """Upsert de múltiples puntos en una sola operación (más eficiente)."""
        n = len(vectors)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(n)]

        points = [
            PointStruct(id=ids[i], vector=vectors[i].tolist(), payload=payloads[i])
            for i in range(n)
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        return ids

    # ── Búsqueda semántica ────────────────────────────────────────────────────
    def search_semantic(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        score_threshold: float = 0.4,
        filter_: Optional[Filter] = None,
    ) -> list[dict]:
        """
        Búsqueda semántica con BAAI/bge-m3.
        Compatible con versiones recientes de qdrant-client.
        """
        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector.tolist(),
            query_filter=filter_,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        )

        points = getattr(response, "points", response)

        return [
            {"id": str(p.id), "score": p.score, **p.payload}
            for p in points
        ]

    # ── Búsqueda híbrida ──────────────────────────────────────────────────────
    def search_hybrid(
        self,
        query_vector: np.ndarray,
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
        """
        Búsqueda semántica + filtros estructurados combinados.
        """
        filter_ = self._build_filter(
            categoria=categoria,
            subcategorias=subcategorias,
            etiquetas=etiquetas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            etapa=etapa,
            iniciativa=iniciativa,
            camara_origen=camara_origen,
        )
        return self.search_semantic(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_=filter_,
        )

    # ── Búsqueda estructurada (sin vector) ───────────────────────────────────
    def scroll_structured(
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
        """
        Scroll por filtros sin búsqueda vectorial.
        Retorna (resultados, next_offset).
        """
        filter_ = self._build_filter(
            categoria=categoria,
            subcategorias=subcategorias,
            etiquetas=etiquetas,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            etapa=etapa,
        )
        points, next_page = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=filter_,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        results = [{"id": str(p.id), **p.payload} for p in points]
        return results, (str(next_page) if next_page else None)

    # ── Búsqueda por boletín ──────────────────────────────────────────────────
    def get_by_boletin(self, boletin: str) -> list[dict]:
        """Retorna todos los chunks de un boletín específico."""
        filter_ = Filter(
            must=[FieldCondition(key="boletin", match=MatchValue(value=boletin))]
        )
        points, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=filter_,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        return [{"id": str(p.id), **p.payload} for p in points]

    # ── Construcción de filtros ───────────────────────────────────────────────
    def _build_filter(
        self,
        categoria: Optional[str] = None,
        subcategorias: Optional[list[str]] = None,
        etiquetas: Optional[list[str]] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        etapa: Optional[str] = None,
        iniciativa: Optional[str] = None,
        camara_origen: Optional[str] = None,
    ) -> Optional[Filter]:
        conditions = []

        if categoria:
            conditions.append(
                FieldCondition(
                    key="categoria_principal",
                    match=MatchValue(value=categoria),
                )
            )
        if subcategorias:
            conditions.append(
                FieldCondition(
                    key="subcategorias",
                    match=MatchAny(any=subcategorias),
                )
            )
        if etiquetas:
            conditions.append(
                FieldCondition(
                    key="etiquetas",
                    match=MatchAny(any=etiquetas),
                )
            )
        if fecha_desde or fecha_hasta:
            range_kwargs = {}
            if fecha_desde:
                range_kwargs["gte"] = fecha_desde
            if fecha_hasta:
                range_kwargs["lte"] = fecha_hasta
            conditions.append(
                FieldCondition(
                    key="fecha_ingreso",
                    range=Range(**range_kwargs),
                )
            )
        if etapa:
            conditions.append(
                FieldCondition(key="etapa", match=MatchValue(value=etapa))
            )
        if iniciativa:
            conditions.append(
                FieldCondition(key="iniciativa", match=MatchValue(value=iniciativa))
            )
        if camara_origen:
            conditions.append(
                FieldCondition(
                    key="camara_origen",
                    match=MatchValue(value=camara_origen),
                )
            )

        if not conditions:
            return None
        return Filter(must=conditions)

    # ── Clusters para taxonomía emergente ────────────────────────────────────
    def get_all_vectors_and_texts(
        self, limit: int = 5000
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """
        Retorna (vectors, textos, boletines) para clustering emergente.
        """
        points, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=True,
        )
        vectors = np.array([p.vector for p in points], dtype=np.float32)
        texts = [p.payload.get("texto_chunk", "") for p in points]
        boletines = [p.payload.get("boletin", "") for p in points]
        return vectors, texts, boletines
