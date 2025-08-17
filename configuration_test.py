import requests
import sys
import json
import io
import pandas as pd
import math
from datetime import datetime, timedelta

class ConfigurationSystemTester:
    def __init__(self, base_url="https://key-switcher.preview.emergentagent.com"):
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

    def create_multi_depot_commandes_excel(self):
        """Create sample commandes Excel file with multiple depots and articles for configuration testing"""
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004', 'CMD005', 'CMD006', 'CMD007', 'CMD008'],
            'Article': ['A1', 'A2', 'A3', 'A4', 'A1', 'A2', 'A3', 'A4'],  # Articles A1-A4
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6', 'Desc7', 'Desc8'],
            'Point d\'Expédition': ['M212', 'M212', 'M212', 'M212', 'M213', 'M213', 'M213', 'M213'],  # M212 and M213 depots (both allowed)
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6', 'Extra7', 'Extra8'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200, 110, 130],
            'Stock Utilisation Libre': [50, 75, 40, 60, 45, 100, 55, 65],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6', 'Extra7', 'Extra8'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre', 'pet', 'ciel', 'verre', 'pet'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4', 'Extra5', 'Extra6', 'Extra7', 'Extra8'],
            'Produits par Palette': [30, 30, 30, 30, 30, 30, 30, 30]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_stock_excel(self):
        """Create sample stock M210 Excel file"""
        data = {
            'Division': ['M210', 'M210', 'M210', 'M210'],
            'Article': ['A1', 'A2', 'A3', 'A4'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'STOCK A DATE': [500, 300, 200, 400]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_transit_excel(self):
        """Create sample transit Excel file"""
        data = {
            'Article': ['A1', 'A2', 'A3', 'A4'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Division': ['M212', 'M213', 'M212', 'M213'],  # Use allowed depots
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Division cédante': ['M210', 'M210', 'M210', 'M210'],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Quantité': [30, 20, 25, 15]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_get_configuration_initial(self):
        """Test GET /api/configuration - should return empty configuration initially"""
        success, response = self.run_test(
            "Get Initial Configuration",
            "GET",
            "api/configuration",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['depot_article_mapping', 'enabled']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Should be empty initially
            if response['depot_article_mapping'] != {}:
                print(f"❌ Expected empty depot_article_mapping, got {response['depot_article_mapping']}")
                return False
            
            if response['enabled'] != False:
                print(f"❌ Expected enabled=False initially, got {response['enabled']}")
                return False
            
            print("✅ Initial configuration is empty as expected")
            return True
        return False

    def test_upload_test_data(self):
        """Upload test data for configuration testing"""
        # Upload commandes data
        excel_file = self.create_multi_depot_commandes_excel()
        files = {
            'file': ('commandes.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes for Configuration Test",
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
        
        # Upload stock data
        stock_file = self.create_sample_stock_excel()
        files = {
            'file': ('stock.xlsx', stock_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Stock for Configuration Test",
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
        
        # Upload transit data
        transit_file = self.create_sample_transit_excel()
        files = {
            'file': ('transit.xlsx', transit_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit for Configuration Test",
            "POST",
            "api/upload-transit-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.transit_session_id = response['session_id']
            print(f"✅ Transit uploaded - Session ID: {self.transit_session_id}")
            return True
        return False

    def test_get_available_options(self):
        """Test GET /api/available-options - should return available depots and articles"""
        success, response = self.run_test(
            "Get Available Options",
            "GET",
            "api/available-options",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['depots', 'articles']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify we have the expected depots and articles
            expected_depots = ['M212', 'M213']
            expected_articles = ['A1', 'A2', 'A3', 'A4']
            
            if set(response['depots']) != set(expected_depots):
                print(f"❌ Expected depots {expected_depots}, got {response['depots']}")
                return False
            
            if set(response['articles']) != set(expected_articles):
                print(f"❌ Expected articles {expected_articles}, got {response['articles']}")
                return False
            
            print(f"✅ Available options: {len(response['depots'])} depots, {len(response['articles'])} articles")
            return True
        return False

    def test_save_configuration(self):
        """Test POST /api/configuration - save depot-article mapping configuration"""
        config_data = {
            "depot_article_mapping": {
                "M212": ["A1", "A2"],
                "M213": ["A3"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Configuration",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['message', 'configuration']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify configuration was saved correctly
            saved_config = response['configuration']
            if saved_config['depot_article_mapping'] != config_data['depot_article_mapping']:
                print(f"❌ Configuration not saved correctly")
                return False
            
            if saved_config['enabled'] != config_data['enabled']:
                print(f"❌ Enabled flag not saved correctly")
                return False
            
            print("✅ Configuration saved successfully")
            return True
        return False

    def test_get_saved_configuration(self):
        """Test GET /api/configuration - should return saved configuration"""
        success, response = self.run_test(
            "Get Saved Configuration",
            "GET",
            "api/configuration",
            200
        )
        
        if success:
            # Verify the configuration we saved is returned
            expected_mapping = {
                "M212": ["A1", "A2"],
                "M213": ["A3"]
            }
            
            if response['depot_article_mapping'] != expected_mapping:
                print(f"❌ Expected mapping {expected_mapping}, got {response['depot_article_mapping']}")
                return False
            
            if response['enabled'] != True:
                print(f"❌ Expected enabled=True, got {response['enabled']}")
                return False
            
            print("✅ Saved configuration retrieved correctly")
            return True
        return False

    def test_calculation_with_configuration_enabled(self):
        """Test calculation with configuration enabled - should filter depot-article combinations"""
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with Configuration Enabled",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify only configured combinations appear
            # M212 should only have A1, A2
            # M213 should only have A3
            # A4 should not appear anywhere
            # M212→A3, M213→A1, M213→A2 should be filtered out
            
            allowed_combinations = {
                ('A1', 'M212'),
                ('A2', 'M212'),
                ('A3', 'M213')
            }
            
            found_combinations = set()
            for calc in calculations:
                combination = (calc['article'], calc['depot'])
                found_combinations.add(combination)
                
                if combination not in allowed_combinations:
                    print(f"❌ Found non-configured combination: {combination}")
                    return False
            
            # Verify we have the expected combinations
            if found_combinations != allowed_combinations:
                print(f"❌ Expected combinations {allowed_combinations}, got {found_combinations}")
                return False
            
            print(f"✅ Configuration filtering working - only {len(calculations)} configured combinations in results")
            print(f"✅ Found combinations: {found_combinations}")
            return True
        return False

    def test_calculation_with_configuration_disabled(self):
        """Test calculation with configuration disabled - should work normally"""
        # First disable configuration
        config_data = {
            "depot_article_mapping": {
                "M212": ["A1", "A2"],
                "M213": ["A3"]
            },
            "enabled": False
        }
        
        success, response = self.run_test(
            "Disable Configuration",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Now test calculation
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with Configuration Disabled",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Should have all combinations (8 total: M212→A1,A2,A3,A4 and M213→A1,A2,A3,A4)
            expected_combinations = {
                ('A1', 'M212'), ('A2', 'M212'), ('A3', 'M212'), ('A4', 'M212'),
                ('A1', 'M213'), ('A2', 'M213'), ('A3', 'M213'), ('A4', 'M213')
            }
            
            found_combinations = set()
            for calc in calculations:
                combination = (calc['article'], calc['depot'])
                found_combinations.add(combination)
            
            if found_combinations != expected_combinations:
                print(f"❌ Expected all combinations {expected_combinations}, got {found_combinations}")
                return False
            
            print(f"✅ Configuration disabled - all {len(calculations)} combinations in results")
            return True
        return False

    def test_empty_depot_article_mapping(self):
        """Test with empty depot_article_mapping - should work normally when empty"""
        config_data = {
            "depot_article_mapping": {},
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Empty Configuration",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Test calculation with empty mapping - should work normally (not apply filtering)
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with Empty Mapping",
            "POST",
            "api/calculate",
            200,  # Should return 200 and work normally
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Should have all combinations (8 total) since empty mapping means no filtering
            expected_combinations = {
                ('A1', 'M212'), ('A2', 'M212'), ('A3', 'M212'), ('A4', 'M212'),
                ('A1', 'M213'), ('A2', 'M213'), ('A3', 'M213'), ('A4', 'M213')
            }
            
            found_combinations = set()
            for calc in calculations:
                combination = (calc['article'], calc['depot'])
                found_combinations.add(combination)
            
            if found_combinations != expected_combinations:
                print(f"❌ Expected all combinations {expected_combinations}, got {found_combinations}")
                return False
            
            print("✅ Empty depot-article mapping works normally (no filtering applied)")
            return True
        return False

    def test_depot_configured_no_articles(self):
        """Test with depot configured but no articles selected"""
        config_data = {
            "depot_article_mapping": {
                "M212": [],
                "M213": ["A3"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Configuration with Empty Article List",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Test calculation
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with Empty Article List for Depot",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Should only have M213→A3, no M212 combinations
            expected_combinations = {('A3', 'M213')}
            
            found_combinations = set()
            for calc in calculations:
                combination = (calc['article'], calc['depot'])
                found_combinations.add(combination)
            
            if found_combinations != expected_combinations:
                print(f"❌ Expected only {expected_combinations}, got {found_combinations}")
                return False
            
            print("✅ Depot with empty article list correctly excluded")
            return True
        return False

    def test_no_configured_combinations_found(self):
        """Test error handling when no configured combinations are found in data"""
        config_data = {
            "depot_article_mapping": {
                "M999": ["X1", "X2"]  # Non-existent depot and articles
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Configuration with Non-existent Combinations",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Test calculation - should return error
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with No Matching Combinations",
            "POST",
            "api/calculate",
            400,  # Should return error
            data=calculation_data
        )
        
        if success:
            print("✅ No configured combinations found correctly returns error")
            return True
        return False

    def test_partial_configuration_match(self):
        """Test configuration where only some combinations exist in data"""
        config_data = {
            "depot_article_mapping": {
                "M212": ["A1", "X999"],  # A1 exists, X999 doesn't
                "M213": ["A3"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Partial Configuration",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Test calculation
        calculation_data = {
            "days": 10
        }
        
        success, response = self.run_test(
            "Calculation with Partial Configuration Match",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Should only have combinations that exist in data: M212→A1, M213→A3
            expected_combinations = {('A1', 'M212'), ('A3', 'M213')}
            
            found_combinations = set()
            for calc in calculations:
                combination = (calc['article'], calc['depot'])
                found_combinations.add(combination)
            
            if found_combinations != expected_combinations:
                print(f"❌ Expected {expected_combinations}, got {found_combinations}")
                return False
            
            print("✅ Partial configuration match works correctly")
            return True
        return False

    def test_configuration_update(self):
        """Test updating existing configuration"""
        # First set initial configuration
        config_data = {
            "depot_article_mapping": {
                "M212": ["A1"],
                "M213": ["A2"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Save Initial Configuration for Update Test",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Update configuration
        updated_config_data = {
            "depot_article_mapping": {
                "M212": ["A1", "A2", "A3"],
                "M213": ["A4"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Update Configuration",
            "POST",
            "api/configuration",
            200,
            data=updated_config_data
        )
        
        if not success:
            return False
        
        # Verify updated configuration
        success, response = self.run_test(
            "Get Updated Configuration",
            "GET",
            "api/configuration",
            200
        )
        
        if success:
            if response['depot_article_mapping'] != updated_config_data['depot_article_mapping']:
                print(f"❌ Configuration not updated correctly")
                return False
            
            print("✅ Configuration updated successfully")
            return True
        return False

    def test_configuration_with_calculation_edge_cases(self):
        """Test configuration system with various calculation scenarios"""
        # Set configuration for comprehensive testing
        config_data = {
            "depot_article_mapping": {
                "M212": ["A1", "A2"],
                "M213": ["A3"]
            },
            "enabled": True
        }
        
        success, response = self.run_test(
            "Set Configuration for Edge Cases",
            "POST",
            "api/configuration",
            200,
            data=config_data
        )
        
        if not success:
            return False
        
        # Test with different days values
        for days in [1, 5, 10, 30]:
            calculation_data = {
                "days": days
            }
            
            success, response = self.run_test(
                f"Configuration Test with {days} Days",
                "POST",
                "api/calculate",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                
                # Verify filtering is consistent regardless of days
                allowed_combinations = {('A1', 'M212'), ('A2', 'M212'), ('A3', 'M213')}
                found_combinations = set()
                for calc in calculations:
                    combination = (calc['article'], calc['depot'])
                    found_combinations.add(combination)
                
                if found_combinations != allowed_combinations:
                    print(f"❌ Configuration filtering inconsistent for {days} days")
                    return False
                
                print(f"✅ Configuration filtering consistent for {days} days")
            else:
                return False
        
        return True

    def run_all_tests(self):
        """Run all configuration system tests"""
        print("🚀 Starting Configuration System Tests...")
        print("=" * 60)
        
        test_methods = [
            self.test_get_configuration_initial,
            self.test_upload_test_data,
            self.test_get_available_options,
            self.test_save_configuration,
            self.test_get_saved_configuration,
            self.test_calculation_with_configuration_enabled,
            self.test_calculation_with_configuration_disabled,
            self.test_empty_depot_article_mapping,
            self.test_depot_configured_no_articles,
            self.test_no_configured_combinations_found,
            self.test_partial_configuration_match,
            self.test_configuration_update,
            self.test_configuration_with_calculation_edge_cases
        ]
        
        for test_method in test_methods:
            try:
                if not test_method():
                    print(f"\n❌ Test failed: {test_method.__name__}")
                    break
            except Exception as e:
                print(f"\n💥 Test error in {test_method.__name__}: {str(e)}")
                break
        
        print("\n" + "=" * 60)
        print(f"📊 Configuration Tests Summary: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All configuration system tests passed!")
            return True
        else:
            print("❌ Some configuration system tests failed!")
            return False

if __name__ == "__main__":
    tester = ConfigurationSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)