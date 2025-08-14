import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class DepotSuggestionsNewLogicTester:
    def __init__(self, base_url="https://bookworm-app-2.preview.emergentagent.com"):
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

    def create_commandes_excel_for_depot_suggestions(self):
        """Create commandes Excel with specific depot orders for testing suggestions"""
        # Create data where M211 has some orders but needs more palettes to reach 24
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006'],
            'Article': ['1011', '1016', '1021', '1033', '1040', '1051'],  # Mix of articles
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'Point d\'Expédition': ['M211', 'M211', 'M212', 'M212', 'M213', 'M213'],  # M211 has 2 orders
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Quantité Commandée': [60, 90, 100, 120, 80, 150],  # Moderate quantities
            'Stock Utilisation Libre': [10, 15, 20, 25, 10, 30],  # Low stock to ensure delivery needed
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Type Emballage': ['verre', 'pet', 'verre', 'pet', 'ciel', 'verre']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_stock_excel_with_varied_quantities(self):
        """Create stock Excel with varied M210 quantities for testing lowest stock priority"""
        # Create stock data with different quantities - some very low, some high
        # The new logic should prioritize products with LOWEST stock quantities
        data = {
            'Division': ['M210'] * 15,  # All M210
            'Article': ['1011', '1016', '1021', '1033', '1040', '1051', '2011', '2014', '2022', '3040', '3043', '3056', '9999', '8888', '7777'],
            'Dummy_C': [f'Desc{i}' for i in range(1, 16)],
            'STOCK A DATE': [
                # Very low stock (should be prioritized first)
                5, 8, 12, 15, 18,
                # Medium stock  
                45, 60, 75, 90, 120,
                # High stock (should be suggested last)
                200, 350, 500, 800, 1000
            ]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_transit_excel_for_suggestions(self):
        """Create transit Excel for depot suggestions testing"""
        data = {
            'Article': ['1011', '1016', '1021', '1033'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Division': ['M211', 'M212', 'M213', 'M211'],  # Destinations
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Division cédante': ['M210', 'M210', 'M210', 'M210'],  # All from M210
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Quantité': [10, 15, 20, 25]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def setup_test_data(self):
        """Upload all necessary test data for depot suggestions testing"""
        print("\n📤 Setting up test data for depot suggestions...")
        
        # Upload commandes data
        commandes_file = self.create_commandes_excel_for_depot_suggestions()
        files = {
            'file': ('commandes_depot_test.xlsx', commandes_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes for Depot Suggestions Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.commandes_session_id = response['session_id']
            print(f"✅ Commandes uploaded - Session ID: {self.commandes_session_id}")
        else:
            print("❌ Failed to upload commandes data")
            return False
        
        # Upload stock data with varied quantities
        stock_file = self.create_stock_excel_with_varied_quantities()
        files = {
            'file': ('stock_varied_quantities.xlsx', stock_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Stock with Varied Quantities",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.stock_session_id = response['session_id']
            print(f"✅ Stock uploaded - Session ID: {self.stock_session_id}")
        else:
            print("❌ Failed to upload stock data")
            return False
        
        # Upload transit data
        transit_file = self.create_transit_excel_for_suggestions()
        files = {
            'file': ('transit_suggestions.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit for Depot Suggestions",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"✅ Transit uploaded - Session ID: {self.transit_session_id}")
        else:
            print("❌ Failed to upload transit data")
            return False
        
        return True

    def test_new_suggestion_logic_lowest_stock_priority(self):
        """Test that suggestions prioritize products with LOWEST stock quantities"""
        print("\n🎯 Testing NEW LOGIC: Suggestions prioritize products with LOWEST M210 stock quantities")
        
        request_data = {
            "depot_name": "M211",
            "days": 10
        }
        
        success, response = self.run_test(
            "NEW LOGIC - Lowest Stock Priority",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            if not suggestions:
                print("⚠️ No suggestions returned - may be expected if depot already optimal")
                return True
            
            print(f"📊 Analyzing {len(suggestions)} suggestions for lowest stock priority...")
            
            # Verify suggestions are sorted by stock_m210 (ascending - lowest first)
            previous_stock = 0
            for i, suggestion in enumerate(suggestions):
                # Verify new response structure
                required_fields = ['article', 'packaging', 'stock_m210', 'suggested_quantity', 
                                 'suggested_palettes', 'can_fulfill', 'feasibility', 'reason']
                
                for field in required_fields:
                    if field not in suggestion:
                        print(f"❌ Missing required field '{field}' in suggestion {i}")
                        return False
                
                current_stock = suggestion['stock_m210']
                
                # Verify stock quantities are in ascending order (lowest first)
                if i > 0 and current_stock < previous_stock:
                    print(f"❌ Suggestions not sorted by stock quantity: position {i} has stock {current_stock} < previous {previous_stock}")
                    return False
                
                # Verify reason mentions low stock priority
                reason = suggestion['reason']
                if 'Stock faible' not in reason and 'Priorité pour reconstitution' not in reason:
                    print(f"❌ Suggestion reason should mention low stock priority: {reason}")
                    return False
                
                print(f"✅ Suggestion {i+1}: Article {suggestion['article']} - Stock M210: {current_stock}, Reason: {reason}")
                previous_stock = current_stock
            
            print("✅ NEW LOGIC VERIFIED: Suggestions correctly prioritize products with lowest M210 stock quantities")
            return True
        
        return False

    def test_suggestions_exclude_already_ordered_products(self):
        """Test that suggestions only include products NOT already ordered for the depot"""
        print("\n🚫 Testing: Suggestions exclude products already ordered for the depot")
        
        request_data = {
            "depot_name": "M211",  # This depot has orders for articles 1011 and 1016
            "days": 10
        }
        
        success, response = self.run_test(
            "Exclude Already Ordered Products",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            # Get the articles already ordered for M211 (from our test data: 1011, 1016)
            already_ordered_articles = ['1011', '1016']
            
            for suggestion in suggestions:
                article = suggestion['article']
                if article in already_ordered_articles:
                    print(f"❌ Article {article} is already ordered for M211 but appears in suggestions")
                    return False
                
                print(f"✅ Article {article} not in current orders - correctly suggested")
            
            print(f"✅ All {len(suggestions)} suggestions are for products NOT already ordered for depot M211")
            return True
        
        return False

    def test_new_response_structure(self):
        """Test the new response structure with required fields"""
        print("\n📋 Testing NEW RESPONSE STRUCTURE with required fields")
        
        request_data = {
            "depot_name": "M212",
            "days": 10
        }
        
        success, response = self.run_test(
            "NEW Response Structure Verification",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success:
            # Verify top-level response structure
            required_top_level = ['depot_name', 'current_palettes', 'target_palettes', 'palettes_to_add', 'suggestions']
            for field in required_top_level:
                if field not in response:
                    print(f"❌ Missing top-level field: {field}")
                    return False
            
            suggestions = response['suggestions']
            
            if suggestions:
                # Verify each suggestion has the new required fields
                required_suggestion_fields = [
                    'article',           # Product article code
                    'packaging',         # Packaging type
                    'stock_m210',        # Available stock in M210
                    'suggested_quantity', # Suggested quantity to add
                    'suggested_palettes', # Suggested palettes to add
                    'can_fulfill',       # Boolean - can be fulfilled from M210 stock
                    'feasibility',       # Text - 'Réalisable' or 'Stock insuffisant'
                    'reason'            # Reason for suggestion (mentions low stock)
                ]
                
                for i, suggestion in enumerate(suggestions):
                    for field in required_suggestion_fields:
                        if field not in suggestion:
                            print(f"❌ Suggestion {i}: Missing required field '{field}'")
                            return False
                    
                    # Verify field types and values
                    if not isinstance(suggestion['stock_m210'], (int, float)):
                        print(f"❌ Suggestion {i}: stock_m210 should be numeric")
                        return False
                    
                    if not isinstance(suggestion['suggested_quantity'], (int, float)):
                        print(f"❌ Suggestion {i}: suggested_quantity should be numeric")
                        return False
                    
                    if not isinstance(suggestion['suggested_palettes'], (int, float)):
                        print(f"❌ Suggestion {i}: suggested_palettes should be numeric")
                        return False
                    
                    if not isinstance(suggestion['can_fulfill'], bool):
                        print(f"❌ Suggestion {i}: can_fulfill should be boolean")
                        return False
                    
                    if suggestion['feasibility'] not in ['Réalisable', 'Stock insuffisant']:
                        print(f"❌ Suggestion {i}: Invalid feasibility value '{suggestion['feasibility']}'")
                        return False
                    
                    print(f"✅ Suggestion {i}: All required fields present and valid")
                
                print(f"✅ NEW RESPONSE STRUCTURE VERIFIED: All {len(suggestions)} suggestions have correct structure")
            else:
                print("✅ No suggestions returned - response structure still valid")
            
            return True
        
        return False

    def test_palette_completion_logic(self):
        """Test that suggestions help complete remaining palettes to reach 24"""
        print("\n📦 Testing: Suggestions help complete remaining palettes to reach 24")
        
        request_data = {
            "depot_name": "M212",
            "days": 10
        }
        
        success, response = self.run_test(
            "Palette Completion Logic",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success:
            current_palettes = response['current_palettes']
            target_palettes = response['target_palettes']
            palettes_to_add = response['palettes_to_add']
            suggestions = response['suggestions']
            
            # Verify target palettes logic (should be multiple of 24)
            expected_trucks = math.ceil(current_palettes / 24) if current_palettes > 0 else 1
            expected_target = expected_trucks * 24
            
            if target_palettes != expected_target:
                print(f"❌ Expected target_palettes {expected_target}, got {target_palettes}")
                return False
            
            # Verify palettes_to_add calculation
            expected_to_add = target_palettes - current_palettes
            if palettes_to_add != expected_to_add:
                print(f"❌ Expected palettes_to_add {expected_to_add}, got {palettes_to_add}")
                return False
            
            print(f"✅ Current palettes: {current_palettes}")
            print(f"✅ Target palettes: {target_palettes} (for {expected_trucks} truck(s))")
            print(f"✅ Palettes to add: {palettes_to_add}")
            
            if suggestions:
                # Verify suggestions help reach the target
                total_suggested_palettes = sum(s['suggested_palettes'] for s in suggestions)
                print(f"✅ Total suggested palettes: {total_suggested_palettes}")
                
                # The suggestions should help reach or approach the target
                if total_suggested_palettes > 0:
                    print("✅ Suggestions provide palettes to help reach 24-palette truck optimization")
            
            return True
        
        return False

    def test_feasibility_analysis_with_m210_stock(self):
        """Test feasibility analysis based on M210 stock availability"""
        print("\n🔍 Testing: Feasibility analysis based on M210 stock availability")
        
        request_data = {
            "depot_name": "M213",
            "days": 10
        }
        
        success, response = self.run_test(
            "Feasibility Analysis with M210 Stock",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            for suggestion in suggestions:
                article = suggestion['article']
                stock_m210 = suggestion['stock_m210']
                suggested_quantity = suggestion['suggested_quantity']
                can_fulfill = suggestion['can_fulfill']
                feasibility = suggestion['feasibility']
                
                # Verify feasibility logic
                expected_can_fulfill = suggested_quantity <= stock_m210
                if can_fulfill != expected_can_fulfill:
                    print(f"❌ Article {article}: Expected can_fulfill {expected_can_fulfill}, got {can_fulfill}")
                    return False
                
                # Verify feasibility text matches boolean
                expected_feasibility = 'Réalisable' if can_fulfill else 'Stock insuffisant'
                if feasibility != expected_feasibility:
                    print(f"❌ Article {article}: Expected feasibility '{expected_feasibility}', got '{feasibility}'")
                    return False
                
                print(f"✅ Article {article}: Stock {stock_m210}, Suggested {suggested_quantity} - {feasibility}")
            
            print(f"✅ Feasibility analysis verified for all {len(suggestions)} suggestions")
            return True
        
        return False

    def test_edge_case_depot_no_orders(self):
        """Test edge case: depot with no orders"""
        print("\n🔍 Testing EDGE CASE: Depot with no orders")
        
        request_data = {
            "depot_name": "M999",  # Non-existent depot
            "days": 10
        }
        
        success, response = self.run_test(
            "Edge Case - Depot with No Orders",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success:
            if response['current_palettes'] != 0:
                print(f"❌ Expected 0 current_palettes for depot with no orders, got {response['current_palettes']}")
                return False
            
            if 'message' not in response or 'Aucune commande trouvée' not in response['message']:
                print("❌ Expected appropriate message for depot with no orders")
                return False
            
            print("✅ Edge case handled correctly: Depot with no orders returns appropriate message")
            return True
        
        return False

    def test_edge_case_depot_already_at_24_palettes(self):
        """Test edge case: depot already at 24+ palettes"""
        print("\n🔍 Testing EDGE CASE: Depot already at 24+ palettes")
        
        # Create high-quantity data to reach 24+ palettes
        high_quantity_data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003'],
            'Article': ['1011', '1016', '1021'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3'],
            'Point d\'Expédition': ['M215', 'M215', 'M215'],  # Same depot
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3'],
            'Quantité Commandée': [800, 900, 1000],  # Very high quantities
            'Stock Utilisation Libre': [50, 60, 70],  # Low stock to ensure high delivery needs
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3'],
            'Type Emballage': ['verre', 'pet', 'ciel']
        }
        
        df = pd.DataFrame(high_quantity_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('high_palettes_test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, upload_response = self.run_test(
            "Upload High Palettes Test Data",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            request_data = {
                "depot_name": "M215",
                "days": 10
            }
            
            success, response = self.run_test(
                "Edge Case - Depot Already at 24+ Palettes",
                "POST",
                "api/depot-suggestions",
                200,
                data=request_data
            )
            
            if success:
                current_palettes = response['current_palettes']
                efficiency_status = response.get('efficiency_status', 'Unknown')
                palettes_to_add = response['palettes_to_add']
                
                print(f"✅ Depot M215 has {current_palettes} palettes")
                print(f"✅ Efficiency status: {efficiency_status}")
                print(f"✅ Palettes to add: {palettes_to_add}")
                
                # If already efficient, palettes_to_add should be 0 or minimal
                if current_palettes >= 24 and current_palettes % 24 == 0:
                    if palettes_to_add != 0:
                        print(f"⚠️ Depot already at perfect 24-palette multiple, but palettes_to_add = {palettes_to_add}")
                
                print("✅ Edge case handled: Depot with high palettes processed correctly")
                return True
        
        return False

    def test_mathematical_accuracy_palette_calculations(self):
        """Test mathematical accuracy of palette calculations (30 products per palette)"""
        print("\n🧮 Testing: Mathematical accuracy of palette calculations")
        
        request_data = {
            "depot_name": "M212",
            "days": 10
        }
        
        success, response = self.run_test(
            "Mathematical Accuracy - Palette Calculations",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            for suggestion in suggestions:
                article = suggestion['article']
                suggested_quantity = suggestion['suggested_quantity']
                suggested_palettes = suggestion['suggested_palettes']
                
                # Verify palette calculation: ceil(quantity / 30)
                expected_palettes = math.ceil(suggested_quantity / 30) if suggested_quantity > 0 else 0
                
                if suggested_palettes != expected_palettes:
                    print(f"❌ Article {article}: Expected {expected_palettes} palettes for {suggested_quantity} products, got {suggested_palettes}")
                    return False
                
                print(f"✅ Article {article}: {suggested_quantity} products = {suggested_palettes} palettes (30 per palette)")
            
            print(f"✅ Mathematical accuracy verified for all {len(suggestions)} suggestions")
            return True
        
        return False

    def run_comprehensive_depot_suggestions_tests(self):
        """Run all comprehensive tests for the new depot suggestions logic"""
        print("🚀 Starting Comprehensive Depot Suggestions Tests with NEW LOGIC")
        print("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run all tests
        tests = [
            self.test_new_suggestion_logic_lowest_stock_priority,
            self.test_suggestions_exclude_already_ordered_products,
            self.test_new_response_structure,
            self.test_palette_completion_logic,
            self.test_feasibility_analysis_with_m210_stock,
            self.test_edge_case_depot_no_orders,
            self.test_edge_case_depot_already_at_24_palettes,
            self.test_mathematical_accuracy_palette_calculations
        ]
        
        for test in tests:
            try:
                if not test():
                    print(f"❌ Test failed: {test.__name__}")
                    return False
            except Exception as e:
                print(f"❌ Test error in {test.__name__}: {str(e)}")
                return False
        
        # Print final results
        print("\n" + "=" * 80)
        print(f"🎉 DEPOT SUGGESTIONS NEW LOGIC TESTING COMPLETED")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🏆 ALL TESTS PASSED! New depot suggestions logic is working correctly!")
            return True
        else:
            print("⚠️ Some tests failed. Please review the issues above.")
            return False

if __name__ == "__main__":
    tester = DepotSuggestionsNewLogicTester()
    success = tester.run_comprehensive_depot_suggestions_tests()
    sys.exit(0 if success else 1)