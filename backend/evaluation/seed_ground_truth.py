"""
seed_ground_truth.py — Genera un JSONL semilla de ground truth a partir de
los proyectos ya ingestados en projects_collection, usando como anotación
INICIAL la clasificación predicha por el sistema.

ATENCIÓN:
    Este archivo es solo un punto de partida para revisión manual.
    Evaluar el clasificador contra sus propias predicciones es circular y
    arrojaría métricas artificialmente perfectas. SIEMPRE hay que revisar
    y corregir las anotaciones a mano antes de usar el archivo como
    ground truth.

Uso típico:
    # 1) Generar la semilla (estratificada por categoría)
    python -m backend.evaluation.seed_ground_truth \\
        --output backend/evaluation/ground_truth_seed.jsonl \\
        --csv backend/evaluation/ground_truth_seed.csv \\
        --per-category 20 \\
        --skip-por-clasificar

    # 2) Abrir el CSV en una planilla, corregir 'labels' y 'primary_category'
    #    a mano. Marcar 'reviewed' = true en las filas validadas.

    # 3) Convertir el CSV revisado de vuelta a JSONL (formato del loader):
    python -m backend.evaluation.seed_ground_truth \\
        --from-csv backend/evaluation/ground_truth_seed.csv \\
        --output backend/evaluation/ground_truth_sample.jsonl \\
        --only-reviewed
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger("seed_ground_truth")

# Campos que escribimos en el JSONL/CSV
_JSONL_FIELDS = ["boletin", "suma", "labels", "primary_category", "materias"]
_CSV_FIELDS = [
    "boletin",
    "suma",
    "primary_category",
    "labels",         # separadas por coma
    "materias",
    "reviewed",       # "true" cuando un humano lo validó
    "notes",          # comentarios libres del revisor
    "_seed_origin",   # "auto" cuando viene del clasificador
]


# ── 1. Lectura desde Qdrant ──────────────────────────────────────────────────

def _scroll_all_projects(batch_size: int = 256) -> Iterable[dict]:
    """
    Generator que itera todos los puntos de projects_collection.

    Se importa QdrantManager perezosamente para que el script se pueda
    ejecutar sin levantar el modelo de embeddings.
    """
    from backend.qdrant.client import QdrantManager, PROJECTS_COLLECTION

    qm = QdrantManager()
    offset = None
    while True:
        points, next_offset = qm.client.scroll(
            collection_name=PROJECTS_COLLECTION,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            if payload:
                yield payload
        if next_offset is None:
            break
        offset = next_offset


# ── 2. Filtrado y muestreo estratificado ─────────────────────────────────────

def _is_usable(payload: dict, skip_por_clasificar: bool) -> bool:
    if not payload.get("boletin") or not payload.get("suma"):
        return False
    if not payload.get("categoria_principal"):
        return False
    if skip_por_clasificar and payload.get("estado_clasificacion") == "POR_CLASIFICAR":
        return False
    return True


def _stratified_sample(
    payloads: list[dict],
    per_category: int,
    total_cap: Optional[int],
    seed: int,
) -> list[dict]:
    """
    Muestreo estratificado por categoría_principal:
      - Toma hasta `per_category` proyectos por categoría
      - Luego trunca a `total_cap` si se especifica
    """
    rng = random.Random(seed)

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for p in payloads:
        by_cat[p["categoria_principal"]].append(p)

    sampled: list[dict] = []
    for cat, items in by_cat.items():
        rng.shuffle(items)
        sampled.extend(items[:per_category])

    rng.shuffle(sampled)  # mezclamos para que el orden no sea por categoría

    if total_cap and len(sampled) > total_cap:
        sampled = sampled[:total_cap]
    return sampled


# ── 3. Escritura ─────────────────────────────────────────────────────────────

def _materias_to_string(materias_raw) -> str:
    if not materias_raw:
        return ""
    if isinstance(materias_raw, list):
        return " / ".join(str(m) for m in materias_raw)
    return str(materias_raw)


def _payload_to_jsonl_row(payload: dict) -> dict:
    return {
        "boletin": payload.get("boletin"),
        "suma": payload.get("suma"),
        "labels": list(payload.get("subcategorias") or []),
        "primary_category": payload.get("categoria_principal"),
        "materias": _materias_to_string(payload.get("materias_raw")),
    }


def _payload_to_csv_row(payload: dict) -> dict:
    labels = payload.get("subcategorias") or []
    return {
        "boletin": payload.get("boletin", ""),
        "suma": payload.get("suma", ""),
        "primary_category": payload.get("categoria_principal", ""),
        "labels": ", ".join(labels),
        "materias": _materias_to_string(payload.get("materias_raw")),
        "reviewed": "false",
        "notes": "",
        "_seed_origin": "auto",
    }


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ── 4. Conversión CSV revisado → JSONL ───────────────────────────────────────

def _csv_to_jsonl(
    csv_path: Path,
    jsonl_path: Path,
    only_reviewed: bool,
) -> tuple[int, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

    rows_out: list[dict] = []
    skipped = 0
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviewed = (row.get("reviewed") or "").strip().lower() in {
                "true", "1", "yes", "sí", "si",
            }
            if only_reviewed and not reviewed:
                skipped += 1
                continue

            labels_raw = (row.get("labels") or "").strip()
            labels = [l.strip() for l in labels_raw.split(",") if l.strip()]
            if not labels:
                skipped += 1
                continue

            rows_out.append(
                {
                    "boletin": (row.get("boletin") or "").strip(),
                    "suma": (row.get("suma") or "").strip(),
                    "labels": labels,
                    "primary_category": (row.get("primary_category") or "").strip()
                                          or labels[0],
                    "materias": (row.get("materias") or "").strip(),
                }
            )

    _write_jsonl(rows_out, jsonl_path)
    return len(rows_out), skipped


# ── 5. CLI ───────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Genera un ground truth semilla a partir de projects_collection, "
            "o convierte un CSV revisado al JSONL final."
        )
    )
    p.add_argument(
        "--output",
        default="backend/evaluation/ground_truth_seed.jsonl",
        help="Ruta del JSONL de salida.",
    )
    p.add_argument(
        "--csv",
        default=None,
        help=(
            "Si se especifica, además del JSONL escribe un CSV editable "
            "(útil para revisar en planilla)."
        ),
    )
    p.add_argument(
        "--per-category", type=int, default=25,
        help="Máximo de proyectos por categoría_principal (estratificación).",
    )
    p.add_argument(
        "--total", type=int, default=None,
        help="Tope global de filas en la salida (después del estratificado).",
    )
    p.add_argument(
        "--seed", type=int, default=42, help="Semilla del shuffle.",
    )
    p.add_argument(
        "--batch-size", type=int, default=256,
        help="Tamaño de página al scrollear Qdrant.",
    )
    p.add_argument(
        "--skip-por-clasificar", action="store_true", default=True,
        help="(default) Excluir proyectos con estado POR_CLASIFICAR.",
    )
    p.add_argument(
        "--include-por-clasificar", action="store_true",
        help="Incluir proyectos sin clasificar.",
    )

    p.add_argument(
        "--from-csv", default=None,
        help=(
            "Convierte un CSV (revisado a mano) al JSONL definido en --output. "
            "Si se pasa esta opción, NO se consulta Qdrant."
        ),
    )
    p.add_argument(
        "--only-reviewed", action="store_true",
        help="Al convertir desde CSV, exportar solo filas con reviewed=true.",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    args = _build_parser().parse_args(argv)
    output_path = Path(args.output)

    # Modo conversión CSV → JSONL (no toca Qdrant)
    if args.from_csv:
        csv_path = Path(args.from_csv)
        n_out, n_skip = _csv_to_jsonl(csv_path, output_path, args.only_reviewed)
        logger.info(
            f"CSV → JSONL: {n_out} filas escritas, {n_skip} saltadas."
        )
        logger.info(f"JSONL en: {output_path}")
        return 0

    # Modo semilla desde Qdrant
    skip_pc = args.skip_por_clasificar and not args.include_por_clasificar

    logger.info("Leyendo projects_collection desde Qdrant...")
    payloads: list[dict] = []
    seen: set[str] = set()
    for payload in _scroll_all_projects(batch_size=args.batch_size):
        b = payload.get("boletin")
        if not b or b in seen:
            continue
        seen.add(b)
        if _is_usable(payload, skip_por_clasificar=skip_pc):
            payloads.append(payload)

    logger.info(f"Total proyectos utilizables: {len(payloads)}")
    if not payloads:
        logger.error(
            "No hay proyectos clasificados en projects_collection. "
            "Corre primero la ingesta (POST /api/v1/ingest/run)."
        )
        return 1

    sampled = _stratified_sample(
        payloads,
        per_category=args.per_category,
        total_cap=args.total,
        seed=args.seed,
    )

    # Escribir JSONL
    jsonl_rows = [_payload_to_jsonl_row(p) for p in sampled]
    _write_jsonl(jsonl_rows, output_path)
    logger.info(f"JSONL escrito en: {output_path} ({len(jsonl_rows)} filas)")

    # Escribir CSV opcional
    if args.csv:
        csv_path = Path(args.csv)
        csv_rows = [_payload_to_csv_row(p) for p in sampled]
        _write_csv(csv_rows, csv_path)
        logger.info(f"CSV escrito en: {csv_path}")

    # Reporte por categoría
    cat_counter: Counter = Counter(p.get("categoria_principal") for p in sampled)
    logger.info("Distribución por categoría_principal en la muestra:")
    for cat, n in cat_counter.most_common():
        logger.info(f"  {cat:<35s} {n:>4d}")

    logger.info(
        "Recuerda: este archivo es una SEMILLA. Antes de evaluar, revisa "
        "y corrige las anotaciones a mano. Las predicciones del clasificador "
        "no constituyen ground truth."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
