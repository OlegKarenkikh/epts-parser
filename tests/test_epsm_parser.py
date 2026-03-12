"""
Tests for EPSM parser, model, validator and auto-detector.
Standards: EEC Decision No. 81 (2016) R.019, NAMI Appendix 3.
"""
import json
import pathlib

import pytest

from epts_parser.models_epsm import (
    VehiclePassportEPSM,
    AxleLoadDetails,
    EngineDetails,
)
from epts_parser.validators_epsm import validate_epsm
from epts_parser.parser_epsm import detect_passport_type, EPSMParser

FIXTURE = pathlib.Path("tests/fixtures/john_deere_8r.json")

_LIST_FIELDS = {
    "axle_loads", "registrations", "modifications_history", "engines",
}
_COMPLEX_FIELDS = {"transmission"}


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _fixture_to_record(d: dict) -> VehiclePassportEPSM:
    simple = {
        k: v for k, v in d.items()
        if not k.startswith("_") and k not in _LIST_FIELDS | _COMPLEX_FIELDS
    }
    return VehiclePassportEPSM(**simple)


class TestEPSMModel:
    def test_fixture_loads(self):
        d = _load_fixture()
        assert d["passport_type"] == "\u042d\u041f\u0421\u041c"
        assert d["epsm_number"] == "264300200012345"

    def test_record_creation(self):
        rec = _fixture_to_record(_load_fixture())
        assert rec.brand == "John Deere"
        assert rec.category_epsm == "F"
        assert rec.propulsion_type == "\u043a\u043e\u043b\u0435\u0441\u043d\u044b\u0439"

    def test_default_lists_empty(self):
        rec = VehiclePassportEPSM()
        assert rec.axle_loads == []
        assert rec.registrations == []
        assert rec.modifications_history == []
        assert rec.engines == []

    def test_axle_load_record(self):
        al = AxleLoadDetails(axle_index=1, max_load_kg="5800")
        assert al.axle_index == 1
        assert al.max_load_kg == "5800"

    def test_engine_details_defaults(self):
        eng = EngineDetails()
        assert eng.engine_power_kw is None
        assert eng.fuel_type is None

    def test_passport_type_default(self):
        rec = VehiclePassportEPSM()
        assert rec.passport_type == "\u042d\u041f\u0421\u041c"


class TestEPSMValidator:
    def test_valid_record(self):
        rec = _fixture_to_record(_load_fixture())
        errors = validate_epsm(rec)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_invalid_epsm_number(self):
        rec = VehiclePassportEPSM(epsm_number="12345")
        errors = validate_epsm(rec)
        assert any("EPSM number" in e[1] for e in errors)

    def test_valid_epsm_number_15_digits(self):
        rec = VehiclePassportEPSM(epsm_number="264300200012345")
        errors = validate_epsm(rec)
        assert not any("EPSM number" in e[1] for e in errors)

    def test_invalid_category(self):
        rec = VehiclePassportEPSM(category_epsm="Z")
        errors = validate_epsm(rec)
        assert any("category" in e[1].lower() for e in errors)

    def test_valid_category_A(self):
        for cat in ("A", "AI", "AII", "AIII", "AIV", "B", "C", "F", "R"):
            rec = VehiclePassportEPSM(category_epsm=cat)
            errors = validate_epsm(rec)
            assert not any("category" in e[1].lower() for e in errors), f"Failed for {cat}"

    def test_invalid_year(self):
        rec = VehiclePassportEPSM(year="1899")
        errors = validate_epsm(rec)
        assert any("year" in e[1].lower() for e in errors)

    def test_valid_year(self):
        rec = VehiclePassportEPSM(year="2023")
        errors = validate_epsm(rec)
        assert not any("year" in e[1].lower() for e in errors)

    def test_valid_customs_format(self):
        rec = VehiclePassportEPSM(customs_declaration="10702000/150823/100000001")
        errors = validate_epsm(rec)
        assert not any("customs" in e[1].lower() for e in errors)

    def test_invalid_mass(self):
        rec = VehiclePassportEPSM(curb_mass="abc")
        errors = validate_epsm(rec)
        assert any("curb_mass" in e[0] for e in errors)

    def test_valid_mass(self):
        rec = VehiclePassportEPSM(curb_mass="9500")
        errors = validate_epsm(rec)
        assert not any("curb_mass" in e[0] for e in errors)

    def test_none_fields_no_errors(self):
        """Fields with None value should not produce validation errors."""
        rec = VehiclePassportEPSM()
        errors = validate_epsm(rec)
        assert errors == []

    def test_invalid_month(self):
        rec = VehiclePassportEPSM(month="13")
        errors = validate_epsm(rec)
        assert any("month" in e[1].lower() for e in errors)

    def test_valid_month(self):
        rec = VehiclePassportEPSM(month="06")
        errors = validate_epsm(rec)
        assert not any("month" in e[1].lower() for e in errors)


