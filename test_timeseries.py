import requests
import json

data = {
    'coordinates': [[75.3433, 19.8762], [75.3435, 19.8760], [75.3437, 19.8762], [75.3435, 19.8764]],
    'start_date': '2025-01-27',
    'end_date': '2025-02-26',
    'index': 'NDVI'
}

print('Testing /api/indices/timeseries endpoint...')
r = requests.post('http://localhost:5001/api/indices/timeseries', json=data, timeout=30)
print('Status:', r.status_code)
print('Full response:')
print(json.dumps(r.json(), indent=2)[:1500])
