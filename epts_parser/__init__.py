from .models import VehiclePassportData
from .parser import EPTSParser
from .models_epsm import VehiclePassportEPSM
from .parser_epsm import EPSMParser, parse_epsm, detect_passport_type
from .validators import validate_record
from .validators_epsm import validate_epsm
from .auto_parser import parse_any, passport_type_str

__all__ = [
    # EPTS
    "EPTSParser",
    "VehiclePassportData",
    "validate_record",
    # EPSM
    "EPSMParser",
    "VehiclePassportEPSM",
    "parse_epsm",
    "validate_epsm",
    # Auto-detect
    "parse_any",
    "passport_type_str",
    "detect_passport_type",
]
__version__ = "1.1.0"
