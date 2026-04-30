"""
EmbeddingClassifier: clasificación por similitud semántica con BAAI/bge-m3.

Estrategia:
  1. Al inicializar, calcula vectores prototipo por categoría promediando
     los embeddings de todos los textos ejemplo/prototipo de cada categoría.
  2. Para clasificar un texto: codifica el texto y calcula similitud coseno
     con cada prototipo.

Ventaja: completamente sin supervisión — no requiere datos etiquetados.
"""
from __future__ import annotations

import logging
import numpy as np
from typing import Optional

from backend.embeddings.encoder import BGEEncoder
from backend.taxonomy.manual_taxonomy import ManualTaxonomy

logger = logging.getLogger(__name__)

_TAXONOMY = ManualTaxonomy()


class EmbeddingClassifier:
    """
    Clasifica proyectos de ley usando similitud coseno contra prototipos
    calculados con BAAI/bge-m3.
    """

    def __init__(
        self,
        encoder: Optional[BGEEncoder] = None,
        taxonomy: Optional[ManualTaxonomy] = None,
    ):
        self.encoder = encoder or BGEEncoder.get_instance()
        self.taxonomy = taxonomy or _TAXONOMY

        # {cat_code: np.ndarray (1024,)}
        self._prototypes: dict[str, np.ndarray] = {}
        self._build_prototypes()

    # ── Construcción de prototipos ────────────────────────────────────────────
    def _build_prototypes(self):
        """
        Para cada categoría: promedia los embeddings de todos sus textos prototipo.
        Si no hay textos suficientes, usa la definición + keywords concatenadas.
        """
        all_protos = self.taxonomy.get_all_prototype_texts()

        for cat_code, texts in all_protos.items():
            if not texts:
                logger.warning(f"Categoría {cat_code} sin textos prototipo.")
                continue
            try:
                vecs = self.encoder.encode(texts, batch_size=16)  # (N, 1024)
                centroid = vecs.mean(axis=0)
                norm = np.linalg.norm(centroid)
                self._prototypes[cat_code] = centroid / (norm + 1e-9)
            except Exception as e:
                logger.error(f"Error al codificar prototipos de {cat_code}: {e}")

        logger.info(f"Prototipos calculados para {len(self._prototypes)} categorías.")

    # ── Predicción ────────────────────────────────────────────────────────────
    def predict(self, text: str) -> dict[str, float]:
        """
        Devuelve {cat_code: cosine_similarity} ∈ [-1, 1], normalizado a [0, 1].
        """
        if not self._prototypes:
            return {}

        query_vec = self.encoder.encode_for_query(text)  # (1024,)
        norm_q = np.linalg.norm(query_vec)
        if norm_q == 0:
            return {c: 0.0 for c in self._prototypes}

        query_vec_n = query_vec / norm_q
        scores: dict[str, float] = {}

        for cat_code, proto in self._prototypes.items():
            sim = float(np.dot(query_vec_n, proto))
            # Mapear de [-1,1] a [0,1]
            scores[cat_code] = round((sim + 1.0) / 2.0, 4)

        return scores

    def get_prototypes(self) -> dict[str, np.ndarray]:
        """Retorna el diccionario de prototipos (para clustering emergente)."""
        return self._prototypes
