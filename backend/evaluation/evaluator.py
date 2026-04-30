"""
SystemEvaluator: orquesta la evaluación completa del sistema.

Evalúa dos métodos y genera benchmarking comparativo:
  1. RuleBasedClassifier
  2. EmbeddingClassifier
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from backend.evaluation.metrics import MetricsCalculator, BenchmarkResult
from backend.evaluation.ground_truth import GroundTruthLoader
from backend.classification.rule_classifier import RuleBasedClassifier
from backend.classification.embedding_classifier import EmbeddingClassifier

logger = logging.getLogger(__name__)
RESULTS_DIR = Path(__file__).parent / "results"


class SystemEvaluator:
    """
    Evaluador completo del sistema de clasificación.

    Ejecuta los clasificadores sobre el ground truth y genera:
      - Métricas por método
      - Reporte de benchmarking comparativo
      - Exportación JSON para reproducibilidad
    """

    def __init__(
        self,
        gt_loader: Optional[GroundTruthLoader] = None,
        threshold: float = 0.45,
    ):
        self.gt_loader = gt_loader or GroundTruthLoader()
        self.threshold = threshold
        self.calc = MetricsCalculator()

    # ── Evaluación completa ───────────────────────────────────────────────────
    def run_full_evaluation(self) -> dict:
        """
        Ejecuta evaluación de los métodos configurados y retorna reporte JSON completo.
        """
        entries = self.gt_loader.load()
        if len(entries) < 10:
            return {"error": "Ground truth insuficiente (mínimo 10 entradas)."}

        all_classes = self.gt_loader.get_all_classes()
        y_true = self.gt_loader.get_y_true()

        logger.info(f"Evaluando {len(entries)} entradas con {len(all_classes)} clases.")

        # ── Método 1: Reglas ──────────────────────────────────────────────────
        rule_clf = RuleBasedClassifier()
        y_pred_rules = self._predict_rules(entries, rule_clf)
        metrics_rules = self.calc.classification_metrics(y_true, y_pred_rules, all_classes)

        # ── Método 2: Embeddings ──────────────────────────────────────────────
        emb_clf = EmbeddingClassifier()
        y_pred_emb = self._predict_embeddings(entries, emb_clf)
        metrics_emb = self.calc.classification_metrics(y_true, y_pred_emb, all_classes)

        # ── Benchmarking ──────────────────────────────────────────────────────
        benchmark_results = [
            BenchmarkResult(method="rules", classification=metrics_rules),
            BenchmarkResult(method="embeddings", classification=metrics_emb),
        ]

        report = self.calc.benchmark_report(
            benchmark_results,
            output_path=RESULTS_DIR / "benchmark_report.json",
        )

        # Exportar métricas individuales
        RESULTS_DIR.mkdir(exist_ok=True)
        for method, metrics in [
            ("rules", metrics_rules),
            ("embeddings", metrics_emb),
        ]:
            self.calc.export_metrics(
                metrics,
                RESULTS_DIR / f"metrics_{method}.json",
                method_name=method,
            )

        # Stats del ground truth
        gt_stats = self.gt_loader.stats_report()

        full_report = {
            "ground_truth_stats": gt_stats,
            "methods": {
                "rules": self._metrics_to_dict(metrics_rules),
                "embeddings": self._metrics_to_dict(metrics_emb),
            },
            "benchmark": report,
        }

        with open(RESULTS_DIR / "full_evaluation.json", "w", encoding="utf-8") as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)

        logger.info("Evaluación completa. Resultados en evaluation/results/")
        return full_report

    # ── Predictores ──────────────────────────────────────────────────────────
    def _predict_rules(self, entries, clf: RuleBasedClassifier) -> list[list[str]]:
        results = []
        for e in entries:
            scores = clf.predict(f"{e.suma} {e.materias or ''}")
            labels = [
                cat for cat, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if sc >= self.threshold
            ]
            if not labels and scores:
                labels = [max(scores, key=scores.get)]
            results.append(labels[:5])
        return results

    def _predict_embeddings(self, entries, clf: EmbeddingClassifier) -> list[list[str]]:
        results = []
        for e in entries:
            scores = clf.predict(f"{e.suma} {e.materias or ''}")
            labels = [
                cat for cat, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True)
                if sc >= self.threshold
            ]
            if not labels and scores:
                labels = [max(scores, key=scores.get)]
            results.append(labels[:5])
        return results

    @staticmethod
    def _metrics_to_dict(m) -> dict:
        return {
            "accuracy_subset": round(m.accuracy_subset, 4),
            "hamming_loss": round(m.hamming_loss, 4),
            "f1_weighted": round(m.f1_weighted, 4),
            "f1_macro": round(m.f1_macro, 4),
            "f1_micro": round(m.f1_micro, 4),
            "precision_weighted": round(m.precision_weighted, 4),
            "recall_weighted": round(m.recall_weighted, 4),
            "per_class": m.per_class,
        }
