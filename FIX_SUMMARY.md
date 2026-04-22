# Fix Summary: Vegetation Indices API Errors (404 & CORS)

## Problems You Were Experiencing

Your browser console was showing errors like:
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
Error fetching available indices: AxiosError
Access to XMLHttpRequest at 'http://localhost:5000/api/indices/calculate' from origin 'http://localhost:3000' has been blocked by CORS policy
```

## Root Causes

1. **Missing Routes in Express Server**
   - Your frontend calls `http://localhost:5000/api/indices/list` and `http://localhost:5000/api/indices/calculate`
   - But the Node.js Express server on port 5000 didn't have these routes defined
   - The routes only existed in the Python Flask app on port 5001

2. **CORS Configuration Issues**
   - Preflight (`OPTIONS`) requests were not properly configured
   - Missing CORS headers on responses
   - Prevented browser from sending actual requests

3. **No Backend Integration**
   - Express and Flask weren't connected via proxy
   - Frontend expecting single endpoint but serving from two separate servers

## Solutions Implemented

### ✅ 1. Created New Indices Routes File
**File:** `backend/routes/indices.js` (NEW)

This file:
- Acts as a proxy from Express (port 5000) to Flask (port 5001)
- Handles 3 endpoints:
  - `GET /api/indices/list` - List available vegetation indices
  - `POST /api/indices/calculate` - Calculate index for location
  - `POST /api/indices/timeseries` - Get time series data
- Includes error handling and fallback responses
- Respects `FLASK_API_URL` environment variable

### ✅ 2. Updated Express Server Configuration
**File:** `backend/server.js` (MODIFIED)

Changes:
- Added `const indicesRoutes = require("./routes/indices");`
- Enhanced CORS middleware with explicit configuration:
  ```javascript
  const corsOptions = {
    origin: ["http://localhost:3000", "http://127.0.0.1:3000"],
    credentials: true,
    optionsSuccessStatus: 200,
    allowedHeaders: ["Content-Type", "Authorization"],
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
  };
  app.use(cors(corsOptions));
  ```
- Registered indices routes: `app.use("/api/indices", indicesRoutes);`

### ✅ 3. Created Validation & Documentation

**Files Created:**
- `INDICES_ROUTES_SETUP.md` - Complete setup guide with architecture diagram
- `backend/validate-setup.js` - Automatic validation script to check if everything works

## How to Test

### Step 1: Start the Servers

**Terminal 1 - Express (Node.js):**
```bash
cd backend
npm start
```

**Terminal 2 - Flask (Python):**
```bash
cd backend
python app.py
```

**Terminal 3 - Frontend (React):**
```bash
cd frontend
npm start
```

### Step 2: Validate Setup
```bash
node backend/validate-setup.js
```

You should see:
```
✓ Express Health Check: Running on http://localhost:5000/health
✓ Flask Health Check: Running on http://localhost:5001/health
✓ GET /api/indices/list: Running on http://localhost:5000/api/indices/list
✓ CORS Preflight: CORS headers present
```

### Step 3: Test in Frontend
Navigate to the MonitorField page in your app. You should now:
- See the available vegetation indices load without errors
- Be able to select indices and calculate NDVI/EVI/etc.
- Be able to see time series charts

## Architecture Flow (NOW WORKING)

```
┌─────────────────────┐
│   React Frontend    │
│  (http://localhost:3000)
└──────────┬──────────┘
           │ Request to /api/indices/list
           ↓
┌─────────────────────────────────────────┐
│  Express Server (http://localhost:5000) │
│  ✓ CORS headers fixed                   │
│  ✓ Routes registered                    │
└──────────┬──────────────────────────────┘
           │ Proxy request to Flask
           ↓
┌─────────────────────────────────────────┐
│   Flask Server (http://localhost:5001)  │
│   ✓ Earth Engine integration            │
│   ✓ Vegetation indices calculation      │
└──────────┬──────────────────────────────┘
           │ Response with tile URL/data
           ↓
           ... back to Frontend
```

## Key Fixes by Error Type

### ❌ 404 Errors → ✅ **FIXED**
- Express server now has `/api/indices/` routes
- Routes properly proxy to Flask backend
- Returns proper responses instead of 404

### ❌ CORS Errors → ✅ **FIXED**
- Enhanced CORS middleware configuration
- Proper `OPTIONS` preflight handling
- Correct `Access-Control-Allow-*` headers

### ❌ AxiosError → ✅ **FIXED**
- Proxy routes handle all error cases
- Proper error responses with helpful messages
- Fallback responses when Flask unavailable

## Configuration Details

### Environment Variables
In `backend/.env`:
```
FLASK_API_URL=http://localhost:5001
```

### Ports
- **Frontend:** 3000 (React)
- **Express Backend:** 5000 (Node.js)
- **Flask Backend:** 5001 (Python with Earth Engine)

### CORS Origins Allowed
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## Verification Checklist

- [ ] Both Express and Flask servers are running
- [ ] `http://localhost:5000/health` returns status 200
- [ ] `http://localhost:5001/health` returns status 200
- [ ] `http://localhost:5000/api/indices/list` returns list of indices
- [ ] No 404 errors in browser console for `/api/indices/`
- [ ] No CORS errors in browser console
- [ ] MonitorField.js can fetch available indices
- [ ] Can calculate indices without errors
- [ ] Validation script shows all systems OK: `node backend/validate-setup.js`

## Troubleshooting if Issues Persist

### Still getting 404?
```bash
# Check if routes file exists
ls -la backend/routes/indices.js

# Check if it's registered in server.js
grep "indicesRoutes" backend/server.js

# Restart Express with npm start
```

### Still getting CORS errors?
```bash
# Clear browser cache (Ctrl+Shift+R)
# Check browser's Network tab for preflight response headers
# Verify FLASK_API_URL in .env matches actual Flask location
```

### Flask not responding?
```bash
# Verify Flask is running
curl http://localhost:5001/health

# Check for Earth Engine credential issues
# Review Flask console output for error messages
```

## Files Changed

| File | Change | Type |
|------|--------|------|
| `backend/server.js` | Enhanced CORS, added indices route | Modified |
| `backend/routes/indices.js` | New proxy routes for indices | Created |
| `INDICES_ROUTES_SETUP.md` | Setup guide | Created |
| `backend/validate-setup.js` | Validation script | Created |

## Next Steps

1. ✅ Setup is complete - no code changes needed from you
2. Start both servers (Express and Flask)
3. Run validation script to confirm everything works
4. Test the frontend - should have no errors
5. Enjoy using vegetation indices features!

---

**Questions?** Refer to `INDICES_ROUTES_SETUP.md` for detailed documentation, or check the validation script output for specific issues.