class TestDetector:
    def test_detect_epsm(self):
        text = (
            "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u044b\u0439 \u043f\u0430\u0441\u043f\u043e\u0440\u0442 \u0441\u0430\u043c\u043e\u0445\u043e\u0434\u043d\u043e\u0439 \u043c\u0430\u0448\u0438\u043d\u044b \u0438 \u0434\u0440\u0443\u0433\u0438\u0445 \u0432\u0438\u0434\u043e\u0432 \u0442\u0435\u0445\u043d\u0438\u043a\u0438\n"
            "\u0413\u043e\u0441\u0442\u0435\u0445\u043d\u0430\u0434\u0437\u043e\u0440\n\u0422\u0438\u043f \u0434\u0432\u0438\u0436\u0438\u0442\u0435\u043b\u044f: \u043a\u043e\u043b\u0435\u0441\u043d\u044b\u0439\n\u0422\u0440\u0430\u043a\u0442\u043e\u0440 John Deere"
        )
        assert detect_passport_type(text) == "EPSM"

    def test_detect_epts(self):
        text = (
            "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u044b\u0439 \u043f\u0430\u0441\u043f\u043e\u0440\u0442 \u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e \u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430\n"
            "\u0413\u0418\u0411\u0414\u0414 \u041c\u0420\u042d\u041e\n\u041e\u0434\u043e\u0431\u0440\u0435\u043d\u0438\u0435 \u0442\u0438\u043f\u0430 \u0442\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u043e\u0433\u043e \u0441\u0440\u0435\u0434\u0441\u0442\u0432\u0430 \u041e\u0422\u0422\u0421"
        )
        assert detect_passport_type(text) == "EPTS"

    def test_detect_unknown_returns_str(self):
        result = detect_passport_type("\u041a\u0430\u043a\u043e\u0439-\u0442\u043e \u0441\u043b\u0443\u0447\u0430\u0439\u043d\u044b\u0439 \u0442\u0435\u043a\u0441\u0442")
        assert result in ("EPTS", "EPSM", "UNKNOWN")

    def test_epsm_via_samohodny_fallback(self):
        text = "\u0421\u0430\u043c\u043e\u0445\u043e\u0434\u043d\u0430\u044f \u043c\u0430\u0448\u0438\u043d\u0430 \u0431\u0435\u0437 \u044f\u0432\u043d\u044b\u0445 \u043c\u0430\u0440\u043a\u0435\u0440\u043e\u0432"
        assert detect_passport_type(text) == "EPSM"


class TestEPSMParserText:
    def test_parse_epsm_number_from_text(self):
        text = "\u041d\u043e\u043c\u0435\u0440 \u042d\u041f\u0421\u041c: 264300200012345\n\u0421\u0442\u0430\u0442\u0443\u0441: \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_number == "264300200012345"

    def test_parse_epsm_number_fallback_bare(self):
        """Fallback: bare 15-digit number on a line without label."""
        text = "\u0421\u0442\u0430\u0442\u0443\u0441 \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0433\u043e \u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u2013 \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439\n264300200012345"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_number == "264300200012345"

    def test_parse_status(self):
        text = "\u0421\u0442\u0430\u0442\u0443\u0441 \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u043e\u0433\u043e \u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430: \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439\n264300200012345"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_status == "\u0434\u0435\u0439\u0441\u0442\u0432\u0443\u044e\u0449\u0438\u0439"

    def test_parse_vin(self):
        text = "\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440: 1RW8330XPNC123456\n\u041c\u0430\u0440\u043a\u0430: John Deere"
        rec = EPSMParser().parse_text(text)
        assert rec.vin == "1RW8330XPNC123456"

    def test_parse_brand_and_year(self):
        text = "\u041c\u0430\u0440\u043a\u0430: CLAAS\n\u0413\u043e\u0434 \u0438\u0437\u0433\u043e\u0442\u043e\u0432\u043b\u0435\u043d\u0438\u044f: 2022\n"
        rec = EPSMParser().parse_text(text)
        assert rec.brand == "CLAAS"
        assert rec.year == "2022"

    def test_parse_month_year(self):
        text = "\u041c\u0435\u0441\u044f\u0446 \u0438 \u0433\u043e\u0434 \u0438\u0437\u0433\u043e\u0442\u043e\u0432\u043b\u0435\u043d\u0438\u044f: 04/2021"
        rec = EPSMParser().parse_text(text)
        assert rec.month == "04"
        assert rec.year == "2021"

    def test_parse_axle_loads(self):
        text = "\u041e\u0441\u044c 1: 5800 \u043a\u0433\n\u041e\u0441\u044c 2: 6200 \u043a\u0433"
        rec = EPSMParser().parse_text(text)
        assert len(rec.axle_loads) == 2
        assert rec.axle_loads[0].max_load_kg == "5800"

    def test_parse_engine_power(self):
        text = "\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u043c\u043e\u0449\u043d\u043e\u0441\u0442\u044c: 206,0 \u043a\u0412\u0442\n"
        rec = EPSMParser().parse_text(text)
        assert rec.engines[0].engine_power_kw is not None

    def test_empty_text_returns_empty_record(self):
        rec = EPSMParser().parse_text("")
        assert rec.epsm_number is None
        assert rec.brand is None
