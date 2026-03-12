"""
Tests for auto_parser: passport_type_str and parse_any dispatch logic.
No real PDF required — we test the detect_passport_type routing.
"""
import pytest
from unittest.mock import patch, MagicMock

from epts_parser.parser_epsm import detect_passport_type
from epts_parser.auto_parser import parse_any, passport_type_str
from epts_parser.models_epsm import VehiclePassportEPSM


class TestDetectPassportType:
    """Unit tests for detect_passport_type (no PDF I/O)."""

    def test_epsm_wins_on_score(self):
        text = (
            "Электронный паспорт самоходной машины\n"
            "ЭПСМ\nГостехнадзор\nТип движителя: гусеничный\n"
            "Трактор Кировец\nВал отбора мощности: задний\n"
        )
        assert detect_passport_type(text) == "EPSM"

    def test_epts_wins_on_score(self):
        text = (
            "Электронный паспорт транспортного средства\n"
            "ЭПТС\nГИБДД МРЭО\nОдобрение типа транспортного средства\nОТТС\n"
        )
        assert detect_passport_type(text) == "EPTS"

    def test_epsm_fallback_via_samohodny(self):
        text = "Самоходная машина без явных маркеров"
        assert detect_passport_type(text) == "EPSM"

    def test_unknown_no_markers(self):
        result = detect_passport_type("Абсолютно нейтральный текст без слов")
        assert result == "UNKNOWN"

    def test_epsm_marker_in_uppercase(self):
        text = "ПАСПОРТ САМОХОДНОЙ МАШИНЫ И ДРУГИХ ВИДОВ ТЕХНИКИ\nГОСТЕХНАДЗОР"
        assert detect_passport_type(text) == "EPSM"


class TestPassportTypeStr:
    """Test passport_type_str with mocked pdfplumber."""

    def _make_pdf_mock(self, page_text: str):
        page = MagicMock()
        page.extract_text.return_value = page_text
        pdf_ctx = MagicMock()
        pdf_ctx.__enter__ = MagicMock(return_value=pdf_ctx)
        pdf_ctx.__exit__ = MagicMock(return_value=False)
        pdf_ctx.pages = [page]
        return pdf_ctx

    def test_returns_epts_for_vehicle_pdf(self, tmp_path):
        fake_pdf = tmp_path / "test.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")
        mock_pdf = self._make_pdf_mock(
            "Электронный паспорт транспортного средства ЭПТС ГИБДД МРЭО"
        )
        with patch("epts_parser.auto_parser.pdfplumber") as mock_pdfplumber:
            mock_pdfplumber.open.return_value = mock_pdf
            result = passport_type_str(fake_pdf)
        assert result == "EPTS"

    def test_returns_epsm_for_machine_pdf(self, tmp_path):
        fake_pdf = tmp_path / "test.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")
        mock_pdf = self._make_pdf_mock(
            "Электронный паспорт самоходной машины ЭПСМ Гостехнадзор Трактор"
        )
        with patch("epts_parser.auto_parser.pdfplumber") as mock_pdfplumber:
            mock_pdfplumber.open.return_value = mock_pdf
            result = passport_type_str(fake_pdf)
        assert result == "EPSM"


class TestParseAnyDispatch:
    """Test that parse_any dispatches to the correct parser."""

    def _make_pdf_mock(self, page_text: str):
        page = MagicMock()
        page.extract_text.return_value = page_text
        pdf_ctx = MagicMock()
        pdf_ctx.__enter__ = MagicMock(return_value=pdf_ctx)
        pdf_ctx.__exit__ = MagicMock(return_value=False)
        pdf_ctx.pages = [page, page]
        return pdf_ctx

    def test_dispatches_to_epsm_parser(self, tmp_path):
        fake_pdf = tmp_path / "epsm.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")
        epsm_text = (
            "Электронный паспорт самоходной машины ЭПСМ Гостехнадзор "
            "Тип движителя колесный Трактор"
        )
        mock_pdf = self._make_pdf_mock(epsm_text)
        with patch("epts_parser.auto_parser.pdfplumber") as ap_mock, \
             patch("epts_parser.parser_epsm.pdfplumber") as ep_mock:  # noqa: F841
            ap_mock.open.return_value = mock_pdf
            ep_mock.open.return_value = mock_pdf
            result = parse_any(fake_pdf)
        assert isinstance(result, VehiclePassportEPSM)

    def test_raises_on_unknown_type(self, tmp_path):
        fake_pdf = tmp_path / "unknown.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")
        mock_pdf = self._make_pdf_mock("Совершенно непонятный документ")
        with patch("epts_parser.auto_parser.pdfplumber") as ap_mock:
            ap_mock.open.return_value = mock_pdf
            with pytest.raises(ValueError, match="Cannot detect"):
                parse_any(fake_pdf)
