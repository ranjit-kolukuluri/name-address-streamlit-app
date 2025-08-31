# src/name_address_validator/components/name_validation_api_tab.py
"""
Name Validation API Tab - Clean Implementation
Provides Swagger-like UI for API testing with JSON payloads
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional


class NameValidationAPITab:
    """Name validation API testing tab with Swagger-like interface"""
    
    def __init__(self, validation_service, logger):
        self.validation_service = validation_service
        self.logger = logger
        
        # Initialize session state for API testing
        if 'api_test_history' not in st.session_state:
            st.session_state.api_test_history = []
        
        if 'api_processing_stats' not in st.session_state:
            st.session_state.api_processing_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_records_processed': 0
            }
    
    def render(self):
        """Render the API testing tab"""
        st.markdown("### 🧪 Name Validation API Service")
        st.info("Test your name validation API with JSON payloads and get structured responses")
        
        # Check if name validation is available
        if not self.validation_service or not self.validation_service.is_name_validation_available():
            st.error("❌ Name validation service is not available. Please check your configuration.")
            return
        
        # API Documentation section
        self._render_api_documentation()
        
        st.markdown("---")
        
        # API Testing Interface
        self._render_api_testing_interface()
        
        st.markdown("---")
        
        # API Statistics
        self._render_api_statistics()
    
    def _render_api_documentation(self):
        """Render API documentation section"""
        with st.expander("📖 API Documentation", expanded=False):
            st.markdown("""
            #### **Name Validation API Endpoint**
            
            **Request Format:**
            ```json
            {
              "records": [
                {
                  "uniqueid": "string (required)",
                  "name": "string (required)",
                  "gender": "string (optional: M/F/'')",
                  "party_type": "string (optional: I/O/'')", 
                  "parseInd": "string (optional: Y/N/'')"
                }
              ]
            }
            ```
            
            **Response Format:**
            ```json
            {
              "status": "success|error",
              "processed_count": "integer",
              "successful_count": "integer",
              "results": [
                {
                  "uniqueid": "string",
                  "name": "string",
                  "gender": "string",
                  "party_type": "string",
                  "parse_indicator": "string",
                  "validation_status": "valid|invalid|warning|error",
                  "confidence_score": "float (0.0-1.0)",
                  "parsed_components": {
                    "first_name": "string",
                    "last_name": "string", 
                    "middle_name": "string"
                  },
                  "suggestions": {
                    "name_suggestions": ["array"],
                    "gender_prediction": "M|F|",
                    "party_type_prediction": "I|O"
                  },
                  "errors": ["array"],
                  "warnings": ["array"]
                }
              ],
              "processing_time_ms": "integer",
              "timestamp": "string"
            }
            ```
            
            **Field Descriptions:**
            - `uniqueid`: Unique identifier for the record
            - `name`: Full name to validate
            - `gender`: Optional gender hint (M/F or empty)
            - `party_type`: Optional type hint (I=Individual, O=Organization or empty)
            - `parseInd`: Parse indicator (Y=parse name, N=use as-is, empty=auto-detect)
            """)
    
    def _render_api_testing_interface(self):
        """Render the main API testing interface"""
        st.markdown("### 🧪 API Testing Interface")
        
        # Input method selection
        col1, col2 = st.columns(2)
        
        with col1:
            input_method = st.selectbox(
                "Choose input method:",
                ["Direct JSON Input", "Quick Test Generator", "Upload JSON File"]
            )
        
        with col2:
            # Processing options
            include_suggestions = st.checkbox("Include suggestions", value=True)
        
        if input_method == "Direct JSON Input":
            self._render_json_input()
        elif input_method == "Quick Test Generator":
            self._render_test_generator()
        else:
            self._render_file_upload()
    
    def _render_json_input(self):
        """Render direct JSON input interface"""
        st.markdown("#### Direct JSON Input")
        
        # Default payload
        default_payload = {
            "records": [
                {
                    "uniqueid": "001",
                    "name": "John Michael Smith",
                    "gender": "",
                    "party_type": "I",
                    "parseInd": "Y"
                },
                {
                    "uniqueid": "002", 
                    "name": "TechCorp Solutions LLC",
                    "gender": "",
                    "party_type": "O",
                    "parseInd": "N"
                },
                {
                    "uniqueid": "003",
                    "name": "Mary Johnson-Williams",
                    "gender": "F",
                    "party_type": "",
                    "parseInd": "Y"
                }
            ]
        }
        
        # JSON input area
        json_input = st.text_area(
            "Enter JSON payload:",
            value=json.dumps(default_payload, indent=2),
            height=350,
            help="Enter valid JSON payload with records array"
        )
        
        # Submit button
        if st.button("🚀 Submit API Request", type="primary", use_container_width=True):
            self._process_json_payload(json_input)
    
    def _render_test_generator(self):
        """Render quick test generator"""
        st.markdown("#### Quick Test Generator")
        
        # Test scenario selection
        scenario = st.selectbox(
            "Select test scenario:",
            [
                "Mixed Individual Names",
                "Organization Names", 
                "Names with Parsing Challenges",
                "International Names",
                "Names with Titles"
            ]
        )
        
        # Number of records
        num_records = st.slider("Number of test records:", 1, 8, 3)
        
        if st.button("🎯 Generate & Submit Test", type="primary", use_container_width=True):
            test_payload = self._generate_test_payload(scenario, num_records)
            json_string = json.dumps(test_payload, indent=2)
            
            st.markdown("**Generated Test Payload:**")
            st.code(json_string, language="json")
            
            # Auto-submit
            self._process_json_payload(json_string)
    
    def _render_file_upload(self):
        """Render file upload interface"""
        st.markdown("#### Upload JSON File")
        
        uploaded_file = st.file_uploader(
            "Choose JSON file",
            type=['json'],
            help="Upload a JSON file containing the payload"
        )
        
        if uploaded_file is not None:
            try:
                json_content = json.load(uploaded_file)
                st.success("✅ File loaded successfully")
                
                # Preview
                with st.expander("📋 File Preview"):
                    st.json(json_content)
                
                # Submit
                if st.button("🚀 Process Uploaded File", type="primary", use_container_width=True):
                    json_string = json.dumps(json_content)
                    self._process_json_payload(json_string)
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    def _generate_test_payload(self, scenario: str, num_records: int) -> Dict:
        """Generate test payload based on scenario"""
        
        test_data = {
            "Mixed Individual Names": [
                "John Michael Smith", "Mary Johnson-Williams", "Robert Brown Jr",
                "Jennifer Lisa Garcia", "William James Davis", "Sarah Michelle Wilson",
                "Michael David Miller", "Jessica Anne Martinez"
            ],
            "Organization Names": [
                "ABC Technology Solutions LLC", "Springfield Medical Center", "Global Manufacturing Inc",
                "Downtown Law Offices", "City Hospital System", "Regional Bank Corp",
                "TechStart Solutions", "Healthcare Partners LLC"
            ],
            "Names with Parsing Challenges": [
                "Mary-Jane O'Connor-Smith", "Jean-Pierre du Lac", "Dr. William Smith III",
                "Rev. John Baptist", "Ms. Sarah von Habsburg", "Prof. Maria Santos-Cruz",
                "José María García", "Li Wei-Chen"
            ],
            "International Names": [
                "Zhang Wei", "Hiroshi Tanaka", "María José González",
                "Ahmed Hassan", "Priya Sharma", "Giovanni Rossi",
                "Olaf Andersson", "Fatima Al-Zahra"
            ],
            "Names with Titles": [
                "Dr. John Smith MD", "Prof. Sarah Wilson PhD", "Rev. Michael Brown",
                "Ms. Jennifer Davis CPA", "Mr. Robert Johnson Jr", "Mrs. Mary Smith-Jones",
                "Judge William Miller", "Senator Lisa Garcia"
            ]
        }
        
        names = test_data.get(scenario, test_data["Mixed Individual Names"])
        
        records = []
        for i in range(min(num_records, len(names))):
            # Determine party type based on scenario
            party_type = "O" if "Organization" in scenario else ""
            parse_ind = "Y" if "Organization" not in scenario else "N"
            
            records.append({
                "uniqueid": f"{i+1:03d}",
                "name": names[i],
                "gender": "",
                "party_type": party_type,
                "parseInd": parse_ind
            })
        
        return {"records": records}
    
    def _process_json_payload(self, json_input: str):
        """Process JSON payload and return structured results"""
        
        self.logger.log("Processing API payload request", "API_VALIDATION")
        start_time = time.time()
        
        try:
            # Parse JSON
            try:
                payload = json.loads(json_input)
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
                return
            
            # Validate payload structure
            if not isinstance(payload, dict) or 'records' not in payload:
                st.error("❌ Payload must contain 'records' array")
                return
            
            if not isinstance(payload['records'], list):
                st.error("❌ 'records' must be an array")
                return
            
            records = payload['records']
            if not records:
                st.error("❌ 'records' array cannot be empty")
                return
            
            # Process records
            with st.spinner(f"🔄 Processing {len(records)} records..."):
                results = []
                successful_count = 0
                
                for i, record in enumerate(records):
                    try:
                        # Validate required fields
                        if not isinstance(record, dict):
                            raise ValueError("Record must be an object")
                        
                        if not record.get('uniqueid'):
                            raise ValueError("'uniqueid' is required")
                        
                        if not record.get('name'):
                            raise ValueError("'name' is required")
                        
                        # Process single record
                        result = self._process_single_record(record)
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
                
                # Build response
                processing_time = int((time.time() - start_time) * 1000)
                
                response = {
                    'status': 'success',
                    'processed_count': len(results),
                    'successful_count': successful_count,
                    'results': results,
                    'processing_time_ms': processing_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update stats
                st.session_state.api_processing_stats['total_requests'] += 1
                st.session_state.api_processing_stats['total_records_processed'] += len(results)
                if successful_count > 0:
                    st.session_state.api_processing_stats['successful_requests'] += 1
                else:
                    st.session_state.api_processing_stats['failed_requests'] += 1
                
                # Store in history
                st.session_state.api_test_history.append({
                    'timestamp': datetime.now(),
                    'request_size': len(records),
                    'successful_count': successful_count,
                    'processing_time_ms': processing_time,
                    'response': response
                })
                
                # Display results
                self._display_api_results(response)
                
        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")
            self.logger.log(f"API processing error: {e}", "API_VALIDATION", level="ERROR")
    
    def _process_single_record(self, record: Dict) -> Dict:
        """Process a single record for validation"""
        
        uniqueid = record['uniqueid']
        name = record['name'].strip()
        gender_hint = record.get('gender', '').strip()
        party_type_hint = record.get('party_type', '').strip()
        parse_ind = record.get('parseInd', '').strip()
        
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
        is_org = self._detect_organization(name, party_type_hint)
        
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
            
        else:
            # Handle individual name
            result['party_type'] = 'I'
            
            # Parse name if requested
            if parse_ind.upper() == 'Y' or parse_ind == '':
                parsed = self._parse_individual_name(name)
                result['parsed_components'] = parsed
                result['parse_indicator'] = 'Y'
                
                # Validate parsed components
                if parsed['first_name'] or parsed['last_name']:
                    result['validation_status'] = 'valid'
                    result['confidence_score'] = 0.8
                    
                    # Predict gender if not provided
                    if not gender_hint and parsed['first_name']:
                        predicted_gender = self._predict_gender(parsed['first_name'])
                        if predicted_gender:
                            result['gender'] = predicted_gender
                            result['suggestions']['gender_prediction'] = predicted_gender
                else:
                    result['validation_status'] = 'invalid'
                    result['errors'].append('Could not parse name into valid components')
                    result['confidence_score'] = 0.2
            else:
                result['parse_indicator'] = 'N'
                result['parsed_components'] = {
                    'original_name': name,
                    'first_name': '',
                    'last_name': '',
                    'middle_name': ''
                }
                result['confidence_score'] = 0.6
        
        # Add party type prediction if not provided
        if not party_type_hint:
            result['suggestions']['party_type_prediction'] = result['party_type']
        
        return result
    
    def _detect_organization(self, name: str, party_type_hint: str) -> bool:
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
            'school', 'technologies', 'systems', 'enterprises'
        ]
        
        return any(indicator in name_lower for indicator in org_indicators)
    
    def _parse_individual_name(self, full_name: str) -> Dict[str, str]:
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
    
    def _predict_gender(self, first_name: str) -> str:
        """Predict gender from first name"""
        if not first_name:
            return ''
        
        # Use dictionary loader if available
        if (hasattr(self.validation_service, 'name_standardizer') and 
            self.validation_service.name_standardizer and
            hasattr(self.validation_service.name_standardizer, 'dictionary_loader') and
            self.validation_service.name_standardizer.dictionary_loader):
            
            return self.validation_service.name_standardizer.dictionary_loader.predict_gender(first_name)
        
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
    
    def _display_api_results(self, response: Dict):
        """Display API response results"""
        st.markdown("### 🎉 API Response")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", response['status'].upper())
        
        with col2:
            st.metric("Processed", response['processed_count'])
        
        with col3:
            st.metric("Successful", response['successful_count'])
        
        with col4:
            st.metric("Processing Time", f"{response['processing_time_ms']}ms")
        
        # Results display options
        display_format = st.radio(
            "Display format:",
            ["JSON Response", "Table View", "Detailed View"],
            horizontal=True,
            key="api_display_format"
        )
        
        if display_format == "JSON Response":
            st.markdown("**Full JSON Response:**")
            st.json(response)
            
            # Download option
            json_str = json.dumps(response, indent=2)
            st.download_button(
                "📥 Download JSON Response",
                data=json_str,
                file_name=f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        elif display_format == "Table View":
            # Convert to table format
            table_data = []
            for result in response['results']:
                parsed = result.get('parsed_components', {})
                table_data.append({
                    'UniqueID': result['uniqueid'],
                    'Name': result['name'],
                    'Status': result['validation_status'],
                    'Confidence': f"{result['confidence_score']:.2f}",
                    'Gender': result['gender'],
                    'Party Type': result['party_type'],
                    'Parse Indicator': result['parse_indicator'],
                    'First Name': parsed.get('first_name', ''),
                    'Last Name': parsed.get('last_name', ''),
                    'Middle Name': parsed.get('middle_name', ''),
                    'Organization': parsed.get('organization_name', '')
                })
            
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=f"api_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        else:  # Detailed View
            st.markdown("**Detailed Results:**")
            for i, result in enumerate(response['results']):
                with st.expander(f"Record {i+1}: {result['uniqueid']} - {result['name']}"):
                    
                    # Status
                    status_color = {"valid": "🟢", "invalid": "🔴", "warning": "🟡", "error": "⚫"}.get(result['validation_status'], "⚪")
                    st.write(f"**Status:** {status_color} {result['validation_status'].upper()}")
                    st.write(f"**Confidence:** {result['confidence_score']:.2%}")
                    
                    # Parsed components
                    if result['parsed_components']:
                        st.write("**Parsed Components:**")
                        for key, value in result['parsed_components'].items():
                            if value:
                                st.write(f"- {key.replace('_', ' ').title()}: {value}")
                    
                    # Suggestions
                    if result['suggestions']:
                        st.write("**Suggestions:**")
                        for key, value in result['suggestions'].items():
                            if isinstance(value, list):
                                st.write(f"- {key.replace('_', ' ').title()}: {', '.join(value)}")
                            elif value:
                                st.write(f"- {key.replace('_', ' ').title()}: {value}")
                    
                    # Errors and warnings
                    if result['errors']:
                        st.error("**Errors:**")
                        for error in result['errors']:
                            st.write(f"- {error}")
                    
                    if result['warnings']:
                        st.warning("**Warnings:**")
                        for warning in result['warnings']:
                            st.write(f"- {warning}")
    
    def _render_api_statistics(self):
        """Render API testing statistics"""
        st.markdown("### 📊 API Testing Statistics")
        
        stats = st.session_state.api_processing_stats
        
        # Stats metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", stats['total_requests'])
        
        with col2:
            st.metric("Successful", stats['successful_requests'])
        
        with col3:
            st.metric("Failed", stats['failed_requests'])
        
        with col4:
            st.metric("Records Processed", stats['total_records_processed'])
        
        # Recent history
        history = st.session_state.api_test_history
        if history:
            st.markdown("### 📝 Recent Requests")
            
            # Show last 5 requests
            recent_history = history[-5:]
            
            history_data = []
            for request in recent_history:
                history_data.append({
                    'Timestamp': request['timestamp'].strftime('%H:%M:%S'),
                    'Records': request['request_size'],
                    'Successful': request['successful_count'],
                    'Time (ms)': request['processing_time_ms'],
                    'Success Rate': f"{(request['successful_count'] / request['request_size'] * 100):.0f}%" if request['request_size'] > 0 else "0%"
                })
            
            if history_data:
                history_df = pd.DataFrame(history_data)
                st.dataframe(history_df, use_container_width=True)
                
                # Clear history option
                if st.button("🗑️ Clear History", type="secondary"):
                    st.session_state.api_test_history = []
                    st.session_state.api_processing_stats = {
                        'total_requests': 0,
                        'successful_requests': 0,
                        'failed_requests': 0,
                        'total_records_processed': 0
                    }
                    st.success("History cleared!")
                    st.rerun()
        else:
            st.info("No API requests made yet")