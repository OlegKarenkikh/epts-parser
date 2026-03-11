"""Command-line interface for epts-parser."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m epts_parser",
        description="Извлечение данных из ЭПТС PDF-документов.",
    )
    p.add_argument(
        "input",
        help="Путь к PDF-файлу или директории с PDF-файлами.",
    )
    p.add_argument(
        "--format",
        choices=["json", "text", "csv", "jsonl"],
        default="json",
        dest="fmt",
        help="Формат вывода (по умолчанию: json).",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Путь к выходному файлу (по умолчанию: stdout).",
    )
    p.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Использовать OCR для извлечения текста.",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Отступ для JSON-вывода (по умолчанию: 2).",
    )
    return p


def _collect_pdfs(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(input_path.glob("**/*.pdf"))
    return [input_path]


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    from .exporters import to_csv, to_jsonl
    from .parser import EPTSParser

    input_path = Path(args.input)
    pdf_files = _collect_pdfs(input_path)

    if not pdf_files:
        print(f"Нет PDF-файлов в: {input_path}", file=sys.stderr)
        sys.exit(1)

    parsers: list[EPTSParser] = []
    for pdf in pdf_files:
        parser = EPTSParser(pdf, ocr=args.ocr)
        parser.parse()
        parsers.append(parser)

    fmt = args.fmt
    output = args.output

    if fmt == "csv":
        records = [p._data for p in parsers]  # type: ignore[union-attr]
        if output:
            to_csv(records, output)
        else:
            import csv
            import dataclasses
            import io

            from .models import VehiclePassportData

            fieldnames = [
                f.name
                for f in dataclasses.fields(VehiclePassportData)
                if f.name != "raw_tables"
            ]
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                row = {
                    k: (v if v is not None else "")
                    for k, v in dataclasses.asdict(record).items()
                    if k != "raw_tables"
                }
                writer.writerow(row)
            print(buf.getvalue(), end="")

    elif fmt == "jsonl":
        records = [p._data for p in parsers]  # type: ignore[union-attr]
        if output:
            to_jsonl(records, output)
        else:
            import dataclasses

            for record in records:
                row = {
                    k: v
                    for k, v in dataclasses.asdict(record).items()
                    if v is not None and k != "raw_tables"
                }
                print(json.dumps(row, ensure_ascii=False))

    elif fmt == "text":
        lines_out: list[str] = []
        for pdf, parser in zip(pdf_files, parsers):
            if len(pdf_files) > 1:
                lines_out.append(f"=== {pdf.name} ===")
            lines_out.append(parser.to_flat_text())
        text_result = "\n".join(lines_out)
        if output:
            Path(output).write_text(text_result, encoding="utf-8")
        else:
            print(text_result)

    else:  # json
        if len(parsers) == 1:
            result = parsers[0].to_json(indent=args.indent)
        else:
            result = json.dumps(
                [p.to_dict() for p in parsers],
                ensure_ascii=False,
                indent=args.indent,
            )
        if output:
            Path(output).write_text(result, encoding="utf-8")
        else:
            print(result)


if __name__ == "__main__":
    main()
