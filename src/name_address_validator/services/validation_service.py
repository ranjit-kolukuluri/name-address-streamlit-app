# src/name_address_validator/services/validation_service.py
"""
Complete Working Validation Service
"""

import time
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..validators.name_validator import EnhancedNameValidator
from ..validators.address_validator import USPSAddressValidator
from ..utils.config import load_usps_credentials


class ValidationService:
    """
    Complete working validation service
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or self._default_logger
        
        # Initialize validators
        self.name_validator = EnhancedNameValidator()
        self.address_validator = None
        
        # Initialize USPS validator
        self._initialize_address_validator()
        
        self.debug_callback("✅ ValidationService initialized", "SERVICE")
    
    def _default_logger(self, message: str, category: str = "GENERAL", level: str = "INFO"):
        """Default logging function"""
        print(f"[{level}] {category}: {message}")
    
    def _initialize_address_validator(self):
        """Initialize USPS address validator"""
        try:
            client_id, client_secret = load_usps_credentials()
            if client_id and client_secret:
                self.address_validator = USPSAddressValidator(
                    client_id, 
                    client_secret,
                    debug_callback=self.debug_callback
                )
                self.debug_callback("✅ USPS validator initialized", "SERVICE")
            else:
                self.debug_callback("⚠️ USPS credentials not available", "SERVICE")
        except Exception as e:
            self.debug_callback(f"❌ Failed to initialize USPS validator: {str(e)}", "SERVICE")
    
    # SERVICE STATUS METHODS
    
    def is_name_validation_available(self) -> bool:
        """Check if name validation is available"""
        return self.name_validator is not None
    
    def is_address_validation_available(self) -> bool:
        """Check if USPS address validation is available"""
        return self.address_validator is not None and self.address_validator.is_configured()
    
    def get_service_status(self) -> Dict:
        """Get comprehensive service status"""
        return {
            'name_validation_available': self.is_name_validation_available(),
            'address_validation_available': self.is_address_validation_available(),
            'usps_configured': self.address_validator is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    # SINGLE RECORD VALIDATION
    
    def validate_single_record(self, first_name: str, last_name: str, 
                              street_address: str, city: str, state: str, zip_code: str) -> Dict:
        """Validate a single complete record (name + address)"""
        self.debug_callback("🔍 Single record validation started", "VALIDATION")
        start_time = time.time()
        
        results = {
            'timestamp': datetime.now(),
            'name_result': None,
            'address_result': None,
            'overall_valid': False,
            'overall_confidence': 0.0,
            'processing_time_ms': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate name
            if self.is_name_validation_available():
                name_result = self.name_validator.validate(first_name, last_name)
                results['name_result'] = name_result
            else:
                results['errors'].append("Name validation service unavailable")
            
            # Validate address
            if self.is_address_validation_available():
                address_data = {
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                }
                address_result = self.address_validator.validate_address(address_data)
                results['address_result'] = address_result
            else:
                results['address_result'] = {
                    'success': False,
                    'error': 'USPS API not configured',
                    'deliverable': False
                }
                results['warnings'].append("USPS validation unavailable")
            
            # Calculate overall results
            name_valid = results['name_result'].get('valid', False) if results['name_result'] else False
            address_deliverable = results['address_result'].get('deliverable', False)
            
            results['overall_valid'] = name_valid and address_deliverable
            
            # Calculate confidence
            name_confidence = results['name_result'].get('confidence', 0) if results['name_result'] else 0
            address_confidence = results['address_result'].get('confidence', 0) if results['address_result'].get('success') else 0
            
            if results['name_result'] and results['address_result'].get('success'):
                results['overall_confidence'] = (name_confidence + address_confidence) / 2
            elif results['name_result']:
                results['overall_confidence'] = name_confidence * 0.5  # Reduce confidence if address unavailable
            else:
                results['overall_confidence'] = 0
            
        except Exception as e:
            error_msg = f"Single validation error: {str(e)}"
            results['errors'].append(error_msg)
            self.debug_callback(f"❌ {error_msg}", "VALIDATION")
        
        results['processing_time_ms'] = int((time.time() - start_time) * 1000)
        self.debug_callback(f"✅ Single validation completed ({results['processing_time_ms']}ms)", "VALIDATION")
        
        return results