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
