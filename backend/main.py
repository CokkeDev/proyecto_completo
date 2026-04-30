"""
FastAPI — Punto de entrada principal.

Ejecutar:
    cd C:/Users/DCANDIA/Documents/Programa
    uvicorn backend.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes_search import router as search_router
from backend.api.routes_ingest import router as ingest_router
from backend.api.routes_classify import router as classify_router
from backend.api.routes_eval import router as eval_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)

    # 1. Asegurar colección Qdrant
    try:
        from backend.qdrant.client import QdrantManager
        qm = QdrantManager()
        qm.ensure_collection()
    except Exception as e:
        logger.warning(f"No se pudo conectar a Qdrant: {e}. Continúa en modo degradado.")

    # 2. Pre-cargar modelo de embeddings (pesado, solo una vez)
    try:
        from backend.embeddings.encoder import BGEEncoder
        BGEEncoder.get_instance()
        logger.info("Modelo BAAI/bge-m3 listo.")
    except Exception as e:
        logger.warning(f"No se pudo cargar BAAI/bge-m3: {e}. Continúa sin embeddings.")

    logger.info("Sistema listo. Esperando requests.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Apagando sistema...")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description=(
        "API para búsqueda semántica y clasificación automática de proyectos de ley chilenos. "
        "Usa BAAI/bge-m3 para embeddings y Qdrant como base de datos vectorial."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS: permite que el frontend estático llame a la API ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(search_router,   prefix="/api/v1", tags=["Búsqueda"])
app.include_router(ingest_router,   prefix="/api/v1", tags=["Ingesta"])
app.include_router(classify_router, prefix="/api/v1", tags=["Clasificación"])
app.include_router(eval_router,     prefix="/api/v1", tags=["Evaluación"])


# ── Health checks ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Sistema"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/health", tags=["Sistema"])
def health():
    """Verifica disponibilidad de Qdrant y del modelo de embeddings."""
    qdrant_ok = False
    model_ok = False

    try:
        from backend.qdrant.client import QdrantManager
        QdrantManager().collection_info()
        qdrant_ok = True
    except Exception:
        pass

    try:
        from backend.embeddings.encoder import BGEEncoder
        enc = BGEEncoder.get_instance()
        model_ok = enc is not None
    except Exception:
        pass

    status = "ok" if qdrant_ok and model_ok else "degraded"
    return {
        "status": status,
        "qdrant": "ok" if qdrant_ok else "unavailable",
        "embedding_model": "ok" if model_ok else "unavailable",
    }
