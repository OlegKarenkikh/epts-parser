"""Tests for epts_parser.validators against R.019 patterns."""
from __future__ import annotations

from epts_parser.models import VehiclePassportData
from epts_parser.validators import validate_record, ValidationError


def _lada_record() -> VehiclePassportData:
    """Minimal valid record built from the LADA XRAY fixture."""
    return VehiclePassportData(
        epts_number="164301027146619",
        vin="XTAG AB440M1382290".replace(" ", ""),  # 17 chars after strip
        customs_declaration=None,
        category="B",
        vehicle_type="M1",
        year="2021",
        eco_class="пятый",  # Russian word -> resolves to 5
    )


def _honda_record() -> VehiclePassportData:
    """Minimal record built from the Honda INSIGHT HYBRID fixture."""
    return VehiclePassportData(
        epts_number="164302059225225",
        customs_declaration="10702000/140323/100000000",
        category="B",
        vehicle_type="M1",
        year="2019",
        eco_class="четвёртый",  # Russian word -> resolves to 4
    )


class TestValidRecords:
    def test_lada_no_errors(self):
        errors = validate_record(_lada_record())
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_honda_customs_valid(self):
        errors = validate_record(_honda_record())
        customs_errors = [e for e in errors if e.field == "customs_declaration"]
        assert customs_errors == []

    def test_honda_overall_clean(self):
        errors = validate_record(_honda_record())
        assert errors == [], f"Expected no errors, got: {errors}"


class TestInvalidPatterns:
    def test_bad_epts_number(self):
        rec = _lada_record()
        rec.epts_number = "9999999"  # too short, starts with 9
        errors = validate_record(rec)
        assert any(e.field == "epts_number" for e in errors)

    def test_bad_vin(self):
        rec = _lada_record()
        rec.vin = "INVALID_VIN_XXXX"  # invalid chars + wrong length
        errors = validate_record(rec)
        assert any(e.field == "vin" for e in errors)

    def test_bad_customs_declaration(self):
        rec = _honda_record()
        rec.customs_declaration = "1234/56/789"  # wrong segment lengths
        errors = validate_record(rec)
        assert any(e.field == "customs_declaration" for e in errors)

    def test_bad_category(self):
        rec = _lada_record()
        rec.category = "Z"  # not in [A-FR]
        errors = validate_record(rec)
        assert any(e.field == "category" for e in errors)

    def test_bad_vehicle_type(self):
        rec = _lada_record()
        rec.vehicle_type = "12"  # digits only - does not match [A-Z]...
        errors = validate_record(rec)
        assert any(e.field == "vehicle_type" for e in errors)

    def test_bad_year_two_digits(self):
        rec = _lada_record()
        rec.year = "21"  # 2-digit year
        errors = validate_record(rec)
        assert any(e.field == "year" for e in errors)

    def test_bad_year_too_old(self):
        rec = _lada_record()
        rec.year = "1800"  # before 1900
        errors = validate_record(rec)
        assert any(e.field == "year" for e in errors)

    def test_multiple_errors_all_reported(self):
        """Multiple bad fields must all be reported (no short-circuit)."""
        rec = VehiclePassportData(
            epts_number="BAD",
            vin="BAD",
            customs_declaration="wrong",
            category="Z",
            vehicle_type="99",
            year="1800",
        )
        errors = validate_record(rec)
        fields = {e.field for e in errors}
        expected = {"epts_number", "vin", "customs_declaration",
                    "category", "vehicle_type", "year"}
        assert expected.issubset(fields), f"Missing error fields: {expected - fields}"

    def test_validation_error_str(self):
        err = ValidationError(field="vin", message="bad value")
        assert "vin" in str(err)
        assert "bad value" in str(err)
