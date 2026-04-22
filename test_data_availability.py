#!/usr/bin/env python3
"""
Test Sentinel-2 data availability for various locations and date ranges
"""

import requests
import json
from datetime import datetime, timedelta

SERVER_URL = "http://127.0.0.1:5001"

# Test locations
TEST_LOCATIONS = {
    "Aurangabad (Your location)": {
        "lat": 19.8762,
        "lng": 75.3433
    },
    "Mumbai": {
        "lat": 19.0760,
        "lng": 72.8777
    },
    "Pune": {
        "lat": 18.5204,
        "lng": 73.8567
    },
    "Nashik": {
        "lat": 19.9975,
        "lng": 73.7898
    }
}

print("="*80)
print("  SENTINEL-2 DATA AVAILABILITY CHECKER")
print("="*80)

# Today's date
today = datetime.now()
end_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
start_date = (today - timedelta(days=35)).strftime('%Y-%m-%d')

print(f"\nTesting data availability for date range:")
print(f"  Start: {start_date}")
print(f"  End:   {end_date}")
print(f"\nNote: Sentinel-2 has ~5 day processing delay")
print(f"Today is {today.strftime('%Y-%m-%d')}, so data up to {end_date} should be available\n")

for location_name, coords in TEST_LOCATIONS.items():
    print(f"\n{'─'*80}")
    print(f"📍 Testing: {location_name}")
    print(f"   Lat: {coords['lat']}, Lng: {coords['lng']}")
    print(f"{'─'*80}")
    
    try:
        response = requests.get(
            f"{SERVER_URL}/debug/data-availability/{coords['lat']}/{coords['lng']}/{start_date}/{end_date}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            avail = data['availability']
            
            print(f"✅ Query successful!")
            print(f"   Total images found:        {avail['total_images']}")
            print(f"   Cloud-free (≤20% cloudy): {avail['cloud_free_20%']}")
            print(f"   Very clear (≤5% cloudy):  {avail['very_clear_5%']}")
            
            status = data['status']
            if status['has_cloud_free']:
                print(f"✅ Data available! You can use this location.")
            else:
                print(f"⚠️  No cloud-free data. Try:")
                print(f"    - Different date range")
                print(f"    - Different location")
                print(f"    - Wait for clearer weather")
        else:
            print(f"❌ Error: {response.status_code}")
            if response.text:
                print(f"   {response.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timeout - server is processing")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*80)
print("Testing complete! Use locations with has_cloud_free=true for best results.")
print("="*80)
