"""
Endpoints de ingesta.

POST /api/v1/ingest/run    - ejecuta pipeline completo
GET  /api/v1/ingest/status - estado de la colección Qdrant
POST /api/v1/ingest/single - ingesta de un proyecto individual (por boletín)
"""
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.ingestion.pipeline import IngestionPipeline
from backend.qdrant.client import QdrantManager

router = APIRouter()
logger = logging.getLogger(__name__)

_ingestion_status = {"running": False, "last_stats": None}


class SingleIngestRequest(BaseModel):
    boletin: str
    suma: str
    materias: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    etapa: Optional[str] = None


# ── Run pipeline ──────────────────────────────────────────────────────────────
@router.post("/ingest/run")
async def run_ingestion(background_tasks: BackgroundTasks, skip_existing: bool = True):
    """
    Ejecuta el pipeline completo de ingesta en background.

    Descarga proyectos de la API del Senado, los clasifica con el
    clasificador híbrido, genera embeddings con BAAI/bge-m3 y los
    almacena en Qdrant.
    """
    if _ingestion_status["running"]:
        raise HTTPException(status_code=409, detail="Ingesta ya en curso.")

    background_tasks.add_task(_run_pipeline, skip_existing)
    return {"message": "Pipeline de ingesta iniciado en background.", "skip_existing": skip_existing}


async def _run_pipeline(skip_existing: bool):
    _ingestion_status["running"] = True
    try:
        pipeline = IngestionPipeline(skip_existing=skip_existing)
        stats = await asyncio.get_event_loop().run_in_executor(None, pipeline.run)
        _ingestion_status["last_stats"] = {
            "fetched": stats.fetched,
            "normalized": stats.normalized,
            "classified": stats.classified,
            "stored": stats.stored,
            "skipped": stats.skipped,
            "errors": stats.errors,
        }
        logger.info(f"Ingesta completada: {stats.stored} puntos almacenados.")
    except Exception as e:
        logger.error(f"Error en pipeline: {e}")
        _ingestion_status["last_stats"] = {"error": str(e)}
    finally:
        _ingestion_status["running"] = False


# ── Estado ────────────────────────────────────────────────────────────────────
@router.get("/ingest/status")
def ingestion_status():
    """Estado del pipeline y estadísticas de la colección Qdrant."""
    try:
        qdrant = QdrantManager()
        collection_info = qdrant.collection_info()
    except Exception as e:
        collection_info = {"error": str(e)}

    return {
        "pipeline_running": _ingestion_status["running"],
        "last_run_stats": _ingestion_status["last_stats"],
        "collection": collection_info,
    }


# ── Ingesta individual ────────────────────────────────────────────────────────
@router.post("/ingest/single")
def ingest_single(request: SingleIngestRequest):
    """
    Ingesta un proyecto individual (útil para testing y demostración).
    """
    from backend.ingestion.normalizer import ProjectNormalizer, NormalizedProject
    from backend.ingestion.pipeline import IngestionPipeline

    raw = {
        "ID_PROYECTO": 0,
        "BOLETIN": request.boletin,
        "SUMA": request.suma,
        "MATERIAS": request.materias or "",
        "FECHA_INGRESO": request.fecha_ingreso or "01/01/2024",
        "INICIATIVA": "Moción",
        "TIPO": "Proyecto de ley",
        "CAMARA_ORIGEN": "Senado",
        "AUTORES": "",
        "ETAPA": request.etapa or "Primer trámite constitucional",
        "LINK_PROYECTO_LEY": f"https://www.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini={request.boletin}",
        "DOCUMENTO": "",
    }

    pipeline = IngestionPipeline(skip_existing=False)
    try:
        pipeline._process_batch([raw], type("Stats", (), {
            "fetched": 0, "normalized": 0, "skipped": 0,
            "classified": 0, "encoded": 0, "stored": 0,
            "errors": 0, "error_details": []
        })())
        return {"status": "ok", "boletin": request.boletin}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
