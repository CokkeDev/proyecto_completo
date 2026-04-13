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

GT_FILE = Path(__file__).parent / "ground_truth_sample.jsonl"


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
            logger.error(f"Ground truth no encontrado en {self.gt_path}")
            return []

        entries = []
        with open(self.gt_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    data = json.loads(line)
                    entries.append(
                        GTEntry(
                            boletin=data["boletin"],
                            suma=data["suma"],
                            labels=data["labels"],
                            primary_category=data.get("primary_category", data["labels"][0]),
                            materias=data.get("materias"),
                        )
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Línea {line_num} inválida: {e}")

        self._entries = entries
        logger.info(f"Ground truth cargado: {len(entries)} entradas.")
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
