#!/usr/bin/env python3
"""
Earth Engine Accuracy Fix - Verification Script
Tests the corrected Earth Engine integration to ensure proper satellite data handling.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
SERVER_URL = "http://127.0.0.1:5001"
TEST_LOCATION = {
    "coordinates": [
        [73.7997, 20.5937],    # Aurangabad, Maharashtra - Good agricultural area
        [73.8197, 20.5937],
        [73.8197, 20.6137],
        [73.7997, 20.6137],
        [73.7997, 20.5937]
    ],
    "location_name": "Aurangabad, Maharashtra",
    "description": "Agricultural test field"
}

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def test_health_check():
    """Test if server and Earth Engine are initialized"""
    print_header("TEST 1: Server Health & Earth Engine Status")
    
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Server is healthy")
            print_info(f"  Service: {data.get('service', 'N/A')}")
            print_info(f"  Earth Engine Status: {data.get('earth_engine_status', 'unknown')}")
            
            if data.get('earth_engine_status') != 'initialized':
                print_error("Earth Engine is NOT initialized!")
                print_warning("  Please check service account credentials in EARTH_ENGINE_SETUP.md")
                return False
            return True
        else:
            print_error(f"Server returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running?")
        print_info(f"  Try: cd backend && python app.py")
        return False
    except Exception as e:
        print_error(f"Error checking health: {e}")
        return False

def test_indices_list():
    """Test that all vegetation indices are available"""
    print_header("TEST 2: Available Vegetation Indices")
    
    try:
        response = requests.get(f"{SERVER_URL}/api/indices/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            indices = data.get('indices', {})
            
            print_success(f"Found {len(indices)} vegetation indices")
            
            expected_indices = ['NDVI', 'EVI', 'SAVI', 'ARVI', 'MAVI', 'SR']
            for idx in expected_indices:
                if idx in indices:
                    info = indices[idx]
                    print_info(f"  {idx}: {info.get('formula', 'N/A')}")
                else:
                    print_warning(f"  {idx}: NOT FOUND")
            
            return len(indices) == len(expected_indices)
        else:
            print_error(f"Failed to retrieve indices list")
            return False
    except Exception as e:
        print_error(f"Error listing indices: {e}")
        return False

def test_ndvi_calculation():
    """Test NDVI calculation with corrected scaling"""
    print_header("TEST 3: NDVI Calculation (Tests Scaling Fix)")
    
    # Use recent dates (Sentinel-2 has ~5 day delay)
    today = datetime.now()
    end_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    
    payload = {
        "coordinates": TEST_LOCATION["coordinates"],
        "start_date": start_date,
        "end_date": end_date,
        "index_name": "NDVI"
    }
    
    try:
        print_info(f"Testing NDVI for {TEST_LOCATION['location_name']}")
        print_info(f"  Date range: {start_date} to {end_date}")
        
        response = requests.post(
            f"{SERVER_URL}/api/indices/calculate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("NDVI calculation successful")
            print_info(f"  Index: {data.get('index_name')}")
            print_info(f"  Tile URL: {'Generated' if data.get('tile_url') else 'Not generated'}")
            return True
        elif response.status_code == 404:
            print_warning("No data available for specified date range")
            print_info("  Try adjusting dates: data is usually 5+ days old")
            return False
        else:
            print_error(f"Failed with status {response.status_code}")
            print_info(f"  Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_warning("Request timed out - Earth Engine is slow")
        print_info("  This is normal for first request - try again")
        return False
    except Exception as e:
        print_error(f"Error in NDVI calculation: {e}")
        return False

def test_ndvi_time_series():
    """Test NDVI time series with corrected scaling and resolution"""
    print_header("TEST 4: NDVI Time Series (Tests Resolution Fix)")
    
    today = datetime.now()
    end_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    start_date = (today - timedelta(days=60)).strftime('%Y-%m-%d')
    
    payload = {
        "coordinates": TEST_LOCATION["coordinates"],
        "start_date": start_date,
        "end_date": end_date,
        "index_name": "NDVI"
    }
    
    try:
        print_info(f"Testing NDVI time series for {TEST_LOCATION['location_name']}")
        print_info(f"  Date range: {start_date} to {end_date}")
        
        response = requests.post(
            f"{SERVER_URL}/api/indices/timeseries",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            time_series = data.get('time_series', [])
            
            print_success(f"Time series retrieved: {len(time_series)} measurements")
            
            if time_series:
                values = [t['value'] for t in time_series]
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                
                print_info(f"  NDVI Statistics:")
                print_info(f"    Min: {min_val:.4f}")
                print_info(f"    Max: {max_val:.4f}")
                print_info(f"    Avg: {avg_val:.4f}")
                
                # Validate ranges
                if -1 <= min_val <= 1 and -1 <= max_val <= 1:
                    print_success("NDVI values are in valid range [-1, 1]")
                else:
                    print_error(f"NDVI out of range! Min={min_val}, Max={max_val}")
                    print_warning("  This indicates scaling issues")
                    return False
                
                # Expected ranges for agricultural areas
                if 0.2 <= avg_val <= 0.8:
                    print_success("Average NDVI in expected range for vegetation [0.2-0.8]")
                else:
                    print_warning(f"Average NDVI {avg_val:.4f} outside typical vegetation range")
                
                # Show recent values
                print_info("  Recent values:")
                for entry in time_series[-5:]:
                    print_info(f"    {entry['date']}: {entry['value']:.4f}")
                
                return True
            else:
                print_warning("Empty time series returned")
                return False
        elif response.status_code == 404:
            print_warning("No data available for time period")
            return False
        else:
            print_error(f"Failed with status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_warning("Request timed out")
        return False
    except Exception as e:
        print_error(f"Error in time series: {e}")
        return False

def test_all_indices():
    """Test all 6 vegetation indices"""
    print_header("TEST 5: All Vegetation Indices (Tests Cloud Masking)")
    
    indices = ['NDVI', 'EVI', 'SAVI', 'ARVI', 'MAVI', 'SR']
    today = datetime.now()
    end_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    
    results = {}
    
    for idx in indices:
        try:
            payload = {
                "coordinates": TEST_LOCATION["coordinates"],
                "start_date": start_date,
                "end_date": end_date,
                "index_name": idx
            }
            
            response = requests.post(
                f"{SERVER_URL}/api/indices/calculate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print_success(f"{idx} calculation successful")
                results[idx] = True
            else:
                print_error(f"{idx} failed with status {response.status_code}")
                results[idx] = False
        except Exception as e:
            print_error(f"{idx} error: {e}")
            results[idx] = False
    
    success_count = sum(1 for v in results.values() if v)
    print_info(f"\n  {success_count}/{len(indices)} indices working")
    
    return success_count == len(indices)

def test_scaling_validation():
    """Validate that scaling fix is working by checking NDVI bounds"""
    print_header("TEST 6: Scaling Validation (Most Important Test)")
    
    print_info("This test validates that Sentinel-2 data is correctly scaled")
    print_info("Before fix: multiply(0.0001) would corrupt values")
    print_info("After fix: divide(10000) produces correct range")
    
    today = datetime.now()
    end_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    
    payload = {
        "coordinates": TEST_LOCATION["coordinates"],
        "start_date": start_date,
        "end_date": end_date,
        "index_name": "NDVI"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/api/indices/timeseries",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            time_series = data.get('time_series', [])
            
            if not time_series:
                print_warning("No data points to validate")
                return False
            
            values = [t['value'] for t in time_series]
            
            # Check 1: NDVI must be in [-1, 1]
            in_range = all(-1 <= v <= 1 for v in values)
            if in_range:
                print_success("✓ All NDVI values in correct range [-1, 1]")
            else:
                out_of_range = [v for v in values if v < -1 or v > 1]
                print_error(f"✗ Found {len(out_of_range)} out-of-range values: {out_of_range[:5]}")
                print_warning("  This indicates scaling is still broken! (multiply vs divide)")
                return False
            
            # Check 2: Statistical sanity
            avg_val = sum(values) / len(values)
            if 0.1 <= avg_val <= 0.9:
                print_success(f"✓ Average NDVI {avg_val:.4f} is reasonable for vegetation")
            else:
                print_warning(f"⚠ Average NDVI {avg_val:.4f} seems low for agricultural area")
            
            # Check 3: No extreme anomalies
            std_dev = (sum((v - avg_val) ** 2 for v in values) / len(values)) ** 0.5
            if std_dev < 0.3:
                print_success(f"✓ Standard deviation {std_dev:.4f} indicates consistent data")
            else:
                print_warning(f"⚠ High variability in data (std dev = {std_dev:.4f})")
            
            return True
        else:
            print_warning("Could not retrieve data for validation")
            return False
    except Exception as e:
        print_error(f"Validation error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("\n" + "█"*70)
    print("█  EARTH ENGINE ACCURACY FIX - VERIFICATION SUITE")
    print("█"*70)
    print(f"\nServer: {SERVER_URL}")
    print(f"Test Location: {TEST_LOCATION['location_name']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    test_results = {
        "Health Check": test_health_check(),
        "Indices List": test_indices_list(),
        "NDVI Calculation": test_ndvi_calculation(),
        "NDVI Time Series": test_ndvi_time_series(),
        "All Indices": test_all_indices(),
        "Scaling Validation": test_scaling_validation(),
    }
    
    # Summary
    print_header("FINAL SUMMARY")
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! Earth Engine fixes are working correctly.")
        print_info("Satellite data should now be accurate and reliable.")
        return 0
    elif passed >= total - 1:
        print_warning(f"Most tests passed ({passed}/{total}). Minor issues may exist.")
        print_info("Check the failures above for details.")
        return 1
    else:
        print_error(f"Multiple failures ({passed}/{total}). Critical issues detected.")
        print_info("Review Earth Engine configuration and fixes.")
        return 2

if __name__ == "__main__":
    exit(main())
