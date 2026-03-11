from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from .mappings import FIELD_MAPPING, RU_LABELS
from .models import VehiclePassportData, _ECO_WORDS, _to_int, _to_float


class EPTSParser:
    _VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
    _EPTS_NUM_RE = re.compile(r"\b(\d{15})\b")
    _DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
    _INN_RE = re.compile(r"\b\u0418\u041d\u041d\b[^\d]*(\d{10}|\d{12})")
    _OGRN_RE = re.compile(r"\b\u041e\u0413\u0420\u041d\b[^\d]*(\d{13}|\d{15})")
    _POWER_RE = re.compile(
        r"([\d.,]+)\s*(?:\u043a\u0412\u0442|kW|\u043a\u0432\u0442)"
        r"(?:\s*[\(/]?\s*([\d.,]+)\s*(?:\u043b\.\u0441\.|hp|\u043b\.\u0441|\u043b\u0441)\s*[\)]?)?"
    )
    _YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
    _INLINE_PATTERNS: list[tuple[re.Pattern, str]] | None = None

    def __init__(self, pdf_path: str | Path, ocr: bool = False) -> None:
        self.pdf_path = Path(pdf_path)
        self.ocr = ocr
        self._data: Optional[VehiclePassportData] = None

    def parse(self) -> VehiclePassportData:
        result = VehiclePassportData()
        if self.ocr:
            text = self._ocr_text()
            self._parse_text(text, result)
        else:
            raw_tables: list = []
            text_parts: list[str] = []
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        raw_tables.append(table)
                        for row in table:
                            self._process_row(row, result)
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            result.raw_tables = raw_tables
            full_text = "\n".join(text_parts)
            self._parse_text(full_text, result, overwrite=False)
            self._parse_inline(full_text, result)
        self._postprocess(result)
        self._data = result
        return result

    def to_dict(self) -> dict[str, Any]:
        if self._data is None:
            self.parse()
        return {
            k: v
            for k, v in dataclasses.asdict(self._data).items()
            if v is not None and k != "raw_tables"
        }

    def to_typed_dict(self) -> dict[str, Any]:
        if self._data is None:
            self.parse()
        return self._data.to_typed_dict()

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_flat_text(self) -> str:
        lines = []
        for field_name, value in self.to_dict().items():
            label = RU_LABELS.get(field_name, field_name)
            lines.append(f"{label}: {value}")
        return "\n".join(lines)

    def _process_row(self, row: list, result: VehiclePassportData) -> None:
        if not row or len(row) < 2:
            return
        label_cell, value_cell = (row[1], row[2]) if len(row) >= 3 else (row[0], row[1])
        if not label_cell or not value_cell:
            return
        label = str(label_cell).strip().lower()
        value = str(value_cell).strip()
        for pattern, field_name in FIELD_MAPPING.items():
            if re.search(pattern, label, re.IGNORECASE):
                if getattr(result, field_name, None) is None:
                    setattr(result, field_name, value)
                break

    @classmethod
    def _get_inline_patterns(cls) -> list[tuple[re.Pattern, str]]:
        if cls._INLINE_PATTERNS is not None:
            return cls._INLINE_PATTERNS
        compiled = []
        for raw_pat, field_name in FIELD_MAPPING.items():
            stripped = raw_pat.lstrip("^").rstrip("$")
            pat = re.compile(
                r"(?i)^" + stripped + r"[\s:\-\(\)]*(.+)$",
                re.UNICODE,
            )
            compiled.append((pat, field_name))
        cls._INLINE_PATTERNS = compiled
        return compiled

    def _parse_inline(self, text: str, result: VehiclePassportData) -> None:
        patterns = self._get_inline_patterns()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            for pat, field_name in patterns:
                m = pat.match(line)
                if m:
                    value = m.group(1).strip()
                    if value and getattr(result, field_name, None) is None:
                        setattr(result, field_name, value)
                    break

    def _parse_text(
        self, text: str, result: VehiclePassportData, overwrite: bool = True
    ) -> None:
        if not text:
            return

        def _set(field_name: str, value: str) -> None:
            if overwrite or getattr(result, field_name, None) is None:
                setattr(result, field_name, value)

        m = self._VIN_RE.search(text)
        if m:
            _set("vin", m.group(1))
        m = self._EPTS_NUM_RE.search(text)
        if m:
            _set("epts_number", m.group(1))
        dates = self._DATE_RE.findall(text)
        if dates:
            _set("issue_date", dates[0])
        m = self._INN_RE.search(text)
        if m:
            _set("owner_inn", m.group(1))
        m = self._OGRN_RE.search(text)
        if m:
            _set("owner_ogrn", m.group(1))

    def _postprocess(self, result: VehiclePassportData) -> None:
        if result.vin:
            result.vin = result.vin.upper().strip()

        # Extract 4-digit year from strings like "2019 г."
        if result.year:
            m = self._YEAR_RE.search(result.year)
            result.year = m.group(1) if m else None

        # Normalize eco class: word -> digit
        if result.eco_class:
            result.eco_class = _ECO_WORDS.get(
                result.eco_class.lower().strip(), result.eco_class
            )
            # keep only leading digit
            m2 = re.match(r"(\d+)", result.eco_class)
            if m2:
                result.eco_class = m2.group(1)

        # Seats: keep only leading integer (handles "5 (1-2, 2-3)" or "45 мест")
        if result.seats_count:
            m3 = re.search(r"(\d+)", result.seats_count)
            result.seats_count = m3.group(1) if m3 else None

        # Mass fields: strip kg-unit suffixes, keep numeric string
        for mass_f in ("max_mass", "curb_mass"):
            val = getattr(result, mass_f)
            if val:
                m4 = re.search(r"(\d[\d\s]*)", val.replace("\xa0", ""))
                setattr(result, mass_f, m4.group(1).strip() if m4 else None)

        # Engine volume: keep numeric part (cm3)
        if result.engine_volume:
            m5 = re.search(r"(\d+)", result.engine_volume)
            result.engine_volume = m5.group(1) if m5 else None

        # Engine power: split "77.0 kVt (104.7 l.s.)" -> kw + hp
        if result.engine_power_kw:
            raw = result.engine_power_kw
            m6 = self._POWER_RE.search(raw)
            if m6:
                result.engine_power_kw = m6.group(1).replace(",", ".")
                if m6.group(2):
                    result.engine_power_hp = m6.group(2).replace(",", ".")
            else:
                # "64,7 (5800)" format — keep first number
                m7 = re.match(r"([\d]+[.,]\d+|\d+)", raw)
                if m7:
                    result.engine_power_kw = m7.group(1).replace(",", ".")

        # 30-min electric power: keep first number
        if result.engine_power_30min_kw:
            m8 = re.match(r"([\d]+[.,]?\d*)", result.engine_power_30min_kw)
            if m8:
                result.engine_power_30min_kw = m8.group(1).replace(",", ".")

        # Strip whitespace from all string fields
        for f in dataclasses.fields(result):
            if f.name == "raw_tables":
                continue
            val = getattr(result, f.name)
            if isinstance(val, str):
                cleaned = val.strip()
                setattr(result, f.name, cleaned if cleaned else None)

    def _ocr_text(self) -> str:
        from .ocr import pdf_to_text_via_ocr
        return pdf_to_text_via_ocr(self.pdf_path)
