"""
Endpoints de clasificación.

POST /api/v1/classify          - clasifica un texto con el clasificador por reglas
POST /api/v1/classify/batch    - clasifica múltiples proyectos
GET  /api/v1/classify/emergent - detecta subcategorías emergentes en el corpus
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from backend.classification.rule_classifier import RuleBasedClassifier
from backend.classification.models import ClassificationInput, ClassificationResult

router = APIRouter()
logger = logging.getLogger(__name__)

_classifier: Optional[RuleBasedClassifier] = None


def get_classifier() -> RuleBasedClassifier:
    global _classifier
    if _classifier is None:
        _classifier = RuleBasedClassifier()
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
    Clasifica un proyecto de ley con el sistema basado en reglas.

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
    """Clasifica múltiples proyectos con reglas (máximo 50 por request)."""
    if len(request.items) > 50:
        raise HTTPException(status_code=400, detail="Máximo 50 items por lote.")

    clf = get_classifier()
    results = []
    errors = []

    for item in request.items:
        try:
            inp = ClassificationInput(
                boletin=item.boletin,
                suma=item.suma,
                materias=item.materias
            )
            results.append(clf.classify(inp))
        except Exception as e:
            errors.append({"boletin": item.boletin, "error": str(e)})

    return {
        "classified": len(results),
        "errors": errors,
        "results": [r.model_dump() for r in results]
    }


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
    return {
        "total_novel_clusters": len(_emergent_results),
        "clusters": _emergent_results
    }


# ── Diagnóstico de clasificación ──────────────────────────────────────────────
class DiagnoseRequest(BaseModel):
    """Permite diagnosticar pasando texto crudo o un boletín ya ingestado."""
    boletin: Optional[str] = None
    suma: Optional[str] = None
    materias: Optional[str] = None
    top_k: int = 5  # cuántos scores mostrar por capa


@router.post("/classify/diagnose")
def diagnose_classification(request: DiagnoseRequest):
    """
    Inspecciona qué hace cada capa del clasificador híbrido para un proyecto.

    Devuelve:
      - texto evaluado y de dónde viene (texto crudo vs Qdrant)
      - matches de Capa 1 (regex) por subcategoría
      - matches de Capa 2 (keywords) por subcategoría
      - similitud coseno con cada centroide positivo de Capa 3
      - similitud coseno con cada subcategoría (granularidad fina)
      - resultado final del ClosedSetClassifier (qué predijo y por qué)

    Útil para entender por qué un boletín cae en una clase incorrecta.
    """
    import re as _re
    import numpy as _np

    from backend.classification.closed_set_classifier import ClosedSetClassifier
    from backend.classification.embedding_classifier import EmbeddingClassifier
    from backend.classification.rule_classifier import RuleBasedClassifier
    from backend.taxonomy.taxonomy_data import TAXONOMY
    from backend.taxonomy.manual_taxonomy import ManualTaxonomy
    from backend.utils.text_normalizer import normalize_text
    from backend.qdrant.client import QdrantManager

    # ── Resolver texto a evaluar ──────────────────────────────────────────────
    suma = request.suma
    materias = request.materias
    source = "input"

    if request.boletin and not suma:
        try:
            qm = QdrantManager()
            project = qm.get_project_by_boletin(request.boletin)
            if project:
                suma = project.get("suma", "") or project.get("suma_clean", "")
                materias_raw = project.get("materias_raw") or []
                if isinstance(materias_raw, list):
                    materias = " / ".join(materias_raw)
                else:
                    materias = str(materias_raw)
                source = "qdrant"
        except Exception as e:
            logger.warning(f"No se pudo leer boletín {request.boletin}: {e}")

    if not suma:
        raise HTTPException(
            status_code=400,
            detail="Debes pasar 'suma' o un 'boletin' ya ingestado.",
        )

    text = f"{suma} {materias or ''}".strip()
    text_norm = normalize_text(text)

    # ── Capa 1 — reglas regex por subcategoría ────────────────────────────────
    layer1: list[dict] = []
    taxonomy = ManualTaxonomy()
    for cat_code, cat_data in TAXONOMY.items():
        for sub_code, sub_data in cat_data.get("subcategorias", {}).items():
            matched_rules = []
            for rule in sub_data.get("reglas_semanticas", []):
                try:
                    if _re.search(normalize_text(rule), text_norm,
                                  flags=_re.IGNORECASE | _re.UNICODE):
                        matched_rules.append(rule)
                except _re.error:
                    continue
            if matched_rules:
                layer1.append({
                    "categoria": cat_code,
                    "subcategoria": sub_code,
                    "matched_rules": matched_rules,
                    "match_count": len(matched_rules),
                })
    layer1.sort(key=lambda x: x["match_count"], reverse=True)

    # ── Capa 2 — keyword score por subcategoría ───────────────────────────────
    layer2: list[dict] = []
    for cat_code, cat_data in TAXONOMY.items():
        for sub_code, sub_data in cat_data.get("subcategorias", {}).items():
            kws = sub_data.get("keywords", [])
            hits = [
                kw for kw in kws if normalize_text(kw) in text_norm
            ]
            if hits:
                layer2.append({
                    "categoria": cat_code,
                    "subcategoria": sub_code,
                    "matched_keywords": hits[:8],
                    "hits": len(hits),
                    "kw_score": round(len(hits) / max(1, len(kws)), 4),
                })
    layer2.sort(key=lambda x: x["kw_score"], reverse=True)

    # ── Capa 3 — similitud semántica vs centroides ────────────────────────────
    emb_clf = EmbeddingClassifier()
    cat_scores = emb_clf.predict(text)
    cat_scores_sorted = sorted(
        cat_scores.items(), key=lambda x: x[1], reverse=True
    )[: request.top_k]

    sub_scores = emb_clf.predict_subcategories(text)
    sub_scores_sorted = sorted(
        sub_scores.items(), key=lambda x: x[1], reverse=True
    )[: request.top_k]

    # ── Predicción final del híbrido ──────────────────────────────────────────
    closed_clf = ClosedSetClassifier()
    closed_input = ClassificationInput(
        boletin=request.boletin or "DIAGNOSE",
        suma=suma,
        materias=materias,
    )
    closed_result = closed_clf.classify(closed_input)

    final = {
        "estado": closed_result.estado,
        "primary": (
            {
                "categoria": closed_result.primary.categoria_id,
                "subcategoria": closed_result.primary.subcategoria_id,
                "confianza": round(closed_result.primary.confianza, 4),
                "metodo_match": closed_result.primary.metodo_match,
                "matched_rules": closed_result.primary.matched_rules,
            } if closed_result.primary else None
        ),
        "secondary": [
            {
                "categoria": m.categoria_id,
                "subcategoria": m.subcategoria_id,
                "confianza": round(m.confianza, 4),
                "metodo_match": m.metodo_match,
            } for m in closed_result.secondary
        ],
        "texto_fuente": closed_result.texto_fuente,
    }

    # ── Sugerencia heurística de por qué falla ────────────────────────────────
    reason: str
    if not layer1 and not layer2:
        reason = (
            "Capas 1 y 2 no encontraron ningún match — el texto no contiene "
            "ninguna keyword ni dispara ninguna regla regex de la taxonomía. "
            "El sistema cayó a Capa 3 (embeddings), que es la más permisiva "
            "y la causa más común de clasificaciones incorrectas. "
            "Solución: agregar keywords y/o reglas regex para esta temática "
            "en taxonomy_data.py."
        )
    elif not layer1:
        reason = (
            "Capa 1 (regex) no matcheó. El sistema usa keywords + embeddings, "
            "que son más permisivos. Si la clasificación es incorrecta, "
            "considera agregar una regla regex específica en la subcategoría "
            "correcta."
        )
    else:
        reason = (
            "Capas 1 y/o 2 produjeron matches. Si el resultado final es "
            "incorrecto, revisa que la subcategoría correcta tenga reglas "
            "más específicas, o ajusta MULTI_CAT_MARGIN / SEMANTIC_THRESHOLD "
            "en ClosedSetClassifier."
        )

    return {
        "input": {
            "boletin": request.boletin,
            "suma": suma,
            "materias": materias,
            "source": source,
        },
        "layer1_regex": layer1[: request.top_k],
        "layer2_keywords": layer2[: request.top_k],
        "layer3_semantic": {
            "top_categories": [
                {"categoria": c, "score": round(s, 4)} for c, s in cat_scores_sorted
            ],
            "top_subcategories": [
                {"subcategoria": s, "score": round(sc, 4)} for s, sc in sub_scores_sorted
            ],
        },
        "final_prediction": final,
        "diagnosis": reason,
    }
