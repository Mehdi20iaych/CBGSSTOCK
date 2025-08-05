import requests
import json

# Test the business logic more thoroughly
base_url = "https://e4d7cb4e-74c3-4168-8b71-3d543dbf6be5.preview.emergentagent.com"

# Use the session IDs from the previous test
order_session_id = "60821168-4ae9-45ca-8f67-c754118f0270"
inventory_session_id = "c5f22eef-c13e-4206-b8e4-7f41a9975f9a"
transit_session_id = "e9caeb60-53e0-4c97-b255-59c56d157dc5"

print("🔍 Detailed Business Logic Analysis")
print("=" * 50)

# Test enhanced calculation with all data
calculation_data = {
    "days": 30,
    "order_session_id": order_session_id,
    "inventory_session_id": inventory_session_id,
    "transit_session_id": transit_session_id,
    "product_filter": None,
    "packaging_filter": None
}

response = requests.post(f"{base_url}/api/enhanced-calculate", json=calculation_data)

if response.status_code == 200:
    data = response.json()
    calculations = data.get('calculations', [])
    
    print(f"Found {len(calculations)} calculations")
    print()
    
    for calc in calculations:
        article_code = calc.get('article_code')
        depot = calc.get('depot')
        current_stock = calc.get('current_stock', 0)
        inventory_available = calc.get('inventory_available', 0)
        transit_available = calc.get('transit_available', 0)
        total_available = calc.get('total_available', 0)
        required_stock = calc.get('required_for_x_days', 0)
        quantity_to_send = calc.get('quantity_to_send', 0)
        
        print(f"📋 Article: {article_code} in {depot}")
        print(f"   Current Stock: {current_stock}")
        print(f"   Inventory Available: {inventory_available}")
        print(f"   Transit Available: {transit_available}")
        print(f"   Total Available: {total_available}")
        print(f"   Required for 30 days: {required_stock}")
        print(f"   Quantity to Send: {quantity_to_send}")
        
        # Expected logic: Quantity to Send = max(0, Required - Total Available)
        expected_quantity_to_send = max(0, required_stock - total_available)
        print(f"   Expected Quantity to Send: {expected_quantity_to_send}")
        
        if abs(quantity_to_send - expected_quantity_to_send) > 0.01:
            print(f"   ❌ CALCULATION ERROR!")
        else:
            print(f"   ✅ Calculation correct")
        print()
else:
    print(f"❌ Request failed: {response.status_code}")
    print(response.text)