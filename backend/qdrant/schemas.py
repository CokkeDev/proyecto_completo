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

COLLECTION_NAME = "proyectos_ley"
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
    "texto_chunk":       "text",

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
    "origen_clasificacion":  "keyword",   # "rules" | "embeddings" | "hybrid"
    "explicacion":           "text",

    # URLs
    "link_proyecto":     "keyword",
    "documento_url":     "keyword",
}


def get_vector_config() -> VectorParams:
    return VectorParams(size=VECTOR_DIM, distance=VECTOR_DISTANCE)
