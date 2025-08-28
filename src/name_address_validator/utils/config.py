import os
import streamlit as st
from typing import Tuple, Optional


def load_usps_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load USPS credentials from secrets or environment with debug logging"""
    
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets'):
            client_id = st.secrets.get("USPS_CLIENT_ID", "")
            client_secret = st.secrets.get("USPS_CLIENT_SECRET", "")
            if client_id and client_secret:
                print("✅ USPS credentials loaded from Streamlit secrets")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠️ Failed to load from Streamlit secrets: {str(e)}")
    
    # Try environment variables
    client_id = os.getenv('USPS_CLIENT_ID', '')
    client_secret = os.getenv('USPS_CLIENT_SECRET', '')
    
    if client_id and client_secret:
        print("✅ USPS credentials loaded from environment variables")
        return client_id, client_secret
    
    print("❌ USPS credentials not found in secrets or environment")
    return None, None


def get_app_config() -> dict:
    """Get application configuration settings"""
    return {
        'max_batch_records': 500,
        'validation_timeout': 30,
        'max_suggestions': 5,
        'enable_debug_logging': True,
        'performance_tracking': True
    }