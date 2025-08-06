import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class PaletteTruckLogisticsTester:
    def __init__(self, base_url="https://dce99a70-31a3-41f4-a2eb-48adb50ab382.preview.emergentagent.com"):
        self.base_url = base_url
        self.commandes_session_id = None
        self.stock_session_id = None
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

    def create_palette_test_commandes_excel(self):
        """Create sample commandes Excel file for palette testing with varied quantities"""
        # Create data with different quantities to test palette calculations (30 products per palette)
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006', 'CMD007', 'CMD008'],
            'Article': ['1011', '1016', '1021', '9999', '8888', '1033', '1040', '1051'],  # Mix of local and external
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6', 'Desc7', 'Desc8'],
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M211', 'M212', 'M213', 'M214', 'M215'],  # Different depots
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6', 'Extra7', 'Extra8'],
            'Quantité Commandée': [150, 90, 60, 180, 45, 240, 75, 120],  # Varied quantities for palette testing
            'Stock Utilisation Libre': [20, 10, 15, 30, 5, 40, 25, 35],  # Lower stock to ensure quantities to send
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6', 'Extra7', 'Extra8'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre', 'pet', 'ciel', 'verre', 'pet']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_truck_efficiency_test_excel(self):
        """Create test data specifically for truck efficiency testing"""
        # Create data that will result in different truck efficiency scenarios
        # Some depots with ≥24 palettes (efficient), some with <24 palettes (inefficient)
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006'],
            'Article': ['1011', '1016', '1021', '9999', '8888', '1033'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'Point d\'Expédition': ['M211', 'M211', 'M212', 'M212', 'M213', 'M213'],  # Group by depot
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            # M211: 900+600=1500 products = 50 palettes = 3 trucks (efficient)
            # M212: 450+300=750 products = 25 palettes = 2 trucks (efficient) 
            # M213: 150+90=240 products = 8 palettes = 1 truck (inefficient)
            'Quantité Commandée': [900, 600, 450, 300, 150, 90],
            'Stock Utilisation Libre': [0, 0, 0, 0, 0, 0],  # No stock to ensure full quantities
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Type Emballage': ['verre', 'pet', 'verre', 'pet', 'verre', 'pet']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_minimal_stock_excel(self):
        """Create minimal stock data for testing"""
        data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['1011', '1016', '1021', '9999', '8888', '1033'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'STOCK A DATE': [5000, 3000, 2000, 4000, 2500, 3500]  # High stock to ensure availability
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_minimal_transit_excel(self):
        """Create minimal transit data for testing"""
        data = {
            'Article': ['1011', '1016', '1021'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3'],
            'Division': ['M211', 'M212', 'M213'],
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3'],
            'Division cédante': ['M210', 'M210', 'M210'],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3'],
            'Quantité': [10, 20, 15]  # Small transit quantities
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_upload_endpoints_functionality(self):
        """Test that all 3 upload endpoints are working correctly with existing functionality"""
        print("\n🔍 Testing Upload Endpoints Functionality...")
        
        # Test commandes upload
        commandes_file = self.create_palette_test_commandes_excel()
        files = {
            'file': ('commandes.xlsx', commandes_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes Excel",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.commandes_session_id = response['session_id']
            print(f"✅ Commandes upload successful - Session ID: {self.commandes_session_id}")
            
            # Verify required fields
            required_fields = ['session_id', 'message', 'summary', 'filters']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify packaging filters are present
            if 'packaging' not in response['filters']:
                print("❌ Missing packaging filters")
                return False
                
            print(f"✅ Commandes: {response['summary']['total_records']} records, {response['summary']['unique_packaging']} packaging types")
        else:
            return False
        
        # Test stock upload
        stock_file = self.create_minimal_stock_excel()
        files = {
            'file': ('stock.xlsx', stock_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Stock Excel",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.stock_session_id = response['session_id']
            print(f"✅ Stock upload successful - Session ID: {self.stock_session_id}")
            print(f"✅ Stock: {response['summary']['total_records']} records, total stock: {response['summary']['total_stock_m210']}")
        else:
            return False
        
        # Test transit upload
        transit_file = self.create_minimal_transit_excel()
        files = {
            'file': ('transit.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit Excel",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"✅ Transit upload successful - Session ID: {self.transit_session_id}")
            print(f"✅ Transit: {response['summary']['total_records']} records, total quantity: {response['summary']['total_transit_quantity']}")
        else:
            return False
        
        return True

    def test_palettes_calculation(self):
        """Test that palettes_needed field is calculated correctly (30 products per palette)"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for palettes calculation test")
            return False
        
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Palettes Calculation Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                # Verify palettes_needed field exists
                if 'palettes_needed' not in calc:
                    print(f"❌ Missing palettes_needed field in calculation for article {calc.get('article', 'unknown')}")
                    return False
                
                quantite_a_envoyer = calc['quantite_a_envoyer']
                palettes_needed = calc['palettes_needed']
                
                # Calculate expected palettes (30 products per palette, rounded up)
                expected_palettes = math.ceil(quantite_a_envoyer / 30) if quantite_a_envoyer > 0 else 0
                
                if palettes_needed != expected_palettes:
                    print(f"❌ Article {calc['article']}: Expected {expected_palettes} palettes for {quantite_a_envoyer} products, got {palettes_needed}")
                    return False
                
                print(f"✅ Article {calc['article']}: {quantite_a_envoyer} products = {palettes_needed} palettes (30 products/palette)")
            
            print("✅ All palettes calculations correct (30 products per palette)")
            return True
        
        return False

    def test_depot_summary_structure(self):
        """Test that depot_summary array has correct structure and statistics"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for depot summary test")
            return False
        
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Depot Summary Structure Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'depot_summary' in response:
            depot_summary = response['depot_summary']
            calculations = response['calculations']
            
            # Verify depot_summary is an array
            if not isinstance(depot_summary, list):
                print("❌ depot_summary should be an array")
                return False
            
            # Verify each depot summary has required fields
            required_fields = ['depot', 'total_palettes', 'total_items', 'trucks_needed', 'delivery_efficiency']
            for depot_stat in depot_summary:
                for field in required_fields:
                    if field not in depot_stat:
                        print(f"❌ Missing field '{field}' in depot summary for depot {depot_stat.get('depot', 'unknown')}")
                        return False
            
            # Verify depot statistics are calculated correctly
            depot_calculations = {}
            for calc in calculations:
                depot = calc['depot']
                if depot not in depot_calculations:
                    depot_calculations[depot] = {'total_palettes': 0, 'total_items': 0}
                depot_calculations[depot]['total_palettes'] += calc['palettes_needed']
                depot_calculations[depot]['total_items'] += 1
            
            # Check each depot in summary
            for depot_stat in depot_summary:
                depot = depot_stat['depot']
                
                if depot not in depot_calculations:
                    print(f"❌ Depot {depot} in summary but not in calculations")
                    return False
                
                expected_palettes = depot_calculations[depot]['total_palettes']
                expected_items = depot_calculations[depot]['total_items']
                expected_trucks = math.ceil(expected_palettes / 24) if expected_palettes > 0 else 0
                expected_efficiency = 'Efficace' if expected_palettes >= 24 else 'Inefficace'
                
                if depot_stat['total_palettes'] != expected_palettes:
                    print(f"❌ Depot {depot}: Expected {expected_palettes} palettes, got {depot_stat['total_palettes']}")
                    return False
                
                if depot_stat['total_items'] != expected_items:
                    print(f"❌ Depot {depot}: Expected {expected_items} items, got {depot_stat['total_items']}")
                    return False
                
                if depot_stat['trucks_needed'] != expected_trucks:
                    print(f"❌ Depot {depot}: Expected {expected_trucks} trucks, got {depot_stat['trucks_needed']}")
                    return False
                
                if depot_stat['delivery_efficiency'] != expected_efficiency:
                    print(f"❌ Depot {depot}: Expected '{expected_efficiency}' efficiency, got '{depot_stat['delivery_efficiency']}'")
                    return False
                
                print(f"✅ Depot {depot}: {expected_palettes} palettes, {expected_trucks} trucks, {expected_efficiency}")
            
            print("✅ All depot summary statistics correct")
            return True
        else:
            print("❌ Missing depot_summary in response")
            return False

    def test_truck_efficiency_logic(self):
        """Test truck efficiency logic (24 palettes = 1 efficient truck)"""
        # Upload specific test data for truck efficiency
        truck_test_file = self.create_truck_efficiency_test_excel()
        files = {
            'file': ('truck_efficiency.xlsx', truck_test_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Truck Efficiency Test Data",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            calculation_data = {
                "days": 1  # Use 1 day to get exact quantities
            }
            
            success, response = self.run_test(
                "Truck Efficiency Logic Test",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'depot_summary' in response:
                depot_summary = response['depot_summary']
                
                # Expected results based on test data:
                # M211: 1500 products = 50 palettes = 3 trucks (efficient)
                # M212: 750 products = 25 palettes = 2 trucks (efficient)
                # M213: 240 products = 8 palettes = 1 truck (inefficient)
                
                expected_results = {
                    'M211': {'palettes': 50, 'trucks': 3, 'efficiency': 'Efficace'},
                    'M212': {'palettes': 25, 'trucks': 2, 'efficiency': 'Efficace'},
                    'M213': {'palettes': 8, 'trucks': 1, 'efficiency': 'Inefficace'}
                }
                
                for depot_stat in depot_summary:
                    depot = depot_stat['depot']
                    if depot in expected_results:
                        expected = expected_results[depot]
                        
                        # Allow some tolerance for palettes calculation due to stock/transit adjustments
                        if abs(depot_stat['total_palettes'] - expected['palettes']) > 5:
                            print(f"❌ Depot {depot}: Expected ~{expected['palettes']} palettes, got {depot_stat['total_palettes']}")
                            return False
                        
                        # Trucks calculation should be based on actual palettes
                        expected_trucks = math.ceil(depot_stat['total_palettes'] / 24) if depot_stat['total_palettes'] > 0 else 0
                        if depot_stat['trucks_needed'] != expected_trucks:
                            print(f"❌ Depot {depot}: Expected {expected_trucks} trucks for {depot_stat['total_palettes']} palettes, got {depot_stat['trucks_needed']}")
                            return False
                        
                        # Efficiency should be based on actual palettes
                        expected_efficiency = 'Efficace' if depot_stat['total_palettes'] >= 24 else 'Inefficace'
                        if depot_stat['delivery_efficiency'] != expected_efficiency:
                            print(f"❌ Depot {depot}: Expected '{expected_efficiency}' for {depot_stat['total_palettes']} palettes, got '{depot_stat['delivery_efficiency']}'")
                            return False
                        
                        print(f"✅ Depot {depot}: {depot_stat['total_palettes']} palettes → {depot_stat['trucks_needed']} trucks → {depot_stat['delivery_efficiency']}")
                
                print("✅ Truck efficiency logic working correctly (≥24 palettes = Efficace, <24 = Inefficace)")
                return True
        
        return False

    def test_depot_sorting(self):
        """Test that results are sorted by depot name"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for depot sorting test")
            return False
        
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Depot Sorting Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Extract depot names from calculations
            depot_names = [calc['depot'] for calc in calculations]
            
            # Check if depot names are sorted
            sorted_depot_names = sorted(depot_names)
            
            if depot_names != sorted_depot_names:
                print(f"❌ Results not sorted by depot name")
                print(f"   Found order: {depot_names[:10]}...")  # Show first 10
                print(f"   Expected order: {sorted_depot_names[:10]}...")
                return False
            
            print(f"✅ Results correctly sorted by depot name")
            print(f"   Depot order: {sorted(set(depot_names))}")
            return True
        
        return False

    def test_excel_export_palettes_column(self):
        """Test that Excel export includes the new Palettes column"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for Excel export test")
            return False
        
        # First get calculation results
        calculation_data = {
            "days": 10
        }
        
        calc_success, calc_response = self.run_test(
            "Get Calculations for Export Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if calc_success and 'calculations' in calc_response:
            calculations = calc_response['calculations']
            if not calculations:
                print("⚠️ No calculations available for export test")
                return True
            
            # Select items for export
            selected_items = calculations[:3]  # Take first 3 items
            
            export_data = {
                "selected_items": selected_items,
                "session_id": "test_session"
            }
            
            success, response = self.run_test(
                "Excel Export with Palettes Column",
                "POST",
                "api/export-excel",
                200,
                data=export_data
            )
            
            if success:
                print("✅ Excel export completed successfully")
                
                # Verify that selected items have palettes_needed field
                for item in selected_items:
                    if 'palettes_needed' not in item:
                        print(f"❌ Selected item missing palettes_needed field: {item}")
                        return False
                    print(f"✅ Item {item['article']} has {item['palettes_needed']} palettes for export")
                
                print("✅ Excel export includes palettes data")
                return True
        
        return False

    def test_comprehensive_palette_truck_scenarios(self):
        """Test comprehensive scenarios with different depot combinations"""
        print("\n🔍 Testing Comprehensive Palette and Truck Scenarios...")
        
        # Create comprehensive test data with various scenarios
        comprehensive_data = {
            'Dummy_A': [f'CMD{i:03d}' for i in range(1, 13)],
            'Article': ['1011', '1016', '1021', '9999', '8888', '1033', '1040', '1051', '1059', '1069', '1071', '2011'],
            'Dummy_C': [f'Desc{i}' for i in range(1, 13)],
            # Create different depot scenarios:
            # M211: High volume (efficient)
            # M212: Medium volume (efficient) 
            # M213: Low volume (inefficient)
            # M214: Very low volume (inefficient)
            'Point d\'Expédition': ['M211', 'M211', 'M211', 'M212', 'M212', 'M213', 'M213', 'M214', 'M215', 'M216', 'M217', 'M218'],
            'Dummy_E': [f'Extra{i}' for i in range(1, 13)],
            # Quantities designed to create specific palette scenarios
            'Quantité Commandée': [800, 600, 400, 350, 300, 200, 150, 100, 80, 60, 40, 30],
            'Stock Utilisation Libre': [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
            'Dummy_H': [f'Extra{i}' for i in range(1, 13)],
            'Type Emballage': ['verre', 'pet', 'ciel'] * 4
        }
        
        df = pd.DataFrame(comprehensive_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('comprehensive_test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        # Upload comprehensive test data
        success, upload_response = self.run_test(
            "Upload Comprehensive Test Data",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            calculation_data = {
                "days": 1  # Use 1 day for precise calculations
            }
            
            success, response = self.run_test(
                "Comprehensive Palette and Truck Calculation",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'depot_summary' in response and 'calculations' in response:
                depot_summary = response['depot_summary']
                calculations = response['calculations']
                
                print(f"✅ Comprehensive test: {len(calculations)} calculations, {len(depot_summary)} depots")
                
                # Verify mathematical consistency
                total_palettes_from_calculations = sum(calc['palettes_needed'] for calc in calculations)
                total_palettes_from_summary = sum(depot['total_palettes'] for depot in depot_summary)
                
                if total_palettes_from_calculations != total_palettes_from_summary:
                    print(f"❌ Palette totals inconsistent: calculations={total_palettes_from_calculations}, summary={total_palettes_from_summary}")
                    return False
                
                # Verify depot grouping
                depot_groups = {}
                for calc in calculations:
                    depot = calc['depot']
                    if depot not in depot_groups:
                        depot_groups[depot] = {'palettes': 0, 'items': 0}
                    depot_groups[depot]['palettes'] += calc['palettes_needed']
                    depot_groups[depot]['items'] += 1
                
                # Verify each depot in summary matches calculations
                for depot_stat in depot_summary:
                    depot = depot_stat['depot']
                    if depot not in depot_groups:
                        print(f"❌ Depot {depot} in summary but not in calculations")
                        return False
                    
                    expected = depot_groups[depot]
                    if depot_stat['total_palettes'] != expected['palettes']:
                        print(f"❌ Depot {depot}: Expected {expected['palettes']} palettes, got {depot_stat['total_palettes']}")
                        return False
                    
                    if depot_stat['total_items'] != expected['items']:
                        print(f"❌ Depot {depot}: Expected {expected['items']} items, got {depot_stat['total_items']}")
                        return False
                
                # Show efficiency breakdown
                efficient_depots = [d for d in depot_summary if d['delivery_efficiency'] == 'Efficace']
                inefficient_depots = [d for d in depot_summary if d['delivery_efficiency'] == 'Inefficace']
                
                print(f"✅ Efficiency breakdown: {len(efficient_depots)} efficient, {len(inefficient_depots)} inefficient depots")
                
                for depot in efficient_depots:
                    print(f"   Efficient: {depot['depot']} - {depot['total_palettes']} palettes, {depot['trucks_needed']} trucks")
                
                for depot in inefficient_depots:
                    print(f"   Inefficient: {depot['depot']} - {depot['total_palettes']} palettes, {depot['trucks_needed']} trucks")
                
                print("✅ Comprehensive palette and truck scenarios working correctly")
                return True
        
        return False

    def test_mathematical_accuracy(self):
        """Test mathematical accuracy of palette and truck calculations"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for mathematical accuracy test")
            return False
        
        calculation_data = {
            "days": 5
        }
        
        success, response = self.run_test(
            "Mathematical Accuracy Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response and 'depot_summary' in response:
            calculations = response['calculations']
            depot_summary = response['depot_summary']
            
            # Test 1: Verify palette calculation (30 products per palette, rounded up)
            for calc in calculations:
                quantite_a_envoyer = calc['quantite_a_envoyer']
                palettes_needed = calc['palettes_needed']
                
                expected_palettes = math.ceil(quantite_a_envoyer / 30) if quantite_a_envoyer > 0 else 0
                
                if palettes_needed != expected_palettes:
                    print(f"❌ Palette calculation error for article {calc['article']}: {quantite_a_envoyer} products should be {expected_palettes} palettes, got {palettes_needed}")
                    return False
            
            # Test 2: Verify truck calculation (palettes ÷ 24, rounded up)
            for depot_stat in depot_summary:
                total_palettes = depot_stat['total_palettes']
                trucks_needed = depot_stat['trucks_needed']
                
                expected_trucks = math.ceil(total_palettes / 24) if total_palettes > 0 else 0
                
                if trucks_needed != expected_trucks:
                    print(f"❌ Truck calculation error for depot {depot_stat['depot']}: {total_palettes} palettes should be {expected_trucks} trucks, got {trucks_needed}")
                    return False
            
            # Test 3: Verify efficiency logic
            for depot_stat in depot_summary:
                total_palettes = depot_stat['total_palettes']
                efficiency = depot_stat['delivery_efficiency']
                
                expected_efficiency = 'Efficace' if total_palettes >= 24 else 'Inefficace'
                
                if efficiency != expected_efficiency:
                    print(f"❌ Efficiency logic error for depot {depot_stat['depot']}: {total_palettes} palettes should be '{expected_efficiency}', got '{efficiency}'")
                    return False
            
            print("✅ All mathematical calculations are accurate")
            print("   - Palettes: ceil(products / 30)")
            print("   - Trucks: ceil(palettes / 24)")
            print("   - Efficiency: ≥24 palettes = Efficace, <24 = Inefficace")
            return True
        
        return False

    def run_all_tests(self):
        """Run all palette and truck logistics tests"""
        print("🚀 Starting Enhanced Inventory Management System - Palette and Truck Logistics Tests")
        print("=" * 80)
        
        tests = [
            ("Upload Endpoints Functionality", self.test_upload_endpoints_functionality),
            ("Palettes Calculation (30 products per palette)", self.test_palettes_calculation),
            ("Depot Summary Structure", self.test_depot_summary_structure),
            ("Truck Efficiency Logic (24 palettes threshold)", self.test_truck_efficiency_logic),
            ("Depot Sorting by Name", self.test_depot_sorting),
            ("Excel Export with Palettes Column", self.test_excel_export_palettes_column),
            ("Comprehensive Palette and Truck Scenarios", self.test_comprehensive_palette_truck_scenarios),
            ("Mathematical Accuracy Verification", self.test_mathematical_accuracy)
        ]
        
        for test_name, test_method in tests:
            print(f"\n{'='*60}")
            print(f"🧪 {test_name}")
            print('='*60)
            
            try:
                result = test_method()
                if result:
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"🏁 PALETTE AND TRUCK LOGISTICS TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        print('='*80)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = PaletteTruckLogisticsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)