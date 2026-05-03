"""
analyze_errors.py — Audita las predicciones de H0 y agrupa errores por tipo
para que sea fácil identificar qué arreglar primero.

Lee: backend/evaluation/results/predictions_h0_hybrid.jsonl
Imprime: ranking de subcategorías con más errores + detalle por caso.

Uso:
    python -m backend.evaluation.analyze_errors

    # Filtrar a una subcategoría específica:
    python -m backend.evaluation.analyze_errors --subcategory CONTRATOS_LABORALES

    # Mostrar solo los errores de categoría principal:
    python -m backend.evaluation.analyze_errors --only primary

    # Salida JSON estructurada para procesar:
    python -m backend.evaluation.analyze_errors --json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PREDICTIONS_FILE = (
    Path(__file__).resolve().parent / "results" / "predictions_h0_hybrid.jsonl"
)


def _load(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Corre primero POST /api/v1/eval/run."
        )
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _classify_error(row: dict) -> str:
    """
    Tipos de error:
      - OK_TOTAL: primary y subcategorías exactas
      - OK_PRIMARY_SUB_PARTIAL: primary correcta, subcategorías incompletas o extras
      - WRONG_PRIMARY: categoría principal incorrecta
      - POR_CLASIFICAR: el sistema no clasificó
    """
    if row.get("estado") == "POR_CLASIFICAR":
        return "POR_CLASIFICAR"
    if row["predicted_primary_category"] != row["ground_truth_primary"]:
        return "WRONG_PRIMARY"
    gt_secondary = set(row.get("ground_truth_secondary") or [])
    pred_secondary = set(row.get("predicted_subcategories") or [])
    if gt_secondary == pred_secondary:
        return "OK_TOTAL"
    return "OK_PRIMARY_SUB_PARTIAL"


def _diff_subcategories(row: dict) -> tuple[set[str], set[str]]:
    """Devuelve (faltantes, extras) entre GT y predicción."""
    gt = set(row.get("ground_truth_secondary") or [])
    pred = set(row.get("predicted_subcategories") or [])
    missing = gt - pred           # FN: el sistema no las predijo
    spurious = pred - gt          # FP: el sistema las inventó
    return missing, spurious


def _summary_by_subcategory(rows: list[dict]) -> dict[str, dict]:
    """
    Por subcategoría calcula:
      - support (apariciones en GT)
      - false_negatives (no predicha cuando estaba en GT)
      - false_positives (predicha cuando no estaba en GT)
    """
    stats: dict[str, dict] = defaultdict(
        lambda: {"support": 0, "fn": 0, "fp": 0, "tp": 0}
    )
    for row in rows:
        gt = set(row.get("ground_truth_secondary") or [])
        pred = set(row.get("predicted_subcategories") or [])
        for sub in gt:
            stats[sub]["support"] += 1
            if sub in pred:
                stats[sub]["tp"] += 1
            else:
                stats[sub]["fn"] += 1
        for sub in pred - gt:
            stats[sub]["fp"] += 1
    # Calcular F1 por clase
    for sub, d in stats.items():
        precision = d["tp"] / max(1, d["tp"] + d["fp"])
        recall = d["tp"] / max(1, d["tp"] + d["fn"])
        f1 = 2 * precision * recall / max(1e-9, precision + recall)
        d["precision"] = round(precision, 3)
        d["recall"] = round(recall, 3)
        d["f1"] = round(f1, 3)
    return dict(stats)


def _print_table(title: str, rows: list[tuple]) -> None:
    print(f"\n{'='*70}\n{title}\n{'='*70}")
    if not rows:
        print("  (vacío)")
        return
    for r in rows:
        print("  " + " | ".join(str(c) for c in r))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(PREDICTIONS_FILE),
                        help="Ruta a predictions_h0_hybrid.jsonl")
    parser.add_argument("--subcategory", default=None,
                        help="Filtra solo errores donde aparece esta subcategoría")
    parser.add_argument("--only", choices=["primary", "subs", "all"], default="all",
                        help="Tipo de errores a mostrar")
    parser.add_argument("--json", action="store_true",
                        help="Salida en JSON estructurado")
    args = parser.parse_args()

    rows = _load(Path(args.file))

    # Clasificar cada fila por tipo de error
    error_types: Counter = Counter()
    for r in rows:
        error_types[_classify_error(r)] += 1

    # Stats por subcategoría
    sub_stats = _summary_by_subcategory(rows)

    # Errores específicos
    error_rows: list[dict] = []
    for r in rows:
        etype = _classify_error(r)
        if etype == "OK_TOTAL":
            continue
        missing, spurious = _diff_subcategories(r)
        error_rows.append(
            {
                "boletin": r["boletin"],
                "error_type": etype,
                "gt_primary": r["ground_truth_primary"],
                "pred_primary": r["predicted_primary_category"],
                "gt_secondary": sorted(r.get("ground_truth_secondary") or []),
                "pred_secondary": sorted(r.get("predicted_subcategories") or []),
                "missing": sorted(missing),       # falsos negativos
                "spurious": sorted(spurious),     # falsos positivos
                "match_methods": r.get("match_methods") or [],
                "confidence": r.get("confidence"),
            }
        )

    # Filtros
    if args.subcategory:
        sub = args.subcategory
        error_rows = [
            e for e in error_rows
            if sub in e["missing"] or sub in e["spurious"]
        ]
    if args.only == "primary":
        error_rows = [e for e in error_rows if e["error_type"] == "WRONG_PRIMARY"]
    elif args.only == "subs":
        error_rows = [e for e in error_rows if e["error_type"] == "OK_PRIMARY_SUB_PARTIAL"]

    if args.json:
        print(json.dumps(
            {
                "total_entries": len(rows),
                "error_distribution": dict(error_types),
                "subcategory_stats": sub_stats,
                "errors": error_rows,
            },
            ensure_ascii=False, indent=2,
        ))
        return 0

    # ── Reporte humano ───────────────────────────────────────────────────────
    print(f"\nTotal entradas: {len(rows)}")
    print(f"Distribución de errores: {dict(error_types)}")

    # Top subcategorías con peor F1 y support > 0
    ranked = sorted(
        [(s, d) for s, d in sub_stats.items() if d["support"] > 0],
        key=lambda x: (x[1]["f1"], -x[1]["support"]),
    )
    _print_table(
        "Subcategorías ordenadas por F1 ASC (peores primero)",
        [
            (
                f"{sub:<28}",
                f"sup={d['support']}",
                f"tp={d['tp']}",
                f"fn={d['fn']}",
                f"fp={d['fp']}",
                f"P={d['precision']}",
                f"R={d['recall']}",
                f"F1={d['f1']}",
            )
            for sub, d in ranked
        ],
    )

    # Subcategorías que el sistema PREDICE pero NO están en el GT (puro ruido)
    pure_fp = [(s, d) for s, d in sub_stats.items() if d["support"] == 0 and d["fp"] > 0]
    if pure_fp:
        _print_table(
            "Subcategorías con falsos positivos puros (sistema las predice "
            "pero no aparecen en el GT — fuentes de ruido)",
            [(f"{sub:<28}", f"fp={d['fp']}") for sub, d in
             sorted(pure_fp, key=lambda x: -x[1]["fp"])],
        )

    # Detalle de errores
    print(f"\n{'='*70}\nDETALLE DE ERRORES ({len(error_rows)} casos)\n{'='*70}")
    for e in error_rows:
        print(f"\n  Boletín: {e['boletin']}  [{e['error_type']}]")
        print(f"    GT primary    : {e['gt_primary']}")
        print(f"    Pred primary  : {e['pred_primary']}")
        print(f"    GT subs       : {e['gt_secondary']}")
        print(f"    Pred subs     : {e['pred_secondary']}")
        if e["missing"]:
            print(f"    Faltantes (FN): {e['missing']}")
        if e["spurious"]:
            print(f"    Espurias (FP) : {e['spurious']}")
        print(f"    Métodos       : {e['match_methods']}")
        print(f"    Confianza     : {e['confidence']}")

    print(f"\nSugerencia: corre /classify/diagnose con cada boletín errado:")
    print('  curl -X POST http://localhost:8000/api/v1/classify/diagnose \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"boletin": "<BOLETIN>"}\' | jq')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
