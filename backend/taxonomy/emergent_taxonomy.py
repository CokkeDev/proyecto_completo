"""
EmergentTaxonomyDetector: detecta clusters temáticos emergentes mediante HDBSCAN
sobre los embeddings de BAAI/bge-m3.

Pipeline:
  1. Recibe embeddings (N, 1024)
  2. Reduce dimensionalidad con UMAP (1024 → 50)
  3. Agrupa con HDBSCAN
  4. Propone etiquetas automáticas extrayendo keywords por cluster
  5. Mide novedad respecto a la taxonomía manual
"""
from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmergentCluster:
    cluster_id: int
    size: int
    sample_texts: list[str] = field(default_factory=list)
    top_keywords: list[str] = field(default_factory=list)
    suggested_label: str = ""
    novelty_score: float = 0.0        # 0=conocido, 1=completamente nuevo
    closest_manual_category: str = ""
    closest_similarity: float = 0.0
    centroid: Optional[np.ndarray] = None
    validated: bool = False


class EmergentTaxonomyDetector:
    """
    Detecta subcategorías emergentes en un corpus de proyectos.

    Uso típico:
        detector = EmergentTaxonomyDetector()
        clusters = detector.detect(embeddings, texts)
        novel = detector.filter_novel(clusters, threshold=0.6)
    """

    def __init__(
        self,
        min_cluster_size: int = 5,
        min_samples: int = 3,
        umap_components: int = 50,
        umap_neighbors: int = 15,
        novelty_threshold: float = 0.55,
    ):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.umap_components = umap_components
        self.umap_neighbors = umap_neighbors
        self.novelty_threshold = novelty_threshold

    # ── Pipeline principal ────────────────────────────────────────────────────
    def detect(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        category_prototypes: Optional[dict[str, np.ndarray]] = None,
    ) -> list[EmergentCluster]:
        """
        Parameters
        ----------
        embeddings : (N, 1024) float32
        texts      : lista de N textos correspondientes
        category_prototypes : {cat_code: centroid_vector} de taxonomía manual

        Returns
        -------
        lista de EmergentCluster (excluye ruido = label -1)
        """
        n = len(embeddings)
        if n < self.min_cluster_size * 2:
            logger.warning(f"Muy pocos documentos ({n}) para clustering emergente.")
            return []

        reduced = self._reduce_dimensions(embeddings)
        labels, probs = self._cluster(reduced)
        clusters = self._build_clusters(labels, probs, embeddings, texts)

        if category_prototypes:
            clusters = self._score_novelty(clusters, category_prototypes)

        logger.info(
            f"Clustering emergente: {len(clusters)} clusters encontrados "
            f"(noise={np.sum(labels == -1)})."
        )
        return clusters

    def filter_novel(
        self, clusters: list[EmergentCluster], threshold: Optional[float] = None
    ) -> list[EmergentCluster]:
        """Filtra solo los clusters suficientemente nuevos."""
        t = threshold or self.novelty_threshold
        return [c for c in clusters if c.novelty_score >= t]

    # ── UMAP ─────────────────────────────────────────────────────────────────
    def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        try:
            import umap
            reducer = umap.UMAP(
                n_components=self.umap_components,
                n_neighbors=self.umap_neighbors,
                metric="cosine",
                random_state=42,
                low_memory=True,
            )
            return reducer.fit_transform(embeddings)
        except ImportError:
            logger.warning("umap-learn no instalado. Usando PCA de sklearn como fallback.")
            from sklearn.decomposition import PCA
            n_comp = min(self.umap_components, embeddings.shape[1], embeddings.shape[0] - 1)
            return PCA(n_components=n_comp, random_state=42).fit_transform(embeddings)

    # ── HDBSCAN ───────────────────────────────────────────────────────────────
    def _cluster(self, reduced: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
                cluster_selection_method="eom",
                prediction_data=True,
            )
            labels = clusterer.fit_predict(reduced)
            probs = clusterer.probabilities_
            return labels, probs
        except ImportError:
            logger.warning("hdbscan no instalado. Usando AgglomerativeClustering como fallback.")
            from sklearn.cluster import AgglomerativeClustering
            n_clusters = max(2, len(reduced) // self.min_cluster_size)
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
            labels = clusterer.fit_predict(reduced)
            probs = np.ones(len(labels))
            return labels, probs

    # ── Construcción de clusters ──────────────────────────────────────────────
    def _build_clusters(
        self,
        labels: np.ndarray,
        probs: np.ndarray,
        embeddings: np.ndarray,
        texts: list[str],
    ) -> list[EmergentCluster]:
        unique_labels = set(labels) - {-1}
        clusters = []

        for cid in sorted(unique_labels):
            mask = labels == cid
            cluster_texts = [t for t, m in zip(texts, mask) if m]
            cluster_embs = embeddings[mask]
            centroid = cluster_embs.mean(axis=0)

            top_kws = self._extract_keywords(cluster_texts)
            suggested = self._suggest_label(top_kws)

            clusters.append(
                EmergentCluster(
                    cluster_id=int(cid),
                    size=int(mask.sum()),
                    sample_texts=cluster_texts[:5],
                    top_keywords=top_kws[:10],
                    suggested_label=suggested,
                    centroid=centroid,
                )
            )

        return clusters

    # ── Novedad ───────────────────────────────────────────────────────────────
    def _score_novelty(
        self,
        clusters: list[EmergentCluster],
        category_prototypes: dict[str, np.ndarray],
    ) -> list[EmergentCluster]:
        """
        Novelty = 1 - max_similarity(cluster_centroid, category_prototypes).
        Si el cluster es muy similar a una categoría conocida, no es nuevo.
        """
        proto_matrix = np.stack(list(category_prototypes.values()))  # (K, 1024)
        proto_keys = list(category_prototypes.keys())

        for cluster in clusters:
            if cluster.centroid is None:
                cluster.novelty_score = 0.5
                continue

            centroid = cluster.centroid
            norm_c = np.linalg.norm(centroid)
            if norm_c == 0:
                cluster.novelty_score = 0.5
                continue

            # similitud coseno con todos los prototipos
            norms = np.linalg.norm(proto_matrix, axis=1)
            sims = (proto_matrix @ centroid) / (norms * norm_c + 1e-9)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            cluster.closest_manual_category = proto_keys[best_idx]
            cluster.closest_similarity = best_sim
            cluster.novelty_score = max(0.0, 1.0 - best_sim)

        return clusters

    # ── Keywords (TF-IDF simple) ──────────────────────────────────────────────
    def _extract_keywords(self, texts: list[str], top_n: int = 15) -> list[str]:
        """Extrae keywords por frecuencia de términos relevantes."""
        import re
        from collections import Counter

        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "las", "del", "que",
            "se", "por", "con", "para", "un", "una", "al", "es", "su",
            "lo", "le", "no", "este", "esta", "como", "más", "pero",
            "o", "e", "ni", "si", "ya", "todo", "toda", "todos", "todas",
            "sobre", "entre", "cuando", "así", "sin", "ser", "ha",
            "son", "fue", "han", "puede", "también", "caso", "que",
        }
        counter: Counter = Counter()
        for text in texts:
            tokens = re.findall(r"\b[a-záéíóúüñ]{4,}\b", text.lower())
            for t in tokens:
                if t not in stopwords:
                    counter[t] += 1

        return [word for word, _ in counter.most_common(top_n)]

    def _suggest_label(self, keywords: list[str]) -> str:
        """Genera un label descriptivo a partir de los top keywords."""
        if not keywords:
            return "cluster_sin_etiqueta"
        return "_".join(kw.upper() for kw in keywords[:3])

    # ── Reporte para validación humana ────────────────────────────────────────
    def to_validation_report(self, clusters: list[EmergentCluster]) -> list[dict]:
        return [
            {
                "cluster_id": c.cluster_id,
                "size": c.size,
                "suggested_label": c.suggested_label,
                "top_keywords": c.top_keywords,
                "sample_texts": c.sample_texts,
                "novelty_score": round(c.novelty_score, 3),
                "closest_manual_category": c.closest_manual_category,
                "closest_similarity": round(c.closest_similarity, 3),
                "validated": c.validated,
            }
            for c in clusters
        ]
