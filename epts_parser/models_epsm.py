"""VehiclePassportEPSM — data model for EPSM.

Regulation: EEC Board Decision No. 81, 12.07.2016, R.019 schema.
RF implementation: Government Decree No. 981, 28.05.2022.
Active since: 02.11.2022.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EngineDetails:
    """One propulsion unit (ICE or electric)."""

    engine_number: Optional[str] = None
    engine_type: Optional[str] = None
    engine_brand: Optional[str] = None
    engine_volume: Optional[str] = None
    engine_power_kw: Optional[str] = None
    engine_rpm_at_max_power: Optional[str] = None
    engine_torque: Optional[str] = None
    engine_cylinders: Optional[str] = None
    engine_cylinder_layout: Optional[str] = None
    fuel_type: Optional[str] = None
    ignition_type: Optional[str] = None
    electric_voltage: Optional[str] = None
    electric_power_30min_kw: Optional[str] = None
    energy_storage_type: Optional[str] = None
    energy_storage_location: Optional[str] = None
    range_km: Optional[str] = None


@dataclass
class GearboxDetails:
    gearbox_number: Optional[str] = None
    gearbox_brand: Optional[str] = None
    gearbox_type: Optional[str] = None
    gears_forward: Optional[str] = None
    gears_reverse: Optional[str] = None
    gear_ratios: Optional[str] = None


@dataclass
class TransmissionDetails:
    transmission_type: Optional[str] = None
    gearbox: Optional[GearboxDetails] = None
    transfer_case_type: Optional[str] = None
    transfer_case_ratios: Optional[str] = None
    final_drive_type: Optional[str] = None
    final_drive_ratio: Optional[str] = None
    pto_shaft: Optional[str] = None
    drive_axle_number: Optional[str] = None


@dataclass
class AxleLoadDetails:
    axle_index: int = 1
    max_load_kg: Optional[str] = None


@dataclass
class RegistrationRecord:
    state: Optional[str] = None
    owner_type: Optional[str] = None
    action: Optional[str] = None
    action_date: Optional[str] = None
    region: Optional[str] = None


@dataclass
class ConstructionModification:
    description: Optional[str] = None
    characteristics: Optional[str] = None
    approver: Optional[str] = None
    executor: Optional[str] = None


@dataclass
class VehiclePassportEPSM:
    """Full data model for EPSM — Electronic Passport of Self-Propelled Machine.

    Standards:
      - EEC Board Decision No. 81 (2016), R.019 XML schema
      - EEC Board Decision No. 122 (2015), Appendix 7 — categories
      - RF Govt. Decree No. 981 (2022)
      - NAMI Appendix 3 — full field list
    """

    # -- Document identity
    passport_type: str = "ЭПСМ"
    epsm_number: Optional[str] = None
    epsm_status: Optional[str] = None
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    printed_date: Optional[str] = None
    base_code: Optional[str] = None
    base_text: Optional[str] = None

    # -- Machine identification
    vin: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    machine_name: Optional[str] = None
    machine_type: Optional[str] = None
    modification: Optional[str] = None

    # -- Categories
    category_epsm: Optional[str] = None
    category_trts: Optional[str] = None

    # -- Aggregate numbers
    engine_number: Optional[str] = None
    body_number: Optional[str] = None
    chassis_number: Optional[str] = None
    gearbox_number: Optional[str] = None
    drive_axle_number: Optional[str] = None
    satellite_nav_id: Optional[str] = None
    emergency_services_id: Optional[str] = None

    # -- Propulsion type (EPSM-specific)
    propulsion_type: Optional[str] = None

    # -- Color
    color: Optional[str] = None
    color_shade: Optional[str] = None
    color_combined: Optional[bool] = None

    # -- Production
    year: Optional[str] = None
    month: Optional[str] = None
    country_of_manufacture: Optional[str] = None

    # -- Geometry (mm)
    length_mm: Optional[str] = None
    width_mm: Optional[str] = None
    height_mm: Optional[str] = None
    wheelbase_mm: Optional[str] = None
    track_mm: Optional[str] = None
    ground_clearance_mm: Optional[str] = None

    # -- Mass (kg)
    curb_mass: Optional[str] = None
    max_mass: Optional[str] = None
    axle_loads: List[AxleLoadDetails] = field(default_factory=list)
    coupling_load: Optional[str] = None
    payload: Optional[str] = None
    max_combined_mass: Optional[str] = None
    max_tow_mass: Optional[str] = None

    # -- Engine(s)
    engines: List[EngineDetails] = field(default_factory=list)
    hybrid_description: Optional[str] = None
    nominal_voltage: Optional[str] = None

    # -- Transmission
    transmission: Optional[TransmissionDetails] = None

    # -- Chassis & steering
    axle_count: Optional[str] = None
    wheel_count: Optional[str] = None
    layout: Optional[str] = None
    cab_type: Optional[str] = None
    steering_wheel_position: Optional[str] = None
    reversible_operator_seat: Optional[bool] = None
    max_speed_kmh: Optional[str] = None
    suspension_front: Optional[str] = None
    suspension_rear: Optional[str] = None
    steering_description: Optional[str] = None
    brake_service: Optional[str] = None
    brake_parking: Optional[str] = None
    brake_emergency: Optional[str] = None
    tyre_size: Optional[str] = None
    seats_count: Optional[str] = None

    # -- Compliance document
    compliance_doc_type: Optional[str] = None
    compliance_doc_number: Optional[str] = None
    compliance_doc_date: Optional[str] = None
    compliance_doc_issuer: Optional[str] = None

    # -- Manufacturer
    manufacturer_name: Optional[str] = None
    manufacturer_address: Optional[str] = None
    manufacturer_country: Optional[str] = None

    # -- Customs / recycling
    customs_declaration: Optional[str] = None
    customs_restrictions: Optional[str] = None
    import_country: Optional[str] = None
    recycling_paid_country: Optional[str] = None

    # -- Marking locations (EPSM-specific)
    vin_plate_location: Optional[str] = None
    vin_location: Optional[str] = None
    vin_structure: Optional[str] = None
    engine_number_location: Optional[str] = None
    engine_number_structure: Optional[str] = None

    # -- Registration history
    registrations: List[RegistrationRecord] = field(default_factory=list)
    any_restrictions: Optional[str] = None
    registered_country: Optional[str] = None

    # -- Construction modifications
    modifications_history: List[ConstructionModification] = field(default_factory=list)

    # -- Base vehicle
    base_vehicle_brand: Optional[str] = None
    base_vehicle_model: Optional[str] = None
    base_vehicle_passport_number: Optional[str] = None
    base_vehicle_passport_date: Optional[str] = None

    # -- Misc
    additional_info: Optional[str] = None
    manufacturer_info: Optional[str] = None
    tnved_code: Optional[str] = None
    privileged_mode: Optional[str] = None
    notes: Optional[str] = None

    raw_tables: List[str] = field(default_factory=list, repr=False)
