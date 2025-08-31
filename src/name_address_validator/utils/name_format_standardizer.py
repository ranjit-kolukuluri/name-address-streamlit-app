# src/name_address_validator/utils/name_format_standardizer.py
"""
Simplified Name Format Standardizer
"""

import pandas as pd
import re
from typing import Dict, List, Tuple

# Import from same directory
try:
    from .dictionary_loader import NameDictionaryLoader
except ImportError:
    print("Warning: Could not import NameDictionaryLoader")
    NameDictionaryLoader = None

try:
    from nameparser import HumanName
    NAMEPARSER_AVAILABLE = True
except ImportError:
    NAMEPARSER_AVAILABLE = False


class NameFormatStandardizer:
    """Simplified name standardizer"""
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries", debug_callback=None):
        self.debug_callback = debug_callback
        
        # Load dictionaries if available
        self.dictionaries_loaded = False
        if NameDictionaryLoader:
            try:
                self.dictionary_loader = NameDictionaryLoader(dictionary_path, debug_callback)
                self.dictionaries_loaded = self.dictionary_loader.load_dictionaries()
                print(f"[STANDARDIZER] Dictionaries loaded: {self.dictionaries_loaded}")
            except Exception as e:
                print(f"[STANDARDIZER] Dictionary loading failed: {e}")
                self.dictionary_loader = None
        else:
            self.dictionary_loader = None
    
    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect column mappings"""
        print(f"[STANDARDIZER] Detecting columns in: {list(df.columns)}")
        
        # Clean column names and create mapping
        columns_clean = {}
        for col in df.columns:
            clean_col = str(col).lower().strip().replace(' ', '')
            columns_clean[clean_col] = col
            print(f"[STANDARDIZER] Column mapping: '{col}' -> '{clean_col}'")
        
        detected = {}
        
        # Map columns
        mappings = {
            'id': ['uniqueid', 'unique_id', 'id', 'identifier'],
            'name': ['name', 'full_name', 'fullname'],
            'gender': ['gender', 'sex'],
            'party_type': ['partytype', 'party_type', 'type'],
            'parse_ind': ['parseind', 'parse_ind']
        }
        
        for std_col, variations in mappings.items():
            for var in variations:
                if var in columns_clean:
                    detected[std_col] = columns_clean[var]
                    print(f"[STANDARDIZER] ✅ Found {std_col}: {var} -> {columns_clean[var]}")
                    break
        
        print(f"[STANDARDIZER] Final detected columns: {detected}")
        return detected
    
    def parse_name_simple(self, full_name: str) -> Dict[str, str]:
        """Simple name parsing"""
        if not full_name or str(full_name).strip() in ['', 'nan', 'None']:
            return {'first_name': '', 'last_name': '', 'middle_name': ''}
        
        name = str(full_name).strip()
        words = name.split()
        
        if len(words) == 0:
            return {'first_name': '', 'last_name': '', 'middle_name': ''}
        elif len(words) == 1:
            return {'first_name': words[0], 'last_name': '', 'middle_name': ''}
        elif len(words) == 2:
            return {'first_name': words[0], 'last_name': words[1], 'middle_name': ''}
        else:
            return {
                'first_name': words[0],
                'last_name': words[-1],
                'middle_name': ' '.join(words[1:-1])
            }
    
    def is_organization_simple(self, name: str) -> bool:
        """Simple organization detection"""
        if not name:
            return False
        
        name_lower = name.lower()
        org_words = ['llc', 'inc', 'corp', 'company', 'trust', 'bank', 'hospital', 'clinic', 'pediatrics']
        return any(word in name_lower for word in org_words)
    
    def process_record(self, row: pd.Series, column_mapping: Dict[str, str], row_num: int) -> Dict:
        """Process single record"""
        print(f"[STANDARDIZER] Processing row {row_num}")
        
        # Extract values safely
        record_id = row.get(column_mapping.get('id'), f"row_{row_num}")
        full_name = str(row.get(column_mapping.get('name', ''), '')).strip()
        
        print(f"[STANDARDIZER] Row {row_num}: ID='{record_id}', Name='{full_name}'")
        
        result = {
            'id': record_id,
            'original_name': full_name,
            'first_name': '',
            'last_name': '',
            'middle_name': '',
            'gender': '',
            'party_type': '',
            'is_organization': False,
            'processing_successful': False
        }
        
        if not full_name or full_name in ['nan', 'None', '']:
            print(f"[STANDARDIZER] Row {row_num}: Empty name")
            return result
        
        # Check if organization
        is_org = self.is_organization_simple(full_name)
        result['is_organization'] = is_org
        
        if is_org:
            print(f"[STANDARDIZER] Row {row_num}: Organization detected")
            result['party_type'] = 'O'
            result['organization_name'] = full_name
            result['processing_successful'] = True
            return result
        
        # Parse individual name
        print(f"[STANDARDIZER] Row {row_num}: Parsing as individual")
        parsed = self.parse_name_simple(full_name)
        result.update(parsed)
        result['party_type'] = 'I'
        
        # Mark successful if we have at least first or last name
        result['processing_successful'] = bool(result['first_name'] or result['last_name'])
        
        print(f"[STANDARDIZER] Row {row_num}: Success={result['processing_successful']}, First='{result['first_name']}', Last='{result['last_name']}'")
        return result
    
    def standardize_dataframe(self, df: pd.DataFrame, file_name: str = "unknown") -> Tuple[pd.DataFrame, Dict]:
        """Process DataFrame"""
        print(f"[STANDARDIZER] Processing file: {file_name}, Shape: {df.shape}")
        print(f"[STANDARDIZER] Columns: {list(df.columns)}")
        
        # Show first few rows for debugging
        print(f"[STANDARDIZER] First 3 rows:")
        print(df.head(3).to_string())
        
        # Detect columns
        column_mapping = self.detect_columns(df)
        
        if 'name' not in column_mapping:
            error_msg = f"Name column not found in {list(df.columns)}"
            print(f"[STANDARDIZER] ERROR: {error_msg}")
            return pd.DataFrame(), {
                'success': False,
                'error': error_msg,
                'available_columns': list(df.columns)
            }
        
        print(f"[STANDARDIZER] Using name column: {column_mapping['name']}")
        
        # Process records
        processed_records = []
        successful_count = 0
        
        for idx, row in df.iterrows():
            try:
                result = self.process_record(row, column_mapping, idx + 1)
                processed_records.append(result)
                if result['processing_successful']:
                    successful_count += 1
            except Exception as e:
                print(f"[STANDARDIZER] Error processing row {idx + 1}: {e}")
                import traceback
                print(traceback.format_exc())
        
        print(f"[STANDARDIZER] Processed {successful_count}/{len(df)} records successfully")
        
        if not processed_records:
            return pd.DataFrame(), {
                'success': False,
                'error': 'No records could be processed'
            }
        
        # Create result DataFrame
        result_df = pd.DataFrame(processed_records)
        result_df['source_file'] = file_name
        
        print(f"[STANDARDIZER] Result DataFrame shape: {result_df.shape}")
        print(f"[STANDARDIZER] Result columns: {list(result_df.columns)}")
        
        info = {
            'success': successful_count > 0,
            'file_name': file_name,
            'total_records': len(df),
            'successful_records': successful_count,
            'columns_detected': column_mapping
        }
        
        return result_df, info
    
    def standardize_multiple_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Tuple[pd.DataFrame, List[Dict]]:
        """Process multiple files"""
        print(f"[STANDARDIZER] Processing {len(file_data_list)} files")
        
        all_dfs = []
        all_info = []
        
        for i, (df, filename) in enumerate(file_data_list):
            print(f"[STANDARDIZER] === Processing file {i+1}: {filename} ===")
            result_df, info = self.standardize_dataframe(df, filename)
            
            if not result_df.empty and info.get('successful_records', 0) > 0:
                all_dfs.append(result_df)
                print(f"[STANDARDIZER] File {i+1} added: {len(result_df)} records")
            else:
                print(f"[STANDARDIZER] File {i+1} had no successful records")
            
            all_info.append(info)
        
        if all_dfs:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            print(f"[STANDARDIZER] ✅ Combined result: {len(combined_df)} records")
            return combined_df, all_info
        else:
            print(f"[STANDARDIZER] ❌ No successful data from any file")
            return pd.DataFrame(), all_info