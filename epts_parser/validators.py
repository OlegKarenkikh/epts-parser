"""Field-level validation sourced from EEC R.019 (Table 3).

Each validator checks one field of VehiclePassportData against the
pattern / constraint defined in the official spec.  validate_record()
returns a list of ValidationError - an empty list means the record
passed all checks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from epts_parser.models import VehiclePassportData


@dataclass
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


# ---------------------------------------------------------------------------
# Patterns taken verbatim from R.019 Table 3
# ---------------------------------------------------------------------------

# 6. Номер ЭПТС -> trsdo:VehicleEPassportId
#    Pattern: [1-3][0-9]{3}0[1-4][0-9]{9}
_RE_EPTS_NUMBER = re.compile(r"^[1-3][0-9]{3}0[1-4][0-9]{9}$")

# 11.1.1 / 11.1.4  Идентификационный номер (VIN, кузов)
#    Реальный VIN (ISO 3779): 17 символов A-H,J-N,P-Z,0-9 (без I,O,Q)
_RE_VIN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

# 11.14. Номер таможенного документа -> trsdo:CustomsDocumentId
#    R.019 spec: [0-9]{8}/[0-9]{6}/[0-9]{7}
#    Real PDFs emit 9-10 digit last segment (e.g. 100000000 = 9 digits)
#    -> relaxed to [0-9]{7,10}
_RE_CUSTOMS = re.compile(r"^[0-9]{8}/[0-9]{6}/[0-9]{7,10}$")

# 11.2. Категория ТС (Конвенция) -> trsdo:VehicleCategoryCode
#    Pattern: [A-FR](IV|I{1,3})?
_RE_CATEGORY = re.compile(r"^[A-FR](IV|I{1,3})?$")

# 11.3. Категория ТР ТС 018/2011 -> trsdo:MachineCategoryCode
#    Pattern: [A-Z]([ab]?[1-9])?G?(\.[1-3])?
_RE_VEHICLE_TYPE = re.compile(r"^[A-Z]([ab]?[1-9])?G?(\.[1-3])?$")

# 11.9. Год изготовления -> bdt:YearType
#    4-значное число, диапазон 1900-2099
_RE_YEAR = re.compile(r"^(19|20)\d{2}$")

# Экологический класс — 1..6
_RE_ECO_CLASS = re.compile(r"^[1-6]$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_record(record: VehiclePassportData) -> list[ValidationError]:
    """Validate *record* against R.019 patterns. Return list of errors."""
    errors: list[ValidationError] = []

    def _check(field_name: str, pattern: re.Pattern, label: str) -> None:
        raw = getattr(record, field_name, None)
        if raw is None:
            return
        value = str(raw).strip()
        if not pattern.match(value):
            errors.append(ValidationError(
                field=field_name,
                message=(
                    f"'{value}' does not match R.019 pattern "
                    f"for {label} ({pattern.pattern})"
                ),
            ))

    _check("epts_number",         _RE_EPTS_NUMBER,  "VehicleEPassportId")
    _check("vin",                 _RE_VIN,          "VehicleIdentityNumberId (VIN)")
    _check("body_number",         _RE_VIN,          "VehicleBodyIdDetails")
    _check("customs_declaration", _RE_CUSTOMS,      "CustomsDocumentId")
    _check("category",            _RE_CATEGORY,     "VehicleCategoryCode")
    _check("vehicle_type",        _RE_VEHICLE_TYPE, "MachineCategoryCode")

    year_val = getattr(record, "year", None)
    if year_val is not None:
        year_str = str(year_val).strip()
        if not _RE_YEAR.match(year_str):
            errors.append(ValidationError(
                field="year",
                message=f"'{year_str}' is not a valid 4-digit year (1900-2099)",
            ))

    eco_raw = getattr(record, "eco_class", None)
    if eco_raw is not None:
        eco_int = record.get_int("eco_class")
        eco_str = str(eco_int) if eco_int is not None else ""
        if eco_str and not _RE_ECO_CLASS.match(eco_str):
            errors.append(ValidationError(
                field="eco_class",
                message=(
                    f"'{eco_raw}' resolves to '{eco_str}' "
                    f"which is outside range 1-6"
                ),
            ))

    return errors
