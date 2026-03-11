from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


_INT_FIELDS = {
    "year", "seats_count", "eco_class",
    "max_mass", "curb_mass",
    "engine_volume",
}
_FLOAT_FIELDS = {"engine_power_kw", "engine_power_hp", "engine_power_30min_kw"}

_ECO_WORDS: dict[str, str] = {
    "\u043f\u0435\u0440\u0432\u044b\u0439": "1",
    "\u0432\u0442\u043e\u0440\u043e\u0439": "2",
    "\u0442\u0440\u0435\u0442\u0438\u0439": "3",
    "\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u044b\u0439": "4",
    "\u0447\u0435\u0442\u0432\u0451\u0440\u0442\u044b\u0439": "4",
    "\u043f\u044f\u0442\u044b\u0439": "5",
    "\u0448\u0435\u0441\u0442\u043e\u0439": "6",
}


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    m = re.search(r"(\d+)", value.replace("\xa0", "").replace(" ", ""))
    return int(m.group(1)) if m else None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.replace(",", ".").replace("\xa0", "").replace(" ", "")
    m = re.search(r"([\d]+\.?\d*)", cleaned)
    return float(m.group(1)) if m else None


@dataclass
class VehiclePassportData:
    # --- Identity ---
    epts_number: Optional[str] = None
    epts_status: Optional[str] = None
    vin: Optional[str] = None
    pts_number: Optional[str] = None

    # --- Vehicle description ---
    brand: Optional[str] = None
    model: Optional[str] = None
    vehicle_type: Optional[str] = None      # TR TS 018/2011 category (M1, N1 ...)
    category: Optional[str] = None          # Convention category (B, C, D ...)
    modification: Optional[str] = None
    year: Optional[str] = None
    color: Optional[str] = None
    color_shade: Optional[str] = None

    # --- Identifiers ---
    body_number: Optional[str] = None
    chassis_number: Optional[str] = None
    country_of_manufacture: Optional[str] = None

    # --- ICE engine ---
    engine_number: Optional[str] = None
    engine_type: Optional[str] = None       # brand + type, e.g. "Honda, LDA, ..."
    engine_power_kw: Optional[str] = None
    engine_power_hp: Optional[str] = None
    engine_volume: Optional[str] = None     # cm3

    # --- Electric / hybrid ---
    engine_electric_type: Optional[str] = None
    engine_electric_voltage: Optional[str] = None
    engine_power_30min_kw: Optional[str] = None
    hybrid_description: Optional[str] = None

    # --- Fuel & ecology ---
    fuel_type: Optional[str] = None
    eco_class: Optional[str] = None

    # --- Mass & dimensions ---
    max_mass: Optional[str] = None          # kg, technically permitted max
    curb_mass: Optional[str] = None         # kg, mass in service order
    seats_count: Optional[str] = None
    drive_wheels: Optional[str] = None
    transmission: Optional[str] = None

    # --- Manufacturer ---
    manufacturer_name: Optional[str] = None
    manufacturer_inn: Optional[str] = None
    manufacturer_country: Optional[str] = None
    manufacturer_address: Optional[str] = None
    org_registered: Optional[str] = None   # org that issued EPTS

    # --- Approval / compliance ---
    otts_number: Optional[str] = None       # type approval number
    otts_date: Optional[str] = None
    vehicle_type_approval: Optional[str] = None  # safety compliance doc
    emergency_services_number: Optional[str] = None

    # --- Customs ---
    customs_declaration: Optional[str] = None
    customs_restrictions: Optional[str] = None
    recycling_pay_country: Optional[str] = None

    # --- Owner ---
    owner_name: Optional[str] = None
    owner_inn: Optional[str] = None
    owner_ogrn: Optional[str] = None
    owner_address: Optional[str] = None
    any_restrictions: Optional[str] = None
    registered_country: Optional[str] = None
    registered_country_info: Optional[str] = None

    # --- Document ---
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    printed_date: Optional[str] = None

    raw_tables: list = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Typed accessors — parse stored string to target Python type
    # ------------------------------------------------------------------

    def get_int(self, field_name: str) -> int | None:
        """Return integer value of an int-typed field, or None."""
        val = getattr(self, field_name, None)
        if isinstance(val, int):
            return val
        raw = _ECO_WORDS.get(str(val).lower().strip(), val) if field_name == "eco_class" else val
        return _to_int(raw)

    def get_float(self, field_name: str) -> float | None:
        """Return float value of a float-typed field, or None."""
        return _to_float(getattr(self, field_name, None))

    def to_typed_dict(self) -> dict:
        """Return dict with numeric fields converted to int/float."""
        result: dict = {}
        for f_name, val in self.__dict__.items():
            if f_name == "raw_tables" or val is None:
                continue
            if f_name in _INT_FIELDS:
                result[f_name] = _to_int(val)
            elif f_name in _FLOAT_FIELDS:
                result[f_name] = _to_float(val)
            else:
                result[f_name] = val
        return result
