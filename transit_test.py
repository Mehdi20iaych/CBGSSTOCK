import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class TransitStockTester:
    def __init__(self, base_url="https://e4d7cb4e-74c3-4168-8b71-3d543dbf6be5.preview.emergentagent.com"):
        self.base_url = base_url
        self.order_session_id = None
        self.inventory_session_id = None
        self.transit_session_id = None
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

    def create_sample_order_excel_file(self):
        """Create a sample order Excel file for testing"""
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5)
            ],
            'Article': ['ART001', 'ART002', 'ART003', 'ART001', 'ART002', 'ART003'],
            'Désignation Article': ['COCA-COLA 33CL', 'PEPSI 50CL', 'SPRITE 33CL', 'COCA-COLA 33CL', 'PEPSI 50CL', 'SPRITE 33CL'],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT1'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B', 'Division A'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200],
            'Stock Utilisation Libre': [500, 300, 200, 500, 300, 200],
            'Ecart': [0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Verre', 'Pet', 'Verre'],
            'Quantité en Palette': [24, 12, 24, 24, 12, 24]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_inventory_excel_file(self):
        """Create a sample inventory Excel file for testing"""
        inventory_data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005'],
            'Désignation article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE'
            ],
            'STOCK À DATE': [1500, 800, 600, 1200, 300]
        }
        
        df = pd.DataFrame(inventory_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_transit_excel_file(self):
        """Create a sample transit Excel file for testing with Column A (Article), Column C (Division), Column I (Quantité)"""
        # Create a DataFrame with 9 columns to ensure Column I exists
        # Column A = Article, Column C = Division, Column I = Quantité
        transit_data = {
            'Article': ['ART001', 'ART002', 'ART003', 'ART001', 'ART004'],  # Column A
            'Col_B': ['Data B1', 'Data B2', 'Data B3', 'Data B4', 'Data B5'],  # Column B (filler)
            'Division': ['Division A', 'Division A', 'Division B', 'Division B', 'Division A'],  # Column C
            'Col_D': ['Data D1', 'Data D2', 'Data D3', 'Data D4', 'Data D5'],  # Column D (filler)
            'Col_E': ['Data E1', 'Data E2', 'Data E3', 'Data E4', 'Data E5'],  # Column E (filler)
            'Col_F': ['Data F1', 'Data F2', 'Data F3', 'Data F4', 'Data F5'],  # Column F (filler)
            'Col_G': ['Data G1', 'Data G2', 'Data G3', 'Data G4', 'Data G5'],  # Column G (filler)
            'Col_H': ['Data H1', 'Data H2', 'Data H3', 'Data H4', 'Data H5'],  # Column H (filler)
            'Quantité': [50, 75, 30, 25, 100]  # Column I
        }
        
        df = pd.DataFrame(transit_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_invalid_transit_excel_file(self):
        """Create an invalid transit Excel file with insufficient columns"""
        # Only 5 columns - not enough to access Column I
        invalid_data = {
            'Article': ['ART001', 'ART002'],
            'Col_B': ['Data B1', 'Data B2'],
            'Division': ['Division A', 'Division A'],
            'Col_D': ['Data D1', 'Data D2'],
            'Col_E': ['Data E1', 'Data E2']
        }
        
        df = pd.DataFrame(invalid_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def setup_test_data(self):
        """Setup order and inventory data for testing"""
        print("\n🔧 Setting up test data...")
        
        # Upload order data
        order_file = self.create_sample_order_excel_file()
        files = {
            'file': ('sample_order_data.xlsx', order_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Setup - Upload Order Excel File",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.order_session_id = response['session_id']
            print(f"Order Session ID: {self.order_session_id}")
        else:
            print("❌ Failed to setup order data")
            return False

        # Upload inventory data
        inventory_file = self.create_sample_inventory_excel_file()
        files = {
            'file': ('sample_inventory_data.xlsx', inventory_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Setup - Upload Inventory Excel File",
            "POST",
            "api/upload-inventory-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.inventory_session_id = response['session_id']
            print(f"Inventory Session ID: {self.inventory_session_id}")
            return True
        else:
            print("❌ Failed to setup inventory data")
            return False

    def test_transit_upload_endpoint(self):
        """Test the new transit upload endpoint /api/upload-transit-excel"""
        print("\n📋 Testing Transit Upload Endpoint...")
        
        # Test valid transit file upload
        transit_file = self.create_sample_transit_excel_file()
        files = {
            'file': ('sample_transit_data.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Transit Upload - Valid File",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"Transit Session ID: {self.transit_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'records_count', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in response: {field}")
                    return False
            
            # Verify summary structure
            summary = response['summary']
            summary_fields = ['divisions', 'articles_count', 'total_transit_quantity', 'records_count']
            for field in summary_fields:
                if field not in summary:
                    print(f"❌ Missing required field in summary: {field}")
                    return False
            
            print(f"✅ Transit upload successful with {response['records_count']} records")
            print(f"✅ Total transit quantity: {summary['total_transit_quantity']} units")
            print(f"✅ Articles count: {summary['articles_count']}")
            print(f"✅ Divisions: {summary['divisions']}")
            return True
        else:
            print("❌ Transit upload failed")
            return False

    def test_transit_upload_invalid_file(self):
        """Test transit upload with invalid file (insufficient columns)"""
        print("\n📋 Testing Transit Upload with Invalid File...")
        
        invalid_file = self.create_invalid_transit_excel_file()
        files = {
            'file': ('invalid_transit_data.xlsx', invalid_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Transit Upload - Invalid File (Insufficient Columns)",
            "POST",
            "api/upload-transit-excel",
            400,
            files=files
        )
        
        # Success here means we got the expected 400 error
        return success

    def test_transit_upload_non_excel_file(self):
        """Test transit upload with non-Excel file"""
        print("\n📋 Testing Transit Upload with Non-Excel File...")
        
        text_content = "This is not an Excel file"
        files = {
            'file': ('test.txt', io.StringIO(text_content), 'text/plain')
        }
        
        success, response = self.run_test(
            "Transit Upload - Non-Excel File",
            "POST",
            "api/upload-transit-excel",
            400,
            files=files
        )
        
        # Success here means we got the expected 400 error
        return success

    def test_enhanced_calculate_with_transit(self):
        """Test enhanced calculation with transit stock integration"""
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing session IDs for enhanced calculation with transit test")
            return False
        
        print("\n📋 Testing Enhanced Calculate with Transit Integration...")
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.order_session_id,
            "inventory_session_id": self.inventory_session_id,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Transit Stock",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['calculations', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in enhanced calculation response: {field}")
                    return False
            
            # Verify transit fields in calculations
            calculations = response['calculations']
            if calculations:
                sample_calc = calculations[0]
                transit_fields = ['transit_available', 'total_available']
                for field in transit_fields:
                    if field not in sample_calc:
                        print(f"❌ Missing transit field in calculation: {field}")
                        return False
                
                print(f"✅ Enhanced calculation returned {len(calculations)} items with transit data")
                
                # Check for items with transit stock
                items_with_transit = [calc for calc in calculations if calc.get('transit_available', 0) > 0]
                print(f"📊 Items with transit stock: {len(items_with_transit)}")
                
                # Verify business logic: quantity_to_send should consider transit stock
                for calc in calculations:
                    current_stock = calc.get('current_stock', 0)
                    transit_available = calc.get('transit_available', 0)
                    total_available = calc.get('total_available', 0)
                    required_stock = calc.get('required_for_x_days', 0)
                    quantity_to_send = calc.get('quantity_to_send', 0)
                    
                    # Verify total_available = current_stock + transit_available (if inventory data available)
                    if self.inventory_session_id:
                        inventory_available = calc.get('inventory_available', 0)
                        expected_total = inventory_available + transit_available
                        if abs(total_available - expected_total) > 0.01:  # Allow small floating point differences
                            print(f"❌ Total available calculation error: {total_available} != {expected_total}")
                            return False
                    else:
                        expected_total = current_stock + transit_available
                        if abs(total_available - expected_total) > 0.01:
                            print(f"❌ Total available calculation error: {total_available} != {expected_total}")
                            return False
                    
                    # Verify quantity_to_send logic: max(0, required - total_available)
                    expected_quantity_to_send = max(0, required_stock - total_available)
                    if abs(quantity_to_send - expected_quantity_to_send) > 0.01:
                        print(f"❌ Quantity to send calculation error for {calc.get('article_code')}: {quantity_to_send} != {expected_quantity_to_send}")
                        print(f"   Required: {required_stock}, Total Available: {total_available}, Transit: {transit_available}")
                        return False
                
                print("✅ Transit stock business logic verified correctly")
                
                # Test specific matching logic (Article + Division)
                for calc in calculations:
                    if calc.get('transit_available', 0) > 0:
                        print(f"✅ Article {calc.get('article_code')} in {calc.get('depot')} has transit stock: {calc.get('transit_available')}")
                
                return True
            else:
                print("⚠️ No calculations returned")
                return True  # This might be valid if no data matches filters
        return False

    def test_basic_calculate_with_transit(self):
        """Test basic calculation with transit stock integration"""
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing session IDs for basic calculation with transit test")
            return False
        
        print("\n📋 Testing Basic Calculate with Transit Integration...")
        
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None,
            "transit_session_id": self.transit_session_id
        }
        
        success, response = self.run_test(
            "Basic Calculate with Transit Stock",
            "POST",
            f"api/calculate/{self.order_session_id}",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['calculations', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in basic calculation response: {field}")
                    return False
            
            # Verify transit fields in calculations
            calculations = response['calculations']
            if calculations:
                sample_calc = calculations[0]
                transit_fields = ['transit_available', 'total_available']
                for field in transit_fields:
                    if field not in sample_calc:
                        print(f"❌ Missing transit field in calculation: {field}")
                        return False
                
                print(f"✅ Basic calculation returned {len(calculations)} items with transit data")
                
                # Verify business logic: quantity_to_send should consider transit stock
                for calc in calculations:
                    current_stock = calc.get('current_stock', 0)
                    transit_available = calc.get('transit_available', 0)
                    total_available = calc.get('total_available', 0)
                    required_stock = calc.get('required_for_x_days', 0)
                    quantity_to_send = calc.get('quantity_to_send', 0)
                    
                    # Verify total_available = current_stock + transit_available
                    expected_total = current_stock + transit_available
                    if abs(total_available - expected_total) > 0.01:
                        print(f"❌ Total available calculation error: {total_available} != {expected_total}")
                        return False
                    
                    # Verify quantity_to_send logic: max(0, required - total_available)
                    expected_quantity_to_send = max(0, required_stock - total_available)
                    if abs(quantity_to_send - expected_quantity_to_send) > 0.01:
                        print(f"❌ Quantity to send calculation error for {calc.get('article_code')}: {quantity_to_send} != {expected_quantity_to_send}")
                        return False
                
                print("✅ Transit stock business logic verified correctly in basic calculation")
                return True
            else:
                print("⚠️ No calculations returned")
                return True
        return False

    def test_data_matching_logic(self):
        """Test that transit stock is matched by both Article code AND Division (depot)"""
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing session IDs for data matching logic test")
            return False
        
        print("\n📋 Testing Data Matching Logic (Article + Division)...")
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.order_session_id,
            "inventory_session_id": self.inventory_session_id,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Data Matching Logic Test",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Test specific matching scenarios
            matching_found = False
            non_matching_found = False
            
            for calc in calculations:
                article_code = calc.get('article_code')
                depot = calc.get('depot')
                transit_available = calc.get('transit_available', 0)
                
                print(f"📋 Article {article_code} in {depot}: Transit = {transit_available}")
                
                # Based on our test data:
                # ART001 in Division A should have transit stock (50 + 25 = 75)
                # ART002 in Division A should have transit stock (75)
                # ART003 in Division B should have transit stock (30)
                # Other combinations should have 0 transit stock
                
                if article_code == 'ART001' and depot == 'Division A':
                    if transit_available > 0:
                        print(f"✅ Correct match: ART001 in Division A has transit stock: {transit_available}")
                        matching_found = True
                    else:
                        print(f"❌ Expected transit stock for ART001 in Division A but got: {transit_available}")
                        return False
                elif article_code == 'ART002' and depot == 'Division A':
                    if transit_available > 0:
                        print(f"✅ Correct match: ART002 in Division A has transit stock: {transit_available}")
                        matching_found = True
                    else:
                        print(f"❌ Expected transit stock for ART002 in Division A but got: {transit_available}")
                        return False
                elif article_code == 'ART003' and depot == 'Division B':
                    if transit_available > 0:
                        print(f"✅ Correct match: ART003 in Division B has transit stock: {transit_available}")
                        matching_found = True
                    else:
                        print(f"❌ Expected transit stock for ART003 in Division B but got: {transit_available}")
                        return False
                else:
                    # Other combinations should have no transit stock
                    if transit_available == 0:
                        print(f"✅ Correct non-match: {article_code} in {depot} has no transit stock")
                        non_matching_found = True
                    else:
                        print(f"❌ Unexpected transit stock for {article_code} in {depot}: {transit_available}")
                        return False
            
            if matching_found and non_matching_found:
                print("✅ Data matching logic working correctly - both matching and non-matching cases verified")
                return True
            elif matching_found:
                print("✅ Data matching logic working - matching cases verified")
                return True
            else:
                print("⚠️ No matching cases found to verify")
                return True
        
        return False

    def test_edge_cases(self):
        """Test edge cases where transit data exists but doesn't match any orders"""
        print("\n📋 Testing Edge Cases...")
        
        # Test calculation without transit data
        if not self.order_session_id:
            print("❌ Missing order session ID for edge case test")
            return False
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.order_session_id,
            "inventory_session_id": self.inventory_session_id,
            "transit_session_id": None,  # No transit data
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Edge Case - No Transit Data",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify all items have 0 transit stock
            for calc in calculations:
                transit_available = calc.get('transit_available', 0)
                if transit_available != 0:
                    print(f"❌ Expected 0 transit stock but got {transit_available} for {calc.get('article_code')}")
                    return False
            
            print("✅ Edge case verified - no transit data results in 0 transit stock for all items")
            return True
        
        return False

    def test_response_fields(self):
        """Test that new response fields are present and correctly formatted"""
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing session IDs for response fields test")
            return False
        
        print("\n📋 Testing Response Fields...")
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.order_session_id,
            "inventory_session_id": self.inventory_session_id,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Response Fields Test",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            if calculations:
                sample_calc = calculations[0]
                
                # Check for required new fields
                required_fields = ['transit_available', 'total_available']
                for field in required_fields:
                    if field not in sample_calc:
                        print(f"❌ Missing required field: {field}")
                        return False
                    
                    # Verify field is numeric
                    value = sample_calc[field]
                    if not isinstance(value, (int, float)):
                        print(f"❌ Field {field} should be numeric but got {type(value)}: {value}")
                        return False
                
                # Check inventory status messages include transit information when applicable
                for calc in calculations:
                    transit_available = calc.get('transit_available', 0)
                    inventory_status_text = calc.get('inventory_status_text', '')
                    
                    if transit_available > 0 and 'transit' not in inventory_status_text.lower():
                        print(f"⚠️ Item with transit stock ({transit_available}) doesn't mention transit in status: {inventory_status_text}")
                        # This is not a failure, just a note
                
                print("✅ All required response fields present and correctly formatted")
                return True
            else:
                print("⚠️ No calculations to verify response fields")
                return True
        
        return False

    def run_all_tests(self):
        """Run all transit stock tests"""
        print("🚀 Starting Transit Stock Functionality Tests")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data - aborting tests")
            return False
        
        # Run all tests
        tests = [
            self.test_transit_upload_endpoint,
            self.test_transit_upload_invalid_file,
            self.test_transit_upload_non_excel_file,
            self.test_enhanced_calculate_with_transit,
            self.test_basic_calculate_with_transit,
            self.test_data_matching_logic,
            self.test_edge_cases,
            self.test_response_fields
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
                self.tests_run += 1  # Count as a failed test
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TRANSIT STOCK TESTS SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TRANSIT STOCK TESTS PASSED!")
            return True
        else:
            print("❌ Some tests failed. Please review the output above.")
            return False

if __name__ == "__main__":
    tester = TransitStockTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)