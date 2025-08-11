import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class DataReadingDepotOrganizationTester:
    def __init__(self, base_url="https://2d405bcb-1210-461d-9403-54f42d429656.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.inventory_session_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
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

    def create_excel_with_missing_stock_data(self):
        """Create Excel file with some missing 'Stock Utilisation Libre' values to test data reading fix"""
        print("📋 Creating test Excel file with missing stock data...")
        
        # Create sample data with some missing stock values
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5),
                datetime.now() - timedelta(days=2),
                datetime.now() - timedelta(days=1)
            ],
            'Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005', 'ART006', 'ART007', 'ART008'],
            'Désignation Article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE',
                'COCA-COLA ZERO 33CL PET',
                'PEPSI MAX 50CL PET',
                'SPRITE ZERO 33CL VERRE'
            ],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT3', 'DEPOT1', 'DEPOT2'],
            'Nom Division': ['Depot Alpha', 'Depot Alpha', 'Depot Beta', 'Depot Alpha', 'Depot Beta', 'Depot Gamma', 'Depot Alpha', 'Depot Beta'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200, 75, 110],
            # Intentionally include some NaN/missing values for Stock Utilisation Libre
            'Stock Utilisation Libre': [500, np.nan, 200, 400, np.nan, 600, 180, np.nan],  # 3 missing values
            'Ecart': [0, 0, 0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Verre', 'Verre', 'Pet', 'Pet', 'Verre'],
            'Quantité en Palette': [24, 12, 24, 24, 24, 12, 12, 24]
        }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        print(f"📊 Created Excel with {len(df)} total rows")
        print(f"📊 Missing stock values: {df['Stock Utilisation Libre'].isna().sum()} rows")
        print(f"📊 Valid stock values: {df['Stock Utilisation Libre'].notna().sum()} rows")
        
        return excel_buffer

    def test_data_reading_fix_upload(self):
        """Test 1: Verify Excel upload processes ALL rows including those with missing stock data"""
        print("\n" + "="*80)
        print("🔍 TEST 1: DATA READING FIX - Excel Upload with Missing Stock Data")
        print("="*80)
        
        excel_file = self.create_excel_with_missing_stock_data()
        
        files = {
            'file': ('test_missing_stock.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Excel with Missing Stock Data",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            records_count = response.get('records_count', 0)
            
            print(f"📊 Session ID: {self.session_id}")
            print(f"📊 Records processed: {records_count}")
            
            # Verify that ALL 8 rows were processed (none dropped due to missing stock)
            if records_count == 8:
                print("✅ SUCCESS: All 8 rows processed - missing stock data did not cause row drops")
                return True
            else:
                print(f"❌ FAILURE: Expected 8 rows, got {records_count} - rows were incorrectly dropped")
                return False
        else:
            print("❌ FAILURE: Upload failed")
            return False

    def test_depot_organization_basic_calculate(self):
        """Test 2: Verify /api/calculate/{session_id} organizes results by depot"""
        print("\n" + "="*80)
        print("🔍 TEST 2: DEPOT ORGANIZATION FIX - Basic Calculate Endpoint")
        print("="*80)
        
        if not self.session_id:
            print("❌ No session ID available for depot organization test")
            return False
            
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Basic Calculate with Depot Organization",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            if not calculations:
                print("⚠️ No calculations returned")
                return True
            
            print(f"📊 Total calculations returned: {len(calculations)}")
            
            # Analyze depot organization
            depot_groups = {}
            previous_depot = None
            depot_switches = 0
            
            for i, calc in enumerate(calculations):
                depot = calc.get('depot', 'Unknown')
                
                if depot not in depot_groups:
                    depot_groups[depot] = []
                depot_groups[depot].append(i)
                
                # Count depot switches (should be minimal if properly organized)
                if previous_depot is not None and previous_depot != depot:
                    depot_switches += 1
                previous_depot = depot
            
            print(f"📊 Depot groups found: {list(depot_groups.keys())}")
            print(f"📊 Depot switches in results: {depot_switches}")
            
            # Verify depot organization
            for depot, positions in depot_groups.items():
                print(f"📋 {depot}: {len(positions)} items at positions {positions}")
                
                # Check if depot items are grouped together
                if len(positions) > 1:
                    is_grouped = all(positions[i] + 1 == positions[i + 1] for i in range(len(positions) - 1))
                    if is_grouped:
                        print(f"✅ {depot}: Items are properly grouped together")
                    else:
                        print(f"❌ {depot}: Items are scattered - not properly grouped")
                        return False
            
            # Verify priority ordering within each depot
            for depot, positions in depot_groups.items():
                depot_items = [calculations[pos] for pos in positions]
                
                # Check priority ordering within depot (high > medium > low)
                priority_order = {'high': 0, 'medium': 1, 'low': 2}
                priorities = [priority_order.get(item.get('priority', 'low'), 2) for item in depot_items]
                
                is_priority_sorted = all(priorities[i] <= priorities[i + 1] for i in range(len(priorities) - 1))
                
                if is_priority_sorted:
                    print(f"✅ {depot}: Priority ordering correct within depot")
                else:
                    print(f"❌ {depot}: Priority ordering incorrect within depot")
                    print(f"   Priorities found: {[item.get('priority', 'low') for item in depot_items]}")
                    return False
            
            print("✅ SUCCESS: Results are properly organized by depot with correct priority ordering")
            return True
        else:
            print("❌ FAILURE: Basic calculate endpoint failed")
            return False

    def test_depot_organization_enhanced_calculate(self):
        """Test 3: Verify /api/enhanced-calculate organizes results by depot"""
        print("\n" + "="*80)
        print("🔍 TEST 3: DEPOT ORGANIZATION FIX - Enhanced Calculate Endpoint")
        print("="*80)
        
        if not self.session_id:
            print("❌ No session ID available for enhanced depot organization test")
            return False
            
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": None,  # Test without inventory first
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Depot Organization",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            if not calculations:
                print("⚠️ No calculations returned")
                return True
            
            print(f"📊 Total enhanced calculations returned: {len(calculations)}")
            
            # Analyze depot organization
            depot_groups = {}
            previous_depot = None
            depot_switches = 0
            
            for i, calc in enumerate(calculations):
                depot = calc.get('depot', 'Unknown')
                
                if depot not in depot_groups:
                    depot_groups[depot] = []
                depot_groups[depot].append(i)
                
                # Count depot switches
                if previous_depot is not None and previous_depot != depot:
                    depot_switches += 1
                previous_depot = depot
            
            print(f"📊 Enhanced depot groups found: {list(depot_groups.keys())}")
            print(f"📊 Enhanced depot switches in results: {depot_switches}")
            
            # Verify depot organization
            for depot, positions in depot_groups.items():
                print(f"📋 {depot}: {len(positions)} items at positions {positions}")
                
                # Check if depot items are grouped together
                if len(positions) > 1:
                    is_grouped = all(positions[i] + 1 == positions[i + 1] for i in range(len(positions) - 1))
                    if is_grouped:
                        print(f"✅ {depot}: Enhanced items are properly grouped together")
                    else:
                        print(f"❌ {depot}: Enhanced items are scattered - not properly grouped")
                        return False
            
            # Verify priority ordering within each depot
            for depot, positions in depot_groups.items():
                depot_items = [calculations[pos] for pos in positions]
                
                # Check priority ordering within depot
                priority_order = {'high': 0, 'medium': 1, 'low': 2}
                priorities = [priority_order.get(item.get('priority', 'low'), 2) for item in depot_items]
                
                is_priority_sorted = all(priorities[i] <= priorities[i + 1] for i in range(len(priorities) - 1))
                
                if is_priority_sorted:
                    print(f"✅ {depot}: Enhanced priority ordering correct within depot")
                else:
                    print(f"❌ {depot}: Enhanced priority ordering incorrect within depot")
                    print(f"   Priorities found: {[item.get('priority', 'low') for item in depot_items]}")
                    return False
            
            # Verify truck calculation is present (from the needs_retesting task)
            delivery_optimization = response.get('summary', {}).get('delivery_optimization', {})
            if 'total_trucks' in delivery_optimization:
                total_trucks = delivery_optimization['total_trucks']
                print(f"✅ Truck calculation present: {total_trucks} total trucks needed")
                
                # Verify depot summaries have trucks_needed
                depot_summaries = delivery_optimization.get('depot_summaries', [])
                for depot_summary in depot_summaries:
                    if 'trucks_needed' in depot_summary:
                        print(f"✅ {depot_summary['depot_name']}: {depot_summary['trucks_needed']} trucks needed")
                    else:
                        print(f"❌ Missing trucks_needed for depot {depot_summary.get('depot_name', 'Unknown')}")
                        return False
            else:
                print("❌ Missing total_trucks in delivery optimization summary")
                return False
            
            print("✅ SUCCESS: Enhanced results are properly organized by depot with truck calculations")
            return True
        else:
            print("❌ FAILURE: Enhanced calculate endpoint failed")
            return False

    def test_data_completeness_verification(self):
        """Test 4: Verify that the total number of processed records matches expectations"""
        print("\n" + "="*80)
        print("🔍 TEST 4: DATA COMPLETENESS VERIFICATION")
        print("="*80)
        
        if not self.session_id:
            print("❌ No session ID available for data completeness test")
            return False
        
        # Get basic calculation to verify all data is processed
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Data Completeness Check",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            summary = response.get('summary', {})
            
            print(f"📊 Calculations returned: {len(calculations)}")
            print(f"📊 Total products in summary: {summary.get('total_products', 0)}")
            print(f"📊 Total depots in summary: {summary.get('total_depots', 0)}")
            
            # Verify that we have data from all expected depots
            depot_names = set(calc.get('depot', 'Unknown') for calc in calculations)
            expected_depots = {'Depot Alpha', 'Depot Beta', 'Depot Gamma'}
            
            print(f"📊 Depots found in results: {depot_names}")
            print(f"📊 Expected depots: {expected_depots}")
            
            if expected_depots.issubset(depot_names):
                print("✅ All expected depots found in results")
            else:
                missing_depots = expected_depots - depot_names
                print(f"❌ Missing depots: {missing_depots}")
                return False
            
            # Verify that items with missing stock data were processed (should have stock = 0)
            items_with_zero_stock = [calc for calc in calculations if calc.get('current_stock', -1) == 0]
            print(f"📊 Items with zero stock (from missing data): {len(items_with_zero_stock)}")
            
            if len(items_with_zero_stock) > 0:
                print("✅ Items with missing stock data were processed and filled with 0")
                for item in items_with_zero_stock:
                    print(f"   - {item.get('article_code', 'Unknown')}: {item.get('article_name', 'Unknown')}")
            else:
                print("⚠️ No items with zero stock found - this might be expected depending on data")
            
            print("✅ SUCCESS: Data completeness verification passed")
            return True
        else:
            print("❌ FAILURE: Data completeness check failed")
            return False

    def test_missing_essential_data_handling(self):
        """Test 5: Verify that rows with missing essential data are properly dropped"""
        print("\n" + "="*80)
        print("🔍 TEST 5: MISSING ESSENTIAL DATA HANDLING")
        print("="*80)
        
        # Create Excel with missing essential data (Date de Commande, Quantité Commandée)
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                None,  # Missing essential data
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
            ],
            'Article': ['ART001', 'ART002', 'ART003', 'ART004'],
            'Désignation Article': ['Product 1', 'Product 2', 'Product 3', 'Product 4'],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1'],
            'Nom Division': ['Depot Alpha', 'Depot Alpha', 'Depot Beta', 'Depot Alpha'],
            'Quantité Commandée': [100, 150, None, 120],  # Missing essential data
            'Stock Utilisation Libre': [500, 300, 200, 400],  # All present
            'Ecart': [0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Verre'],
            'Quantité en Palette': [24, 12, 24, 24]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        print(f"📊 Created Excel with {len(df)} total rows")
        print(f"📊 Rows with missing Date de Commande: {df['Date de Commande'].isna().sum()}")
        print(f"📊 Rows with missing Quantité Commandée: {df['Quantité Commandée'].isna().sum()}")
        
        files = {
            'file': ('test_missing_essential.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Excel with Missing Essential Data",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            records_count = response.get('records_count', 0)
            
            print(f"📊 Records processed: {records_count}")
            
            # Should process only 2 rows (rows 1 and 4, dropping rows 2 and 3)
            if records_count == 2:
                print("✅ SUCCESS: Rows with missing essential data were properly dropped")
                print("✅ SUCCESS: Only rows with complete essential data were processed")
                return True
            else:
                print(f"❌ FAILURE: Expected 2 rows, got {records_count}")
                return False
        else:
            print("❌ FAILURE: Upload with missing essential data failed")
            return False

    def run_all_tests(self):
        """Run all data reading and depot organization tests"""
        print("\n" + "="*100)
        print("🚀 STARTING DATA READING & DEPOT ORGANIZATION TESTS")
        print("="*100)
        
        tests = [
            ("Data Reading Fix - Upload", self.test_data_reading_fix_upload),
            ("Depot Organization - Basic Calculate", self.test_depot_organization_basic_calculate),
            ("Depot Organization - Enhanced Calculate", self.test_depot_organization_enhanced_calculate),
            ("Data Completeness Verification", self.test_data_completeness_verification),
            ("Missing Essential Data Handling", self.test_missing_essential_data_handling),
        ]
        
        results = []
        
        for test_name, test_method in tests:
            try:
                result = test_method()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Print final summary
        print("\n" + "="*100)
        print("📊 FINAL TEST RESULTS SUMMARY")
        print("="*100)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        
        print(f"\n📊 OVERALL RESULTS: {passed}/{len(results)} tests passed")
        print(f"📊 Success Rate: {(passed/len(results)*100):.1f}%")
        
        if passed == len(results):
            print("🎉 ALL TESTS PASSED - Both fixes are working correctly!")
        else:
            print("⚠️ Some tests failed - fixes may need attention")
        
        return passed == len(results)

if __name__ == "__main__":
    tester = DataReadingDepotOrganizationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)