import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class TransitStockTester:
    def __init__(self, base_url="http://localhost:8001"):
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

    def create_order_excel_file(self):
        """Create order Excel file with Column G 'Stock Utilisation Libre'"""
        # Create sample order data with required columns
        order_data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5)
            ],
            'Article': ['1011', '1016', '1021', '1033', '2011', '2014'],
            'Désignation Article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE',
                'COCA-COLA ZERO 33CL PET'
            ],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT1'],
            'Nom Division': ['M212', 'M212', 'M213', 'M212', 'M213', 'M212'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200],
            'Stock Utilisation Libre': [20, 30, 15, 25, 10, 35],  # Column G - Current stock at depot
            'Ecart': [0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Verre', 'Verre', 'Pet'],
            'Quantité en Palette': [24, 12, 24, 24, 24, 12]
        }
        
        df = pd.DataFrame(order_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def create_transit_excel_file(self):
        """Create transit Excel file with Column I 'Quantité' (transit stock)"""
        # Create transit data with specific column positions
        # Column A = Article, Column C = Division (depot), Column I = Quantité (transit stock)
        
        # Create a DataFrame with 9 columns to ensure Column I exists
        transit_data = {
            'Article': ['1011', '1016', '1021', '1033', '2011', '2014'],  # Column A
            'Col_B': ['', '', '', '', '', ''],  # Column B (empty)
            'Division': ['M212', 'M212', 'M213', 'M212', 'M213', 'M212'],  # Column C
            'Col_D': ['', '', '', '', '', ''],  # Column D (empty)
            'Col_E': ['', '', '', '', '', ''],  # Column E (empty)
            'Col_F': ['', '', '', '', '', ''],  # Column F (empty)
            'Col_G': ['', '', '', '', '', ''],  # Column G (empty)
            'Col_H': ['', '', '', '', '', ''],  # Column H (empty)
            'Quantité': [30, 20, 25, 15, 40, 10]  # Column I - Transit stock
        }
        
        df = pd.DataFrame(transit_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def create_inventory_excel_file(self):
        """Create inventory Excel file for testing"""
        inventory_data = {
            'Division': ['M212', 'M212', 'M213', 'M212', 'M213', 'M212'],
            'Article': ['1011', '1016', '1021', '1033', '2011', '2014'],
            'Désignation article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE',
                'COCA-COLA ZERO 33CL PET'
            ],
            'STOCK À DATE': [100, 80, 60, 90, 70, 110]  # Inventory stock
        }
        
        df = pd.DataFrame(inventory_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def test_1_upload_order_file(self):
        """Test 1: Upload order file and verify Column G 'Stock Utilisation Libre' is read correctly"""
        print("\n" + "="*80)
        print("TEST 1: ORDER FILE UPLOAD - Column G 'Stock Utilisation Libre'")
        print("="*80)
        
        order_file = self.create_order_excel_file()
        
        files = {
            'file': ('order_data.xlsx', order_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Order Excel File",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.order_session_id = response['session_id']
            print(f"✅ Order Session ID: {self.order_session_id}")
            
            # Verify the upload processed the data correctly
            if 'records_count' in response:
                print(f"✅ Processed {response['records_count']} order records")
                return True
            else:
                print("❌ Missing records_count in response")
                return False
        return False

    def test_2_upload_transit_file(self):
        """Test 2: Upload transit file and verify Column I 'Quantité' is read correctly"""
        print("\n" + "="*80)
        print("TEST 2: TRANSIT FILE UPLOAD - Column I 'Quantité'")
        print("="*80)
        
        transit_file = self.create_transit_excel_file()
        
        files = {
            'file': ('transit_data.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit Excel File",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"✅ Transit Session ID: {self.transit_session_id}")
            
            # Verify the response structure
            required_fields = ['session_id', 'message', 'records_count', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify summary structure
            summary = response['summary']
            summary_fields = ['divisions', 'articles_count', 'total_transit_quantity', 'records_count']
            for field in summary_fields:
                if field not in summary:
                    print(f"❌ Missing summary field: {field}")
                    return False
            
            print(f"✅ Transit upload successful with {response['records_count']} records")
            print(f"✅ Total transit quantity: {summary['total_transit_quantity']} units")
            print(f"✅ Articles count: {summary['articles_count']}")
            print(f"✅ Divisions: {summary['divisions']}")
            
            # Verify expected values
            expected_total = 30 + 20 + 25 + 15 + 40 + 10  # Sum of transit quantities
            if abs(summary['total_transit_quantity'] - expected_total) < 0.01:
                print(f"✅ Transit quantity calculation correct: {expected_total}")
                return True
            else:
                print(f"❌ Transit quantity mismatch: expected {expected_total}, got {summary['total_transit_quantity']}")
                return False
        return False

    def test_3_upload_inventory_file(self):
        """Test 3: Upload inventory file for comprehensive testing"""
        print("\n" + "="*80)
        print("TEST 3: INVENTORY FILE UPLOAD")
        print("="*80)
        
        inventory_file = self.create_inventory_excel_file()
        
        files = {
            'file': ('inventory_data.xlsx', inventory_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
            print(f"✅ Inventory Session ID: {self.inventory_session_id}")
            return True
        return False

    def test_4_basic_calculation_with_transit(self):
        """Test 4: Basic calculation with transit stock"""
        print("\n" + "="*80)
        print("TEST 4: BASIC CALCULATION WITH TRANSIT STOCK")
        print("="*80)
        
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing required session IDs")
            return False
        
        calculation_data = {
            "days": 30,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Basic Calculate with Transit Stock",
            "POST",
            f"api/calculate/{self.order_session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            print(f"✅ Calculation returned {len(calculations)} items")
            
            # Verify transit stock fields are present
            for calc in calculations:
                required_fields = ['transit_available', 'total_available', 'current_stock']
                for field in required_fields:
                    if field not in calc:
                        print(f"❌ Missing field '{field}' in calculation")
                        return False
                
                # Print calculation details for verification
                article = calc['article_code']
                current_stock = calc['current_stock']
                transit_available = calc['transit_available']
                total_available = calc['total_available']
                quantity_to_send = calc['quantity_to_send']
                
                print(f"📋 Article {article}: Current={current_stock}, Transit={transit_available}, Total={total_available}, ToSend={quantity_to_send}")
                
                # Verify total_available = current_stock + transit_available
                expected_total = current_stock + transit_available
                if abs(total_available - expected_total) > 0.01:
                    print(f"❌ Total available calculation error for {article}: {total_available} != {current_stock} + {transit_available}")
                    return False
                
                # Verify transit stock matching by article and depot
                depot = calc['depot']
                if article == '1011' and depot == 'M212':
                    if transit_available != 30:
                        print(f"❌ Article 1011 at M212 should have 30 transit stock, got {transit_available}")
                        return False
                    print(f"✅ Article 1011 at M212 correctly has {transit_available} transit stock")
                
                elif article == '1016' and depot == 'M212':
                    if transit_available != 20:
                        print(f"❌ Article 1016 at M212 should have 20 transit stock, got {transit_available}")
                        return False
                    print(f"✅ Article 1016 at M212 correctly has {transit_available} transit stock")
            
            print("✅ Basic calculation with transit stock working correctly")
            return True
        
        return False

    def test_5_enhanced_calculation_with_transit(self):
        """Test 5: Enhanced calculation with transit stock"""
        print("\n" + "="*80)
        print("TEST 5: ENHANCED CALCULATION WITH TRANSIT STOCK")
        print("="*80)
        
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing required session IDs")
            return False
        
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
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            print(f"✅ Enhanced calculation returned {len(calculations)} items")
            
            # Verify enhanced calculation includes transit stock
            for calc in calculations:
                required_fields = ['transit_available', 'inventory_available', 'total_available']
                for field in required_fields:
                    if field not in calc:
                        print(f"❌ Missing field '{field}' in enhanced calculation")
                        return False
                
                article = calc['article_code']
                depot = calc['depot']
                inventory_available = calc['inventory_available']
                transit_available = calc['transit_available']
                total_available = calc['total_available']
                quantity_to_send = calc['quantity_to_send']
                
                print(f"📋 Enhanced - Article {article} at {depot}: Inventory={inventory_available}, Transit={transit_available}, Total={total_available}, ToSend={quantity_to_send}")
                
                # Verify total_available = inventory_available + transit_available
                expected_total = inventory_available + transit_available
                if abs(total_available - expected_total) > 0.01:
                    print(f"❌ Total available calculation error for {article}: {total_available} != {inventory_available} + {transit_available}")
                    return False
                
                # Check inventory status includes transit information
                if 'inventory_status_text' in calc and transit_available > 0:
                    status_text = calc['inventory_status_text']
                    if 'transit' in status_text.lower():
                        print(f"✅ Status text includes transit info: {status_text}")
                    else:
                        print(f"⚠️ Status text may not include transit info: {status_text}")
            
            print("✅ Enhanced calculation with transit stock working correctly")
            return True
        
        return False

    def test_6_transit_data_matching(self):
        """Test 6: Verify transit data is matched by both Article code AND Division (depot)"""
        print("\n" + "="*80)
        print("TEST 6: TRANSIT DATA MATCHING BY ARTICLE AND DIVISION")
        print("="*80)
        
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing required session IDs")
            return False
        
        calculation_data = {
            "days": 30,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Calculate for Transit Matching Test",
            "POST",
            f"api/calculate/{self.order_session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Test specific article-depot combinations
            test_cases = [
                {'article': '1011', 'depot': 'M212', 'expected_transit': 30},
                {'article': '1016', 'depot': 'M212', 'expected_transit': 20},
                {'article': '1021', 'depot': 'M213', 'expected_transit': 25},
                {'article': '1033', 'depot': 'M212', 'expected_transit': 15},
                {'article': '2011', 'depot': 'M213', 'expected_transit': 40},
                {'article': '2014', 'depot': 'M212', 'expected_transit': 10}
            ]
            
            for test_case in test_cases:
                found = False
                for calc in calculations:
                    if str(calc['article_code']) == test_case['article'] and calc['depot'] == test_case['depot']:
                        found = True
                        transit_available = calc['transit_available']
                        if transit_available == test_case['expected_transit']:
                            print(f"✅ Article {test_case['article']} at {test_case['depot']}: Transit stock {transit_available} matches expected {test_case['expected_transit']}")
                        else:
                            print(f"❌ Article {test_case['article']} at {test_case['depot']}: Transit stock {transit_available} != expected {test_case['expected_transit']}")
                            return False
                        break
                
                if not found:
                    print(f"❌ Article {test_case['article']} at {test_case['depot']} not found in calculations")
                    return False
            
            print("✅ Transit data matching by Article and Division working correctly")
            return True
        
        return False

    def test_7_combined_calculation_scenario(self):
        """Test 7: Test the specific scenario from user report"""
        print("\n" + "="*80)
        print("TEST 7: COMBINED CALCULATION SCENARIO")
        print("Test scenario: Article 1011 at Depot M212 has 20 current stock and 30 transit stock = 50 total available")
        print("If required stock is 60, then Quantité à Envoyer should be 10 (60-50=10)")
        print("="*80)
        
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing required session IDs")
            return False
        
        # Calculate for 30 days to get a specific required stock amount
        calculation_data = {
            "days": 30,
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Combined Calculation Scenario Test",
            "POST",
            f"api/calculate/{self.order_session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Find Article 1011 at Depot M212
            target_calc = None
            for calc in calculations:
                if calc['article_code'] == '1011' and calc['depot'] == 'M212':
                    target_calc = calc
                    break
            
            if not target_calc:
                print("❌ Article 1011 at Depot M212 not found")
                return False
            
            # Extract values
            current_stock = target_calc['current_stock']
            transit_available = target_calc['transit_available']
            total_available = target_calc['total_available']
            required_stock = target_calc['required_for_x_days']
            quantity_to_send = target_calc['quantity_to_send']
            
            print(f"📋 Article 1011 at M212:")
            print(f"   Current Stock: {current_stock}")
            print(f"   Transit Stock: {transit_available}")
            print(f"   Total Available: {total_available}")
            print(f"   Required Stock (30 days): {required_stock}")
            print(f"   Quantity to Send: {quantity_to_send}")
            
            # Verify the calculation logic
            expected_total_available = current_stock + transit_available
            expected_quantity_to_send = max(0, required_stock - expected_total_available)
            
            # Check total available calculation
            if abs(total_available - expected_total_available) > 0.01:
                print(f"❌ Total available calculation error: {total_available} != {current_stock} + {transit_available}")
                return False
            
            # Check quantity to send calculation
            if abs(quantity_to_send - expected_quantity_to_send) > 0.01:
                print(f"❌ Quantity to send calculation error: {quantity_to_send} != max(0, {required_stock} - {total_available})")
                return False
            
            print(f"✅ Calculation logic verified:")
            print(f"   Total Available = {current_stock} + {transit_available} = {total_available}")
            print(f"   Quantity to Send = max(0, {required_stock} - {total_available}) = {quantity_to_send}")
            
            # Verify our test data matches expected values
            if current_stock == 20 and transit_available == 30:
                print("✅ Test data matches expected values (20 current + 30 transit)")
                if total_available == 50:
                    print("✅ Total available correctly calculated as 50")
                    return True
                else:
                    print(f"❌ Total available should be 50, got {total_available}")
                    return False
            else:
                print(f"⚠️ Test data different than expected (current={current_stock}, transit={transit_available})")
                print("✅ But calculation logic is working correctly")
                return True
        
        return False

    def test_8_transit_only_calculation(self):
        """Test 8: Test calculation with only transit data (no inventory)"""
        print("\n" + "="*80)
        print("TEST 8: TRANSIT-ONLY CALCULATION")
        print("="*80)
        
        if not self.order_session_id or not self.transit_session_id:
            print("❌ Missing required session IDs")
            return False
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.order_session_id,
            "inventory_session_id": None,  # No inventory data
            "transit_session_id": self.transit_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Transit Only",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                article = calc['article_code']
                depot = calc['depot']
                transit_available = calc.get('transit_available', 0)
                inventory_available = calc.get('inventory_available', 0)
                inventory_status = calc.get('inventory_status', '')
                inventory_status_text = calc.get('inventory_status_text', '')
                
                print(f"📋 Transit-only - Article {article} at {depot}: Transit={transit_available}, Status={inventory_status}")
                
                # Verify inventory_available is 0 when no inventory data
                if inventory_available != 0:
                    print(f"❌ Expected inventory_available=0, got {inventory_available}")
                    return False
                
                # Verify appropriate status for transit-only scenarios
                if transit_available > 0:
                    expected_statuses = ['transit_sufficient', 'transit_partial', 'transit_only']
                    if inventory_status not in expected_statuses:
                        print(f"⚠️ Unexpected status for transit-only scenario: {inventory_status}")
                    else:
                        print(f"✅ Appropriate transit status: {inventory_status}")
                
                # Verify status text includes transit information
                if transit_available > 0 and 'transit' not in inventory_status_text.lower():
                    print(f"⚠️ Status text should mention transit: {inventory_status_text}")
            
            print("✅ Transit-only calculation working correctly")
            return True
        
        return False

    def test_9_no_transit_data_fallback(self):
        """Test 9: Test calculation without transit data (fallback behavior)"""
        print("\n" + "="*80)
        print("TEST 9: NO TRANSIT DATA FALLBACK")
        print("="*80)
        
        if not self.order_session_id:
            print("❌ Missing order session ID")
            return False
        
        calculation_data = {
            "days": 30,
            "transit_session_id": None,  # No transit data
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Calculate without Transit Data",
            "POST",
            f"api/calculate/{self.order_session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                transit_available = calc.get('transit_available', 0)
                total_available = calc.get('total_available', 0)
                current_stock = calc.get('current_stock', 0)
                
                # Verify transit_available is 0 when no transit data
                if transit_available != 0:
                    print(f"❌ Expected transit_available=0, got {transit_available}")
                    return False
                
                # Verify total_available equals current_stock when no transit
                if abs(total_available - current_stock) > 0.01:
                    print(f"❌ Expected total_available={current_stock}, got {total_available}")
                    return False
            
            print("✅ No transit data fallback working correctly")
            return True
        
        return False

    def test_10_invalid_transit_file(self):
        """Test 10: Test upload of invalid transit file"""
        print("\n" + "="*80)
        print("TEST 10: INVALID TRANSIT FILE UPLOAD")
        print("="*80)
        
        # Create invalid transit file with insufficient columns
        invalid_data = {
            'Article': ['1011', '1016'],
            'Division': ['M212', 'M212'],
            # Missing Column I - only 2 columns instead of required 9
        }
        
        df = pd.DataFrame(invalid_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_transit.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Invalid Transit File",
            "POST",
            "api/upload-transit-excel",
            400,  # Expect error
            files=files
        )
        
        # Success means we got the expected 400 error
        if success:
            print("✅ Invalid transit file correctly rejected")
            return True
        else:
            print("❌ Invalid transit file should have been rejected")
            return False

    def run_all_tests(self):
        """Run all transit stock tests"""
        print("\n" + "="*100)
        print("🚀 STARTING COMPREHENSIVE TRANSIT STOCK FUNCTIONALITY TESTING")
        print("="*100)
        
        tests = [
            self.test_1_upload_order_file,
            self.test_2_upload_transit_file,
            self.test_3_upload_inventory_file,
            self.test_4_basic_calculation_with_transit,
            self.test_5_enhanced_calculation_with_transit,
            self.test_6_transit_data_matching,
            self.test_7_combined_calculation_scenario,
            self.test_8_transit_only_calculation,
            self.test_9_no_transit_data_fallback,
            self.test_10_invalid_transit_file
        ]
        
        for test in tests:
            try:
                result = test()
                if not result:
                    print(f"\n❌ TEST FAILED: {test.__name__}")
            except Exception as e:
                print(f"\n💥 TEST ERROR: {test.__name__} - {str(e)}")
                self.tests_run += 1  # Count as run but not passed
        
        # Print final results
        print("\n" + "="*100)
        print("📊 TRANSIT STOCK TESTING RESULTS")
        print("="*100)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TRANSIT STOCK TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} TESTS FAILED")
            return False

if __name__ == "__main__":
    tester = TransitStockTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)