"""
Tests for exporters: to_csv and to_jsonl.
"""
import csv
import json

import pytest

from epts_parser.models import VehiclePassportData
from epts_parser.exporters import to_csv, to_jsonl


@pytest.fixture
def sample_records():
    return [
        VehiclePassportData(
            epts_number="111222333444555",
            vin="XTA21099071234567",
            brand="LADA",
            model="VESTA",
            year="2023",
            fuel_type="Бензин",
            engine_power_kw="77.0",
            owner_name="Иванов Иван Иванович",
        ),
        VehiclePassportData(
            epts_number="999888777666555",
            vin="WAUZZZ8K9BA012345",
            brand="Audi",
            model="A4",
            year="2022",
        ),
    ]


class TestToCsv:
    def test_creates_file(self, tmp_path, sample_records):
        out = tmp_path / "out.csv"
        to_csv(sample_records, out)
        assert out.exists()

    def test_header_contains_vin(self, tmp_path, sample_records):
        out = tmp_path / "out.csv"
        to_csv(sample_records, out)
        with open(out, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            assert "vin" in reader.fieldnames

    def test_row_count(self, tmp_path, sample_records):
        out = tmp_path / "out.csv"
        to_csv(sample_records, out)
        with open(out, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2

    def test_none_fields_empty_string(self, tmp_path, sample_records):
        out = tmp_path / "out.csv"
        to_csv(sample_records, out)
        with open(out, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        assert rows[1]["engine_power_kw"] == ""

    def test_values_correct(self, tmp_path, sample_records):
        out = tmp_path / "out.csv"
        to_csv(sample_records, out)
        with open(out, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["brand"] == "LADA"
        assert rows[1]["brand"] == "Audi"

    def test_empty_records(self, tmp_path):
        out = tmp_path / "empty.csv"
        to_csv([], out)
        assert out.read_text(encoding="utf-8") == ""


class TestToJsonl:
    def test_creates_file(self, tmp_path, sample_records):
        out = tmp_path / "out.jsonl"
        to_jsonl(sample_records, out)
        assert out.exists()

    def test_line_count(self, tmp_path, sample_records):
        out = tmp_path / "out.jsonl"
        to_jsonl(sample_records, out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_valid_json_per_line(self, tmp_path, sample_records):
        out = tmp_path / "out.jsonl"
        to_jsonl(sample_records, out)
        for line in out.read_text(encoding="utf-8").strip().splitlines():
            obj = json.loads(line)
            assert "vin" in obj

    def test_none_fields_excluded(self, tmp_path, sample_records):
        out = tmp_path / "out.jsonl"
        to_jsonl(sample_records, out)
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        obj2 = json.loads(lines[1])
        assert "engine_power_kw" not in obj2

    def test_cyrillic_preserved(self, tmp_path, sample_records):
        out = tmp_path / "out.jsonl"
        to_jsonl(sample_records, out)
        content = out.read_text(encoding="utf-8")
        assert "Иванов" in content
