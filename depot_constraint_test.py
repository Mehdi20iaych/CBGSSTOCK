import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class DepotConstraintTester:
    def __init__(self, base_url="https://26c0a26b-a6c0-48b9-82e9-52e8233e0e04.preview.emergentagent.com"):
        self.base_url = base_url
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

    def create_depot_test_commandes_excel(self, depots):
        """Create commandes Excel file with specified depots"""
        data = {
            'Dummy_A': [f'CMD{i:03d}' for i in range(1, len(depots) + 1)],
            'Article': [f'ART{i:03d}' for i in range(1, len(depots) + 1)],
            'Dummy_C': [f'Desc{i}' for i in range(1, len(depots) + 1)],
            'Point d\'Expédition': depots,
            'Dummy_E': [f'Extra{i}' for i in range(1, len(depots) + 1)],
            'Quantité Commandée': [100] * len(depots),
            'Stock Utilisation Libre': [50] * len(depots),
            'Dummy_H': [f'Extra{i}' for i in range(1, len(depots) + 1)],
            'Type Emballage': ['verre'] * len(depots)
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_depot_test_transit_excel(self, destination_depots):
        """Create transit Excel file with specified destination depots"""
        data = {
            'Article': [f'ART{i:03d}' for i in range(1, len(destination_depots) + 1)],
            'Dummy_B': [f'Desc{i}' for i in range(1, len(destination_depots) + 1)],
            'Division': destination_depots,  # Destination depots
            'Dummy_D': [f'Extra{i}' for i in range(1, len(destination_depots) + 1)],
            'Dummy_E': [f'Extra{i}' for i in range(1, len(destination_depots) + 1)],
            'Dummy_F': [f'Extra{i}' for i in range(1, len(destination_depots) + 1)],
            'Division cédante': ['M210'] * len(destination_depots),  # All from M210
            'Dummy_H': [f'Extra{i}' for i in range(1, len(destination_depots) + 1)],
            'Quantité': [30] * len(destination_depots)
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_allowed_depots_commandes(self):
        """Test that only allowed depots are accepted in commandes upload"""
        print("\n🔍 Testing allowed depots in commandes upload...")
        
        # Test with allowed depots
        allowed_depots = ['M115', 'M120', 'M130', 'M170', 'M171', 'M212', 'M250', 'M280']
        excel_file = self.create_depot_test_commandes_excel(allowed_depots)
        
        files = {
            'file': ('allowed_depots.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Allowed Depots",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # All depots should be kept
            if response['summary']['total_records'] != len(allowed_depots):
                print(f"❌ Expected {len(allowed_depots)} records, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(allowed_depots)
            if found_depots != expected_depots:
                print(f"❌ Expected depots {expected_depots}, got {found_depots}")
                return False
            
            print(f"✅ All {len(allowed_depots)} allowed depots accepted")
            return True
        return False

    def test_non_allowed_depots_commandes(self):
        """Test that non-allowed depots are filtered out in commandes upload"""
        print("\n🔍 Testing non-allowed depots filtering in commandes upload...")
        
        # Mix of allowed and non-allowed depots
        mixed_depots = ['M115', 'M210', 'M211', 'M281', 'M300', 'M120', 'M212']
        expected_allowed = ['M115', 'M120', 'M212']  # Only these should remain
        
        excel_file = self.create_depot_test_commandes_excel(mixed_depots)
        
        files = {
            'file': ('mixed_depots.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Mixed Depots (Should Filter)",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # Only allowed depots should remain
            if response['summary']['total_records'] != len(expected_allowed):
                print(f"❌ Expected {len(expected_allowed)} records after filtering, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(expected_allowed)
            if found_depots != expected_depots:
                print(f"❌ Expected filtered depots {expected_depots}, got {found_depots}")
                return False
            
            print(f"✅ Correctly filtered to {len(expected_allowed)} allowed depots: {expected_allowed}")
            return True
        return False

    def test_no_allowed_depots_error(self):
        """Test error when no allowed depots are found in commandes"""
        print("\n🔍 Testing error when no allowed depots found...")
        
        # Only non-allowed depots
        non_allowed_depots = ['M210', 'M211', 'M281', 'M300', 'M400']
        
        excel_file = self.create_depot_test_commandes_excel(non_allowed_depots)
        
        files = {
            'file': ('no_allowed_depots.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with No Allowed Depots (Should Error)",
            "POST",
            "api/upload-commandes-excel",
            400,  # Should return error
            files=files
        )
        
        if success:
            # Check error message mentions allowed depots
            error_detail = response.get('detail', '')
            if 'M115, M120, M130, M170, M171' not in error_detail or 'M212-M280' not in error_detail:
                print(f"❌ Error message should mention allowed depots: {error_detail}")
                return False
            
            print("✅ Correctly returned error with allowed depots list")
            return True
        return False

    def test_transit_depot_filtering(self):
        """Test that transit destinations are filtered to allowed depots"""
        print("\n🔍 Testing transit destination depot filtering...")
        
        # Mix of allowed and non-allowed destination depots
        mixed_destinations = ['M115', 'M210', 'M211', 'M281', 'M120', 'M212', 'M300']
        expected_allowed = ['M115', 'M120', 'M212']  # Only these should remain
        
        excel_file = self.create_depot_test_transit_excel(mixed_destinations)
        
        files = {
            'file': ('mixed_transit_destinations.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit with Mixed Destinations (Should Filter)",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success:
            # Only allowed destination depots should remain
            if response['summary']['total_records'] != len(expected_allowed):
                print(f"❌ Expected {len(expected_allowed)} records after filtering, got {response['summary']['total_records']}")
                return False
            
            print(f"✅ Correctly filtered transit destinations to {len(expected_allowed)} allowed depots")
            return True
        return False

    def test_depot_suggestions_allowed_depot(self):
        """Test depot suggestions endpoint with allowed depot"""
        print("\n🔍 Testing depot suggestions with allowed depot...")
        
        # First upload some commandes data
        allowed_depots = ['M115', 'M120', 'M212']
        excel_file = self.create_depot_test_commandes_excel(allowed_depots)
        
        files = {
            'file': ('suggestions_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        upload_success, upload_response = self.run_test(
            "Upload Commandes for Suggestions Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if upload_success:
            # Test with allowed depot
            suggestion_data = {
                "depot_name": "M115",
                "days": 10
            }
            
            success, response = self.run_test(
                "Depot Suggestions with Allowed Depot (M115)",
                "POST",
                "api/depot-suggestions",
                200,
                data=suggestion_data
            )
            
            if success:
                required_fields = ['depot_name', 'current_palettes', 'target_palettes', 'suggestions']
                for field in required_fields:
                    if field not in response:
                        print(f"❌ Missing required field: {field}")
                        return False
                
                if response['depot_name'] != 'M115':
                    print(f"❌ Expected depot_name 'M115', got '{response['depot_name']}'")
                    return False
                
                print("✅ Depot suggestions working for allowed depot M115")
                return True
        return False

    def test_depot_suggestions_non_allowed_depot(self):
        """Test depot suggestions endpoint with non-allowed depot"""
        print("\n🔍 Testing depot suggestions with non-allowed depot...")
        
        suggestion_data = {
            "depot_name": "M300",  # Non-allowed depot
            "days": 10
        }
        
        success, response = self.run_test(
            "Depot Suggestions with Non-Allowed Depot (M300)",
            "POST",
            "api/depot-suggestions",
            400,  # Should return error
            data=suggestion_data
        )
        
        if success:
            # Check error message mentions allowed depots
            error_detail = response.get('detail', '')
            if 'M115, M120, M130, M170, M171' not in error_detail or 'M212-M280' not in error_detail:
                print(f"❌ Error message should mention allowed depots: {error_detail}")
                return False
            
            print("✅ Correctly returned error for non-allowed depot with allowed depots list")
            return True
        return False

    def test_depot_case_sensitivity(self):
        """Test depot codes with different case"""
        print("\n🔍 Testing depot case sensitivity...")
        
        # Test with different cases
        case_variants = ['m115', 'M115', 'm120', 'M120']
        
        excel_file = self.create_depot_test_commandes_excel(case_variants)
        
        files = {
            'file': ('case_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Mixed Case Depots",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # All case variants should be accepted (validation is case-insensitive)
            if response['summary']['total_records'] != len(case_variants):
                print(f"❌ Expected {len(case_variants)} records, got {response['summary']['total_records']}")
                return False
            
            # Original format should be preserved
            found_depots = set(response['filters']['depots'])
            expected_depots = set(case_variants)
            if found_depots != expected_depots:
                print(f"❌ Expected original case preserved {expected_depots}, got {found_depots}")
                return False
            
            print("✅ Case sensitivity handled correctly - all case variations accepted, original format preserved")
            return True
        return False

    def test_depot_whitespace_handling(self):
        """Test depot codes with extra whitespace"""
        print("\n🔍 Testing depot whitespace handling...")
        
        # Test with whitespace
        whitespace_depots = [' M115 ', '  M120', 'M130  ', ' M170 ']
        expected_cleaned = ['M115', 'M120', 'M130', 'M170']
        
        excel_file = self.create_depot_test_commandes_excel(whitespace_depots)
        
        files = {
            'file': ('whitespace_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Whitespace in Depots",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # All whitespace variants should be accepted and cleaned
            if response['summary']['total_records'] != len(whitespace_depots):
                print(f"❌ Expected {len(whitespace_depots)} records, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(expected_cleaned)
            if found_depots != expected_depots:
                print(f"❌ Expected cleaned depots {expected_depots}, got {found_depots}")
                return False
            
            print("✅ Whitespace handling correct - extra spaces removed")
            return True
        return False

    def test_boundary_depot_values(self):
        """Test boundary values for depot range M212-M280"""
        print("\n🔍 Testing boundary depot values...")
        
        # Test boundary values
        boundary_depots = ['M211', 'M212', 'M280', 'M281']  # M212 and M280 should be allowed
        expected_allowed = ['M212', 'M280']
        
        excel_file = self.create_depot_test_commandes_excel(boundary_depots)
        
        files = {
            'file': ('boundary_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Boundary Depot Values",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # Only M212 and M280 should be kept
            if response['summary']['total_records'] != len(expected_allowed):
                print(f"❌ Expected {len(expected_allowed)} records, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(expected_allowed)
            if found_depots != expected_depots:
                print(f"❌ Expected boundary depots {expected_depots}, got {found_depots}")
                return False
            
            print("✅ Boundary values correct - M212 and M280 allowed, M211 and M281 filtered out")
            return True
        return False

    def test_invalid_depot_formats(self):
        """Test invalid depot formats"""
        print("\n🔍 Testing invalid depot formats...")
        
        # Test invalid formats
        invalid_depots = ['M115', 'X115', 'M12A', '115', 'MABC', 'M120']  # Only M115 and M120 should be allowed
        expected_allowed = ['M115', 'M120']
        
        excel_file = self.create_depot_test_commandes_excel(invalid_depots)
        
        files = {
            'file': ('invalid_format_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with Invalid Depot Formats",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # Only valid formats should be kept
            if response['summary']['total_records'] != len(expected_allowed):
                print(f"❌ Expected {len(expected_allowed)} records, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(expected_allowed)
            if found_depots != expected_depots:
                print(f"❌ Expected valid format depots {expected_depots}, got {found_depots}")
                return False
            
            print("✅ Invalid formats correctly filtered out - only valid M115 and M120 kept")
            return True
        return False

    def test_range_depot_values(self):
        """Test various values in the M212-M280 range"""
        print("\n🔍 Testing M212-M280 range depot values...")
        
        # Test various values in the range
        range_depots = ['M212', 'M220', 'M235', 'M250', 'M265', 'M280']
        
        excel_file = self.create_depot_test_commandes_excel(range_depots)
        
        files = {
            'file': ('range_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes with M212-M280 Range Values",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if success:
            # All range values should be kept
            if response['summary']['total_records'] != len(range_depots):
                print(f"❌ Expected {len(range_depots)} records, got {response['summary']['total_records']}")
                return False
            
            found_depots = set(response['filters']['depots'])
            expected_depots = set(range_depots)
            if found_depots != expected_depots:
                print(f"❌ Expected range depots {expected_depots}, got {found_depots}")
                return False
            
            print("✅ All M212-M280 range values correctly accepted")
            return True
        return False

    def test_calculation_with_filtered_depots(self):
        """Test that calculations work correctly with filtered depot data"""
        print("\n🔍 Testing calculations with filtered depot data...")
        
        # Upload mixed depot data (some will be filtered)
        mixed_depots = ['M115', 'M210', 'M211', 'M120', 'M212', 'M300']
        expected_allowed = ['M115', 'M120', 'M212']
        
        excel_file = self.create_depot_test_commandes_excel(mixed_depots)
        
        files = {
            'file': ('calc_filter_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        upload_success, upload_response = self.run_test(
            "Upload Mixed Depots for Calculation Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if upload_success:
            # Perform calculation
            calculation_data = {
                "days": 10
            }
            
            success, response = self.run_test(
                "Calculate with Filtered Depot Data",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                
                # Verify only allowed depots appear in results
                found_depots = set(calc['depot'] for calc in calculations)
                expected_depots = set(expected_allowed)
                
                if found_depots != expected_depots:
                    print(f"❌ Expected calculation depots {expected_depots}, got {found_depots}")
                    return False
                
                # Verify calculations are mathematically correct
                for calc in calculations:
                    expected_required = calc['cqm'] * 10  # 10 days
                    if abs(calc['quantite_requise'] - expected_required) > 0.01:
                        print(f"❌ Calculation error for {calc['depot']}: expected {expected_required}, got {calc['quantite_requise']}")
                        return False
                
                print(f"✅ Calculations work correctly with {len(calculations)} filtered depot results")
                return True
        return False

    def test_depot_suggestions_case_insensitive(self):
        """Test depot suggestions endpoint is case insensitive"""
        print("\n🔍 Testing depot suggestions case insensitivity...")
        
        # First upload some data
        allowed_depots = ['M115', 'M120']
        excel_file = self.create_depot_test_commandes_excel(allowed_depots)
        
        files = {
            'file': ('case_suggestions_test.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        upload_success, upload_response = self.run_test(
            "Upload for Case Insensitive Suggestions Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if upload_success:
            # Test with lowercase depot name
            suggestion_data = {
                "depot_name": "m115",  # lowercase
                "days": 10
            }
            
            success, response = self.run_test(
                "Depot Suggestions with Lowercase Depot Name",
                "POST",
                "api/depot-suggestions",
                200,
                data=suggestion_data
            )
            
            if success:
                if response['depot_name'] != 'm115':  # Should return as provided
                    print(f"❌ Expected depot_name 'm115', got '{response['depot_name']}'")
                    return False
                
                print("✅ Depot suggestions case insensitive - lowercase depot accepted")
                return True
        return False

    def run_all_tests(self):
        """Run all depot constraint tests"""
        print("🚀 Starting Depot Constraint Testing...")
        print("=" * 60)
        
        test_methods = [
            self.test_allowed_depots_commandes,
            self.test_non_allowed_depots_commandes,
            self.test_no_allowed_depots_error,
            self.test_transit_depot_filtering,
            self.test_depot_suggestions_allowed_depot,
            self.test_depot_suggestions_non_allowed_depot,
            self.test_depot_case_sensitivity,
            self.test_depot_whitespace_handling,
            self.test_boundary_depot_values,
            self.test_invalid_depot_formats,
            self.test_range_depot_values,
            self.test_calculation_with_filtered_depots,
            self.test_depot_suggestions_case_insensitive
        ]
        
        for test_method in test_methods:
            try:
                if not test_method():
                    print(f"❌ Test failed: {test_method.__name__}")
            except Exception as e:
                print(f"❌ Test error in {test_method.__name__}: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"🏁 Depot Constraint Testing Complete!")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = DepotConstraintTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)