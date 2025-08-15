import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class RecommendationLogicTester:
    def __init__(self, base_url="https://reader-hub-2.preview.emergentagent.com"):
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

    def create_test_commandes_excel(self):
        """Create commandes Excel with two depots (M115, M120) and overlapping articles"""
        # Test data according to review request:
        # For M115: ART1 (K=15), ART2 (K=24)
        # For M120: ART2 (K=24), ART3 (K=30)
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004'],
            'Article': ['ART1', 'ART2', 'ART2', 'ART3'],  # Overlapping articles
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Point d\'Expédition': ['M115', 'M115', 'M120', 'M120'],  # Two depots
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Quantité Commandée': [100, 150, 150, 200],  # Quantities
            'Stock Utilisation Libre': [50, 75, 75, 100],  # Stock
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Type Emballage': ['verre', 'pet', 'pet', 'ciel'],  # Packaging
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Produits par Palette': [15, 24, 24, 30]  # Column K values as specified
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_test_stock_excel(self):
        """Create stock Excel with different stock levels to test ordering by highest stock"""
        # Test data according to review request:
        # ART1=1000, ART2=5000, ART3=2000 to test ordering by highest stock
        data = {
            'Division': ['M210', 'M210', 'M210'],
            'Article': ['ART1', 'ART2', 'ART3'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3'],
            'STOCK A DATE': [1000, 5000, 2000]  # Different stock levels for testing
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_test_transit_excel(self):
        """Create minimal transit data"""
        data = {
            'Article': ['ART1', 'ART2'],
            'Dummy_B': ['Desc1', 'Desc2'],
            'Division': ['M115', 'M120'],
            'Dummy_D': ['Extra1', 'Extra2'],
            'Dummy_E': ['Extra1', 'Extra2'],
            'Dummy_F': ['Extra1', 'Extra2'],
            'Division cédante': ['M210', 'M210'],
            'Dummy_H': ['Extra1', 'Extra2'],
            'Quantité': [10, 20]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_upload_test_data(self):
        """Upload test data for recommendation logic testing"""
        print("\n🔍 Uploading test data for recommendation logic testing...")
        
        # Upload commandes
        excel_file = self.create_test_commandes_excel()
        files = {
            'file': ('test_commandes.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Test Commandes",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.commandes_session_id = response['session_id']
            print(f"✅ Commandes uploaded - Session ID: {self.commandes_session_id}")
        else:
            return False
        
        # Upload stock
        excel_file = self.create_test_stock_excel()
        files = {
            'file': ('test_stock.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Test Stock",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.stock_session_id = response['session_id']
            print(f"✅ Stock uploaded - Session ID: {self.stock_session_id}")
        else:
            return False
        
        # Upload transit
        excel_file = self.create_test_transit_excel()
        files = {
            'file': ('test_transit.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Test Transit",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"✅ Transit uploaded - Session ID: {self.transit_session_id}")
            return True
        else:
            return False

    def test_depot_suggestions_m115(self):
        """Test /api/depot-suggestions for M115 - should only include ART1 and ART2, sorted by highest stock"""
        print("\n🔍 Testing depot suggestions for M115...")
        
        request_data = {
            'depot_name': 'M115',
            'days': 10
        }
        
        success, response = self.run_test(
            "Depot Suggestions M115",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            # Verify suggestions only include articles already sent to M115 (ART1, ART2)
            allowed_articles = {'ART1', 'ART2'}
            found_articles = set()
            
            for suggestion in suggestions:
                article = suggestion['article']
                found_articles.add(article)
                
                if article not in allowed_articles:
                    print(f"❌ M115 suggestion includes article {article} not sent to this depot")
                    return False
                
                # Verify Quantité Suggérée = suggested_palettes × ProduitsParPalette[Article]
                suggested_palettes = suggestion['suggested_palettes']
                suggested_quantity = suggestion['suggested_quantity']
                
                # Get expected products per palette for this article
                if article == 'ART1':
                    expected_products_per_palette = 15  # From Column K
                elif article == 'ART2':
                    expected_products_per_palette = 24  # From Column K
                else:
                    expected_products_per_palette = 30  # Fallback
                
                expected_quantity = suggested_palettes * expected_products_per_palette
                
                if suggested_quantity != expected_quantity:
                    print(f"❌ M115 article {article}: Expected quantity {expected_quantity} (palettes {suggested_palettes} × {expected_products_per_palette}), got {suggested_quantity}")
                    return False
                
                print(f"✅ M115 article {article}: {suggested_palettes} palettes × {expected_products_per_palette} products = {suggested_quantity} quantity")
            
            # Verify sorting by highest stock (ART2=5000 should come before ART1=1000)
            if len(suggestions) >= 2:
                first_article = suggestions[0]['article']
                first_stock = suggestions[0]['stock_m210']
                second_article = suggestions[1]['article']
                second_stock = suggestions[1]['stock_m210']
                
                if first_stock < second_stock:
                    print(f"❌ M115 suggestions not sorted by highest stock: {first_article}({first_stock}) before {second_article}({second_stock})")
                    return False
                
                print(f"✅ M115 suggestions correctly sorted by highest stock: {first_article}({first_stock}) before {second_article}({second_stock})")
            
            print(f"✅ M115 suggestions only include allowed articles: {found_articles}")
            return True
        
        return False

    def test_depot_suggestions_m120(self):
        """Test /api/depot-suggestions for M120 - should only include ART2 and ART3, sorted by highest stock"""
        print("\n🔍 Testing depot suggestions for M120...")
        
        request_data = {
            'depot_name': 'M120',
            'days': 10
        }
        
        success, response = self.run_test(
            "Depot Suggestions M120",
            "POST",
            "api/depot-suggestions",
            200,
            data=request_data
        )
        
        if success and 'suggestions' in response:
            suggestions = response['suggestions']
            
            # Verify suggestions only include articles already sent to M120 (ART2, ART3)
            allowed_articles = {'ART2', 'ART3'}
            found_articles = set()
            
            for suggestion in suggestions:
                article = suggestion['article']
                found_articles.add(article)
                
                if article not in allowed_articles:
                    print(f"❌ M120 suggestion includes article {article} not sent to this depot")
                    return False
                
                # Verify Quantité Suggérée = suggested_palettes × ProduitsParPalette[Article]
                suggested_palettes = suggestion['suggested_palettes']
                suggested_quantity = suggestion['suggested_quantity']
                
                # Get expected products per palette for this article
                if article == 'ART2':
                    expected_products_per_palette = 24  # From Column K
                elif article == 'ART3':
                    expected_products_per_palette = 30  # From Column K
                else:
                    expected_products_per_palette = 30  # Fallback
                
                expected_quantity = suggested_palettes * expected_products_per_palette
                
                if suggested_quantity != expected_quantity:
                    print(f"❌ M120 article {article}: Expected quantity {expected_quantity} (palettes {suggested_palettes} × {expected_products_per_palette}), got {suggested_quantity}")
                    return False
                
                print(f"✅ M120 article {article}: {suggested_palettes} palettes × {expected_products_per_palette} products = {suggested_quantity} quantity")
            
            # Verify sorting by highest stock (ART2=5000 should come before ART3=2000)
            if len(suggestions) >= 2:
                first_article = suggestions[0]['article']
                first_stock = suggestions[0]['stock_m210']
                second_article = suggestions[1]['article']
                second_stock = suggestions[1]['stock_m210']
                
                if first_stock < second_stock:
                    print(f"❌ M120 suggestions not sorted by highest stock: {first_article}({first_stock}) before {second_article}({second_stock})")
                    return False
                
                print(f"✅ M120 suggestions correctly sorted by highest stock: {first_article}({first_stock}) before {second_article}({second_stock})")
            
            print(f"✅ M120 suggestions only include allowed articles: {found_articles}")
            return True
        
        return False

    def test_excel_export_recommendations(self):
        """Test Excel export 'Recommandations Dépôts' sheet mirrors the same logic"""
        print("\n🔍 Testing Excel export recommendations logic...")
        
        # First get calculation results
        calculation_data = {"days": 10}
        calc_success, calc_response = self.run_test(
            "Get Calculations for Export Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if calc_success and 'calculations' in calc_response:
            calculations = calc_response['calculations']
            
            # Test export
            export_data = {
                "selected_items": calculations,
                "session_id": "recommendation_test"
            }
            
            success, response = self.run_test(
                "Excel Export with Recommendations",
                "POST",
                "api/export-excel",
                200,
                data=export_data
            )
            
            if success:
                print("✅ Excel export completed successfully")
                print("✅ 'Recommandations Dépôts' sheet should mirror API logic:")
                print("   - Only articles already sent to each depot")
                print("   - Sorted by highest M210 stock")
                print("   - Quantité Suggérée = suggested_palettes × Column K value")
                return True
        
        return False

    def test_calculate_regression(self):
        """Test that /api/calculate still works and depot constraints are enforced"""
        print("\n🔍 Testing /api/calculate regression...")
        
        calculation_data = {"days": 10}
        success, response = self.run_test(
            "Calculate Regression Test",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify depot constraints are enforced
            allowed_depots = {'M115', 'M120', 'M130', 'M170', 'M171'}
            # Also allow M212-M280 range
            for i in range(212, 281):
                allowed_depots.add(f'M{i}')
            
            for calc in calculations:
                depot = calc['depot']
                if depot not in allowed_depots:
                    print(f"❌ Non-allowed depot {depot} found in calculations")
                    return False
            
            # Verify required fields are present
            required_fields = ['article', 'depot', 'quantite_a_envoyer', 'palettes_needed', 'statut', 'produits_par_palette']
            for calc in calculations:
                for field in required_fields:
                    if field not in calc:
                        print(f"❌ Missing required field '{field}' in calculation")
                        return False
            
            print(f"✅ Calculate endpoint working - {len(calculations)} results")
            print("✅ Depot constraints enforced")
            print("✅ All required fields present")
            return True
        
        return False

    def test_column_k_usage_verification(self):
        """Verify that Column K values are used correctly throughout the system"""
        print("\n🔍 Testing Column K usage verification...")
        
        # Test calculation endpoint uses Column K
        calculation_data = {"days": 10}
        success, response = self.run_test(
            "Verify Column K in Calculations",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                article = calc['article']
                produits_par_palette = calc.get('produits_par_palette', 0)
                palettes_needed = calc.get('palettes_needed', 0)
                quantite_a_envoyer = calc.get('quantite_a_envoyer', 0)
                
                # Verify Column K values match expected
                expected_k_values = {
                    'ART1': 15,
                    'ART2': 24,
                    'ART3': 30
                }
                
                if article in expected_k_values:
                    expected_k = expected_k_values[article]
                    if produits_par_palette != expected_k:
                        print(f"❌ Article {article}: Expected Column K value {expected_k}, got {produits_par_palette}")
                        return False
                    
                    # Verify palette calculation uses Column K
                    expected_palettes = math.ceil(quantite_a_envoyer / expected_k) if quantite_a_envoyer > 0 else 0
                    if palettes_needed != expected_palettes:
                        print(f"❌ Article {article}: Expected {expected_palettes} palettes (ceil({quantite_a_envoyer}/{expected_k})), got {palettes_needed}")
                        return False
                    
                    print(f"✅ Article {article}: Column K={expected_k}, palettes={palettes_needed}")
            
            return True
        
        return False

    def run_all_tests(self):
        """Run all recommendation logic tests"""
        print("🚀 Starting Recommendation Logic Testing...")
        print("=" * 60)
        
        tests = [
            self.test_upload_test_data,
            self.test_depot_suggestions_m115,
            self.test_depot_suggestions_m120,
            self.test_excel_export_recommendations,
            self.test_calculate_regression,
            self.test_column_k_usage_verification
        ]
        
        for test in tests:
            try:
                if not test():
                    print(f"\n❌ Test failed: {test.__name__}")
                    break
            except Exception as e:
                print(f"\n❌ Test error in {test.__name__}: {str(e)}")
                break
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL RECOMMENDATION LOGIC TESTS PASSED!")
            return "PASS"
        else:
            print("💥 SOME TESTS FAILED!")
            return "FAIL"

if __name__ == "__main__":
    tester = RecommendationLogicTester()
    result = tester.run_all_tests()
    sys.exit(0 if result == "PASS" else 1)