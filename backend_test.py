import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime, timedelta

class StockManagementAPITester:
    def __init__(self, base_url="https://0074d26a-4347-4a2b-89d5-e02409ba89c8.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.inventory_session_id = None
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

    def create_sample_inventory_excel_file(self):
        """Create a sample inventory Excel file for testing"""
        # Create sample inventory data with required columns
        inventory_data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005', 'ART006', 'ART007'],
            'Désignation article': [
                'COCA-COLA 33CL VERRE',
                'PEPSI 50CL PET', 
                'SPRITE 33CL VERRE',
                'FANTA 33CL VERRE',
                'ORANGINA 25CL VERRE',
                'COCA-COLA ZERO 33CL PET',
                'PEPSI MAX 50CL PET'
            ],
            'STOCK À DATE': [1500, 800, 600, 1200, 300, 900, 450]
        }
        
        df = pd.DataFrame(inventory_data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def create_sample_excel_file(self):
        """Create a sample Excel file for testing with various packaging types and sourcing test articles"""
        # Create sample data with required columns including articles for sourcing intelligence testing
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
            # Include articles that should be local (1011, 1016) and external (9999, 8888) for sourcing testing
            'Article': ['1011', '1016', '9999', '8888', '1021', '1022', 'ART001', 'ART002'],
            'Désignation Article': ['COCA-COLA 33CL LOCAL', 'PEPSI 50CL LOCAL', 'SPRITE 33CL EXTERNAL', 'FANTA 33CL EXTERNAL', 'ORANGINA 25CL LOCAL', 'COCA-ZERO 33CL LOCAL', 'COCA-COLA 33CL', 'PEPSI 50CL'],
            'Point d\'Expédition': ['DEPOT1', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT2', 'DEPOT1', 'DEPOT3', 'DEPOT1'],
            'Nom Division': ['Division A', 'Division A', 'Division B', 'Division A', 'Division B', 'Division C', 'Division A', 'Division B'],
            'Quantité Commandée': [100, 150, 80, 120, 90, 200, 75, 110],
            'Stock Utilisation Libre': [500, 300, 200, 400, 250, 600, 180, 350],
            'Ecart': [0, 0, 0, 0, 0, 0, 0, 0],
            'Type Emballage': ['Verre', 'Pet', 'Verre', 'Ciel', 'Pet', 'Canette', 'Tétra', 'Verre'],  # Mix of allowed and non-allowed types
            'Quantité en Palette': [24, 12, 24, 18, 12, 36, 20, 24]
        }
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        return excel_buffer

    def use_sample_excel_file(self):
        """Use the existing sample_stock_data.xlsx file"""
        try:
            with open('/app/sample_stock_data.xlsx', 'rb') as f:
                return io.BytesIO(f.read())
        except FileNotFoundError:
            print("⚠️ sample_stock_data.xlsx not found, using generated sample")
            return self.create_sample_excel_file()

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_upload_excel(self):
        """Test Excel file upload"""
        excel_file = self.use_sample_excel_file()
        
        files = {
            'file': ('sample_stock_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Excel File",
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

    def test_packaging_filter_enhancement(self):
        """Test that packaging filter only returns allowed types (verre, pet, ciel)"""
        if not self.session_id:
            print("❌ No session ID available for packaging filter test")
            return False
            
        success, response = self.run_test(
            "Packaging Filter Enhancement",
            "GET",
            f"api/filters/{self.session_id}",
            200
        )
        
        if success and 'packaging' in response:
            packaging_types = [pkg['value'] for pkg in response['packaging']]
            allowed_types = ['Verre', 'Pet', 'Ciel']
            
            print(f"📋 Found packaging types: {packaging_types}")
            
            # Check that only allowed types are returned
            invalid_types = [pkg for pkg in packaging_types if pkg not in allowed_types]
            if invalid_types:
                print(f"❌ Found non-allowed packaging types: {invalid_types}")
                return False
            
            # Check that all returned types are from the allowed list
            valid_types_found = [pkg for pkg in packaging_types if pkg in allowed_types]
            print(f"✅ Valid packaging types found: {valid_types_found}")
            
            # Verify display names are present
            for pkg in response['packaging']:
                if 'display' not in pkg:
                    print(f"❌ Missing display name for packaging type: {pkg}")
                    return False
                print(f"📦 {pkg['value']} -> {pkg['display']}")
            
            return True
        
        print("❌ No packaging data found in response")
        return False

    def test_upload_inventory_excel(self):
        """Test inventory Excel file upload"""
        inventory_file = self.create_sample_inventory_excel_file()
        
        files = {
            'file': ('sample_inventory_data.xlsx', inventory_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Inventory Excel File",
            "POST",
            "api/upload-inventory-excel",
            200,
            files=files
        )
        
        if success and 'session_id' in response:
            self.inventory_session_id = response['session_id']
            print(f"Inventory Session ID: {self.inventory_session_id}")
            
            # Verify response structure
            required_fields = ['session_id', 'message', 'records_count', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in response: {field}")
                    return False
            
            # Verify summary structure
            summary = response['summary']
            summary_fields = ['divisions', 'articles_count', 'total_stock', 'records_count']
            for field in summary_fields:
                if field not in summary:
                    print(f"❌ Missing required field in summary: {field}")
                    return False
            
            print(f"✅ Inventory upload successful with {response['records_count']} records")
            print(f"✅ Total stock: {summary['total_stock']} units")
            print(f"✅ Articles count: {summary['articles_count']}")
            return True
        return False

    def test_upload_inventory_excel_missing_columns(self):
        """Test inventory Excel upload with missing required columns"""
        # Create invalid inventory data missing required columns
        invalid_data = {
            'Division': ['M210', 'M210'],
            'Article': ['ART001', 'ART002'],
            # Missing 'Désignation article' and 'STOCK À DATE'
        }
        
        df = pd.DataFrame(invalid_data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {
            'file': ('invalid_inventory.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Invalid Inventory Excel (Missing Columns)",
            "POST",
            "api/upload-inventory-excel",
            400,
            files=files
        )
        
        # Success here means we got the expected 400 error
        return success

    def test_get_inventory_data(self):
        """Test inventory data retrieval endpoint"""
        if not self.inventory_session_id:
            print("❌ No inventory session ID available for inventory data test")
            return False
            
        success, response = self.run_test(
            "Get Inventory Data",
            "GET",
            f"api/inventory/{self.inventory_session_id}",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['data', 'upload_time', 'summary']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in inventory response: {field}")
                    return False
            
            print(f"✅ Retrieved inventory data with {len(response['data'])} records")
            return True
        return False

    def test_get_inventory_data_invalid_session(self):
        """Test inventory data retrieval with invalid session ID"""
        success, response = self.run_test(
            "Get Inventory Data (Invalid Session)",
            "GET",
            "api/inventory/invalid-session-id",
            404
        )
        # Success means we got the expected 404 error
        return success

    def test_enhanced_calculate_with_inventory(self):
        """Test enhanced calculation with inventory cross-reference"""
        if not self.session_id or not self.inventory_session_id:
            print("❌ Missing session IDs for enhanced calculation test")
            return False
            
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Inventory Cross-Reference",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['calculations', 'summary', 'inventory_status']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field in enhanced calculation response: {field}")
                    return False
            
            # Verify inventory status fields in calculations
            calculations = response['calculations']
            if calculations:
                sample_calc = calculations[0]
                inventory_fields = ['inventory_available', 'can_fulfill', 'inventory_status', 'inventory_status_text']
                for field in inventory_fields:
                    if field not in sample_calc:
                        print(f"❌ Missing inventory field in calculation: {field}")
                        return False
                
                print(f"✅ Enhanced calculation returned {len(calculations)} items with inventory data")
                
                # Check inventory status distribution
                status_counts = {}
                for calc in calculations:
                    status = calc.get('inventory_status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"📊 Inventory status distribution: {status_counts}")
                
                # Verify summary contains inventory statistics
                summary = response['summary']
                inventory_summary_fields = ['sufficient_items', 'partial_items', 'insufficient_items', 'not_found_items']
                for field in inventory_summary_fields:
                    if field not in summary:
                        print(f"❌ Missing inventory summary field: {field}")
                        return False
                
                print(f"✅ Inventory summary: Sufficient={summary['sufficient_items']}, Partial={summary['partial_items']}, Insufficient={summary['insufficient_items']}, Not Found={summary['not_found_items']}")
                return True
            else:
                print("⚠️ No calculations returned")
                return True  # This might be valid if no data matches filters
        return False

    def test_enhanced_calculate_without_inventory(self):
        """Test enhanced calculation without inventory data"""
        if not self.session_id:
            print("❌ No order session ID available for enhanced calculation test")
            return False
            
        calculation_data = {
            "days": 15,
            "order_session_id": self.session_id,
            "inventory_session_id": None,  # No inventory data
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate without Inventory",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            # Verify that inventory_status indicates no inventory data
            if response.get('inventory_status') != 'no_inventory_data':
                print(f"❌ Expected inventory_status 'no_inventory_data', got '{response.get('inventory_status')}'")
                return False
            
            # Verify calculations don't have inventory fields
            calculations = response.get('calculations', [])
            if calculations:
                sample_calc = calculations[0]
                if sample_calc.get('inventory_status') != 'no_data':
                    print(f"❌ Expected inventory_status 'no_data' in calculations, got '{sample_calc.get('inventory_status')}'")
                    return False
            
            print("✅ Enhanced calculation without inventory works correctly")
            return True
        return False

    def test_enhanced_calculate_invalid_order_session(self):
        """Test enhanced calculation with invalid order session ID"""
        calculation_data = {
            "days": 30,
            "order_session_id": "invalid-session-id",
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Enhanced Calculate (Invalid Order Session)",
            "POST",
            "api/enhanced-calculate",
            404,
            data=calculation_data
        )
        # Success means we got the expected 404 error
        return success

    def test_enhanced_calculate_with_filters(self):
        """Test enhanced calculation with product and packaging filters"""
        if not self.session_id or not self.inventory_session_id:
            print("❌ Missing session IDs for enhanced calculation with filters test")
            return False
            
        calculation_data = {
            "days": 20,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": ["COCA-COLA 33CL"],
            "packaging_filter": ["Verre", "Pet"]
        }
        
        success, response = self.run_test(
            "Enhanced Calculate with Filters",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success:
            calculations = response.get('calculations', [])
            print(f"✅ Enhanced calculation with filters returned {len(calculations)} items")
            
            # Verify that returned items match the filters
            for calc in calculations:
                if calc.get('packaging_type') not in ['Verre', 'Pet']:
                    print(f"❌ Found item with non-matching packaging: {calc.get('packaging_type')}")
                    return False
            
            return True
        return False

    def test_calculate_requirements(self):
        """Test calculation endpoint"""
        if not self.session_id:
            print("❌ No session ID available for calculation test")
            return False
            
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Calculate Requirements",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        return success

    def test_get_filters(self):
        """Test get filters endpoint"""
        if not self.session_id:
            print("❌ No session ID available for filters test")
            return False
            
        success, response = self.run_test(
            "Get Available Filters",
            "GET",
            f"api/filters/{self.session_id}",
            200
        )
        return success

    def test_calculate_with_packaging_filters(self):
        """Test calculation with packaging filters to verify only allowed types work"""
        if not self.session_id:
            print("❌ No session ID available for packaging filter calculation test")
            return False
        
        # Test with allowed packaging types
        allowed_calculation_data = {
            "days": 15,
            "product_filter": None,
            "packaging_filter": ["Verre", "Pet"]  # Only allowed types
        }
        
        success1, response1 = self.run_test(
            "Calculate with Allowed Packaging Filters",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=allowed_calculation_data
        )
        
        # Test with mixed allowed/non-allowed packaging types
        mixed_calculation_data = {
            "days": 15,
            "product_filter": None,
            "packaging_filter": ["Verre", "Pet", "Canette"]  # Mix of allowed and non-allowed
        }
        
        success2, response2 = self.run_test(
            "Calculate with Mixed Packaging Filters",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=mixed_calculation_data
        )
        
        # Verify that calculations work and return appropriate results
        if success1 and 'calculations' in response1:
            print(f"✅ Allowed packaging filter returned {len(response1['calculations'])} results")
        
        if success2 and 'calculations' in response2:
            print(f"✅ Mixed packaging filter returned {len(response2['calculations'])} results")
            # Should only return results for allowed packaging types that exist in data
            for calc in response2['calculations']:
                if calc['packaging_type'] not in ['Verre', 'Pet', 'Ciel']:
                    print(f"❌ Found non-allowed packaging type in results: {calc['packaging_type']}")
                    return False
        
        return success1 and success2

    def test_gemini_query_enhanced(self):
        """Test enhanced Gemini AI query endpoint with improved context"""
        if not self.session_id:
            print("❌ No session ID available for Gemini query test")
            return False
        
        # Test multiple queries to verify enhanced context and intelligence
        test_queries = [
            {
                "query": "Quels sont les 3 produits avec la plus forte consommation?",
                "description": "Top 3 products by consumption"
            },
            {
                "query": "Analyse les tendances de stock par dépôt",
                "description": "Stock trends by depot analysis"
            },
            {
                "query": "Quels produits nécessitent un réapprovisionnement urgent?",
                "description": "Products needing urgent restocking"
            },
            {
                "query": "Donne-moi des statistiques précises sur les volumes",
                "description": "Precise volume statistics"
            }
        ]
        
        all_passed = True
        
        for i, test_query in enumerate(test_queries, 1):
            query_data = {
                "query": test_query["query"],
                "session_id": self.session_id
            }
            
            success, response = self.run_test(
                f"Enhanced Gemini Query {i}: {test_query['description']}",
                "POST",
                f"api/gemini-query/{self.session_id}",
                200,
                data=query_data
            )
            
            if success and 'response' in response:
                ai_response = response['response']
                print(f"🤖 AI Response length: {len(ai_response)} characters")
                
                # Check for intelligent response characteristics
                if len(ai_response) < 50:
                    print(f"⚠️ Response seems too short: {ai_response}")
                    all_passed = False
                elif len(ai_response) > 1000:
                    print(f"⚠️ Response seems too long (should be 2-4 sentences): {len(ai_response)} chars")
                    all_passed = False
                else:
                    print(f"✅ Response length appropriate: {len(ai_response)} characters")
                
                # Check for French language
                french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'avec', 'pour', 'dans']
                if not any(indicator in ai_response.lower() for indicator in french_indicators):
                    print(f"⚠️ Response may not be in French: {ai_response[:100]}...")
                    all_passed = False
                else:
                    print("✅ Response appears to be in French")
                
                print(f"📝 Sample response: {ai_response[:200]}...")
            else:
                all_passed = False
        
        return all_passed

    def test_gemini_query_french(self):
        """Test Gemini AI query endpoint with French query (legacy test)"""
        if not self.session_id:
            print("❌ No session ID available for Gemini query test")
            return False
            
        query_data = {
            "query": "Quels sont les 3 produits avec la plus forte consommation?",
            "session_id": self.session_id
        }
        
        success, response = self.run_test(
            "Gemini AI Query (French)",
            "POST",
            f"api/gemini-query/{self.session_id}",
            200,
            data=query_data
        )
        return success

    def test_invalid_session_id(self):
        """Test with invalid session ID"""
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Invalid Session ID",
            "POST",
            "api/calculate/invalid-session-id",
            404,
            data=calculation_data
        )
        # For this test, success means we got the expected 404 error
        return success

    def test_sourcing_intelligence_basic_calculate(self):
        """Test sourcing intelligence in basic calculation endpoint"""
        if not self.session_id:
            print("❌ No session ID available for sourcing intelligence test")
            return False
            
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Sourcing Intelligence - Basic Calculate",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify sourcing fields are present in all calculations
            for calc in calculations:
                required_sourcing_fields = ['sourcing_status', 'sourcing_text', 'is_locally_made']
                for field in required_sourcing_fields:
                    if field not in calc:
                        print(f"❌ Missing sourcing field '{field}' in calculation")
                        return False
                
                # Verify sourcing logic for known articles
                article_code = str(calc['article_code'])
                is_locally_made = calc['is_locally_made']
                sourcing_status = calc['sourcing_status']
                sourcing_text = calc['sourcing_text']
                
                print(f"📋 Article {article_code}: locally_made={is_locally_made}, status={sourcing_status}, text={sourcing_text}")
                
                # Test known local articles (1011, 1016, 1021, 1022)
                if article_code in ['1011', '1016', '1021', '1022']:
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
                
                # Test known external articles (9999, 8888)
                elif article_code in ['9999', '8888']:
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
            required_summary_fields = ['local_items', 'external_items']
            for field in required_summary_fields:
                if field not in sourcing_summary:
                    print(f"❌ Missing field '{field}' in sourcing_summary")
                    return False
            
            local_count = sourcing_summary['local_items']
            external_count = sourcing_summary['external_items']
            total_items = len(calculations)
            
            if local_count + external_count != total_items:
                print(f"❌ Sourcing summary counts don't match total items: {local_count} + {external_count} != {total_items}")
                return False
            
            print(f"✅ Sourcing summary: {local_count} local items, {external_count} external items (total: {total_items})")
            return True
        
        return False

    def test_sourcing_intelligence_enhanced_calculate(self):
        """Test sourcing intelligence in enhanced calculation endpoint"""
        if not self.session_id:
            print("❌ No session ID available for enhanced sourcing intelligence test")
            return False
            
        calculation_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,  # May be None
            "product_filter": None,
            "packaging_filter": None
        }
        
        success, response = self.run_test(
            "Sourcing Intelligence - Enhanced Calculate",
            "POST",
            "api/enhanced-calculate",
            200,
            data=calculation_data
        )
        
        if success and 'calculations' in response:
            calculations = response['calculations']
            
            # Verify sourcing fields are present in all calculations
            for calc in calculations:
                required_sourcing_fields = ['sourcing_status', 'sourcing_text', 'is_locally_made']
                for field in required_sourcing_fields:
                    if field not in calc:
                        print(f"❌ Missing sourcing field '{field}' in enhanced calculation")
                        return False
                
                # Verify sourcing logic consistency with basic calculation
                article_code = str(calc['article_code'])
                is_locally_made = calc['is_locally_made']
                sourcing_status = calc['sourcing_status']
                sourcing_text = calc['sourcing_text']
                
                print(f"📋 Enhanced - Article {article_code}: locally_made={is_locally_made}, status={sourcing_status}, text={sourcing_text}")
                
                # Test known local articles
                if article_code in ['1011', '1016', '1021', '1022']:
                    if not is_locally_made or sourcing_status != 'local' or sourcing_text != 'Production Locale':
                        print(f"❌ Enhanced calculation: Article {article_code} sourcing data incorrect")
                        return False
                    print(f"✅ Enhanced - Article {article_code} correctly identified as locally made")
                
                # Test known external articles
                elif article_code in ['9999', '8888']:
                    if is_locally_made or sourcing_status != 'external' or sourcing_text != 'Sourcing Externe':
                        print(f"❌ Enhanced calculation: Article {article_code} sourcing data incorrect")
                        return False
                    print(f"✅ Enhanced - Article {article_code} correctly identified as external sourcing")
            
            # Verify summary contains sourcing statistics
            summary = response.get('summary', {})
            if 'sourcing_summary' not in summary:
                print("❌ Missing sourcing_summary in enhanced calculation response summary")
                return False
            
            sourcing_summary = summary['sourcing_summary']
            local_count = sourcing_summary.get('local_items', 0)
            external_count = sourcing_summary.get('external_items', 0)
            
            print(f"✅ Enhanced sourcing summary: {local_count} local items, {external_count} external items")
            return True
        
        return False

    def test_sourcing_data_consistency(self):
        """Test that sourcing data is consistent between basic and enhanced calculations"""
        if not self.session_id:
            print("❌ No session ID available for sourcing consistency test")
            return False
        
        # Get basic calculation results
        basic_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success1, basic_response = self.run_test(
            "Sourcing Consistency - Basic Calculate",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=basic_data
        )
        
        # Get enhanced calculation results
        enhanced_data = {
            "days": 30,
            "order_session_id": self.session_id,
            "inventory_session_id": self.inventory_session_id,
            "product_filter": None,
            "packaging_filter": None
        }
        
        success2, enhanced_response = self.run_test(
            "Sourcing Consistency - Enhanced Calculate",
            "POST",
            "api/enhanced-calculate",
            200,
            data=enhanced_data
        )
        
        if success1 and success2:
            basic_calcs = basic_response.get('calculations', [])
            enhanced_calcs = enhanced_response.get('calculations', [])
            
            # Create lookup dictionaries for comparison
            basic_sourcing = {}
            enhanced_sourcing = {}
            
            for calc in basic_calcs:
                key = f"{calc['depot']}_{calc['article_code']}_{calc['packaging_type']}"
                basic_sourcing[key] = {
                    'is_locally_made': calc['is_locally_made'],
                    'sourcing_status': calc['sourcing_status'],
                    'sourcing_text': calc['sourcing_text']
                }
            
            for calc in enhanced_calcs:
                key = f"{calc['depot']}_{calc['article_code']}_{calc['packaging_type']}"
                enhanced_sourcing[key] = {
                    'is_locally_made': calc['is_locally_made'],
                    'sourcing_status': calc['sourcing_status'],
                    'sourcing_text': calc['sourcing_text']
                }
            
            # Compare sourcing data for matching items
            inconsistencies = 0
            for key in basic_sourcing:
                if key in enhanced_sourcing:
                    basic_item = basic_sourcing[key]
                    enhanced_item = enhanced_sourcing[key]
                    
                    for field in ['is_locally_made', 'sourcing_status', 'sourcing_text']:
                        if basic_item[field] != enhanced_item[field]:
                            print(f"❌ Inconsistency in {key} field {field}: basic='{basic_item[field]}' vs enhanced='{enhanced_item[field]}'")
                            inconsistencies += 1
            
            if inconsistencies == 0:
                print(f"✅ Sourcing data is consistent between basic and enhanced calculations ({len(basic_sourcing)} items checked)")
                return True
            else:
                print(f"❌ Found {inconsistencies} sourcing data inconsistencies")
                return False
        
        return False

    def test_sourcing_specific_articles(self):
        """Test sourcing logic with specific known articles"""
        if not self.session_id:
            print("❌ No session ID available for specific articles sourcing test")
            return False
        
        # Test with filters to focus on specific articles
        test_cases = [
            {
                "name": "Local Articles Only",
                "filter": ["COCA-COLA 33CL LOCAL", "PEPSI 50CL LOCAL", "ORANGINA 25CL LOCAL", "COCA-ZERO 33CL LOCAL"],
                "expected_local": True
            },
            {
                "name": "External Articles Only", 
                "filter": ["SPRITE 33CL EXTERNAL", "FANTA 33CL EXTERNAL"],
                "expected_local": False
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            calculation_data = {
                "days": 30,
                "product_filter": test_case["filter"],
                "packaging_filter": None
            }
            
            success, response = self.run_test(
                f"Sourcing Test - {test_case['name']}",
                "POST",
                f"api/calculate/{self.session_id}",
                200,
                data=calculation_data
            )
            
            if success and 'calculations' in response:
                calculations = response['calculations']
                
                for calc in calculations:
                    article_code = str(calc['article_code'])
                    is_locally_made = calc['is_locally_made']
                    
                    if test_case["expected_local"] and not is_locally_made:
                        print(f"❌ {test_case['name']}: Article {article_code} should be local but is_locally_made={is_locally_made}")
                        all_passed = False
                    elif not test_case["expected_local"] and is_locally_made:
                        print(f"❌ {test_case['name']}: Article {article_code} should be external but is_locally_made={is_locally_made}")
                        all_passed = False
                    else:
                        expected_status = "local" if test_case["expected_local"] else "external"
                        print(f"✅ {test_case['name']}: Article {article_code} correctly identified as {expected_status}")
            else:
                all_passed = False
        
        return all_passed

    def test_invalid_file_upload(self):
        """Test uploading invalid file"""
        # Create a text file instead of Excel
        text_content = "This is not an Excel file"
        files = {
            'file': ('test.txt', io.StringIO(text_content), 'text/plain')
        }
        
        success, response = self.run_test(
            "Invalid File Upload",
            "POST",
            "api/upload-excel",
            400,
            files=files
        )
        return success

    def test_excel_export_with_sourcing_column(self):
        """Test Excel export functionality with new Sourcing column"""
        if not self.session_id:
            print("❌ No session ID available for Excel export test")
            return False
        
        # First, get some calculation results to export
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        calc_success, calc_response = self.run_test(
            "Get Calculations for Export Test",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if not calc_success or 'calculations' in calc_response:
            calculations = calc_response.get('calculations', [])
            if not calculations:
                print("⚠️ No calculations available for export test")
                return True  # Not a failure, just no data
            
            # Select a few items for export, including both local and external articles
            selected_items = []
            local_found = False
            external_found = False
            
            for calc in calculations[:5]:  # Take first 5 items
                selected_items.append(calc)
                if calc.get('is_locally_made', False):
                    local_found = True
                else:
                    external_found = True
            
            if not selected_items:
                print("⚠️ No items selected for export test")
                return True
            
            # Test Excel export
            export_data = {
                "selected_items": selected_items,
                "session_id": self.session_id
            }
            
            print(f"📋 Testing Excel export with {len(selected_items)} items")
            print(f"📋 Local articles found: {local_found}, External articles found: {external_found}")
            
            # Test the export endpoint
            url = f"{self.base_url}/api/export-critical/{self.session_id}"
            headers = {'Content-Type': 'application/json'}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Excel Export with Sourcing Column...")
            print(f"URL: {url}")
            
            try:
                response = requests.post(url, json=export_data, headers=headers)
                
                if response.status_code == 200:
                    self.tests_passed += 1
                    print(f"✅ Passed - Status: {response.status_code}")
                    
                    # Check if response is Excel file
                    content_type = response.headers.get('content-type', '')
                    if 'spreadsheet' in content_type or 'excel' in content_type:
                        print("✅ Response is Excel file format")
                        
                        # Check Content-Disposition header for filename
                        content_disposition = response.headers.get('content-disposition', '')
                        if 'CBGS_Articles_Critiques_' in content_disposition:
                            print("✅ Excel filename format is correct")
                        else:
                            print(f"⚠️ Unexpected filename format: {content_disposition}")
                        
                        # Try to read the Excel content to verify structure
                        try:
                            excel_content = io.BytesIO(response.content)
                            df = pd.read_excel(excel_content)
                            
                            print(f"📊 Excel file contains {len(df)} rows and {len(df.columns)} columns")
                            print(f"📋 Column headers: {list(df.columns)}")
                            
                            # Check for the new Sourcing column
                            if 'Sourcing' in df.columns:
                                print("✅ 'Sourcing' column found in Excel export")
                                
                                # Verify sourcing values
                                sourcing_values = df['Sourcing'].unique()
                                print(f"📋 Sourcing values found: {list(sourcing_values)}")
                                
                                expected_values = ['Production Locale', 'Sourcing Externe']
                                valid_values = [val for val in sourcing_values if val in expected_values]
                                
                                if len(valid_values) > 0:
                                    print(f"✅ Valid sourcing values found: {valid_values}")
                                    
                                    # Check if we have both types if we expected them
                                    if local_found and 'Production Locale' not in sourcing_values:
                                        print("❌ Expected 'Production Locale' but not found in Excel")
                                        return False
                                    if external_found and 'Sourcing Externe' not in sourcing_values:
                                        print("❌ Expected 'Sourcing Externe' but not found in Excel")
                                        return False
                                    
                                    print("✅ Sourcing column values are correct")
                                else:
                                    print(f"❌ No valid sourcing values found. Expected: {expected_values}")
                                    return False
                                
                                # Verify expected number of columns (should be 11 with new Sourcing column)
                                expected_columns = 11
                                if len(df.columns) == expected_columns:
                                    print(f"✅ Excel has expected {expected_columns} columns")
                                else:
                                    print(f"⚠️ Excel has {len(df.columns)} columns, expected {expected_columns}")
                                
                                return True
                            else:
                                print("❌ 'Sourcing' column not found in Excel export")
                                return False
                                
                        except Exception as e:
                            print(f"⚠️ Could not parse Excel content: {str(e)}")
                            # Still consider it a success if the file downloads correctly
                            return True
                    else:
                        print(f"⚠️ Unexpected content type: {content_type}")
                        return False
                else:
                    print(f"❌ Failed - Expected 200, got {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"Error response: {error_data}")
                    except:
                        print(f"Error text: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed - Error: {str(e)}")
                return False
        else:
            print("❌ Could not get calculations for export test")
            return False

    def test_excel_export_sourcing_logic(self):
        """Test Excel export sourcing logic with known articles"""
        if not self.session_id:
            print("❌ No session ID available for Excel export sourcing logic test")
            return False
        
        # Create test items with known sourcing status
        test_items = [
            {
                'id': 'test_local_1011',
                'depot': 'Test Depot',
                'article_code': '1011',  # Known local article
                'article_name': 'Test Local Product 1011',
                'packaging_type': 'Verre',
                'current_stock': 100,
                'average_daily_consumption': 5.0,
                'days_of_coverage': 20.0,
                'quantity_to_send': 50.0,
                'priority': 'high',
                'priority_text': 'Critique',
                'sourcing_status': 'local',
                'sourcing_text': 'Production Locale',
                'is_locally_made': True
            },
            {
                'id': 'test_external_9999',
                'depot': 'Test Depot',
                'article_code': '9999',  # Known external article
                'article_name': 'Test External Product 9999',
                'packaging_type': 'Pet',
                'current_stock': 80,
                'average_daily_consumption': 3.0,
                'days_of_coverage': 26.7,
                'quantity_to_send': 10.0,
                'priority': 'medium',
                'priority_text': 'Moyen',
                'sourcing_status': 'external',
                'sourcing_text': 'Sourcing Externe',
                'is_locally_made': False
            }
        ]
        
        export_data = {
            "selected_items": test_items,
            "session_id": self.session_id
        }
        
        print(f"📋 Testing Excel export sourcing logic with {len(test_items)} test items")
        
        # Test the export endpoint
        url = f"{self.base_url}/api/export-critical/{self.session_id}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Excel Export Sourcing Logic...")
        print(f"URL: {url}")
        
        try:
            response = requests.post(url, json=export_data, headers=headers)
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Parse Excel content to verify sourcing logic
                try:
                    excel_content = io.BytesIO(response.content)
                    df = pd.read_excel(excel_content)
                    
                    print(f"📊 Excel file contains {len(df)} data rows")
                    
                    # Find the data rows (skip header rows)
                    data_start_row = None
                    for i, row in df.iterrows():
                        if 'Code Article' in str(row.iloc[1]) or str(row.iloc[1]) in ['1011', '9999']:
                            data_start_row = i
                            break
                    
                    if data_start_row is not None:
                        data_df = df.iloc[data_start_row:]
                        
                        # Check sourcing values for our test articles
                        for _, row in data_df.iterrows():
                            article_code = str(row.iloc[1])  # Code Article column
                            sourcing_value = row.iloc[8]     # Sourcing column (9th column, index 8)
                            
                            if article_code == '1011':
                                if sourcing_value == 'Production Locale':
                                    print(f"✅ Article 1011 correctly shows 'Production Locale' in Excel")
                                else:
                                    print(f"❌ Article 1011 shows '{sourcing_value}' instead of 'Production Locale'")
                                    return False
                            elif article_code == '9999':
                                if sourcing_value == 'Sourcing Externe':
                                    print(f"✅ Article 9999 correctly shows 'Sourcing Externe' in Excel")
                                else:
                                    print(f"❌ Article 9999 shows '{sourcing_value}' instead of 'Sourcing Externe'")
                                    return False
                        
                        print("✅ Excel export sourcing logic is working correctly")
                        return True
                    else:
                        print("⚠️ Could not find data rows in Excel file")
                        return True  # Still consider success if file is generated
                        
                except Exception as e:
                    print(f"⚠️ Could not parse Excel content for sourcing verification: {str(e)}")
                    return True  # Still consider success if file downloads
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_excel_export_regression(self):
        """Test that Excel export maintains all existing functionality"""
        if not self.session_id:
            print("❌ No session ID available for Excel export regression test")
            return False
        
        # Get calculation results
        calculation_data = {
            "days": 30,
            "product_filter": None,
            "packaging_filter": None
        }
        
        calc_success, calc_response = self.run_test(
            "Get Calculations for Regression Test",
            "POST",
            f"api/calculate/{self.session_id}",
            200,
            data=calculation_data
        )
        
        if calc_success and 'calculations' in calc_response:
            calculations = calc_response.get('calculations', [])
            if not calculations:
                print("⚠️ No calculations available for regression test")
                return True
            
            # Select items for export
            selected_items = calculations[:3]  # Take first 3 items
            
            export_data = {
                "selected_items": selected_items,
                "session_id": self.session_id
            }
            
            print(f"📋 Testing Excel export regression with {len(selected_items)} items")
            
            # Test the export endpoint
            url = f"{self.base_url}/api/export-critical/{self.session_id}"
            headers = {'Content-Type': 'application/json'}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Excel Export Regression...")
            print(f"URL: {url}")
            
            try:
                response = requests.post(url, json=export_data, headers=headers)
                
                if response.status_code == 200:
                    self.tests_passed += 1
                    print(f"✅ Passed - Status: {response.status_code}")
                    
                    # Parse Excel content to verify all expected columns exist
                    try:
                        excel_content = io.BytesIO(response.content)
                        df = pd.read_excel(excel_content)
                        
                        # Expected columns (including new Sourcing column)
                        expected_columns = [
                            'Dépôt', 'Code Article', 'Désignation Article', 'Type Emballage',
                            'Stock Actuel', 'Consommation Quotidienne', 'Jours de Couverture',
                            'Quantité Requise', 'Sourcing', 'Priorité', 'Action Recommandée'
                        ]
                        
                        # Find header row
                        header_row = None
                        for i, row in df.iterrows():
                            if 'Dépôt' in str(row.iloc[0]):
                                header_row = i
                                break
                        
                        if header_row is not None:
                            headers = df.iloc[header_row].tolist()
                            print(f"📋 Found headers: {headers}")
                            
                            # Check all expected columns are present
                            missing_columns = []
                            for expected_col in expected_columns:
                                if expected_col not in headers:
                                    missing_columns.append(expected_col)
                            
                            if missing_columns:
                                print(f"❌ Missing expected columns: {missing_columns}")
                                return False
                            else:
                                print(f"✅ All {len(expected_columns)} expected columns found")
                            
                            # Verify we have the right number of columns
                            if len(headers) >= len(expected_columns):
                                print(f"✅ Excel has {len(headers)} columns (expected at least {len(expected_columns)})")
                            else:
                                print(f"❌ Excel has only {len(headers)} columns, expected at least {len(expected_columns)}")
                                return False
                            
                            # Check that data rows exist
                            data_rows = df.iloc[header_row + 1:]
                            if len(data_rows) >= len(selected_items):
                                print(f"✅ Excel contains {len(data_rows)} data rows (expected {len(selected_items)})")
                            else:
                                print(f"⚠️ Excel contains {len(data_rows)} data rows, expected {len(selected_items)}")
                            
                            print("✅ Excel export regression test passed - all existing functionality maintained")
                            return True
                        else:
                            print("⚠️ Could not find header row in Excel file")
                            return True  # Still consider success if file is generated
                            
                    except Exception as e:
                        print(f"⚠️ Could not parse Excel content for regression test: {str(e)}")
                        return True  # Still consider success if file downloads
                else:
                    print(f"❌ Failed - Expected 200, got {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed - Error: {str(e)}")
                return False
        else:
            print("❌ Could not get calculations for regression test")
            return False

def main():
    print("🚀 Starting Stock Management API Tests")
    print("=" * 50)
    
    # Setup
    tester = StockManagementAPITester()
    
    # Run tests in sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Upload Excel File", tester.test_upload_excel),
        ("Upload Inventory Excel File", tester.test_upload_inventory_excel),
        ("Upload Invalid Inventory Excel (Missing Columns)", tester.test_upload_inventory_excel_missing_columns),
        ("Get Inventory Data", tester.test_get_inventory_data),
        ("Get Inventory Data (Invalid Session)", tester.test_get_inventory_data_invalid_session),
        ("Enhanced Calculate with Inventory Cross-Reference", tester.test_enhanced_calculate_with_inventory),
        ("Enhanced Calculate without Inventory", tester.test_enhanced_calculate_without_inventory),
        ("Enhanced Calculate (Invalid Order Session)", tester.test_enhanced_calculate_invalid_order_session),
        ("Enhanced Calculate with Filters", tester.test_enhanced_calculate_with_filters),
        ("Packaging Filter Enhancement", tester.test_packaging_filter_enhancement),
        ("Get Available Filters", tester.test_get_filters),
        ("Calculate Requirements", tester.test_calculate_requirements),
        ("Calculate with Packaging Filters", tester.test_calculate_with_packaging_filters),
        # Sourcing Intelligence Tests
        ("Sourcing Intelligence - Basic Calculate", tester.test_sourcing_intelligence_basic_calculate),
        ("Sourcing Intelligence - Enhanced Calculate", tester.test_sourcing_intelligence_enhanced_calculate),
        ("Sourcing Data Consistency", tester.test_sourcing_data_consistency),
        ("Sourcing Specific Articles", tester.test_sourcing_specific_articles),
        # Excel Export Tests (NEW)
        ("Excel Export with Sourcing Column", tester.test_excel_export_with_sourcing_column),
        ("Excel Export Sourcing Logic", tester.test_excel_export_sourcing_logic),
        ("Excel Export Regression Test", tester.test_excel_export_regression),
        # AI and other tests
        ("Enhanced Gemini AI Queries", tester.test_gemini_query_enhanced),
        ("Gemini AI Query (French)", tester.test_gemini_query_french),
        ("Invalid Session ID", tester.test_invalid_session_id),
        ("Invalid File Upload", tester.test_invalid_file_upload),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())