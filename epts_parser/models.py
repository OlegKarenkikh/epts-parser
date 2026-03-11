from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VehiclePassportData:
    epts_number: Optional[str] = None
    vin: Optional[str] = None
    pts_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    vehicle_type: Optional[str] = None
    category: Optional[str] = None
    year: Optional[str] = None
    color: Optional[str] = None
    body_number: Optional[str] = None
    chassis_number: Optional[str] = None
    country_of_manufacture: Optional[str] = None
    engine_number: Optional[str] = None
    engine_type: Optional[str] = None
    engine_power_kw: Optional[str] = None
    engine_power_hp: Optional[str] = None
    engine_volume: Optional[str] = None
    fuel_type: Optional[str] = None
    eco_class: Optional[str] = None
    max_mass: Optional[str] = None
    curb_mass: Optional[str] = None
    seats_count: Optional[str] = None
    manufacturer_name: Optional[str] = None
    manufacturer_inn: Optional[str] = None
    manufacturer_country: Optional[str] = None
    otts_number: Optional[str] = None
    otts_date: Optional[str] = None
    customs_declaration: Optional[str] = None
    owner_name: Optional[str] = None
    owner_inn: Optional[str] = None
    owner_ogrn: Optional[str] = None
    owner_address: Optional[str] = None
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    raw_tables: list = field(default_factory=list, repr=False)
