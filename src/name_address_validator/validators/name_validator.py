# src/name_address_validator/validators/name_validator.py
"""
Simplified Name Validator
"""

import time
from typing import Dict, List
import pandas as pd

# Try to import dictionary loader from utils
try:
    from ..utils.dictionary_loader import NameDictionaryLoader
    DICT_AVAILABLE = True
except ImportError:
    print("Warning: Could not import NameDictionaryLoader")
    NameDictionaryLoader = None
    DICT_AVAILABLE = False


class EnhancedNameValidator:
    """Simple name validator"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries", debug_callback=None):
        self.debug_callback = debug_callback
        
        # Try to load dictionaries
        self.dictionaries_loaded = False
        if DICT_AVAILABLE and NameDictionaryLoader:
            try:
                self.dictionary_loader = NameDictionaryLoader(dictionary_path, debug_callback)
                self.dictionaries_loaded = self.dictionary_loader.load_dictionaries()
                print(f"[VALIDATOR] Dictionaries loaded: {self.dictionaries_loaded}")
            except Exception as e:
                print(f"[VALIDATOR] Dictionary loading failed: {e}")
                self.dictionary_loader = None
        else:
            self.dictionary_loader = None
            
        print(f"[VALIDATOR] Name Validator initialized")
    
    def validate(self, first_name: str, last_name: str) -> Dict:
        """Simple validation"""
        start_time = time.time()
        
        result = {
            'valid': False,
            'confidence': 0.0,
            'errors': [],
            'warnings': [],
            'suggestions': {},
            'normalized': {
                'first_name': first_name.strip().title() if first_name else '',
                'last_name': last_name.strip().title() if last_name else ''
            }
        }
        
        # Basic validation
        if not first_name or not first_name.strip():
            result['errors'].append("First name required")
        if not last_name or not last_name.strip():
            result['errors'].append("Last name required")
        
        # Set validity and confidence
        result['valid'] = len(result['errors']) == 0
        result['confidence'] = 0.8 if result['valid'] else 0.0
        
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    def get_validator_status(self) -> Dict:
        """Get status"""
        return {
            'dictionaries_loaded': self.dictionaries_loaded,
            'dict_available': DICT_AVAILABLE
        }