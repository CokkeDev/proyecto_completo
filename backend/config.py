from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Buscador de Proyectos de Ley"
    app_version: str = "1.0.0"
    debug: bool = False

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection: str = "proyectos_ley"
    qdrant_in_memory: bool = False  # True para tests sin Docker

    # BAAI/bge-m3
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    embedding_batch_size: int = 8
    embedding_use_fp16: bool = True

    # Fuente de datos Senado
    senado_api_base: str = "https://restsil-ventanillaunica.senado.cl/v3"
    senado_api_desde: str = "18/03/2020"
    senado_api_hasta: str = "30/03/2026"
    senado_api_limit: int = 1000
    senado_api_timeout: int = 30

    # Clasificación híbrida
    rule_weight: float = 0.40
    embedding_weight: float = 0.60
    classification_threshold: float = 0.60
    max_labels: int = 5

    # Chunking (en palabras)
    chunk_size: int = 400
    chunk_overlap: int = 50

    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
