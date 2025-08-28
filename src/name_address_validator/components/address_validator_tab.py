# src/name_address_validator/components/address_validator_tab.py
"""
Address Validator Tab - Handles both single and multi-file address validation
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class AddressValidatorTab:
    """Address validation tab component"""
    
    def __init__(self, validation_service, logger):
        self.validation_service = validation_service
        self.logger = logger
        
        # Initialize session state for address validation
        if 'address_validation_results' not in st.session_state:
            st.session_state.address_validation_results = []
        
        if 'address_processing_stats' not in st.session_state:
            st.session_state.address_processing_stats = {
                'total_processed': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'files_processed': 0,
                'addresses_qualified': 0
            }
    
    def render(self):
        """Render the address validation tab"""
        st.markdown('<div class="validation-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Address Validation Services</div>', unsafe_allow_html=True)
        
        # Check if USPS service is available
        if not self.validation_service.is_address_validation_available():
            self._render_usps_not_available()
            return
        
        # Sub-tabs for single and multi-file validation
        single_tab, multi_tab = st.tabs(["Single Address", "Multi-File Processing"])
        
        with single_tab:
            self._render_single_address_validation()
        
        with multi_tab:
            self._render_multi_file_validation()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_usps_not_available(self):
        """Render when USPS service is not available"""
        st.warning("⚠️ **USPS API Not Configured**")
        st.write("Address validation requires USPS API credentials.")
        st.write("**To enable address validation:**")
        st.write("1. Obtain USPS API credentials from USPS Developer Portal")
        st.write("2. Set environment variables: `USPS_CLIENT_ID` and `USPS_CLIENT_SECRET`")
        st.write("3. Or configure them in Streamlit secrets")
        
        st.info("💡 **Note:** Name validation is still available and does not require USPS credentials")
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_single_address_validation(self):
        """Render single address validation interface"""
        st.markdown("### Single Address Validation")
        st.write("Validate addresses using USPS API with real-time deliverability verification")
        
        # Input form
        with st.form("single_address_form", clear_on_submit=False):
            # Name fields
            st.markdown("**Contact Information**")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input(
                    "First Name",
                    placeholder="Enter first name",
                    help="Contact's first name"
                )
            
            with col2:
                last_name = st.text_input(
                    "Last Name",
                    placeholder="Enter last name", 
                    help="Contact's last name"
                )
            
            # Address fields
            st.markdown("**Address Information**")
            street_address = st.text_input(
                "Street Address",
                placeholder="123 Main Street, Apt 4B",
                help="Complete street address including apartment/unit if applicable"
            )
            
            col3, col4, col5 = st.columns([3, 1, 2])
            
            with col3:
                city = st.text_input(
                    "City",
                    placeholder="Enter city name",
                    help="City name"
                )
            
            with col4:
                state = st.text_input(
                    "State",
                    placeholder="CA",
                    help="2-letter state code (e.g., CA, NY, TX)",
                    max_chars=2
                )
            
            with col5:
                zip_code = st.text_input(
                    "ZIP Code",
                    placeholder="12345 or 12345-6789",
                    help="5-digit ZIP or ZIP+4 format"
                )
            
            # Validation options
            st.markdown("**Validation Options**")
            col6, col7 = st.columns(2)
            
            with col6:
                include_suggestions = st.checkbox("Include corrections", value=True)
                detailed_analysis = st.checkbox("Detailed USPS analysis", value=True)
            
            with col7:
                check_business = st.checkbox("Business/residential check", value=True)
            
            # Validation check
            all_fields_filled = all([
                first_name.strip(), last_name.strip(), street_address.strip(),
                city.strip(), state.strip(), zip_code.strip()
            ])
            
            # Submit button
            submit_button = st.form_submit_button(
                "🔍 Validate Address",
                type="primary",
                disabled=not all_fields_filled,
                use_container_width=True
            )
            
            # Show missing fields message
            if not all_fields_filled:
                missing_fields = []
                if not first_name.strip(): missing_fields.append("First Name")
                if not last_name.strip(): missing_fields.append("Last Name") 
                if not street_address.strip(): missing_fields.append("Street Address")
                if not city.strip(): missing_fields.append("City")
                if not state.strip(): missing_fields.append("State")
                if not zip_code.strip(): missing_fields.append("ZIP Code")
                
                if missing_fields:
                    st.info(f"ℹ️ Please complete: {', '.join(missing_fields)}")
            
            if submit_button:
                self._process_single_address_validation(
                    first_name, last_name, street_address, city, state, zip_code,
                    include_suggestions, detailed_analysis, check_business
                )
    
    def _process_single_address_validation(self, first_name: str, last_name: str,
                                          street_address: str, city: str, state: str, zip_code: str,
                                          include_suggestions: bool, detailed_analysis: bool,
                                          check_business: bool):
        """Process single address validation"""
        
        self.logger.log(f"Processing single address validation: {street_address}, {city}, {state} {zip_code}", "ADDRESS_VALIDATION")
        
        try:
            with st.spinner("🔄 Validating address with USPS..."):
                start_time = time.time()
                
                # Use the validation service
                result = self.validation_service.validate_single_record(
                    first_name, last_name, street_address, city, state, zip_code
                )
                
                duration = int((time.time() - start_time) * 1000)
                result['processing_time_ms'] = duration
                
                # Update stats
                st.session_state.address_processing_stats['total_processed'] += 1
                if result['overall_valid']:
                    st.session_state.address_processing_stats['successful_validations'] += 1
                else:
                    st.session_state.address_processing_stats['failed_validations'] += 1
                
                # Store result
                result['timestamp'] = datetime.now()
                st.session_state.address_validation_results.append(result)
                
                self._display_single_address_results(result)
                
        except Exception as e:
            st.error(f"❌ Validation error: {str(e)}")
            self.logger.log(f"Single address validation error: {e}", "ADDRESS_VALIDATION", level="ERROR")
    
    def _display_single_address_results(self, result: Dict):
        """Display single address validation results"""
        st.markdown("### 🎉 Address Validation Results")
        
        # Status overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_status = "✅ Valid" if result['overall_valid'] else "❌ Invalid"
            st.metric("Overall Status", overall_status)
        
        with col2:
            name_result = result.get('name_result', {})
            name_status = "✅ Valid" if name_result.get('valid', False) else "❌ Invalid"
            st.metric("Name Status", name_status)
        
        with col3:
            address_result = result.get('address_result', {})
            deliverable = address_result.get('deliverable', False)
            address_status = "✅ Deliverable" if deliverable else "❌ Not Deliverable"
            st.metric("Address Status", address_status)
        
        with col4:
            confidence = result.get('overall_confidence', 0)
            st.metric("Confidence", f"{confidence:.1%}")
        
        # USPS Address Results
        if address_result.get('success') and address_result.get('standardized'):
            st.markdown("### 📮 USPS Standardized Address")
            standardized = address_result['standardized']
            
            st.success(f"""
            **Standardized Address:**
            {standardized['street_address']}
            {standardized['city']}, {standardized['state']} {standardized['zip_code']}
            """)
            
            # USPS Metadata
            if address_result.get('metadata'):
                with st.expander("📊 USPS Address Analysis"):
                    metadata = address_result['metadata']
                    
                    col5, col6, col7 = st.columns(3)
                    
                    with col5:
                        st.write("**Address Type:**")
                        business = "Business" if metadata.get('business', False) else "Residential"
                        st.write(f"- Classification: {business}")
                        
                        vacant = "Yes" if metadata.get('vacant', False) else "No"
                        st.write(f"- Vacant: {vacant}")
                        
                        centralized = "Yes" if metadata.get('centralized', False) else "No"
                        st.write(f"- Centralized Delivery: {centralized}")
                    
                    with col6:
                        st.write("**USPS Codes:**")
                        st.write(f"- DPV Confirmation: {metadata.get('dpv_confirmation', 'N/A')}")
                        st.write(f"- Carrier Route: {metadata.get('carrier_route', 'N/A')}")
                        st.write(f"- Delivery Point: {metadata.get('delivery_point', 'N/A')}")
                    
                    with col7:
                        st.write("**Validation Details:**")
                        st.write(f"- Method: {address_result.get('validation_method', 'N/A')}")
                        st.write(f"- Processing Time: {result.get('processing_time_ms', 0)}ms")
                        match_info = address_result.get('match_info', {})
                        if match_info:
                            st.write(f"- Match Code: {match_info.get('code', 'N/A')}")
        
        # Name Analysis
        if name_result and name_result.get('analysis'):
            with st.expander("👤 Name Analysis"):
                analysis = name_result['analysis']
                
                if 'first_name' in analysis:
                    first_info = analysis['first_name']
                    st.write(f"**First Name:** {'Common' if first_info.get('is_common') else 'Uncommon'}")
                    if first_info.get('rank'):
                        st.write(f"- Popularity Rank: #{first_info['rank']}")
                
                if 'last_name' in analysis:
                    last_info = analysis['last_name']
                    st.write(f"**Last Name:** {'Common' if last_info.get('is_common') else 'Uncommon'}")
                    if last_info.get('rank'):
                        st.write(f"- Popularity Rank: #{last_info['rank']}")
        
        # Errors and Warnings
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
        """Render multi-file address validation interface"""
        st.markdown("### Multi-File Address Processing")
        st.write("Upload multiple CSV files for batch address validation and USPS standardization")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose CSV files",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV files containing addresses in various formats"
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
            
            # Show template download
            with st.expander("📄 Download Address Templates"):
                self._show_address_templates()
            
            # Processing options
            st.markdown("### Processing Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_records = st.number_input(
                    "Max records to validate",
                    min_value=1,
                    max_value=1000,
                    value=100,
                    help="Maximum addresses to validate with USPS (qualified only)"
                )
            
            with col2:
                include_suggestions = st.checkbox(
                    "Include corrections",
                    value=True,
                    help="Include USPS address corrections"
                )
            
            with col3:
                preview_only = st.checkbox(
                    "Preview only",
                    value=False,
                    help="Show qualification results without USPS validation"
                )
            
            # Processing buttons
            col4, col5 = st.columns(2)
            
            with col4:
                if st.button("📋 Address Qualification Preview", type="secondary", use_container_width=True):
                    self._process_address_qualification(uploaded_files, max_records)
            
            with col5:
                if preview_only:
                    if st.button("🔄 Qualification Only", type="primary", use_container_width=True):
                        self._process_address_qualification(uploaded_files, max_records)
                else:
                    if st.button("🚀 Full USPS Validation", type="primary", use_container_width=True):
                        self._process_multi_file_addresses(
                            uploaded_files, max_records, include_suggestions
                        )
    
    def _show_address_templates(self):
        """Show address template downloads"""
        # Standard template
        template_data = {
            'first_name': ['John', 'Jane', 'Michael'],
            'last_name': ['Smith', 'Doe', 'Johnson'],
            'street_address': ['123 Main Street', '456 Oak Avenue', '789 Pine Road'],
            'city': ['New York', 'Los Angeles', 'Chicago'],
            'state': ['NY', 'CA', 'IL'],
            'zip_code': ['10001', '90210', '60601']
        }
        template_df = pd.DataFrame(template_data)
        
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            "📥 Standard Address Template",
            data=csv_template,
            file_name="address_validation_template.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.write("**Supported Column Variations:**")
        st.write("""
        - **Names:** first_name, first, fname, last_name, last, lname, surname
        - **Address:** street_address, address, addr, street, address1
        - **City:** city, town, municipality
        - **State:** state, st, state_code (2-letter codes)
        - **ZIP:** zip_code, zip, zipcode, postal_code
        - **Combined Address:** full_address (format: "Street, City, ST ZIP")
        """)
    
    def _process_address_qualification(self, uploaded_files, max_records: int):
        """Process address qualification preview"""
        try:
            # Convert uploaded files
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                if max_records:
                    df = df.head(max_records)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Analyzing address formats and US qualification..."):
                # Use address standardization service
                standardization_result = self.validation_service.standardize_and_qualify_csv_files(file_data_list)
                
                if standardization_result['success']:
                    preview_result = self.validation_service.generate_comprehensive_preview(standardization_result)
                    
                    if preview_result['success']:
                        self._display_address_qualification_results(preview_result, standardization_result)
                    else:
                        st.error(f"Preview generation failed: {preview_result.get('error', 'Unknown error')}")
                else:
                    st.error(f"Address qualification failed: {standardization_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"Qualification processing error: {str(e)}")
            self.logger.log(f"Address qualification error: {e}", "ADDRESS_QUALIFICATION", level="ERROR")
    
    def _display_address_qualification_results(self, preview_result: Dict, standardization_result: Dict):
        """Display address qualification results"""
        st.markdown("### 🏠 Address Qualification Results")
        
        overview = preview_result['overview']
        
        # Overview metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Files", overview['total_files'])
        
        with col2:
            st.metric("Total Addresses", overview['total_rows'])
        
        with col3:
            st.metric("✅ Qualified", overview['qualified_rows'])
        
        with col4:
            st.metric("❌ Disqualified", overview['disqualified_rows'])
        
        with col5:
            rate = overview['qualification_rate']
            st.metric("Qualification Rate", f"{rate:.1%}")
        
        # Status message
        if overview['ready_for_usps']:
            st.success(f"✅ {overview['qualified_rows']} addresses qualified for USPS validation ({rate:.1%} success rate)")
        else:
            st.warning("⚠️ No qualified US addresses found. Please check your data format.")
        
        # Sample qualified addresses
        qualified_preview = preview_result['qualified_preview']
        if qualified_preview['count'] > 0 and qualified_preview['sample_data']:
            st.markdown("### ✅ Sample Qualified Addresses")
            sample_df = pd.DataFrame(qualified_preview['sample_data'])
            display_columns = ['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code', 'source_file']
            available_columns = [col for col in display_columns if col in sample_df.columns]
            st.dataframe(sample_df[available_columns].head(10), use_container_width=True)
        
        # Download qualified data
        if qualified_preview['count'] > 0:
            qualified_df = standardization_result['qualified_data']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            col1, col2 = st.columns(2)
            
            with col1:
                qualified_csv = qualified_df.to_csv(index=False)
                st.download_button(
                    f"📥 Download Qualified Addresses ({qualified_preview['count']})",
                    data=qualified_csv,
                    file_name=f"qualified_addresses_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Summary data
                summary_data = {
                    'Metric': ['Total Files', 'Total Addresses', 'Qualified', 'Disqualified', 'Qualification Rate'],
                    'Value': [
                        overview['total_files'],
                        overview['total_rows'], 
                        overview['qualified_rows'],
                        overview['disqualified_rows'],
                        f"{rate:.1%}"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_csv = summary_df.to_csv(index=False)
                
                st.download_button(
                    "📊 Download Summary",
                    data=summary_csv,
                    file_name=f"qualification_summary_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    def _process_multi_file_addresses(self, uploaded_files, max_records: int, include_suggestions: bool):
        """Process multiple files for full address validation"""
        try:
            # Convert uploaded files
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Processing complete address validation pipeline..."):
                # Use complete address validation pipeline
                pipeline_result = self.validation_service.process_complete_pipeline_with_preview(
                    file_data_list=file_data_list,
                    include_suggestions=include_suggestions,
                    max_records=max_records
                )
                
                if pipeline_result['success']:
                    self._display_multi_file_address_results(pipeline_result)
                    
                    # Update stats
                    summary = pipeline_result['summary']
                    st.session_state.address_processing_stats['files_processed'] += summary['files_processed']
                    st.session_state.address_processing_stats['total_processed'] += summary['validated_rows']
                    st.session_state.address_processing_stats['successful_validations'] += summary['successful_validations']
                    st.session_state.address_processing_stats['addresses_qualified'] += summary['qualified_rows']
                    
                else:
                    st.error(f"Processing failed: {pipeline_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"Multi-file address processing error: {str(e)}")
            self.logger.log(f"Multi-file address processing error: {e}", "ADDRESS_PROCESSING", level="ERROR")
    
    def _display_multi_file_address_results(self, pipeline_result: Dict):
        """Display multi-file address processing results"""
        st.markdown("### 🎉 Complete Address Validation Results")
        
        summary = pipeline_result['summary']
        validation_result = pipeline_result['validation']
        
        # Summary metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Files Processed", summary['files_processed'])
        
        with col2:
            st.metric("Source Rows", summary['total_source_rows'])
        
        with col3:
            st.metric("Qualified", summary['qualified_rows'])
        
        with col4:
            st.metric("USPS Validated", summary['validated_rows'])
        
        with col5:
            st.metric("Deliverable", summary['successful_validations'])
        
        with col6:
            usps_rate = summary['successful_validations'] / summary['validated_rows'] if summary['validated_rows'] > 0 else 0
            st.metric("USPS Success Rate", f"{usps_rate:.1%}")
        
        # Results table
        if validation_result.get('records'):
            st.markdown("### 📊 Detailed USPS Validation Results")
            results_df = pd.DataFrame(validation_result['records'])
            st.dataframe(results_df, use_container_width=True)
            
            # Download options
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download USPS Results (CSV)",
                    data=csv_data,
                    file_name=f"address_validation_results_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Performance summary
                perf_data = {
                    'Metric': ['Files Processed', 'Addresses Qualified', 'USPS Validated', 
                              'Deliverable', 'USPS Success Rate', 'Processing Time'],
                    'Value': [
                        summary['files_processed'],
                        summary['qualified_rows'],
                        summary['validated_rows'],
                        summary['successful_validations'],
                        f"{usps_rate:.1%}",
                        f"{pipeline_result.get('pipeline_duration_ms', 0) / 1000:.1f}s"
                    ]
                }
                perf_df = pd.DataFrame(perf_data)
                perf_csv = perf_df.to_csv(index=False)
                
                st.download_button(
                    "📊 Download Performance Summary",
                    data=perf_csv,
                    file_name=f"address_validation_summary_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.warning("No validation results to display.")