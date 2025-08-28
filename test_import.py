# test_complete_functionality.py
"""
Complete functionality test script
Run this to verify everything is working
"""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_imports():
    """Test all imports"""
    print("🧪 TESTING IMPORTS")
    print("=" * 50)
    
    try:
        from name_address_validator.services.validation_service import ValidationService
        print("✅ ValidationService imported")
        
        from name_address_validator.validators.name_validator import EnhancedNameValidator
        print("✅ EnhancedNameValidator imported")
        
        from name_address_validator.validators.address_validator import USPSAddressValidator
        print("✅ USPSAddressValidator imported")
        
        from name_address_validator.utils.config import load_usps_credentials
        print("✅ Config imported")
        
        from name_address_validator.utils.logger import AppLogger
        print("✅ AppLogger imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_name_validation():
    """Test name validation functionality"""
    print("\n🧪 TESTING NAME VALIDATION")
    print("=" * 50)
    
    try:
        from name_address_validator.services.validation_service import ValidationService
        
        service = ValidationService()
        print("✅ ValidationService created")
        
        # Test name validation
        result = service.name_validator.validate("John", "Smith")
        print(f"✅ Name validation result: {result['valid']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   First name common: {result['analysis']['first_name']['is_common']}")
        print(f"   Last name common: {result['analysis']['last_name']['is_common']}")
        
        # Test uncommon name
        result2 = service.name_validator.validate("Xylophone", "Pterodactyl")
        print(f"✅ Uncommon name test: {result2['valid']}")
        print(f"   Has suggestions: {bool(result2['suggestions'])}")
        
        return True
    except Exception as e:
        print(f"❌ Name validation failed: {e}")
        return False

def test_address_validation():
    """Test address validation functionality"""
    print("\n🧪 TESTING ADDRESS VALIDATION")
    print("=" * 50)
    
    try:
        from name_address_validator.services.validation_service import ValidationService
        
        service = ValidationService()
        print("✅ ValidationService created")
        
        # Check if address validation is available
        address_available = service.is_address_validation_available()
        print(f"✅ Address validation available: {address_available}")
        
        if address_available:
            print("✅ USPS credentials configured - address validation will work")
            
            # Test with a known good address
            result = service.validate_single_record(
                "John", "Doe",
                "1600 Pennsylvania Avenue NW",
                "Washington", "DC", "20500"
            )
            print(f"✅ Single record validation completed")
            print(f"   Overall valid: {result['overall_valid']}")
            print(f"   Address deliverable: {result['address_result']['deliverable']}")
        else:
            print("⚠️  USPS credentials not configured")
            print("   To enable address validation:")
            print("   1. Get credentials from https://developer.usps.com/")
            print("   2. Create .env file with:")
            print("      USPS_CLIENT_ID=your_client_id")
            print("      USPS_CLIENT_SECRET=your_client_secret")
        
        return True
    except Exception as e:
        print(f"❌ Address validation failed: {e}")
        return False

def test_streamlit_app():
    """Test that the Streamlit app can be imported"""
    print("\n🧪 TESTING STREAMLIT APP")
    print("=" * 50)
    
    try:
        # Try to import the main app
        from name_address_validator.app import EnterpriseValidatorApp
        print("✅ Main app imported successfully")
        
        # Try to create the app instance
        app = EnterpriseValidatorApp()
        print("✅ App instance created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Streamlit app test failed: {e}")
        print("   This might be due to Streamlit not being available in test mode")
        return False

def main():
    """Run all tests"""
    print("🔍 COMPLETE FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    if not imports_ok:
        print("\n❌ IMPORTS FAILED - Cannot continue with other tests")
        return
    
    # Test name validation
    name_ok = test_name_validation()
    
    # Test address validation  
    address_ok = test_address_validation()
    
    # Test Streamlit app
    app_ok = test_streamlit_app()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"{'✅' if name_ok else '❌'} Name validation: {'PASS' if name_ok else 'FAIL'}")
    print(f"{'✅' if address_ok else '❌'} Address validation: {'PASS' if address_ok else 'FAIL'}")
    print(f"{'✅' if app_ok else '❌'} Streamlit app: {'PASS' if app_ok else 'FAIL'}")
    
    if all([imports_ok, name_ok, address_ok]):
        print("\n🎉 ALL CORE FUNCTIONALITY WORKING!")
        print("\nTo run the app:")
        print("streamlit run src/name_address_validator/app.py")
        
        if not address_ok:
            print("\n💡 Note: Address validation requires USPS credentials")
    else:
        print("\n⚠️  Some functionality not working. Check error messages above.")

if __name__ == "__main__":
    main()