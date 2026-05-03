"""
GroundTruthLoader: carga y valida el dataset de evaluación.

Formato JSONL (ground_truth_sample.jsonl):
  {"boletin": "13312-03", "suma": "...", "labels": ["CAT1", "CAT2"], "primary_category": "CAT1"}

Requisitos:
  - Mínimo 200 proyectos anotados manualmente (para validez estadística)
  - Formato multi-label: múltiples categorías por proyecto
  - Manejo de clases desbalanceadas: reportar soporte por clase
  - Ground truth creado por experto en derecho / validación de dominio
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from collections import Counter

logger = logging.getLogger(__name__)

# Buscamos el ground truth en cualquiera de estos nombres (por compatibilidad
# con archivos existentes de la tesis). Se usa el primero que exista.
_GT_DIR = Path(__file__).parent
_GT_CANDIDATES = [
    _GT_DIR / "ground_truth_sample.jsonl",
    _GT_DIR / "ground_truth_to_label.jsonl",
    _GT_DIR / "ground_truth.jsonl",
]


def _resolve_gt_path() -> Path:
    for candidate in _GT_CANDIDATES:
        if candidate.exists():
            return candidate
    # Si no existe ninguno, devolvemos el "canónico" para que el log sea claro.
    return _GT_CANDIDATES[0]


GT_FILE = _resolve_gt_path()


def _coerce_labels(raw) -> list[str]:
    """
    Acepta labels en formatos heterogéneos y lo normaliza a list[str]:
      - ["A", "B"]                           → ["A", "B"]
      - "A"                                  → ["A"]
      - "A, B, C"                            → ["A", "B", "C"]
      - ["A, B, C"]   (string adentro)       → ["A", "B", "C"]
      - None / "" / []                       → []
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
        return [p for p in parts if p]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if isinstance(item, str):
                # Cada item podría ser "A, B, C" en una sola string mal escrita
                out.extend([p.strip() for p in item.split(",") if p.strip()])
            elif item is not None:
                out.append(str(item).strip())
        return [p for p in out if p]
    return [str(raw).strip()]


@dataclass
class GTEntry:
    boletin: str
    suma: str
    labels: list[str]           # multi-label
    primary_category: str
    materias: Optional[str] = None


class GroundTruthLoader:
    """
    Carga el dataset de evaluación y provee estadísticas de distribución.
    """

    def __init__(self, gt_path: Path = GT_FILE):
        self.gt_path = gt_path
        self._entries: list[GTEntry] = []

    def load(self) -> list[GTEntry]:
        if not self.gt_path.exists():
            logger.error(
                f"Ground truth no encontrado. Probé: "
                f"{[str(p) for p in _GT_CANDIDATES]}"
            )
            return []

        logger.info(f"Cargando ground truth desde: {self.gt_path}")

        entries: list[GTEntry] = []
        skipped = 0
        with open(self.gt_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Línea {line_num}: JSON inválido ({e})")
                    skipped += 1
                    continue

                boletin = data.get("boletin")
                suma = data.get("suma")
                labels = _coerce_labels(data.get("labels"))
                if not boletin or not suma or not labels:
                    logger.warning(
                        f"Línea {line_num}: faltan campos obligatorios "
                        f"(boletin/suma/labels). Saltada."
                    )
                    skipped += 1
                    continue

                primary = data.get("primary_category") or labels[0]

                entries.append(
                    GTEntry(
                        boletin=str(boletin),
                        suma=str(suma),
                        labels=labels,
                        primary_category=str(primary),
                        materias=data.get("materias"),
                    )
                )

        self._entries = entries
        logger.info(
            f"Ground truth cargado: {len(entries)} entradas válidas "
            f"(saltadas: {skipped})."
        )
        return entries

    def get_y_true(self) -> list[list[str]]:
        """Retorna lista de listas de etiquetas para métricas multi-label."""
        return [e.labels for e in self._entries]

    def get_all_classes(self) -> list[str]:
        """Retorna todas las clases únicas ordenadas."""
        classes: set[str] = set()
        for e in self._entries:
            classes.update(e.labels)
        return sorted(classes)

    def class_distribution(self) -> dict[str, int]:
        counter: Counter = Counter()
        for e in self._entries:
            for label in e.labels:
                counter[label] += 1
        return dict(counter.most_common())

    def imbalance_ratio(self) -> float:
        """
        Razón de desbalance: max_support / min_support.
        > 10 indica desbalance significativo que justifica F1-weighted sobre accuracy.
        """
        dist = self.class_distribution()
        if not dist:
            return 1.0
        counts = list(dist.values())
        return max(counts) / max(1, min(counts))

    def stats_report(self) -> dict:
        dist = self.class_distribution()
        ir = self.imbalance_ratio()
        return {
            "total_entries": len(self._entries),
            "total_classes": len(dist),
            "class_distribution": dist,
            "imbalance_ratio": round(ir, 2),
            "note": (
                "Imbalance ratio > 10 justifica el uso de F1-weighted como métrica "
                "principal sobre accuracy, que sería engañosa al favorecer clases mayoritarias."
            ) if ir > 5 else "Distribución moderadamente balanceada.",
        }
