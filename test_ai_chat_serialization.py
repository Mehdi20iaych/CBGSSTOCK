#!/usr/bin/env python3

import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime

class AIChatSerializationTester:
    def __init__(self, base_url="https://shipment-planner-1.preview.emergentagent.com"):
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
                    print(f"Response preview: {str(response_data)[:200]}...")
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
            'Dummy_A': ['CMD001', 'CMD002', 'CMD003'],
            'Article': ['1011', '1016', '1021'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3'],
            'Point d\'Expédition': ['M211', 'M212', 'M213'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3'],
            'Quantité Commandée': [100, 150, 80],
            'Stock Utilisation Libre': [50, 75, 40],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3'],
            'Type Emballage': ['verre', 'pet', 'ciel']
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_stock_excel(self):
        """Create sample stock M210 Excel file"""
        data = {
            'Division': ['M210', 'M210', 'M210'],
            'Article': ['1011', '1016', '1021'],
            'Dummy_C': ['Desc1', 'Desc2', 'Desc3'],
            'STOCK A DATE': [500, 300, 200]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def create_sample_transit_excel(self):
        """Create sample transit Excel file"""
        data = {
            'Article': ['1011', '1016', '1021'],
            'Dummy_B': ['Desc1', 'Desc2', 'Desc3'],
            'Division': ['M211', 'M212', 'M213'],
            'Dummy_D': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_E': ['Extra1', 'Extra2', 'Extra3'],
            'Dummy_F': ['Extra1', 'Extra2', 'Extra3'],
            'Division cédante': ['M210', 'M210', 'M210'],
            'Dummy_H': ['Extra1', 'Extra2', 'Extra3'],
            'Quantité': [30, 20, 25]
        }
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        return excel_buffer

    def upload_sample_data(self):
        """Upload sample data to create datetime objects in the system"""
        print("\n📤 Uploading sample data to create datetime objects...")
        
        # Upload commandes
        excel_file = self.create_sample_commandes_excel()
        files = {
            'file': ('commandes.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Commandes (Creates datetime objects)",
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
        excel_file = self.create_sample_stock_excel()
        files = {
            'file': ('stock.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Stock (Creates datetime objects)",
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
        excel_file = self.create_sample_transit_excel()
        files = {
            'file': ('transit.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        success, response = self.run_test(
            "Upload Transit (Creates datetime objects)",
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

    def test_chat_json_serialization_fix(self):
        """Test that AI chat properly handles JSON serialization of datetime objects"""
        print("\n🔍 Testing AI Chat JSON Serialization Fix...")
        
        # Test questions that would trigger context building from uploaded data
        # These questions should cause the system to serialize datetime objects
        serialization_test_questions = [
            "Quand ont été uploadées mes données?",
            "Donne-moi un résumé détaillé de toutes mes données uploadées",
            "Analyse complète de ma situation avec toutes les données disponibles",
            "Montre-moi les informations sur mes sessions de données"
        ]
        
        for question in serialization_test_questions:
            chat_data = {
                "message": question
            }
            
            success, response = self.run_test(
                f"JSON Serialization Test: {question[:40]}...",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if success:
                # Verify response structure is properly JSON serialized
                required_fields = ['response', 'conversation_id', 'has_data', 'data_types', 'message']
                for field in required_fields:
                    if field not in response:
                        print(f"❌ Missing required field: {field} - JSON serialization may have failed")
                        return False
                
                # Verify has_data is True (indicating context was built from uploaded data)
                if response['has_data'] != True:
                    print(f"❌ Expected has_data=True when data uploaded, got {response['has_data']}")
                    return False
                
                # Verify data_types includes all expected types (indicating datetime objects were processed)
                expected_types = ['commandes', 'stock', 'transit']
                data_types = response['data_types']
                
                for expected_type in expected_types:
                    if expected_type not in data_types:
                        print(f"❌ Expected data type '{expected_type}' not found - context building may have failed due to serialization")
                        return False
                
                # Verify response is not empty (indicating AI processing worked)
                if not response['response'] or len(response['response']) < 50:
                    print("❌ Response too short - AI processing may have failed due to serialization issues")
                    return False
                
                # Verify conversation_id is properly generated (string format)
                if not isinstance(response['conversation_id'], str) or len(response['conversation_id']) < 10:
                    print("❌ Invalid conversation_id format - JSON serialization may have issues")
                    return False
                
                print(f"✅ JSON serialization working correctly for question: {question[:30]}...")
                print(f"   Response length: {len(response['response'])} characters")
                print(f"   Data types processed: {data_types}")
                
            else:
                print(f"❌ Failed to get response for serialization test question: {question}")
                return False
        
        return True

    def test_datetime_specific_serialization(self):
        """Test datetime-specific serialization scenarios"""
        print("\n🔍 Testing Datetime-Specific Serialization...")
        
        # Test that would specifically trigger datetime serialization
        datetime_specific_question = {
            "message": "Donne-moi les détails techniques de mes sessions de données avec les heures d'upload"
        }
        
        success, response = self.run_test(
            "Datetime Serialization Specific Test",
            "POST",
            "api/chat",
            200,
            data=datetime_specific_question
        )
        
        if success:
            # This should work without any "Object of type Timestamp is not JSON serializable" errors
            print("✅ Datetime-specific question processed successfully")
            print(f"   Context built with {len(response['data_types'])} data types")
            
            # Verify the response mentions data or time-related information
            response_text = response['response'].lower()
            time_indicators = ['données', 'session', 'upload', 'fichier', 'temps', 'heure']
            found_indicators = [indicator for indicator in time_indicators if indicator in response_text]
            
            if len(found_indicators) >= 2:
                print(f"✅ Response appropriately references time/data concepts: {found_indicators}")
            else:
                print(f"⚠️ Response may not fully address datetime question, but serialization worked")
            
            return True
        else:
            print("❌ Datetime-specific serialization test failed")
            return False

    def test_multiple_chat_requests(self):
        """Test multiple chat requests to ensure consistent serialization"""
        print("\n🔍 Testing Multiple Chat Requests for Serialization Consistency...")
        
        questions = [
            "Combien d'articles j'ai dans mes données?",
            "Quel est le statut de mes stocks?",
            "Analyse mes données de transit",
            "Résume ma situation globale",
            "Quelles sont mes sessions actives?"
        ]
        
        for i, question in enumerate(questions, 1):
            chat_data = {
                "message": question
            }
            
            success, response = self.run_test(
                f"Multiple Request Test {i}/5: {question[:30]}...",
                "POST",
                "api/chat",
                200,
                data=chat_data
            )
            
            if success:
                # Verify basic response structure
                if not all(field in response for field in ['response', 'conversation_id', 'has_data', 'data_types']):
                    print(f"❌ Request {i}: Missing required fields in response")
                    return False
                
                # Verify data context is maintained
                if response['has_data'] != True:
                    print(f"❌ Request {i}: Data context lost")
                    return False
                
                print(f"✅ Request {i}: Serialization working correctly")
            else:
                print(f"❌ Request {i}: Failed")
                return False
        
        print("✅ All multiple requests processed successfully - serialization is consistent")
        return True

    def run_all_tests(self):
        """Run all AI chat JSON serialization tests"""
        print("🚀 Starting AI Chat JSON Serialization Testing")
        print("=" * 70)
        print("Focus: Verify that 'Object of type Timestamp is not JSON serializable' error is fixed")
        print("=" * 70)
        
        # First upload sample data to create datetime objects
        if not self.upload_sample_data():
            print("❌ Failed to upload sample data - cannot test serialization")
            return False
        
        # Run serialization tests
        tests = [
            ("JSON Serialization Fix", self.test_chat_json_serialization_fix),
            ("Datetime Specific Serialization", self.test_datetime_specific_serialization),
            ("Multiple Chat Requests", self.test_multiple_chat_requests)
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
        
        # Print summary
        print("\n" + "="*70)
        print("📊 AI CHAT JSON SERIALIZATION TEST SUMMARY")
        print("="*70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL JSON SERIALIZATION TESTS PASSED!")
            print("✅ The 'Object of type Timestamp is not JSON serializable' error has been FIXED!")
            print("✅ AI chat functionality works correctly with datetime objects")
        else:
            print("⚠️ Some serialization tests failed. The JSON serialization fix may need attention.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AIChatSerializationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)