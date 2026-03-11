from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from .mappings import FIELD_MAPPING, RU_LABELS
from .models import VehiclePassportData, _ECO_WORDS

# ---------------------------------------------------------------------------
# Exact single-line patterns derived from real 2026 EPTS PDF text.
# Each tuple: (compiled_re, field_name, value_group_index)
# The regex MUST match the full line; group(1) or group(2) is the value.
# Priority: first match wins, so more-specific patterns come first.
# ---------------------------------------------------------------------------
_LINE_RULES: list[tuple[re.Pattern, str]] = [
    # EPTS number (line like "164302059225225")
    (re.compile(r"^(\d{15})$", re.I), "epts_number"),
    # Status
    (re.compile(r"[Cc]\u0442\u0430\u0442\u0443\u0441\s+\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0433\u043e\s+\u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430\s+[\u2013\-]\s+(.*)", re.I), "epts_status"),
    # Issue date: "\u0414\u0430\u0442\u0430 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0433\u043e \u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u2013 DD.MM.YYYY"
    (re.compile(r"\u0414\u0430\u0442\u0430\s+\u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f\s+\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0433\u043e\s+\u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430\s+[\u2013\-]\s+(\d{2}\.\d{2}\.\d{4})", re.I), "issue_date"),
    # Printed date: "\u0414\u0430\u0442\u0430 \u0438 \u0432\u0440\u0435\u043c\u044f \u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f* DD.MM.YYYY HH:MM" (may be no space before time)
    (re.compile(r"\u0414\u0430\u0442\u0430\s+\u0438\s+\u0432\u0440\u0435\u043c\u044f\s+\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f\*?\s*(\d{2}\.\d{2}\.\d{4}\s*\d{2}:\d{2})", re.I), "printed_date"),
    # VIN: "\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 VALUE"
    (re.compile(r"\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439\s+\u043d\u043e\u043c\u0435\u0440\s+(\S+)", re.I), "vin"),
    # Brand
    (re.compile(r"^\u041c\u0430\u0440\u043a\u0430\s+(\S.*)", re.I), "brand"),
    # Model
    (re.compile(r"\u041a\u043e\u043c\u043c\u0435\u0440\u0447\u0435\u0441\u043a\u043e\u0435\s+\u043d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435\s+(\S.*)", re.I), "model"),
    # Category (Konventsiya): "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e \u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430 ... \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f VALUE"
    (re.compile(r"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\s+\u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e\s+\u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430\s+.*\u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\s+(\S+)", re.I), "category"),
    # Vehicle type (TR TS): "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0432 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u0438 \u0441 \u0422\u0420 \u0422\u0421 018/2011 VALUE"
    (re.compile(r"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f\s+\u0432\s+\u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u0438\s+\u0441\s+\u0422\u0420\s+\u0422\u0421.*?(\S+)\s*$", re.I), "vehicle_type"),
    # Year
    (re.compile(r"\u0413\u043e\u0434\s+\u0438\u0437\u0433\u043e\u0442\u043e\u0432\u043b\u0435\u043d\u0438\u044f\s+(\d{4})", re.I), "year"),
    # Color
    (re.compile(r"\u0426\u0432\u0435\u0442\s+\u043a\u0443\u0437\u043e\u0432\u0430\s+\(\u043a\u0430\u0431\u0438\u043d\u044b[^)]*\)\s+(\S.*)", re.I), "color"),
    # Color shade: "\u041e\u0442\u0442\u0435\u043d\u043e\u043a \u0446\u0432\u0435\u0442\u0430 ... VALUE" - value is ALL-CAPS word at end
    (re.compile(r"\u041e\u0442\u0442\u0435\u043d\u043e\u043a\s+\u0446\u0432\u0435\u0442\u0430\s+.*?\s+([\u0410-\u042f\u0401A-Z][\u0410-\u042f\u0401A-Z]+)\s*$", re.I), "color_shade"),
    # Body number
    (re.compile(r"\u041d\u043e\u043c\u0435\u0440\s+\u043a\u0443\u0437\u043e\u0432\u0430\s+\([^)]*\)\s+(\S.*)", re.I), "body_number"),
    # Chassis number
    (re.compile(r"\u041d\u043e\u043c\u0435\u0440\s+\u0448\u0430\u0441\u0441\u0438\s+\([^)]*\)\s+(\S.*)", re.I), "chassis_number"),
    # Engine number
    (re.compile(r"\u041d\u043e\u043c\u0435\u0440\s+\u0434\u0432\u0438\u0433\u0430\u0442\u0435\u043b\u044f\s+\([^)]*\)\s+(\S.*)", re.I), "engine_number"),
    # Engine type (ICE): "\u0414\u0432\u0438\u0433\u0430\u0442\u0435\u043b\u044c \u0432\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0435\u0433\u043e \u0441\u0433\u043e\u0440\u0430\u043d\u0438\u044f (\u043c\u0430\u0440\u043a\u0430, \u0442\u0438\u043f) VALUE"
    (re.compile(r"\u0414\u0432\u0438\u0433\u0430\u0442\u0435\u043b\u044c\s+\u0432\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0435\u0433\u043e\s+\u0441\u0433\u043e\u0440\u0430\u043d\u0438\u044f\s+\([^)]*\)\s+(\S.*)", re.I), "engine_type"),
    # Engine volume: "-\u0440\u0430\u0431\u043e\u0447\u0438\u0439 \u043e\u0431\u044a\u0435\u043c \u0446\u0438\u043b\u0438\u043d\u0434\u0440\u043e\u0432 (\u0441\u043c3) VALUE"
    (re.compile(r"\u0440\u0430\u0431\u043e\u0447\u0438\u0439\s+\u043e\u0431\u044a[\u0435\u0451]\u043c\s+\u0446\u0438\u043b\u0438\u043d\u0434\u0440\u043e\u0432\s+\([^)]*\)\s+(\d[\d\s]*)", re.I), "engine_volume"),
    # Engine power kW: "-\u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u043c\u043e\u0449\u043d\u043e\u0441\u0442\u044c (\u043a\u0412\u0442) (\u043c\u0438\u043d-1 VALUE"
    (re.compile(r"\u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f\s+\u043c\u043e\u0449\u043d\u043e\u0441\u0442\u044c\s+\(\u043a[\u0412\u0432][\u0422\u0442]\).*?([\d][\d,\.]+(?:\s*\(\d+\))?)", re.I), "engine_power_kw"),
    # Electric motor type: "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043c\u0430\u0448\u0438\u043d\u0430 (\u043c\u0430\u0440\u043a\u0430, \u0442\u0438\u043f) VALUE"
    (re.compile(r"\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043c\u0430\u0448\u0438\u043d\u0430\s+\([^)]*\)\s+(\S.*)", re.I), "engine_electric_type"),
    # Electric voltage: "-\u0440\u0430\u0431\u043e\u0447\u0435\u0435 \u043d\u0430\u043f\u0440\u044f\u0436\u0435\u043d\u0438\u0435 (\u0412) VALUE"
    (re.compile(r"\u0440\u0430\u0431\u043e\u0447\u0435\u0435\s+\u043d\u0430\u043f\u0440\u044f\u0436\u0435\u043d\u0438\u0435\s+\([^)]*\)\s+(\d[\d\.]*)", re.I), "engine_electric_voltage"),
    # 30-min power: "-\u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f 30-\u043c\u0438\u043d\u0443\u0442\u043d\u0430\u044f \u043c\u043e\u0449\u043d\u043e\u0441\u0442\u044c (\u043a\u0412\u0442) VALUE"
    (re.compile(r"\u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f\s+30\-\u043c\u0438\u043d\u0443\u0442\u043d\u0430\u044f\s+\u043c\u043e\u0449\u043d\u043e\u0441\u0442\u044c\s+\([^)]*\)\s+(\d[\d\.]*)", re.I), "engine_power_30min_kw"),
    # Eco class
    (re.compile(r"\u042d\u043a\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0438\u0439\s+\u043a\u043b\u0430\u0441\u0441\s+(\S.*)", re.I), "eco_class"),
    # Max mass: "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u0430\u044f \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u043c\u0430\u0441\u0441\u0430 VALUE"
    (re.compile(r"\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\s+\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u0430\u044f\s+\u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f\s+\u043c\u0430\u0441\u0441\u0430\s+(\d[\d\s]*)", re.I), "max_mass"),
    # Curb mass: "\u041c\u0430\u0441\u0441\u0430 \u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e \u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430 VALUE"
    (re.compile(r"\u041c\u0430\u0441\u0441\u0430\s+\u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e\s+\u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430\s+(\d[\d\s]*)", re.I), "curb_mass"),
    # Drive wheels: "\u041a\u043e\u043b\u0435\u0441\u043d\u0430\u044f \u0444\u043e\u0440\u043c\u0443\u043b\u0430/\u0432\u0435\u0434\u0443\u0449\u0438\u0435 \u043a\u043e\u043b\u0435\u0441\u0430 VALUE"
    (re.compile(r"\u041a\u043e\u043b\u0435\u0441\u043d\u0430\u044f\s+\u0444\u043e\u0440\u043c\u0443\u043b\u0430/?\u0432\u0435\u0434\u0443\u0449\u0438\u0435\s+\u043a\u043e\u043b\u0435\u0441\u0430\s+(\S.*)", re.I), "drive_wheels"),
    # Seats: "\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u043c\u0435\u0441\u0442 \u0434\u043b\u044f \u0441\u0438\u0434\u0435\u043d\u0438\u044f VALUE"
    (re.compile(r"\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e\s+\u043c\u0435\u0441\u0442\s+\u0434\u043b\u044f\s+\u0441\u0438\u0434\u0435\u043d\u0438\u044f\s+(\S.*)", re.I), "seats_count"),
    # Transmission: "\u0422\u0440\u0430\u043d\u0441\u043c\u0438\u0441\u0441\u0438\u044f (\u0442\u0438\u043f) VALUE"
    (re.compile(r"\u0422\u0440\u0430\u043d\u0441\u043c\u0438\u0441\u0441\u0438\u044f\s+\([^)]*\)\s+(\S.*)", re.I), "transmission"),
    # Fuel type
    (re.compile(r"\u0412\u0438\u0434\s+\u0442\u043e\u043f\u043b\u0438\u0432\u0430\s+(\S.*)", re.I), "fuel_type"),
    # OTTS: "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442.*\u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0438\u0435.*\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438 VALUE (contains \"\u0442\u0435\"/RU)"
    (re.compile(r"\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442.*?\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438\s+(\S.*)", re.I), "otts_number"),
    # Manufacturer
    (re.compile(r"^\u0418\u0437\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u0435\u043b\u044c\s+(\S.*)", re.I), "manufacturer_name"),
    # Manufacturer address
    (re.compile(r"\u0410\u0434\u0440\u0435\u0441\s+\u0438\u0437\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u0435\u043b\u044f\s+(\S.*)", re.I), "manufacturer_address"),
    # Org registered
    (re.compile(r"\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435\s+\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438.*?\u043e\u0440\u0433\u0430\u043d\u0430\)\s*,?\s*(\S.*)", re.I), "org_registered"),
    # Registered country / territory
    (re.compile(r"\u0422\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u044f.*?\u0441\u0442\u0430\u0442\u0443\u0441\s+(\S.*)", re.I), "registered_country"),
    # Customs declaration: "\u0421\u0435\u0440\u0438\u044f, \u043d\u043e\u043c\u0435\u0440 \u0442\u0430\u043c\u043e\u0436\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u0440\u0438\u0445\u043e\u0434\u043d\u043e\u0433\u043e VALUE"
    (re.compile(r"\u0421\u0435\u0440\u0438\u044f.*?\u043f\u0440\u0438\u0445\u043e\u0434\u043d\u043e\u0433\u043e\s+(\d.*)", re.I), "customs_declaration"),
    # Customs restrictions
    (re.compile(r"\u0422\u0430\u043c\u043e\u0436\u0435\u043d\u043d\u044b\u0435\s+\u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f\s+(\S.*)", re.I), "customs_restrictions"),
    # Registered country info / Inaya
    (re.compile(r"\u0418\u043d\u0430\u044f\s+\u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f\s+\u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438.*?\s+(\".*)", re.I), "registered_country_info"),
    # Owner name
    (re.compile(r"^\u0421\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u043d\u0438\u043a\s+(\S.*)", re.I), "owner_name"),
    # Any restrictions: "\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f (\u043e\u0431\u0440\u0435\u043c\u0435\u043d\u0435\u043d\u0438\u044f) \u0437\u0430 \u0438\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\u043c VALUE"
    (re.compile(r"\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f\s+\([^)]*\)\s+\u0437\u0430\s+\u0438\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\u043c\s+(\S.*)", re.I), "any_restrictions"),
    # Modification
    (re.compile(r"^\u041c\u043e\u0434\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f\s+(\S.*)", re.I), "modification"),
]


