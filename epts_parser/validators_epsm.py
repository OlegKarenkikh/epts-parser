"""
validators_epsm.py — field validation for VehiclePassportEPSM.
Patterns derived from EEC Decision No. 81 (R.019) and NAMI Appendix 3.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from .models_epsm import VehiclePassportEPSM

_RE_EPSM_NUMBER   = re.compile(r"^[1-3]\d{3}0[1-4]\d{9}$")
_RE_CATEGORY_SM   = re.compile(r"^A(IV|I{1,3})?$|^[B-FRr]$")
_RE_CUSTOMS       = re.compile(r"^\d{8}/\d{6}/\d{7,10}$")
_RE_YEAR          = re.compile(r"^(19|20)\d{2}$")
_RE_MONTH         = re.compile(r"^(0[1-9]|1[0-2])$")
_RE_DATE_RU       = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

ValidationResult = List[Tuple[str, str]]  # [(field_name, error_message), ...]

VALID_STATUSES = {
    "незавершенный",
    "действующий",
    "аннулированный",
    "погашенный",
    "утилизированная самоходная машина",
    "утилизированная самоходная машина (другой вид техники)",
}

VALID_PROPULSION = {
    "колесный",
    "гусеничный",
    "полугусеничный",
    "вальцовый",
    "лыжно-гусеничный",
    "санный",
}


def validate_epsm(record: VehiclePassportEPSM) -> ValidationResult:
    """Validate a VehiclePassportEPSM record. Returns list of (field, error) tuples."""
    errors: ValidationResult = []

    def _check(field: str, pattern: re.Pattern, label: str) -> None:
        val = getattr(record, field, None)
        if val is not None and not pattern.match(val):
            errors.append((field, f"{label}: '{val}' does not match {pattern.pattern}"))

    def _check_set(field: str, valid: set, label: str) -> None:
        val = getattr(record, field, None)
        if val is not None and val.lower().strip() not in valid:
            errors.append((field, f"{label}: '{val}' not in allowed set"))

    _check("epsm_number",         _RE_EPSM_NUMBER,  "EPSM number")
    _check("category_epsm",       _RE_CATEGORY_SM,  "EPSM category (A(I-IV)/B-F/R)")
    _check("customs_declaration", _RE_CUSTOMS,       "Customs declaration")
    _check("year",                _RE_YEAR,          "Production year")
    _check("month",               _RE_MONTH,         "Production month")
    _check("issue_date",          _RE_DATE_RU,       "Issue date (DD.MM.YYYY)")

    _check_set("epsm_status",     VALID_STATUSES,    "EPSM status")
    _check_set("propulsion_type", VALID_PROPULSION,  "Propulsion type")

    for mass_field in ("curb_mass", "max_mass", "payload", "max_tow_mass"):
        val = getattr(record, mass_field, None)
        if val is not None and not re.match(r"^\d{3,6}$", val):
            errors.append(
                (mass_field, f"Mass field '{mass_field}': expected integer kg, got '{val}'")
            )

    return errors
