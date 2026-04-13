"""
Endpoints de evaluación.

POST /api/v1/eval/run          - ejecuta evaluación completa
GET  /api/v1/eval/report       - obtiene el último reporte
POST /api/v1/eval/cosine       - calcula similitud coseno entre textos
POST /api/v1/eval/rouge        - calcula ROUGE-L entre predicciones y referencias
GET  /api/v1/eval/gt/stats     - estadísticas del ground truth
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.evaluation.evaluator import SystemEvaluator
from backend.evaluation.metrics import MetricsCalculator
from backend.evaluation.ground_truth import GroundTruthLoader

router = APIRouter()
logger = logging.getLogger(__name__)

_last_report: Optional[dict] = None


class CosineSimilarityRequest(BaseModel):
    text_a: str
    text_b: str


class CosineBatchRequest(BaseModel):
    pairs: list[tuple[str, str]]


class RougeRequest(BaseModel):
    predictions: list[str]
    references: list[str]


# ── Evaluación completa ───────────────────────────────────────────────────────
@router.post("/eval/run")
def run_evaluation():
    """
    Ejecuta evaluación completa: reglas vs embeddings vs híbrido.

    Requiere ground_truth_sample.jsonl con ≥ 10 entradas anotadas.

    Métricas calculadas:
      - Accuracy (subset), Hamming Loss
      - Precision / Recall / F1 (micro, macro, weighted)
      - Reporte por clase
      - Benchmarking comparativo
    """
    global _last_report
    try:
        evaluator = SystemEvaluator()
        report = evaluator.run_full_evaluation()
        _last_report = report
        return report
    except Exception as e:
        logger.error(f"Error en evaluación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Último reporte ────────────────────────────────────────────────────────────
@router.get("/eval/report")
def get_report():
    if not _last_report:
        raise HTTPException(
            status_code=404,
            detail="No hay reporte disponible. Ejecuta POST /eval/run primero."
        )
    return _last_report


# ── Similitud coseno individual ───────────────────────────────────────────────
@router.post("/eval/cosine")
def cosine_similarity(request: CosineSimilarityRequest):
    """
    Calcula la similitud coseno entre dos textos usando BAAI/bge-m3.

    Útil para evaluar calidad de embeddings y coherencia temática.
    """
    from backend.embeddings.encoder import BGEEncoder
    encoder = BGEEncoder.get_instance()
    try:
        vec_a = encoder.encode_single(request.text_a)
        vec_b = encoder.encode_single(request.text_b)
        sim = encoder.cosine_similarity(vec_a, vec_b)
        return {
            "text_a": request.text_a[:100],
            "text_b": request.text_b[:100],
            "cosine_similarity": round(float(sim), 4),
            "interpretation": _interpret_cosine(sim),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Similitud coseno en lote ──────────────────────────────────────────────────
@router.post("/eval/cosine/batch")
def cosine_batch(request: CosineBatchRequest):
    """Calcula similitud coseno para múltiples pares de textos."""
    import numpy as np
    if len(request.pairs) > 100:
        raise HTTPException(status_code=400, detail="Máximo 100 pares.")
    from backend.embeddings.encoder import BGEEncoder
    encoder = BGEEncoder.get_instance()
    try:
        texts_a = [p[0] for p in request.pairs]
        texts_b = [p[1] for p in request.pairs]
        vecs_a = encoder.encode(texts_a)
        vecs_b = encoder.encode(texts_b)
        sims = MetricsCalculator.cosine_similarity_score(vecs_a, vecs_b)
        return {
            "pairs": len(request.pairs),
            "mean_cosine_similarity": round(float(np.mean(sims)), 4),
            "similarities": [round(float(s), 4) for s in sims],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── ROUGE-L ────────────────────────────────────────────────────────────────────
@router.post("/eval/rouge")
def rouge_evaluation(request: RougeRequest):
    """
    Calcula ROUGE-L entre predicciones y referencias.

    Uso: evaluación de calidad de resúmenes y explicaciones generadas.
    """
    if len(request.predictions) != len(request.references):
        raise HTTPException(status_code=400, detail="predictions y references deben tener el mismo largo.")
    if len(request.predictions) > 200:
        raise HTTPException(status_code=400, detail="Máximo 200 pares.")
    try:
        metrics = MetricsCalculator.rouge_l(request.predictions, request.references)
        return {
            "n": len(request.predictions),
            "rouge_l_precision": metrics.rouge_l_precision,
            "rouge_l_recall": metrics.rouge_l_recall,
            "rouge_l_fmeasure": metrics.rouge_l_fmeasure,
            "note": "ROUGE-L mide la subsecuencia común más larga (LCS), capturando orden y coherencia textual.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Ground truth stats ────────────────────────────────────────────────────────
@router.get("/eval/gt/stats")
def gt_stats():
    """Estadísticas del dataset de evaluación (ground truth)."""
    loader = GroundTruthLoader()
    loader.load()
    stats = loader.stats_report()
    stats["why_not_accuracy"] = (
        "La accuracy (subset) en multi-label es estricta: solo cuenta 1 cuando "
        "el conjunto predicho es IDÉNTICO al real. En presencia de desbalance de clases "
        "(imbalance_ratio > 5), un clasificador trivial que predice la clase mayoritaria "
        "obtiene alta accuracy pero falla en clases minoritarias importantes. "
        "F1-weighted es la métrica principal porque: (1) pondera por soporte de clase, "
        "(2) penaliza tanto falsos positivos como falsos negativos, "
        "(3) es interpretable y comparable entre métodos."
    )
    return stats


# ── Helpers ───────────────────────────────────────────────────────────────────
def _interpret_cosine(sim: float) -> str:
    if sim >= 0.9:
        return "Muy alta similitud semántica (prácticamente idénticos)"
    if sim >= 0.75:
        return "Alta similitud semántica (mismo tema)"
    if sim >= 0.55:
        return "Similitud moderada (temas relacionados)"
    if sim >= 0.35:
        return "Baja similitud (temas distintos)"
    return "Sin similitud semántica relevante"
