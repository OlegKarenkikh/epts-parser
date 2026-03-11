from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import VehiclePassportData


def to_csv(
    records: Iterable[VehiclePassportData],
    output_path: str | Path,
) -> None:
    """Write an iterable of VehiclePassportData records to a CSV file."""
    import dataclasses

    records_list = list(records)
    if not records_list:
        Path(output_path).write_text("", encoding="utf-8")
        return

    fieldnames = [
        f.name
        for f in dataclasses.fields(VehiclePassportData)
        if f.name != "raw_tables"
    ]

    # FIX: utf-8-sig adds BOM so the file opens correctly in Excel
    with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records_list:
            # FIX: replace None with empty string — avoids literal "None" in cells
            row = {
                k: (v if v is not None else "")
                for k, v in dataclasses.asdict(record).items()
                if k != "raw_tables"
            }
            writer.writerow(row)


def to_jsonl(
    records: Iterable[VehiclePassportData],
    output_path: str | Path,
) -> None:
    """Write an iterable of VehiclePassportData records to a JSON Lines file."""
    import dataclasses

    with open(output_path, "w", encoding="utf-8") as fh:
        for record in records:
            row = {
                k: v
                for k, v in dataclasses.asdict(record).items()
                if v is not None and k != "raw_tables"
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
