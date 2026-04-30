"""
Endpoints de ingesta.

POST /api/v1/ingest/run         - pipeline completo (background)
POST /api/v1/ingest/demo        - últimos 15 proyectos con texto completo (foreground)
GET  /api/v1/ingest/status      - estado de la colección Qdrant
POST /api/v1/ingest/single      - ingesta de un proyecto individual (testing)
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

DEMO_LIMIT = 15


class SingleIngestRequest(BaseModel):
    boletin: str



# ── Run pipeline completo ─────────────────────────────────────────────────────
@router.post("/ingest/run")
async def run_ingestion(background_tasks: BackgroundTasks, skip_existing: bool = True):
    """
    Ejecuta el pipeline completo de ingesta en background.
    Usa ClosedSetClassifier con SUMA+MATERIAS para clasificar.
    """
    if _ingestion_status["running"]:
        raise HTTPException(status_code=409, detail="Ingesta ya en curso.")

    background_tasks.add_task(_run_pipeline, skip_existing)
    return {
        "message": "Pipeline de ingesta iniciado en background.",
        "skip_existing": skip_existing,
        "clasificador": "ClosedSetClassifier",
    }


async def _run_pipeline(skip_existing: bool):
    _ingestion_status["running"] = True
    try:
        pipeline = IngestionPipeline(
            skip_existing=skip_existing,
            use_closed_set=True,
            use_full_text=False,
        )
        stats = await asyncio.get_event_loop().run_in_executor(None, pipeline.run)
        _ingestion_status["last_stats"] = _stats_to_dict(stats)
        logger.info(f"Ingesta completada: {stats.stored} puntos almacenados.")
    except Exception as e:
        logger.error(f"Error en pipeline: {e}")
        _ingestion_status["last_stats"] = {"error": str(e)}
    finally:
        _ingestion_status["running"] = False


# ── Demo: últimos 15 proyectos con PDF completo ───────────────────────────────
@router.post("/ingest/demo")
def run_demo_ingestion(skip_existing: bool = False):
    """
    Ingesta de demostración: descarga los últimos 15 proyectos de la API del Senado,
    obtiene el texto completo de cada PDF, y los clasifica con el ClosedSetClassifier.

    - Texto fuente: documento completo (PDF) cuando está disponible, SUMA+MATERIAS si no.
    - Clasificador: ClosedSetClassifier (conjunto cerrado, sin categorías inventadas).
    - skip_existing=False por defecto para forzar re-clasificación con el nuevo sistema.

    Retorna los resultados directamente (no en background).
    """
    from backend.ingestion.fetcher import SenadoAPIFetcher
    from backend.ingestion.normalizer import ProjectNormalizer
    from backend.ingestion.document_fetcher import DocumentFetcher
    from backend.classification.closed_set_classifier import ClosedSetClassifier
    from backend.classification.models import ClassificationInput

    fetcher = SenadoAPIFetcher()
    normalizer = ProjectNormalizer()
    doc_fetcher = DocumentFetcher()
    classifier = ClosedSetClassifier()

    # 1. Obtener los últimos 15 proyectos
    logger.info(f"Demo: descargando últimos {DEMO_LIMIT} proyectos...")
    raw_projects = fetcher.fetch_last_n(DEMO_LIMIT)

    if not raw_projects:
        raise HTTPException(status_code=503, detail="No se pudieron descargar proyectos de la API del Senado.")

    normalized = normalizer.normalize_batch(raw_projects)
    logger.info(f"Demo: {len(normalized)} proyectos normalizados.")

    results = []

    for proj in normalized:
        if not proj.boletin or not proj.suma_clean:
            continue

        # 2. Descargar PDF
        doc_text: Optional[str] = None
        pdf_status = "no_url"
        if proj.documento_url:
            doc_text = doc_fetcher.fetch_text(proj.documento_url)
            pdf_status = "ok" if doc_text else "failed"

        # 3. Clasificar con ClosedSetClassifier
        inp = ClassificationInput(
            boletin=proj.boletin,
            suma=proj.suma_clean,
            materias="/".join(proj.materias) if proj.materias else None,
        )
        closed_result = classifier.classify(inp, texto_completo=doc_text)

        result_entry = {
            "boletin": proj.boletin,
            "suma": proj.suma_clean[:200] + ("..." if len(proj.suma_clean) > 200 else ""),
            "fecha_ingreso": proj.fecha_ingreso,
            "pdf_status": pdf_status,
            "palabras_analizadas": closed_result.palabras_analizadas,
            "texto_fuente": closed_result.texto_fuente,
            "estado_clasificacion": closed_result.estado,
            "primary": None,
            "secondary": [],
        }

        if closed_result.primary:
            p = closed_result.primary
            result_entry["primary"] = {
                "categoria_id": p.categoria_id,
                "categoria_label": p.categoria_label,
                "subcategoria_id": p.subcategoria_id,
                "subcategoria_label": p.subcategoria_label,
                "metodo_match": p.metodo_match,
                "confianza": p.confianza,
                "matched_rules": p.matched_rules[:5],
            }
            result_entry["secondary"] = [
                {
                    "categoria_id": m.categoria_id,
                    "categoria_label": m.categoria_label,
                    "subcategoria_id": m.subcategoria_id,
                    "subcategoria_label": m.subcategoria_label,
                    "metodo_match": m.metodo_match,
                    "confianza": m.confianza,
                }
                for m in closed_result.secondary
            ]

        results.append(result_entry)

        # 4. Guardar en Qdrant (opcional, si skip_existing=False o no existe)
        try:
            pipeline = IngestionPipeline(
                skip_existing=skip_existing,
                use_closed_set=True,
                use_full_text=False,  # ya tenemos doc_text, lo inyectamos directamente
            )
            pipeline._process_batch([{
                "ID_PROYECTO": proj.id_proyecto,
                "BOLETIN": proj.boletin,
                "SUMA": proj.suma,
                "MATERIAS": "/".join(proj.materias) if proj.materias else "",
                "FECHA_INGRESO": proj.fecha_ingreso_raw,
                "INICIATIVA": proj.iniciativa,
                "TIPO": proj.tipo,
                "CAMARA_ORIGEN": proj.camara_origen,
                "AUTORES": "/".join(proj.autores),
                "ETAPA": proj.etapa,
                "LINK_PROYECTO_LEY": proj.link_proyecto,
                "DOCUMENTO": proj.documento_url,
            }], type("Stats", (), {
                "fetched": 0, "normalized": 0, "skipped": 0, "classified": 0,
                "por_clasificar": 0, "encoded": 0, "stored": 0, "errors": 0,
                "pdf_ok": 0, "pdf_failed": 0, "error_details": [],
            })())
        except Exception as e:
            logger.warning(f"No se pudo guardar {proj.boletin} en Qdrant: {e}")

    clasificados = sum(1 for r in results if r["estado_clasificacion"] == "clasificado")
    por_clasificar = sum(1 for r in results if r["estado_clasificacion"] == "POR_CLASIFICAR")
    pdf_ok = sum(1 for r in results if r["pdf_status"] == "ok")

    return {
        "total_procesados": len(results),
        "clasificados": clasificados,
        "por_clasificar": por_clasificar,
        "pdf_descargados": pdf_ok,
        "resultados": results,
    }


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
    from backend.ingestion.fetcher import SenadoAPIFetcher
    from backend.ingestion.pipeline import IngestionPipeline
    from backend.ingestion.document_fetcher import DocumentFetcher
    from backend.ingestion.normalizer import ProjectNormalizer

    fetcher = SenadoAPIFetcher()
    normalizer = ProjectNormalizer()

    # 1. Fetch real
    raw_projects = fetcher.fetch_by_boletin(request.boletin)

    if not raw_projects:
        raise HTTPException(status_code=404, detail="Boletín no encontrado")

    raw = raw_projects[0]  # USAR DIRECTO

    if "data" in raw:
        raw = raw["data"][0]

    print("RAW LIMPIO:", raw)

    # Descarga de PDF
    doc_fetcher = DocumentFetcher()

    doc_text = None
    pdf_status = "no_url"

    documento_url = raw.get("DOCUMENTO")

    if documento_url:
        doc_text = doc_fetcher.fetch_text(documento_url)
        pdf_status = "ok" if doc_text else "failed"


    if doc_text:
        doc_text = normalizer._clean_text(doc_text)
        doc_text = doc_text[:3000]  # opcional (recomendado)

    #  Inyectar texto en raw
    raw["TEXTO_COMPLETO"] = doc_text
    
    print("TEXTO_COMPLETO",doc_text)

    # Pipeline
    pipeline = IngestionPipeline(skip_existing=False,use_full_text=True)

    dummy_stats = type("Stats", (), {
        "fetched": 0, "normalized": 0, "skipped": 0, "classified": 0,
        "por_clasificar": 0, "encoded": 0, "stored": 0, "errors": 0,
        "pdf_ok": 0, "pdf_failed": 0, "error_details": [],
    })()

    pipeline._process_batch([raw], dummy_stats)

    return {
        "status": "ok",
        "boletin": raw.get("BOLETIN"),
        "suma": raw.get("SUMA"),
        "pdf_status": pdf_status,
        "usa_pdf": True if doc_text else False
    }

# ── Helpers ───────────────────────────────────────────────────────────────────
def _stats_to_dict(stats) -> dict:
    return {
        "fetched": stats.fetched,
        "normalized": stats.normalized,
        "classified": stats.classified,
        "por_clasificar": stats.por_clasificar,
        "stored": stats.stored,
        "skipped": stats.skipped,
        "pdf_ok": stats.pdf_ok,
        "pdf_failed": stats.pdf_failed,
        "errors": stats.errors,
    }
