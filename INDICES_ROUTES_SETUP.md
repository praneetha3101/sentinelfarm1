# API Indices Routes - Setup Guide

## Problem Fixed

Your frontend was getting `404` and `CORS` errors when trying to access vegetation indices endpoints because:

1. **Missing Routes**: The Node.js Express server (port 5000) didn't have the `/api/indices/` endpoints
2. **CORS Issues**: Preflight requests were failing due to missing CORS headers
3. **Backend Separation**: The actual indices logic is in the Python Flask app (port 5001), but Express wasn't proxying to it

## Solution

### 1. **Express Routes Created** ✅
Created new file: `backend/routes/indices.js`
- Proxies all indices requests to the Flask backend
- Handles 3 endpoints:
  - `GET /api/indices/list` - List available vegetation indices
  - `POST /api/indices/calculate` - Calculate index for coordinates
  - `POST /api/indices/timeseries` - Get time series data

### 2. **CORS Configuration Fixed** ✅
Updated `backend/server.js`:
- Enhanced CORS middleware with proper preflight handling (`OPTIONS` requests)
- Configured allowed methods, headers, and origins
- Fixed `Access-Control-Allow` headers

### 3. **Architecture Overview**

```
Frontend (React on port 3000)
         ↓
Express Server (port 5000) - handles routing
         ↓
Flask Server (port 5001) - handles Earth Engine indices
```

**Requests flow:**
```
Frontend request to http://localhost:5000/api/indices/calculate
         ↓
Express server receives request
         ↓
Express proxies request to http://localhost:5001/api/indices/calculate (Flask)
         ↓
Flask processes with Earth Engine
         ↓
Response sent back to frontend
```

## How to Run

### Terminal 1: Start Node.js Express Server (port 5000)
```bash
cd backend
npm start
# or for development with hot reload:
npm run dev
```

### Terminal 2: Start Python Flask Server (port 5001)
```bash
cd backend
python app.py
# or with venv:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Terminal 3: Start React Frontend (port 3000)
```bash
cd frontend
npm start
```

## Configuration

The Flask backend URL can be configured via environment variables:

**In `backend/.env`:**
```
FLASK_API_URL=http://localhost:5001
```

If Flask runs on a different host/port, update this variable.

## API Endpoints

Now these endpoints work correctly from the frontend:

### 1. **GET /api/indices/list**
Lists all available vegetation indices.

**Response:**
```json
{
  "status": "success",
  "indices": [
    {
      "name": "NDVI",
      "description": "Normalized Difference Vegetation Index",
      "formula": "(NIR - R) / (NIR + R)"
    },
    // ... other indices
  ]
}
```

### 2. **POST /api/indices/calculate**
Calculate vegetation index for a location and date range.

**Request:**
```json
{
  "coordinates": [[longitude, latitude], ...],
  "start_date": "2026-02-01",
  "end_date": "2026-03-01",
  "index_name": "NDVI"
}
```

**Response:**
```json
{
  "status": "success",
  "index_name": "NDVI",
  "tile_url": "https://earthengine.googleapis.com/...",
  "visualization_params": { ... }
}
```

### 3. **POST /api/indices/timeseries**
Get time series data for an index over multiple observations.

**Request:**
```json
{
  "coordinates": [[longitude, latitude], ...],
  "start_date": "2026-02-01",
  "end_date": "2026-03-01",
  "index_name": "NDVI"
}
```

**Response:**
```json
{
  "status": "success",
  "index_name": "NDVI",
  "time_series": [
    {
      "date": "2026-02-15",
      "value": 0.65
    },
    // ... more data points
  ],
  "total_measurements": 4
}
```

## Troubleshooting

### ❌ Still getting 404 errors?
1. **Check Flask is running**: Visit `http://localhost:5001` in browser - should see a health check response
2. **Check Express is running**: Visit `http://localhost:5000/health` - should respond
3. **Check FLASK_API_URL env variable** is set correctly in `backend/.env`

### ❌ CORS errors still appearing?
1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check browsers console**: Should no longer show CORS blocking errors
3. **Verify both CORS headers are set**: Check Network tab in Dev Tools

### ❌ Flask connection refused?
1. Ensure Flask app is running (check Terminal 2)
2. Verify Earth Engine credentials are set up in Flask
3. Check firewall isn't blocking port 5001

### ✅ How to verify it's working?
Use curl or Postman to test:

```bash
# Test Express is running
curl http://localhost:5000/api/indices/list

# Should either get the indices list or proxy to Flask backend
```

## Files Modified

- ✅ `backend/server.js` - Added indices routes and fixed CORS
- ✅ `backend/routes/indices.js` - New proxy routes (created)

## Next Steps

1. Start both servers (Express & Flask)
2. Test the endpoints from the browser
3. All `/api/indices/*` endpoints should now work
4. Frontend MonitorField component should successfully fetch available indices and calculate vegetation indices

---

**Questions?** Check the console output for detailed error messages and logs.
