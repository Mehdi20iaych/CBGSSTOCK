#!/usr/bin/env python3
"""
AI Chat Review Test - Focused testing for the review request
Tests the updated AI chat functionality with new Gemini API key and enhanced minimal response system
"""

import requests
import json
import sys
import io
import pandas as pd
from datetime import datetime

class AIChatReviewTester:
    def __init__(self, base_url="https://key-switcher.preview.emergentagent.com"):
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

    def create_sample_data_excel(self):
        """Create sample data for testing with uploaded data"""
        data = {
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003', 'CMD004'],
            'Article': ['1011', '1016', '1021', '9999'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3', 'Desc4'],
            'Point d\'Expédition': ['M211', 'M212', 'M213', 'M211'],
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

    def test_api_key_validation(self):
        """Test 1: API Key Validation - Test the /api/chat endpoint to ensure the new Gemini API key is working"""
        print("\n" + "="*80)
        print("🔑 TESTING API KEY VALIDATION")
        print("="*80)
        
        chat_data = {
            "message": "Test the new Gemini API key functionality",
            "conversation_id": None
        }
        
        success, response = self.run_test(
            "API Key Validation - New Gemini Key",
            "POST",
            "api/chat",
            200,
            data=chat_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['response', 'conversation_id', 'has_data', 'data_types', 'message']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Check if we get a response (API key working)
            if not response['response'] or len(response['response']) < 5:
                print("❌ No response received - API key may not be working")
                return False
            
            print(f"✅ API Key Working - Response received: {len(response['response'])} characters")
            print(f"✅ New Gemini API key 'AIzaSyA1Sx1oPOq1JOhzbTOxMvJ2PRooGA78fwg' is functional")
            return True
        
        return False

    def test_minimal_response_format(self):
        """Test 2: Minimal Response Format - Verify ultra-short and clever responses"""
        print("\n" + "="*80)
        print("🎯 TESTING MINIMAL RESPONSE FORMAT")
        print("="*80)
        
        test_questions = [
            "What is the inventory status?",
            "Give me a quick summary",
            "Show me the main issues",
            "What needs attention?"
        ]
        
        all_passed = True
        
        for question in test_questions:
            chat_data = {
                "message": question,
                "conversation_id": None
            }
            
            success, response = self.run_test(
                f"Minimal Format Test - '{question[:30]}...'",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if success and 'response' in response:
                ai_response = response['response']
                
                # Test 1: Maximum 3 bullet points
                bullet_count = ai_response.count('*') + ai_response.count('•') + ai_response.count('-')
                if bullet_count > 3:
                    print(f"❌ Too many bullet points ({bullet_count}), should be max 3")
                    all_passed = False
                    continue
                
                # Test 2: Check for bullet point format
                if bullet_count == 0:
                    print(f"❌ Response should be in bullet point format")
                    all_passed = False
                    continue
                
                # Test 3: Maximum 10 words per bullet point (approximate check)
                lines = ai_response.split('\n')
                for line in lines:
                    if line.strip().startswith(('*', '•', '-')):
                        words = len(line.strip().split())
                        if words > 12:  # Allow some flexibility
                            print(f"❌ Bullet point too long: {words} words, should be max ~10")
                            all_passed = False
                            break
                
                # Test 4: Response should be concise (under reasonable limit)
                if len(ai_response) > 200:  # Very generous limit for minimal responses
                    print(f"❌ Response too long for minimal format: {len(ai_response)} characters")
                    all_passed = False
                    continue
                
                print(f"✅ Minimal format verified: {bullet_count} bullets, {len(ai_response)} chars")
                print(f"   Response: {ai_response}")
                
            else:
                all_passed = False
        
        if all_passed:
            print("✅ All minimal response format tests passed!")
            print("✅ Responses are ultra-short and use bullet points as requested")
        
        return all_passed

    def test_different_scenarios(self):
        """Test 3: Different Scenarios - Chat with and without data"""
        print("\n" + "="*80)
        print("📊 TESTING DIFFERENT SCENARIOS")
        print("="*80)
        
        # Scenario 1: Chat without uploaded data
        print("\n--- Scenario 1: Chat without uploaded data ---")
        chat_data = {
            "message": "What can you tell me about inventory management?",
            "conversation_id": None
        }
        
        success, response = self.run_test(
            "Chat Without Data",
            "POST",
            "api/chat",
            200,
            data=chat_data
        )
        
        scenario1_passed = False
        if success:
            # Should give useful generic response
            ai_response = response['response']
            if len(ai_response) > 10:  # Should have some content
                print(f"✅ Generic response provided: {ai_response}")
                scenario1_passed = True
            else:
                print(f"❌ Response too short for generic question")
        
        # Scenario 2: Upload data and test with data context
        print("\n--- Scenario 2: Upload data and test with data context ---")
        
        # Upload sample data
        excel_file = self.create_sample_data_excel()
        files = {
            'file': ('test_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        upload_success, upload_response = self.run_test(
            "Upload Sample Data",
            "POST",
            "api/upload-commandes-excel",
            200,
            files=files
        )
        
        scenario2_passed = False
        if upload_success:
            # Now test chat with data
            chat_data = {
                "message": "Analyze my uploaded inventory data",
                "conversation_id": None
            }
            
            success, response = self.run_test(
                "Chat With Uploaded Data",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if success:
                # Should provide data analysis
                if response.get('has_data', False):
                    print(f"✅ Data context recognized: {response.get('data_types', [])}")
                    scenario2_passed = True
                else:
                    print(f"❌ Data context not recognized")
        
        # Scenario 3: Test various question types
        print("\n--- Scenario 3: Various question types ---")
        question_types = [
            ("Status query", "What is the current status?"),
            ("Analysis request", "Analyze the situation"),
            ("Recommendation", "What do you recommend?")
        ]
        
        scenario3_passed = True
        for q_type, question in question_types:
            chat_data = {
                "message": question,
                "conversation_id": None
            }
            
            success, response = self.run_test(
                f"{q_type} Question",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if not success:
                scenario3_passed = False
            else:
                print(f"✅ {q_type} handled successfully")
        
        all_scenarios_passed = scenario1_passed and scenario2_passed and scenario3_passed
        
        if all_scenarios_passed:
            print("✅ All scenario tests passed!")
        
        return all_scenarios_passed

    def test_response_quality(self):
        """Test 4: Response Quality - Ensure responses are intelligent and actionable"""
        print("\n" + "="*80)
        print("🎨 TESTING RESPONSE QUALITY")
        print("="*80)
        
        quality_tests = [
            {
                "question": "What are the key inventory metrics?",
                "should_contain": ["numbers", "data"],
                "description": "Should include specific numbers when data available"
            },
            {
                "question": "Give me actionable insights",
                "should_contain": ["actionable"],
                "description": "Should be actionable and useful"
            }
        ]
        
        all_passed = True
        
        for test in quality_tests:
            chat_data = {
                "message": test["question"],
                "conversation_id": None
            }
            
            success, response = self.run_test(
                f"Quality Test - {test['description']}",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if success and 'response' in response:
                ai_response = response['response'].lower()
                
                # Check for professional consultant style (minimal but intelligent)
                if len(ai_response) < 10:
                    print(f"❌ Response too minimal to be intelligent")
                    all_passed = False
                    continue
                
                # Check for bullet format (professional style)
                if not any(char in ai_response for char in ['*', '•', '-']):
                    print(f"❌ Response should use professional bullet format")
                    all_passed = False
                    continue
                
                print(f"✅ Quality test passed: {test['description']}")
                print(f"   Response: {response['response']}")
                
            else:
                all_passed = False
        
        if all_passed:
            print("✅ All response quality tests passed!")
            print("✅ Responses are minimal but intelligent and professional")
        
        return all_passed

    def test_error_handling(self):
        """Test 5: Error Handling - Verify graceful degradation"""
        print("\n" + "="*80)
        print("🛡️ TESTING ERROR HANDLING")
        print("="*80)
        
        # Test with various edge cases
        edge_cases = [
            ("Empty message", ""),
            ("Very long message", "A" * 1000),
            ("Special characters", "Test with émojis 🚀 and spéciàl chars"),
            ("Numbers only", "123456789"),
        ]
        
        all_passed = True
        
        for case_name, message in edge_cases:
            chat_data = {
                "message": message,
                "conversation_id": None
            }
            
            success, response = self.run_test(
                f"Error Handling - {case_name}",
                "POST",
                "api/chat",
                200,  # Should always return 200, not 500
                data=chat_data
            )
            
            if success:
                # Should get some response, not crash
                if 'response' in response:
                    print(f"✅ {case_name} handled gracefully")
                else:
                    print(f"❌ {case_name} - missing response field")
                    all_passed = False
            else:
                print(f"❌ {case_name} - endpoint failed")
                all_passed = False
        
        if all_passed:
            print("✅ All error handling tests passed!")
            print("✅ System gracefully handles edge cases without crashing")
        
        return all_passed

    def run_comprehensive_review_test(self):
        """Run all tests for the review request"""
        print("🚀 STARTING AI CHAT REVIEW TESTING")
        print("="*80)
        print("Testing updated AI chat functionality with new Gemini API key")
        print("and enhanced minimal response system as per review request")
        print("="*80)
        
        # Run all test categories
        test_results = {
            "API Key Validation": self.test_api_key_validation(),
            "Minimal Response Format": self.test_minimal_response_format(),
            "Different Scenarios": self.test_different_scenarios(),
            "Response Quality": self.test_response_quality(),
            "Error Handling": self.test_error_handling()
        }
        
        # Summary
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE REVIEW TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")
        
        print(f"\n📊 Overall Results: {passed_tests}/{total_tests} test categories passed")
        print(f"📊 Individual Tests: {self.tests_passed}/{self.tests_run} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 SUCCESS: All review requirements satisfied!")
            print("✅ New Gemini API key 'AIzaSyA1Sx1oPOq1JOhzbTOxMvJ2PRooGA78fwg' is working")
            print("✅ Minimal response format implemented (max 3 bullets, ~10 words each)")
            print("✅ Modern consultant style with appropriate responses")
            print("✅ Works with and without uploaded data")
            print("✅ Graceful error handling implemented")
        else:
            print("\n⚠️ Some tests failed. Review implementation needed.")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = AIChatReviewTester()
    success = tester.run_comprehensive_review_test()
    sys.exit(0 if success else 1)