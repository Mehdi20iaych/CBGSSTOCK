import requests
import sys
import json
import io
import pandas as pd
import math

class AdditionalEdgeTests:
    def __init__(self, base_url="https://bookworm-app-2.preview.emergentagent.com"):
        self.base_url = base_url
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
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_zero_negative_k_values_filtering(self):
        """Test that zero and negative K values are filtered out during upload"""
        print("\n" + "="*80)
        print("EDGE TEST: Zero and negative K values should be filtered out")
        print("="*80)
        
        # Create data with zero and negative K values
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005'],
            'Article': ['ART_ZERO', 'ART_NEG', 'ART_GOOD1', 'ART_GOOD2', 'ART_GOOD3'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5'],
            'Point d\'Expédition': ['M115', 'M120', 'M115', 'M120', 'M115'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Quantité Commandée': [100, 150, 80, 120, 90],
            'Stock Utilisation Libre': [50, 75, 40, 60, 45],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre', 'pet'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Produits par Palette': [0, -5, 15, 20, 25]  # Zero and negative values
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('zero_negative_k.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload with Zero/Negative K Values",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # Should only have 3 records (ART_GOOD1, ART_GOOD2, ART_GOOD3)
            expected_records = 3
            actual_records = response['summary']['total_records']
            
            if actual_records == expected_records:
                print(f"✅ Correct filtering: {actual_records} records kept (zero/negative K values filtered out)")
                
                # Verify only good articles remain
                articles = response['filters']['articles']
                expected_articles = {'ART_GOOD1', 'ART_GOOD2', 'ART_GOOD3'}
                actual_articles = set(articles)
                
                if actual_articles == expected_articles:
                    print(f"✅ Correct articles kept: {actual_articles}")
                    return True
                else:
                    print(f"❌ Expected articles {expected_articles}, got {actual_articles}")
            else:
                print(f"❌ Expected {expected_records} records, got {actual_records}")
        
        return False

    def test_mixed_depot_scenarios_with_different_k_values(self):
        """Test depot suggestions with articles having different K values across different depots"""
        print("\n" + "="*80)
        print("EDGE TEST: Mixed depot scenarios with different K values")
        print("="*80)
        
        # Create comprehensive test data
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006'],
            'Article': ['ART_MIXED1', 'ART_MIXED2', 'ART_MIXED1', 'ART_MIXED2', 'ART_UNIQUE1', 'ART_UNIQUE2'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'Point d\'Expédition': ['M115', 'M115', 'M120', 'M120', 'M115', 'M120'],  # Mixed depots
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 110],
            'Stock Utilisation Libre': [50, 75, 40, 60, 45, 55],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre', 'pet', 'ciel'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Produits par Palette': [12, 18, 12, 18, 24, 30]  # Same articles have same K values
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        # Create corresponding stock data
        stock_data = {
            'Division': ['M210'] * 10,
            'Article': ['ART_MIXED1', 'ART_MIXED2', 'ART_UNIQUE1', 'ART_UNIQUE2', 'ART_STOCK1', 'ART_STOCK2', 'ART_STOCK3', 'ART_STOCK4', 'ART_STOCK5', 'ART_STOCK6'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6', 'Desc7', 'Desc8', 'Desc9', 'Desc10'],
            'STOCK A DATE': [500, 300, 200, 400, 80, 120, 150, 180, 220, 250]  # Various stock levels
        }
        
        stock_df = pd.DataFrame(stock_data)
        stock_buffer = io.BytesIO()
        stock_df.to_excel(stock_buffer, index=False)
        stock_buffer.seek(0)
        
        # Upload commandes
        files = {
            'file': ('mixed_depot_k.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success1, response1 = self.run_test(
            "Upload Mixed Depot Commandes",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if not success1:
            return False
        
        # Upload stock
        files = {
            'file': ('mixed_stock.xlsx', stock_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success2, response2 = self.run_test(
            "Upload Mixed Stock",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if not success2:
            return False
        
        # Test depot suggestions for M115
        request_data = {'depot_name': 'M115', 'days': 10}
        
        success3, response3 = self.run_test(
            "Depot Suggestions M115 - Mixed K Values",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success3 and 'suggestions' in response3:
            suggestions = response3['suggestions']
            print(f"✅ Got {len(suggestions)} suggestions for M115")
            
            # Verify suggestions use correct K values
            expected_k_values = {
                'ART_MIXED1': 12, 'ART_MIXED2': 18, 'ART_UNIQUE1': 24, 'ART_UNIQUE2': 30,
                # Stock-only articles should use fallback 30
                'ART_STOCK1': 30, 'ART_STOCK2': 30, 'ART_STOCK3': 30, 'ART_STOCK4': 30, 'ART_STOCK5': 30, 'ART_STOCK6': 30
            }
            
            for suggestion in suggestions:
                article = suggestion['article']
                suggested_quantity = suggestion['suggested_quantity']
                suggested_palettes = suggestion['suggested_palettes']
                expected_k = expected_k_values.get(article, 30)
                expected_quantity = suggested_palettes * expected_k
                
                print(f"📊 Article {article}: {suggested_palettes} palettes × {expected_k} = {expected_quantity} (actual: {suggested_quantity})")
                
                if suggested_quantity != expected_quantity:
                    print(f"❌ Incorrect calculation for {article}")
                    return False
            
            print("✅ All mixed depot suggestions use correct K values")
            return True
        
        return False

    def test_comprehensive_calculation_verification(self):
        """Test comprehensive calculation to ensure all formulas work together"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST: Full calculation workflow verification")
        print("="*80)
        
        # Get calculations to verify the complete workflow
        calculation_data = {"days": 15}
        
        success, response = self.run_test(
            "Comprehensive Calculation Verification",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            print(f"✅ Got {len(calculations)} calculation results")
            
            # Verify each calculation has all required fields
            required_fields = ['article', 'depot', 'quantite_a_envoyer', 'palettes_needed', 'produits_par_palette', 'statut']
            
            for calc in calculations:
                for field in required_fields:
                    if field not in calc:
                        print(f"❌ Missing field {field} in calculation for {calc.get('article', 'unknown')}")
                        return False
                
                # Verify palettes calculation
                quantite = calc['quantite_a_envoyer']
                palettes = calc['palettes_needed']
                k_value = calc['produits_par_palette']
                
                expected_palettes = math.ceil(quantite / k_value) if quantite > 0 and k_value > 0 else 0
                
                if palettes != expected_palettes:
                    print(f"❌ Incorrect palettes for {calc['article']}: expected {expected_palettes}, got {palettes}")
                    return False
                
                print(f"✅ {calc['article']}: {quantite} products ÷ {k_value} = {palettes} palettes ({calc['statut']})")
            
            # Verify depot summary
            if 'depot_summary' in response:
                depot_summary = response['depot_summary']
                print(f"✅ Depot summary includes {len(depot_summary)} depots")
                
                for depot_info in depot_summary:
                    total_palettes = depot_info['total_palettes']
                    trucks_needed = depot_info['trucks_needed']
                    expected_trucks = math.ceil(total_palettes / 24) if total_palettes > 0 else 0
                    
                    if trucks_needed != expected_trucks:
                        print(f"❌ Incorrect trucks for {depot_info['depot']}: expected {expected_trucks}, got {trucks_needed}")
                        return False
            
            print("✅ Comprehensive calculation verification passed")
            return True
        
        return False

    def run_additional_edge_tests(self):
        """Run all additional edge tests"""
        print("\n" + "🧪" * 40)
        print("ADDITIONAL EDGE TESTS FOR QUANTITÉ SUGGÉRÉE")
        print("🧪" * 40)
        
        tests = [
            self.test_zero_negative_k_values_filtering,
            self.test_mixed_depot_scenarios_with_different_k_values,
            self.test_comprehensive_calculation_verification
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        print(f"\n🏁 ADDITIONAL TESTS SUMMARY:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")

if __name__ == "__main__":
    tester = AdditionalEdgeTests()
    tester.run_additional_edge_tests()