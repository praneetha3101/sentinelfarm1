import requests
import json

# Test with a different location - Mumbai area  
data = {
    'coordinates': [[72.8479, 19.0760], [72.8490, 19.0760], [72.8490, 19.0770], [72.8479, 19.0770]],
    'start_date': '2025-02-01',
    'end_date': '2025-02-25',
    'index': 'NDVI'
}

print('Testing with Mumbai coordinates...')
r = requests.post('http://localhost:5001/api/indices/calculate', json=data, timeout=30)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print('SUCCESS! Tile generated for Mumbai area')
else:
    print(f'Response: {r.text[:500]}')
