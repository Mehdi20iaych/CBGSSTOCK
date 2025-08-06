#!/usr/bin/env python3

import pandas as pd
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8001"

def test_transit_matching():
    """Debug transit data matching to see why transit stock shows as 0"""
    
    print("🔍 DEBUGGING TRANSIT DATA MATCHING")
    print("=" * 50)
    
    try:
        # Get all uploaded data to see what's stored
        response = requests.get(f"{API_BASE_URL}/api/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print(f"📊 Found {len(sessions)} sessions")
            
            # Find most recent order and transit sessions
            order_session = None
            transit_session = None
            
            for session in sessions:
                if session.get('type') == 'order':
                    order_session = session
                elif session.get('type') == 'transit':
                    transit_session = session
            
            if order_session:
                print(f"📦 Order Session: {order_session['session_id']}")
                print(f"   Records: {order_session.get('records_count', 0)}")
                
                # Get order data sample
                order_response = requests.get(f"{API_BASE_URL}/api/data/{order_session['session_id']}")
                if order_response.status_code == 200:
                    order_data = order_response.json()
                    if order_data['data']:
                        sample = order_data['data'][0]
                        print(f"   Sample Article: '{sample.get('Article')}' (type: {type(sample.get('Article'))})")
                        print(f"   Sample Division: '{sample.get('Nom Division')}' (type: {type(sample.get('Nom Division'))})")
            
            if transit_session:
                print(f"🚛 Transit Session: {transit_session['session_id']}")
                print(f"   Records: {transit_session.get('records_count', 0)}")
                
                # Get transit data sample
                transit_response = requests.get(f"{API_BASE_URL}/api/transit-data/{transit_session['session_id']}")
                if transit_response.status_code == 200:
                    transit_data = transit_response.json()
                    if transit_data['data']:
                        sample = transit_data['data'][0]
                        print(f"   Sample Article: '{sample.get('Article')}' (type: {type(sample.get('Article'))})")
                        print(f"   Sample Division: '{sample.get('Division')}' (type: {type(sample.get('Division'))})")
                        print(f"   Sample Quantité: {sample.get('Quantité')} (type: {type(sample.get('Quantité'))})")
                        
                        # Show all transit data
                        print(f"\n🔍 ALL TRANSIT DATA:")
                        for i, record in enumerate(transit_data['data'][:10]):  # Show first 10
                            print(f"   {i+1}. Article: '{record.get('Article')}', Division: '{record.get('Division')}', Quantité: {record.get('Quantité')}")
                            
            # If we have both sessions, test a calculation
            if order_session and transit_session:
                print(f"\n🧮 TESTING CALCULATION WITH BOTH SESSIONS")
                calc_data = {
                    "days": 15,
                    "order_session_id": order_session['session_id'],
                    "inventory_session_id": None,
                    "transit_session_id": transit_session['session_id'],
                    "product_filter": None,
                    "packaging_filter": None
                }
                
                calc_response = requests.post(f"{API_BASE_URL}/api/enhanced-calculate", 
                                            headers={'Content-Type': 'application/json'},
                                            data=json.dumps(calc_data))
                
                if calc_response.status_code == 200:
                    results = calc_response.json()
                    print(f"✅ Calculation successful! {len(results['calculations'])} items processed")
                    
                    # Check transit values
                    transit_found = 0
                    for item in results['calculations'][:5]:  # Show first 5
                        transit_val = item.get('transit_available', 0)
                        if transit_val > 0:
                            transit_found += 1
                        print(f"   Article {item.get('article_code')}: current_stock={item.get('current_stock')}, transit_available={transit_val}, total_available={item.get('total_available', 0)}")
                    
                    print(f"📈 Items with transit stock > 0: {transit_found}/{len(results['calculations'])}")
                    
                else:
                    print(f"❌ Calculation failed: {calc_response.status_code}")
                    print(calc_response.text)
            else:
                print("❌ Missing order or transit session for calculation test")
                
        else:
            print(f"❌ Failed to get sessions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_transit_matching()