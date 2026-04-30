"""
RuleBasedClassifier: clasificación por reglas semánticas (regex + keywords).

Versión ajustada para mejorar H0:
- Reduce sobrepredicción de TECNOLOGIA_INNOVACION.
- Refuerza categorías débiles detectadas en evaluación.
- Aplica prioridades jerárquicas por dominio.
- Mantiene compatibilidad con ManualTaxonomy.
"""
from __future__ import annotations

import logging
import re
import unicodedata

from backend.taxonomy.manual_taxonomy import ManualTaxonomy

logger = logging.getLogger(__name__)

_TAXONOMY = ManualTaxonomy()


def _normalize(text: str) -> str:
    """Normaliza texto para búsquedas robustas sin depender de acentos."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


class RuleBasedClassifier:
    """
    Clasifica texto usando reglas semánticas y keywords de la taxonomía manual.

    Score base por categoría:
      - rule_score  (60%): fracción de reglas regex que hacen match
      - kw_score    (40%): fracción de keywords encontradas

    Luego se aplica post-procesamiento de dominio para corregir errores observados:
      - TECNOLOGIA_INNOVACION estaba sobreprediciendo por términos demasiado generales.
      - Algunas categorías principales requerían boosts por patrones jurídicos fuertes.
    """

    def __init__(self, taxonomy: ManualTaxonomy | None = None):
        self.taxonomy = taxonomy or _TAXONOMY

    def predict(self, text: str) -> dict[str, float]:
        """
        Devuelve {cat_code: score} para todas las categorías principales.
        """
        rule_scores = self.taxonomy.match_rules(text)
        scores: dict[str, float] = {}

        for cat_code in self.taxonomy.get_categories():
            kw_score = self.taxonomy.keyword_score(text, cat_code)
            r_score = rule_scores.get(cat_code, 0.0)
            combined = 0.6 * r_score + 0.4 * kw_score
            scores[cat_code] = float(combined)

        scores = self._apply_domain_adjustments(text, scores)
        return {cat: round(max(0.0, min(score, 1.0)), 4) for cat, score in scores.items()}

    def _apply_domain_adjustments(self, text: str, scores: dict[str, float]) -> dict[str, float]:
        """
        Ajustes de calibración derivados del análisis de errores.
        Estos boosts/penalizaciones ayudan a mejorar precisión y recall sin romper la taxonomía.
        """
        t = _normalize(text)

        # ─────────────────────────────────────────────────────────────
        # 1) Reducir sobrepredicción de TECNOLOGIA_INNOVACION
        # Antes: términos genéricos como "digital", "sistema" o "datos" podían absorber casos.
        # Ahora tecnología solo se refuerza con señales tecnológicas fuertes.
        # ─────────────────────────────────────────────────────────────
        strong_tech = _has_any(t, [
            r"inteligencia\s+artificial|\bia\b|machine\s+learning",
            r"algoritm(o|os|ico|icos)|sistemas?\s+algoritmic",
            r"ciberseguridad|delitos?\s+informaticos?|seguridad\s+informatica",
            r"hackeo|hacking|ransomware|malware|phishing",
            r"telecomunicaciones|\bsubtel\b|fibra\s+optica|\b5g\b|banda\s+ancha",
            r"blockchain|criptomoneda|activos?\s+digitales?|fintech",
            r"reconocimiento\s+facial|deepfake|automatizacion",
        ])

        weak_tech_only = _has_any(t, [r"\bdigital\b", r"\btecnologia\b", r"\bsistema\b", r"\bdatos\b"])

        if strong_tech:
            scores["TECNOLOGIA_INNOVACION"] = scores.get("TECNOLOGIA_INNOVACION", 0.0) + 0.28
        elif weak_tech_only:
            # Si no hay señal tecnológica fuerte, se limita tecnología para evitar falsos positivos.
            scores["TECNOLOGIA_INNOVACION"] = min(scores.get("TECNOLOGIA_INNOVACION", 0.0), 0.22)
        else:
            scores["TECNOLOGIA_INNOVACION"] = min(scores.get("TECNOLOGIA_INNOVACION", 0.0), 0.18)

        # ─────────────────────────────────────────────────────────────
        # 2) Refuerzos por categoría principal débil
        # ─────────────────────────────────────────────────────────────
        if _has_any(t, [
            r"vida\s+privada|intimidad|honra|derecho\s+a\s+la\s+imagen",
            r"derechos?\s+fundamentales?|derechos?\s+humanos|garantias?\s+constitucionales?",
            r"libertad\s+de\s+(expresion|prensa|informacion|reunion|asociacion)",
            r"igualdad\s+ante\s+la\s+ley|no\s+discriminacion|discriminacion\s+arbitraria",
            r"ninos?|ninas?|adolescentes?|infancia|menores?\s+de\s+edad",
        ]):
            scores["DERECHOS_FUNDAMENTALES"] = scores.get("DERECHOS_FUNDAMENTALES", 0.0) + 0.25
            # Evita que privacidad/datos personales se vaya siempre a tecnología.
            if not strong_tech:
                scores["TECNOLOGIA_INNOVACION"] = min(scores.get("TECNOLOGIA_INNOVACION", 0.0), 0.25)

        if _has_any(t, [
            r"reforma\s+constitucional|carta\s+fundamental|constitucion\s+politica",
            r"iniciativa\s+exclusiva\s+del\s+presidente|proceso\s+legislativo",
            r"acceso\s+a\s+la\s+informacion\s+publica|transparencia|probidad|lobby",
            r"gobiernos?\s+regionales?|municipalidad|municipio|funcionarios?\s+publicos?",
            r"plantas?\s+de\s+personal|estatuto\s+administrativo|contraloria",
        ]):
            scores["INSTITUCIONALIDAD_ESTADO"] = scores.get("INSTITUCIONALIDAD_ESTADO", 0.0) + 0.20

        if _has_any(t, [
            r"proteccion\s+de\s+los\s+derechos\s+del\s+consumidor|ley\s+19\.496",
            r"consumidor|proveedor|boleta|factura|transaccion\s+comercial",
            r"impuesto|tributacion|\biva\b|renta|\bsii\b|sistema\s+financiero",
            r"libre\s+competencia|colusion|\bfne\b|\btdlc\b|mercado",
        ]):
            scores["ECONOMIA_FINANZAS"] = scores.get("ECONOMIA_FINANZAS", 0.0) + 0.22

        if _has_any(t, [
            r"codigo\s+del\s+trabajo|trabajador(es)?|empleador|permiso\s+laboral|fuero\s+laboral",
            r"contrato\s+de\s+trabajo|despido|remuneracion|jornada\s+(laboral|de\s+trabajo)",
            r"sindicato|negociacion\s+colectiva|huelga|seguridad\s+social|afp|pension",
        ]):
            scores["DERECHO_LABORAL_EMPLEO"] = scores.get("DERECHO_LABORAL_EMPLEO", 0.0) + 0.22

        if _has_any(t, [
            r"educacion|colegio|escuela|liceo|establecimiento\s+educacional",
            r"universidad|educacion\s+superior|instituto\s+profesional|\bcft\b",
            r"docente|profesor(es)?|estudiante(s)?|alumno(s)?|mineduc",
            r"subvencion\s+escolar|admision\s+escolar|\bcae\b|gratuidad|beca",
        ]):
            scores["EDUCACION"] = scores.get("EDUCACION", 0.0) + 0.22
            # Si el contexto es educativo, no dejar que "docente/trabajador" derive automáticamente en laboral.
            if _has_any(t, [r"docente|profesor(es)?|establecimiento\s+educacional|educacion"]):
                scores["DERECHO_LABORAL_EMPLEO"] = max(0.0, scores.get("DERECHO_LABORAL_EMPLEO", 0.0) - 0.08)

        if _has_any(t, [
            r"biodiversidad|servicio\s+de\s+biodiversidad|areas?\s+protegidas?|sitios?\s+prioritarios?",
            r"medio\s+ambiente|ambiental|ecosistema|flora|fauna|humedal|conservacion",
            r"cambio\s+climatico|emisiones|gases?\s+de\s+efecto\s+invernadero|carbono",
            r"recursos?\s+hidricos?|codigo\s+de\s+aguas|glaciar|sequia|contaminacion|residuos?",
        ]):
            scores["MEDIO_AMBIENTE"] = scores.get("MEDIO_AMBIENTE", 0.0) + 0.25

        if _has_any(t, [
            r"salud\s+publica|hospital|paciente|fonasa|isapre|ges|auge",
            r"medicamento|farmacia|farmaco|receta\s+medica|salud\s+mental",
            r"trasplante|donacion\s+de\s+organos",
            r"lista\s+de\s+espera\s+(quirurgica|medica|hospitalaria)",
            r"paciente(s)?|prestacion(es)?\s+de\s+salud",  
            r"pandemia|covid|vacuna|emergencia\s+sanitaria",
        ]):
            scores["SALUD_PUBLICA"] = scores.get("SALUD_PUBLICA", 0.0) + 0.24

        if _has_any(t, [
            r"codigo\s+penal|codigo\s+procesal\s+penal|delito|pena|sancion\s+penal",
            r"narcotrafico|crimen\s+organizado|lavado\s+de\s+activos|armas?\s+de\s+fuego",
            r"carabineros|\bpdi\b|gendarmeria|ministerio\s+publico|prision\s+preventiva",
            r"violencia\s+intrafamiliar|femicidio|acoso\s+sexual|abuso\s+sexual",
        ]):
            scores["SEGURIDAD_JUSTICIA"] = scores.get("SEGURIDAD_JUSTICIA", 0.0) + 0.23

        if _has_any(t, [
            r"ley\s+18\.290|licencia\s+de\s+conducir|transito\s+vial",
            r"transporte\s+publico|transporte\s+remunerado\s+de\s+pasajeros",
            r"vehiculo(s)?\s+(motorizados?|electricos?)|motocicleta(s)?",
            r"transporte\s+publico|pasajeros?|conductores?|motocicleta|buses?|taxis?",
            r"aviacion|aeronautico|puertos?|maritimo|ferrocarril|metro",
        ]):
            scores["TRANSPORTE"] = scores.get("TRANSPORTE", 0.0) + 0.20

        if _has_any(t, [
            r"vivienda|habitacional|subsidio\s+(habitacional|de\s+vivienda)|serviu|minvu",
            r"urbanismo|plan\s+regulador|uso\s+de\s+suelo|zonificacion|territorial",
            r"arriendo|arrendamiento|copropiedad|condominio|desalojo|campamento",
        ]):
            scores["VIVIENDA_URBANISMO"] = scores.get("VIVIENDA_URBANISMO", 0.0) + 0.22

        # ─────────────────────────────────────────────────────────────
        # 3) Reglas de desempate: patrones muy fuertes deben prevalecer.
        # ─────────────────────────────────────────────────────────────
        strong_overrides = [
            ("TRANSPORTE", [r"ley\s+18\.290", r"licencia\s+de\s+conducir", r"transporte\s+publico"]),
            ("VIVIENDA_URBANISMO", [r"subsidio\s+habitacional", r"plan\s+regulador", r"ley\s+general\s+de\s+urbanismo"]),
            ("MEDIO_AMBIENTE", [r"servicio\s+de\s+biodiversidad", r"areas?\s+protegidas?", r"codigo\s+de\s+aguas"]),
            ("EDUCACION", [r"ley\s+general\s+de\s+educacion", r"establecimiento\s+educacional", r"educacion\s+superior"]),
            ("SALUD_PUBLICA", [r"fonasa|isapre|ges|auge", r"donacion\s+de\s+organos|trasplante"]),
            ("SEGURIDAD_JUSTICIA", [r"codigo\s+penal|codigo\s+procesal\s+penal", r"prision\s+preventiva"]),
            ("DERECHO_LABORAL_EMPLEO", [r"codigo\s+del\s+trabajo", r"permiso\s+laboral|fuero\s+laboral"]),
            ("INSTITUCIONALIDAD_ESTADO", [r"reforma\s+constitucional", r"carta\s+fundamental", r"acceso\s+a\s+la\s+informacion\s+publica"]),
        ]
        for cat, patterns in strong_overrides:
            if _has_any(t, patterns):
                scores[cat] = scores.get(cat, 0.0) + 0.18

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
