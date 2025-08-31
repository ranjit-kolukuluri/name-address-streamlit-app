# src/name_address_validator/services/validation_service.py
"""
Fixed Validation Service
"""

import time
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..validators.name_validator import EnhancedNameValidator
from ..validators.address_validator import USPSAddressValidator
from ..utils.config import load_usps_credentials
from ..utils.name_format_standardizer import NameFormatStandardizer


class ValidationService:
    """
    Fixed validation service
    """
    
    def __init__(self, dictionary_path: str = "/Users/t93uyz8/Documents/name_dictionaries", debug_callback=None):
        self.debug_callback = debug_callback or self._default_logger
        self.dictionary_path = dictionary_path
        
        print("[SERVICE] Initializing ValidationService...")
        
        # Initialize validators
        try:
            self.name_validator = EnhancedNameValidator(dictionary_path, debug_callback)
            print("[SERVICE] ✅ Name validator initialized")
        except Exception as e:
            print(f"[SERVICE] ❌ Name validator failed: {e}")
            self.name_validator = None
        
        # Initialize name standardizer
        try:
            self.name_standardizer = NameFormatStandardizer(dictionary_path, debug_callback)
            print("[SERVICE] ✅ Name standardizer initialized")
        except Exception as e:
            print(f"[SERVICE] ❌ Name standardizer failed: {e}")
            self.name_standardizer = None
        
        # Initialize address validator
        self.address_validator = None
        self._initialize_address_validator()
        
        print("[SERVICE] ✅ ValidationService initialization complete")
    
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
                print("[SERVICE] ✅ USPS validator initialized")
            else:
                print("[SERVICE] ⚠️ USPS credentials not available")
        except Exception as e:
            print(f"[SERVICE] ❌ Failed to initialize USPS validator: {str(e)}")
    
    # SERVICE STATUS METHODS
    
    def is_name_validation_available(self) -> bool:
        """Check if name validation is available"""
        available = self.name_validator is not None
        print(f"[SERVICE] Name validation available: {available}")
        return available
    
    def is_address_validation_available(self) -> bool:
        """Check if USPS address validation is available"""
        available = self.address_validator is not None and self.address_validator.is_configured()
        print(f"[SERVICE] Address validation available: {available}")
        return available
    
    def get_service_status(self) -> Dict:
        """Get comprehensive service status"""
        status = {
            'name_validation_available': self.is_name_validation_available(),
            'address_validation_available': self.is_address_validation_available(),
            'usps_configured': self.address_validator is not None,
            'timestamp': datetime.now().isoformat()
        }
        print(f"[SERVICE] Service status: {status}")
        return status
    
    # SINGLE RECORD VALIDATION
    
    def validate_single_record(self, first_name: str, last_name: str, 
                              street_address: str, city: str, state: str, zip_code: str) -> Dict:
        """Validate a single complete record (name + address)"""
        print(f"[SERVICE] Single record validation: {first_name} {last_name}")
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
                print(f"[SERVICE] Name validation result: {name_result.get('valid', False)}")
            else:
                results['errors'].append("Name validation service unavailable")
                print("[SERVICE] ❌ Name validation unavailable")
            
            # Validate address (if provided)
            if street_address and city and state and zip_code:
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
            address_deliverable = results['address_result'].get('deliverable', True) if results['address_result'] else True
            
            results['overall_valid'] = name_valid and address_deliverable
            
            # Calculate confidence
            name_confidence = results['name_result'].get('confidence', 0) if results['name_result'] else 0
            results['overall_confidence'] = name_confidence
            
        except Exception as e:
            error_msg = f"Single validation error: {str(e)}"
            results['errors'].append(error_msg)
            print(f"[SERVICE] ❌ {error_msg}")
        
        results['processing_time_ms'] = int((time.time() - start_time) * 1000)
        print(f"[SERVICE] ✅ Single validation completed ({results['processing_time_ms']}ms)")
        
        return results
    
    # NAME PROCESSING METHODS - FIXED
    
    def standardize_and_parse_names_from_csv(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """Standardize and parse names from CSV files - FIXED VERSION"""
        print(f"[SERVICE] 🔄 Starting name standardization for {len(file_data_list)} files")
        start_time = time.time()
        
        try:
            if not self.name_standardizer:
                print("[SERVICE] ❌ Name standardizer not available")
                return {
                    'success': False,
                    'error': 'Name standardizer not initialized',
                    'standardized_data': pd.DataFrame()
                }
            
            # Use name format standardizer
            print("[SERVICE] 📋 Calling name standardizer...")
            standardized_df, standardization_info = self.name_standardizer.standardize_multiple_files(file_data_list)
            
            print(f"[SERVICE] 📊 Standardizer returned: {len(standardized_df)} rows")
            print(f"[SERVICE] 📊 Standardizer info: {len(standardization_info)} file info records")
            
            # Check if we got any data
            if standardized_df.empty:
                print("[SERVICE] ❌ No data returned from standardizer")
                # Print detailed info about what went wrong
                for info in standardization_info:
                    print(f"[SERVICE] File info: {info}")
                
                return {
                    'success': False,
                    'error': 'No valid names found after standardization',
                    'standardized_data': standardized_df,
                    'standardization_info': standardization_info
                }
            
            # Check successful records
            successful_records = 0
            if 'processing_successful' in standardized_df.columns:
                successful_records = standardized_df['processing_successful'].sum()
            else:
                # Fallback: count records with names
                successful_records = len(standardized_df[
                    (standardized_df.get('first_name', '') != '') | 
                    (standardized_df.get('last_name', '') != '') |
                    (standardized_df.get('is_organization', False) == True)
                ])
            
            print(f"[SERVICE] 📊 Found {successful_records} successful records out of {len(standardized_df)}")
            
            duration = int((time.time() - start_time) * 1000)
            
            result = {
                'success': successful_records > 0,
                'standardized_data': standardized_df,
                'standardization_info': standardization_info,
                'processing_time_ms': duration,
                'successful_records': successful_records,
                'total_records': len(standardized_df)
            }
            
            if successful_records == 0:
                result['error'] = f'No valid names found in uploaded files. Processed {len(standardized_df)} records but none were successful.'
            
            print(f"[SERVICE] ✅ Name standardization result: success={result['success']}, records={successful_records}")
            
            return result
            
        except Exception as e:
            error_msg = f"Name standardization failed: {str(e)}"
            print(f"[SERVICE] ❌ {error_msg}")
            import traceback
            print(f"[SERVICE] Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': error_msg,
                'standardized_data': pd.DataFrame(),
                'standardization_info': []
            }
    
    def generate_name_validation_preview(self, standardization_result: Dict) -> Dict:
        """Generate preview of name validation results - FIXED"""
        print("[SERVICE] 🔍 Generating name validation preview")
        
        if not standardization_result.get('success'):
            error = standardization_result.get('error', 'Standardization failed')
            print(f"[SERVICE] ❌ Preview failed - standardization error: {error}")
            return {
                'success': False,
                'error': error
            }
        
        try:
            standardized_df = standardization_result['standardized_data']
            
            if standardized_df.empty:
                print("[SERVICE] ❌ Preview failed - no standardized data")
                return {
                    'success': False,
                    'error': 'No standardized data available'
                }
            
            print(f"[SERVICE] 📊 Generating preview for {len(standardized_df)} records")
            
            total_records = len(standardized_df)
            
            # Count valid records
            valid_records = 0
            invalid_records = 0
            
            # Check different ways to count valid records
            if 'processing_successful' in standardized_df.columns:
                valid_records = int(standardized_df['processing_successful'].sum())
                invalid_records = total_records - valid_records
            else:
                # Fallback counting
                for idx, row in standardized_df.iterrows():
                    has_name = bool(row.get('first_name', '') or row.get('last_name', '') or row.get('is_organization', False))
                    if has_name:
                        valid_records += 1
                    else:
                        invalid_records += 1
            
            print(f"[SERVICE] 📊 Preview stats: {valid_records} valid, {invalid_records} invalid")
            
            # Create sample data for preview
            sample_valid_data = []
            sample_invalid_data = []
            
            for idx, row in standardized_df.head(10).iterrows():
                record = {
                    'original_name': row.get('original_name', ''),
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'is_organization': row.get('is_organization', False),
                    'source_file': row.get('source_file', 'unknown')
                }
                
                is_valid = row.get('processing_successful', False) or bool(record['first_name'] or record['last_name'] or record['is_organization'])
                
                if is_valid:
                    sample_valid_data.append(record)
                else:
                    sample_invalid_data.append(record)
            
            validation_rate = valid_records / total_records if total_records > 0 else 0
            
            result = {
                'success': True,
                'overview': {
                    'total_files': len(standardization_result.get('standardization_info', [])),
                    'total_records': total_records,
                    'valid_names': valid_records,
                    'invalid_names': invalid_records,
                    'validation_rate': validation_rate,
                    'ready_for_validation': valid_records > 0
                },
                'valid_preview': {
                    'count': valid_records,
                    'sample_data': sample_valid_data
                },
                'invalid_preview': {
                    'count': invalid_records,
                    'sample_data': sample_invalid_data
                }
            }
            
            print(f"[SERVICE] ✅ Preview generated successfully: {valid_records}/{total_records} valid records")
            return result
            
        except Exception as e:
            error_msg = f"Preview generation failed: {str(e)}"
            print(f"[SERVICE] ❌ {error_msg}")
            import traceback
            print(f"[SERVICE] Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def process_complete_name_validation_pipeline(self, file_data_list: List[Tuple[pd.DataFrame, str]], 
                                                 include_suggestions: bool = True, 
                                                 max_records: Optional[int] = None) -> Dict:
        """Complete name validation pipeline - FIXED"""
        print(f"[SERVICE] 🚀 Starting complete name validation pipeline")
        start_time = time.time()
        
        try:
            # Step 1: Standardize and parse names
            print("[SERVICE] 📋 Step 1: Standardizing names...")
            standardization_result = self.standardize_and_parse_names_from_csv(file_data_list)
            
            if not standardization_result['success']:
                print(f"[SERVICE] ❌ Step 1 failed: {standardization_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': f"Standardization failed: {standardization_result.get('error', 'Unknown error')}"
                }
            
            standardized_df = standardization_result['standardized_data']
            
            if standardized_df.empty:
                print("[SERVICE] ❌ Step 1 produced no data")
                return {
                    'success': False,
                    'error': 'No valid names found after standardization'
                }
            
            print(f"[SERVICE] ✅ Step 1 complete: {len(standardized_df)} records")
            
            # Step 2: Limit records if specified
            if max_records and len(standardized_df) > max_records:
                standardized_df = standardized_df.head(max_records)
                print(f"[SERVICE] ⚠️ Limited to {max_records} records")
            
            # Step 3: Create validation records
            validation_results = []
            successful_validations = 0
            failed_validations = 0
            
            print(f"[SERVICE] 📋 Step 3: Creating validation results for {len(standardized_df)} records")
            
            for idx, row in standardized_df.iterrows():
                try:
                    result_record = {
                        'source_file': row.get('source_file', 'unknown'),
                        'record_id': row.get('id', idx + 1),
                        'original_name': row.get('original_name', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'middle_name': row.get('middle_name', ''),
                        'gender': row.get('gender', ''),
                        'party_type': row.get('party_type', ''),
                        'is_organization': row.get('is_organization', False),
                        'processing_successful': row.get('processing_successful', False)
                    }
                    
                    # Add organization name if applicable
                    if row.get('is_organization', False):
                        result_record['organization_name'] = row.get('organization_name', row.get('original_name', ''))
                    
                    validation_results.append(result_record)
                    
                    if result_record['processing_successful']:
                        successful_validations += 1
                    else:
                        failed_validations += 1
                        
                except Exception as e:
                    print(f"[SERVICE] ❌ Error processing record {idx}: {e}")
                    failed_validations += 1
            
            duration = int((time.time() - start_time) * 1000)
            
            validation_success_rate = successful_validations / len(validation_results) if validation_results else 0
            
            result = {
                'success': successful_validations > 0,
                'summary': {
                    'files_processed': len(file_data_list),
                    'validated_names': len(validation_results),
                    'successful_validations': successful_validations,
                    'failed_validations': failed_validations,
                    'validation_success_rate': validation_success_rate
                },
                'validation': {
                    'records': validation_results
                },
                'pipeline_duration_ms': duration
            }
            
            if successful_validations == 0:
                result['error'] = f'No successful validations. Processed {len(validation_results)} records.'
            
            print(f"[SERVICE] ✅ Pipeline complete: {successful_validations}/{len(validation_results)} successful")
            
            return result
            
        except Exception as e:
            error_msg = f"Name validation pipeline failed: {str(e)}"
            print(f"[SERVICE] ❌ {error_msg}")
            import traceback
            print(f"[SERVICE] Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': error_msg
            }
        
def validate_api_records(self, records: List[Dict], include_suggestions: bool = True,
                            detailed_analysis: bool = True, validate_gender: bool = True,
                            validate_party_type: bool = True) -> Dict:
        """
        Validate records from API payload format
        
        Args:
            records: List of records with format:
                {
                    "uniqueid": "string",
                    "name": "string", 
                    "gender": "M|F|",
                    "party_type": "I|O|",
                    "parseInd": "Y|N|"
                }
            include_suggestions: Include name suggestions
            detailed_analysis: Include detailed parsing analysis
            validate_gender: Predict gender from names
            validate_party_type: Predict party type
        
        Returns:
            Dict with validation results in API format
        """
        print(f"[SERVICE] 🚀 API validation for {len(records)} records")
        start_time = time.time()
        
        results = []
        successful_count = 0
        
        try:
            for i, record in enumerate(records):
                print(f"[SERVICE] Processing API record {i+1}: {record.get('uniqueid', 'unknown')}")
                
                try:
                    # Validate record format
                    if not isinstance(record, dict):
                        raise ValueError("Record must be an object")
                    
                    if not record.get('uniqueid'):
                        raise ValueError("uniqueid is required")
                    
                    if not record.get('name'):
                        raise ValueError("name is required")
                    
                    # Process the record
                    result = self._process_api_record(
                        record, include_suggestions, detailed_analysis,
                        validate_gender, validate_party_type
                    )
                    
                    results.append(result)
                    
                    if result['validation_status'] != 'error':
                        successful_count += 1
                        
                except Exception as e:
                    error_result = {
                        'uniqueid': record.get('uniqueid', f'record_{i+1}'),
                        'name': record.get('name', ''),
                        'gender': '',
                        'party_type': '',
                        'parse_indicator': '',
                        'validation_status': 'error',
                        'confidence_score': 0.0,
                        'parsed_components': {},
                        'suggestions': {},
                        'errors': [str(e)],
                        'warnings': []
                    }
                    results.append(error_result)
                    print(f"[SERVICE] ❌ Error processing record {i+1}: {e}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            response = {
                'status': 'success',
                'processed_count': len(results),
                'successful_count': successful_count,
                'results': results,
                'processing_time_ms': duration_ms,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"[SERVICE] ✅ API validation complete: {successful_count}/{len(results)} successful")
            return response
            
        except Exception as e:
            error_msg = f"API validation failed: {str(e)}"
            print(f"[SERVICE] ❌ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'processed_count': 0,
                'successful_count': 0,
                'results': [],
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': datetime.now().isoformat()
            }
        
def _process_api_record(self, record: Dict, include_suggestions: bool,
                           detailed_analysis: bool, validate_gender: bool,
                           validate_party_type: bool) -> Dict:
        """Process a single API record"""
        
        uniqueid = record['uniqueid']
        name = record['name'].strip()
        gender_hint = record.get('gender', '').strip()
        party_type_hint = record.get('party_type', '').strip()
        parse_ind = record.get('parseInd', '').strip()
        
        print(f"[SERVICE] Processing: ID={uniqueid}, Name='{name}', Gender={gender_hint}, Type={party_type_hint}, Parse={parse_ind}")
        
        # Initialize result
        result = {
            'uniqueid': uniqueid,
            'name': name,
            'gender': gender_hint,
            'party_type': party_type_hint,
            'parse_indicator': parse_ind,
            'validation_status': 'valid',
            'confidence_score': 0.0,
            'parsed_components': {},
            'suggestions': {},
            'errors': [],
            'warnings': []
        }
        
        # Determine if organization
        is_org = self._detect_organization_api(name, party_type_hint)
        
        if is_org:
            # Handle organization
            result['party_type'] = 'O'
            result['gender'] = ''
            result['parse_indicator'] = 'N'  # Don't parse organization names
            result['parsed_components'] = {
                'organization_name': name,
                'first_name': '',
                'last_name': '',
                'middle_name': ''
            }
            result['confidence_score'] = 0.9
            print(f"[SERVICE] Detected as organization: {name}")
            
        else:
            # Handle individual name
            result['party_type'] = 'I'
            
            # Parse name if requested
            if parse_ind.upper() == 'Y' or parse_ind == '':
                parsed = self._parse_individual_name_api(name)
                result['parsed_components'] = parsed
                result['parse_indicator'] = 'Y'
                
                print(f"[SERVICE] Parsed name: {parsed}")
                
                # Validate parsed components using existing validator
                if self.is_name_validation_available():
                    first_name = parsed.get('first_name', '')
                    last_name = parsed.get('last_name', '')
                    
                    if first_name or last_name:
                        # Use existing name validator
                        validation_result = self.name_validator.validate(first_name, last_name)
                        
                        if validation_result.get('valid'):
                            result['validation_status'] = 'valid'
                            result['confidence_score'] = validation_result.get('confidence', 0.8)
                        else:
                            result['validation_status'] = 'warning'
                            result['confidence_score'] = 0.4
                            result['warnings'].extend(validation_result.get('errors', []))
                        
                        # Add suggestions from validator
                        if include_suggestions and validation_result.get('suggestions'):
                            result['suggestions'].update(validation_result['suggestions'])
                    else:
                        result['validation_status'] = 'invalid'
                        result['errors'].append('Could not parse name into valid components')
                        result['confidence_score'] = 0.2
                else:
                    # Basic validation without dictionaries
                    if parsed['first_name'] or parsed['last_name']:
                        result['validation_status'] = 'valid'
                        result['confidence_score'] = 0.7
                    else:
                        result['validation_status'] = 'invalid'
                        result['errors'].append('Could not parse name into valid components')
                        result['confidence_score'] = 0.2
                
                # Predict gender if requested
                if validate_gender and not gender_hint and parsed.get('first_name'):
                    predicted_gender = self._predict_gender_api(parsed['first_name'])
                    if predicted_gender:
                        result['gender'] = predicted_gender
                        result['suggestions']['gender_prediction'] = predicted_gender
                        print(f"[SERVICE] Predicted gender: {predicted_gender}")
                
            else:
                result['parse_indicator'] = 'N'
                result['parsed_components'] = {
                    'original_name': name,
                    'first_name': '',
                    'last_name': '',
                    'middle_name': ''
                }
                result['confidence_score'] = 0.6
        
        # Add party type prediction if requested
        if validate_party_type and not party_type_hint:
            result['suggestions']['party_type_prediction'] = result['party_type']
        
        print(f"[SERVICE] ✅ Result: Status={result['validation_status']}, Confidence={result['confidence_score']:.2f}")
        return result
def _detect_organization_api(self, name: str, party_type_hint: str) -> bool:
        """Detect if name is an organization"""
        if party_type_hint.upper() == 'O':
            return True
        elif party_type_hint.upper() == 'I':
            return False
        
        # Auto-detect based on name
        name_lower = name.lower()
        org_indicators = [
            'llc', 'inc', 'corp', 'company', 'ltd', 'co.', 'corporation',
            'hospital', 'medical', 'clinic', 'center', 'services', 'solutions',
            'group', 'partners', 'associates', 'firm', 'office', 'bank',
            'trust', 'foundation', 'institute', 'university', 'college',
            'school', 'church', 'ministry', 'department', 'agency'
        ]
        
        return any(indicator in name_lower for indicator in org_indicators)
    
def _parse_individual_name_api(self, full_name: str) -> Dict[str, str]:
    """Parse individual name into components"""
    if not full_name or not full_name.strip():
        return {'first_name': '', 'last_name': '', 'middle_name': ''}

    # Clean the name
    name = full_name.strip()

    # Remove common titles and suffixes
    titles = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'rev', 'judge', 'senator', 'captain']
    suffixes = ['jr', 'sr', 'iii', 'iv', 'md', 'phd', 'cpa', 'esq']

    # Simple parsing logic
    parts = name.split()
    clean_parts = []

    for part in parts:
        part_lower = part.lower().rstrip('.')
        if part_lower not in titles and part_lower not in suffixes:
            clean_parts.append(part)

    if len(clean_parts) == 0:
        return {'first_name': '', 'last_name': '', 'middle_name': ''}
    elif len(clean_parts) == 1:
        return {'first_name': clean_parts[0], 'last_name': '', 'middle_name': ''}
    elif len(clean_parts) == 2:
        return {'first_name': clean_parts[0], 'last_name': clean_parts[1], 'middle_name': ''}
    else:
        return {
            'first_name': clean_parts[0],
            'last_name': clean_parts[-1],
            'middle_name': ' '.join(clean_parts[1:-1])
        }        
def _predict_gender_api(self, first_name: str) -> str:
        """Predict gender from first name"""
        if not first_name:
            return ''
        
        # Use dictionary loader if available
        if (hasattr(self, 'name_standardizer') and 
            self.name_standardizer and
            hasattr(self.name_standardizer, 'dictionary_loader') and
            self.name_standardizer.dictionary_loader):
            
            return self.name_standardizer.dictionary_loader.predict_gender(first_name)
        
        # Simple heuristic fallback
        name_lower = first_name.lower()
        
        # Common female endings
        if name_lower.endswith(('a', 'ia', 'ana', 'ella', 'ina', 'lyn', 'lynn', 'elle')):
            return 'F'
        
        # Common male endings  
        elif name_lower.endswith(('er', 'on', 'an', 'en', 'son')):
            return 'M'
        
        # Specific common names
        common_female = {'mary', 'jennifer', 'patricia', 'linda', 'barbara', 'susan', 'jessica', 'sarah', 'karen', 'nancy'}
        common_male = {'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'charles', 'joseph', 'thomas'}
        
        if name_lower in common_female:
            return 'F'
        elif name_lower in common_male:
            return 'M'
        
        return ''

def get_api_service_status(self) -> Dict:
        """Get API service status"""
        return {
            'name_validation_api': True,
            'name_validation_available': self.is_name_validation_available(),
            'address_validation_available': self.is_address_validation_available(),
            'dictionary_support': hasattr(self, 'name_standardizer') and self.name_standardizer is not None,
            'gender_prediction': True,
            'organization_detection': True,
            'timestamp': datetime.now().isoformat()
        }    