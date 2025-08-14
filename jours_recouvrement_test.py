import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class JoursRecouvrementTester:
    def __init__(self, base_url="https://upbeat-payne.preview.emergentagent.com"):
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

    def create_jours_recouvrement_test_commandes(self):
        """Create sample commandes Excel file for jours de recouvrement testing"""
        # Create test data with different daily consumption rates
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006'],
            'Article': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005', 'TEST006'],  # Test articles
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M211', 'M212', 'M213'],  # Different depots
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Quantité Commandée': [50, 100, 150, 200, 300, 0],  # Different consumption rates including zero
            'Stock Utilisation Libre': [500, 1000, 75, 100, 50, 200],  # Different stock levels
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre', 'pet', 'ciel'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6'],
            'Produits par Palette': [30, 30, 30, 30, 30, 30]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_jours_recouvrement_test_stock(self):
        """Create sample stock M210 Excel file for jours de recouvrement testing"""
        data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005', 'TEST006'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'STOCK A DATE': [1000, 500, 2000, 150, 75, 10000]  # Different stock levels
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_jours_recouvrement_test_transit(self):
        """Create sample transit Excel file for jours de recouvrement testing"""
        data = {
            'Article': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5'],
            'Division': ['M211', 'M212', 'M213', 'M211', 'M212'],  # Destination depots
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Division cédante': ['M210', 'M210', 'M210', 'M210', 'M210'],  # From M210
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5'],
            'Quantité': [500, 300, 100, 50, 25]  # Different transit quantities
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def upload_test_data(self):
        """Upload all test data files"""
        print("\n📤 Uploading test data for Jours de Recouvrement testing...")
        
        # Upload commandes
        commandes_file = self.create_jours_recouvrement_test_commandes()
        files = {
            'file': ('jours_test_commandes.xlsx', commandes_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Jours Test Commandes",
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
        stock_file = self.create_jours_recouvrement_test_stock()
        files = {
            'file': ('jours_test_stock.xlsx', stock_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Jours Test Stock",
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
        transit_file = self.create_jours_recouvrement_test_transit()
        files = {
            'file': ('jours_test_transit.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Jours Test Transit",
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

    def test_jours_recouvrement_field_presence(self):
        """Test that jours_recouvrement field is present in all calculation results"""
        if not self.commandes_session_id:
            print("❌ No commandes session available")
            return False
        
        calculation_data = {"days": 10}
        
        success, response = self.run_test(
            "Jours Recouvrement Field Presence",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                if 'jours_recouvrement' not in calc:
                    print(f"❌ Missing jours_recouvrement field in calculation for article {calc.get('article', 'unknown')}")
                    return False
                
                # Verify it's a numeric value
                jours_value = calc['jours_recouvrement']
                if not isinstance(jours_value, (int, float)):
                    print(f"❌ jours_recouvrement should be numeric, got {type(jours_value)} for article {calc['article']}")
                    return False
                
                # Verify it's non-negative
                if jours_value < 0:
                    print(f"❌ jours_recouvrement should be non-negative, got {jours_value} for article {calc['article']}")
                    return False
            
            print(f"✅ All {len(calculations)} calculations include jours_recouvrement field with valid values")
            return True
        
        return False

    def test_jours_recouvrement_formula_accuracy(self):
        """Test the mathematical accuracy of the jours_recouvrement formula"""
        if not self.commandes_session_id:
            print("❌ No commandes session available")
            return False
        
        calculation_data = {"days": 10}
        
        success, response = self.run_test(
            "Jours Recouvrement Formula Accuracy",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                article = calc['article']
                stock_actuel = calc['stock_actuel']
                stock_transit = calc['stock_transit']
                cqm = calc['cqm']  # This is the daily consumption (Quantité Commandée)
                jours_recouvrement = calc['jours_recouvrement']
                
                # Formula: jours_recouvrement = (Stock Actuel + Quantité en Transit) / Quantité Commandée
                if cqm > 0:
                    expected_jours = round((stock_actuel + stock_transit) / cqm, 1)
                else:
                    expected_jours = 0  # Zero consumption should result in 0 jours
                
                if abs(jours_recouvrement - expected_jours) > 0.1:  # Allow small rounding differences
                    print(f"❌ Article {article}: Expected jours_recouvrement {expected_jours}, got {jours_recouvrement}")
                    print(f"   Formula: ({stock_actuel} + {stock_transit}) / {cqm} = {expected_jours}")
                    return False
                
                print(f"✅ Article {article}: ({stock_actuel} + {stock_transit}) / {cqm} = {jours_recouvrement} jours")
            
            print(f"✅ All {len(calculations)} calculations have mathematically correct jours_recouvrement values")
            return True
        
        return False

    def test_specific_calculation_scenarios(self):
        """Test specific calculation scenarios mentioned in the review request"""
        print("\n🧮 Testing specific calculation scenarios...")
        
        # Test scenario: Stock Actuel = 1000, Quantité en Transit = 500, Quantité Commandée = 50
        # Expected: jours_recouvrement = (1000+500)/50 = 30.0
        
        # Create specific test data
        specific_data = {
            'Dummy_A': ['CMD001'],
            'Article': ['SPECIFIC001'],
            'Dummy_C': ['Desc1'],
            'Point d\'Expédition': ['M212'],
            'Dummy_E': ['Extra1'],
            'Quantité Commandée': [50],  # Daily consumption
            'Stock Utilisation Libre': [1000],  # Stock Actuel
            'Dummy_H': ['Extra1'],
            'Type Emballage': ['verre'],
            'Dummy_J': ['Extra1'],
            'Produits par Palette': [30]
        }
        
        df = pd.DataFrame(specific_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        # Upload specific test commandes
        files = {
            'file': ('specific_test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Specific Test Commandes",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Upload specific stock data
        stock_data = {
            'Division': ['M210'],
            'Article': ['SPECIFIC001'],
            'Dummy_C': ['Desc1'],
            'STOCK A DATE': [2000]  # Enough stock for testing
        }
        
        df = pd.DataFrame(stock_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('specific_stock.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Specific Test Stock",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Upload specific transit data (500 units in transit)
        transit_data = {
            'Article': ['SPECIFIC001'],
            'Dummy_B': ['Desc1'],
            'Division': ['M212'],
            'Dummy_D': ['Extra1'],
            'Dummy_E': ['Extra1'],
            'Dummy_F': ['Extra1'],
            'Division cédante': ['M210'],
            'Dummy_H': ['Extra1'],
            'Quantité': [500]  # 500 units in transit
        }
        
        df = pd.DataFrame(transit_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('specific_transit.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Specific Test Transit",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Now test the calculation
        calculation_data = {"days": 10}
        
        success, response = self.run_test(
            "Specific Scenario Calculation",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Find our specific test article
            specific_calc = None
            for calc in calculations:
                if calc['article'] == 'SPECIFIC001':
                    specific_calc = calc
                    break
            
            if not specific_calc:
                print("❌ Could not find SPECIFIC001 article in calculations")
                return False
            
            # Verify the calculation
            stock_actuel = specific_calc['stock_actuel']  # Should be 1000
            stock_transit = specific_calc['stock_transit']  # Should be 500
            cqm = specific_calc['cqm']  # Should be 50
            jours_recouvrement = specific_calc['jours_recouvrement']
            
            print(f"📊 Specific scenario verification:")
            print(f"   Stock Actuel: {stock_actuel}")
            print(f"   Quantité en Transit: {stock_transit}")
            print(f"   Quantité Commandée (daily): {cqm}")
            print(f"   Jours de Recouvrement: {jours_recouvrement}")
            
            # Expected: (1000 + 500) / 50 = 30.0
            expected_jours = (stock_actuel + stock_transit) / cqm if cqm > 0 else 0
            
            if abs(jours_recouvrement - expected_jours) > 0.1:
                print(f"❌ Expected jours_recouvrement {expected_jours}, got {jours_recouvrement}")
                return False
            
            print(f"✅ Specific scenario correct: ({stock_actuel} + {stock_transit}) / {cqm} = {jours_recouvrement}")
            return True
        
        return False

    def test_edge_cases(self):
        """Test edge cases like zero consumption, zero stock, etc."""
        print("\n🔍 Testing edge cases...")
        
        # Create edge case test data
        edge_data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004'],
            'Article': ['EDGE001', 'EDGE002', 'EDGE003', 'EDGE004'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M211'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Quantité Commandée': [0, 1, 1000, 0.5],  # Zero, very low, very high, decimal
            'Stock Utilisation Libre': [0, 0, 5000, 100],  # Zero stock, normal stock
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Produits par Palette': [30, 30, 30, 30]
        }
        
        df = pd.DataFrame(edge_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('edge_cases.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Edge Cases Commandes",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Upload corresponding stock data
        stock_data = {
            'Division': ['M210', 'M210', 'M210', 'M210'],
            'Article': ['EDGE001', 'EDGE002', 'EDGE003', 'EDGE004'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'STOCK A DATE': [1000, 50, 10000, 200]
        }
        
        df = pd.DataFrame(stock_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('edge_stock.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Edge Cases Stock",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Upload transit data
        transit_data = {
            'Article': ['EDGE001', 'EDGE002', 'EDGE003'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3'],
            'Division': ['M211', 'M212', 'M213'],
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3'],
            'Division cédante': ['M210', 'M210', 'M210'],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3'],
            'Quantité': [0, 10, 2000]  # Zero, low, high transit
        }
        
        df = pd.DataFrame(transit_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('edge_transit.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Edge Cases Transit",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Test calculation
        calculation_data = {"days": 10}
        
        success, response = self.run_test(
            "Edge Cases Calculation",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            for calc in calculations:
                article = calc['article']
                cqm = calc['cqm']
                jours_recouvrement = calc['jours_recouvrement']
                
                # Test zero consumption case
                if cqm == 0:
                    if jours_recouvrement != 0:
                        print(f"❌ Article {article}: Zero consumption should result in 0 jours_recouvrement, got {jours_recouvrement}")
                        return False
                    print(f"✅ Article {article}: Zero consumption correctly handled (0 jours)")
                
                # Test very high consumption case
                elif cqm >= 1000:
                    # Should result in low jours_recouvrement
                    if jours_recouvrement > 100:  # Arbitrary threshold
                        print(f"⚠️ Article {article}: High consumption ({cqm}) resulted in high jours_recouvrement ({jours_recouvrement})")
                    print(f"✅ Article {article}: High consumption case handled ({jours_recouvrement} jours)")
                
                # Test decimal consumption case
                elif cqm < 1:
                    # Should result in high jours_recouvrement
                    print(f"✅ Article {article}: Decimal consumption case handled ({jours_recouvrement} jours)")
                
                # Verify non-negative values
                if jours_recouvrement < 0:
                    print(f"❌ Article {article}: Negative jours_recouvrement not allowed: {jours_recouvrement}")
                    return False
            
            print(f"✅ All {len(calculations)} edge cases handled correctly")
            return True
        
        return False

    def test_higher_values_than_before(self):
        """Test that jours_recouvrement values are higher than before (since we removed division by days)"""
        print("\n📈 Testing that jours_recouvrement values are higher than before...")
        
        if not self.commandes_session_id:
            print("❌ No commandes session available")
            return False
        
        # Test with different day scenarios
        test_scenarios = [1, 5, 10, 30]
        
        for days in test_scenarios:
            calculation_data = {"days": days}
            
            success, response = self.run_test(
                f"Jours Recouvrement Test - {days} days",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                
                for calc in calculations:
                    article = calc['article']
                    stock_actuel = calc['stock_actuel']
                    stock_transit = calc['stock_transit']
                    cqm = calc['cqm']
                    jours_recouvrement = calc['jours_recouvrement']
                    
                    # The new formula should NOT be divided by days
                    # Old formula would have been: (stock_actuel + stock_transit) / (cqm / days)
                    # New formula is: (stock_actuel + stock_transit) / cqm
                    
                    if cqm > 0:
                        # Calculate what the old formula would have given
                        old_formula_result = (stock_actuel + stock_transit) / (cqm / days)
                        new_formula_result = (stock_actuel + stock_transit) / cqm
                        
                        # The new formula should give the same result regardless of days
                        # And it should be higher than the old formula when days > 1
                        if days > 1:
                            if new_formula_result <= old_formula_result:
                                print(f"❌ Article {article} ({days} days): New formula ({new_formula_result}) should be higher than old formula ({old_formula_result})")
                                return False
                        
                        # Verify our calculation matches the API result
                        if abs(jours_recouvrement - new_formula_result) > 0.1:
                            print(f"❌ Article {article} ({days} days): Expected {new_formula_result}, got {jours_recouvrement}")
                            return False
                        
                        print(f"✅ Article {article} ({days} days): {jours_recouvrement} jours (new formula)")
                
                print(f"✅ All calculations for {days} days use new formula correctly")
            else:
                return False
        
        return True

    def test_consistency_across_different_days(self):
        """Test that jours_recouvrement values are consistent across different day calculations"""
        print("\n🔄 Testing consistency across different day calculations...")
        
        if not self.commandes_session_id:
            print("❌ No commandes session available")
            return False
        
        # Test with different day values - jours_recouvrement should be the same
        day_scenarios = [1, 7, 15, 30]
        results_by_days = {}
        
        for days in day_scenarios:
            calculation_data = {"days": days}
            
            success, response = self.run_test(
                f"Consistency Test - {days} days",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                results_by_days[days] = {}
                
                for calc in calculations:
                    article = calc['article']
                    jours_recouvrement = calc['jours_recouvrement']
                    results_by_days[days][article] = jours_recouvrement
            else:
                return False
        
        # Compare results across different day scenarios
        base_days = day_scenarios[0]
        base_results = results_by_days[base_days]
        
        for days in day_scenarios[1:]:
            current_results = results_by_days[days]
            
            for article in base_results:
                if article in current_results:
                    base_value = base_results[article]
                    current_value = current_results[article]
                    
                    if abs(base_value - current_value) > 0.1:
                        print(f"❌ Article {article}: jours_recouvrement inconsistent across days")
                        print(f"   {base_days} days: {base_value}")
                        print(f"   {days} days: {current_value}")
                        return False
        
        print("✅ jours_recouvrement values are consistent across different day calculations")
        print("✅ This confirms the new formula is NOT divided by days")
        return True

    def run_all_tests(self):
        """Run all jours de recouvrement tests"""
        print("🚀 Starting Jours de Recouvrement Comprehensive Testing")
        print("=" * 60)
        
        # Upload test data
        if not self.upload_test_data():
            print("❌ Failed to upload test data")
            return False
        
        # Run all tests
        tests = [
            self.test_jours_recouvrement_field_presence,
            self.test_jours_recouvrement_formula_accuracy,
            self.test_specific_calculation_scenarios,
            self.test_edge_cases,
            self.test_higher_values_than_before,
            self.test_consistency_across_different_days
        ]
        
        for test in tests:
            if not test():
                print(f"\n❌ Test failed: {test.__name__}")
                break
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 JOURS DE RECOUVREMENT TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL JOURS DE RECOUVREMENT TESTS PASSED!")
            return True
        else:
            print("❌ Some tests failed")
            return False

if __name__ == "__main__":
    tester = JoursRecouvrementTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)