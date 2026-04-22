#!/usr/bin/env python3
"""
Test crop recommendations end-to-end
Tests: Field data submission and recommendations retrieval
"""
import requests
import json
from datetime import datetime, timedelta
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test dates (6 months back, excluding last 5 days)
end_date = datetime.now()
end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = end_date - timedelta(days=5)
start_date = end_date - timedelta(days=180)

# Sample field data
field_data = {
    "location": "28.6139°N, 77.2090°E",  # Delhi
    "area": 2.5,
    "fertility_level": "medium",
    "soil_ph": 6.8,
    "nitrogen": 75.0,
    "phosphorus": 28.0,
    "potassium": 51.0,
    "temperature": 24.5,
    "humidity": 65.0,
    "rainfall": 120.0
}

# Sample coordinates (Delhi region)
coordinates = [[77.1, 28.5], [77.2, 28.5], [77.2, 28.6], [77.1, 28.6]]

payload = {
    "field_data": field_data,
    "coordinates": coordinates
}

api_url = "http://localhost:5001/api/crop-recommendations"

print("=" * 70)
print("CROP RECOMMENDATIONS API TEST")
print("=" * 70)
print(f"\nAPI URL: {api_url}")
print(f"\nPayload:")
print(json.dumps(payload, indent=2))

try:
    print("\n\nSending request...")
    response = requests.post(api_url, json=payload, timeout=30)
    print(f"Response Status Code: {response.status_code}")
    
    data = response.json()
    print(f"\nResponse Status: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    
    # Check for recommendations
    if 'recommendations' in data:
        recs = data['recommendations']
        print(f"\n[OK] Recommendations received!")
        
        # Check for key sections
        keys_to_check = ['land_analysis', 'season_analysis', 'market_insights', 'recommended_crops', 'action_plan', 'sustainability_advice']
        for key in keys_to_check:
            if key in recs:
                print(f"  [YES] {key}")
            else:
                print(f"  [NO] {key} - MISSING")
        
        # Check recommended crops
        if 'recommended_crops' in recs and isinstance(recs['recommended_crops'], list):
            crops = recs['recommended_crops']
            print(f"\nRecommended Crops: {len(crops)}")
            for i, crop in enumerate(crops, 1):
                print(f"\n  Crop {i}: {crop.get('name', 'Unknown')}")
                print(f"    - Variety: {crop.get('variety', 'N/A')}")
                why = crop.get('why_suitable', 'N/A')
                print(f"    - Why Suitable: {why[:100] if len(why) > 100 else why}...")
                market = crop.get('market_potential', 'N/A')
                print(f"    - Market Potential: {market[:100] if len(market) > 100 else market}...")
        else:
            print("[ERROR] recommended_crops is not a list or missing!")
    else:
        print("[ERROR] No recommendations found in response!")
        print(f"\nResponse keys: {list(data.keys())}")
    
    # Print full response for debugging
    print("\n\n" + "=" * 70)
    print("FULL RESPONSE (first 2000 chars):")
    print("=" * 70)
    full_json = json.dumps(data, indent=2)
    print(full_json[:2000] + "..." if len(full_json) > 2000 else full_json)
    
except requests.exceptions.ConnectionError:
    print("[ERROR] CONNECTION ERROR")
    print("Could not connect to Flask API at http://localhost:5001")
    print("Make sure:")
    print("  1. Python/Flask backend is running")
    print("  2. Port 5001 is accessible")
    print("  3. GEMINI_API_KEY is configured")
    
except requests.exceptions.Timeout:
    print("[ERROR] REQUEST TIMEOUT")
    print("The API took too long to respond. Check if the backend is overloaded.")
    
except json.JSONDecodeError:
    print("[ERROR] INVALID JSON RESPONSE")
    print(f"Response text: {response.text[:500]}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)


print("\n" + "=" * 70)
