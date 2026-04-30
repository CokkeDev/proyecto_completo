"""
TextChunker: divide textos largos en chunks solapados.

Estrategia: palabras (no tokens) para simplicidad y velocidad.
BAAI/bge-m3 puede procesar hasta 8192 tokens (~6000 palabras),
pero chunks más pequeños mejoran la precisión de recuperación.
"""
from __future__ import annotations

from dataclasses import dataclass
from backend.config import settings


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    start_word: int
    end_word: int
    is_single: bool  # True si el texto completo cabe en un chunk


class TextChunker:
    """
    Divide texto en chunks solapados de tamaño fijo (en palabras).

    Parámetros:
        chunk_size    : palabras por chunk (default 400)
        chunk_overlap : palabras de solapamiento entre chunks (default 50)
    """

    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[TextChunk]:
        words = text.split()
        if len(words) <= self.chunk_size:
            return [
                TextChunk(
                    text=text,
                    chunk_index=0,
                    start_word=0,
                    end_word=len(words),
                    is_single=True,
                )
            ]

        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        step = max(1, self.chunk_size - self.chunk_overlap)

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    chunk_index=idx,
                    start_word=start,
                    end_word=end,
                    is_single=False,
                )
            )
            if end == len(words):
                break
            start += step
            idx += 1

        return chunks
