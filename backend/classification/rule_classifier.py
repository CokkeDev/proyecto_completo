"""
RuleBasedClassifier: clasificación por reglas semánticas (regex + keywords).

Produce scores por categoría para cada texto analizado.
"""
from __future__ import annotations

import logging
from backend.taxonomy.manual_taxonomy import ManualTaxonomy

logger = logging.getLogger(__name__)

_TAXONOMY = ManualTaxonomy()


class RuleBasedClassifier:
    """
    Clasifica texto usando las reglas semánticas y keywords de la taxonomía manual.

    Score por categoría = promedio ponderado de:
      - rule_score  (60%): fracción de reglas regex que hacen match
      - kw_score    (40%): fracción de keywords encontradas
    """

    def __init__(self, taxonomy: ManualTaxonomy | None = None):
        self.taxonomy = taxonomy or _TAXONOMY

    def predict(self, text: str) -> dict[str, float]:
        """
        Devuelve {cat_code: score} ∈ [0, 1] para todas las categorías.
        """
        rule_scores = self.taxonomy.match_rules(text)
        scores: dict[str, float] = {}

        for cat_code in self.taxonomy.get_categories():
            kw_score = self.taxonomy.keyword_score(text, cat_code)
            r_score = rule_scores.get(cat_code, 0.0)
            combined = 0.6 * r_score + 0.4 * kw_score
            scores[cat_code] = round(combined, 4)

        return scores

    def predict_with_subcategories(
        self, text: str
    ) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
        """
        Retorna (cat_scores, sub_scores).
        sub_scores = {cat: {sub: score}}
        """
        cat_scores = self.predict(text)
        sub_scores = self.taxonomy.match_rules_detailed(text)
        return cat_scores, sub_scores
