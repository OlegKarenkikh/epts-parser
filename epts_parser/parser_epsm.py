"""
EPSM PDF parser — Electronic Passport of Self-Propelled Machine.
Handles выписки из СЭП for tractors, road-construction machines, etc.
Uses the same text-extraction pipeline as parser.py (pdfplumber).

Standards:
  EEC Board Decision No. 81 (12.07.2016), R.019 XML schema
  RF Govt Decree No. 981 (28.05.2022), active since 02.11.2022
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore

from .models_epsm import (
    VehiclePassportEPSM,
    EngineDetails,
    GearboxDetails,
    TransmissionDetails,
    AxleLoadDetails,
    RegistrationRecord,
)


# ── Regex helpers ──────────────────────────────────────────────────────────

def _first(pattern: str, text: str, flags: int = re.I) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _after_label(label: str, text: str, max_len: int = 200) -> Optional[str]:
    """
    Extract value after a field label.
    Handles 'Label: value' and tabular 'Label\nvalue' layouts.
    """
    pat = rf"{re.escape(label)}\s*[:\-\u2013\u2014]?\s*(.{{1,{max_len}}}?)(?=\n|$)"
    m = re.search(pat, text, re.I)
    if m:
        val = m.group(1).strip(" \t|")
        if val:
            return val
    pat2 = rf"{re.escape(label)}\s*\n+\s*(.{{1,{max_len}}}?)(?=\n|$)"
    m2 = re.search(pat2, text, re.I)
    if m2:
        val2 = m2.group(1).strip(" \t|")
        if val2:
            return val2
    return None


# EPSM number: 15 digits (same length as EPTS), per R.019 / EEC Decision 81
_RE_EPSM_NUMBER = re.compile(r"\b(\d{15})\b")
_RE_DATE        = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")


# ── Document-type detector ─────────────────────────────────────────────────

def detect_passport_type(text: str) -> str:
    """
    Detect whether a PDF extract is EPTS (vehicle) or EPSM (self-propelled machine).
    Returns 'EPSM', 'EPTS', or 'UNKNOWN'.

    Uses keyword-scoring on the first 2000 characters:
    counts EPSM markers (гостехнадзор, тип движителя, гусеничн*, трактор, ...)
    and EPTS markers (ГИБДД, МРЭО, одобрение типа ТС, ...),
    then picks the winner. Both document types share the same R.019 schema,
    so distinction is purely by vocabulary.
    """
    t = text[:2000].lower()
    epsm_markers = [
        "паспорт самоходной машины",
        "электронный паспорт самоходной",
        "эпсм",
        "гостехнадзор",
        "тип движителя",
        "вал отбора мощности",
        "раздаточная коробка",
        "гусеничн",
        "трактор",
        "самоходн",
    ]
    epts_markers = [
        "паспорт транспортного средства",
        "электронный паспорт транспортного",
        "эптс",
        "гибдд",
        "мрэо",
        "одобрение типа транспортного средства",
        "оттс",
    ]
    epsm_score = sum(1 for m in epsm_markers if m in t)
    epts_score = sum(1 for m in epts_markers if m in t)
    if epsm_score > epts_score:
        return "EPSM"
    if epts_score > epsm_score:
        return "EPTS"
    if re.search(r"самоходн", text[:3000], re.I):
        return "EPSM"
    return "UNKNOWN"


# ── Main parser ────────────────────────────────────────────────────────────

class EPSMParser:
    """Parse a PDF выписка of EPSM into VehiclePassportEPSM."""

    def parse_file(self, path: str | Path) -> VehiclePassportEPSM:
        if pdfplumber is None:
            raise ImportError("pdfplumber is required: pip install pdfplumber")
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        full_text = "\n".join(pages)
        return self.parse_text(full_text)

    def parse_text(self, text: str) -> VehiclePassportEPSM:
        rec = VehiclePassportEPSM()
        self._parse_document_identity(text, rec)
        self._parse_identification(text, rec)
        self._parse_machine_info(text, rec)
        self._parse_geometry_mass(text, rec)
        self._parse_engine(text, rec)
        self._parse_transmission(text, rec)
        self._parse_chassis(text, rec)
        self._parse_compliance(text, rec)
        self._parse_manufacturer(text, rec)
        self._parse_customs(text, rec)
        self._parse_markings(text, rec)
        self._parse_registration(text, rec)
        return rec

    def _parse_document_identity(self, text: str, r: VehiclePassportEPSM) -> None:
        # Try labeled pattern first: "Номер ЭПСМ: XXXXXXXXXXXXXXX"
        m = re.search(r"[Нн]омер\s+[ЭэEe][ПпPp][СсSs][МмMm]\s*[:\-]?\s*(\d{15})", text)
        if m:
            r.epsm_number = m.group(1)
        else:
            m2 = _RE_EPSM_NUMBER.search(text)
            r.epsm_number = m2.group(1) if m2 else None
        r.epsm_status = (
            _after_label("Статус электронного паспорта", text)
            or _after_label("Статус", text)
        )
        dates = _RE_DATE.findall(text)
        r.issue_date = dates[0] if dates else None
        r.issuer = (
            _after_label("Наименование организации", text)
            or _after_label("оформившей электронный паспорт", text)
        )
        printed = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})", text)
        r.printed_date = f"{printed.group(1)} {printed.group(2)}" if printed else None

    def _parse_identification(self, text: str, r: VehiclePassportEPSM) -> None:
        r.vin = _after_label("Идентификационный номер", text) or _first(
            r"\bVIN\b\s*[:\-]?\s*([A-Z0-9]{6,17})", text
        )
        r.engine_number  = _after_label("Номер двигателя", text)
        r.body_number    = _after_label("Номер кузова", text) or _after_label("Номер кабины", text)
        r.chassis_number = _after_label("Номер шасси", text) or _after_label("Номер рамы", text)
        r.gearbox_number = _after_label("Номер коробки передач", text)
        r.drive_axle_number = _after_label("Номер основного ведущего моста", text)
        r.propulsion_type = _after_label("Тип движителя", text)
        r.color = _after_label("Цвет кузова", text) or _after_label("Цвет кабины", text)
        ym = re.search(
            r"[Мм]есяц\s+и\s+год\s+изготовления\s*[:\-]?\s*(\d{2})\s*/\s*(\d{4})", text
        )
        if ym:
            r.month, r.year = ym.group(1), ym.group(2)
        else:
            r.year = _first(r"[Гг]од\s+изготовления\s*[:\-]?\s*(\d{4})", text)

    def _parse_machine_info(self, text: str, r: VehiclePassportEPSM) -> None:
        r.brand        = _after_label("Марка", text)
        r.model        = _after_label("Коммерческое наименование", text)
        r.machine_name = _after_label("Наименование, определяемое", text)
        r.machine_type = _after_label("Тип машины", text) or _after_label("Тип", text)
        r.modification = _after_label("Модификация", text)
        r.category_epsm = _after_label(
            "Категория в соответствии с Правилами оформления", text
        ) or _first(r"[Кк]атегория\s*[:\-]?\s*([A-FRabI]+)", text)
        r.category_trts = _after_label(
            "Категория в соответствии с техническим регламентом", text
        )

    def _parse_geometry_mass(self, text: str, r: VehiclePassportEPSM) -> None:
        def mm(label: str) -> Optional[str]:
            return _first(
                rf"{re.escape(label)}\s*[:\-]?\s*(\d{{3,5}})\s*(?:мм|mm)", text, re.I
            )

        r.length_mm = mm("Длина")
        r.width_mm  = mm("Ширина")
        r.height_mm = mm("Высота")
        r.wheelbase_mm = mm("База") or mm("Колёсная база")
        r.track_mm  = mm("Колея")
        r.ground_clearance_mm = mm("Дорожный просвет")

        def kg(label: str) -> Optional[str]:
            return _first(
                rf"{re.escape(label)}\s*[:\-]?\s*(\d{{3,6}})\s*(?:кг|kg)", text, re.I
            )

        r.curb_mass    = kg("Снаряжённая") or kg("Снаряженная масса")
        r.max_mass     = kg("Технически допустимая максимальная масса")
        r.payload      = kg("Полезная нагрузка")
        r.max_tow_mass = kg("Технически допустимая буксируемая масса")
        r.coupling_load = kg("Вертикальная нагрузка в точке сцепки") or kg(
            "нагрузка в точке сцепки"
        )
        for m in re.finditer(r"[Оо]сь\s+(\d+)\s*[:\-]?\s*(\d{3,6})\s*кг", text):
            r.axle_loads.append(
                AxleLoadDetails(axle_index=int(m.group(1)), max_load_kg=m.group(2))
            )

    def _parse_engine(self, text: str, r: VehiclePassportEPSM) -> None:
        eng = EngineDetails()
        eng.engine_number = r.engine_number
        eng.engine_brand  = _after_label("Марка двигателя", text) or _after_label(
            "Двигатель внутреннего сгорания", text
        )
        eng.engine_type   = _after_label("Тип двигателя", text)
        eng.engine_volume = _first(
            r"[Рр]абочий\s+объём?\s+цилиндров\s*[:\-]?\s*(\d{2,5})\s*(?:см|cm)", text
        )
        eng.engine_power_kw = _first(
            r"[Мм]аксимальная\s+мощность\s*[:\-]?\s*([\d,\.]+)\s*кВт", text
        )
        eng.engine_torque = _first(
            r"[Мм]аксимальный\s+крутящий\s+момент\s*[:\-]?\s*([\d,\.]+)\s*Н", text
        )
        eng.engine_cylinders = _first(
            r"[Кк]оличество\s+цилиндров\s*[:\-]?\s*(\d{1,2})", text
        )
        eng.fuel_type = _after_label("Топливо", text)
        eng.electric_voltage = _first(
            r"[Рр]абочее\s+напряжение\s*[:\-]?\s*(\d{2,4})\s*[ВV]", text
        )
        eng.electric_power_30min_kw = _first(
            r"30.?минутн\w+\s+мощность\s*[:\-]?\s*([\d,\.]+)\s*кВт", text
        )
        r.engines = [eng]
        r.hybrid_description = _after_label("Описание гибридной", text)
        r.nominal_voltage = _first(
            r"[Нн]оминальное\s+напряжение\s*[:\-]?\s*(\d{2,4})\s*[ВV]", text
        )

    def _parse_transmission(self, text: str, r: VehiclePassportEPSM) -> None:
        gb = GearboxDetails()
        gb.gearbox_number = r.gearbox_number
        gb.gearbox_type   = _after_label("Коробка передач", text)
        gb.gears_forward  = _first(r"[Чч]исло\s+передач\s+вперёд\s*[:\-]?\s*(\d+)", text)
        gb.gears_reverse  = _first(r"[Чч]исло\s+передач\s+назад\s*[:\-]?\s*(\d+)", text)
        t = TransmissionDetails()
        t.gearbox = gb
        t.transmission_type = _after_label("Трансмиссия", text)
        t.transfer_case_type = _after_label("Раздаточная коробка", text)
        t.final_drive_ratio  = _first(
            r"[Пп]ередаточное\s+число\s+главной\s+передачи\s*[:\-]?\s*([\d,\.]+)", text
        )
        t.pto_shaft = _after_label("Вал отбора мощности", text)
        t.drive_axle_number = r.drive_axle_number
        r.transmission = t

    def _parse_chassis(self, text: str, r: VehiclePassportEPSM) -> None:
        r.axle_count = _first(r"[Кк]оличество\s+осей\s*[:\-]?\s*(\d)", text)
        r.layout = _after_label("Схема компоновки", text)
        r.steering_wheel_position = _after_label("Положение рулевого колеса", text)
        r.max_speed_kmh = _first(
            r"[Мм]аксимальная\s+скорость\s*[:\-]?\s*(\d{2,3})\s*(?:км/ч|km/h)", text
        )
        r.suspension_front = _after_label("Передняя подвеска", text)
        r.suspension_rear  = _after_label("Задняя подвеска", text)
        r.steering_description = _after_label("Рулевое управление", text)
        r.brake_service  = _after_label("Рабочая тормозная система", text)
        r.brake_parking  = _after_label("Стояночная тормозная система", text)
        r.tyre_size = _after_label("Шины", text) or _after_label("Размерность шин", text)
        r.seats_count = _first(r"[Пп]ассажировместимость\s*[:\-]?\s*(\d+)", text)

    def _parse_compliance(self, text: str, r: VehiclePassportEPSM) -> None:
        r.compliance_doc_type = _after_label(
            "Документ, подтверждающий соответствие", text
        )
        r.compliance_doc_number = _first(
            r"(?:ОТТС|сертификат|декларация|свидетельство)\s*[№N]?\s*([\w\-/]+)",
            text,
            re.I,
        )
        r.compliance_doc_date   = _after_label("Дата одобрения", text) or _after_label(
            "Дата сертификата", text
        )
        r.compliance_doc_issuer = _after_label("Орган по сертификации", text)

    def _parse_manufacturer(self, text: str, r: VehiclePassportEPSM) -> None:
        r.manufacturer_name    = _after_label("Изготовитель и его адрес", text) or _after_label(
            "Изготовитель", text
        )
        r.manufacturer_address = _after_label("Адрес изготовителя", text)
        r.manufacturer_country = _after_label("Страна происхождения", text)
        r.country_of_manufacture = r.manufacturer_country

    def _parse_customs(self, text: str, r: VehiclePassportEPSM) -> None:
        r.customs_declaration = _first(
            r"(?:таможенн\w+\s+(?:приходн\w+\s+ордер|декларац\w+))[^\d]*"
            r"([0-9]{8}/[0-9]{6}/[0-9]{7,10})",
            text,
        )
        r.import_country = _after_label("Страна вывоза", text)
        r.recycling_paid_country = _after_label("уплаты утилизационного сбора", text)

    def _parse_markings(self, text: str, r: VehiclePassportEPSM) -> None:
        r.vin_plate_location = _after_label(
            "Место расположения таблички изготовителя", text
        )
        r.vin_location = _after_label(
            "Место расположения идентификационного номера", text
        )
        r.vin_structure = _after_label(
            "Структура и содержание идентификационного номера", text
        )
        r.engine_number_location = _after_label(
            "Место расположения номера двигателя", text
        )
        r.engine_number_structure = _after_label(
            "Структура и содержание номера двигателя", text
        )

    def _parse_registration(self, text: str, r: VehiclePassportEPSM) -> None:
        r.any_restrictions   = _after_label("ограничения", text) or _after_label(
            "обременения", text
        )
        r.registered_country = _after_label("Государство - член", text)
        for m in re.finditer(
            r"[Рр]егистрационное\s+действие\s*[:\-]?\s*(.+?)\n"
            r".*?[Дд]ата\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{4})",
            text,
            re.S,
        ):
            r.registrations.append(
                RegistrationRecord(action=m.group(1).strip(), action_date=m.group(2))
            )


# ── Convenience function ───────────────────────────────────────────────────

def parse_epsm(path: str | Path) -> VehiclePassportEPSM:
    """Parse an EPSM PDF file and return a VehiclePassportEPSM record."""
    return EPSMParser().parse_file(path)
