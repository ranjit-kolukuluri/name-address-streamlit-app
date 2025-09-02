# test_api.py
"""
Test script for Name Validation API
Run this to verify your API is working correctly
"""

import requests
import json
import time
import sys

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check passed")
            print(f"   Status: {result['status']}")
            print(f"   Validation Available: {result['validation_available']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_service_status():
    """Test the service status endpoint"""
    print("\n🔍 Testing service status endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Service status retrieved")
            print(f"   Name Validation: {result['service_status']['name_validation_available']}")
            print(f"   Dictionary Support: {result['service_status']['dictionary_support']}")
            return True
        else:
            print(f"❌ Service status failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Service status failed: {e}")
        return False

def test_single_name_validation():
    """Test single name validation"""
    print("\n🔍 Testing single name validation...")
    
    payload = {
        "records": [
            {
                "uniqueid": "test_001",
                "name": "John Michael Smith",
                "gender": "",
                "party_type": "I",
                "parseInd": "Y"
            },
            {
                "uniqueid": "test_002",
                "name": "ABC Technology Solutions LLC",
                "gender": "",
                "party_type": "O",
                "parseInd": "N"
            },
            {
                "uniqueid": "test_003",
                "name": "Mary Johnson-Williams",
                "gender": "F",
                "party_type": "",
                "parseInd": "Y"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/validate-names", 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Name validation successful")
            print(f"   Processed: {result['processed_count']} records")
            print(f"   Successful: {result['successful_count']} records")
            print(f"   Processing time: {result['processing_time_ms']}ms")
            
            # Show sample results
            print("\n📊 Sample Results:")
            for i, record in enumerate(result['results'][:2]):  # Show first 2
                print(f"   Record {i+1}: {record['uniqueid']}")
                print(f"     Name: {record['name']}")
                print(f"     Status: {record['validation_status']}")
                print(f"     Confidence: {record['confidence_score']:.2f}")
                print(f"     Party Type: {record['party_type']}")
                if record['parsed_components'].get('first_name'):
                    print(f"     Parsed: {record['parsed_components']['first_name']} {record['parsed_components']['last_name']}")
                if record['suggestions'].get('gender_prediction'):
                    print(f"     Gender: {record['suggestions']['gender_prediction']}")
            
            return True
        else:
            print(f"❌ Name validation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Name validation failed: {e}")
        return False

def test_csv_processing():
    """Test CSV processing (create a small test file)"""
    print("\n🔍 Testing CSV processing...")
    
    # Create test CSV content
    csv_content = """uniqueid,name,gender,party_type,parseInd
001,John Smith,,I,Y
002,Jane Doe,F,,Y
003,Microsoft Corporation,,O,N
004,Dr. Robert Johnson Jr.,,I,Y"""
    
    # Save to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Upload CSV file
        with open(csv_file_path, 'rb') as f:
            files = {'file': f}
            data = {'max_records': 10, 'include_suggestions': True}
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/validate-csv-upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result['job_id']
            print("✅ CSV upload successful")
            print(f"   Job ID: {job_id}")
            print(f"   Status URL: {result['check_status_url']}")
            
            # Poll for job completion (with timeout)
            max_attempts = 30  # 30 seconds max
            for attempt in range(max_attempts):
                status_response = requests.get(f"{API_BASE_URL}/api/v1/job/{job_id}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   Status: {status['status']} - Progress: {status['progress']:.1%}")
                    
                    if status['status'] == 'completed':
                        print("✅ CSV processing completed")
                        print(f"   Processed: {status['processed_count']} records")
                        return True
                    elif status['status'] == 'failed':
                        print(f"❌ CSV processing failed: {status.get('error_message', 'Unknown error')}")
                        return False
                
                time.sleep(1)  # Wait 1 second
            
            print("⚠️ CSV processing timeout (still running)")
            return False
        else:
            print(f"❌ CSV upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ CSV processing failed: {e}")
        return False
    finally:
        # Clean up temp file
        import os
        try:
            os.unlink(csv_file_path)
        except:
            pass

def main():
    """Run all tests"""
    print("🧪 Name Validation API Test Suite")
    print("=" * 50)
    
    # Check if API server is running
    print(f"Testing API at: {API_BASE_URL}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Service Status", test_service_status),
        ("Single Name Validation", test_single_name_validation),
        ("CSV Processing", test_csv_processing)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed / (passed + failed) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your API is working correctly.")
        print(f"📖 API Documentation: {API_BASE_URL}/docs")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("1. Make sure the API server is running: ./start_api.sh")
        print("2. Check the server logs for errors")
        print("3. Verify your dictionary files are in place")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)