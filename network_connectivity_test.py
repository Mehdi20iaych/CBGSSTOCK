#!/usr/bin/env python3
"""
Network Connectivity Test - Focused test to verify NetworkError resolution
"""

import requests
import json
import sys

class NetworkConnectivityTester:
    def __init__(self, base_url="https://1471fe46-cff7-448e-b32d-2e138d2a26fd.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def test_endpoint(self, name, method, endpoint, expected_status=200, data=None):
        """Test a single endpoint for connectivity"""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == expected_status:
                self.tests_passed += 1
                print(f"✅ PASSED - No NetworkError, API responding correctly")
                try:
                    response_data = response.json()
                    print(f"Response preview: {json.dumps(response_data, indent=2)[:300]}...")
                except:
                    print("Response received (non-JSON)")
                return True
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error response: {error_data}")
                except:
                    print(f"Error text: {response.text[:200]}...")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ NETWORK ERROR - Connection failed: {str(e)}")
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ TIMEOUT ERROR - Request timed out: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR - {str(e)}")
            return False

    def run_connectivity_tests(self):
        """Run focused connectivity tests"""
        print("🚀 NETWORK CONNECTIVITY TEST - Verifying NetworkError Resolution")
        print("=" * 80)
        
        # Test 1: Health check
        self.test_endpoint("Health Check", "GET", "")
        
        # Test 2: Sessions endpoint (basic API functionality)
        self.test_endpoint("Sessions Endpoint", "GET", "api/sessions")
        
        # Test 3: Calculate endpoint (should fail gracefully without data)
        self.test_endpoint("Calculate Endpoint (No Data)", "POST", "api/calculate", 
                          expected_status=400, data={"days": 10})
        
        # Test 4: Upload endpoint (should fail gracefully without file)
        self.test_endpoint("Upload Endpoint (No File)", "POST", "api/upload-commandes-excel", 
                          expected_status=422)  # FastAPI validation error
        
        print("\n" + "=" * 80)
        print("📊 NETWORK CONNECTIVITY TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL CONNECTIVITY TESTS PASSED - NetworkError issue resolved!")
            print("✅ Backend is accessible and responding correctly")
            return True
        else:
            print("❌ Some connectivity tests failed - NetworkError may still exist")
            return False

if __name__ == "__main__":
    tester = NetworkConnectivityTester()
    success = tester.run_connectivity_tests()
    sys.exit(0 if success else 1)