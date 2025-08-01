import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class StockManagementAPITester:
    def __init__(self, base_url="https://83758c24-bcda-4a92-895c-e1aff3c57fe0.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.inventory_session_id = None
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

    def create_sample_inventory_excel_file(self):
        """Create a sample inventory Excel file for testing"""
        # Create sample inventory data with required columns
        inventory_data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005', 'ART006', 'ART007'],
            'Désignation article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE',
                'COCA-COLA ZERO 33CL PET',
                'PEPSI MAX 50CL PET'
            ],
            'STOCK À DATE': [1500, 800, 600, 1200, 300, 900, 450]
        }
        
        df = pd.DataFrame(inventory_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def create_sample_excel_file(self):
        """Create a sample Excel file for testing with various packaging types"""
        # Create sample data with required columns including non-allowed packaging types
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5),
                datetime.now() - timedelta(days=2)
            ],
            'Article': ['ART001', 'ART002', 'ART001', 'ART003', 'ART002', 'ART004', 'ART005'],
            'Désignation Article': ['COCA-COLA 33CL', 'PEPSI 50CL', 'COCA-COLA 33CL', 'SPRITE 33CL', 'PEPSI 50CL', 'FANTA 33CL', 'ORANGINA 25CL'],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT3'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B', 'Division C', 'Division A'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200, 75],
            'Stock Utilisation Libre': [500, 300, 200, 400, 250, 600, 180],
            'Ecart': [0, 0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Ciel', 'Pet', 'Canette', 'Tétra'],  # Mix of allowed and non-allowed types
            'Quantité en Palette': [24, 12, 24, 18, 12, 36, 20]
        }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def use_sample_excel_file(self):
        """Use the existing sample_stock_data.xlsx file"""
        try:
            with open('/app/sample_stock_data.xlsx', 'rb') as f:
                return io.BytesIO(f.read())
        except FileNotFoundError:
            print("⚠️ sample_stock_data.xlsx not found, using generated sample")
            return self.create_sample_excel_file()

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
        excel_file = self.use_sample_excel_file()
        
        files = {
            'file': ('sample_stock_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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

    def test_packaging_filter_enhancement(self):
        """Test that packaging filter only returns allowed types (verre, pet, ciel)"""
        if not self.session_id:
            print("❌ No session ID available for packaging filter test")
            return False
            
        success, response = self.run_test(
            "Packaging Filter Enhancement",
            "GET",
            f"api/filters/{self.session_id}",
            200
        )
        
        if success and 'packaging' in response:
            packaging_types = [pkg['value'] for pkg in response['packaging']]
            allowed_types = ['Verre', 'Pet', 'Ciel']
            
            print(f"📋 Found packaging types: {packaging_types}")
            
            # Check that only allowed types are returned
            invalid_types = [pkg for pkg in packaging_types if pkg not in allowed_types]
            if invalid_types:
                print(f"❌ Found non-allowed packaging types: {invalid_types}")
                return False
            
            # Check that all returned types are from the allowed list
            valid_types_found = [pkg for pkg in packaging_types if pkg in allowed_types]
            print(f"✅ Valid packaging types found: {valid_types_found}")
            
            # Verify display names are present
            for pkg in response['packaging']:
                if 'display' not in pkg:
                    print(f"❌ Missing display name for packaging type: {pkg}")
                    return False
                print(f"📦 {pkg['value']} -> {pkg['display']}")
            
            return True
        
        print("❌ No packaging data found in response")
        return False

    def test_upload_inventory_excel(self):
        """Test inventory Excel file upload"""
        inventory_file = self.create_sample_inventory_excel_file()
        
        files = {
            'file': ('sample_inventory_data.xlsx', inventory_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Inventory Excel File",
            "POST",
            "api/upload-inventory-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.inventory_session_id = response['session_id']
            print(f"Inventory Session ID: {self.inventory_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'records_count', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in response: {field}")
                    return False
            
            # Verify summary structure
            summary = response['summary']
            summary_fields = ['divisions', 'articles_count', 'total_stock', 'records_count']
            for field in summary_fields:
                if field not in summary:
                    print(f"❌ Missing required field in summary: {field}")
                    return False
            
            print(f"✅ Inventory upload successful with {response['records_count']} records")
            print(f"✅ Total stock: {summary['total_stock']} units")
            print(f"✅ Articles count: {summary['articles_count']}")
            return True
        return False

    def test_upload_inventory_excel_missing_columns(self):
        """Test inventory Excel upload with missing required columns"""
        # Create invalid inventory data missing required columns
        invalid_data = {
            'Division': ['M210', 'M210'],
            'Article': ['ART001', 'ART002'],
            # Missing 'Désignation article' and 'STOCK À DATE'
        }
        
        df = pd.DataFrame(invalid_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_inventory.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Invalid Inventory Excel (Missing Columns)",
            "POST",
            "api/upload-inventory-excel",
            400,
            files=files
        )
        
        # Success here means we got the expected 400 error
        return success

    def test_get_inventory_data(self):
        """Test inventory data retrieval endpoint"""
        if not self.inventory_session_id:
            print("❌ No inventory session ID available for inventory data test")
            return False
            
        success, response = self.run_test(
            "Get Inventory Data",
            "GET",
            f"api/inventory/{self.inventory_session_id}",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['data', 'upload_time', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in inventory response: {field}")
                    return False
            
            print(f"✅ Retrieved inventory data with {len(response['data'])} records")
            return True
        return False

    def test_get_inventory_data_invalid_session(self):
        """Test inventory data retrieval with invalid session ID"""
        success, response = self.run_test(
            "Get Inventory Data (Invalid Session)",
            "GET",
            "api/inventory/invalid-session-id",
            404
        )
        # Success means we got the expected 404 error
        return success

    def test_enhanced_calculate_with_inventory(self):
        """Test enhanced calculation with inventory cross-reference"""
        if not self.session_id or not self.inventory_session_id:
            print("❌ Missing session IDs for enhanced calculation test")
            return False
            
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Inventory Cross-Reference",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['calculations', 'summary', 'inventory_status']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in enhanced calculation response: {field}")
                    return False
            
            # Verify inventory status fields in calculations
            calculations = response['calculations']
            if calculations:
                sample_calc = calculations[0]
                inventory_fields = ['inventory_available', 'can_fulfill', 'inventory_status', 'inventory_status_text']
                for field in inventory_fields:
                    if field not in sample_calc:
                        print(f"❌ Missing inventory field in calculation: {field}")
                        return False
                
                print(f"✅ Enhanced calculation returned {len(calculations)} items with inventory data")
                
                # Check inventory status distribution
                status_counts = {}
                for calc in calculations:
                    status = calc.get('inventory_status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"📊 Inventory status distribution: {status_counts}")
                
                # Verify summary contains inventory statistics
                summary = response['summary']
                inventory_summary_fields = ['sufficient_items', 'partial_items', 'insufficient_items', 'not_found_items']
                for field in inventory_summary_fields:
                    if field not in summary:
                        print(f"❌ Missing inventory summary field: {field}")
                        return False
                
                print(f"✅ Inventory summary: Sufficient={summary['sufficient_items']}, Partial={summary['partial_items']}, Insufficient={summary['insufficient_items']}, Not Found={summary['not_found_items']}")
                return True
            else:
                print("⚠️ No calculations returned")
                return True  # This might be valid if no data matches filters
        return False

    def test_enhanced_calculate_without_inventory(self):
        """Test enhanced calculation without inventory data"""
        if not self.session_id:
            print("❌ No order session ID available for enhanced calculation test")
            return False
            
        calculation_data = {
            "days": 15,
            "order_session_id": self.session_id,
            "inventory_session_id": None,  # No inventory data
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate without Inventory",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify that inventory_status indicates no inventory data
            if response.get('inventory_status') != 'no_inventory_data':
                print(f"❌ Expected inventory_status 'no_inventory_data', got '{response.get('inventory_status')}'")
                return False
            
            # Verify calculations don't have inventory fields
            calculations = response.get('calculations', [])
            if calculations:
                sample_calc = calculations[0]
                if sample_calc.get('inventory_status') != 'no_data':
                    print(f"❌ Expected inventory_status 'no_data' in calculations, got '{sample_calc.get('inventory_status')}'")
                    return False
            
            print("✅ Enhanced calculation without inventory works correctly")
            return True
        return False

    def test_enhanced_calculate_invalid_order_session(self):
        """Test enhanced calculation with invalid order session ID"""
        calculation_data = {
            "days": 30,
            "order_session_id": "invalid-session-id",
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate (Invalid Order Session)",
            "POST",
            "api/enhanced-calculate",
            404,
            data=calculation_data
        )
        # Success means we got the expected 404 error
        return success

    def test_enhanced_calculate_with_filters(self):
        """Test enhanced calculation with product and packaging filters"""
        if not self.session_id or not self.inventory_session_id:
            print("❌ Missing session IDs for enhanced calculation with filters test")
            return False
            
        calculation_data = {
            "days": 20,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": ["COCA-COLA 33CL"],
            "packaging_filter": ["Verre", "Pet"]
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Filters",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            calculations = response.get('calculations', [])
            print(f"✅ Enhanced calculation with filters returned {len(calculations)} items")
            
            # Verify that returned items match the filters
            for calc in calculations:
                if calc.get('packaging_type') not in ['Verre', 'Pet']:
                    print(f"❌ Found item with non-matching packaging: {calc.get('packaging_type')}")
                    return False
            
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

    def test_calculate_with_packaging_filters(self):
        """Test calculation with packaging filters to verify only allowed types work"""
        if not self.session_id:
            print("❌ No session ID available for packaging filter calculation test")
            return False
        
        # Test with allowed packaging types
        allowed_calculation_data = {
            "days": 15,
            "product_filter": None,
            "packaging_filter": ["Verre", "Pet"]  # Only allowed types
        }
        
        success1, response1 = self.run_test(
            "Calculate with Allowed Packaging Filters",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=allowed_calculation_data
        )
        
        # Test with mixed allowed/non-allowed packaging types
        mixed_calculation_data = {
            "days": 15,
            "product_filter": None,
            "packaging_filter": ["Verre", "Pet", "Canette"]  # Mix of allowed and non-allowed
        }
        
        success2, response2 = self.run_test(
            "Calculate with Mixed Packaging Filters",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=mixed_calculation_data
        )
        
        # Verify that calculations work and return appropriate results
        if success1 and 'calculations' in response1:
            print(f"✅ Allowed packaging filter returned {len(response1['calculations'])} results")
        
        if success2 and 'calculations' in response2:
            print(f"✅ Mixed packaging filter returned {len(response2['calculations'])} results")
            # Should only return results for allowed packaging types that exist in data
            for calc in response2['calculations']:
                if calc['packaging_type'] not in ['Verre', 'Pet', 'Ciel']:
                    print(f"❌ Found non-allowed packaging type in results: {calc['packaging_type']}")
                    return False
        
        return success1 and success2

    def test_gemini_query_enhanced(self):
        """Test enhanced Gemini AI query endpoint with improved context"""
        if not self.session_id:
            print("❌ No session ID available for Gemini query test")
            return False
        
        # Test multiple queries to verify enhanced context and intelligence
        test_queries = [
            {
                "query": "Quels sont les 3 produits avec la plus forte consommation?",
                "description": "Top 3 products by consumption"
            },
            {
                "query": "Analyse les tendances de stock par dépôt",
                "description": "Stock trends by depot analysis"
            },
            {
                "query": "Quels produits nécessitent un réapprovisionnement urgent?",
                "description": "Products needing urgent restocking"
            },
            {
                "query": "Donne-moi des statistiques précises sur les volumes",
                "description": "Precise volume statistics"
            }
        ]
        
        all_passed = True
        
        for i, test_query in enumerate(test_queries, 1):
            query_data = {
                "query": test_query["query"],
                "session_id": self.session_id
            }
            
            success, response = self.run_test(
                f"Enhanced Gemini Query {i}: {test_query['description']}",
                "POST",
                f"api/gemini-query/{self.session_id}",
                200,
                data=query_data
            )
            
            if success and 'response' in response:
                ai_response = response['response']
                print(f"🤖 AI Response length: {len(ai_response)} characters")
                
                # Check for intelligent response characteristics
                if len(ai_response) < 50:
                    print(f"⚠️ Response seems too short: {ai_response}")
                    all_passed = False
                elif len(ai_response) > 1000:
                    print(f"⚠️ Response seems too long (should be 2-4 sentences): {len(ai_response)} chars")
                    all_passed = False
                else:
                    print(f"✅ Response length appropriate: {len(ai_response)} characters")
                
                # Check for French language
                french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'avec', 'pour', 'dans']
                if not any(indicator in ai_response.lower() for indicator in french_indicators):
                    print(f"⚠️ Response may not be in French: {ai_response[:100]}...")
                    all_passed = False
                else:
                    print("✅ Response appears to be in French")
                
                print(f"📝 Sample response: {ai_response[:200]}...")
            else:
                all_passed = False
        
        return all_passed

    def test_gemini_query_french(self):
        """Test Gemini AI query endpoint with French query (legacy test)"""
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
        ("Upload Inventory Excel File", tester.test_upload_inventory_excel),
        ("Upload Invalid Inventory Excel (Missing Columns)", tester.test_upload_inventory_excel_missing_columns),
        ("Get Inventory Data", tester.test_get_inventory_data),
        ("Get Inventory Data (Invalid Session)", tester.test_get_inventory_data_invalid_session),
        ("Enhanced Calculate with Inventory Cross-Reference", tester.test_enhanced_calculate_with_inventory),
        ("Enhanced Calculate without Inventory", tester.test_enhanced_calculate_without_inventory),
        ("Enhanced Calculate (Invalid Order Session)", tester.test_enhanced_calculate_invalid_order_session),
        ("Enhanced Calculate with Filters", tester.test_enhanced_calculate_with_filters),
        ("Packaging Filter Enhancement", tester.test_packaging_filter_enhancement),
        ("Get Available Filters", tester.test_get_filters),
        ("Calculate Requirements", tester.test_calculate_requirements),
        ("Calculate with Packaging Filters", tester.test_calculate_with_packaging_filters),
        ("Enhanced Gemini AI Queries", tester.test_gemini_query_enhanced),
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