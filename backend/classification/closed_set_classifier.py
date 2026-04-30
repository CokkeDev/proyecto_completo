"""
ClosedSetClassifier: clasificación exclusivamente en el conjunto cerrado de TAXONOMY.

Ninguna categoría puede ser inventada o inferida fuera de las keys de TAXONOMY.
Si un proyecto no alcanza ningún umbral, se etiqueta como POR_CLASIFICAR.

Arquitectura en 3 capas (orden de prioridad):

  Capa 1 — Reglas Duras (reglas_semanticas):
    Aplica los patrones regex de cada subcategoría.
    Acepta si ≥ 1 patrón hace match.
    Confianza base: 0.60 + 0.08 por cada regla adicional (tope 0.96).

  Capa 2 — Keywords ponderadas:
    Score = peso_matched / (peso_total × 0.25).
    Acepta si score ≥ KW_THRESHOLD (0.30).
    Frases de ≥2 palabras pesan 2; palabras sueltas pesan 1.

  Capa 3 — Similitud Semántica (BAAI/bge-m3):
    Solo activa si Capas 1 y 2 no producen ningún match.
    Umbral conservador: SEMANTIC_THRESHOLD (0.70).
    Usa centroides positivos pre-calculados por categoría.

  Validación de Negativos (antes de confirmar cualquier match):
    Compara embedding del texto vs. centroide_positivo y centroide_negativo.
    Rechaza si sim_negativo > sim_positivo − NEGATIVE_MARGIN (0.05).
    Solo aplica si la subcategoría tiene ejemplos_negativos en la taxonomía.

Salida: ClosedSetResult con:
  primary   → match de mayor confianza
  secondary → otros matches de categorías distintas, dentro de MULTI_CAT_MARGIN
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import numpy as np

from backend.utils.text_normalizer import normalize_text
from backend.embeddings.encoder import BGEEncoder
from backend.taxonomy.manual_taxonomy import ManualTaxonomy
from backend.taxonomy.taxonomy_data import TAXONOMY
from .models import ClassificationMatch, ClassificationInput, ClosedSetResult

logger = logging.getLogger(__name__)


class ClosedSetClassifier:
    """
    Clasificador multi-label de conjunto cerrado.

    Parámetros de umbral ajustables (útil para experimentos):
      kw_threshold       : score mínimo de keywords para Capa 2 (default 0.30)
      semantic_threshold : similitud coseno mínima para Capa 3 (default 0.70)
      negative_margin    : margen de rechazo en validación de negativos (default 0.05)
      multi_cat_margin   : rango de confianza para categorías secundarias (default 0.15)
    """

    KW_THRESHOLD = 0.25
    SEMANTIC_THRESHOLD = 0.70
    NEGATIVE_MARGIN = 0.05
    MULTI_CAT_MARGIN = 0.15

    def __init__(
        self,
        encoder: Optional[BGEEncoder] = None,
        taxonomy: Optional[ManualTaxonomy] = None,
        kw_threshold: float = KW_THRESHOLD,
        semantic_threshold: float = SEMANTIC_THRESHOLD,
    ):
        self.taxonomy = taxonomy or ManualTaxonomy()
        self.encoder = encoder or BGEEncoder.get_instance()
        self.kw_threshold = kw_threshold
        self.semantic_threshold = semantic_threshold

        # (cat_code, sub_code) → list[re.Pattern]
        self._compiled_rules: dict[tuple[str, str], list[re.Pattern]] = {}
        # cat_code → np.ndarray (1024,)  — centroide positivo por categoría
        self._positive_centroids: dict[str, np.ndarray] = {}
        # (cat_code, sub_code) → np.ndarray (1024,) — centroide negativo
        self._negative_centroids: dict[tuple[str, str], np.ndarray] = {}

        self._compile_rules()
        self._build_centroids()

    # ── Inicialización ────────────────────────────────────────────────────────

    def _compile_rules(self):
        for cat_code, cat_data in TAXONOMY.items():
            for sub_code, sub_data in cat_data.get("subcategorias", {}).items():
                patterns: list[re.Pattern] = []
                for rule in sub_data.get("reglas_semanticas", []):
                    try:
                        patterns.append(re.compile(rule, re.IGNORECASE | re.UNICODE))
                    except re.error as e:
                        logger.warning(f"Regex inválido en {cat_code}/{sub_code}: {rule} — {e}")
                self._compiled_rules[(cat_code, sub_code)] = patterns

    def _build_centroids(self):
        """Pre-calcula centroides positivos y negativos para validación."""
        # Centroides positivos por categoría
        for cat_code in TAXONOMY:
            texts = self.taxonomy.get_prototype_texts(cat_code)
            if not texts:
                continue
            try:
                vecs = self.encoder.encode(texts, batch_size=16)
                centroid = vecs.mean(axis=0)
                norm = np.linalg.norm(centroid)
                self._positive_centroids[cat_code] = centroid / (norm + 1e-9)
            except Exception as e:
                logger.warning(f"Error calculando centroide positivo de {cat_code}: {e}")

        # Centroides negativos por subcategoría
        for cat_code, cat_data in TAXONOMY.items():
            for sub_code, sub_data in cat_data.get("subcategorias", {}).items():
                neg_texts = sub_data.get("ejemplos_negativos", [])
                if not neg_texts:
                    continue
                try:
                    vecs = self.encoder.encode(neg_texts, batch_size=16)
                    centroid = vecs.mean(axis=0)
                    norm = np.linalg.norm(centroid)
                    self._negative_centroids[(cat_code, sub_code)] = centroid / (norm + 1e-9)
                except Exception as e:
                    logger.warning(f"Error calculando centroide negativo de {cat_code}/{sub_code}: {e}")

        logger.info(
            f"ClosedSetClassifier listo: {len(self._positive_centroids)} centroides positivos, "
            f"{len(self._negative_centroids)} centroides negativos."
        )

    # ── Clasificación principal ───────────────────────────────────────────────

    def classify(self, inp: ClassificationInput, texto_completo: Optional[str] = None) -> ClosedSetResult:
        """
        Clasifica un proyecto de ley.

        Si texto_completo está disponible (PDF descargado), lo usa para clasificar
        y el texto_fuente del resultado indica 'documento_completo'.
        De lo contrario usa inp.full_text (SUMA + MATERIAS).
        """
        if texto_completo and len(texto_completo.split()) > len(inp.full_text.split()):
            text = texto_completo
            texto_fuente = "documento_completo"
        else:
            text = inp.full_text
            texto_fuente = "suma_materias"

        text_clean = " ".join(text.split())
        text_lower = normalize_text(text_clean)
        words_count = len(text_clean.split())

        # Calcular embedding del texto una sola vez (usado en Capa 3 y validación negativos)
        text_vec: Optional[np.ndarray] = self._encode_normalized(text_clean)

        # ── Capas 1 y 2: Reglas y Keywords ───────────────────────────────────
        sub_matches: dict[tuple[str, str], ClassificationMatch] = {}

        for cat_code, cat_data in TAXONOMY.items():
            for sub_code, sub_data in cat_data.get("subcategorias", {}).items():
                match = self._evaluate_rule_keyword(text_lower, cat_code, sub_code, sub_data)
                if match:
                    sub_matches[(cat_code, sub_code)] = match

        # ── Capa 3: Semántica (solo si Capas 1+2 no encontraron nada) ────────
        if not sub_matches and text_vec is not None:
            sub_matches = self._semantic_classify(text_vec, text_lower)

        if not sub_matches:
            return ClosedSetResult(
                boletin=inp.boletin,
                estado="POR_CLASIFICAR",
                primary=None,
                secondary=[],
                texto_fuente=texto_fuente,
                palabras_analizadas=words_count,
            )

        # ── Validación de negativos ───────────────────────────────────────────
        if text_vec is not None:
            validated = {
                key: match
                for key, match in sub_matches.items()
                if not self._fails_negative_check(text_vec, key[0], key[1])
            }
            # Si la validación rechaza todo, preservar los matches originales
            sub_matches = validated if validated else sub_matches

        # ── Selección de categoría principal y subcategorías ────────────────────
        # No agrupar por categoría: conservar todos los matches de subcategoría
        all_matches = sorted(
            sub_matches.values(),
            key=lambda x: x.confianza,
            reverse=True
        )

        primary = all_matches[0]

        # Mantener subcategorías adicionales, incluso si pertenecen a la misma categoría
        secondary = [
            m for m in all_matches[1:]
            if (
                m.subcategoria_id != primary.subcategoria_id
                and m.confianza >= 0.70
                and m.confianza >= primary.confianza - self.MULTI_CAT_MARGIN
            )
        ]

        # Evitar sobre-predicción extrema
        secondary = secondary[:4]

        return ClosedSetResult(
            boletin=inp.boletin,
            estado="clasificado",
            primary=primary,
            secondary=secondary,
            texto_fuente=texto_fuente,
            palabras_analizadas=words_count,
        )

    # ── Capa 1 y 2: Evaluación por reglas y keywords ─────────────────────────

    def _evaluate_rule_keyword(
        self,
        text_lower: str,
        cat_code: str,
        sub_code: str,
        sub_data: dict,
    ) -> Optional[ClassificationMatch]:
        """Evalúa Capa 1 (regex) y Capa 2 (keywords) para una subcategoría."""

        # Capa 1: Regex (versión más estricta)
        patterns = self._compiled_rules.get((cat_code, sub_code), [])
        if patterns:
            matched: list[str] = [p.pattern for p in patterns if p.search(text_lower)]
        
            # 🔥 EXIGIR MÁS EVIDENCIA
            if len(matched) >= 2:
                confidence = min(0.98, 0.70 + 0.10 * (len(matched) - 1))
                return ClassificationMatch(
                    categoria_id=cat_code,
                    categoria_label=TAXONOMY[cat_code]["label"],
                    subcategoria_id=sub_code,
                    subcategoria_label=sub_data["label"],
                    metodo_match="regla_regex",
                    confianza=round(confidence, 3),
                    matched_rules=matched,
                )

        # Capa 2: Keywords ponderadas
        keywords = sub_data.get("keywords", [])
        if keywords:
            kw_score = self._weighted_keyword_score(text_lower, keywords)
            if kw_score >= self.kw_threshold:
                return ClassificationMatch(
                    categoria_id=cat_code,
                    categoria_label=TAXONOMY[cat_code]["label"],
                    subcategoria_id=sub_code,
                    subcategoria_label=sub_data["label"],
                    metodo_match="keyword",
                    confianza=round(min(1.0, kw_score), 3),
                    matched_rules=[],
                )

        return None

    @staticmethod
    def _weighted_keyword_score(text_lower: str, keywords: list[str]) -> float:
        """
        Score ponderado de keywords.

        - Frases (≥2 palabras): peso 3, basta 1 aparición
        - Palabras sueltas: peso 1, exige al menos 2 apariciones
        - Usa regex para evitar falsos positivos por substrings
        """

        import re

        total_weight = sum(3 if len(kw.split()) >= 2 else 1 for kw in keywords)

        matched_weight = 0

        for kw in keywords:
            kw_norm = normalize_text(kw)
            pattern = r"\b" + re.escape(kw_norm) + r"\b"
            occurrences = len(re.findall(pattern, text_lower))

            if len(kw.split()) >= 2:
                # Frases → basta 1 aparición
                if occurrences >= 1:
                    matched_weight += 3
            else:
                # Palabras sueltas → exigir al menos 2 apariciones
                if occurrences >= 2:
                    matched_weight += 1

        return matched_weight / max(1, total_weight * 0.20)

    # ── Capa 3: Similitud semántica ───────────────────────────────────────────
    def _semantic_classify(
        self, text_vec: np.ndarray, text_lower: str
    ) -> dict[tuple[str, str], ClassificationMatch]:
        """Clasifica por similitud coseno vs. centroides positivos de categoría."""
        matches: dict[tuple[str, str], ClassificationMatch] = {}

        for cat_code, proto in self._positive_centroids.items():
            sim = float(np.dot(text_vec, proto))
            calibrated = (sim + 1.0) / 2.0  # mapear [-1,1] → [0,1]

            if calibrated >= self.semantic_threshold:
                best_sub = self._best_sub_by_keywords(text_lower, cat_code)
                if best_sub:
                    sub_data = TAXONOMY[cat_code]["subcategorias"][best_sub]
                    matches[(cat_code, best_sub)] = ClassificationMatch(
                        categoria_id=cat_code,
                        categoria_label=TAXONOMY[cat_code]["label"],
                        subcategoria_id=best_sub,
                        subcategoria_label=sub_data["label"],
                        metodo_match="semantica",
                        confianza=round(calibrated, 3),
                        matched_rules=[],
                    )

        return matches

    def _best_sub_by_keywords(self, text_lower: str, cat_code: str) -> Optional[str]:
        """Retorna la subcategoría con mayor overlap de keywords para asignar a un match semántico."""
        best_sub: Optional[str] = None
        best_score = -1.0

        for sub_code, sub_data in TAXONOMY[cat_code].get("subcategorias", {}).items():
            keywords = sub_data.get("keywords", [])
            if not keywords:
                continue
            score = self._weighted_keyword_score(text_lower, keywords)
            if score > best_score:
                best_score = score
                best_sub = sub_code

        if best_sub is None:
            # Fallback: primera subcategoría de la categoría
            subs = list(TAXONOMY[cat_code].get("subcategorias", {}).keys())
            return subs[0] if subs else None

        return best_sub

    # ── Validación de negativos ───────────────────────────────────────────────

    def _fails_negative_check(
        self, text_vec: np.ndarray, cat_code: str, sub_code: str
    ) -> bool:
        """
        Retorna True si el match debe ser rechazado.

        Lógica: rechazar si el texto es más parecido al centroide negativo
        que al centroide positivo, con un margen de NEGATIVE_MARGIN.
        """
        neg_centroid = self._negative_centroids.get((cat_code, sub_code))
        pos_centroid = self._positive_centroids.get(cat_code)

        if neg_centroid is None or pos_centroid is None:
            return False

        pos_sim = float(np.dot(text_vec, pos_centroid))
        neg_sim = float(np.dot(text_vec, neg_centroid))

        return neg_sim > pos_sim - self.NEGATIVE_MARGIN

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _encode_normalized(self, text: str) -> Optional[np.ndarray]:
        """Codifica el texto y normaliza a norma unitaria."""
        try:
            vec = self.encoder.encode_for_query(text)
            norm = np.linalg.norm(vec)
            if norm == 0:
                return None
            return vec / norm
        except Exception as e:
            logger.warning(f"Error al codificar texto: {e}")
            return None

    # ── Conversión a ClassificationResult (compatibilidad pipeline) ───────────

    def to_legacy_result(self, closed_result: ClosedSetResult):
        """
        Convierte ClosedSetResult al formato ClassificationResult legado
        para compatibilidad con el pipeline de ingesta existente.
        """
        from .models import ClassificationResult

        if closed_result.estado == "POR_CLASIFICAR" or closed_result.primary is None:
            return ClassificationResult(
                boletin=closed_result.boletin,
                primary_category="POR_CLASIFICAR",
                primary_category_display="Por Clasificar — Revisión Manual",
                subcategories=[],
                labels=[],
                confidence=0.0,
                explanation="El proyecto no superó ningún umbral de clasificación.",
                origin="closed_set",
            )

        p = closed_result.primary
        secondary_cats = [m.categoria_id for m in closed_result.secondary]
        secondary_subs = [m.subcategoria_id for m in closed_result.secondary]

        # Etiquetas desde subcategoría principal
        etiquetas = (
            TAXONOMY.get(p.categoria_id, {})
            .get("subcategorias", {})
            .get(p.subcategoria_id, {})
            .get("etiquetas", [])
        )

        matched_rules_str = "; ".join(p.matched_rules[:3]) if p.matched_rules else ""
        explanation = (
            f"Clasificado como '{p.categoria_label}' → '{p.subcategoria_label}' "
            f"(método={p.metodo_match}, confianza={p.confianza:.2f}, "
            f"fuente={closed_result.texto_fuente})."
        )
        if matched_rules_str:
            explanation += f" Patrones activos: {matched_rules_str}."
        if closed_result.secondary:
            sec_labels = ", ".join(f"'{m.categoria_label}'" for m in closed_result.secondary)
            explanation += f" Categorías secundarias: {sec_labels}."

        return ClassificationResult(
            boletin=closed_result.boletin,
            primary_category=p.categoria_id,
            primary_category_display=p.categoria_label,
            subcategories=[p.subcategoria_id] + secondary_subs,
            labels=etiquetas[:5],
            confidence=p.confianza,
            explanation=explanation,
            origin=p.metodo_match,
        )
