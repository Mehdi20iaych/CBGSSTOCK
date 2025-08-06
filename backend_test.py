import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class SimplifiedStockManagementTester:
    def __init__(self, base_url="https://b0faa87f-aabd-4cf0-b42c-460dbf858756.preview.emergentagent.com"):
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

    def create_sample_commandes_excel(self):
        """Create sample commandes Excel file with columns B, D, F, G"""
        # Create sample data with proper column structure - using actual column names
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006'],  # Dummy column A
            'Article': ['ART001', 'ART002', 'ART003', 'ART001', 'ART002', 'ART004'],  # Article (Column B)
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],  # Dummy column C
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M212', 'M211', 'M213'],  # Point d'Expédition (Column D) - M210 excluded
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],  # Dummy column E
            'Quantité Commandée': [100, 150, 80, 120, 90, 200],  # Quantité Commandée (Column F)
            'Stock Utilisation Libre': [50, 75, 40, 60, 45, 100]  # Stock Utilisation Libre (Column G)
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_stock_excel(self):
        """Create sample stock M210 Excel file with columns A, B, D"""
        # Create sample stock data for M210 only
        data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210'],  # Division (Column A)
            'Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005'],  # Article (Column B)
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5'],  # Dummy column C
            'STOCK A DATE': [500, 300, 200, 400, 250]  # STOCK A DATE (Column D)
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_transit_excel(self):
        """Create sample transit Excel file with columns A, C, G, I"""
        # Create sample transit data from M210 to other depots
        data = {
            'A': ['ART001', 'ART002', 'ART003', 'ART001', 'ART004'],  # Article (Column A)
            'B': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5'],  # Dummy column B
            'C': ['M211', 'M212', 'M213', 'M212', 'M211'],  # Division destinataire (Column C)
            'D': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],  # Dummy column D
            'E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],  # Dummy column E
            'F': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],  # Dummy column F
            'G': ['M210', 'M210', 'M210', 'M210', 'M210'],  # Division cédante (Column G) - Only M210
            'H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],  # Dummy column H
            'I': [30, 20, 25, 15, 40]  # Quantité (Column I)
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_invalid_commandes_excel(self):
        """Create invalid commandes Excel with M210 as destination (should be filtered out)"""
        data = {
            'A': ['CMD001', 'CMD002'],
            'B': ['ART001', 'ART002'],  # Article
            'C': ['Desc1', 'Desc2'],
            'D': ['M210', 'M211'],  # Point d'Expédition - M210 should be excluded
            'E': ['Extra1', 'Extra2'],
            'F': [100, 150],  # Quantité Commandée
            'G': [50, 75]  # Stock Utilisation Libre
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_invalid_stock_excel(self):
        """Create invalid stock Excel with non-M210 divisions (should be filtered out)"""
        data = {
            'A': ['M211', 'M212', 'M210'],  # Division - only M210 should be kept
            'B': ['ART001', 'ART002', 'ART003'],  # Article
            'C': ['Desc1', 'Desc2', 'Desc3'],
            'D': [500, 300, 200]  # STOCK A DATE
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_invalid_transit_excel(self):
        """Create invalid transit Excel with non-M210 source (should be filtered out)"""
        data = {
            'A': ['ART001', 'ART002'],  # Article
            'B': ['Desc1', 'Desc2'],
            'C': ['M211', 'M212'],  # Division destinataire
            'D': ['Extra1', 'Extra2'],
            'E': ['Extra1', 'Extra2'],
            'F': ['Extra1', 'Extra2'],
            'G': ['M211', 'M210'],  # Division cédante - only M210 should be kept
            'H': ['Extra1', 'Extra2'],
            'I': [30, 20]  # Quantité
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_upload_commandes_excel(self):
        """Test commandes Excel upload with column validation"""
        excel_file = self.create_sample_commandes_excel()
        
        files = {
            'file': ('commandes.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
            print(f"Commandes Session ID: {self.commandes_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'summary', 'filters']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify M210 exclusion
            depots = response['filters']['depots']
            if 'M210' in depots:
                print(f"❌ M210 should be excluded from destinations but found in: {depots}")
                return False
            
            print(f"✅ M210 correctly excluded from destinations. Found depots: {depots}")
            print(f"✅ Uploaded {response['summary']['total_records']} commandes records")
            return True
        return False

    def test_upload_stock_excel(self):
        """Test stock M210 Excel upload with M210 filtering"""
        excel_file = self.create_sample_stock_excel()
        
        files = {
            'file': ('stock_m210.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Stock M210 Excel",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.stock_session_id = response['session_id']
            print(f"Stock Session ID: {self.stock_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            print(f"✅ Uploaded {response['summary']['total_records']} stock M210 records")
            print(f"✅ Total stock M210: {response['summary']['total_stock_m210']}")
            return True
        return False

    def test_upload_transit_excel(self):
        """Test transit Excel upload with M210 source filtering"""
        excel_file = self.create_sample_transit_excel()
        
        files = {
            'file': ('transit.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
            print(f"Transit Session ID: {self.transit_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            print(f"✅ Uploaded {response['summary']['total_records']} transit records")
            print(f"✅ Total transit quantity: {response['summary']['total_transit_quantity']}")
            return True
        return False

    def test_m210_filtering_validation(self):
        """Test that M210 filtering works correctly for all file types"""
        print("\n🔍 Testing M210 filtering validation...")
        
        # Test commandes with M210 destination (should be excluded)
        invalid_commandes = self.create_invalid_commandes_excel()
        files = {
            'file': ('invalid_commandes.xlsx', invalid_commandes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Commandes with M210 Destination (Should Filter Out)",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # Should have only 1 record (M211), M210 should be filtered out
            if response['summary']['total_records'] == 1:
                print("✅ M210 correctly filtered out from commandes destinations")
            else:
                print(f"❌ Expected 1 record after M210 filtering, got {response['summary']['total_records']}")
                return False
        else:
            return False
        
        # Test stock with mixed divisions (should keep only M210)
        invalid_stock = self.create_invalid_stock_excel()
        files = {
            'file': ('mixed_stock.xlsx', invalid_stock, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Stock with Mixed Divisions (Should Keep Only M210)",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if success:
            # Should have only 1 record (M210), others should be filtered out
            if response['summary']['total_records'] == 1:
                print("✅ Only M210 records kept in stock data")
            else:
                print(f"❌ Expected 1 M210 record, got {response['summary']['total_records']}")
                return False
        else:
            return False
        
        # Test transit with mixed sources (should keep only from M210)
        invalid_transit = self.create_invalid_transit_excel()
        files = {
            'file': ('mixed_transit.xlsx', invalid_transit, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Transit with Mixed Sources (Should Keep Only From M210)",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success:
            # Should have only 1 record (from M210), others should be filtered out
            if response['summary']['total_records'] == 1:
                print("✅ Only M210 source records kept in transit data")
            else:
                print(f"❌ Expected 1 M210 source record, got {response['summary']['total_records']}")
                return False
        else:
            return False
        
        return True

    def test_simplified_calculation_formula(self):
        """Test the simplified calculation formula"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for calculation test")
            return False
        
        calculation_data = {
            "days": 10  # 10 days coverage
        }
        
        success, response = self.run_test(
            "Simplified Calculation Formula",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify formula: Quantité à Envoyer = max(0, (Quantité Commandée × Jours à Couvrir) - Stock Utilisation Libre - Quantité en Transit)
            for calc in calculations:
                article = calc['article']
                cqm = calc['cqm']
                stock_actuel = calc['stock_actuel']
                stock_transit = calc['stock_transit']
                quantite_requise = calc['quantite_requise']
                quantite_a_envoyer = calc['quantite_a_envoyer']
                
                # Verify quantite_requise = cqm * days
                expected_requise = cqm * 10
                if abs(quantite_requise - expected_requise) > 0.01:
                    print(f"❌ Article {article}: Expected quantite_requise {expected_requise}, got {quantite_requise}")
                    return False
                
                # Verify formula: max(0, quantite_requise - stock_actuel - stock_transit)
                expected_a_envoyer = max(0, quantite_requise - stock_actuel - stock_transit)
                if abs(quantite_a_envoyer - expected_a_envoyer) > 0.01:
                    print(f"❌ Article {article}: Expected quantite_a_envoyer {expected_a_envoyer}, got {quantite_a_envoyer}")
                    return False
                
                print(f"✅ Article {article}: Formula correct - {cqm}*10 - {stock_actuel} - {stock_transit} = {quantite_a_envoyer}")
            
            # Verify negative values are limited to 0
            negative_values = [calc for calc in calculations if calc['quantite_a_envoyer'] < 0]
            if negative_values:
                print(f"❌ Found negative quantite_a_envoyer values: {[calc['quantite_a_envoyer'] for calc in negative_values]}")
                return False
            
            print("✅ All calculations follow simplified formula with max(0, ...) constraint")
            return True
        
        return False

    def test_calculation_with_all_data_types(self):
        """Test calculation with commandes, stock, and transit data"""
        if not all([self.commandes_session_id, self.stock_session_id, self.transit_session_id]):
            print("❌ Missing session IDs for comprehensive calculation test")
            return False
        
        calculation_data = {
            "days": 15
        }
        
        success, response = self.run_test(
            "Calculation with All Data Types",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['calculations', 'summary', 'has_stock_data', 'has_transit_data']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify data availability flags
            if not response['has_stock_data']:
                print("❌ has_stock_data should be True when stock data is available")
                return False
            
            if not response['has_transit_data']:
                print("❌ has_transit_data should be True when transit data is available")
                return False
            
            # Verify calculations include all data types
            calculations = response['calculations']
            for calc in calculations:
                required_calc_fields = ['article', 'depot', 'cqm', 'stock_actuel', 'stock_transit', 
                                      'quantite_requise', 'quantite_a_envoyer', 'stock_dispo_m210', 'statut']
                for field in required_calc_fields:
                    if field not in calc:
                        print(f"❌ Missing calculation field: {field}")
                        return False
            
            print(f"✅ Comprehensive calculation with {len(calculations)} results")
            print(f"✅ Summary: {response['summary']['items_ok']} OK, {response['summary']['items_a_livrer']} À livrer, {response['summary']['items_non_couverts']} Non couvert")
            return True
        
        return False

    def test_calculation_without_optional_data(self):
        """Test calculation with only commandes data (stock and transit optional)"""
        # Create new commandes session for isolated test
        excel_file = self.create_sample_commandes_excel()
        files = {
            'file': ('commandes_only.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        # Clear existing data to test without stock/transit
        original_stock = self.stock_session_id
        original_transit = self.transit_session_id
        self.stock_session_id = None
        self.transit_session_id = None
        
        success, upload_response = self.run_test(
            "Upload Commandes for Isolated Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            calculation_data = {
                "days": 20
            }
            
            success, response = self.run_test(
                "Calculation Without Stock/Transit Data",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success:
                # Verify data availability flags
                if response.get('has_stock_data', True):
                    print("❌ has_stock_data should be False when no stock data available")
                    return False
                
                if response.get('has_transit_data', True):
                    print("❌ has_transit_data should be False when no transit data available")
                    return False
                
                # Verify calculations work with default values
                calculations = response['calculations']
                for calc in calculations:
                    if calc['stock_dispo_m210'] != 0:
                        print(f"❌ Expected stock_dispo_m210=0 without stock data, got {calc['stock_dispo_m210']}")
                        return False
                    
                    if calc['stock_transit'] != 0:
                        print(f"❌ Expected stock_transit=0 without transit data, got {calc['stock_transit']}")
                        return False
                
                print("✅ Calculation works correctly without optional stock/transit data")
                
                # Restore original sessions
                self.stock_session_id = original_stock
                self.transit_session_id = original_transit
                return True
        
        # Restore original sessions
        self.stock_session_id = original_stock
        self.transit_session_id = original_transit
        return False

    def test_excel_export(self):
        """Test Excel export functionality"""
        if not self.commandes_session_id:
            print("❌ No commandes session available for export test")
            return False
        
        # First get calculation results
        calculation_data = {
            "days": 10
        }
        
        calc_success, calc_response = self.run_test(
            "Get Calculations for Export",
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
                "Excel Export",
                "POST",
                "api/export-excel",
                200,
                data=export_data
            )
            
            if success:
                print("✅ Excel export completed successfully")
                return True
        
        return False

    def test_sessions_endpoint(self):
        """Test sessions endpoint"""
        success, response = self.run_test(
            "Get Active Sessions",
            "GET",
            "api/sessions",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['commandes_sessions', 'stock_sessions', 'transit_sessions']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            print(f"✅ Sessions: {len(response['commandes_sessions'])} commandes, {len(response['stock_sessions'])} stock, {len(response['transit_sessions'])} transit")
            return True
        
        return False

    def test_column_validation_errors(self):
        """Test proper error handling for missing columns"""
        print("\n🔍 Testing column validation errors...")
        
        # Test commandes with missing columns
        invalid_data = {
            'A': ['CMD001'],
            'B': ['ART001']  # Missing columns D, F, G
        }
        df = pd.DataFrame(invalid_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_commandes.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Commandes Missing Columns Error",
            "POST",
            "api/upload-commandes-excel",
            400,
            files=files
        )
        
        if not success:
            return False
        
        # Test stock with missing columns
        invalid_stock_data = {
            'A': ['M210'],
            'B': ['ART001']  # Missing column D
        }
        df = pd.DataFrame(invalid_stock_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_stock.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Stock Missing Columns Error",
            "POST",
            "api/upload-stock-excel",
            400,
            files=files
        )
        
        if not success:
            return False
        
        # Test transit with missing columns
        invalid_transit_data = {
            'A': ['ART001'],
            'C': ['M211']  # Missing columns G, I
        }
        df = pd.DataFrame(invalid_transit_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_transit.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Transit Missing Columns Error",
            "POST",
            "api/upload-transit-excel",
            400,
            files=files
        )
        
        return success

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n🔍 Testing edge cases...")
        
        # Test calculation with 0 days
        if self.commandes_session_id:
            calculation_data = {
                "days": 0
            }
            
            success, response = self.run_test(
                "Calculation with 0 Days",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                # All quantite_requise should be 0
                calculations = response['calculations']
                for calc in calculations:
                    if calc['quantite_requise'] != 0:
                        print(f"❌ Expected quantite_requise=0 for 0 days, got {calc['quantite_requise']}")
                        return False
                print("✅ 0 days calculation works correctly")
            else:
                return False
        
        # Test with very high stock values (should result in 0 quantite_a_envoyer)
        high_stock_data = {
            'A': ['CMD001'],
            'B': ['ART001'],  # Article
            'C': ['Desc1'],
            'D': ['M211'],  # Point d'Expédition
            'E': ['Extra1'],
            'F': [10],  # Low Quantité Commandée
            'G': [10000]  # Very high Stock Utilisation Libre
        }
        
        df = pd.DataFrame(high_stock_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('high_stock.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload High Stock Scenario",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            calculation_data = {
                "days": 30
            }
            
            success, response = self.run_test(
                "High Stock Calculation (Should Result in 0)",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                for calc in calculations:
                    if calc['quantite_a_envoyer'] != 0:
                        print(f"❌ Expected quantite_a_envoyer=0 for high stock scenario, got {calc['quantite_a_envoyer']}")
                        return False
                print("✅ High stock scenario correctly results in 0 quantite_a_envoyer")
            else:
                return False
        else:
            return False
        
        return True

    def run_all_tests(self):
        """Run all tests for the simplified stock management system"""
        print("🚀 Starting Simplified Stock Management System Tests")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Upload Commandes Excel", self.test_upload_commandes_excel),
            ("Upload Stock Excel", self.test_upload_stock_excel),
            ("Upload Transit Excel", self.test_upload_transit_excel),
            ("M210 Filtering Validation", self.test_m210_filtering_validation),
            ("Simplified Calculation Formula", self.test_simplified_calculation_formula),
            ("Calculation with All Data Types", self.test_calculation_with_all_data_types),
            ("Calculation without Optional Data", self.test_calculation_without_optional_data),
            ("Excel Export", self.test_excel_export),
            ("Sessions Endpoint", self.test_sessions_endpoint),
            ("Column Validation Errors", self.test_column_validation_errors),
            ("Edge Cases", self.test_edge_cases)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                result = test_func()
                if result:
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {str(e)}")
                self.tests_run += 1  # Count as attempted
        
        # Print final summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Simplified system is working correctly.")
        else:
            print("⚠️ Some tests failed. Please review the issues above.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = SimplifiedStockManagementTester()
    tester.run_all_tests()