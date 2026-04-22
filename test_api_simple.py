import requests
import json

data = {
    'coordinates': [[75.3433, 19.8762], [75.3435, 19.8760], [75.3437, 19.8762], [75.3435, 19.8764]],
    'start_date': '2025-01-27',
    'end_date': '2025-02-26',
    'index': 'NDVI'
}

print('Testing /api/indices/calculate with Aurangabad coordinates...')
r = requests.post('http://localhost:5001/api/indices/calculate', json=data, timeout=30)
print('Status:', r.status_code)
if r.status_code == 200:
    result = r.json()
    print('SUCCESS! Data was retrieved! Full response:')
    print(json.dumps(result, indent=2)[:500])
else:
    print('ERROR - Status code:', r.status_code)
    print('Response:', r.text[:300])
