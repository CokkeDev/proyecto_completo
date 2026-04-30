"""
Endpoints de búsqueda.

GET  /api/v1/search/semantic   - búsqueda semántica
GET  /api/v1/search/hybrid     - búsqueda híbrida (semántica + filtros)
GET  /api/v1/search/structured - búsqueda estructurada (solo filtros)
GET  /api/v1/search/detail/{boletin}  - detalle de un proyecto
GET  /api/v1/search/similar/{boletin} - proyectos similares
GET  /api/v1/search/categories        - listar categorías disponibles
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.search.searcher import SearchEngine
from backend.taxonomy.taxonomy_data import TAXONOMY
import logging
import traceback
from datetime import date

logger = logging.getLogger(__name__)
router = APIRouter()
_engine: Optional[SearchEngine] = None


def get_engine() -> SearchEngine:
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


# ── Búsqueda semántica ────────────────────────────────────────────────────────
@router.get("/search/semantic")
def search_semantic(
    q: str = Query(..., min_length=3, description="Consulta en lenguaje natural"),
    top_k: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.35, ge=0.0, le=1.0),
):
    """
    Busca proyectos de ley por similitud semántica usando BAAI/bge-m3.

    Ejemplo: ?q=subsidio habitacional familias vulnerables
    """
    try:
        results = get_engine().search_semantic(q, top_k=top_k, score_threshold=score_threshold)
        return {"query": q, "total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Búsqueda híbrida ──────────────────────────────────────────────────────────
@router.get("/search/hybrid")
def search_hybrid(
    q: str = Query(..., min_length=3),
    top_k: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.30, ge=0.0, le=1.0),
    categoria: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    fecha_hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    etapa: Optional[str] = Query(None),
    iniciativa: Optional[str] = Query(None, description="Mensaje o Moción"),
    camara_origen: Optional[str] = Query(None, description="Senado o C.Diputados"),
):
    """
    Búsqueda semántica con filtros estructurados combinados.

    Ejemplo: ?q=reforma pensiones&categoria=DERECHO_LABORAL_EMPLEO&fecha_desde=2022-01-01
    """
    try:
        results = get_engine().search_hybrid(
            query=q,
            top_k=top_k,
            score_threshold=score_threshold,
            categoria=categoria,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            etapa=etapa,
            iniciativa=iniciativa,
            camara_origen=camara_origen,
        )
        return {"query": q, "filters_applied": bool(categoria or fecha_desde or etapa), "total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Búsqueda estructurada ─────────────────────────────────────────────────────
@router.get("/search/structured")
def search_structured(
    categoria: Optional[str] = Query(None),
    etiquetas: Optional[str] = Query(None, description="Etiquetas separadas por coma"),
    fecha_desde: Optional[date] = Query(None, description="YYYY-MM-DD"),
    fecha_hasta: Optional[date] = Query(None, description="YYYY-MM-DD"),
    etapa: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: Optional[str] = Query(None),
):
    """Búsqueda por filtros sin consulta semántica."""
    etiquetas_list = [e.strip() for e in etiquetas.split(",") if e.strip()] if etiquetas else None

    try:
        results, next_offset = get_engine().search_structured(
            categoria=categoria,
            etiquetas=etiquetas_list,
            fecha_desde=fecha_desde.isoformat() if fecha_desde else None,
            fecha_hasta=fecha_hasta.isoformat() if fecha_hasta else None,
            etapa=etapa,
            limit=limit,
            offset=offset,
        )
        return {
            "total": len(results),
            "next_offset": next_offset,
            "results": results,
        }
    except Exception as e:
        logger.exception("Error en /search/structured")
        raise HTTPException(status_code=500, detail=f"Error interno en búsqueda estructurada: {str(e)}")


# ── Detalle ───────────────────────────────────────────────────────────────────
@router.get("/search/detail/{boletin}")
def get_detail(boletin: str):
    """Retorna el detalle completo de un proyecto por su boletín."""
    result = get_engine().get_detail(boletin)
    if not result:
        raise HTTPException(status_code=404, detail=f"Boletín {boletin} no encontrado.")
    return result


# ── Proyectos similares ───────────────────────────────────────────────────────
@router.get("/search/similar/{boletin}")
def get_similar(boletin: str, top_k: int = Query(5, ge=1, le=20)):
    """Retorna proyectos similares al boletín dado."""
    results = get_engine().get_similar(boletin, top_k=top_k)
    return {"boletin": boletin, "similar": results}


# ── Categorías disponibles ────────────────────────────────────────────────────
@router.get("/search/categories")
def get_categories():
    """Lista todas las categorías y subcategorías de la taxonomía."""
    return {
        "categories": [
            {
                "code": code,
                "label": data["label"],
                "definition": data["definition"],
                "subcategories": [
                    {
                        "code": sub_code,
                        "label": sub_data["label"],
                    }
                    for sub_code, sub_data in data["subcategorias"].items()
                ],
            }
            for code, data in TAXONOMY.items()
        ]
    }
