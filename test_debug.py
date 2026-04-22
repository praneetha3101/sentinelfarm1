import requests
import json

# Test debug
url = 'http://localhost:5001/debug/data-availability/19.8762/75.3433/2025-01-27/2025-02-26'
print('Testing debug endpoint for Aurangabad...')
r = requests.get(url, timeout=30)
print('Status:', r.status_code)
if r.status_code == 200:
    result = r.json()
    print(json.dumps(result, indent=2)[:800])
else:
    print('Error:', r.text[:300])
