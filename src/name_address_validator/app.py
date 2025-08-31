# src/name_address_validator/app.py
"""
Complete Working Enterprise Name & Address Validator - Main Application
UPDATED to use NameValidatorTab component with API functionality
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

# Import services and components
try:
    from name_address_validator.services.validation_service import ValidationService
    from name_address_validator.utils.config import load_usps_credentials
    from name_address_validator.utils.logger import AppLogger
    
    # Import the tab components
    from name_address_validator.components.name_validator_tab import NameValidatorTab
    from name_address_validator.components.address_validator_tab import AddressValidatorTab
    from name_address_validator.components.monitoring_tab import MonitoringTab
    
    COMPONENTS_AVAILABLE = True
    
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error("Please ensure all components are properly installed")
    COMPONENTS_AVAILABLE = False


class EnterpriseValidatorApp:
    """Main application class for enterprise validator"""
    
    def __init__(self):
        self.logger = AppLogger()
        self.validation_service = None
        
        # Initialize tab components
        self.name_validator_tab = None
        self.address_validator_tab = None
        self.monitoring_tab = None
        
        self._initialize_services()
        self._initialize_components()
    
    def _initialize_services(self):
        """Initialize core services"""
        try:
            self.validation_service = ValidationService(debug_callback=self.logger.log)
            self.logger.log("✅ Validation services initialized", "SYSTEM")
        except Exception as e:
            self.logger.log(f"❌ Failed to initialize services: {e}", "SYSTEM", level="ERROR")
            st.error(f"Service initialization failed: {e}")
    
    def _initialize_components(self):
        """Initialize tab components"""
        if not COMPONENTS_AVAILABLE or not self.validation_service:
            self.logger.log("❌ Cannot initialize components - missing dependencies", "SYSTEM", level="ERROR")
            return
        
        try:
            # Initialize tab components
            self.name_validator_tab = NameValidatorTab(self.validation_service, self.logger)
            self.address_validator_tab = AddressValidatorTab(self.validation_service, self.logger)
            self.monitoring_tab = MonitoringTab(self.logger)
            
            self.logger.log("✅ Tab components initialized", "SYSTEM")
        except Exception as e:
            self.logger.log(f"❌ Failed to initialize components: {e}", "SYSTEM", level="ERROR")
            st.error(f"Component initialization failed: {e}")
    
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
        
        /* Validation card styling */
        .validation-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e40af;
            margin-bottom: 1rem;
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
            <div class="subtitle">Professional Name & Address Validation Platform with API Testing</div>
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
        """Render name validation functionality using the component"""
        if self.name_validator_tab and COMPONENTS_AVAILABLE:
            # Use the component which now includes API testing
            self.name_validator_tab.render()
        else:
            # Fallback implementation if components not available
            st.error("❌ Name Validation component not available")
            st.info("Please ensure all components are properly installed and configured")
            
            # Show basic debug info
            if self.validation_service:
                st.write("**Service Status:**")
                st.write(f"- Name validation available: {self.validation_service.is_name_validation_available()}")
                st.write(f"- Components available: {COMPONENTS_AVAILABLE}")
    
    def render_address_validation_tab(self):
        """Render address validation functionality using the component"""
        if self.address_validator_tab and COMPONENTS_AVAILABLE:
            self.address_validator_tab.render()
        else:
            # Fallback implementation
            st.error("❌ Address Validation component not available")
            st.info("Please ensure all components are properly installed and configured")
    
    def render_monitoring_tab(self):
        """Render monitoring functionality using the component"""
        if self.monitoring_tab and COMPONENTS_AVAILABLE:
            self.monitoring_tab.render()
        else:
            # Fallback implementation
            st.markdown("## 📊 System Monitoring")
            
            # Simple system status
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name_status = "✅ Available" if (self.validation_service and 
                                                self.validation_service.is_name_validation_available()) else "❌ Unavailable"
                st.metric("Name Service", name_status)
            
            with col2:
                addr_status = "✅ Available" if (self.validation_service and 
                                               self.validation_service.is_address_validation_available()) else "❌ Unavailable"
                st.metric("Address Service", addr_status)
            
            with col3:
                uptime = datetime.now() - st.session_state.get('app_start_time', datetime.now())
                st.metric("Uptime", f"{int(uptime.total_seconds() / 60)} min")
            
            # Component status
            st.markdown("### 🔧 Component Status")
            st.write(f"- Components Available: {'✅' if COMPONENTS_AVAILABLE else '❌'}")
            st.write(f"- Validation Service: {'✅' if self.validation_service else '❌'}")
            st.write(f"- Name Validator Tab: {'✅' if self.name_validator_tab else '❌'}")
            st.write(f"- Address Validator Tab: {'✅' if self.address_validator_tab else '❌'}")
            st.write(f"- Monitoring Tab: {'✅' if self.monitoring_tab else '❌'}")
    
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
        
        # Debug info (can be removed in production)
        if st.checkbox("🔧 Show Debug Info", value=False):
            st.write("**Debug Information:**")
            st.write(f"- Components Available: {COMPONENTS_AVAILABLE}")
            st.write(f"- Validation Service: {self.validation_service is not None}")
            st.write(f"- Name Validator Tab: {self.name_validator_tab is not None}")
            st.write(f"- Address Validator Tab: {self.address_validator_tab is not None}")
            st.write(f"- Monitoring Tab: {self.monitoring_tab is not None}")
        
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
    try:
        app = EnterpriseValidatorApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application failed to start: {str(e)}")
        st.error("Please check your installation and configuration")
        
        # Show debug info
        st.write("**Debug Information:**")
        st.write(f"- Components Available: {COMPONENTS_AVAILABLE}")
        st.code(str(e))


if __name__ == "__main__":
    main()