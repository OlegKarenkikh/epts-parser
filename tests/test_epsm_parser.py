"""
Tests for EPSM parser, model, validator and auto-detector.
Standards: EEC Decision No. 81 (2016) R.019, NAMI Appendix 3.
"""
import json
import pathlib

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

    def test_engine_details_defaults(self):
        eng = EngineDetails()
        assert eng.engine_power_kw is None
        assert eng.fuel_type is None

    def test_passport_type_default(self):
        rec = VehiclePassportEPSM()
        assert rec.passport_type == "ЭПСМ"


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

    def test_epsm_via_samohodny_fallback(self):
        text = "Самоходная машина без явных маркеров"
        assert detect_passport_type(text) == "EPSM"


class TestEPSMParserText:
    def test_parse_epsm_number_from_text(self):
        text = "Номер ЭПСМ: 264300200012345\nСтатус: действующий"
        rec = EPSMParser().parse_text(text)
        assert rec.epsm_number == "264300200012345"

    def test_parse_epsm_number_fallback_bare(self):
        text = "Статус электронного паспорта – действующий\n264300200012345"
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

    def test_parse_brand_and_year(self):
        text = "Марка: CLAAS\nГод изготовления: 2022\n"
        rec = EPSMParser().parse_text(text)
        assert rec.brand == "CLAAS"
        assert rec.year == "2022"

    def test_parse_month_year(self):
        text = "Месяц и год изготовления: 04/2021"
        rec = EPSMParser().parse_text(text)
        assert rec.month == "04"
        assert rec.year == "2021"

    def test_parse_axle_loads(self):
        text = "Ось 1: 5800 кг\nОсь 2: 6200 кг"
        rec = EPSMParser().parse_text(text)
        assert len(rec.axle_loads) == 2
        assert rec.axle_loads[0].max_load_kg == "5800"

    def test_parse_engine_power(self):
        text = "Максимальная мощность: 206,0 кВт\n"
        rec = EPSMParser().parse_text(text)
        assert rec.engines[0].engine_power_kw is not None

    def test_empty_text_returns_empty_record(self):
        rec = EPSMParser().parse_text("")
        assert rec.epsm_number is None
        assert rec.brand is None
