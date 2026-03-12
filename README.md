# epts-parser — ЭПТС + ЭПСМ Парсер

[![CI](https://github.com/OlegKarenkikh/epts-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/OlegKarenkikh/epts-parser/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![pdfplumber](https://img.shields.io/badge/pdf-pdfplumber-orange)](https://github.com/jsvine/pdfplumber)

Структурированное извлечение данных из PDF-выписок **ЭПТС** (электронный паспорт транспортного средства) и **ЭПСМ** (электронный паспорт самоходной машины) по стандарту R.019 (Решение Коллегии ЕЭК № 81).

---

## Возможности

- ✅ Поддержка **ЭПТС** (легковые, грузовые, автобусы)
- ✅ Поддержка **ЭПСМ** (тракторы, спецтехника, дорожные машины)
- ✅ Авто-определение типа документа (`parse_any`)
- ✅ Извлечение 30+ полей ЭПТС и 70+ полей ЭПСМ
- ✅ Поддержка многостраничных PDF
- ✅ Первичное извлечение через таблицы (`pdfplumber`)
- ✅ Fallback-извлечение через Regex из свободного текста
- ✅ Валидация извлечённых данных (`validate_epts`, `validate_epsm`)
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

### ЭПТС (транспортное средство)

```python
from epts_parser import EPTSParser

parser = EPTSParser("vyipiska_epts.pdf")
data = parser.parse()

print(parser.to_json())       # JSON
print(parser.to_flat_text())  # читабельный текст

print(data.vin)             # XTA21099071234567
print(data.epts_number)     # 111222333444555
print(data.owner_name)      # ООО «Ромашка»
print(data.engine_power_kw) # 77.0
print(data.engine_power_hp) # 104.7
```

### ЭПСМ (самоходная машина)

```python
from epts_parser import EPSMParser, validate_epsm

rec = EPSMParser().parse_file("traktor_john_deere.pdf")
print(rec.epsm_number)      # 264300200012345
print(rec.brand)            # John Deere
print(rec.category_epsm)   # F

errors = validate_epsm(rec)
if errors:
    for field, msg in errors:
        print(f"[{field}] {msg}")
```

### Авто-определение типа документа

```python
from epts_parser import parse_any, passport_type_str

# Определить тип без полного парсинга
print(passport_type_str("doc.pdf"))  # 'EPTS' или 'EPSM'

# Распарсить автоматически
record = parse_any("doc.pdf")  # → VehiclePassportData или VehiclePassportEPSM
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

## Структура полей ЭПТС

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

## Структура полей ЭПСМ

| Группа | Ключевые поля |
|---|---|
| Документ | `epsm_number`, `epsm_status`, `issue_date`, `printed_date` |
| Идентификация | `vin`, `engine_number`, `chassis_number`, `body_number` |
| Машина | `brand`, `model`, `machine_type`, `category_epsm`, `category_trts` |
| Движитель | `propulsion_type` (колесный / гусеничный / …) |
| Двигатель | `engines[0].engine_power_kw`, `engines[0].fuel_type`, `engines[0].engine_volume` |
| Трансмиссия | `transmission.gearbox_type`, `transmission.pto_shaft` |
| Масса | `curb_mass`, `max_mass`, `payload`, `max_tow_mass`, `axle_loads` |
| Изготовитель | `manufacturer_name`, `manufacturer_country` |
| Соответствие | `compliance_doc_type`, `compliance_doc_number` |
| Таможня | `customs_declaration`, `customs_restrictions` |
| Владелец | `registrations[].action`, `any_restrictions` |

---

## Тестирование

```bash
pip install -e .[dev]
pytest tests/ -v --cov=epts_parser --cov-report=term-missing
```

Целевое покрытие: **≥ 80%** по всем модулям.

---

## Требования

- Python 3.10+
- `pdfplumber>=0.10.0`

Для OCR-режима дополнительно: `pytesseract>=0.3.10`, `pdf2image>=1.16.0`, Tesseract OCR с пакетом `rus`.

---

## Структура проекта

```
epts-parser/
├── .github/workflows/ci.yml
├── epts_parser/
│   ├── __init__.py          # публичный API
│   ├── __main__.py          # CLI
│   ├── models.py            # VehiclePassportData (ЭПТС)
│   ├── models_epsm.py       # VehiclePassportEPSM + sub-dataclasses (ЭПСМ)
│   ├── mappings.py          # таблица маппинга полей
│   ├── parser.py            # EPTSParser
│   ├── parser_epsm.py       # EPSMParser + detect_passport_type
│   ├── auto_parser.py       # parse_any / passport_type_str
│   ├── validators.py        # validate_epts
│   ├── validators_epsm.py   # validate_epsm
│   ├── exporters.py         # to_csv / to_jsonl
│   └── ocr.py
├── tests/
│   ├── fixtures/
│   │   └── john_deere_8r.json
│   ├── test_parser.py
│   ├── test_epsm_parser.py
│   ├── test_auto_parser.py
│   └── test_validators.py
├── docs/FIELDS.md
├── pyproject.toml
└── LICENSE
```

---

## Лицензия

MIT © 2026 [OlegKarenkikh](https://github.com/OlegKarenkikh)
