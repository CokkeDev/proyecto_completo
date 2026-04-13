"""
Módulo de embeddings con BAAI/bge-m3.

Usa FlagEmbedding (biblioteca oficial de BAAI) que expone:
  - dense_vecs  : numpy (N, 1024) — usados para Qdrant
  - lexical_weights : dict por token — para búsqueda sparse (BM25-style)
  - colbert_vecs : multi-vector (no usado en MVP, disponible como upgrade)

Patrón Singleton: una sola instancia del modelo para toda la aplicación.
"""
from __future__ import annotations

import logging
import numpy as np
from typing import Union

logger = logging.getLogger(__name__)

_INSTANCE: "BGEEncoder | None" = None


class BGEEncoder:
    """Wrapper sobre BGEM3FlagModel con pool de lote y soporte lazy-load."""

    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True):
        logger.info(f"Cargando modelo {model_name} (fp16={use_fp16})...")
        from FlagEmbedding import BGEM3FlagModel  # importación tardía — pesada
        self.model = BGEM3FlagModel(model_name, use_fp16=use_fp16)
        self.dim = 1024
        logger.info("Modelo cargado OK.")

    # ── Singleton ────────────────────────────────────────────────────────────
    @classmethod
    def get_instance(cls) -> "BGEEncoder":
        global _INSTANCE
        if _INSTANCE is None:
            from backend.config import settings
            _INSTANCE = cls(
                model_name=settings.embedding_model,
                use_fp16=settings.embedding_use_fp16,
            )
        return _INSTANCE

    # ── Encode ───────────────────────────────────────────────────────────────
    def encode(
        self,
        texts: Union[str, list[str]],
        batch_size: int = 8,
        max_length: int = 8192,
    ) -> np.ndarray:
        """
        Devuelve matriz (N, 1024) de vectores densos normalizados L2.

        Parameters
        ----------
        texts : str o list[str]
        batch_size : tamaño del lote para GPU/CPU
        max_length : tokens máximos por texto (BGE-M3 soporta hasta 8192)

        Returns
        -------
        np.ndarray  shape (N, 1024)  dtype float32
        """
        if isinstance(texts, str):
            texts = [texts]

        output = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vecs: np.ndarray = output["dense_vecs"]  # (N, 1024)
        return vecs.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """Shortcut para un solo texto. Devuelve (1024,)."""
        return self.encode([text])[0]

    def encode_for_query(self, query: str) -> np.ndarray:
        """
        BGE-M3 recomienda prefijo 'Represent this sentence for searching relevant passages:'
        para consultas de recuperación.
        """
        prefixed = f"Represent this sentence for searching relevant passages: {query}"
        return self.encode_single(prefixed)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Similitud coseno entre dos vectores 1-D."""
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def batch_cosine_similarity(
        self, query: np.ndarray, matrix: np.ndarray
    ) -> np.ndarray:
        """
        Similitudes coseno entre `query` (1024,) y cada fila de `matrix` (N, 1024).
        Devuelve (N,).
        """
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        safe = np.where(norms == 0, 1e-9, norms)
        normed_matrix = matrix / safe
        normed_query = query / (np.linalg.norm(query) + 1e-9)
        return (normed_matrix @ normed_query).astype(np.float32)
