import requests
import sys
import json
import io
import pandas as pd
import os
from datetime import datetime

class AIChatRobustnessTester:
    def __init__(self, base_url="https://palette-qty-logic.preview.emergentagent.com"):
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

    def create_sample_commandes_excel(self):
        """Create sample commandes Excel file"""
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004'],
            'Article': ['1011', '1016', '1021', '9999'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M212'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Quantité Commandée': [100, 150, 80, 120],
            'Stock Utilisation Libre': [50, 75, 40, 60],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Type Emballage': ['verre', 'pet', 'ciel', 'verre'],
            'Dummy_J': ['Extra1', 'Extra2', 'Extra3', 'Extra4'],
            'Produits par Palette': [30, 30, 30, 30]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_stock_excel(self):
        """Create sample stock M210 Excel file"""
        data = {
            'Division': ['M210', 'M210', 'M210', 'M210', 'M210', 'M210'],
            'Article': ['1011', '1016', '1021', '9999', '8888', '1033'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4', 'Desc5', 'Desc6'],
            'STOCK A DATE': [500, 300, 200, 400, 250, 350]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def test_ai_chat_without_data(self):
        """Test AI chat endpoint without any uploaded data - should return HTTP 200 with minimal bullet response"""
        print("\n🔍 Testing AI Chat without any uploaded data...")
        
        chat_data = {
            "message": "What is the current status of inventory?",
            "conversation_id": None
        }
        
        success, response = self.run_test(
            "AI Chat Without Data - Minimal Bullet Response",
            "POST",
            "api/chat",
            200,
            data=chat_data
        )
        
        if success:
            # Verify response schema
            required_fields = ['response', 'conversation_id', 'has_data', 'data_types']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify has_data is False when no data uploaded
            if response['has_data'] != False:
                print(f"❌ Expected has_data=False, got {response['has_data']}")
                return False
            
            # Verify data_types is empty when no data uploaded
            if response['data_types'] != []:
                print(f"❌ Expected empty data_types, got {response['data_types']}")
                return False
            
            # Verify response is in minimal bullet format
            response_text = response['response']
            if not response_text.startswith('*'):
                print(f"❌ Expected bullet format response starting with '*', got: {response_text[:50]}")
                return False
            
            # Verify response contains data counts (should be 0s)
            if 'Commandes: 0' not in response_text or 'Stock: 0' not in response_text or 'Transit: 0' not in response_text:
                print(f"❌ Expected minimal bullet response with zero counts, got: {response_text}")
                return False
            
            print("✅ AI Chat without data returns HTTP 200 with minimal bullet response")
            print(f"✅ Response format: {response_text}")
            return True
        
        return False

    def test_ai_chat_with_uploaded_data(self):
        """Test AI chat endpoint after uploading data - should return HTTP 200 with correct bullet counts"""
        print("\n🔍 Testing AI Chat with uploaded data...")
        
        # First upload commandes data
        excel_file = self.create_sample_commandes_excel()
        files = {
            'file': ('commandes.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, upload_response = self.run_test(
            "Upload Commandes for Chat Test",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Upload stock data
        stock_file = self.create_sample_stock_excel()
        files = {
            'file': ('stock.xlsx', stock_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, stock_response = self.run_test(
            "Upload Stock for Chat Test",
            "POST",
            "api/upload-stock-excel",
            200,
            files=files
        )
        
        if not success:
            return False
        
        # Now test AI chat with data
        chat_data = {
            "message": "What is the current status of inventory?",
            "conversation_id": None
        }
        
        success, response = self.run_test(
            "AI Chat With Data - Correct Bullet Counts",
            "POST",
            "api/chat",
            200,
            data=chat_data
        )
        
        if success:
            # Verify response schema
            required_fields = ['response', 'conversation_id', 'has_data', 'data_types']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify has_data is True when data is uploaded
            if response['has_data'] != True:
                print(f"❌ Expected has_data=True, got {response['has_data']}")
                return False
            
            # Verify data_types contains uploaded data types
            expected_data_types = ['commandes', 'stock']
            for data_type in expected_data_types:
                if data_type not in response['data_types']:
                    print(f"❌ Expected data_type '{data_type}' in {response['data_types']}")
                    return False
            
            # Verify response contains correct data counts
            response_text = response['response']
            commandes_count = upload_response['summary']['total_records']
            stock_count = stock_response['summary']['total_records']
            
            if f'Commandes: {commandes_count}' not in response_text:
                print(f"❌ Expected 'Commandes: {commandes_count}' in response: {response_text}")
                return False
            
            if f'Stock: {stock_count}' not in response_text:
                print(f"❌ Expected 'Stock: {stock_count}' in response: {response_text}")
                return False
            
            print("✅ AI Chat with data returns HTTP 200 with correct bullet counts")
            print(f"✅ Response format: {response_text}")
            print(f"✅ Data types: {response['data_types']}")
            return True
        
        return False

    def test_ai_chat_graceful_degradation(self):
        """Test that AI chat degrades gracefully without Google Generative AI library"""
        print("\n🔍 Testing AI Chat graceful degradation...")
        
        # Test multiple scenarios to ensure no 500 errors
        test_messages = [
            "Simple test message",
            "What is the inventory status?",
            "Tell me about stock levels",
            "How many palettes do we need?",
            "What are the depot recommendations?",
            "",  # Empty message
            "A" * 1000,  # Very long message
        ]
        
        for i, message in enumerate(test_messages):
            chat_data = {
                "message": message,
                "conversation_id": f"test_conv_{i}"
            }
            
            success, response = self.run_test(
                f"Graceful Degradation Test {i+1} - Message: '{message[:30]}{'...' if len(message) > 30 else ''}'",
                "POST",
                "api/chat",
                200,  # Should always return 200, never 500
                data=chat_data
            )
            
            if not success:
                print(f"❌ AI Chat returned non-200 status for message: {message[:50]}")
                return False
            
            # Verify no 'Google Generative AI library not available' error
            response_text = response.get('response', '')
            if 'Google Generative AI library not available' in response_text:
                print(f"❌ Found 'Google Generative AI library not available' error in response")
                return False
            
            # Verify response schema is maintained
            required_fields = ['response', 'conversation_id', 'has_data', 'data_types']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field '{field}' in graceful degradation response")
                    return False
        
        print("✅ AI Chat degrades gracefully - no 500 errors, no 'Google Generative AI library not available' messages")
        return True

    def test_ai_chat_response_schema(self):
        """Test that AI chat response always includes required schema fields"""
        print("\n🔍 Testing AI Chat response schema consistency...")
        
        test_scenarios = [
            {"message": "Test message 1", "conversation_id": None},
            {"message": "Test message 2", "conversation_id": "existing_conv"},
            {"message": "What is the status?", "conversation_id": None},
            {"message": "Tell me about inventory", "conversation_id": "test_123"},
        ]
        
        for i, chat_data in enumerate(test_scenarios):
            success, response = self.run_test(
                f"Schema Test {i+1}",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if not success:
                return False
            
            # Verify all required schema fields are present
            required_fields = {
                'response': str,
                'conversation_id': str,
                'has_data': bool,
                'data_types': list
            }
            
            for field, expected_type in required_fields.items():
                if field not in response:
                    print(f"❌ Missing required field '{field}' in response")
                    return False
                
                if not isinstance(response[field], expected_type):
                    print(f"❌ Field '{field}' has wrong type. Expected {expected_type}, got {type(response[field])}")
                    return False
            
            # Verify conversation_id is generated if not provided
            if chat_data['conversation_id'] is None:
                if not response['conversation_id'] or len(response['conversation_id']) < 10:
                    print(f"❌ Conversation ID not properly generated: {response['conversation_id']}")
                    return False
            else:
                if response['conversation_id'] != chat_data['conversation_id']:
                    print(f"❌ Conversation ID not preserved: expected {chat_data['conversation_id']}, got {response['conversation_id']}")
                    return False
        
        print("✅ AI Chat response schema is consistent across all scenarios")
        return True

    def test_other_endpoints_still_work(self):
        """Test that other endpoints (/api/calculate, /api/depot-suggestions) still work after AI chat testing"""
        print("\n🔍 Testing other endpoints still work...")
        
        # Test /api/calculate endpoint
        calculation_data = {
            "days": 10
        }
        
        success, calc_response = self.run_test(
            "Calculate Endpoint Still Works",
            "POST",
            "api/calculate",
            200,
            data=calculation_data
        )
        
        if not success:
            print("❌ /api/calculate endpoint not working")
            return False
        
        # Verify calculation response structure
        if 'calculations' not in calc_response:
            print("❌ /api/calculate missing 'calculations' field")
            return False
        
        print("✅ /api/calculate endpoint working correctly")
        
        # Test /api/depot-suggestions endpoint
        depot_data = {
            "depot_name": "M212",
            "days": 10
        }
        
        success, depot_response = self.run_test(
            "Depot Suggestions Endpoint Still Works",
            "POST",
            "api/depot-suggestions",
            200,
            data=depot_data
        )
        
        if not success:
            print("❌ /api/depot-suggestions endpoint not working")
            return False
        
        # Verify depot suggestions response structure
        required_depot_fields = ['depot_name', 'current_palettes', 'target_palettes', 'suggestions']
        for field in required_depot_fields:
            if field not in depot_response:
                print(f"❌ /api/depot-suggestions missing '{field}' field")
                return False
        
        print("✅ /api/depot-suggestions endpoint working correctly")
        return True

    def test_ai_chat_conversation_persistence(self):
        """Test that conversation IDs are properly handled"""
        print("\n🔍 Testing AI Chat conversation persistence...")
        
        # Start a new conversation
        chat_data_1 = {
            "message": "Start new conversation",
            "conversation_id": None
        }
        
        success, response_1 = self.run_test(
            "Start New Conversation",
            "POST",
            "api/chat",
            200,
            data=chat_data_1
        )
        
        if not success:
            return False
        
        conversation_id = response_1['conversation_id']
        
        # Continue the conversation
        chat_data_2 = {
            "message": "Continue conversation",
            "conversation_id": conversation_id
        }
        
        success, response_2 = self.run_test(
            "Continue Existing Conversation",
            "POST",
            "api/chat",
            200,
            data=chat_data_2
        )
        
        if not success:
            return False
        
        # Verify conversation ID is maintained
        if response_2['conversation_id'] != conversation_id:
            print(f"❌ Conversation ID not maintained: expected {conversation_id}, got {response_2['conversation_id']}")
            return False
        
        print("✅ AI Chat conversation persistence working correctly")
        return True

    def test_ai_chat_with_various_data_combinations(self):
        """Test AI chat with different combinations of uploaded data"""
        print("\n🔍 Testing AI Chat with various data combinations...")
        
        # Test with only commandes data
        chat_data = {
            "message": "What data do we have?",
            "conversation_id": None
        }
        
        success, response = self.run_test(
            "AI Chat with Commandes Data Only",
            "POST",
            "api/chat",
            200,
            data=chat_data
        )
        
        if not success:
            return False
        
        # Should have commandes and stock data from previous tests
        if not response['has_data']:
            print("❌ Expected has_data=True with uploaded data")
            return False
        
        # Verify data types reflect what's available
        if 'commandes' not in response['data_types']:
            print(f"❌ Expected 'commandes' in data_types: {response['data_types']}")
            return False
        
        print("✅ AI Chat correctly identifies available data types")
        return True

    def run_all_tests(self):
        """Run all AI chat robustness tests"""
        print("🚀 Starting AI Chat Robustness Testing...")
        print("=" * 60)
        
        tests = [
            self.test_ai_chat_without_data,
            self.test_ai_chat_with_uploaded_data,
            self.test_ai_chat_graceful_degradation,
            self.test_ai_chat_response_schema,
            self.test_ai_chat_conversation_persistence,
            self.test_ai_chat_with_various_data_combinations,
            self.test_other_endpoints_still_work,
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
        print(f"🏁 AI Chat Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL AI CHAT ROBUSTNESS TESTS PASSED!")
            return True
        else:
            print("⚠️ Some AI chat tests failed")
            return False

if __name__ == "__main__":
    tester = AIChatRobustnessTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)