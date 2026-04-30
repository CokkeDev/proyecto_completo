"""
ProjectNormalizer: limpia y normaliza los campos raw de la API del Senado.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NormalizedProject:
    id_proyecto: int
    boletin: str
    suma: str
    suma_clean: str
    fecha_ingreso: str          # "YYYY-MM-DD"
    fecha_ingreso_raw: str      # "DD/MM/YYYY"
    iniciativa: str             # "Mensaje" | "Moción"
    tipo: str
    camara_origen: str          # "C.Diputados" | "Senado"
    autores: list[str]
    materias: list[str]
    etapa: str
    link_proyecto: str
    documento_url: str
    texto_clasificacion: str    # suma + materias concatenados
    year: int
    month: int


class ProjectNormalizer:
    """
    Transforma el dict raw de la API en un NormalizedProject.
    """

    def normalize(self, raw: dict) -> Optional[NormalizedProject]:
        try:
            return self._normalize(raw)
        except Exception:
            return None

    def normalize_batch(self, raws: list[dict]) -> list[NormalizedProject]:
        results = []
        for raw in raws:
            n = self.normalize(raw)
            if n:
                results.append(n)
        return results

    # ── Lógica interna ────────────────────────────────────────────────────────
    def _normalize(self, raw: dict) -> NormalizedProject:
        boletin = str(raw.get("BOLETIN", "")).strip()
        suma_raw = str(raw.get("SUMA", "") or "").strip()
        suma_clean = self._clean_text(suma_raw)

        materias_raw = raw.get("MATERIAS", "") or ""
        materias = self._parse_materias(materias_raw)

        texto = self._build_classification_text(suma_clean, materias)

        fecha_str = str(raw.get("FECHA_INGRESO", "") or "")
        fecha_iso, year, month = self._parse_date(fecha_str)

        autores_raw = str(raw.get("AUTORES", "") or "")
        autores = [a.strip() for a in autores_raw.split("/") if a.strip()]

        return NormalizedProject(
            id_proyecto=int(raw.get("ID_PROYECTO", 0)),
            boletin=boletin,
            suma=suma_raw,
            suma_clean=suma_clean,
            fecha_ingreso=fecha_iso,
            fecha_ingreso_raw=fecha_str,
            iniciativa=str(raw.get("INICIATIVA", "") or "").strip(),
            tipo=str(raw.get("TIPO", "") or "").strip(),
            camara_origen=str(raw.get("CAMARA_ORIGEN", "") or "").strip(),
            autores=autores,
            materias=materias,
            etapa=str(raw.get("ETAPA", "") or "").strip(),
            link_proyecto=str(raw.get("LINK_PROYECTO_LEY", "") or "").strip(),
            documento_url=str(raw.get("DOCUMENTO", "") or "").strip(),
            texto_clasificacion=texto,
            year=year,
            month=month,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """Limpia HTML residual, múltiples espacios y normaliza unicode."""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = unicodedata.normalize("NFD", text)
        text = "".join(
            char for char in text
            if unicodedata.category(char) != "Mn"
        )
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return text.strip()

    @staticmethod
    def _parse_materias(raw: str) -> list[str]:
        """'CORONAVIRUS/ COVID-19/ PANDEMIA' → ['CORONAVIRUS', 'COVID-19', 'PANDEMIA']"""
        if not raw:
            return []
        return [m.strip().upper() for m in raw.split("/") if m.strip()]

    @staticmethod
    def _build_classification_text(suma: str, materias: list[str]) -> str:
        parts = [suma]
        if materias:
            parts.append(" ".join(materias))
        return " ".join(parts)

    @staticmethod
    def _parse_date(date_str: str) -> tuple[str, int, int]:
        """'DD/MM/YYYY' → ('YYYY-MM-DD', year, month)"""
        try:
            dt = datetime.strptime(date_str.strip(), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d"), dt.year, dt.month
        except ValueError:
            return "1900-01-01", 1900, 1
