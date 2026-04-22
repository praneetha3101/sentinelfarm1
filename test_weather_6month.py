#!/usr/bin/env python3
"""
Test weather data fetching for 6-month period
Simulates what the frontend CropSuggestion page does
"""
import requests
import json
from datetime import datetime, timedelta

# Calculate dates exactly like the frontend does
end_date = datetime.now()
end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = end_date - timedelta(days=5)

start_date = datetime(end_date.year, end_date.month, end_date.day)  
start_date = start_date - timedelta(days=180)  # 6 months back

formatted_start = start_date.strftime('%Y-%m-%d')
formatted_end = end_date.strftime('%Y-%m-%d')

print("=" * 70)
print("WEATHER DATA 6-MONTH FETCH TEST")
print("=" * 70)
print(f"\nBackend: http://localhost:3001/api/weather/data")
print(f"Start Date: {formatted_start}")
print(f"End Date: {formatted_end}")
print(f"Duration: ~6 months")

# Sample Delhi region coordinates
coordinates = [[77.1, 28.5], [77.2, 28.5], [77.2, 28.6], [77.1, 28.6]]
print(f"Location: {coordinates}")

payload = {
    "coordinates": coordinates,
    "start_date": formatted_start,
    "end_date": formatted_end
}

print(f"\nPayload:")
print(json.dumps(payload, indent=2))

try:
    print("\n" + "-" * 70)
    print("Sending request...")
    response = requests.post("http://localhost:3001/api/weather/data", json=payload, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    data = response.json()
    
    if response.status_code == 200:
        # Check both possible locations for parameter data
        params = None
        if 'properties' in data and 'parameter' in data['properties']:
            params = data['properties']['parameter']
            print("Found data in properties.parameter")
        elif 'parameter' in data:
            params = data['parameter']
            print("Found data in parameter")
            
        if params:
            print("\n" + "-" * 70)
            print("WEATHER DATA RETRIEVED SUCCESSFULLY")
            print("-" * 70)
            
            # Temperature
            if 'T2M' in params:
                temps = dict(sorted(params['T2M'].items()))
                temp_list = list(temps.values())
                avg_temp = sum(temp_list) / len(temp_list)
                print(f"\nTemperature (T2M):")
                print(f"  Data points: {len(temp_list)}")
                print(f"  First 5 days: {list(temps.values())[:5]}")
                print(f"  Last 5 days: {list(temps.values())[-5:]}")
                print(f"  Average: {avg_temp:.2f}C")
                print(f"  Min: {min(temp_list):.2f}C")
                print(f"  Max: {max(temp_list):.2f}C")
            
            # Humidity
            if 'RH2M' in params:
                humidity = dict(sorted(params['RH2M'].items()))
                humidity_list = list(humidity.values())
                avg_humidity = sum(humidity_list) / len(humidity_list)
                print(f"\nHumidity (RH2M):")
                print(f"  Data points: {len(humidity_list)}")
                print(f"  First 5 days: {list(humidity.values())[:5]}")
                print(f"  Last 5 days: {list(humidity.values())[-5:]}")
                print(f"  Average: {avg_humidity:.2f}%")
                print(f"  Min: {min(humidity_list):.2f}%")
                print(f"  Max: {max(humidity_list):.2f}%")
            
            # Rainfall
            if 'PRECTOTCORR' in params:
                rainfall = dict(sorted(params['PRECTOTCORR'].items()))
                rainfall_list = list(rainfall.values())
                total_rainfall = sum(rainfall_list)
                avg_daily = total_rainfall / len(rainfall_list)
                print(f"\nRainfall (PRECTOTCORR):")
                print(f"  Data points: {len(rainfall_list)}")
                print(f"  First 5 days: {list(rainfall.values())[:5]}")
                print(f"  Last 5 days: {list(rainfall.values())[-5:]}")
                print(f"  Total: {total_rainfall:.2f}mm")
                print(f"  Daily average: {avg_daily:.2f}mm")
                print(f"  Max daily: {max(rainfall_list):.2f}mm")
            
            print("\n" + "=" * 70)
            print("SUCCESS: Weather API is working correctly!")
            print("The Crop Suggestion form should now display these values.")
            print("=" * 70)
        else:
            print(f"ERROR: No 'parameter' key found in response")
            print(f"Response keys: {list(data.keys())}")
            if 'properties' in data:
                print(f"Properties keys: {list(data['properties'].keys())}")
    else:
        print(f"ERROR: Status {response.status_code}")
        print(f"Response: {response.text[:500]}")

except requests.exceptions.ConnectionError:
    print("\nERROR: Could not connect to http://localhost:3001")
    print("Make sure Node.js backend (Express) is running!")
except requests.exceptions.Timeout:
    print("\nERROR: Request timed out - backend may be slow")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print()
