# src/name_address_validator/app.py
"""
Complete Working Enterprise Name & Address Validator - Main Application
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Setup paths
def setup_python_path():
    current_file = Path(__file__).resolve()
    src_dir = current_file.parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

setup_python_path()

# Import services
try:
    from name_address_validator.services.validation_service import ValidationService
    from name_address_validator.utils.config import load_usps_credentials
    from name_address_validator.utils.logger import AppLogger
    
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error("Please ensure all components are properly installed")
    st.stop()


class EnterpriseValidatorApp:
    """Main application class for enterprise validator"""
    
    def __init__(self):
        self.logger = AppLogger()
        self.validation_service = None
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize core services"""
        try:
            self.validation_service = ValidationService(debug_callback=self.logger.log)
            self.logger.log("✅ Validation services initialized", "SYSTEM")
        except Exception as e:
            self.logger.log(f"❌ Failed to initialize services: {e}", "SYSTEM", level="ERROR")
            st.error(f"Service initialization failed: {e}")
    
    def apply_enterprise_styling(self):
        """Apply clean enterprise styling"""
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .enterprise-header {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
        
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 400;
        }
        
        .status-indicator {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            margin: 0.5rem;
        }
        
        .status-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .status-warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 8px;
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 56px;
            background: transparent;
            border-radius: 8px;
            color: #64748b;
            font-weight: 500;
            border: none;
            transition: all 0.3s ease;
            padding: 0 1.5rem;
            font-size: 1rem;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            font-weight: 600;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render application header with status"""
        name_service_status = self.validation_service.is_name_validation_available() if self.validation_service else False
        address_service_status = self.validation_service.is_address_validation_available() if self.validation_service else False
        
        st.markdown('''
        <div class="enterprise-header">
            <div class="main-title">Enterprise Validator</div>
            <div class="subtitle">Professional Name & Address Validation Platform</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            status_html = ""
            if name_service_status:
                status_html += '<span class="status-indicator status-success">✓ Name Validation Ready</span>'
            else:
                status_html += '<span class="status-indicator status-warning">⚠ Name Service Unavailable</span>'
            
            if address_service_status:
                status_html += '<span class="status-indicator status-success">✓ Address Validation Ready</span>'
            else:
                status_html += '<span class="status-indicator status-warning">⚠ USPS API Not Configured</span>'
            
            st.markdown(f'<div style="text-align: center;">{status_html}</div>', unsafe_allow_html=True)
    
    def render_name_validation_tab(self):
        """Render name validation functionality"""
        st.markdown("## 👤 Name Validation Services")
        
        # Sub-tabs for single and multi-file validation
        single_tab, multi_tab = st.tabs(["Single Name", "Multi-File Processing"])
        
        with single_tab:
            self._render_single_name_validation()
        
        with multi_tab:
            self._render_multi_file_name_validation()
    
    def _render_single_name_validation(self):
        """Render single name validation"""
        st.markdown("### Single Name Validation")
        
        with st.form("single_name_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", placeholder="Enter first name")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Enter last name")
            
            submit_button = st.form_submit_button("🔍 Validate Name", type="primary")
            
            if submit_button and first_name.strip() and last_name.strip():
                self._process_single_name_validation(first_name, last_name)
    
    def _process_single_name_validation(self, first_name: str, last_name: str):
        """Process single name validation"""
        if not self.validation_service or not self.validation_service.is_name_validation_available():
            st.error("❌ Name validation service unavailable")
            return
        
        try:
            with st.spinner("🔄 Validating name..."):
                result = self.validation_service.name_validator.validate(first_name, last_name)
                
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
                
                # Show detailed results
                if result.get('analysis'):
                    with st.expander("📊 Detailed Analysis"):
                        analysis = result['analysis']
                        
                        if 'first_name' in analysis:
                            first_info = analysis['first_name']
                            st.write(f"**First Name:** {'Common' if first_info.get('is_common') else 'Uncommon'}")
                        
                        if 'last_name' in analysis:
                            last_info = analysis['last_name']
                            st.write(f"**Last Name:** {'Common' if last_info.get('is_common') else 'Uncommon'}")
                
                # Show suggestions if available
                if result.get('suggestions'):
                    with st.expander("💡 Name Suggestions"):
                        suggestions = result['suggestions']
                        
                        if 'first_name' in suggestions and suggestions['first_name']:
                            st.write("**First Name Suggestions:**")
                            for suggestion in suggestions['first_name'][:3]:
                                st.write(f"- {suggestion['suggestion']} ({suggestion['confidence']:.1%})")
                        
                        if 'last_name' in suggestions and suggestions['last_name']:
                            st.write("**Last Name Suggestions:**")
                            for suggestion in suggestions['last_name'][:3]:
                                st.write(f"- {suggestion['suggestion']} ({suggestion['confidence']:.1%})")
                
        except Exception as e:
            st.error(f"❌ Validation error: {str(e)}")
    
    def _render_multi_file_name_validation(self):
        """Render multi-file name validation"""
        st.markdown("### Multi-File Name Processing")
        
        uploaded_files = st.file_uploader(
            "Choose CSV files",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV files containing names"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            if st.button("🚀 Process Names", type="primary"):
                self._process_multi_file_names(uploaded_files)
    
    def _process_multi_file_names(self, uploaded_files):
        """Process multiple files for name validation"""
        try:
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Processing names..."):
                # Simple processing - just parse names from the first few columns
                all_results = []
                
                for df, filename in file_data_list:
                    # Try to find name columns
                    name_cols = [col for col in df.columns if any(name_word in col.lower() 
                                for name_word in ['name', 'first', 'last', 'fname', 'lname'])]
                    
                    if len(name_cols) >= 2:
                        first_col, last_col = name_cols[0], name_cols[1]
                        
                        for idx, row in df.head(10).iterrows():  # Process first 10 rows
                            first_name = str(row[first_col]).strip()
                            last_name = str(row[last_col]).strip()
                            
                            if first_name and last_name and first_name != 'nan' and last_name != 'nan':
                                result = self.validation_service.name_validator.validate(first_name, last_name)
                                all_results.append({
                                    'file': filename,
                                    'row': idx + 1,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'status': 'Valid' if result['valid'] else 'Invalid',
                                    'confidence': f"{result['confidence']:.1%}"
                                })
                
                if all_results:
                    st.markdown("### 📊 Processing Results")
                    results_df = pd.DataFrame(all_results)
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download option
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results",
                        data=csv,
                        file_name=f"name_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No valid names found in the uploaded files")
                    
        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")
    
    def render_address_validation_tab(self):
        """Render address validation functionality"""
        st.markdown("## 🏠 Address Validation Services")
        
        if not self.validation_service or not self.validation_service.is_address_validation_available():
            st.warning("⚠️ **USPS API Not Configured**")
            st.write("Address validation requires USPS API credentials.")
            st.write("Create a `.env` file with:")
            st.code("USPS_CLIENT_ID=your_client_id\nUSPS_CLIENT_SECRET=your_client_secret")
            return
        
        # Sub-tabs for single and multi-file validation
        single_tab, multi_tab = st.tabs(["Single Address", "Multi-File Processing"])
        
        with single_tab:
            self._render_single_address_validation()
        
        with multi_tab:
            self._render_multi_file_address_validation()
    
    def _render_single_address_validation(self):
        """Render single address validation"""
        st.markdown("### Single Address Validation")
        
        with st.form("single_address_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", placeholder="Enter first name")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Enter last name")
            
            street_address = st.text_input("Street Address", placeholder="123 Main Street")
            
            col3, col4, col5 = st.columns([3, 1, 2])
            
            with col3:
                city = st.text_input("City", placeholder="New York")
            
            with col4:
                state = st.text_input("State", placeholder="NY", max_chars=2)
            
            with col5:
                zip_code = st.text_input("ZIP Code", placeholder="10001")
            
            submit_button = st.form_submit_button("🔍 Validate Address", type="primary")
            
            if submit_button:
                if all([first_name.strip(), last_name.strip(), street_address.strip(), 
                       city.strip(), state.strip(), zip_code.strip()]):
                    self._process_single_address_validation(
                        first_name, last_name, street_address, city, state, zip_code
                    )
                else:
                    st.error("Please fill in all fields")
    
    def _process_single_address_validation(self, first_name, last_name, street_address, city, state, zip_code):
        """Process single address validation"""
        try:
            with st.spinner("🔄 Validating address with USPS..."):
                result = self.validation_service.validate_single_record(
                    first_name, last_name, street_address, city, state, zip_code
                )
                
                st.markdown("### 🎉 Address Validation Results")
                
                # Status overview
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    overall_status = "✅ Valid" if result['overall_valid'] else "❌ Invalid"
                    st.metric("Overall Status", overall_status)
                
                with col2:
                    address_result = result.get('address_result', {})
                    deliverable = address_result.get('deliverable', False)
                    address_status = "✅ Deliverable" if deliverable else "❌ Not Deliverable"
                    st.metric("Address Status", address_status)
                
                with col3:
                    confidence = result.get('overall_confidence', 0)
                    st.metric("Confidence", f"{confidence:.1%}")
                
                # Show standardized address if available
                if address_result.get('standardized'):
                    standardized = address_result['standardized']
                    st.markdown("### 📮 USPS Standardized Address")
                    st.success(f"""
                    **{standardized['street_address']}**  
                    **{standardized['city']}, {standardized['state']} {standardized['zip_code']}**
                    """)
                
        except Exception as e:
            st.error(f"❌ Validation error: {str(e)}")
    
    def _render_multi_file_address_validation(self):
        """Render multi-file address validation"""
        st.markdown("### Multi-File Address Processing")
        
        uploaded_files = st.file_uploader(
            "Choose CSV files",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload CSV files containing addresses",
            key="address_upload"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            if st.button("🚀 Process Addresses", type="primary"):
                self._process_multi_file_addresses(uploaded_files)
    
    def _process_multi_file_addresses(self, uploaded_files):
        """Process multiple files for address validation"""
        try:
            file_data_list = []
            for uploaded_file in uploaded_files:
                df = pd.read_csv(uploaded_file)
                file_data_list.append((df, uploaded_file.name))
            
            with st.spinner("🔄 Processing addresses..."):
                all_results = []
                
                for df, filename in file_data_list:
                    # Try to find address columns
                    addr_cols = [col for col in df.columns if any(addr_word in col.lower() 
                                for addr_word in ['address', 'street', 'city', 'state', 'zip'])]
                    
                    if len(addr_cols) >= 4:  # Need at least street, city, state, zip
                        for idx, row in df.head(5).iterrows():  # Process first 5 rows
                            try:
                                # Simple column mapping
                                street = str(row[addr_cols[0]])
                                city = str(row[addr_cols[1]]) if len(addr_cols) > 1 else ""
                                state = str(row[addr_cols[2]]) if len(addr_cols) > 2 else ""
                                zip_code = str(row[addr_cols[3]]) if len(addr_cols) > 3 else ""
                                
                                if all([street, city, state, zip_code]) and all(x != 'nan' for x in [street, city, state, zip_code]):
                                    address_data = {
                                        'street_address': street,
                                        'city': city,
                                        'state': state,
                                        'zip_code': zip_code
                                    }
                                    
                                    result = self.validation_service.address_validator.validate_address(address_data)
                                    
                                    all_results.append({
                                        'file': filename,
                                        'row': idx + 1,
                                        'original_address': f"{street}, {city}, {state} {zip_code}",
                                        'deliverable': result.get('deliverable', False),
                                        'status': 'Valid' if result.get('success') and result.get('deliverable') else 'Invalid'
                                    })
                            except Exception as e:
                                continue
                
                if all_results:
                    st.markdown("### 📊 Processing Results")
                    results_df = pd.DataFrame(all_results)
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download option
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results",
                        data=csv,
                        file_name=f"address_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No valid addresses found in the uploaded files")
                    
        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")
    
    def render_monitoring_tab(self):
        """Render monitoring functionality"""
        st.markdown("## 📊 System Monitoring")
        
        # Simple system status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Name Service", "✅ Available" if self.validation_service and self.validation_service.is_name_validation_available() else "❌ Unavailable")
        
        with col2:
            st.metric("Address Service", "✅ Available" if self.validation_service and self.validation_service.is_address_validation_available() else "❌ Unavailable")
        
        with col3:
            uptime = datetime.now() - st.session_state.get('app_start_time', datetime.now())
            st.metric("Uptime", f"{int(uptime.total_seconds() / 60)} min")
        
        # Show recent logs if available
        if hasattr(self.logger, 'logs') and self.logger.logs:
            st.markdown("### 📝 Recent Activity")
            recent_logs = self.logger.logs[-10:]  # Last 10 logs
            
            for log in recent_logs:
                timestamp = log['timestamp'].strftime("%H:%M:%S")
                level_color = {"INFO": "🔵", "WARNING": "🟡", "ERROR": "🔴"}.get(log['level'], "⚪")
                st.write(f"`{timestamp}` {level_color} **{log['category']}**: {log['message']}")
        else:
            st.info("No recent activity to display")
    
    def run(self):
        """Main application entry point"""
        # Initialize session state
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = datetime.now()
        
        # Configure page
        st.set_page_config(
            page_title="Enterprise Name & Address Validator",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply styling
        self.apply_enterprise_styling()
        
        # Render header
        self.render_header()
        
        # Main tabs
        name_tab, address_tab, monitoring_tab = st.tabs([
            "👤 Name Validation", 
            "🏠 Address Validation", 
            "📊 Monitoring"
        ])
        
        with name_tab:
            self.render_name_validation_tab()
        
        with address_tab:
            self.render_address_validation_tab()
        
        with monitoring_tab:
            self.render_monitoring_tab()


def main():
    """Application entry point"""
    app = EnterpriseValidatorApp()
    app.run()


if __name__ == "__main__":
    main()