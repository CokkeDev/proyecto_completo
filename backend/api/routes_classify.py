"""
Endpoints de clasificación.

POST /api/v1/classify          - clasifica un texto con el clasificador híbrido
POST /api/v1/classify/batch    - clasifica múltiples proyectos
GET  /api/v1/classify/emergent - detecta subcategorías emergentes en el corpus
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from backend.classification.hybrid_classifier import HybridClassifier
from backend.classification.models import ClassificationInput, ClassificationResult

router = APIRouter()
logger = logging.getLogger(__name__)

_classifier: Optional[HybridClassifier] = None


def get_classifier() -> HybridClassifier:
    global _classifier
    if _classifier is None:
        _classifier = HybridClassifier()
    return _classifier


class ClassifyRequest(BaseModel):
    boletin: str
    suma: str
    materias: Optional[str] = None


class BatchClassifyRequest(BaseModel):
    items: list[ClassifyRequest]


# ── Clasificación individual ──────────────────────────────────────────────────
@router.post("/classify", response_model=ClassificationResult)
def classify_single(request: ClassifyRequest):
    """
    Clasifica un proyecto de ley con el sistema híbrido.

    Retorna categoría principal, subcategorías, etiquetas, score y explicación.
    """
    inp = ClassificationInput(
        boletin=request.boletin,
        suma=request.suma,
        materias=request.materias,
    )
    try:
        return get_classifier().classify(inp)
    except Exception as e:
        logger.error(f"Error clasificando {request.boletin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Clasificación en lote ─────────────────────────────────────────────────────
@router.post("/classify/batch")
def classify_batch(request: BatchClassifyRequest):
    """Clasifica múltiples proyectos (máximo 50 por request)."""
    if len(request.items) > 50:
        raise HTTPException(status_code=400, detail="Máximo 50 items por lote.")
    clf = get_classifier()
    results = []
    errors = []
    for item in request.items:
        try:
            inp = ClassificationInput(boletin=item.boletin, suma=item.suma, materias=item.materias)
            results.append(clf.classify(inp))
        except Exception as e:
            errors.append({"boletin": item.boletin, "error": str(e)})
    return {"classified": len(results), "errors": errors, "results": [r.model_dump() for r in results]}


# ── Taxonomía emergente ───────────────────────────────────────────────────────
@router.post("/classify/emergent")
async def detect_emergent(background_tasks: BackgroundTasks, max_docs: int = 2000):
    """
    Detecta subcategorías emergentes aplicando HDBSCAN sobre todos los
    embeddings almacenados en Qdrant.

    Proceso en background (puede tomar varios minutos).
    """
    background_tasks.add_task(_run_emergent_detection, max_docs)
    return {
        "message": "Detección de taxonomía emergente iniciada en background.",
        "max_docs": max_docs,
    }


_emergent_results: list[dict] = []


async def _run_emergent_detection(max_docs: int):
    import asyncio
    try:
        from backend.qdrant.client import QdrantManager
        from backend.taxonomy.emergent_taxonomy import EmergentTaxonomyDetector
        from backend.classification.embedding_classifier import EmbeddingClassifier

        qdrant = QdrantManager()
        vectors, texts, boletines = await asyncio.get_event_loop().run_in_executor(
            None, lambda: qdrant.get_all_vectors_and_texts(limit=max_docs)
        )

        if len(vectors) < 10:
            logger.warning("Muy pocos vectores para detección emergente.")
            return

        emb_clf = EmbeddingClassifier()
        prototypes = emb_clf.get_prototypes()

        detector = EmergentTaxonomyDetector(min_cluster_size=5)
        clusters = await asyncio.get_event_loop().run_in_executor(
            None, lambda: detector.detect(vectors, texts, prototypes)
        )

        novel = detector.filter_novel(clusters, threshold=0.55)
        global _emergent_results
        _emergent_results = detector.to_validation_report(novel)
        logger.info(f"Detección emergente: {len(novel)} clusters novedosos encontrados.")
    except Exception as e:
        logger.error(f"Error en detección emergente: {e}")


@router.get("/classify/emergent/results")
def get_emergent_results():
    """Retorna los resultados de la última detección emergente."""
    return {"total_novel_clusters": len(_emergent_results), "clusters": _emergent_results}
