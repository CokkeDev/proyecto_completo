"""
ManualTaxonomy: acceso estructurado a TAXONOMY con soporte de:
  - búsqueda por keyword
  - validación de códigos
  - generación de textos prototipo para embedding classifier
  - reglas semánticas compiladas
"""
from __future__ import annotations

import re
import logging
from functools import cached_property
from typing import Optional

from .taxonomy_data import TAXONOMY

logger = logging.getLogger(__name__)


class ManualTaxonomy:
    """
    Interfaz de acceso sobre el diccionario TAXONOMY.

    Compila las reglas semánticas a expresiones regulares al inicializar.
    """

    def __init__(self):
        self._compiled_rules: dict[str, list[re.Pattern]] = {}
        self._sub_compiled_rules: dict[tuple[str, str], list[re.Pattern]] = {}
        self._compile_all_rules()

    # ── Compilación de reglas ─────────────────────────────────────────────────
    def _compile_all_rules(self):
        for cat_code, cat_data in TAXONOMY.items():
            for sub_code, sub_data in cat_data["subcategorias"].items():
                patterns = []
                for rule in sub_data.get("reglas_semanticas", []):
                    try:
                        patterns.append(re.compile(rule, re.IGNORECASE | re.UNICODE))
                    except re.error as e:
                        logger.warning(f"Regex inválido en {cat_code}/{sub_code}: {rule} — {e}")
                self._sub_compiled_rules[(cat_code, sub_code)] = patterns

    # ── Consultas básicas ─────────────────────────────────────────────────────
    def get_categories(self) -> list[str]:
        return list(TAXONOMY.keys())

    def get_category_label(self, code: str) -> str:
        return TAXONOMY.get(code, {}).get("label", code)

    def get_subcategories(self, cat_code: str) -> list[str]:
        return list(TAXONOMY.get(cat_code, {}).get("subcategorias", {}).keys())

    def get_subcategory_label(self, cat_code: str, sub_code: str) -> str:
        subs = TAXONOMY.get(cat_code, {}).get("subcategorias", {})
        return subs.get(sub_code, {}).get("label", sub_code)

    def is_valid_category(self, code: str) -> bool:
        return code in TAXONOMY

    # ── Rule matching ─────────────────────────────────────────────────────────
    def match_rules(self, text: str) -> dict[str, float]:
        """
        Aplica todas las reglas semánticas sobre `text`.

        Devuelve dict {cat_code: score} donde score ∈ [0, 1].

        Algoritmo:
          - Para cada subcategoría: cuenta cuántas reglas hacen match / total_reglas
          - El score de la categoría es el max de sus subcategorías
        """
        text_lower = text.lower()
        cat_scores: dict[str, float] = {c: 0.0 for c in TAXONOMY}

        for (cat_code, sub_code), patterns in self._sub_compiled_rules.items():
            if not patterns:
                continue
            hits = sum(1 for p in patterns if p.search(text_lower))
            sub_score = hits / len(patterns)
            if sub_score > cat_scores[cat_code]:
                cat_scores[cat_code] = sub_score

        return cat_scores

    def match_rules_detailed(self, text: str) -> dict[str, dict[str, float]]:
        """
        Como match_rules pero devuelve {cat: {sub: score}}.
        Útil para generar explicaciones.
        """
        result: dict[str, dict[str, float]] = {}
        text_lower = text.lower()

        for (cat_code, sub_code), patterns in self._sub_compiled_rules.items():
            if not patterns:
                continue
            hits = sum(1 for p in patterns if p.search(text_lower))
            sub_score = hits / len(patterns)
            if sub_score > 0:
                result.setdefault(cat_code, {})[sub_code] = sub_score

        return result

    # ── Keyword matching ──────────────────────────────────────────────────────
    def keyword_score(self, text: str, cat_code: str) -> float:
        """
        Score basado en overlap de keywords.
        Devuelve fracción de keywords encontradas en text (deduplicado).
        """
        cat = TAXONOMY.get(cat_code)
        if not cat:
            return 0.0
        keywords = cat.get("keywords", [])
        if not keywords:
            return 0.0

        text_lower = text.lower()
        hits = sum(1 for kw in keywords if kw.lower() in text_lower)
        return min(1.0, hits / max(1, len(keywords) * 0.2))  # normalizado

    # ── Textos prototipo ──────────────────────────────────────────────────────
    def get_prototype_texts(self, cat_code: str) -> list[str]:
        """Retorna los textos prototipo de una categoría (para embedding classifier)."""
        cat = TAXONOMY.get(cat_code, {})
        texts = list(cat.get("prototype_texts", []))
        for sub in cat.get("subcategorias", {}).values():
            texts.extend(sub.get("ejemplos_positivos", []))
        return texts

    def get_all_prototype_texts(self) -> dict[str, list[str]]:
        return {code: self.get_prototype_texts(code) for code in TAXONOMY}

    # ── Explicación ──────────────────────────────────────────────────────────
    def generate_explanation(
        self,
        text: str,
        cat_code: str,
        rule_score: float,
        emb_score: float,
        hybrid_score: float,
    ) -> str:
        """Genera texto explicativo de la clasificación."""
        cat_label = self.get_category_label(cat_code)
        detailed = self.match_rules_detailed(text)
        matched_subs = detailed.get(cat_code, {})

        parts = [f"Clasificado como '{cat_label}' (score={hybrid_score:.2f})."]

        if rule_score >= 0.3:
            if matched_subs:
                best_sub = max(matched_subs, key=matched_subs.get)
                sub_label = self.get_subcategory_label(cat_code, best_sub)
                parts.append(
                    f"Reglas semánticas identificaron coincidencia con subcategoría "
                    f"'{sub_label}' (score_reglas={rule_score:.2f})."
                )
            else:
                parts.append(f"Reglas semánticas: score={rule_score:.2f}.")

        if emb_score >= 0.4:
            parts.append(
                f"Similitud semántica (BAAI/bge-m3) con prototipos de la categoría: "
                f"{emb_score:.2f}."
            )

        return " ".join(parts)
