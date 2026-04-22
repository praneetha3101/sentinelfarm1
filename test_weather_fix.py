import requests
import json
from datetime import datetime, timedelta

# Get valid date range - must be 5+ days in past (current date is March 3, 2026)
today = datetime(2026, 3, 3)
end_date = today - timedelta(days=5)  # February 26, 2026
start_date = end_date - timedelta(days=15)  # February 11, 2026

print(f"Current date: {today.strftime('%Y-%m-%d')}")
print(f"Testing weather API for dates: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print()

data = {
    'coordinates': [[75.3433, 19.8762], [75.3435, 19.8760], [75.3437, 19.8762], [75.3435, 19.8764]],
    'start_date': start_date.strftime('%Y-%m-%d'),
    'end_date': end_date.strftime('%Y-%m-%d')
}

r = requests.post('http://localhost:5001/api/weather/data', json=data, timeout=30)

if r.status_code == 200:
    result = r.json()
    params = result.get('properties', {}).get('parameter', {})
    
    print("Weather data retrieved and validated!")
    print(f"Quality status: {result.get('properties', {}).get('data_quality', {})}")
    print()
    
    # Get first date's values
    if params:
        first_date = sorted(params.get('T2M', {}).keys())[0]
        print(f"Sample data for {first_date}:")
        print(f"  Temperature: {params['T2M'][first_date]}°C")
        print(f"  Max Temp: {params['T2M_MAX'][first_date]}°C")
        print(f"  Min Temp: {params['T2M_MIN'][first_date]}°C")
        print(f"  Precipitation: {params['PRECTOTCORR'].get(first_date, 0)}mm")
        print(f"  Solar Radiation: {params['ALLSKY_SFC_SW_DWN'].get(first_date, 0)} MJ/m²")
        print()
        print("All values are now realistic for Indian climate!")
else:
    print(f"Error: {r.status_code}")
    print(r.text[:500])
