#!/usr/bin/env python3
"""
Test weather data fetching with 6-month parameters
"""
import requests
from datetime import datetime, timedelta
import json

# Test date range calculation (6 months back, excluding last 5 days)
end_date = datetime.now()
end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = end_date - timedelta(days=5)

start_date = end_date - timedelta(days=180)  # 6 months

print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
print(f"End date: {end_date.strftime('%Y-%m-%d')}")
print(f"Days difference: {(end_date - start_date).days}")

# Test coordinates (example field)
coordinates = [[78.0, 27.5], [78.1, 27.5], [78.1, 27.4], [78.0, 27.4]]  # Sample polygon

# Calculate center
centerLng = sum(coord[0] for coord in coordinates) / len(coordinates)
centerLat = sum(coord[1] for coord in coordinates) / len(coordinates)

print(f"\nField center: {centerLat}, {centerLng}")

# Test the API endpoint through Express backend
backend_url = 'http://localhost:3001/api/weather/data'

payload = {
    'coordinates': coordinates,
    'start_date': start_date.strftime('%Y-%m-%d'),
    'end_date': end_date.strftime('%Y-%m-%d')
}

print(f"\nSending request to {backend_url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(backend_url, json=payload, timeout=10)
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'parameter' in data:
            params = data['parameter']
            if 'T2M' in params:
                temps = params['T2M']
                avg_temp = sum(temps.values()) / len(temps)
                print(f"Average temperature: {avg_temp:.2f}°C")
                print(f"Temperature data points: {len(temps)}")
            if 'RH2M' in params:
                humidity = params['RH2M']
                avg_humidity = sum(humidity.values()) / len(humidity)
                print(f"Average humidity: {avg_humidity:.2f}%")
            if 'PRECTOTCORR' in params:
                rainfall = params['PRECTOTCORR']
                total_rainfall = sum(rainfall.values())
                print(f"Total rainfall: {total_rainfall:.2f}mm")
        else:
            print("Response:", json.dumps(data, indent=2)[:500])
    else:
        print(f"Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to backend at http://localhost:3001")
    print("Make sure the Express server is running!")
except Exception as e:
    print(f"ERROR: {e}")
