import ee
import json

print("Step 1: Starting script")

with open("service-account-key.json") as f:
    key = json.load(f)

print("Step 2: Key loaded")

project_id = key["project_id"]
service_account = key["client_email"]

print("Project ID:", project_id)
print("Service Account:", service_account)

credentials = ee.ServiceAccountCredentials(
    service_account,
    "service-account-key.json"
)

print("Step 3: Credentials created")

ee.Initialize(credentials, project=project_id)

print("SUCCESS ✅ Earth Engine initialized")