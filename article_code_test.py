#!/usr/bin/env python3
"""
Focused test to verify that backend APIs return both article_code and article_name fields
after frontend changes to display article codes instead of article names.
"""

import requests
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class ArticleCodeFieldTester:
    def __init__(self, base_url="https://0074d26a-4347-4a2b-89d5-e02409ba89c8.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.inventory_session_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, passed, details=""):
        """Log test results"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        if details:
            print(f"   {details}")

    def create_sample_excel_file(self):
        """Create sample order data with article codes"""
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=8),
                datetime.now() - timedelta(days=5),
                datetime.now() - timedelta(days=3),
                datetime.now() - timedelta(days=1)
            ],
            'Article': ['ART001', 'ART002', 'ART003', 'ART001', 'ART002'],
            'Désignation Article': [
                'COCA-COLA 33CL VERRE', 
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'COCA-COLA 33CL VERRE', 
                'PEPSI 50CL PET'
            ],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B'],
            'Quantité Commandée': [100, 150, 80, 120, 90],
            'Stock Utilisation Libre': [500, 300, 200, 500, 300],
            'Ecart': [0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Verre', 'Pet'],
            'Quantité en Palette': [24, 12, 24, 24, 12]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_inventory_file(self):
        """Create sample inventory data with article codes"""
        inventory_data = {
            'Division': ['M210', 'M210', 'M210'],
            'Article': ['ART001', 'ART002', 'ART003'],
            'Désignation article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE'
            ],
            'STOCK À DATE': [1500, 800, 600]
        }
        
        df = pd.DataFrame(inventory_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def upload_test_data(self):
        """Upload test order and inventory data"""
        print("\n🔄 Uploading test data...")
        
        # Upload order data
        excel_file = self.create_sample_excel_file()
        files = {
            'file': ('test_orders.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(f"{self.base_url}/api/upload-excel", files=files)
        if response.status_code == 200:
            data = response.json()
            self.session_id = data['session_id']
            print(f"✅ Order data uploaded - Session ID: {self.session_id}")
        else:
            print(f"❌ Failed to upload order data: {response.status_code}")
            return False

        # Upload inventory data
        inventory_file = self.create_sample_inventory_file()
        files = {
            'file': ('test_inventory.xlsx', inventory_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(f"{self.base_url}/api/upload-inventory-excel", files=files)
        if response.status_code == 200:
            data = response.json()
            self.inventory_session_id = data['session_id']
            print(f"✅ Inventory data uploaded - Session ID: {self.inventory_session_id}")
            return True
        else:
            print(f"❌ Failed to upload inventory data: {response.status_code}")
            return False

    def test_upload_excel_response_fields(self):
        """Test that upload-excel endpoint returns proper data structure"""
        print("\n📋 Testing /api/upload-excel response structure...")
        
        if not self.session_id:
            self.log_test("Upload Excel Response Fields", False, "No session ID available")
            return
        
        # The upload was already done, so we check if it returned the expected structure
        # We'll make a filters request to verify the data structure
        response = requests.get(f"{self.base_url}/api/filters/{self.session_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that products (article names) are available
            has_products = 'products' in data and len(data['products']) > 0
            self.log_test("Upload Excel - Products field present", has_products, 
                         f"Found {len(data.get('products', []))} products")
            
            # Check packaging structure
            has_packaging = 'packaging' in data and len(data['packaging']) > 0
            self.log_test("Upload Excel - Packaging field present", has_packaging,
                         f"Found {len(data.get('packaging', []))} packaging types")
            
            # Check depots
            has_depots = 'depots' in data and len(data['depots']) > 0
            self.log_test("Upload Excel - Depots field present", has_depots,
                         f"Found {len(data.get('depots', []))} depots")
        else:
            self.log_test("Upload Excel Response Fields", False, f"Failed to get filters: {response.status_code}")

    def test_basic_calculate_article_fields(self):
        """Test that /api/calculate returns both article_code and article_name"""
        print("\n🧮 Testing /api/calculate article fields...")
        
        if not self.session_id:
            self.log_test("Basic Calculate Article Fields", False, "No session ID available")
            return
        
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        response = requests.post(
            f"{self.base_url}/api/calculate/{self.session_id}",
            json=calculation_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            calculations = data.get('calculations', [])
            
            if calculations:
                sample_item = calculations[0]
                
                # Check for article_code field
                has_article_code = 'article_code' in sample_item
                article_code_value = sample_item.get('article_code', 'N/A')
                self.log_test("Basic Calculate - article_code field", has_article_code,
                             f"Value: {article_code_value}")
                
                # Check for article_name field
                has_article_name = 'article_name' in sample_item
                article_name_value = sample_item.get('article_name', 'N/A')
                self.log_test("Basic Calculate - article_name field", has_article_name,
                             f"Value: {article_name_value}")
                
                # Verify both fields are present and have values
                both_fields_present = has_article_code and has_article_name
                self.log_test("Basic Calculate - Both article fields present", both_fields_present,
                             f"Code: {article_code_value}, Name: {article_name_value}")
                
                # Check all items have both fields
                all_items_have_fields = all(
                    'article_code' in item and 'article_name' in item 
                    for item in calculations
                )
                self.log_test("Basic Calculate - All items have article fields", all_items_have_fields,
                             f"Checked {len(calculations)} items")
            else:
                self.log_test("Basic Calculate Article Fields", False, "No calculations returned")
        else:
            self.log_test("Basic Calculate Article Fields", False, f"Request failed: {response.status_code}")

    def test_enhanced_calculate_article_fields(self):
        """Test that /api/enhanced-calculate returns both article_code and article_name"""
        print("\n🔬 Testing /api/enhanced-calculate article fields...")
        
        if not self.session_id or not self.inventory_session_id:
            self.log_test("Enhanced Calculate Article Fields", False, "Missing session IDs")
            return
        
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        response = requests.post(
            f"{self.base_url}/api/enhanced-calculate",
            json=calculation_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            calculations = data.get('calculations', [])
            
            if calculations:
                sample_item = calculations[0]
                
                # Check for article_code field
                has_article_code = 'article_code' in sample_item
                article_code_value = sample_item.get('article_code', 'N/A')
                self.log_test("Enhanced Calculate - article_code field", has_article_code,
                             f"Value: {article_code_value}")
                
                # Check for article_name field
                has_article_name = 'article_name' in sample_item
                article_name_value = sample_item.get('article_name', 'N/A')
                self.log_test("Enhanced Calculate - article_name field", has_article_name,
                             f"Value: {article_name_value}")
                
                # Check for inventory-specific fields
                has_inventory_fields = all(field in sample_item for field in [
                    'inventory_available', 'can_fulfill', 'inventory_status', 'inventory_status_text'
                ])
                self.log_test("Enhanced Calculate - Inventory fields present", has_inventory_fields,
                             f"Status: {sample_item.get('inventory_status', 'N/A')}")
                
                # Verify both article fields are present and have values
                both_fields_present = has_article_code and has_article_name
                self.log_test("Enhanced Calculate - Both article fields present", both_fields_present,
                             f"Code: {article_code_value}, Name: {article_name_value}")
                
                # Check all items have both fields
                all_items_have_fields = all(
                    'article_code' in item and 'article_name' in item 
                    for item in calculations
                )
                self.log_test("Enhanced Calculate - All items have article fields", all_items_have_fields,
                             f"Checked {len(calculations)} items")
            else:
                self.log_test("Enhanced Calculate Article Fields", False, "No calculations returned")
        else:
            self.log_test("Enhanced Calculate Article Fields", False, f"Request failed: {response.status_code}")

    def test_export_functionality_with_article_codes(self):
        """Test that export functionality works with article codes"""
        print("\n📤 Testing export functionality with article codes...")
        
        if not self.session_id:
            self.log_test("Export Functionality", False, "No session ID available")
            return
        
        # First get some calculation results to export
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        calc_response = requests.post(
            f"{self.base_url}/api/calculate/{self.session_id}",
            json=calculation_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if calc_response.status_code == 200:
            calc_data = calc_response.json()
            calculations = calc_data.get('calculations', [])
            
            if calculations:
                # Select first item for export
                selected_items = [calculations[0]]
                
                export_data = {
                    "selected_items": selected_items,
                    "session_id": self.session_id
                }
                
                export_response = requests.post(
                    f"{self.base_url}/api/export-critical/{self.session_id}",
                    json=export_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if export_response.status_code == 200:
                    # Check if response is Excel file
                    content_type = export_response.headers.get('content-type', '')
                    is_excel = 'spreadsheet' in content_type or 'excel' in content_type
                    
                    self.log_test("Export - Returns Excel file", is_excel,
                                 f"Content-Type: {content_type}")
                    
                    # Check if filename is present
                    content_disposition = export_response.headers.get('content-disposition', '')
                    has_filename = 'filename=' in content_disposition
                    self.log_test("Export - Has filename", has_filename,
                                 f"Disposition: {content_disposition}")
                    
                    # Check content length
                    content_length = len(export_response.content)
                    has_content = content_length > 0
                    self.log_test("Export - Has content", has_content,
                                 f"Size: {content_length} bytes")
                    
                    # Verify the selected item had both article fields
                    selected_item = selected_items[0]
                    has_both_fields = 'article_code' in selected_item and 'article_name' in selected_item
                    self.log_test("Export - Source data has article fields", has_both_fields,
                                 f"Code: {selected_item.get('article_code', 'N/A')}, Name: {selected_item.get('article_name', 'N/A')}")
                else:
                    self.log_test("Export Functionality", False, f"Export failed: {export_response.status_code}")
            else:
                self.log_test("Export Functionality", False, "No calculations available for export")
        else:
            self.log_test("Export Functionality", False, f"Failed to get calculations: {calc_response.status_code}")

    def test_data_consistency(self):
        """Test that article_code and article_name are consistent across endpoints"""
        print("\n🔍 Testing data consistency across endpoints...")
        
        if not self.session_id or not self.inventory_session_id:
            self.log_test("Data Consistency", False, "Missing session IDs")
            return
        
        # Get data from basic calculate
        basic_calc_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        basic_response = requests.post(
            f"{self.base_url}/api/calculate/{self.session_id}",
            json=basic_calc_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Get data from enhanced calculate
        enhanced_calc_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        enhanced_response = requests.post(
            f"{self.base_url}/api/enhanced-calculate",
            json=enhanced_calc_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if basic_response.status_code == 200 and enhanced_response.status_code == 200:
            basic_data = basic_response.json()
            enhanced_data = enhanced_response.json()
            
            basic_calcs = basic_data.get('calculations', [])
            enhanced_calcs = enhanced_data.get('calculations', [])
            
            if basic_calcs and enhanced_calcs:
                # Create mappings by article_code for comparison
                basic_map = {item['article_code']: item for item in basic_calcs}
                enhanced_map = {item['article_code']: item for item in enhanced_calcs}
                
                # Check if same article codes exist in both
                basic_codes = set(basic_map.keys())
                enhanced_codes = set(enhanced_map.keys())
                same_codes = basic_codes == enhanced_codes
                
                self.log_test("Data Consistency - Same article codes", same_codes,
                             f"Basic: {len(basic_codes)}, Enhanced: {len(enhanced_codes)}")
                
                # Check if article names match for same codes
                name_consistency = True
                for code in basic_codes.intersection(enhanced_codes):
                    basic_name = basic_map[code]['article_name']
                    enhanced_name = enhanced_map[code]['article_name']
                    if basic_name != enhanced_name:
                        name_consistency = False
                        print(f"   ⚠️ Name mismatch for {code}: '{basic_name}' vs '{enhanced_name}'")
                
                self.log_test("Data Consistency - Article names match", name_consistency,
                             f"Checked {len(basic_codes.intersection(enhanced_codes))} common codes")
            else:
                self.log_test("Data Consistency", False, "No calculations available for comparison")
        else:
            self.log_test("Data Consistency", False, "Failed to get data from both endpoints")

    def run_all_tests(self):
        """Run all article code and name field tests"""
        print("🚀 Starting Article Code & Name Field Tests")
        print("=" * 60)
        
        # Upload test data
        if not self.upload_test_data():
            print("❌ Failed to upload test data. Cannot proceed with tests.")
            return
        
        # Run all tests
        self.test_upload_excel_response_fields()
        self.test_basic_calculate_article_fields()
        self.test_enhanced_calculate_article_fields()
        self.test_export_functionality_with_article_codes()
        self.test_data_consistency()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All article code/name field tests passed!")
            print("✅ Backend APIs properly return both article_code and article_name fields")
            print("✅ Frontend can safely display article_code instead of article_name")
            return True
        else:
            print("⚠️ Some tests failed. Backend may have issues with article field consistency.")
            return False

if __name__ == "__main__":
    tester = ArticleCodeFieldTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)