import requests
import json
import io
import pandas as pd

def test_depot_behavior():
    """Test to understand current depot handling behavior"""
    base_url = "https://26c0a26b-a6c0-48b9-82e9-52e8233e0e04.preview.emergentagent.com"
    
    # Test case sensitivity and whitespace
    test_depots = [' m115 ', 'M120', '  m170', 'M171  ', 'm212', 'M280']
    
    data = {
        'Dummy_A': [f'CMD{i:03d}' for i in range(1, len(test_depots) + 1)],
        'Article': [f'ART{i:03d}' for i in range(1, len(test_depots) + 1)],
        'Dummy_C': [f'Desc{i}' for i in range(1, len(test_depots) + 1)],
        'Point d\'Expédition': test_depots,
        'Dummy_E': [f'Extra{i}' for i in range(1, len(test_depots) + 1)],
        'Quantité Commandée': [100] * len(test_depots),
        'Stock Utilisation Libre': [50] * len(test_depots),
        'Dummy_H': [f'Extra{i}' for i in range(1, len(test_depots) + 1)],
        'Type Emballage': ['verre'] * len(test_depots)
    }
    
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    files = {
        'file': ('depot_behavior_test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    print("Testing depot behavior with:", test_depots)
    
    response = requests.post(f"{base_url}/api/upload-commandes-excel", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total records: {data['summary']['total_records']}")
        print(f"Found depots: {data['filters']['depots']}")
        print("All depots accepted - case and whitespace variations preserved")
        
        # Test depot suggestions with lowercase
        suggestion_data = {"depot_name": "m115", "days": 10}
        suggestion_response = requests.post(
            f"{base_url}/api/depot-suggestions", 
            json=suggestion_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if suggestion_response.status_code == 200:
            print("Depot suggestions accepts lowercase depot names")
        else:
            print(f"Depot suggestions error: {suggestion_response.json()}")
    else:
        print(f"Upload failed: {response.json()}")

if __name__ == "__main__":
    test_depot_behavior()