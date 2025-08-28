# src/name_address_validator/utils/name_format_standardizer.py
"""
Enhanced Name Format Standardizer with AI-like intelligent parsing capabilities
Handles various name formats and converts them to standardized first_name/last_name
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

try:
    # Try to use nameparser if available (install with: pip install nameparser)
    from nameparser import HumanName
    NAMEPARSER_AVAILABLE = True
except ImportError:
    NAMEPARSER_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False


class NameFormatStandardizer:
    """
    Enhanced name format standardizer with AI-like intelligent parsing
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or (lambda msg, cat="NAME_STANDARDIZER": None)
        
        # Standard column mapping for names
        self.standard_columns = {
            'first_name': 'first_name',
            'last_name': 'last_name'
        }
        
        # Column name variations for names
        self.name_column_mappings = {
            'first_name': [
                'first_name', 'first', 'fname', 'given_name', 'forename', 'firstname',
                'first_nm', 'f_name', 'givenname', 'christian_name', 'personal_name'
            ],
            'last_name': [
                'last_name', 'last', 'lname', 'surname', 'family_name', 'lastname',
                'last_nm', 'l_name', 'familyname', 'sur_name'
            ],
            'full_name': [
                'full_name', 'name', 'fullname', 'complete_name', 'customer_name',
                'person_name', 'contact_name', 'individual_name', 'full_nm', 'nm'
            ],
            'middle_name': [
                'middle_name', 'middle', 'mname', 'middle_initial', 'mi', 'middle_nm'
            ],
            'title': [
                'title', 'prefix', 'honorific', 'salutation', 'mr_mrs', 'courtesy_title'
            ],
            'suffix': [
                'suffix', 'name_suffix', 'generation', 'jr_sr', 'degree'
            ]
        }
        
        # Common name prefixes/titles
        self.prefixes = {
            'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'professor', 'rev', 'reverend',
            'fr', 'father', 'sr', 'sister', 'brother', 'br', 'capt', 'captain',
            'col', 'colonel', 'gen', 'general', 'lt', 'lieutenant', 'maj', 'major',
            'hon', 'honorable', 'judge', 'senator', 'rep', 'representative'
        }
        
        # Common name suffixes
        self.suffixes = {
            'jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
            'junior', 'senior', 'phd', 'md', 'dds', 'dvm', 'jd', 'esq', 'esquire',
            'cpa', 'cfa', 'rn', 'lpn', 'pa', 'np', 'do', 'pharmd', 'mba', 'ma', 'ms', 'bs', 'ba'
        }
        
        # Common conjunctions that might appear in names
        self.name_conjunctions = {'van', 'von', 'de', 'del', 'della', 'di', 'da', 'le', 'la', 'du', 'mac', 'mc', 'o'}
        
        self.log("🔧 NameFormatStandardizer initialized with AI-like parsing capabilities")
    
    def log(self, message: str, category: str = "NAME_STANDARDIZER"):
        """Log debug message"""
        try:
            self.debug_callback(message, category)
        except:
            print(f"[{category}] {message}")
    
    def detect_name_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect name column mappings with enhanced logic"""
        self.log(f"🔍 Detecting name columns in: {list(df.columns)}")
        
        detected_mapping = {}
        
        # Direct matching first
        for standard_col, variations in self.name_column_mappings.items():
            for variation in variations:
                for actual_col in df.columns:
                    if actual_col.lower().strip() == variation:
                        detected_mapping[standard_col] = actual_col
                        self.log(f"✅ Exact match: {standard_col} -> {actual_col}")
                        break
                if standard_col in detected_mapping:
                    break
        
        # Check for combined name fields if no separate first/last found
        if 'first_name' not in detected_mapping or 'last_name' not in detected_mapping:
            self._detect_combined_name_fields(df, detected_mapping)
        
        self.log(f"📋 Final name mapping: {detected_mapping}")
        return detected_mapping
    
    def _detect_combined_name_fields(self, df: pd.DataFrame, mapping: Dict[str, str]):
        """Detect combined name fields that need parsing"""
        
        # Look for full name columns
        for col in df.columns:
            col_lower = col.lower().strip()
            
            # Check if this might be a full name column
            for indicator in self.name_column_mappings['full_name']:
                if indicator in col_lower:
                    # Test if this column contains full names
                    sample_data = df[col].dropna().head(5)
                    full_name_count = 0
                    
                    for value in sample_data:
                        if isinstance(value, str) and self._test_full_name(value.strip()):
                            full_name_count += 1
                    
                    if full_name_count >= 2:  # At least 2 samples look like full names
                        mapping['full_name'] = col
                        self.log(f"✅ DETECTED full name column: {col}")
                        return
        
        self.log("❌ No combined name column found")
    
    def _test_full_name(self, text: str) -> bool:
        """Test if text looks like a full name"""
        if not text or len(text.strip()) < 3:
            return False
        
        words = text.strip().split()
        
        # Must have at least 2 words
        if len(words) < 2:
            return False
        
        # Check if it contains only valid name characters
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", text):
            return False
        
        # Should not be all uppercase or all lowercase (unless short)
        if len(text) > 10 and (text.isupper() or text.islower()):
            # Allow if it looks like name pattern
            return len(words) >= 2 and all(len(word) >= 2 for word in words[:2])
        
        return True
    
    def parse_full_name_intelligent(self, full_name: str) -> Dict[str, str]:
        """Intelligently parse full name using multiple strategies"""
        if not isinstance(full_name, str) or not full_name.strip():
            return {'first_name': '', 'last_name': '', 'middle_name': '', 'title': '', 'suffix': ''}
        
        original_name = full_name.strip()
        self.log(f"🧠 PARSING: '{original_name}'")
        
        # Strategy 1: Use nameparser library if available (most accurate)
        if NAMEPARSER_AVAILABLE:
            try:
                result = self._parse_with_nameparser(original_name)
                if self._validate_parse_result(result):
                    self.log(f"✅ NAMEPARSER SUCCESS: {result}")
                    return result
            except Exception as e:
                self.log(f"⚠️ Nameparser failed: {e}")
        
        # Strategy 2: Pattern-based parsing (AI-like rules)
        result = self._parse_with_patterns(original_name)
        if self._validate_parse_result(result):
            self.log(f"✅ PATTERN PARSE SUCCESS: {result}")
            return result
        
        # Strategy 3: Fallback basic parsing
        result = self._parse_basic(original_name)
        self.log(f"⚠️ FALLBACK PARSE: {result}")
        return result
    
    def _parse_with_nameparser(self, name: str) -> Dict[str, str]:
        """Parse using nameparser library"""
        parsed = HumanName(name)
        
        return {
            'first_name': parsed.first,
            'last_name': parsed.last,
            'middle_name': parsed.middle,
            'title': parsed.title,
            'suffix': parsed.suffix
        }
    
    def _parse_with_patterns(self, name: str) -> Dict[str, str]:
        """AI-like pattern-based parsing with multiple strategies"""
        
        # Clean and normalize
        cleaned = self._clean_name(name)
        words = cleaned.split()
        
        if not words:
            return {'first_name': '', 'last_name': '', 'middle_name': '', 'title': '', 'suffix': ''}
        
        result = {'first_name': '', 'last_name': '', 'middle_name': '', 'title': '', 'suffix': ''}
        working_words = words.copy()
        
        # Step 1: Extract title/prefix
        if working_words and working_words[0].lower() in self.prefixes:
            result['title'] = working_words.pop(0)
            self.log(f"   Extracted title: '{result['title']}'")
        
        # Step 2: Extract suffix
        if working_words and working_words[-1].lower() in self.suffixes:
            result['suffix'] = working_words.pop()
            self.log(f"   Extracted suffix: '{result['suffix']}'")
        
        if not working_words:
            return result
        
        # Step 3: Handle different name patterns
        if len(working_words) == 1:
            # Single name - assume it's first name
            result['first_name'] = working_words[0]
            
        elif len(working_words) == 2:
            # Two names - check for "Last, First" pattern
            if ',' in name:
                result['last_name'] = working_words[0].rstrip(',')
                result['first_name'] = working_words[1]
            else:
                # Assume "First Last"
                result['first_name'] = working_words[0]
                result['last_name'] = working_words[1]
                
        elif len(working_words) == 3:
            if ',' in name:
                # "Last, First Middle" pattern
                result['last_name'] = working_words[0].rstrip(',')
                result['first_name'] = working_words[1]
                result['middle_name'] = working_words[2]
            else:
                # "First Middle Last" pattern
                result['first_name'] = working_words[0]
                result['middle_name'] = working_words[1]
                result['last_name'] = working_words[2]
                
        elif len(working_words) >= 4:
            if ',' in name:
                # "Last, First Middle..." pattern
                result['last_name'] = working_words[0].rstrip(',')
                result['first_name'] = working_words[1]
                if len(working_words) > 2:
                    result['middle_name'] = ' '.join(working_words[2:])
            else:
                # Handle compound last names and multiple middle names
                result['first_name'] = working_words[0]
                
                # Check for compound last names (van, von, de, etc.)
                last_name_parts = []
                middle_parts = []
                
                for i, word in enumerate(working_words[1:], 1):
                    if i == len(working_words) - 1:  # Last word
                        last_name_parts.append(word)
                    elif word.lower() in self.name_conjunctions:
                        last_name_parts.append(word)
                    elif i == len(working_words) - 2 and working_words[i+1].lower() not in self.name_conjunctions:
                        # Second to last word, and last word is not a conjunction
                        last_name_parts.append(word)
                    else:
                        middle_parts.append(word)
                
                result['middle_name'] = ' '.join(middle_parts) if middle_parts else ''
                result['last_name'] = ' '.join(last_name_parts) if last_name_parts else working_words[-1]
        
        return result
    
    def _parse_basic(self, name: str) -> Dict[str, str]:
        """Basic fallback parsing"""
        cleaned = self._clean_name(name)
        words = cleaned.split()
        
        result = {'first_name': '', 'last_name': '', 'middle_name': '', 'title': '', 'suffix': ''}
        
        if len(words) >= 1:
            result['first_name'] = words[0]
        if len(words) >= 2:
            result['last_name'] = words[-1]
        if len(words) >= 3:
            result['middle_name'] = ' '.join(words[1:-1])
        
        return result
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize name"""
        if not name:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common punctuation except apostrophes and hyphens
        cleaned = re.sub(r'[^\w\s\-\'\.]', ' ', cleaned)
        
        # Handle multiple spaces again
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _validate_parse_result(self, result: Dict[str, str]) -> bool:
        """Validate that parse result is reasonable"""
        if not result:
            return False
        
        first_name = result.get('first_name', '').strip()
        last_name = result.get('last_name', '').strip()
        
        # Must have at least first name
        if not first_name:
            return False
        
        # Names should be reasonable length
        if len(first_name) > 50 or len(last_name) > 50:
            return False
        
        # Should contain only valid characters
        for name in [first_name, last_name]:
            if name and not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
                return False
        
        return True
    
    def standardize_name_dataframe(self, df: pd.DataFrame, file_name: str = "unknown") -> Tuple[pd.DataFrame, Dict]:
        """Standardize DataFrame with intelligent name parsing"""
        self.log(f"🚀 STARTING name standardization: {file_name} ({len(df)} rows)")
        
        # Detect column mapping
        column_mapping = self.detect_name_column_mapping(df)
        
        info = {
            'file_name': file_name,
            'original_columns': list(df.columns),
            'detected_mapping': column_mapping,
            'row_count': len(df),
            'standardization_errors': [],
            'full_name_parsed': False,
            'parsing_success_rate': 0.0,
            'parsing_summary': {}
        }
        
        # Create result DataFrame
        result_df = pd.DataFrame()
        
        # Handle full name parsing if needed
        if 'full_name' in column_mapping:
            self.log(f"👤 PROCESSING FULL NAMES from column: {column_mapping['full_name']}")
            info['full_name_parsed'] = True
            
            full_name_col = column_mapping['full_name']
            parsing_results = []
            success_count = 0
            
            for idx, row in df.iterrows():
                full_name = str(row[full_name_col])
                self.log(f"   Row {idx+1}: '{full_name}'")
                
                parsed = self.parse_full_name_intelligent(full_name)
                
                if parsed and parsed.get('first_name'):
                    success_count += 1
                    self.log(f"     ✅ SUCCESS: {parsed['first_name']} {parsed['last_name']}")
                else:
                    self.log(f"     ❌ FAILED: {parsed}")
                
                parsing_results.append(parsed)
            
            parsing_success_rate = success_count / len(df) if len(df) > 0 else 0
            info['parsing_success_rate'] = parsing_success_rate
            self.log(f"📊 PARSING SUMMARY: {success_count}/{len(df)} successful ({parsing_success_rate:.1%})")
            
            # Add parsed components to result
            for component in ['first_name', 'last_name', 'middle_name', 'title', 'suffix']:
                result_df[component] = [p.get(component, '') for p in parsing_results]
        else:
            # Map existing separate name columns
            for standard_col in ['first_name', 'last_name']:
                if standard_col in column_mapping:
                    source_col = column_mapping[standard_col]
                    result_df[standard_col] = df[source_col].fillna('')
                    self.log(f"✅ Mapped: {source_col} -> {standard_col}")
                else:
                    result_df[standard_col] = ''
                    self.log(f"⚠️ Missing: {standard_col}")
            
            # Add other name components as empty if not parsed
            for component in ['middle_name', 'title', 'suffix']:
                if component not in result_df.columns:
                    result_df[component] = ''
        
        # Clean and normalize names
        result_df = self._clean_name_data(result_df)
        
        # Add name quality assessment
        result_df = self._add_name_quality_assessment(result_df, info)
        
        # Generate parsing summary
        info['parsing_summary'] = self._generate_parsing_summary(result_df)
        
        self.log(f"✅ NAME STANDARDIZATION COMPLETE: {len(result_df)} rows")
        return result_df, info
    
    def _clean_name_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the standardized name data"""
        self.log("🧹 Cleaning name data")
        
        # Convert to strings and strip whitespace
        for col in ['first_name', 'last_name', 'middle_name', 'title', 'suffix']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' with empty string
                df[col] = df[col].replace('nan', '')
        
        # Title case names
        for col in ['first_name', 'last_name', 'middle_name']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x.title() if x and x != 'nan' else '')
        
        # Standardize titles and suffixes
        if 'title' in df.columns:
            df['title'] = df['title'].apply(self._standardize_title)
        
        if 'suffix' in df.columns:
            df['suffix'] = df['suffix'].apply(self._standardize_suffix)
        
        return df
    
    def _standardize_title(self, title: str) -> str:
        """Standardize title/prefix"""
        if not title or title == 'nan':
            return ''
        
        title_lower = title.lower().strip()
        
        # Common standardizations
        standardizations = {
            'mister': 'Mr',
            'misses': 'Mrs',
            'doctor': 'Dr',
            'professor': 'Prof',
            'reverend': 'Rev'
        }
        
        if title_lower in standardizations:
            return standardizations[title_lower]
        elif title_lower in self.prefixes:
            return title_lower.title()
        
        return title.title()
    
    def _standardize_suffix(self, suffix: str) -> str:
        """Standardize suffix"""
        if not suffix or suffix == 'nan':
            return ''
        
        suffix_lower = suffix.lower().strip()
        
        # Common standardizations
        standardizations = {
            'junior': 'Jr',
            'senior': 'Sr',
            'second': 'II',
            'third': 'III',
            'fourth': 'IV',
            'esquire': 'Esq'
        }
        
        if suffix_lower in standardizations:
            return standardizations[suffix_lower]
        elif suffix_lower in self.suffixes:
            return suffix_lower.upper() if len(suffix_lower) <= 3 else suffix_lower.title()
        
        return suffix.title()
    
    def _add_name_quality_assessment(self, df: pd.DataFrame, info: Dict) -> pd.DataFrame:
        """Add name quality assessment"""
        self.log("🎯 Adding name quality assessment")
        
        quality_scores = []
        quality_issues = []
        
        for idx, row in df.iterrows():
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            
            score = 1.0
            issues = []
            
            # Check if names exist
            if not first_name:
                score -= 0.5
                issues.append('Missing first name')
            
            if not last_name:
                score -= 0.3
                issues.append('Missing last name')
            
            # Check name length
            if first_name and len(first_name) < 2:
                score -= 0.1
                issues.append('Very short first name')
            
            if last_name and len(last_name) < 2:
                score -= 0.1
                issues.append('Very short last name')
            
            # Check for valid characters
            for name, name_type in [(first_name, 'first'), (last_name, 'last')]:
                if name and not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
                    score -= 0.2
                    issues.append(f'Invalid characters in {name_type} name')
            
            quality_scores.append(max(0.0, score))
            quality_issues.append('; '.join(issues) if issues else 'No issues')
        
        df['name_quality_score'] = quality_scores
        df['name_quality_issues'] = quality_issues
        df['name_valid'] = [score >= 0.5 for score in quality_scores]
        
        return df
    
    def _generate_parsing_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary of parsing results"""
        summary = {
            'total_records': len(df),
            'valid_names': len(df[df['name_valid'] == True]) if 'name_valid' in df.columns else 0,
            'invalid_names': len(df[df['name_valid'] == False]) if 'name_valid' in df.columns else 0,
            'average_quality_score': df['name_quality_score'].mean() if 'name_quality_score' in df.columns else 0,
            'has_first_name': len(df[df['first_name'].str.strip() != '']),
            'has_last_name': len(df[df['last_name'].str.strip() != '']),
            'has_middle_name': len(df[df['middle_name'].str.strip() != '']),
            'has_title': len(df[df['title'].str.strip() != '']),
            'has_suffix': len(df[df['suffix'].str.strip() != ''])
        }
        
        summary['validation_rate'] = summary['valid_names'] / summary['total_records'] if summary['total_records'] > 0 else 0
        
        return summary
    
    def standardize_multiple_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Tuple[pd.DataFrame, List[Dict]]:
        """Process multiple CSV files for name standardization"""
        self.log(f"🎯 Processing {len(file_data_list)} files for name parsing")
        
        all_dfs = []
        all_info = []
        
        for i, (df, filename) in enumerate(file_data_list):
            self.log(f"📄 File {i+1}: {filename}")
            
            try:
                std_df, std_info = self.standardize_name_dataframe(df, filename)
                
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
            self.log(f"🎉 COMBINED: {len(combined_df)} total name records")
        else:
            combined_df = pd.DataFrame()
        
        return combined_df, all_info
    
    def get_name_standardization_summary(self, standardization_info_list: List[Dict]) -> Dict:
        """Generate name standardization summary"""
        total_records = 0
        valid_records = 0
        total_files = len(standardization_info_list)
        successful_files = 0
        total_success_rate = 0
        
        for info in standardization_info_list:
            if 'error' not in info:
                successful_files += 1
                parsing_summary = info.get('parsing_summary', {})
                total_records += parsing_summary.get('total_records', 0)
                valid_records += parsing_summary.get('valid_names', 0)
                total_success_rate += info.get('parsing_success_rate', 0)
        
        avg_success_rate = total_success_rate / successful_files if successful_files > 0 else 0
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': total_files - successful_files,
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'overall_validation_rate': valid_records / total_records if total_records > 0 else 0,
            'average_parsing_success_rate': avg_success_rate,
            'ready_for_name_validation': valid_records > 0
        }