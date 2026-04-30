"""
Definición del schema de la colección Qdrant para proyectos de ley.

Colección: proyectos_ley
Vector: 1024-dim, distancia coseno (BAAI/bge-m3 dense)
"""
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)

COLLECTION_PROYECTOS = "proyectos_ley"
COLLECTION_CHUNKS = "chunks"
VECTOR_DIM = 1024
VECTOR_DISTANCE = Distance.COSINE

# Schema del payload almacenado en cada punto Qdrant
PAYLOAD_FIELDS = {
    # Identificación
    "id_proyecto":       "integer",
    "boletin":           "keyword",   # ej: "13312-03"
    "chunk_index":       "integer",   # 0 para docs cortos

    # Texto
    "suma":              "text",
    "suma_clean":        "text",

    # Metadata legislativa
    "fecha_ingreso":     "keyword",   # "YYYY-MM-DD"
    "year":              "integer",
    "month":             "integer",
    "iniciativa":        "keyword",   # "Mensaje" | "Moción"
    "camara_origen":     "keyword",
    "etapa":             "keyword",
    "autores":           "keyword",   # lista
    "materias_raw":      "keyword",   # lista

    # Clasificación
    "categoria_principal":   "keyword",
    "categorias":            "keyword",   # lista multi-label
    "subcategorias":         "keyword",   # lista
    "etiquetas":             "keyword",   # lista
    "score_clasificacion":   "float",

    # URLs
    "link_proyecto":     "keyword",
    "documento_url":     "keyword",
}

CHUNK_PAYLOAD_FIELDS = {
    "id_proyecto": "integer",
    "boletin": "keyword",
    "chunk_index": "integer",

    # SOLO lo necesario para búsqueda
    "texto_chunk": "text",

    # opcional (muy útil para filtros)
    "categoria_principal": "keyword",
    "subcategorias": "keyword",
}


def get_vector_config() -> VectorParams:
    return VectorParams(size=VECTOR_DIM, distance=VECTOR_DISTANCE)
