# ЭПТС Парсер — epts-parser

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
- ✅ Вывод в JSON, читабельный текст или CSV
- ✅ Пакетная обработка нескольких файлов
- ✅ OCR-режим для отсканированных PDF
- ✅ CLI-интерфейс

---

## Быстрый старт

### Установка

```bash
git clone https://github.com/OlegKarenkikh/epts-parser.git
cd epts-parser
pip install -r requirements.txt
```

### Использование

#### Программный вызов

```python
from epts_parser import EPTSParser

parser = EPTSParser("vyipiska_epts.pdf")
data = parser.parse()

print(parser.to_json())       # JSON
print(parser.to_flat_text())  # читабельный текст

# Отдельные поля
print(data.vin)           # XTA21099071234567
print(data.epts_number)   # 111222333444555
print(data.owner_name)    # ООО "Ромашка"
```

#### CLI

```bash
# Один файл → JSON (stdout)
python -m epts_parser vyipiska.pdf

# Один файл → читабельный текст
python -m epts_parser vyipiska.pdf --format text

# Папка с PDF → CSV
python -m epts_parser ./docs/ --format csv --output result.csv

# Папка с PDF → JSON Lines
python -m epts_parser ./docs/ --format jsonl --output result.jsonl

# Отсканированный PDF (OCR)
python -m epts_parser scan.pdf --ocr
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

## Требования

- Python 3.10+
- `pdfplumber>=0.10.0`

Для OCR-режима дополнительно:
- `pytesseract>=0.3.10`
- `pdf2image>=1.16.0`
- Tesseract OCR с языковым пакетом `rus`

```bash
pip install -r requirements-ocr.txt
```

---

## Структура проекта

```
epts-parser/
├── epts_parser/
│   ├── __init__.py
│   ├── __main__.py      # CLI точка входа
│   ├── models.py        # Датакласс VehiclePassportData
│   ├── mappings.py      # FIELD_MAPPING (regex → поля)
│   ├── parser.py        # EPTSParser (основная логика)
│   ├── ocr.py           # OCR fallback
│   └── exporters.py     # JSON / CSV / JSONL экспорт
├── tests/
│   └── test_parser.py
├── docs/
│   └── FIELDS.md
├── requirements.txt
├── requirements-ocr.txt
└── LICENSE
```

---

## Тестирование

```bash
pip install pytest
pytest tests/ -v
```

---

## Лицензия

MIT © 2026 [OlegKarenkikh](https://github.com/OlegKarenkikh)
