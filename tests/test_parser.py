"""Tests for EPTSParser using mocked pdfplumber."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from epts_parser.parser import EPTSParser


# ---------------------------------------------------------------------------
# Sample EPTS table data (3-column: index, Russian label, value)
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    ["1", "Номер ЭПТС", "111222333444555"],
    ["2", "Идентификационный номер (VIN)", "XTA21099071234567"],
    ["3", "Номер ПТС", "77 УУ 123456"],
    ["4", "Марка", "LADA (ВАЗ)"],
    ["5", "Коммерческое наименование", "GRANTA"],
    ["6", "Наименование (тип) ТС", "Легковой автомобиль"],
    ["7", "Категория ТС", "B"],
    ["8", "Год изготовления", "2021"],
    ["9", "Цвет", "Белый"],
    ["10", "Номер кузова", "XTA21099071234567"],
    ["11", "Номер шасси", "отсутствует"],
    ["12", "Страна изготовления", "Россия"],
    ["13", "Номер двигателя", "12345A"],
    ["14", "Тип двигателя", "ВАЗ-11183"],
    ["15", "Мощность двигателя", "77.0 кВт (104.7 л.с.)"],
    ["16", "Рабочий объём двигателя", "1596"],
    ["17", "Тип топлива", "Бензин"],
    ["18", "Экологический класс", "5"],
    ["19", "Разрешённая максимальная масса", "1570"],
    ["20", "Масса без нагрузки", "1085"],
    ["21", "Количество мест", "5"],
    ["22", "Наименование изготовителя", "АО «АВТОВАЗ»"],
    ["23", "ИНН изготовителя", "6320000800"],
    ["24", "Страна нахождения изготовителя", "Россия"],
    ["25", "Номер одобрения типа", "РОСС RU.АЯ46.А12345"],
    ["26", "Дата одобрения типа", "01.01.2018"],
    ["27", "Таможенная декларация", "не требуется"],
    ["28", "Наименование владельца", "ООО «Ромашка»"],
    ["29", "ИНН владельца", "7700000001"],
    ["30", "ОГРН владельца", "1027700132195"],
    ["31", "Адрес владельца", "г. Москва, ул. Ленина, д. 1"],
    ["32", "Дата выдачи", "15.03.2021"],
    ["33", "Кем выдан", "МРЭО ГИБДД №1"],
]


def _make_mock_pdf(rows: list[list[str]] | None = None) -> MagicMock:
    """Build a mock pdfplumber PDF object with one page containing *rows*."""
    if rows is None:
        rows = SAMPLE_ROWS

    mock_page = MagicMock()
    mock_page.extract_tables.return_value = [rows]
    mock_page.extract_text.return_value = ""

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


@pytest.fixture()
def parsed_data():
    """Return a VehiclePassportData parsed from SAMPLE_ROWS."""
    mock_pdf = _make_mock_pdf()
    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = EPTSParser("dummy.pdf")
        return parser.parse(), parser


# ---------------------------------------------------------------------------
# Field extraction tests
# ---------------------------------------------------------------------------


def test_epts_number(parsed_data):
    data, _ = parsed_data
    assert data.epts_number == "111222333444555"


def test_vin(parsed_data):
    data, _ = parsed_data
    assert data.vin == "XTA21099071234567"


def test_brand(parsed_data):
    data, _ = parsed_data
    assert data.brand == "LADA (ВАЗ)"


def test_model(parsed_data):
    data, _ = parsed_data
    assert data.model == "GRANTA"


def test_year(parsed_data):
    data, _ = parsed_data
    assert data.year == "2021"


def test_fuel_type(parsed_data):
    data, _ = parsed_data
    assert data.fuel_type == "Бензин"


def test_eco_class(parsed_data):
    data, _ = parsed_data
    assert data.eco_class == "5"


def test_engine_power_split(parsed_data):
    """Engine power '77.0 кВт (104.7 л.с.)' should be split into kW and hp."""
    data, _ = parsed_data
    assert data.engine_power_kw == "77.0"
    assert data.engine_power_hp == "104.7"


def test_owner_name(parsed_data):
    data, _ = parsed_data
    assert data.owner_name == "ООО «Ромашка»"


def test_owner_inn(parsed_data):
    data, _ = parsed_data
    assert data.owner_inn == "7700000001"


def test_issue_date(parsed_data):
    data, _ = parsed_data
    assert data.issue_date == "15.03.2021"


# ---------------------------------------------------------------------------
# Serialisation tests
# ---------------------------------------------------------------------------


def test_to_dict_excludes_none():
    """to_dict() must not include fields whose value is None."""
    mock_page = MagicMock()
    # Only provide epts_number and vin — everything else stays None
    mock_page.extract_tables.return_value = [
        [["1", "Номер ЭПТС", "111222333444555"]],
    ]
    mock_page.extract_text.return_value = ""
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = lambda s: mock_pdf
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("pdfplumber.open", return_value=mock_pdf):
        parser = EPTSParser("dummy.pdf")
        d = parser.to_dict()

    assert "epts_number" in d
    # Fields that were never set must be absent
    for key, value in d.items():
        assert value is not None, f"Field '{key}' should not be None in to_dict()"


def test_to_json_valid(parsed_data):
    """to_json() must produce valid JSON."""
    _, parser = parsed_data
    raw = parser.to_json()
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)
    assert parsed["epts_number"] == "111222333444555"


def test_to_json_indent(parsed_data):
    """to_json() default indent should be 2."""
    _, parser = parsed_data
    raw = parser.to_json()
    # Indented JSON has lines starting with spaces
    assert "\n  " in raw


def test_to_flat_text(parsed_data):
    """to_flat_text() must contain Russian labels and corresponding values."""
    _, parser = parsed_data
    text = parser.to_flat_text()
    assert "Номер ЭПТС" in text
    assert "111222333444555" in text
    assert "VIN" in text
    assert "XTA21099071234567" in text
