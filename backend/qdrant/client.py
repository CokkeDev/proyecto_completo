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
from .schemas import COLLECTION_PROYECTOS, VECTOR_DIM, VECTOR_DISTANCE, COLLECTION_CHUNKS

logger = logging.getLogger(__name__)

# Nombres reales de colección usados por upsert_project / upsert_chunks.
# Mantengo "projects_collection" y "chunks_collection" porque es lo que ya
# tenías cableado en el código de ingesta.
PROJECTS_COLLECTION = "projects_collection"
CHUNKS_COLLECTION = "chunks_collection"

# Alias usado por el resto de los métodos legacy (search_semantic, scroll, etc.)
# que originalmente referenciaban un símbolo COLLECTION_NAME que nunca existió.
# Apuntamos al de chunks porque ahí viven los textos que se buscan.
COLLECTION_NAME = CHUNKS_COLLECTION


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
    def _ensure_one(self, name: str) -> None:
        """Crea una colección con el schema correcto si no existe."""
        existing = [c.name for c in self.client.get_collections().collections]
        if name not in existing:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=VECTOR_DISTANCE),
            )
            logger.info(f"Colección '{name}' creada (dim={VECTOR_DIM}).")
        else:
            logger.info(f"Colección '{name}' ya existe.")

    def ensure_collection(self):
        """Crea ambas colecciones (proyectos y chunks) si no existen."""
        self._ensure_one(PROJECTS_COLLECTION)
        self._ensure_one(CHUNKS_COLLECTION)

    def collection_info(self) -> dict:
        """Obtiene información de la colección de chunks de forma robusta."""
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
        # Búsqueda estructurada va contra projects_collection: no requiere
        # vector, y los campos a filtrar (iniciativa, camara, etapa, etc.)
        # viven completos a nivel de proyecto.
        points, next_page = self.client.scroll(
            collection_name=PROJECTS_COLLECTION,
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
        """
        Retorna el (los) registro(s) del boletín. Apunta a projects_collection
        para que cosas como _already_exists y get_detail trabajen contra el
        payload de proyecto.
        """
        filter_ = Filter(
            must=[FieldCondition(key="boletin", match=MatchValue(value=boletin))]
        )
        points, _ = self.client.scroll(
            collection_name=PROJECTS_COLLECTION,
            scroll_filter=filter_,
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        return [{"id": str(p.id), **p.payload} for p in points]

    def get_project_by_boletin(self, boletin: str) -> Optional[dict]:
        """
        Retorna el payload completo del proyecto desde projects_collection,
        o None si no existe.
        """
        items = self.get_by_boletin(boletin)
        return items[0] if items else None

    def get_projects_by_boletines(self, boletines: list[str]) -> dict[str, dict]:
        """
        Carga en un solo round-trip los payloads de varios boletines desde
        projects_collection. Devuelve un dict {boletin: payload} para enriquecer
        resultados de búsqueda (que vienen de chunks_collection) con la metadata
        legislativa completa: suma, iniciativa, autores, etapa, materias, etc.
        """
        if not boletines:
            return {}
        unique = list(dict.fromkeys(boletines))  # preserva orden, deduplica
        filter_ = Filter(
            must=[FieldCondition(key="boletin", match=MatchAny(any=unique))]
        )
        try:
            points, _ = self.client.scroll(
                collection_name=PROJECTS_COLLECTION,
                scroll_filter=filter_,
                limit=max(len(unique), 100),
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            logger.warning(f"No se pudo leer projects_collection: {e}")
            return {}
        result: dict[str, dict] = {}
        for p in points:
            payload = p.payload or {}
            b = payload.get("boletin")
            if b and b not in result:
                result[b] = {"id": str(p.id), **payload}
        return result

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

    # Namespace estable para derivar UUIDs determinísticos a partir de
    # claves lógicas tipo "<boletin>_project" o "<boletin>_chunk_<i>".
    # Qdrant exige que el id de cada punto sea un entero sin signo o un UUID,
    # por lo que NO podemos usar strings arbitrarios como id.
    _ID_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")

    @classmethod
    def _stable_uuid(cls, key: str) -> str:
        """Genera un UUID determinístico a partir de una clave string."""
        return str(uuid.uuid5(cls._ID_NAMESPACE, key))

    #ingesta de proyectos de ley en su colección indicada.
    def upsert_project(self, vector, payload):
        # Auto-crear la colección si no existe (red de seguridad)
        self._ensure_one(PROJECTS_COLLECTION)

        # Convertir vector numpy a lista si es necesario
        if hasattr(vector, "tolist"):
            vector = vector.tolist()

        logical_id = f"{payload['boletin']}_project"
        point_id = self._stable_uuid(logical_id)

        # Guardamos la clave lógica en el payload para trazabilidad
        payload = {**payload, "logical_id": logical_id}

        self.client.upsert(
            collection_name=PROJECTS_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    #ingesta de chunks.
    def upsert_chunks(self, vectors, payloads):
        # Auto-crear la colección si no existe
        self._ensure_one(CHUNKS_COLLECTION)

        points = []

        for i, (vec, payload) in enumerate(zip(vectors, payloads)):
            if hasattr(vec, "tolist"):
                vec = vec.tolist()

            logical_id = f"{payload['boletin']}_chunk_{i}"
            point_id = self._stable_uuid(logical_id)

            payload = {**payload, "logical_id": logical_id}

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=CHUNKS_COLLECTION,
            points=points,
        )

