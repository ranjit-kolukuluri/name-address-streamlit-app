# src/name_address_validator/components/name_validator_tab.py
"""
Name Validator Tab - Clean Implementation
Handles single, multi-file, and API name validation
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Import the API tab component
try:
    from .name_validation_api_tab import NameValidationAPITab
    API_TAB_AVAILABLE = True
except ImportError:
    API_TAB_AVAILABLE = False


class NameValidatorTab:
    """Name validation tab component with API testing capabilities"""
    
    def __init__(self, validation_service, logger):
        self.validation_service = validation_service
        self.logger = logger
        
        # Initialize the API tab component
        if API_TAB_AVAILABLE:
            self.api_tab = NameValidationAPITab(validation_service, logger)
        else:
            self.api_tab = None
        
        # Initialize session state for name validation
        if 'name_validation_results' not in st.session_state:
            st.session_state.name_validation_results = []
        
        if 'name_processing_stats' not in st.session_state:
            st.session_state.name_processing_stats = {
                'total_processed': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'files_processed': 0
            }
    
    def render(self):
        """Render the name validation tab"""
        st.markdown('<div class="validation-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Name Validation Services</div>', unsafe_allow_html=True)
        
        # Sub-tabs for single, multi-file, and API validation
        single_tab, multi_tab, api_tab = st.tabs(["Single Name", "Multi-File Processing", "API Testing"])
        
        with single_tab:
            self._render_single_name_validation()
        
        with multi_tab:
            self._render_multi_file_validation()
        
        with api_tab:
            self._render_api_validation()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_single_name_validation(self):
        """Render single name validation interface"""
        st.markdown("### Single Name Validation")
        st.write("Validate and analyze individual names with intelligent suggestions")
        
        # Input form
        with st.form("single_name_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name",
                    placeholder="Enter first name",
                    help="Required - Person's first name"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name", 
                    placeholder="Enter last name",
                    help="Required - Person's last name"
                )
            
            # Additional name fields
            with st.expander("Additional Name Details (Optional)"):
                col3, col4 = st.columns(2)
                with col3:
                    middle_name = st.text_input("Middle Name", placeholder="Optional")
                    title = st.text_input("Title/Prefix", placeholder="Mr, Mrs, Dr, etc.")
                
                with col4:
                    suffix = st.text_input("Suffix", placeholder="Jr, Sr, PhD, etc.")
            
            # Validation options
            st.markdown("**Validation Options**")
            col5, col6 = st.columns(2)
            
            with col5:
                include_suggestions = st.checkbox("Include name suggestions", value=True)
                detailed_analysis = st.checkbox("Detailed analysis", value=True)
            
            with col6:
                check_variations = st.checkbox("Check cultural variations", value=True)
            
            # Submit button
            submit_button = st.form_submit_button(
                "🔍 Validate Name", 
                type="primary",
                use_container_width=True
            )
            
            if submit_button:
                self._process_single_name_validation(
                    first_name, last_name, middle_name, title, suffix,
                    include_suggestions, detailed_analysis, check_variations
                )
    
    def _process_single_name_validation(self, first_name: str, last_name: str, 
                                       middle_name: str, title: str, suffix: str,
                                       include_suggestions: bool, detailed_analysis: bool, 
                                       check_variations: bool):
        """Process single name validation"""
        
        if not first_name.strip() or not last_name.strip():
            st.error("⚠️ Both first name and last name are required")
            return
        
        self.logger.log(f"Processing single name validation: {first_name} {last_name}", "NAME_VALIDATION")
        
        try:
            with st.spinner("🔄 Validating name..."):
                # Use the name validator from the service
                result = self.validation_service.name_validator.validate(first_name, last_name)
                
                # Add additional processing if requested
                if detailed_analysis:
                    result['detailed_analysis'] = True
                    result['input_details'] = {
                        'middle_name': middle_name,
                        'title': title,
                        'suffix': suffix
                    }
                
                # Update stats
                st.session_state.name_processing_stats['total_processed'] += 1
                if result['valid']:
                    st.session_state.name_processing_stats['successful_validations'] += 1
                else:
                    st.session_state.name_processing_stats['failed_validations'] += 1
                
                # Store result
                result['timestamp'] = datetime.now()
                st.session_state.name_validation_results.append(result)
                
                self._display_single_name_results(result)
                
        except Exception as e:
            st.error(f"❌ Validation error: {str(e)}")
            self.logger.log(f"Single name validation error: {e}", "NAME_VALIDATION", level="ERROR")
    
    def _display_single_name_results(self, result: Dict):
        """Display single name validation results"""
        st.markdown("### 🎉 Validation Results")
        
        # Status overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Valid" if result['valid'] else "❌ Invalid"
            st.metric("Name Status", status)
        
        with col2:
            confidence = result.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.1%}")
        
        with col3:
            issues = len(result.get('errors', [])) + len(result.get('warnings', []))
            st.metric("Issues Found", issues)
        
        # Normalized names
        if 'normalized' in result:
            st.markdown("**Standardized Format:**")
            normalized = result['normalized']
            st.success(f"**{normalized['first_name']} {normalized['last_name']}**")
        
        # Analysis details
        if 'analysis' in result and result['analysis']:
            with st.expander("📊 Detailed Analysis"):
                analysis = result['analysis']
                
                if 'first_name' in analysis:
                    first_info = analysis['first_name']
                    st.write(f"**First Name Analysis:**")
                    st.write(f"- Common name: {'✅' if first_info.get('is_common') else '❌'}")
                    if first_info.get('rank'):
                        st.write(f"- Popularity rank: #{first_info['rank']}")
                    st.write(f"- Frequency: {first_info.get('frequency', 'unknown').replace('_', ' ').title()}")
                
                if 'last_name' in analysis:
                    last_info = analysis['last_name']
                    st.write(f"**Last Name Analysis:**")
                    st.write(f"- Common name: {'✅' if last_info.get('is_common') else '❌'}")
                    if last_info.get('rank'):
                        st.write(f"- Popularity rank: #{last_info['rank']}")
                    st.write(f"- Frequency: {last_info.get('frequency', 'unknown').replace('_', ' ').title()}")
        
        # Suggestions
        if 'suggestions' in result and result['suggestions']:
            with st.expander("💡 Name Suggestions"):
                suggestions = result['suggestions']
                
                if 'first_name' in suggestions and suggestions['first_name']:
                    st.write("**First Name Suggestions:**")
                    for suggestion in suggestions['first_name'][:3]:
                        st.write(f"- **{suggestion['suggestion']}** ({suggestion['confidence']:.1%} confidence)")
                
                if 'last_name' in suggestions and suggestions['last_name']:
                    st.write("**Last Name Suggestions:**")
                    for suggestion in suggestions['last_name'][:3]:
                        st.write(f"- **{suggestion['suggestion']}** ({suggestion['confidence']:.1%} confidence)")
        
        # Issues
        if result.get('errors') or result.get('warnings'):
            with st.expander("⚠️ Issues & Warnings"):
                if result.get('errors'):
                    st.error("**Errors:**")
                    for error in result['errors']:
                        st.write(f"- {error}")
                
                if result.get('warnings'):
                    st.warning("**Warnings:**")
                    for warning in result['warnings']:
                        st.write(f"- {warning}")
    
    def _render_multi_file_validation(self):
        """Render multi-file name validation interface"""
        st.markdown("### Multi-File Name Processing")
        st.write("Upload multiple CSV files for batch name validation and standardization")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose CSV files",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV files containing names in various formats"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            # Display file info
            with st.expander("📋 File Information"):
                for i, file in enumerate(uploaded_files, 1):
                    try:
                        df = pd.read_csv(file)
                        st.write(f"**{i}. {file.name}** - {len(df)} rows, {len(df.columns)} columns")
                        st.write(f"   Columns: {list(df.columns)}")
                    except Exception as e:
                        st.error(f"   Error reading {file.name}: {e}")
            
            # Processing options
            st.markdown("### Processing Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_records = st.number_input(
                    "Max records per file",
                    min_value=1,
                    max_value=5000,
                    value=1000,
                    help="Maximum number of names to process per file"
                )
            
            with col2:
                include_suggestions = st.checkbox(
                    "Include suggestions",
                    value=True,
                    help="Generate suggestions for invalid or uncommon names"
                )
            
            with col3:
                detailed_output = st.checkbox(
                    "Detailed output",
                    value=True,
                    help="Include detailed analysis and metadata"
                )
            
            # Processing buttons
            col4, col5 = st.columns(2)
            
            with col4:
                if st.button("📋 Preview Only", type="secondary", use_container_width=True):
                    self._process_name_preview(uploaded_files, max_records)
            
            with col5:
                if st.button("🚀 Full Processing", type="primary", use_container_width=True):
                    self._process_multi_file_names(
                        uploaded_files, max_records, include_suggestions, detailed_output
                    )
    
    def _process_name_preview(self, uploaded_files, max_records: int):
        """Generate preview of name processing"""
        try:
            # Convert uploaded files to format expected by service
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                if max_records:
                    df = df.head(max_records)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Generating name processing preview..."):
                # Use the name standardization service
                standardization_result = self.validation_service.standardize_and_parse_names_from_csv(file_data_list)
                
                if standardization_result['success']:
                    preview_result = self.validation_service.generate_name_validation_preview(standardization_result)
                    
                    if preview_result['success']:
                        self._display_name_preview_results(preview_result, standardization_result)
                    else:
                        st.error(f"Preview generation failed: {preview_result.get('error', 'Unknown error')}")
                else:
                    st.error(f"Name standardization failed: {standardization_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"Preview processing error: {str(e)}")
            self.logger.log(f"Name preview error: {e}", "NAME_PREVIEW", level="ERROR")
    
    def _display_name_preview_results(self, preview_result: Dict, standardization_result: Dict):
        """Display name preview results"""
        st.markdown("### 👤 Name Processing Preview")
        
        overview = preview_result['overview']
        
        # Overview metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Files", overview['total_files'])
        
        with col2:
            st.metric("Total Names", overview['total_records'])
        
        with col3:
            st.metric("✅ Valid", overview['valid_names'])
        
        with col4:
            st.metric("❌ Invalid", overview['invalid_names'])
        
        with col5:
            rate = overview['validation_rate']
            st.metric("Success Rate", f"{rate:.1%}")
        
        # Status message
        if overview['ready_for_validation']:
            st.success(f"✅ {overview['valid_names']} names ready for validation ({rate:.1%} success rate)")
        else:
            st.warning("⚠️ No valid names found. Please check your data format.")
        
        # Sample valid names
        valid_preview = preview_result['valid_preview']
        if valid_preview['count'] > 0 and valid_preview['sample_data']:
            st.markdown("### ✅ Sample Valid Names")
            sample_df = pd.DataFrame(valid_preview['sample_data'])
            display_columns = ['first_name', 'last_name', 'middle_name', 'source_file']
            available_columns = [col for col in display_columns if col in sample_df.columns]
            st.dataframe(sample_df[available_columns].head(10), use_container_width=True)
        
        # Sample invalid names
        invalid_preview = preview_result['invalid_preview']
        if invalid_preview['count'] > 0:
            with st.expander(f"❌ Invalid Names ({invalid_preview['count']} total)"):
                if invalid_preview['sample_data']:
                    sample_df = pd.DataFrame(invalid_preview['sample_data'])
                    st.dataframe(sample_df.head(10), use_container_width=True)
                
                # Common issues
                if invalid_preview.get('top_issues'):
                    st.write("**Most Common Issues:**")
                    for issue, count in invalid_preview['top_issues']:
                        percentage = (count / invalid_preview['count']) * 100
                        st.write(f"- **{issue}**: {count} records ({percentage:.1f}%)")
    
    def _process_multi_file_names(self, uploaded_files, max_records: int, 
                                 include_suggestions: bool, detailed_output: bool):
        """Process multiple files for name validation"""
        try:
            # Convert uploaded files
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                if max_records:
                    df = df.head(max_records)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Processing names through complete validation pipeline..."):
                # Use complete name validation pipeline
                pipeline_result = self.validation_service.process_complete_name_validation_pipeline(
                    file_data_list=file_data_list,
                    include_suggestions=include_suggestions,
                    max_records=max_records
                )
                
                if pipeline_result['success']:
                    self._display_multi_file_results(pipeline_result)
                    
                    # Update stats
                    summary = pipeline_result['summary']
                    st.session_state.name_processing_stats['files_processed'] += summary['files_processed']
                    st.session_state.name_processing_stats['total_processed'] += summary['validated_names']
                    st.session_state.name_processing_stats['successful_validations'] += summary['successful_validations']
                    st.session_state.name_processing_stats['failed_validations'] += summary['failed_validations']
                    
                else:
                    st.error(f"Processing failed: {pipeline_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"Multi-file processing error: {str(e)}")
            self.logger.log(f"Multi-file name processing error: {e}", "NAME_PROCESSING", level="ERROR")
    
    def _display_multi_file_results(self, pipeline_result: Dict):
        """Display multi-file processing results"""
        st.markdown("### 🎉 Multi-File Processing Results")
        
        summary = pipeline_result['summary']
        validation_result = pipeline_result['validation']
        
        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Files Processed", summary['files_processed'])
        
        with col2:
            st.metric("Names Validated", summary['validated_names'])
        
        with col3:
            st.metric("Successful", summary['successful_validations'])
        
        with col4:
            st.metric("Failed", summary['failed_validations'])
        
        with col5:
            rate = summary['validation_success_rate']
            st.metric("Success Rate", f"{rate:.1%}")
        
        # Results table
        if validation_result['records']:
            st.markdown("### 📊 Detailed Results")
            results_df = pd.DataFrame(validation_result['records'])
            st.dataframe(results_df, use_container_width=True)
            
            # Download options
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Results (CSV)",
                    data=csv_data,
                    file_name=f"name_validation_results_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Summary statistics
                stats_data = {
                    'Metric': ['Files Processed', 'Names Validated', 'Successful Validations', 
                              'Failed Validations', 'Success Rate', 'Processing Time'],
                    'Value': [
                        summary['files_processed'],
                        summary['validated_names'],
                        summary['successful_validations'],
                        summary['failed_validations'],
                        f"{summary['validation_success_rate']:.1%}",
                        f"{pipeline_result.get('pipeline_duration_ms', 0) / 1000:.1f}s"
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_csv = stats_df.to_csv(index=False)
                
                st.download_button(
                    "📊 Download Summary",
                    data=stats_csv,
                    file_name=f"name_validation_summary_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    def _render_api_validation(self):
        """Render API validation interface"""
        if self.api_tab and API_TAB_AVAILABLE:
            self.api_tab.render()
        else:
            # Fallback simple API interface
            st.markdown("### 🧪 Name Validation API Testing")
            st.warning("⚠️ Full API component not available. Using basic interface.")
            
            # Simple API interface
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
                    }
                ]
            }
            
            import json
            json_input = st.text_area(
                "Enter JSON Payload:",
                value=json.dumps(default_payload, indent=2),
                height=250,
                help="Enter valid JSON with records array"
            )
            
            if st.button("🚀 Test API Request", type="primary", use_container_width=True):
                try:
                    payload = json.loads(json_input)
                    st.success("✅ JSON is valid!")
                    st.json(payload)
                    
                    # Mock response
                    st.markdown("### 📊 Mock API Response")
                    mock_response = {
                        "status": "success",
                        "processed_count": len(payload.get("records", [])),
                        "results": [
                            {
                                "uniqueid": record.get("uniqueid", ""),
                                "name": record.get("name", ""),
                                "validation_status": "valid",
                                "confidence_score": 0.85,
                                "party_type": "I" if "corp" not in record.get("name", "").lower() else "O"
                            } for record in payload.get("records", [])
                        ]
                    }
                    st.json(mock_response)
                    
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")