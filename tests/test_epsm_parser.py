"""
Tests for EPSM parser, model, validator and auto-detector.
Standards: EEC Decision No. 81 (2016) R.019, NAMI Appendix 3.
"""
import json
import pathlib

from epts_parser.models_epsm import (
    VehiclePassportEPSM,
    AxleLoadDetails,
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
        assert d["passport_type"] == "ЭПСМ"
        assert d["epsm_number"] == "264300200012345"

    def test_record_creation(self):
        rec = _fixture_to_record(_load_fixture())
        assert rec.brand == "John Deere"
        assert rec.category_epsm == "F"
        assert rec.propulsion_type == "колесный"

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


class TestEPSMValidator:
    def test_valid_record(self):
        rec = _fixture_to_record(_load_fixture())
        errors = validate_epsm(rec)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_invalid_epsm_number(self):
        rec = VehiclePassportEPSM(epsm_number="12345")
        errors = validate_epsm(rec)
        assert any("EPSM number" in e[1] for e in errors)

    def test_invalid_category(self):
        rec = VehiclePassportEPSM(category_epsm="Z")
        errors = validate_epsm(rec)
        assert any("category" in e[1].lower() for e in errors)

    def test_invalid_year(self):
        rec = VehiclePassportEPSM(year="1899")
        errors = validate_epsm(rec)
        assert any("year" in e[1].lower() for e in errors)

    def test_valid_customs_format(self):
        rec = VehiclePassportEPSM(customs_declaration="10702000/150823/100000001")
        errors = validate_epsm(rec)
        assert not any("customs" in e[1].lower() for e in errors)

    def test_invalid_mass(self):
        rec = VehiclePassportEPSM(curb_mass="abc")
        errors = validate_epsm(rec)
        assert any("curb_mass" in e[0] for e in errors)


class TestDetector:
    def test_detect_epsm(self):
        text = (
            "Электронный паспорт самоходной машины и других видов техники\n"
            "Гостехнадзор\nТип движителя: колесный\nТрактор John Deere"
        )
        assert detect_passport_type(text) == "EPSM"

    def test_detect_epts(self):
        text = (
            "Электронный паспорт транспортного средства\n"
            "ГИБДД МРЭО\nОдобрение типа транспортного средства ОТТС"
        )
        assert detect_passport_type(text) == "EPTS"

    def test_detect_unknown_returns_str(self):
        result = detect_passport_type("Какой-то случайный текст")
        assert result in ("EPTS", "EPSM", "UNKNOWN")


class TestEPSMParserText:
    def test_parse_epsm_number_from_text(self):
        text = "Номер ЭПСМ: 264300200012345\nСтатус: действующий"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_number == "264300200012345"

    def test_parse_status(self):
        text = "Статус электронного паспорта: действующий\n264300200012345"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_status == "действующий"

    def test_parse_vin(self):
        text = "Идентификационный номер: 1RW8330XPNC123456\nМарка: John Deere"
        rec = EPSMParser().parse_text(text)
        assert rec.vin == "1RW8330XPNC123456"
