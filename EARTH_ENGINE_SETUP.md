# Earth Engine Setup Guide - Fix "ee is not getting loaded"

## Problem
When running `npm start` in backend, Earth Engine (ee) is not initialized.

## Root Cause
You have **2 separate backends**:
1. **server.js** (Node.js) - Runs on port 5000 with `npm start`
2. **app.py** (Python/Flask) - Needs to run separately

Earth Engine is a Python library, so it needs the Flask app running.

## Solution: Run Both Servers

### Terminal 1: Node.js Backend
```bash
cd backend
npm start
```
Expected: `🚀 Server running on http://localhost:5000`

### Terminal 2: Python Backend (in a NEW terminal)
```bash
cd backend
python app.py
# OR
python3 app.py
```
Expected: `✅ Earth Engine initialized`

---

## Setup Earth Engine Credentials (REQUIRED)

You need Google Cloud credentials to use Earth Engine. Here's how to set it up:

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (name: `SentinelFarm` or similar)
3. Note the Project ID (e.g., `my-project-123456`)

### Step 2: Create Service Account

1. Go to **Cloud IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
   - Name: `sentinelfarm-service`
   - Description: `Earth Engine service account`
3. Click **Create and Continue**
4. Grant roles:
   - Select **Editor** role
   - Click **Continue** → **Done**

### Step 3: Create Service Account Key

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON**
5. Save the file as `service-account-key.json` in the `backend/` folder

Your folder structure should look like:
```
backend/
├── server.js
├── app.py
├── package.json
├── service-account-key.json  ← Add this file!
└── ... other files
```

### Step 4: Register App as User

1. Go back to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **APIs & Services** → **Enabled APIs & Services**
3. Search for **"Earth Engine API"**
4. Click **Enable**
5. Go to **OAuth Consent Screen**
   - Choose **Internal** user type
   - Fill basic info → Save
6. Go to **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client ID**
   - Choose **Web application**
   - Add URIs:
     - `http://localhost:3000`
     - `http://localhost:5000`
   - Create
7. Download the credentials JSON and note your OAuth credentials

### Step 5: Verify Installation

Run this command to test:
```bash
python3 -c "import ee; print('✅ Earth Engine imported successfully')"
```

Expected output: `✅ Earth Engine imported successfully`

---

## Method 1: Using Service Account Key File (RECOMMENDED)

The app will automatically find and use `service-account-key.json` in the backend folder.

### To verify it's working:
```bash
cd backend
python3 app.py
```

Should show:
```
🔑 Service account key file found
📧 Service account email: sentinelfarm-service@my-project-123456.iam.gserviceaccount.com
📋 Project ID from key: my-project-123456
✅ Earth Engine initialized with service account for project: my-project-123456
```

---

## Method 2: Using Environment Variable

If you can't use a file, set an environment variable:

### On Windows (PowerShell):
```powershell
$env:GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "...", ...}'
python app.py
```

### On Windows (Command Prompt):
```cmd
set GOOGLE_SERVICE_ACCOUNT_KEY={"type": "service_account", "project_id": "...", ...}
python app.py
```

### On Mac/Linux:
```bash
export GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "...", ...}'
python3 app.py
```

---

## Troubleshooting

### Error: "No module named 'ee'"
**Solution:** Install Earth Engine
```bash
pip install earthengine-api
```

### Error: "service-account-key.json not found"
**Solution:** Either:
1. Download the key file and place it in the `backend/` folder
2. Use environment variable instead (Method 2 above)

### Error: "Invalid JSON in service account key"
**Solution:** Make sure the JSON file is valid:
```bash
python3 -m json.tool service-account-key.json
```

### Error: "Authentication failed"
**Solution:** Verify the JSON key file:
1. Has `"type": "service_account"`
2. Has `"client_email"` field
3. Has `"project_id"` field
4. File is not corrupted

### Error: "Earth Engine API not enabled"
**Solution:** Go to Google Cloud Console:
1. Search for "Earth Engine API"
2. Click it and press **Enable**

---

## Complete Startup Procedure

1. **Install Python dependencies** (one time):
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Terminal 1 - Node.js Backend**:
   ```bash
   cd backend
   npm start
   ```
   Expected: Server on port 5000

3. **Terminal 2 - Python Backend**:
   ```bash
   cd backend
   python app.py
   ```
   Expected: Earth Engine initialized

4. **Terminal 3 - React Frontend**:
   ```bash
   cd frontend
   npm start
   ```
   Expected: App on port 3000

5. Open browser: `http://localhost:3000`

---

## Verify Everything Works

### Check Node.js Backend:
```bash
curl http://localhost:5000/health
```
Should return: `{"status":"healthy",...}`

### Check Python Backend:
```bash
curl http://localhost:5000/health
```
Should return: 
```json
{
  "status": "healthy",
  "service": "AgriScope Flask Backend",
  "earth_engine_status": "initialized",
  "timestamp": "2026-03-02T..."
}
```

---

## Running in Degraded Mode (For Development)

If you don't have Google Cloud credentials yet:

1. **Only run Node.js backend**:
   ```bash
   npm start
   ```

2. **Use soil prediction without satellite data**:
   - Soil prediction ML models still work
   - NDVI/satellite features will show limited data
   - Crop recommendations will use fallback data

This is fine for initial development!

---

## Next Steps

1. ✅ Download and place `service-account-key.json` in backend/
2. ✅ Run Terminal 1: `npm start` (Node.js)
3. ✅ Run Terminal 2: `python app.py` (Python/Flask)
4. ✅ Run Terminal 3: `npm start` in frontend/
5. ✅ Open http://localhost:3000

Both servers will now be running and Earth Engine will be initialized! 🚀
