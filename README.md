# ЭПТС Парсер — epts-parser

[![CI](https://github.com/OlegKarenkikh/epts-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/OlegKarenkikh/epts-parser/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![pdfplumber](https://img.shields.io/badge/pdf-pdfplumber-orange)](https://github.com/jsvine/pdfplumber)

Структурированное извлечение данных из PDF-документа **«Выписка из электронного паспорта транспортного средства» (ЭПТС)**.

---

## Возможности

- ✅ Извлечение 30+ полей из стандартного бланка ЭПТС
- ✅ Поддержка многостраничных PDF
- ✅ Первичное извлечение через таблицы (`pdfplumber`)
- ✅ Fallback-извлечение через Regex из свободного текста
- ✅ Вывод в JSON, читабельный текст, CSV или JSONL
- ✅ Пакетная обработка директорий (рекурсивно)
- ✅ OCR-режим для отсканированных PDF
- ✅ CLI-интерфейс (`epts-parser` / `python -m epts_parser`)

---

## Установка

```bash
# Из GitHub
pip install git+https://github.com/OlegKarenkikh/epts-parser.git

# Для разработки
git clone https://github.com/OlegKarenkikh/epts-parser.git
cd epts-parser
pip install -e .[dev]

# OCR-режим
pip install -e .[ocr]
```

---

## Быстрый старт

### Программный вызов

```python
from epts_parser import EPTSParser

parser = EPTSParser("vyipiska_epts.pdf")
data = parser.parse()

print(parser.to_json())       # JSON
print(parser.to_flat_text())  # читабельный текст

# Отдельные поля
print(data.vin)             # XTA21099071234567
print(data.epts_number)     # 111222333444555
print(data.owner_name)      # ООО «Ромашка»
print(data.engine_power_kw) # 77.0
print(data.engine_power_hp) # 104.7
```

### CLI

```bash
# Один файл → JSON (stdout)
epts-parser vyipiska.pdf

# Один файл → читабельный текст
epts-parser vyipiska.pdf --format text

# Папка с PDF → CSV (рекурсивно)
epts-parser ./docs/ --format csv --output result.csv

# Папка с PDF → JSON Lines
epts-parser ./docs/ --format jsonl --output result.jsonl

# Отсканированный PDF (OCR)
epts-parser scan.pdf --ocr
```

---

## Структура полей

| Группа | Поля |
|---|---|
| Идентификация | `epts_number`, `vin`, `pts_number` |
| Общие сведения | `brand`, `model`, `vehicle_type`, `category`, `year`, `color` |
| Номера агрегатов | `body_number`, `chassis_number`, `engine_number` |
| Двигатель | `engine_type`, `engine_power_kw`, `engine_power_hp`, `engine_volume`, `fuel_type`, `eco_class` |
| Масса / места | `max_mass`, `curb_mass`, `seats_count` |
| Изготовитель | `manufacturer_name`, `manufacturer_inn`, `manufacturer_country` |
| ОТТС / таможня | `otts_number`, `otts_date`, `customs_declaration` |
| Владелец | `owner_name`, `owner_inn`, `owner_ogrn`, `owner_address` |
| Документ | `issue_date`, `issuer` |

Подробное описание с примерами значений: [docs/FIELDS.md](docs/FIELDS.md)

---

## Тестирование

```bash
pip install -e .[dev]
pytest tests/ -v --cov=epts_parser
```

---

## Требования

- Python 3.10+
- `pdfplumber>=0.10.0`

Для OCR-режима дополнительно: `pytesseract>=0.3.10`, `pdf2image>=1.16.0`, Tesseract OCR с пакетом `rus`.

---

## Структура проекта

```
epts-parser/
├── .github/workflows/ci.yml  # GitHub Actions: pytest + ruff
├── epts_parser/
│   ├── __init__.py
│   ├── __main__.py      # CLI
│   ├── models.py
│   ├── mappings.py
│   ├── parser.py
│   ├── ocr.py
│   └── exporters.py
├── tests/test_parser.py
├── docs/FIELDS.md
├── pyproject.toml
├── requirements.txt
├── requirements-ocr.txt
└── LICENSE
```

---

## Лицензия

MIT © 2026 [OlegKarenkikh](https://github.com/OlegKarenkikh)
