from __future__ import annotations

import json
import time
import statistics
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Optional

import numpy as np

from backend.embeddings.encoder import BGEEncoder
from backend.qdrant.client import QdrantManager
from backend.qdrant.schemas import COLLECTION_NAME


@dataclass
class QueryResult:
    query_id: str
    query: str
    expected_boletines: list[str]
    retrieved_boletines: list[str]
    response_time_seconds: float
    mean_cosine_top_k: float
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float


@dataclass
class Hypothesis1Summary:
    total_queries: int
    avg_response_time_seconds: float
    max_response_time_seconds: float
    avg_cosine_similarity: float
    avg_precision_at_k: float
    avg_recall_at_k: float
    mrr: float
    passes_time_condition: bool
    passes_cosine_condition: bool
    passes_relevance_condition: bool
    hypothesis_h1_validated: bool


class Hypothesis1Evaluator:
    """
    Evalúa H1 sobre el sistema real del proyecto:
      - tiempo de respuesta de búsqueda semántica
      - similitud coseno promedio
      - relevancia por Precision@k / Recall@k / MRR
    """

    def __init__(
        self,
        top_k: int = 5,
        score_threshold: float = 0.35,
        max_avg_time_seconds: float = 5.0,
        min_avg_cosine: float = 0.75,
        min_avg_precision_at_k: float = 0.60,
    ):
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.max_avg_time_seconds = max_avg_time_seconds
        self.min_avg_cosine = min_avg_cosine
        self.min_avg_precision_at_k = min_avg_precision_at_k

        self.encoder = BGEEncoder.get_instance()
        self.qdrant = QdrantManager()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def _search_with_vectors(self, query_text: str) -> tuple[np.ndarray, list[Any]]:
        query_vec = self.encoder.encode_for_query(query_text)

        response = self.qdrant.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec.tolist(),
            limit=self.top_k,
            score_threshold=self.score_threshold,
            with_payload=True,
            with_vectors=True,
        )

        points = getattr(response, "points", response)
        return query_vec, points

    def _precision_at_k(self, retrieved: list[str], expected: set[str], k: int) -> float:
        if k == 0:
            return 0.0
        rel = sum(1 for b in retrieved[:k] if b in expected)
        return rel / k

    def _recall_at_k(self, retrieved: list[str], expected: set[str], k: int) -> float:
        if not expected:
            return 0.0
        rel = sum(1 for b in retrieved[:k] if b in expected)
        return rel / len(expected)

    def _reciprocal_rank(self, retrieved: list[str], expected: set[str]) -> float:
        for idx, boletin in enumerate(retrieved, start=1):
            if boletin in expected:
                return 1.0 / idx
        return 0.0

    def evaluate_query(self, query_entry: dict[str, Any]) -> QueryResult:
        query_id = str(query_entry["id"])
        query = query_entry["query"]
        expected_boletines = query_entry.get("expected_boletines", [])

        start = time.perf_counter()
        query_vec, points = self._search_with_vectors(query)
        elapsed = time.perf_counter() - start

        cosines: list[float] = []
        retrieved_boletines: list[str] = []

        for p in points:
            payload = getattr(p, "payload", {}) or {}
            boletin = payload.get("boletin")
            if boletin:
                retrieved_boletines.append(str(boletin))

            vector = getattr(p, "vector", None)
            if vector is not None:
                doc_vec = np.array(vector, dtype=np.float32)
                cosines.append(self._cosine_similarity(query_vec, doc_vec))

        expected_set = set(expected_boletines)

        return QueryResult(
            query_id=query_id,
            query=query,
            expected_boletines=expected_boletines,
            retrieved_boletines=retrieved_boletines,
            response_time_seconds=round(elapsed, 4),
            mean_cosine_top_k=round(float(statistics.mean(cosines)) if cosines else 0.0, 4),
            precision_at_k=round(self._precision_at_k(retrieved_boletines, expected_set, self.top_k), 4),
            recall_at_k=round(self._recall_at_k(retrieved_boletines, expected_set, self.top_k), 4),
            reciprocal_rank=round(self._reciprocal_rank(retrieved_boletines, expected_set), 4),
        )

    def run(self, queries_path: str, output_path: Optional[str] = None) -> dict[str, Any]:
        path = Path(queries_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo de queries: {path.resolve()}")

        with path.open("r", encoding="utf-8") as f:
            queries = json.load(f)

        if not isinstance(queries, list) or not queries:
            raise ValueError("El archivo de queries debe contener una lista no vacía.")

        results: list[QueryResult] = [self.evaluate_query(q) for q in queries]

        avg_time = statistics.mean(r.response_time_seconds for r in results)
        max_time = max(r.response_time_seconds for r in results)
        avg_cosine = statistics.mean(r.mean_cosine_top_k for r in results)
        avg_precision = statistics.mean(r.precision_at_k for r in results)
        avg_recall = statistics.mean(r.recall_at_k for r in results)
        mrr = statistics.mean(r.reciprocal_rank for r in results)

        passes_time = avg_time < self.max_avg_time_seconds
        passes_cosine = avg_cosine > self.min_avg_cosine
        passes_relevance = avg_precision >= self.min_avg_precision_at_k

        summary = Hypothesis1Summary(
            total_queries=len(results),
            avg_response_time_seconds=round(avg_time, 4),
            max_response_time_seconds=round(max_time, 4),
            avg_cosine_similarity=round(avg_cosine, 4),
            avg_precision_at_k=round(avg_precision, 4),
            avg_recall_at_k=round(avg_recall, 4),
            mrr=round(mrr, 4),
            passes_time_condition=passes_time,
            passes_cosine_condition=passes_cosine,
            passes_relevance_condition=passes_relevance,
            hypothesis_h1_validated=passes_time and passes_cosine and passes_relevance,
        )

        report = {
            "summary": asdict(summary),
            "queries": [asdict(r) for r in results],
            "criteria": {
                "max_avg_time_seconds": self.max_avg_time_seconds,
                "min_avg_cosine": self.min_avg_cosine,
                "min_avg_precision_at_k": self.min_avg_precision_at_k,
                "top_k": self.top_k,
                "score_threshold": self.score_threshold,
            },
        }

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

        return report


if __name__ == "__main__":
    evaluator = Hypothesis1Evaluator(
        top_k=5,
        score_threshold=0.35,
        max_avg_time_seconds=5.0,
        min_avg_cosine=0.75,
        min_avg_precision_at_k=0.60,
    )

    report = evaluator.run(
        queries_path="backend/evaluation/h1_queries.json",
        output_path="backend/evaluation/results/h1_report.json",
    )

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))