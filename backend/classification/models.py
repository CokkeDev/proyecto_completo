"""
Modelos Pydantic para entrada/salida del clasificador.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ClassificationInput(BaseModel):
    """Texto a clasificar."""
    boletin: str = Field(..., description="Número de boletín, ej: '13312-03'")
    suma: str = Field(..., description="Resumen/descripción del proyecto")
    materias: Optional[str] = Field(None, description="Materias separadas por '/'")

    @property
    def full_text(self) -> str:
        parts = [self.suma]
        if self.materias:
            parts.append(self.materias)
        return " ".join(parts)


class LabelScore(BaseModel):
    label: str = Field(..., description="Código de categoría o subcategoría")
    label_display: str = Field(..., description="Nombre legible")
    score: float = Field(..., ge=0.0, le=1.0)
    origin: str = Field(..., description="'rules', 'embeddings', o 'hybrid'")


class ClassificationResult(BaseModel):
    """Modelo legado — mantenido para compatibilidad con el pipeline de ingesta."""
    boletin: str
    primary_category: str
    primary_category_display: str
    subcategories: list[str] = []
    labels: list[str] = []
    top_scores: list[LabelScore] = []
    confidence: float = 0.0
    explanation: str = ""
    origin: str = "hybrid"

    rule_scores: dict[str, float] = {}
    embedding_scores: dict[str, float] = {}
    hybrid_scores: dict[str, float] = {}


# ── Nuevos modelos para el Clasificador de Conjunto Cerrado ───────────────────

class ClassificationMatch(BaseModel):
    """Un match confirmado contra una categoría del TAXONOMY."""
    categoria_id: str = Field(..., description="Key exacta en TAXONOMY")
    categoria_label: str = Field(..., description="Nombre legible de la categoría")
    subcategoria_id: str = Field(..., description="Key de subcategoría")
    subcategoria_label: str = Field(..., description="Nombre legible de la subcategoría")
    metodo_match: str = Field(..., description="'regla_regex' | 'keyword' | 'semantica'")
    confianza: float = Field(..., ge=0.0, le=1.0, description="Score de confianza [0,1]")
    matched_rules: list[str] = Field(default_factory=list, description="Patrones regex que hicieron match")


class ClosedSetResult(BaseModel):
    """
    Resultado del ClosedSetClassifier.

    estado='clasificado'    → primary contiene el match principal
    estado='POR_CLASIFICAR' → primary=None, se requiere revisión manual
    """
    boletin: str
    estado: str = Field(..., description="'clasificado' | 'POR_CLASIFICAR'")
    primary: Optional[ClassificationMatch] = None
    secondary: list[ClassificationMatch] = Field(default_factory=list)
    texto_fuente: str = Field(default="suma_materias", description="'suma_materias' | 'documento_completo'")
    palabras_analizadas: int = 0
