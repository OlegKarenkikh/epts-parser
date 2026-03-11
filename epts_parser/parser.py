from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from .mappings import FIELD_MAPPING, RU_LABELS
from .models import VehiclePassportData


class EPTSParser:
    """Parse an ЭПТС (Electronic Vehicle Passport) PDF into a structured data object."""

    _VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
    _EPTS_NUM_RE = re.compile(r"\b(\d{15})\b")
    _DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
    _INN_RE = re.compile(r"\b(\d{10}|\d{12})\b")
    _OGRN_RE = re.compile(r"\b(\d{13}|\d{15})\b")
    _POWER_RE = re.compile(
        r"([\d.,]+)\s*(?:кВт|kW|квт)"
        r"(?:\s*[\(/]?\s*([\d.,]+)\s*(?:л\.с\.|hp|л\.с|лс)\s*[\)]?)?"
    )
    _YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")

    def __init__(self, pdf_path: str | Path, ocr: bool = False) -> None:
        self.pdf_path = Path(pdf_path)
        self.ocr = ocr
        self._data: Optional[VehiclePassportData] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def parse(self) -> VehiclePassportData:
        """Extract data from the PDF and return a VehiclePassportData instance."""
        result = VehiclePassportData()

        if self.ocr:
            text = self._ocr_text()
            self._parse_text(text, result)
        else:
            raw_tables = self._extract_tables(result)
            result.raw_tables = raw_tables
            # Fallback: parse free text for fields still missing
            text = self._extract_text()
            self._parse_text(text, result, overwrite=False)

        self._postprocess(result)
        self._data = result
        return result

    def to_dict(self) -> dict[str, Any]:
        """Return a dict of non-None fields (excludes raw_tables)."""
        if self._data is None:
            self.parse()
        return {
            k: v
            for k, v in dataclasses.asdict(self._data).items()
            if v is not None and k != "raw_tables"
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise extracted data to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_flat_text(self) -> str:
        """Return a human-readable text representation."""
        lines = []
        for field_name, value in self.to_dict().items():
            label = RU_LABELS.get(field_name, field_name)
            lines.append(f"{label}: {value}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_tables(self, result: VehiclePassportData) -> list:
        """Use pdfplumber to read tables and populate *result* in place."""
        raw_tables: list = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    raw_tables.append(table)
                    for row in table:
                        self._process_row(row, result)
        return raw_tables

    def _extract_text(self) -> str:
        """Extract all plain text from the PDF."""
        parts: list[str] = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
        return "\n".join(parts)

    def _process_row(self, row: list, result: VehiclePassportData) -> None:
        """Map a table row (index, label, value) to a VehiclePassportData field."""
        if not row or len(row) < 2:
            return
        # Accept both 2-column (label, value) and 3-column (index, label, value) rows
        if len(row) >= 3:
            label_cell = row[1]
            value_cell = row[2]
        else:
            label_cell = row[0]
            value_cell = row[1]

        if not label_cell or not value_cell:
            return

        label = str(label_cell).strip().lower()
        value = str(value_cell).strip()

        for pattern, field_name in FIELD_MAPPING.items():
            if re.search(pattern, label, re.IGNORECASE):
                # Only set the field if it hasn't been set yet
                if getattr(result, field_name) is None:
                    setattr(result, field_name, value)
                break

    def _parse_text(
        self, text: str, result: VehiclePassportData, overwrite: bool = True
    ) -> None:
        """Regex-based fallback extraction from plain text."""
        if not text:
            return

        def _set(field_name: str, value: str) -> None:
            if overwrite or getattr(result, field_name) is None:
                setattr(result, field_name, value)

        # VIN
        m = self._VIN_RE.search(text)
        if m:
            _set("vin", m.group(1))

        # ЭПТС number (15 digits)
        m = self._EPTS_NUM_RE.search(text)
        if m:
            _set("epts_number", m.group(1))

        # Dates (first = issue_date as heuristic)
        dates = self._DATE_RE.findall(text)
        if dates:
            _set("issue_date", dates[0])

        # INN (10 or 12 digits — heuristic: first match)
        m = self._INN_RE.search(text)
        if m:
            _set("owner_inn", m.group(1))

        # OGRN (13 or 15 digits — heuristic: first match)
        m = self._OGRN_RE.search(text)
        if m:
            _set("owner_ogrn", m.group(1))

    def _postprocess(self, result: VehiclePassportData) -> None:
        """Normalise fields after extraction."""
        # Normalise VIN to uppercase
        if result.vin:
            result.vin = result.vin.upper().strip()

        # Extract 4-digit year from longer strings like "2007 г." or "07.06.2007"
        if result.year:
            m = self._YEAR_RE.search(result.year)
            if m:
                result.year = m.group(1)

        # Split combined engine power "77.0 кВт (104.7 л.с.)" into kW and hp
        if result.engine_power_kw:
            raw = result.engine_power_kw
            m = self._POWER_RE.search(raw)
            if m:
                result.engine_power_kw = m.group(1)
                if m.group(2):
                    result.engine_power_hp = m.group(2)

        # Strip extraneous whitespace from all string fields
        for f in dataclasses.fields(result):
            if f.name == "raw_tables":
                continue
            val = getattr(result, f.name)
            if isinstance(val, str):
                setattr(result, f.name, val.strip() or None)

    def _ocr_text(self) -> str:
        """Return text extracted via OCR (requires pdf2image + pytesseract)."""
        from .ocr import pdf_to_text_via_ocr  # lazy import

        return pdf_to_text_via_ocr(self.pdf_path)
