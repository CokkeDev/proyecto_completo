"""
DocumentFetcher: descarga y extrae texto de documentos PDF de proyectos de ley.

Estrategia:
  1. Descarga el documento desde la URL del campo DOCUMENTO de la API
  2. Detecta Content-Type: PDF → pypdf, HTML → extractor simple
  3. Retorna texto limpio o None si falla (el pipeline cae a suma+materias)
"""
from __future__ import annotations

import io
import logging
import re
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_MB = 15
TIMEOUT_SEC = 45
MAX_CLASSIFICATION_WORDS = 1500  # palabras usadas para clasificar (no para Qdrant)


class DocumentFetcher:
    """Descarga y extrae texto del documento adjunto a un proyecto de ley."""

    def __init__(self, timeout: int = TIMEOUT_SEC):
        self.timeout = timeout

    def fetch_text(self, documento_url: str) -> Optional[str]:
        """
        Descarga y extrae texto del documento en documento_url.

        Retorna texto limpio (máx. MAX_CLASSIFICATION_WORDS palabras)
        o None si el documento no está disponible o no es parseable.
        """
        if not documento_url or not documento_url.startswith("http"):
            return None

        try:
            raw_bytes, content_type = self._download(documento_url)
            if not raw_bytes:
                return None

            if "pdf" in content_type:
                text = self._extract_pdf(raw_bytes)
            elif "html" in content_type or "text" in content_type:
                text = self._extract_html(raw_bytes)
            else:
                # Intenta PDF de todos modos (a veces el Content-Type es incorrecto)
                text = self._extract_pdf(raw_bytes)

            if not text or len(text.strip()) < 100:
                return None

            # Truncar para clasificación (no para chunks de Qdrant)
            words = text.split()
            if len(words) > MAX_CLASSIFICATION_WORDS:
                text = " ".join(words[:MAX_CLASSIFICATION_WORDS])

            return text.strip()

        except Exception as e:
            logger.warning(f"Error procesando documento {documento_url}: {e}")
            return None

    def _download(self, url: str) -> tuple[Optional[bytes], str]:
        """Descarga la URL y retorna (bytes, content_type)."""
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for attempt in range(2):
                try:
                    response = client.get(url)
                    response.raise_for_status()

                    size_mb = len(response.content) / (1024 * 1024)
                    if size_mb > MAX_PDF_SIZE_MB:
                        logger.warning(f"Documento demasiado grande ({size_mb:.1f} MB): {url}")
                        return None, ""

                    content_type = response.headers.get("content-type", "").lower()
                    return response.content, content_type

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.debug(f"Documento no encontrado (404): {url}")
                        return None, ""
                    if attempt == 0:
                        time.sleep(3)
                    else:
                        logger.warning(f"HTTP {e.response.status_code} al descargar {url}")
                        return None, ""
                except httpx.RequestError as e:
                    if attempt == 0:
                        time.sleep(3)
                    else:
                        logger.warning(f"Error de red al descargar {url}: {e}")
                        return None, ""

        return None, ""

    def _extract_pdf(self, raw_bytes: bytes) -> Optional[str]:
        """Extrae texto de un PDF usando pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            pages_text: list[str] = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(text.strip())
            full_text = "\n".join(pages_text)
            return self._clean_extracted_text(full_text) if full_text else None
        except Exception as e:
            logger.debug(f"pypdf no pudo extraer texto: {e}")
            return None

    def _extract_html(self, raw_bytes: bytes) -> Optional[str]:
        """Extrae texto visible de HTML eliminando etiquetas."""
        try:
            html = raw_bytes.decode("utf-8", errors="replace")
            # Eliminar scripts, styles y etiquetas
            html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r"<[^>]+>", " ", html)
            html = re.sub(r"&nbsp;", " ", html)
            html = re.sub(r"&[a-z]+;", " ", html)
            return self._clean_extracted_text(html)
        except Exception as e:
            logger.debug(f"Error extrayendo HTML: {e}")
            return None

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Limpia el texto extraído: normaliza espacios y elimina líneas vacías."""
        # Normalizar saltos de línea múltiples
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Normalizar espacios
        text = re.sub(r"[ \t]{2,}", " ", text)
        # Eliminar líneas que solo tienen guiones o números de página
        lines = [line.strip() for line in text.split("\n")]
        lines = [l for l in lines if len(l) > 5 and not re.match(r"^[\-\=\d\s]+$", l)]
        return " ".join(lines)
