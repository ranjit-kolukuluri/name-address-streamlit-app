# src/name_address_validator/utils/dictionary_loader.py
"""
Dictionary Loader - Clean and Simple
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Set

try:
    from fuzzywuzzy import process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False


class NameDictionaryLoader:
    """Simple dictionary loader"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries", debug_callback=None):
        self.dictionary_path = Path(dictionary_path)
        self.debug_callback = debug_callback
        
        # Simple storage
        self.first_names: Set[str] = set()
        self.last_names: Set[str] = set()
        self.male_names: Set[str] = set()
        self.female_names: Set[str] = set()
        
        self.loaded = False
        print(f"[DICT] Dictionary loader initialized with path: {dictionary_path}")
    
    def load_dictionaries(self) -> bool:
        """Load dictionaries quickly"""
        try:
            if not self.dictionary_path.exists():
                print(f"[DICT] Dictionary path not found: {self.dictionary_path}")
                return False
            
            csv_files = list(self.dictionary_path.glob("*.csv"))
            if not csv_files:
                print(f"[DICT] No CSV files found in {self.dictionary_path}")
                return False
            
            print(f"[DICT] Found {len(csv_files)} CSV files")
            
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    print(f"[DICT] Loading {csv_file.name}: {len(df)} rows")
                    
                    # Get first column as names
                    names = df.iloc[:, 0].dropna().astype(str).str.strip().str.lower()
                    valid_names = {name for name in names if self._is_valid_name(name)}
                    
                    # Add to appropriate set based on filename
                    filename = csv_file.name.lower()
                    if 'first' in filename:
                        self.first_names.update(valid_names)
                    elif 'last' in filename:
                        self.last_names.update(valid_names)
                    else:
                        # Add to both if unclear
                        self.first_names.update(valid_names)
                        self.last_names.update(valid_names)
                    
                except Exception as e:
                    print(f"[DICT] Error loading {csv_file.name}: {e}")
            
            self.loaded = len(self.first_names) > 0 or len(self.last_names) > 0
            print(f"[DICT] Loaded {len(self.first_names)} first names, {len(self.last_names)} last names")
            return self.loaded
            
        except Exception as e:
            print(f"[DICT] Load error: {e}")
            return False
    
    def _is_valid_name(self, name: str) -> bool:
        """Quick name validation"""
        return (name and len(name) > 1 and name != 'nan' and 
                re.match(r'^[a-z\-\']+$', name))
    
    def is_valid_first_name(self, name: str) -> bool:
        """Check first name"""
        if not self.loaded:
            return True  # Don't reject if no dictionaries loaded
        return name.strip().lower() in self.first_names
    
    def is_valid_last_name(self, name: str) -> bool:
        """Check last name"""
        if not self.loaded:
            return True  # Don't reject if no dictionaries loaded
        return name.strip().lower() in self.last_names
    
    def predict_gender(self, first_name: str) -> str:
        """Predict gender from name"""
        if not first_name or not self.loaded:
            return ''
        
        name_clean = first_name.strip().lower()
        
        if name_clean in self.male_names:
            return 'M'
        elif name_clean in self.female_names:
            return 'F'
        
        # Simple heuristic
        if name_clean.endswith(('a', 'ia', 'ana', 'ella')):
            return 'F'
        elif name_clean.endswith(('er', 'on', 'an')):
            return 'M'
        
        return ''
    
    def is_organization_name(self, full_name: str) -> bool:
        """Quick organization detection"""
        if not full_name:
            return False
        
        name_lower = full_name.lower()
        org_indicators = ['llc', 'inc', 'corp', 'company', 'trust', 'bank', 'hospital', 'pediatrics']
        return any(indicator in name_lower for indicator in org_indicators)