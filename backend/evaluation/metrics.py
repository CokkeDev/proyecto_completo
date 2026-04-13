"""
Sistema de evaluación formal para la tesis.

Implementa:
  1. Métricas multi-label: accuracy, precision, recall, F1 (macro/micro/weighted)
  2. Similitud semántica: cosine similarity, recall@k
  3. Evaluación de texto: ROUGE-L
  4. Benchmarking: reglas vs embeddings vs híbrido

─── Por qué accuracy NO es suficiente ─────────────────────────────────────
En clasificación multi-label con distribución desbalanceada:
  - Una categoría mayoritaria (ej: DERECHO_LABORAL) podría representar el 40%
    de los proyectos. Un clasificador que predice SIEMPRE esa categoría
    obtendría 40% accuracy — pero sería completamente inútil para las demás.
  - F1-score macro promedia el rendimiento por clase, penalizando el olvido
    de categorías minoritarias.
  - F1-score weighted es más representativo cuando las clases tienen distinto
    soporte (nº de ejemplos).
  - Para sistemas de recuperación donde el recall es crítico (no perderse
    proyectos importantes), F1 con foco en recall es la métrica principal.
─────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ─── Estructuras de datos ─────────────────────────────────────────────────────

@dataclass
class ClassificationMetrics:
    accuracy_subset: float = 0.0   # subset accuracy (strict multi-label)
    hamming_loss: float = 0.0
    precision_micro: float = 0.0
    recall_micro: float = 0.0
    f1_micro: float = 0.0
    precision_macro: float = 0.0
    recall_macro: float = 0.0
    f1_macro: float = 0.0
    precision_weighted: float = 0.0
    recall_weighted: float = 0.0
    f1_weighted: float = 0.0
    per_class: dict[str, dict] = field(default_factory=dict)
    confusion_matrix: Optional[list[list[int]]] = None
    support: dict[str, int] = field(default_factory=dict)


@dataclass
class SemanticMetrics:
    mean_cosine_similarity: float = 0.0
    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    mean_reciprocal_rank: float = 0.0


@dataclass
class TextMetrics:
    rouge_l_precision: float = 0.0
    rouge_l_recall: float = 0.0
    rouge_l_fmeasure: float = 0.0


@dataclass
class BenchmarkResult:
    method: str
    classification: ClassificationMetrics
    semantic: Optional[SemanticMetrics] = None


# ─── Cálculos ─────────────────────────────────────────────────────────────────

class MetricsCalculator:
    """
    Calculadora de métricas formales.

    Decisión de diseño — qué métrica usar en cada caso:
    ┌─────────────────────┬────────────────────────────────────────────────┐
    │ Tarea               │ Métrica principal                              │
    ├─────────────────────┼────────────────────────────────────────────────┤
    │ Clasificación       │ F1-weighted (balanceado por clase)             │
    │                     │ F1-macro (sin sesgo hacia clases mayoritarias) │
    │                     │ Recall (cuando no perderse clases es crítico)  │
    ├─────────────────────┼────────────────────────────────────────────────┤
    │ Embeddings/Retrieval│ Cosine similarity, Recall@k, MRR               │
    ├─────────────────────┼────────────────────────────────────────────────┤
    │ Generación texto    │ ROUGE-L (captura orden + n-gramas largos)      │
    └─────────────────────┴────────────────────────────────────────────────┘
    """

    # ── Clasificación multi-label ─────────────────────────────────────────────
    @staticmethod
    def classification_metrics(
        y_true: list[list[str]],
        y_pred: list[list[str]],
        all_classes: Optional[list[str]] = None,
    ) -> ClassificationMetrics:
        """
        Calcula métricas multi-label completas.

        Parameters
        ----------
        y_true : lista de listas de etiquetas reales
        y_pred : lista de listas de etiquetas predichas
        all_classes : lista de todas las clases posibles (para MLB)
        """
        from sklearn.preprocessing import MultiLabelBinarizer
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            hamming_loss, accuracy_score,
            classification_report,
        )

        mlb = MultiLabelBinarizer(classes=all_classes)
        Y_true = mlb.fit_transform(y_true)
        Y_pred = mlb.transform(y_pred)

        classes = list(mlb.classes_)

        metrics = ClassificationMetrics(
            accuracy_subset=float(accuracy_score(Y_true, Y_pred)),
            hamming_loss=float(hamming_loss(Y_true, Y_pred)),
            precision_micro=float(precision_score(Y_true, Y_pred, average="micro", zero_division=0)),
            recall_micro=float(recall_score(Y_true, Y_pred, average="micro", zero_division=0)),
            f1_micro=float(f1_score(Y_true, Y_pred, average="micro", zero_division=0)),
            precision_macro=float(precision_score(Y_true, Y_pred, average="macro", zero_division=0)),
            recall_macro=float(recall_score(Y_true, Y_pred, average="macro", zero_division=0)),
            f1_macro=float(f1_score(Y_true, Y_pred, average="macro", zero_division=0)),
            precision_weighted=float(precision_score(Y_true, Y_pred, average="weighted", zero_division=0)),
            recall_weighted=float(recall_score(Y_true, Y_pred, average="weighted", zero_division=0)),
            f1_weighted=float(f1_score(Y_true, Y_pred, average="weighted", zero_division=0)),
        )

        # Métricas por clase
        p_per = precision_score(Y_true, Y_pred, average=None, zero_division=0)
        r_per = recall_score(Y_true, Y_pred, average=None, zero_division=0)
        f_per = f1_score(Y_true, Y_pred, average=None, zero_division=0)
        support = Y_true.sum(axis=0)

        metrics.per_class = {
            cls: {
                "precision": round(float(p_per[i]), 4),
                "recall": round(float(r_per[i]), 4),
                "f1": round(float(f_per[i]), 4),
                "support": int(support[i]),
            }
            for i, cls in enumerate(classes)
        }
        metrics.support = {cls: int(support[i]) for i, cls in enumerate(classes)}

        return metrics

    # ── Similitud coseno ──────────────────────────────────────────────────────
    @staticmethod
    def cosine_similarity_score(
        query_vectors: np.ndarray,
        result_vectors: np.ndarray,
    ) -> np.ndarray:
        """
        Similitud coseno entre cada query y su resultado correspondiente.
        query_vectors: (N, D), result_vectors: (N, D)
        Retorna (N,) de similitudes.
        """
        from sklearn.metrics.pairwise import paired_cosine_distances
        distances = paired_cosine_distances(query_vectors, result_vectors)
        return 1.0 - distances

    @staticmethod
    def recall_at_k(
        query_vectors: np.ndarray,
        corpus_vectors: np.ndarray,
        relevant_indices: list[list[int]],
        k_values: list[int] = [1, 3, 5, 10],
    ) -> dict[str, float]:
        """
        Recall@k: fracción de consultas donde al menos 1 relevante está en top-k.

        Parameters
        ----------
        query_vectors    : (Q, D)
        corpus_vectors   : (C, D)
        relevant_indices : para cada query, índices del corpus que son relevantes
        k_values         : valores de k a evaluar
        """
        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(query_vectors, corpus_vectors)  # (Q, C)
        sorted_idx = np.argsort(-sims, axis=1)  # (Q, C) desc

        results = {}
        for k in k_values:
            hits = 0
            for q_idx, top_k_idx in enumerate(sorted_idx[:, :k]):
                relevant = set(relevant_indices[q_idx])
                if relevant & set(top_k_idx.tolist()):
                    hits += 1
            results[f"recall@{k}"] = round(hits / len(query_vectors), 4)

        return results

    @staticmethod
    def mean_reciprocal_rank(
        query_vectors: np.ndarray,
        corpus_vectors: np.ndarray,
        relevant_indices: list[list[int]],
    ) -> float:
        """MRR: posición del primer resultado relevante."""
        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(query_vectors, corpus_vectors)
        sorted_idx = np.argsort(-sims, axis=1)

        rr_sum = 0.0
        for q_idx, sorted_corpus_idx in enumerate(sorted_idx):
            relevant = set(relevant_indices[q_idx])
            for rank, corpus_idx in enumerate(sorted_corpus_idx, start=1):
                if corpus_idx in relevant:
                    rr_sum += 1.0 / rank
                    break

        return round(rr_sum / len(query_vectors), 4)

    # ── ROUGE-L ────────────────────────────────────────────────────────────────
    @staticmethod
    def rouge_l(
        predictions: list[str],
        references: list[str],
    ) -> TextMetrics:
        """
        ROUGE-L para evaluación de texto generado (resúmenes, explicaciones).

        Usa rouge-score library de Google.
        """
        try:
            from rouge_score import rouge_scorer
        except ImportError:
            logger.error("rouge-score no instalado. pip install rouge-score")
            return TextMetrics()

        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
        p_sum = r_sum = f_sum = 0.0
        n = len(predictions)

        for pred, ref in zip(predictions, references):
            score = scorer.score(ref, pred)["rougeL"]
            p_sum += score.precision
            r_sum += score.recall
            f_sum += score.fmeasure

        return TextMetrics(
            rouge_l_precision=round(p_sum / n, 4),
            rouge_l_recall=round(r_sum / n, 4),
            rouge_l_fmeasure=round(f_sum / n, 4),
        )

    # ── Reporte de benchmarking ───────────────────────────────────────────────
    @staticmethod
    def benchmark_report(
        results: list[BenchmarkResult],
        output_path: Optional[Path] = None,
    ) -> dict:
        """
        Genera un reporte comparativo entre métodos.
        """
        report = {
            "benchmark": [
                {
                    "method": r.method,
                    "f1_weighted": round(r.classification.f1_weighted, 4),
                    "f1_macro": round(r.classification.f1_macro, 4),
                    "precision_weighted": round(r.classification.precision_weighted, 4),
                    "recall_weighted": round(r.classification.recall_weighted, 4),
                    "hamming_loss": round(r.classification.hamming_loss, 4),
                    "accuracy_subset": round(r.classification.accuracy_subset, 4),
                }
                for r in results
            ]
        }

        # Mejor método por F1-weighted
        best = max(results, key=lambda r: r.classification.f1_weighted)
        report["best_method"] = best.method
        report["rationale"] = (
            f"F1-weighted es la métrica principal porque pondera por el soporte "
            f"de cada clase, siendo más representativa en datasets desbalanceados "
            f"como el corpus de proyectos de ley chilenos."
        )

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"Reporte guardado en {output_path}")

        return report

    # ── Export completo ───────────────────────────────────────────────────────
    @staticmethod
    def export_metrics(
        metrics: ClassificationMetrics,
        output_path: Path,
        method_name: str = "hybrid",
    ):
        """Exporta métricas a JSON para reproducibilidad."""
        data = {
            "method": method_name,
            "summary": {
                "accuracy_subset": metrics.accuracy_subset,
                "hamming_loss": metrics.hamming_loss,
                "f1_weighted": metrics.f1_weighted,
                "f1_macro": metrics.f1_macro,
                "f1_micro": metrics.f1_micro,
                "precision_weighted": metrics.precision_weighted,
                "recall_weighted": metrics.recall_weighted,
            },
            "per_class": metrics.per_class,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Métricas exportadas en {output_path}")
