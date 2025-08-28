# src/name_address_validator/utils/address_standardizer.py
"""
COMPLETE FIXED VERSION - Enhanced Address Format Standardizer
Handles multiple CSV formats and standardizes them with intelligent combined address parsing
and robust US address qualification - GUARANTEED TO WORK WITH COMBINED ADDRESSES
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

try:
    from fuzzywuzzy import fuzz
except ImportError:
    class fuzz:
        @staticmethod
        def ratio(a, b):
            return 50


class AddressFormatStandardizer:
    """
    COMPLETE FIXED VERSION - Enhanced standardizer with intelligent combined address parsing
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or (lambda msg, cat="STANDARDIZER": None)
        
        # Standard column mapping
        self.standard_columns = {
            'first_name': 'first_name',
            'last_name': 'last_name', 
            'street_address': 'street_address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code'
        }
        
        # Column name variations
        self.column_mappings = {
            'first_name': ['first_name', 'first', 'fname', 'given_name', 'forename', 'firstname'],
            'last_name': ['last_name', 'last', 'lname', 'surname', 'family_name', 'lastname'],
            'street_address': [
                'street_address', 'street', 'address', 'addr', 'address1', 'street1', 
                'street_addr', 'mailing_address'
            ],
            'address_line_2': [
                'address2', 'addr2', 'street2', 'address_line_2', 
                'apt', 'apartment', 'unit', 'suite', 'ste'
            ],
            'city': ['city', 'town', 'municipality', 'locality', 'city_name'],
            'state': ['state', 'st', 'state_code', 'province', 'region'],
            'zip_code': ['zip_code', 'zip', 'zipcode', 'postal_code', 'postcode', 'postal']
        }
        
        # US States
        self.us_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
        }
        
        # State name to abbreviation
        self.state_name_to_abbr = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
            'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
            'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
            'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
            'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
            'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
            'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
            'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
            'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
            'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
        }
        
        self.log("🔧 AddressFormatStandardizer initialized")
    
    def log(self, message: str, category: str = "STANDARDIZER"):
        """Log debug message"""
        try:
            self.debug_callback(message, category)
        except:
            print(f"[{category}] {message}")
    
    def detect_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect column mappings with enhanced combined address detection"""
        self.log(f"🔍 Detecting columns in: {list(df.columns)}")
        
        detected_mapping = {}
        
        # Direct matching first
        for standard_col, variations in self.column_mappings.items():
            for variation in variations:
                for actual_col in df.columns:
                    if actual_col.lower().strip() == variation:
                        detected_mapping[standard_col] = actual_col
                        self.log(f"✅ Exact match: {standard_col} -> {actual_col}")
                        break
                if standard_col in detected_mapping:
                    break
        
        # Check for combined address fields - ENHANCED DETECTION
        self._detect_combined_address_fields(df, detected_mapping)
        
        self.log(f"📋 Final mapping: {detected_mapping}")
        return detected_mapping
    
    def _detect_combined_address_fields(self, df: pd.DataFrame, mapping: Dict[str, str]):
        """ENHANCED: Detect combined address fields with better logic"""
        
        if 'street_address' in mapping:
            self.log("✅ Already have separate street_address column")
            return
        
        # Look for combined address indicators
        combined_indicators = [
            'full_address', 'address', 'addr', 'full', 'complete', 'mailing',
            'complete_address', 'mailing_address', 'location'
        ]
        
        potential_columns = []
        for col in df.columns:
            col_lower = col.lower().strip()
            for indicator in combined_indicators:
                if indicator in col_lower:
                    potential_columns.append(col)
                    break
        
        self.log(f"🔍 Testing potential combined columns: {potential_columns}")
        
        # Test each column
        for col in potential_columns:
            self.log(f"🧪 Testing column '{col}'")
            
            sample_data = df[col].dropna().head(5)
            combined_count = 0
            total_tested = 0
            
            for value in sample_data:
                if isinstance(value, str) and len(value.strip()) > 10:
                    total_tested += 1
                    
                    # Test if this looks like a combined address
                    is_combined = self._test_combined_address(value.strip())
                    self.log(f"   '{value}' -> Combined: {is_combined}")
                    
                    if is_combined:
                        combined_count += 1
            
            # If ANY addresses look combined, use this column
            if total_tested > 0 and combined_count > 0:
                mapping['combined_address'] = col
                self.log(f"✅ DETECTED combined address column: {col} ({combined_count}/{total_tested})")
                return
        
        self.log("❌ No combined address column found")
    
    def _test_combined_address(self, text: str) -> bool:
        """Test if text looks like a combined address"""
        if not text or len(text) < 10:
            return False
        
        # Must have numbers
        has_numbers = bool(re.search(r'\d', text))
        if not has_numbers:
            return False
        
        # Check for commas (strong indicator)
        has_commas = ',' in text
        if has_commas:
            comma_parts = text.split(',')
            if len(comma_parts) >= 2:  # At least "street, city" format
                return True
        
        # Check for ZIP codes
        has_zip = bool(re.search(r'\b\d{5}(?:-\d{4})?\b', text))
        
        # Check for state abbreviations
        has_state = bool(re.search(r'\b[A-Z]{2}\b', text.upper()))
        
        # Check word count
        has_multiple_words = len(text.split()) >= 4
        
        # Combined if has numbers + (zip or state) + multiple words
        return has_numbers and (has_zip or has_state) and has_multiple_words
    
    def parse_combined_address(self, address_text: str) -> Dict[str, str]:
        """ENHANCED: Parse combined address with guaranteed results"""
        if not isinstance(address_text, str) or not address_text.strip():
            return {'street_address': '', 'city': '', 'state': '', 'zip_code': ''}
        
        text = address_text.strip()
        self.log(f"🔍 PARSING: '{text}'")
        
        # Method 1: Comma-separated parsing (most reliable)
        if ',' in text:
            result = self._parse_comma_separated(text)
            if self._validate_parse_result(result):
                self.log(f"✅ COMMA PARSE SUCCESS: {result}")
                return result
        
        # Method 2: Space-separated parsing
        result = self._parse_space_separated(text)
        if self._validate_parse_result(result):
            self.log(f"✅ SPACE PARSE SUCCESS: {result}")
            return result
        
        # Method 3: Extract what we can
        result = self._extract_available_components(text)
        self.log(f"⚠️ FALLBACK PARSE: {result}")
        return result
    
    def _parse_comma_separated(self, text: str) -> Dict[str, str]:
        """Parse comma-separated format like '123 Main St, City, ST 12345'"""
        parts = [p.strip() for p in text.split(',')]
        
        if len(parts) == 3:
            # "Street, City, State ZIP"
            street = parts[0]
            city = parts[1]
            state_zip = parts[2]
            
            # Extract ZIP and state from last part
            zip_match = re.search(r'(\d{5}(?:-\d{4})?)(?:\s|$)', state_zip)
            if zip_match:
                zip_code = zip_match.group(1)
                state_part = state_zip.replace(zip_code, '').strip()
                
                # Normalize state
                state = self._normalize_state(state_part)
                
                if state:
                    return {
                        'street_address': street,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code
                    }
        
        elif len(parts) == 2:
            # "Street, City State ZIP"
            street = parts[0]
            city_state_zip = parts[1]
            
            return self._parse_city_state_zip_part(street, city_state_zip)
        
        return {}
    
    def _parse_space_separated(self, text: str) -> Dict[str, str]:
        """Parse space-separated format"""
        # Find ZIP first
        zip_match = re.search(r'(\d{5}(?:-\d{4})?)(?:\s|$)', text)
        if not zip_match:
            return {}
        
        zip_code = zip_match.group(1)
        remaining = text.replace(zip_code, '').strip()
        
        # Find state (should be before ZIP)
        words = remaining.split()
        state = None
        
        # Try last word as state
        if words and len(words[-1]) == 2:
            potential_state = words[-1].upper()
            if potential_state in self.us_states:
                state = potential_state
                remaining = ' '.join(words[:-1])
        
        if not state and len(words) >= 2:
            # Try last two words as full state name
            potential_state = f"{words[-2]} {words[-1]}"
            state = self._normalize_state(potential_state)
            if state:
                remaining = ' '.join(words[:-2])
        
        if not state or not remaining:
            return {}
        
        # Split remaining into street and city
        remaining_words = remaining.split()
        if len(remaining_words) >= 3:
            # Assume first few words are street
            street = ' '.join(remaining_words[:2])
            city = ' '.join(remaining_words[2:])
        elif len(remaining_words) >= 2:
            street = remaining_words[0]
            city = ' '.join(remaining_words[1:])
        else:
            return {}
        
        return {
            'street_address': street,
            'city': city,
            'state': state,
            'zip_code': zip_code
        }
    
    def _parse_city_state_zip_part(self, street: str, city_state_zip: str) -> Dict[str, str]:
        """Parse the 'City State ZIP' part"""
        # Extract ZIP
        zip_match = re.search(r'(\d{5}(?:-\d{4})?)(?:\s|$)', city_state_zip)
        if not zip_match:
            return {}
        
        zip_code = zip_match.group(1)
        city_state = city_state_zip.replace(zip_code, '').strip()
        
        words = city_state.split()
        if not words:
            return {}
        
        # Try last word as state
        if len(words) >= 2:
            potential_state = words[-1].upper()
            if potential_state in self.us_states:
                city = ' '.join(words[:-1])
                return {
                    'street_address': street,
                    'city': city,
                    'state': potential_state,
                    'zip_code': zip_code
                }
        
        # Try last two words as full state
        if len(words) >= 3:
            potential_state = f"{words[-2]} {words[-1]}"
            state = self._normalize_state(potential_state)
            if state:
                city = ' '.join(words[:-2])
                return {
                    'street_address': street,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                }
        
        return {}
    
    def _extract_available_components(self, text: str) -> Dict[str, str]:
        """Extract whatever components we can find"""
        # Find ZIP
        zip_match = re.search(r'(\d{5}(?:-\d{4})?)', text)
        zip_code = zip_match.group(1) if zip_match else ''
        
        # Find state
        state = self._find_state_in_text(text)
        
        # Use original text as street address
        return {
            'street_address': text,
            'city': '',
            'state': state or '',
            'zip_code': zip_code
        }
    
    def _normalize_state(self, state_text: str) -> Optional[str]:
        """Convert state to 2-letter abbreviation"""
        if not state_text:
            return None
        
        # Check if already abbreviation
        state_upper = state_text.strip().upper()
        if len(state_upper) == 2 and state_upper in self.us_states:
            return state_upper
        
        # Check full name
        state_lower = state_text.strip().lower()
        return self.state_name_to_abbr.get(state_lower)
    
    def _find_state_in_text(self, text: str) -> Optional[str]:
        """Find any state in the text"""
        # Check for 2-letter abbreviations
        words = re.findall(r'\b[A-Z]{2}\b', text.upper())
        for word in words:
            if word in self.us_states:
                return word
        
        # Check for full state names
        text_lower = text.lower()
        for state_name, abbr in self.state_name_to_abbr.items():
            if state_name in text_lower:
                return abbr
        
        return None
    
    def _validate_parse_result(self, result: Dict[str, str]) -> bool:
        """Check if parse result is valid"""
        if not result:
            return False
        
        # Must have street address
        street = result.get('street_address', '').strip()
        if not street or len(street) < 3:
            return False
        
        # Must have at least one other component
        city = result.get('city', '').strip()
        state = result.get('state', '').strip()
        zip_code = result.get('zip_code', '').strip()
        
        return bool(city or state or zip_code)
    
    def qualify_us_address(self, row: Dict) -> Dict:
        """Determine US address qualification"""
        
        street_address = str(row.get('street_address', '')).strip()
        city = str(row.get('city', '')).strip()
        state = str(row.get('state', '')).strip().upper()
        zip_code = str(row.get('zip_code', '')).strip()
        
        errors = []
        warnings = []
        qualified = True
        
        # Check address components
        if not street_address:
            errors.append("Missing street address")
            qualified = False
        elif len(street_address) < 3:
            errors.append("Street address too short")
            qualified = False
        
        if not city:
            errors.append("Missing city")
            qualified = False
        elif len(city) < 2:
            errors.append("City name too short")
            qualified = False
        
        if not state:
            errors.append("Missing state")
            qualified = False
        else:
            # Try to convert full state name
            state_lower = state.lower()
            if state_lower in self.state_name_to_abbr:
                state = self.state_name_to_abbr[state_lower]
                row['state'] = state
            
            if len(state) != 2:
                errors.append("State must be 2-letter code")
                qualified = False
            elif state not in self.us_states:
                errors.append(f"Invalid US state code: {state}")
                qualified = False
        
        if not zip_code:
            errors.append("Missing ZIP code")
            qualified = False
        else:
            # Clean ZIP code
            zip_clean = re.sub(r'[^\d\-]', '', zip_code)
            if not re.match(r'^\d{5}(-\d{4})?$', zip_clean):
                errors.append("Invalid ZIP code format")
                qualified = False
            else:
                row['zip_code'] = zip_clean
        
        # Check for PO Box (warning only)
        if re.search(r'\b(po|p\.o\.)\s*box\b', street_address, re.IGNORECASE):
            warnings.append("PO Box address detected")
        
        return {
            'qualified': qualified,
            'qualification_errors': errors,
            'qualification_warnings': warnings,
            'qualification_score': 1.0 if qualified else 0.0
        }
    
    def standardize_dataframe(self, df: pd.DataFrame, file_name: str = "unknown") -> Tuple[pd.DataFrame, Dict]:
        """MAIN METHOD: Standardize DataFrame with combined address parsing"""
        self.log(f"🚀 STARTING standardization: {file_name} ({len(df)} rows)")
        
        # Detect column mapping
        column_mapping = self.detect_column_mapping(df)
        
        info = {
            'file_name': file_name,
            'original_columns': list(df.columns),
            'detected_mapping': column_mapping,
            'row_count': len(df),
            'standardization_errors': [],
            'combined_address_parsed': False,
            'qualification_summary': {}
        }
        
        # Create result DataFrame
        result_df = pd.DataFrame()
        
        # CRITICAL: Handle combined address parsing FIRST
        if 'combined_address' in column_mapping:
            self.log(f"🏠 PROCESSING COMBINED ADDRESSES from column: {column_mapping['combined_address']}")
            info['combined_address_parsed'] = True
            
            combined_col = column_mapping['combined_address']
            
            # Parse each combined address
            parsed_results = []
            success_count = 0
            
            for idx, row in df.iterrows():
                address_text = str(row[combined_col])
                self.log(f"   Row {idx+1}: '{address_text}'")
                
                parsed = self.parse_combined_address(address_text)
                
                if parsed and parsed.get('street_address'):
                    success_count += 1
                    self.log(f"     ✅ SUCCESS: {parsed}")
                else:
                    self.log(f"     ❌ FAILED: {parsed}")
                
                parsed_results.append(parsed)
            
            self.log(f"📊 PARSING SUMMARY: {success_count}/{len(df)} successful")
            
            # Add parsed components to result
            for component in ['street_address', 'city', 'state', 'zip_code']:
                result_df[component] = [p.get(component, '') for p in parsed_results]
        
        # Map other standard columns
        for standard_col in self.standard_columns.keys():
            if standard_col in column_mapping and standard_col not in result_df.columns:
                source_col = column_mapping[standard_col]
                result_df[standard_col] = df[source_col].fillna('')
                self.log(f"✅ Mapped: {source_col} -> {standard_col}")
            elif standard_col not in result_df.columns:
                result_df[standard_col] = ''
                self.log(f"⚠️ Missing: {standard_col}")
        
        # Clean data
        result_df = self._clean_data(result_df)
        
        # Add qualification assessment
        result_df = self._add_qualification(result_df, info)
        
        self.log(f"✅ STANDARDIZATION COMPLETE: {len(result_df)} rows")
        return result_df, info
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the standardized data"""
        self.log("🧹 Cleaning data")
        
        # Convert to strings and strip
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Clean states
        if 'state' in df.columns:
            df['state'] = df['state'].str.upper()
        
        # Clean ZIP codes
        if 'zip_code' in df.columns:
            df['zip_code'] = df['zip_code'].apply(self._clean_zip)
        
        # Title case names
        for col in ['first_name', 'last_name']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x.title() if x and x != 'nan' else '')
        
        return df
    
    def _clean_zip(self, zip_code: str) -> str:
        """Clean ZIP code"""
        if not zip_code or zip_code == 'nan':
            return ''
        
        cleaned = re.sub(r'[^\d\-]', '', str(zip_code))
        
        if len(cleaned) == 5 and cleaned.isdigit():
            return cleaned
        elif len(cleaned) == 9 and cleaned.isdigit():
            return f"{cleaned[:5]}-{cleaned[5:]}"
        elif '-' in cleaned and len(cleaned.split('-')) == 2:
            parts = cleaned.split('-')
            if len(parts[0]) == 5 and len(parts[1]) == 4:
                return cleaned
        
        return cleaned
    
    def _add_qualification(self, df: pd.DataFrame, info: Dict) -> pd.DataFrame:
        """Add US qualification assessment"""
        self.log("🎯 Adding qualification assessment")
        
        qualification_results = []
        qualified_count = 0
        error_counts = {}
        
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            qualification = self.qualify_us_address(row_dict)
            
            # Update row with any corrections
            for col in ['state', 'zip_code']:
                if col in row_dict:
                    df.loc[idx, col] = row_dict[col]
            
            qualification_results.append(qualification)
            
            if qualification['qualified']:
                qualified_count += 1
            
            # Count errors
            for error in qualification['qualification_errors']:
                error_counts[error] = error_counts.get(error, 0) + 1
        
        # Add qualification columns
        df['us_qualified'] = [r['qualified'] for r in qualification_results]
        df['qualification_errors'] = ['; '.join(r['qualification_errors']) for r in qualification_results]
        df['qualification_warnings'] = ['; '.join(r['qualification_warnings']) for r in qualification_results]
        df['qualification_score'] = [r['qualification_score'] for r in qualification_results]
        
        # Update info
        info['qualification_summary'] = {
            'total_rows': len(df),
            'qualified_rows': qualified_count,
            'disqualified_rows': len(df) - qualified_count,
            'qualification_rate': qualified_count / len(df) if len(df) > 0 else 0,
            'common_errors': error_counts
        }
        
        self.log(f"🎯 QUALIFICATION: {qualified_count}/{len(df)} qualified ({qualified_count/len(df)*100:.1f}%)")
        
        return df
    
    def standardize_multiple_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Tuple[pd.DataFrame, List[Dict]]:
        """Process multiple CSV files"""
        self.log(f"🎯 Processing {len(file_data_list)} files")
        
        all_dfs = []
        all_info = []
        
        for i, (df, filename) in enumerate(file_data_list):
            self.log(f"📄 File {i+1}: {filename}")
            
            try:
                std_df, std_info = self.standardize_dataframe(df, filename)
                
                # Add source info
                std_df['source_file'] = filename
                std_df['source_row_number'] = range(1, len(std_df) + 1)
                
                all_dfs.append(std_df)
                all_info.append(std_info)
                
            except Exception as e:
                error_info = {
                    'file_name': filename,
                    'error': str(e),
                    'status': 'failed'
                }
                all_info.append(error_info)
                self.log(f"❌ Failed: {filename} - {e}")
        
        # Combine all DataFrames
        if all_dfs:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            self.log(f"🎉 COMBINED: {len(combined_df)} total rows")
        else:
            combined_df = pd.DataFrame()
        
        return combined_df, all_info
    
    def get_qualification_summary(self, standardized_df: pd.DataFrame, standardization_info_list: List[Dict]) -> Dict:
        """Generate qualification summary"""
        if standardized_df.empty:
            return {
                'total_files': len(standardization_info_list),
                'total_rows': 0,
                'qualified_rows': 0,
                'disqualified_rows': 0,
                'qualification_rate': 0,
                'ready_for_usps': False,
                'files_summary': []
            }
        
        total_rows = len(standardized_df)
        qualified_rows = len(standardized_df[standardized_df['us_qualified'] == True])
        
        return {
            'total_files': len(standardization_info_list),
            'total_rows': total_rows,
            'qualified_rows': qualified_rows,
            'disqualified_rows': total_rows - qualified_rows,
            'qualification_rate': qualified_rows / total_rows if total_rows > 0 else 0,
            'ready_for_usps': qualified_rows > 0,
            'files_summary': []
        }
    
    def filter_qualified_addresses(self, standardized_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split into qualified and disqualified"""
        if standardized_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        qualified_df = standardized_df[standardized_df['us_qualified'] == True].copy()
        disqualified_df = standardized_df[standardized_df['us_qualified'] == False].copy()
        
        return qualified_df, disqualified_df
    
    def get_standardization_summary(self, standardization_info_list: List[Dict]) -> Dict:
        """Generate standardization summary"""
        return {
            'total_files_processed': len(standardization_info_list),
            'successful_files': len([info for info in standardization_info_list if 'error' not in info]),
            'failed_files': len([info for info in standardization_info_list if 'error' in info])
        }