import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class StockManagementAPITester:
    def __init__(self, base_url="https://eabf8c0a-1917-4652-8fff-4d0ad3bb851e.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        # Don't set Content-Type for file uploads
        if not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error response: {error_data}")
                except:
                    print(f"Error text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_sample_excel_file(self):
        """Create a sample Excel file for testing"""
        # Create sample data with required columns
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10)
            ],
            'Article': ['ART001', 'ART002', 'ART001', 'ART003', 'ART002'],
            'Désignation Article': ['COCA-COLA 33CL', 'PEPSI 50CL', 'COCA-COLA 33CL', 'SPRITE 33CL', 'PEPSI 50CL'],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B'],
            'Quantité Commandée': [100, 150, 80, 120, 90],
            'Stock Utilisation Libre': [500, 300, 200, 400, 250],
            'Ecart': [0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Pet', 'Pet'],
            'Quantité en Palette': [24, 12, 24, 12, 12]
        }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_upload_excel(self):
        """Test Excel file upload"""
        excel_file = self.create_sample_excel_file()
        
        files = {
            'file': ('test_stock_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Excel File",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            print(f"Session ID: {self.session_id}")
            return True
        return False

    def test_calculate_requirements(self):
        """Test calculation endpoint"""
        if not self.session_id:
            print("❌ No session ID available for calculation test")
            return False
            
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Calculate Requirements",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        return success

    def test_get_filters(self):
        """Test get filters endpoint"""
        if not self.session_id:
            print("❌ No session ID available for filters test")
            return False
            
        success, response = self.run_test(
            "Get Available Filters",
            "GET",
            f"api/filters/{self.session_id}",
            200
        )
        return success

    def test_calculate_with_filters(self):
        """Test calculation with array filters"""
        if not self.session_id:
            print("❌ No session ID available for filtered calculation test")
            return False
            
        calculation_data = {
            "days": 15,
            "product_filter": ["COCA-COLA 33CL", "PEPSI 50CL"],
            "packaging_filter": ["Verre", "Pet"]
        }
        
        success, response = self.run_test(
            "Calculate Requirements with Array Filters",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        return success

    def test_gemini_query_french(self):
        """Test Gemini AI query endpoint with French query"""
        if not self.session_id:
            print("❌ No session ID available for Gemini query test")
            return False
            
        query_data = {
            "query": "Quels sont les 3 produits avec la plus forte consommation?",
            "session_id": self.session_id
        }
        
        success, response = self.run_test(
            "Gemini AI Query (French)",
            "POST",
            f"api/gemini-query/{self.session_id}",
            200,
            data=query_data
        )
        return success

    def test_invalid_session_id(self):
        """Test with invalid session ID"""
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Invalid Session ID",
            "POST",
            "api/calculate/invalid-session-id",
            404,
            data=calculation_data
        )
        # For this test, success means we got the expected 404 error
        return success

    def test_invalid_file_upload(self):
        """Test uploading invalid file"""
        # Create a text file instead of Excel
        text_content = "This is not an Excel file"
        files = {
            'file': ('test.txt', io.StringIO(text_content), 'text/plain')
        }
        
        success, response = self.run_test(
            "Invalid File Upload",
            "POST",
            "api/upload-excel",
            400,
            files=files
        )
        return success

def main():
    print("🚀 Starting Stock Management API Tests")
    print("=" * 50)
    
    # Setup
    tester = StockManagementAPITester()
    
    # Run tests in sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Upload Excel File", tester.test_upload_excel),
        ("Get Available Filters", tester.test_get_filters),
        ("Calculate Requirements", tester.test_calculate_requirements),
        ("Calculate with Array Filters", tester.test_calculate_with_filters),
        ("Gemini AI Query (French)", tester.test_gemini_query_french),
        ("Invalid Session ID", tester.test_invalid_session_id),
        ("Invalid File Upload", tester.test_invalid_file_upload),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())