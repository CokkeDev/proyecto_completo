"""
SenadoAPIFetcher: descarga proyectos de ley desde la API REST del Senado.

Maneja paginación, reintentos y errores de red.
"""
from __future__ import annotations

import logging
import time
from typing import Iterator

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class SenadoAPIFetcher:
    """
    Descarga proyectos de ley del endpoint:
    /v3/proyectos?desde=...&hasta=...&offset=...&limit=...&order=asc
    """

    BASE_URL = settings.senado_api_base
    PAGE_SIZE = 200  # Tamaño de página para la paginación interna

    def __init__(
        self,
        desde: str = settings.senado_api_desde,
        hasta: str = settings.senado_api_hasta,
        timeout: int = settings.senado_api_timeout,
    ):
        self.desde = desde
        self.hasta = hasta
        self.timeout = timeout

    # ── Fetch completo ────────────────────────────────────────────────────────
    def fetch_all(self) -> list[dict]:
        """
        Descarga todos los proyectos en el rango configurado.
        Itera por páginas hasta agotar resultados.
        """
        all_projects: list[dict] = []
        offset = 0

        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            while True:
                batch = self._fetch_page(client, offset, self.PAGE_SIZE)
                if not batch:
                    break
                all_projects.extend(batch)
                logger.info(
                    f"Descargados {len(all_projects)} proyectos (offset={offset})."
                )
                if len(batch) < self.PAGE_SIZE:
                    break  # última página
                offset += self.PAGE_SIZE
                time.sleep(0.3)  # respetar rate limit

        logger.info(f"Total descargado: {len(all_projects)} proyectos.")
        return all_projects

    def fetch_last_n(self, n: int) -> list[dict]:
        """
        Descarga los N proyectos más recientes (order=desc, sin filtro de fechas).
        Útil para el pipeline demo con texto completo.
        """
        url = f"{self.BASE_URL}/proyectos"
        params = {
            "limit": n,
            "offset": 0,
            "order": "desc",
        }
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            for attempt in range(3):
                try:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, list):
                        return data[:n]
                    if isinstance(data, dict):
                        items = data.get("data", data.get("proyectos", []))
                        return items[:n]
                    return []
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP {e.response.status_code} al buscar últimos {n} proyectos")
                    if attempt < 2:
                        time.sleep(3)
                except httpx.RequestError as e:
                    logger.error(f"Error de red (intento {attempt+1}/3): {e}")
                    if attempt < 2:
                        time.sleep(2)
        return []

    def fetch_iter(self) -> Iterator[list[dict]]:
        """Versión generadora para procesamiento por lotes sin acumular en memoria."""
        offset = 0
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            while True:
                batch = self._fetch_page(client, offset, self.PAGE_SIZE)
                if not batch:
                    return
                yield batch
                if len(batch) < self.PAGE_SIZE:
                    return
                offset += self.PAGE_SIZE
                time.sleep(0.3)

    # ── Fetch de página ───────────────────────────────────────────────────────
    def _fetch_page(
        self, client: httpx.Client, offset: int, limit: int
    ) -> list[dict]:
        url = f"{self.BASE_URL}/proyectos"
        params = {
            "desde": self.desde,
            "hasta": self.hasta,
            "offset": offset,
            "limit": limit,
            "order": "asc",
        }
        for attempt in range(3):
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                # La API puede devolver lista directa o dict con clave "data"
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("data", data.get("proyectos", []))
                return []
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                if e.response.status_code in (429, 503):
                    time.sleep(5 * (attempt + 1))
                else:
                    raise
            except httpx.RequestError as e:
                logger.error(f"Request error (intento {attempt+1}/3): {e}")
                time.sleep(2 * (attempt + 1))

        logger.error(f"Falló fetch tras 3 intentos (offset={offset}).")
        return []
    
    def fetch_by_boletin(self, boletin: str):
        url = f"{self.BASE_URL}/proyectos?boletin={boletin}"

        response = httpx.get(url)

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, dict):
            return data.get("data", [])

        if not data:
            return []

        return data if isinstance(data, list) else [data]

