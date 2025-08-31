# Package initialization
__version__ = "2.0.0"
__author__ = "Enterprise Development Team"
__description__ = "Professional name and address validation platform"

try:
    from .services.validation_service import ValidationService
    from .utils.config import load_usps_credentials
    from .utils.logger import AppLogger
    
    __all__ = ['ValidationService', 'load_usps_credentials', 'AppLogger']
    
except ImportError as e:
    print(f"Warning: Some components could not be imported: {e}")
    __all__ = []