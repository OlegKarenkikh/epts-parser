from __future__ import annotations

from pathlib import Path


def pdf_to_text_via_ocr(
    pdf_path: str | Path,
    lang: str = "rus",
    dpi: int = 300,
) -> str:
    """Convert a PDF to text via OCR using pdf2image and pytesseract.

    Requires:
        pip install pdf2image pytesseract
        Tesseract OCR installed with the ``rus`` language pack.
    """
    import pytesseract
    from pdf2image import convert_from_path

    images = convert_from_path(str(pdf_path), dpi=dpi)
    pages: list[str] = []
    for image in images:
        text = pytesseract.image_to_string(image, lang=lang)
        pages.append(text)
    return "\n".join(pages)
