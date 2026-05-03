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
from backend.evaluation.ground_truth import GroundTruthLoader, GT_FILE
from backend.evaluation.eval_hypotheses import (
    evaluate_h0_hybrid,
    evaluate_h1_semantic_search,
)
from backend.classification.rule_classifier import RuleBasedClassifier
from backend.classification.embedding_classifier import EmbeddingClassifier
from backend.taxonomy.manual_taxonomy import ManualTaxonomy

logger = logging.getLogger(__name__)
RESULTS_DIR = Path(__file__).parent / "results"


def _extract_verdict(hyp_result: Optional[dict]) -> dict:
    """Extrae un resumen de veredicto compacto desde el resultado de una hipótesis."""
    if not hyp_result or "error" in (hyp_result or {}):
        return {"verdict": "ERROR", "reason": (hyp_result or {}).get("error")}
    test = hyp_result.get("hypothesis_test", {})
    return {
        "verdict": test.get("verdict", "DESCONOCIDO"),
        "passed": test.get("passed", False),
    }


def _detect_label_level(
    all_classes: list[str], taxonomy: ManualTaxonomy
) -> str:
    """
    Decide si el ground truth está anotado a nivel 'category' o 'subcategory'
    contando coincidencias con los códigos válidos de la taxonomía.
    En caso de empate o ambigüedad, prefiere 'subcategory' porque es lo más
    informativo y lo que el sistema produce como salida final.
    """
    cat_codes = set(taxonomy.get_categories())
    sub_codes = set(taxonomy.get_all_subcategory_codes())
    n_cat = sum(1 for c in all_classes if c in cat_codes)
    n_sub = sum(1 for c in all_classes if c in sub_codes)
    logger.info(
        f"GT: {len(all_classes)} clases distintas → "
        f"coincidencias con categorías={n_cat}, con subcategorías={n_sub}"
    )
    if n_sub >= n_cat and n_sub > 0:
        return "subcategory"
    if n_cat > 0:
        return "category"
    # Ground truth no coincide con la taxonomía actual
    logger.warning(
        "Ninguna clase del GT coincide con la taxonomía. Asumiendo 'subcategory'."
    )
    return "subcategory"


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
        taxonomy: Optional[ManualTaxonomy] = None,
    ):
        self.gt_loader = gt_loader or GroundTruthLoader()
        self.threshold = threshold
        self.calc = MetricsCalculator()
        self.taxonomy = taxonomy or ManualTaxonomy()
        # 'category' o 'subcategory'. Se setea en run_full_evaluation.
        self._label_level: str = "subcategory"

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

        # Detectar el nivel taxonómico del GT (categoría vs subcategoría)
        # para usar el método de predicción correcto en cada clasificador.
        self._label_level = _detect_label_level(all_classes, self.taxonomy)
        logger.info(
            f"Evaluando {len(entries)} entradas con {len(all_classes)} clases "
            f"a nivel '{self._label_level}'."
        )

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

        # ── Evaluación de hipótesis (H0: híbrido > 0.70 F1; H1: Qdrant <5s y >0.75 cos)
        hypotheses_report: dict = {}
        try:
            logger.info("Evaluando H0 (modelo híbrido reglas + BGE-M3)...")
            # Evaluamos H0 a nivel categoría principal por defecto. La métrica
            # de subcategoría queda reportada como complemento. Se puede
            # cambiar a "subcategory" o "any" si se prefiere otra interpretación.
            h0 = evaluate_h0_hybrid(gt_path=GT_FILE, eval_level="primary")
            hypotheses_report["h0"] = h0
        except Exception as e:
            logger.error(f"H0 falló: {e}")
            hypotheses_report["h0"] = {"error": str(e)}

        try:
            logger.info("Evaluando H1 (búsqueda semántica con Qdrant)...")
            h1 = evaluate_h1_semantic_search(gt_path=GT_FILE)
            hypotheses_report["h1"] = h1
        except Exception as e:
            logger.error(f"H1 falló: {e}")
            hypotheses_report["h1"] = {"error": str(e)}

        # Resumen compacto de veredictos para que sea fácil de leer arriba del JSON
        verdicts = {
            "H0": _extract_verdict(hypotheses_report.get("h0")),
            "H1": _extract_verdict(hypotheses_report.get("h1")),
        }

        full_report = {
            "ground_truth_stats": gt_stats,
            "label_level": self._label_level,
            "threshold": self.threshold,
            "verdicts": verdicts,
            "methods": {
                "rules": self._metrics_to_dict(metrics_rules),
                "embeddings": self._metrics_to_dict(metrics_emb),
            },
            "benchmark": report,
            "hypotheses": hypotheses_report,
        }

        with open(RESULTS_DIR / "full_evaluation.json", "w", encoding="utf-8") as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Evaluación completa. H0={verdicts['H0']} | H1={verdicts['H1']}. "
            f"Resultados en {RESULTS_DIR}/"
        )
        return full_report

    # ── Predictores ──────────────────────────────────────────────────────────
    def _scores_to_labels(self, scores: dict[str, float]) -> list[str]:
        """Convierte un dict {label: score} en una lista multi-label aplicando
        el threshold; si nada pasa el umbral, devuelve la etiqueta top."""
        if not scores:
            return []
        labels = [
            lbl for lbl, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if sc >= self.threshold
        ]
        if not labels:
            labels = [max(scores, key=scores.get)]
        return labels[:5]

    def _predict_rules(self, entries, clf: RuleBasedClassifier) -> list[list[str]]:
        results = []
        for e in entries:
            text = f"{e.suma} {e.materias or ''}"
            if self._label_level == "subcategory":
                scores = clf.predict_subcategories(text)
            else:
                scores = clf.predict(text)
            results.append(self._scores_to_labels(scores))
        return results

    def _predict_embeddings(self, entries, clf: EmbeddingClassifier) -> list[list[str]]:
        results = []
        for e in entries:
            text = f"{e.suma} {e.materias or ''}"
            if self._label_level == "subcategory":
                scores = clf.predict_subcategories(text)
            else:
                scores = clf.predict(text)
            results.append(self._scores_to_labels(scores))
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
