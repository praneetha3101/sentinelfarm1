"""
Test the /api/crop-recommendations endpoint directly
"""

import requests
import json

print("\n" + "="*70)
print("Testing /api/crop-recommendations Endpoint")
print("="*70 + "\n")

API_URL = "http://localhost:5001/api/crop-recommendations"

test_payload = {
    "field_data": {
        "location": "Delhi, India",
        "area": 2.5,
        "fertility_level": "Medium",
        "nitrogen": 75.0,
        "phosphorus": 28.0,
        "potassium": 51.0,
        "soil_ph": 6.8,
        "temperature": 24.5,
        "humidity": 65.0,
        "rainfall": 120.0
    },
    "coordinates": [[77.1, 28.6], [77.2, 28.6], [77.2, 28.7], [77.1, 28.7]]
}

print("[1] Sending request to /api/crop-recommendations...")
print(f"    URL: {API_URL}")
print(f"    Payload: {json.dumps(test_payload, indent=2)[:200]}...\n")

try:
    response = requests.post(API_URL, json=test_payload, timeout=30)
    
    print(f"[2] Response Status: {response.status_code}")
    print(f"    Headers: {dict(response.headers)}\n")
    
    data = response.json()
    
    print(f"[3] Response Structure:")
    print(f"    Root keys: {list(data.keys())}")
    print(f"    Status: {data.get('status')}")
    print(f"    AI Generated: {data.get('ai_generated')}")
    
    if 'recommendations' in data:
        recs = data['recommendations']
        print(f"\n[4] Recommendations Structure:")
        print(f"    Keys: {list(recs.keys())}")
        print(f"    Recommended crops count: {len(recs.get('recommended_crops', []))}")
        
        if recs.get('recommended_crops'):
            print(f"\n[5] Top 3 Crops:")
            for crop in recs['recommended_crops']:
                print(f"    - {crop.get('name')}: {crop.get('confidence')}% confidence")
                print(f"      Why suitable: {crop.get('why_suitable', 'N/A')[:80]}...")
    else:
        print("\n❌ ERROR: 'recommendations' key not found in response!")
        print(f"    Full response: {json.dumps(data, indent=2)[:500]}")
    
    print(f"\n[6] Full Response Size: {len(json.dumps(data))} bytes")
    print(f"    Can be JSON serialized: ✅ Yes")
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: {e}")
    print("   Make sure the Flask backend is running on localhost:5001")
except requests.exceptions.Timeout as e:
    print(f"❌ Timeout Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