class EPTSParser:
    _VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
    _EPTS_NUM_RE = re.compile(r"^(\d{15})$")
    _DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
    _INN_RE = re.compile(r"\b\u0418\u041d\u041d\b[^\d]*(\d{10}|\d{12})")
    _OGRN_RE = re.compile(r"\b\u041e\u0413\u0420\u041d\b[^\d]*(\d{13}|\d{15})")
    _POWER_RE = re.compile(
        r"([\d.,]+)\s*(?:\u043a\u0412\u0442|kW|\u043a\u0432\u0442)"
        r"(?:\s*[\(/]?\s*([\d.,]+)\s*(?:\u043b\.\u0441\.|hp|\u043b\.\u0441|\u043b\u0441)\s*[\)]?)?"
    )
    _YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")

    def __init__(self, pdf_path: str | Path, ocr: bool = False) -> None:
        self.pdf_path = Path(pdf_path)
        self.ocr = ocr
        self._data: Optional[VehiclePassportData] = None

    def parse(self) -> VehiclePassportData:
        result = VehiclePassportData()
        if self.ocr:
            text = self._ocr_text()
            self._scan_lines(text, result)
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
            self._scan_lines(full_text, result)
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

    # ------------------------------------------------------------------
    # Core text scanner: apply _LINE_RULES to every line
    # ------------------------------------------------------------------
    def _scan_lines(self, text: str, result: VehiclePassportData) -> None:
        if not text:
            return
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            for pat, field_name in _LINE_RULES:
                m = pat.search(line)
                if m:
                    value = m.group(1).strip()
                    if value and getattr(result, field_name, None) is None:
                        setattr(result, field_name, value)
                    break
            # Fallback: INN / OGRN anywhere in line
            if result.owner_inn is None:
                mi = self._INN_RE.search(line)
                if mi:
                    result.owner_inn = mi.group(1)
            if result.owner_ogrn is None:
                mo = self._OGRN_RE.search(line)
                if mo:
                    result.owner_ogrn = mo.group(1)

    # ------------------------------------------------------------------
    # Table row parser (fallback for table-based PDFs)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Post-processing: type normalisation
    # ------------------------------------------------------------------
    def _postprocess(self, result: VehiclePassportData) -> None:
        if result.vin:
            result.vin = result.vin.upper().strip()

        if result.year:
            m = self._YEAR_RE.search(result.year)
            result.year = m.group(1) if m else None

        # Eco class: word -> digit
        if result.eco_class:
            result.eco_class = _ECO_WORDS.get(
                result.eco_class.lower().strip(), result.eco_class
            )
            m2 = re.match(r"(\d+)", result.eco_class)
            if m2:
                result.eco_class = m2.group(1)

        # Seats: first integer only
        if result.seats_count:
            m3 = re.search(r"(\d+)", result.seats_count)
            result.seats_count = m3.group(1) if m3 else None

        # Mass fields: strip non-numeric suffixes
        for mass_f in ("max_mass", "curb_mass"):
            val = getattr(result, mass_f)
            if val:
                m4 = re.search(r"(\d[\d\s]*)", val.replace("\xa0", ""))
                setattr(result, mass_f, m4.group(1).strip() if m4 else None)

        # Engine volume: first integer
        if result.engine_volume:
            m5 = re.search(r"(\d+)", result.engine_volume)
            result.engine_volume = m5.group(1) if m5 else None

        # Engine power: split "64,7 (5800)" -> kw="64.7", keep rpm separately
        if result.engine_power_kw:
            raw = result.engine_power_kw
            m6 = self._POWER_RE.search(raw)
            if m6:
                result.engine_power_kw = m6.group(1).replace(",", ".")
                if m6.group(2):
                    result.engine_power_hp = m6.group(2).replace(",", ".")
            else:
                m7 = re.match(r"([\d]+[.,]\d+|\d+)", raw)
                if m7:
                    result.engine_power_kw = m7.group(1).replace(",", ".")

        # 30-min power
        if result.engine_power_30min_kw:
            m8 = re.match(r"([\d]+[.,]?\d*)", result.engine_power_30min_kw)
            if m8:
                result.engine_power_30min_kw = m8.group(1).replace(",", ".")

        # Category: keep only letter(s) after last space (e.g. "\u0432 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0412" -> "\u0412")
        if result.category:
            result.category = result.category.strip().split()[-1].upper()

        # Vehicle type: strip leading junk, keep e.g. "M1"
        if result.vehicle_type:
            m9 = re.search(r"([A-Z]\d*(?:[a-z]\d*)?)", result.vehicle_type)
            if m9:
                result.vehicle_type = m9.group(1)

        # Printed date: normalise "13.01.202617:17" -> "13.01.2026 17:17"
        if result.printed_date:
            pd = result.printed_date.replace("*", "").strip()
            pd = re.sub(r"(\d{4})(\d{2}:\d{2})", r"\1 \2", pd)
            result.printed_date = pd

        # Drive wheels: strip stray prefix before formula like "4\u04452/..."
        if result.drive_wheels:
            m10 = re.search(r"(\d+[\u0445x]\d+.*)", result.drive_wheels, re.I)
            if m10:
                result.drive_wheels = m10.group(1)

        # Transmission: join continuation line if ends with comma
        # (no action here - continuation lines not captured by single-line rules)

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
