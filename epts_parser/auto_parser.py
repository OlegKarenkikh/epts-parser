"""
auto_parser.py — auto-detects document type (EPTS / EPSM) and returns
the appropriate parsed record.

Usage:
    from epts_parser.auto_parser import parse_any
    record = parse_any("my_file.pdf")
    print(type(record).__name__)  # VehiclePassportData or VehiclePassportEPSM
"""
from __future__ import annotations

from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore

from .parser_epsm import detect_passport_type, EPSMParser


def parse_any(path: str | Path):
    """
    Auto-detect passport type from PDF content and dispatch to the
    correct parser.

    Returns:
        VehiclePassportData  — for EPTS (transport vehicle)
        VehiclePassportEPSM  — for EPSM (self-propelled machine)

    Raises:
        ValueError  — if document type cannot be determined
        ImportError — if pdfplumber is not installed
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    path = Path(path)
    with pdfplumber.open(path) as pdf:
        preview = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])

    doc_type = detect_passport_type(preview)

    if doc_type == "EPSM":
        return EPSMParser().parse_file(path)
    elif doc_type == "EPTS":
        from .parser import EPTSParser  # noqa: PLC0415
        return EPTSParser().parse_file(path)
    else:
        raise ValueError(
            f"Cannot detect passport type in '{path.name}'. "
            "Expected EPTS or EPSM. Check the PDF content."
        )


def passport_type_str(path: str | Path) -> str:
    """Return 'EPTS', 'EPSM', or 'UNKNOWN' without full parsing."""
    if pdfplumber is None:
        raise ImportError("pdfplumber is required")
    with pdfplumber.open(path) as pdf:
        preview = "\n".join((p.extract_text() or "") for p in pdf.pages[:2])
    return detect_passport_type(preview)
