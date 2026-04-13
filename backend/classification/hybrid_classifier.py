"""
HybridClassifier: combina RuleBasedClassifier + EmbeddingClassifier.

Score híbrido = α * score_rules + (1-α) * score_embeddings

Salida: ClassificationResult con categoría principal, subcategorías,
etiquetas, scores, explicación y origen.
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.config import settings
from backend.taxonomy.manual_taxonomy import ManualTaxonomy
from backend.taxonomy.taxonomy_data import TAXONOMY
from .models import ClassificationInput, ClassificationResult, LabelScore
from .rule_classifier import RuleBasedClassifier
from .embedding_classifier import EmbeddingClassifier

logger = logging.getLogger(__name__)


class HybridClassifier:
    """
    Clasificador híbrido multi-label.

    Parámetros clave:
      rule_weight           : peso de las reglas (default 0.40)
      embedding_weight      : peso de los embeddings (default 0.60)
      classification_threshold : umbral mínimo para asignar etiqueta (default 0.45)
      max_labels            : máximo de etiquetas por documento
    """

    def __init__(
        self,
        rule_weight: float = settings.rule_weight,
        embedding_weight: float = settings.embedding_weight,
        threshold: float = settings.classification_threshold,
        max_labels: int = settings.max_labels,
        taxonomy: Optional[ManualTaxonomy] = None,
    ):
        self.rule_weight = rule_weight
        self.embedding_weight = embedding_weight
        self.threshold = threshold
        self.max_labels = max_labels
        self.taxonomy = taxonomy or ManualTaxonomy()

        self.rule_clf = RuleBasedClassifier(taxonomy=self.taxonomy)
        self.emb_clf = EmbeddingClassifier(taxonomy=self.taxonomy)

    # ── Clasificación principal ───────────────────────────────────────────────
    def classify(self, inp: ClassificationInput) -> ClassificationResult:
        """
        Clasifica un proyecto de ley.

        Returns ClassificationResult con:
          - primary_category  : código categoría con mayor score
          - subcategories     : subcategorías con score > threshold
          - labels            : etiquetas de subcategorías
          - top_scores        : lista de LabelScore ordenada desc
          - confidence        : score de la categoría principal
          - explanation       : texto explicativo
          - origin            : 'hybrid'
          - rule_scores / embedding_scores / hybrid_scores
        """
        text = inp.full_text

        # 1. Scores por componente
        rule_scores = self.rule_clf.predict(text)
        emb_scores = self.emb_clf.predict(text)

        # 2. Combinar
        hybrid_scores = self._combine(rule_scores, emb_scores)

        # 3. Filtrar por umbral y ordenar
        above = {
            cat: score
            for cat, score in hybrid_scores.items()
            if score >= self.threshold
        }
        sorted_cats = sorted(above, key=above.get, reverse=True)

        # Categoría principal: la de mayor score (aunque no supere umbral)
        primary = max(hybrid_scores, key=hybrid_scores.get)
        primary_score = hybrid_scores[primary]

        # Si ninguna supera el umbral usamos la mejor de todas
        if not sorted_cats:
            sorted_cats = [primary]

        selected = sorted_cats[: self.max_labels]

        # 4. Subcategorías de la categoría principal
        subcats = self._get_subcategories(text, primary)

        # 5. Etiquetas
        labels = self._get_labels(text, primary, subcats)

        # 6. LabelScore list
        top_scores = [
            LabelScore(
                label=cat,
                label_display=self.taxonomy.get_category_label(cat),
                score=round(hybrid_scores[cat], 4),
                origin=self._determine_origin(rule_scores.get(cat, 0), emb_scores.get(cat, 0)),
            )
            for cat in sorted(hybrid_scores, key=hybrid_scores.get, reverse=True)[:8]
        ]

        # 7. Explicación
        explanation = self.taxonomy.generate_explanation(
            text=text,
            cat_code=primary,
            rule_score=rule_scores.get(primary, 0),
            emb_score=emb_scores.get(primary, 0),
            hybrid_score=primary_score,
        )

        origin = self._determine_origin(
            rule_scores.get(primary, 0), emb_scores.get(primary, 0)
        )

        return ClassificationResult(
            boletin=inp.boletin,
            primary_category=primary,
            primary_category_display=self.taxonomy.get_category_label(primary),
            subcategories=subcats,
            labels=labels,
            top_scores=top_scores,
            confidence=round(primary_score, 4),
            explanation=explanation,
            origin=origin,
            rule_scores={k: round(v, 4) for k, v in rule_scores.items()},
            embedding_scores={k: round(v, 4) for k, v in emb_scores.items()},
            hybrid_scores={k: round(v, 4) for k, v in hybrid_scores.items()},
        )

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _combine(
        self, rule: dict[str, float], emb: dict[str, float]
    ) -> dict[str, float]:
        all_cats = set(rule) | set(emb)
        return {
            cat: self.rule_weight * rule.get(cat, 0.0)
            + self.embedding_weight * emb.get(cat, 0.0)
            for cat in all_cats
        }

    def _get_subcategories(self, text: str, cat_code: str) -> list[str]:
        """Retorna subcategorías de `cat_code` con al menos 1 match de reglas."""
        _, sub_scores = self.rule_clf.predict_with_subcategories(text)
        subs = sub_scores.get(cat_code, {})
        # Filtrar con umbral más bajo (0.2) ya que es más granular
        return [s for s, sc in sorted(subs.items(), key=lambda x: x[1], reverse=True)
                if sc >= 0.2][: 3]

    def _get_labels(self, text: str, cat_code: str, subcats: list[str]) -> list[str]:
        """Extrae etiquetas de las subcategorías activas."""
        labels: list[str] = []
        for sub_code in subcats:
            sub_data = (
                TAXONOMY.get(cat_code, {})
                .get("subcategorias", {})
                .get(sub_code, {})
            )
            etiquetas = sub_data.get("etiquetas", [])
            # Verificar que la etiqueta es relevante para el texto
            for et in etiquetas[:3]:
                if et.lower().replace("_", " ") in text.lower() or len(labels) < 2:
                    labels.append(et)
        return list(dict.fromkeys(labels))[: self.max_labels]  # dedup

    @staticmethod
    def _determine_origin(rule_score: float, emb_score: float) -> str:
        if rule_score >= 0.3 and emb_score >= 0.4:
            return "hybrid"
        if rule_score >= 0.3:
            return "rules"
        return "embeddings"
