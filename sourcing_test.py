import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class SourcingIntelligenceAPITester:
    def __init__(self, base_url="https://26c0a26b-a6c0-48b9-82e9-52e8233e0e04.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
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

    def create_sourcing_test_excel_file(self):
        """Create Excel file with specific article codes for sourcing testing"""
        # Create sample data with known local and external article codes
        data = {
            'Date de Commande': [
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=25),
                datetime.now() - timedelta(days=20),
                datetime.now() - timedelta(days=15),
                datetime.now() - timedelta(days=10),
                datetime.now() - timedelta(days=5)
            ],
            # Include specific articles for sourcing testing
            'Article': ['1011', '1016', '9999', '8888', '1021', '1033'],  # Mix of local and external
            'Désignation Article': [
                'COCA-COLA 33CL LOCAL 1011', 
                'PEPSI 50CL LOCAL 1016', 
                'SPRITE 33CL EXTERNAL 9999', 
                'FANTA 33CL EXTERNAL 8888',
                'ORANGINA 25CL LOCAL 1021',
                'COCA-ZERO 33CL LOCAL 1033'
            ],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT1'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B', 'Division C'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200],
            'Stock Utilisation Libre': [500, 300, 200, 400, 250, 600],
            'Ecart': [0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Ciel', 'Pet', 'Verre'],
            'Quantité en Palette': [24, 12, 24, 18, 12, 24]
        }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def test_upload_sourcing_excel(self):
        """Test Excel file upload with sourcing test data"""
        excel_file = self.create_sourcing_test_excel_file()
        
        files = {
            'file': ('sourcing_test_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Sourcing Test Excel File",
            "POST",
            "api/upload-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            print(f"Session ID: {self.session_id}")
            return True
        return False

    def test_sourcing_basic_calculate(self):
        """Test sourcing intelligence in basic calculation endpoint with specific articles"""
        if not self.session_id:
            print("❌ No session ID available for sourcing test")
            return False
            
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Sourcing Intelligence - Basic Calculate (Specific Articles)",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            print(f"\n📊 Testing {len(calculations)} calculations for sourcing intelligence:")
            
            local_articles_found = []
            external_articles_found = []
            
            for calc in calculations:
                article_code = str(calc['article_code'])
                is_locally_made = calc['is_locally_made']
                sourcing_status = calc['sourcing_status']
                sourcing_text = calc['sourcing_text']
                
                print(f"📋 Article {article_code}: locally_made={is_locally_made}, status={sourcing_status}, text='{sourcing_text}'")
                
                # Verify required sourcing fields are present
                required_fields = ['sourcing_status', 'sourcing_text', 'is_locally_made']
                for field in required_fields:
                    if field not in calc:
                        print(f"❌ Missing sourcing field '{field}' in calculation")
                        return False
                
                # Test known local articles (should be in LOCALLY_MADE_ARTICLES)
                if article_code in ['1011', '1016', '1021', '1033']:
                    local_articles_found.append(article_code)
                    if not is_locally_made:
                        print(f"❌ Article {article_code} should be locally made but is_locally_made={is_locally_made}")
                        return False
                    if sourcing_status != 'local':
                        print(f"❌ Article {article_code} should have sourcing_status='local' but got '{sourcing_status}'")
                        return False
                    if sourcing_text != 'Production Locale':
                        print(f"❌ Article {article_code} should have sourcing_text='Production Locale' but got '{sourcing_text}'")
                        return False
                    print(f"✅ Article {article_code} correctly identified as locally made")
                
                # Test known external articles (should NOT be in LOCALLY_MADE_ARTICLES)
                elif article_code in ['9999', '8888']:
                    external_articles_found.append(article_code)
                    if is_locally_made:
                        print(f"❌ Article {article_code} should be external but is_locally_made={is_locally_made}")
                        return False
                    if sourcing_status != 'external':
                        print(f"❌ Article {article_code} should have sourcing_status='external' but got '{sourcing_status}'")
                        return False
                    if sourcing_text != 'Sourcing Externe':
                        print(f"❌ Article {article_code} should have sourcing_text='Sourcing Externe' but got '{sourcing_text}'")
                        return False
                    print(f"✅ Article {article_code} correctly identified as external sourcing")
            
            # Verify summary contains sourcing statistics
            summary = response.get('summary', {})
            if 'sourcing_summary' not in summary:
                print("❌ Missing sourcing_summary in response summary")
                return False
            
            sourcing_summary = summary['sourcing_summary']
            local_count = sourcing_summary.get('local_items', 0)
            external_count = sourcing_summary.get('external_items', 0)
            
            print(f"\n📈 Sourcing Summary:")
            print(f"   Local items: {local_count}")
            print(f"   External items: {external_count}")
            print(f"   Local articles found: {local_articles_found}")
            print(f"   External articles found: {external_articles_found}")
            
            # Verify counts match expectations
            expected_local = len(local_articles_found)
            expected_external = len(external_articles_found)
            
            if local_count != expected_local:
                print(f"❌ Local count mismatch: expected {expected_local}, got {local_count}")
                return False
            
            if external_count != expected_external:
                print(f"❌ External count mismatch: expected {expected_external}, got {external_count}")
                return False
            
            print(f"✅ Sourcing summary counts are correct")
            return True
        
        return False

    def test_sourcing_enhanced_calculate(self):
        """Test sourcing intelligence in enhanced calculation endpoint"""
        if not self.session_id:
            print("❌ No session ID available for enhanced sourcing test")
            return False
            
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": None,  # No inventory for this test
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Sourcing Intelligence - Enhanced Calculate (Specific Articles)",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            print(f"\n📊 Testing {len(calculations)} enhanced calculations for sourcing intelligence:")
            
            for calc in calculations:
                article_code = str(calc['article_code'])
                is_locally_made = calc['is_locally_made']
                sourcing_status = calc['sourcing_status']
                sourcing_text = calc['sourcing_text']
                
                print(f"📋 Enhanced - Article {article_code}: locally_made={is_locally_made}, status={sourcing_status}, text='{sourcing_text}'")
                
                # Verify sourcing logic consistency
                if article_code in ['1011', '1016', '1021', '1033']:
                    if not is_locally_made or sourcing_status != 'local' or sourcing_text != 'Production Locale':
                        print(f"❌ Enhanced calculation: Article {article_code} sourcing data incorrect")
                        return False
                    print(f"✅ Enhanced - Article {article_code} correctly identified as locally made")
                
                elif article_code in ['9999', '8888']:
                    if is_locally_made or sourcing_status != 'external' or sourcing_text != 'Sourcing Externe':
                        print(f"❌ Enhanced calculation: Article {article_code} sourcing data incorrect")
                        return False
                    print(f"✅ Enhanced - Article {article_code} correctly identified as external sourcing")
            
            # Verify summary
            summary = response.get('summary', {})
            sourcing_summary = summary.get('sourcing_summary', {})
            local_count = sourcing_summary.get('local_items', 0)
            external_count = sourcing_summary.get('external_items', 0)
            
            print(f"✅ Enhanced sourcing summary: {local_count} local items, {external_count} external items")
            return True
        
        return False

def main():
    print("🚀 Starting Sourcing Intelligence API Tests")
    print("=" * 60)
    
    tester = SourcingIntelligenceAPITester()
    
    # Run sourcing-specific tests
    tests = [
        ("Upload Sourcing Test Excel File", tester.test_upload_sourcing_excel),
        ("Sourcing Intelligence - Basic Calculate", tester.test_sourcing_basic_calculate),
        ("Sourcing Intelligence - Enhanced Calculate", tester.test_sourcing_enhanced_calculate),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All sourcing intelligence tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())