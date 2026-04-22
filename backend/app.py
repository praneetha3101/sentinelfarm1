import ee
import json
import time
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import AI service
try:
    from ai_crop_service import generate_ai_crop_recommendations, get_fallback_recommendations
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AI service not available: {e}")
    AI_SERVICE_AVAILABLE = False

# Import soil prediction service
try:
    from soil_prediction_service import soil_model
    SOIL_PREDICTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Soil prediction service not available: {e}")
    SOIL_PREDICTION_AVAILABLE = False

# Import ML crop recommendation service
try:
    from ml_crop_service import MLCropRecommendationService
    ml_crop_service = MLCropRecommendationService('crop_recommendation_dataset.csv')
    ML_CROP_SERVICE_AVAILABLE = True
    print("✅ ML Crop Recommendation Service initialized")
except ImportError as e:
    print(f"⚠️ ML Crop Recommendation Service not available: {e}")
    ML_CROP_SERVICE_AVAILABLE = False
    ml_crop_service = None

# ✅ Retry logic for Earth Engine initialization
MAX_RETRIES = 5
WAIT_SECONDS = 5
EE_INITIALIZED = False

def initialize_ee():
    global EE_INITIALIZED
    
    # Check for service account key file first
    service_account_file = os.path.join(os.path.dirname(__file__), 'service-account-key.json')
    
    if os.path.exists(service_account_file):
        print("🔑 Service account key file found at:", service_account_file)
        try:
            # Load the service account key from file
            with open(service_account_file, 'r') as f:
                service_account_info = json.load(f)
            
            print(f"📧 Service account email: {service_account_info.get('client_email', 'N/A')}")
            print(f"📋 Project ID from key: {service_account_info.get('project_id', 'N/A')}")
            
            # Use the project from service account (this is the source of truth)
            project_id = service_account_info.get('project_id')
            if not project_id:
                raise ValueError("Project ID not found in service account key")
            
            # Initialize with service account file path (correct way)
            credentials = ee.ServiceAccountCredentials(
                email=service_account_info['client_email'],
                key_file=service_account_file
            )
            ee.Initialize(credentials, project=project_id)
            print(f"✅ Earth Engine initialized with service account for project: {project_id}")
            EE_INITIALIZED = True
            return
            
        except json.JSONDecodeError as json_error:
            print(f"❌ Invalid JSON in service account key file: {json_error}")
        except KeyError as key_error:
            print(f"❌ Missing required field in service account key: {key_error}")
        except FileNotFoundError as file_error:
            print(f"❌ Service account key file not found: {file_error}")
        except ee.EEException as ee_error:
            print(f"❌ Earth Engine authentication failed: {ee_error}")
        except Exception as sa_error:
            print(f"❌ Service account authentication failed ({type(sa_error).__name__}): {sa_error}")
    else:
        print("⚠️ No service account key file found at:", service_account_file)
        print("⚠️ Trying environment variable GOOGLE_SERVICE_ACCOUNT_KEY...")
        
        # Fallback to environment variable
        service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if service_account_key:
            try:
                service_account_info = json.loads(service_account_key)
                print(f"📧 Service account email: {service_account_info.get('client_email', 'N/A')}")
                print(f"📋 Project ID from key: {service_account_info.get('project_id', 'N/A')}")
                
                project_id = service_account_info.get('project_id', 'agriscope21')
                
                credentials = ee.ServiceAccountCredentials(
                    email=service_account_info['client_email'],
                    key_data=service_account_key
                )
                ee.Initialize(credentials, project=project_id)
                print(f"✅ Earth Engine initialized with service account for project: {project_id}")
                EE_INITIALIZED = True
                return
                
            except json.JSONDecodeError as json_error:
                print(f"❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY environment variable: {json_error}")
            except ee.EEException as ee_error:
                print(f"❌ Earth Engine authentication from env var failed: {ee_error}")
            except Exception as sa_error:
                print(f"❌ Service account authentication from env var failed ({type(sa_error).__name__}): {sa_error}")
        else:
            print("⚠️ GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set")
    
    # Try default authentication methods as fallback
    print("\n🔄 Attempting default Earth Engine authentication (via gcloud credentials)...")
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   Attempt {attempt + 1}/{MAX_RETRIES}: Trying default authentication...")
            ee.Initialize()
            print("✅ Earth Engine initialized with default authentication (gcloud credentials)!")
            EE_INITIALIZED = True
            return
        except Exception as e:
            error_type = type(e).__name__
            print(f"   ⚠️ Attempt {attempt + 1}/{MAX_RETRIES} failed ({error_type}): {str(e)[:100]}")
            if attempt < MAX_RETRIES - 1:
                print(f"   Waiting {WAIT_SECONDS} seconds before retry...")
                time.sleep(WAIT_SECONDS)
    
    print("\n❌ All Earth Engine authentication methods failed:")
    print("   1. Service account key file - NOT FOUND or INVALID")
    print("   2. Environment variable (GOOGLE_SERVICE_ACCOUNT_KEY) - NOT SET")
    print("   3. Default gcloud credentials - NOT AVAILABLE")
    print("\n⚠️ Running in degraded mode - satellite features will be limited")
    print("\n💡 To fix: Place 'service-account-key.json' in the backend directory")
    print("   and ensure it has valid Earth Engine service account credentials")
    EE_INITIALIZED = False
    return

# Initialize Earth Engine on startup
try:
    initialize_ee()
except Exception as e:
    print(f"⚠️ Failed to initialize Earth Engine: {e}")
    EE_INITIALIZED = False

# ✅ Flask app setup
app = Flask(__name__)
# CORS(app, resources={r"/process_ndvi": {"origins": "*"}})
CORS(app)

# Health check endpoint for Render
@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'service': 'AgriScope Flask Backend',
        'earth_engine_status': 'initialized' if EE_INITIALIZED else 'failed',
        'timestamp': datetime.now().isoformat()
    }), 200

# ✅ Generalized Vegetation Index Calculation Function
def calculate_vegetation_index(image, index_name):
    """
    Calculate a specified vegetation index using GEE server-side expressions.
    
    Args:
        image: ee.Image with bands B2 (Blue), B4 (Red), B8 (NIR), B11 (SWIR)
        index_name: String name of the index to calculate
        
    Returns:
        ee.Image with the calculated index
    """
    # Define the expressions for each vegetation index
    expressions = {
        'SR': 'NIR / R',
        'NDVI': '(NIR - R) / (NIR + R)',
        'EVI': '2.5 * ((NIR - R) / (NIR + 6 * R - 7.5 * B + 1))',
        'SAVI': '((NIR - R) / (NIR + R + 0.5)) * 1.5',  # Using L=0.5
        'ARVI': '(NIR - (2 * R - B)) / (NIR + (2 * R - B))',
        'MAVI': '(NIR - R) / (NIR + R + SWIR + 0.000001)'  # Add small value to avoid division by zero
    }
    
    if index_name not in expressions:
        raise ValueError(f"Unknown index name: {index_name}. Available indices: {list(expressions.keys())}")
    
    # Create band dictionary for expression using the b() function
    band_dict = {
        'B': image.select('B2'),     # Blue
        'R': image.select('B4'),     # Red  
        'NIR': image.select('B8'),   # Near Infrared
        'SWIR': image.select('B11')  # Short Wave Infrared
    }
    
    # Calculate the index using the expression with band names
    index_image = image.expression(expressions[index_name], band_dict).rename(index_name)
    
    return index_image

def get_visualization_params(index_name):
    """
    Get appropriate visualization parameters for each vegetation index.
    
    Args:
        index_name: String name of the index
        
    Returns:
        Dictionary with visualization parameters
    """
    vis_params = {
        'SR': {
            'min': 0, 'max': 8,
            'palette': ['red', 'orange', 'yellow', 'green', 'darkgreen']
        },
        'NDVI': {
            'min': -0.2, 'max': 1.0,
            'palette': ['blue', 'white', 'yellow', 'green', 'darkgreen']
        },
        'EVI': {
            'min': -0.2, 'max': 1.0,
            'palette': ['brown', 'yellow', 'lightgreen', 'green', 'darkgreen']
        },
        'SAVI': {
            'min': -0.2, 'max': 1.0,
            'palette': ['purple', 'blue', 'cyan', 'yellow', 'red']
        },
        'ARVI': {
            'min': -0.2, 'max': 1.0,
            'palette': ['red', 'orange', 'yellow', 'lightgreen', 'darkgreen']
        },
        'MAVI': {
            'min': -0.2, 'max': 1.0,
            'palette': ['red', 'yellow', 'lightblue', 'blue', 'darkblue']
        }
    }
    
    return vis_params.get(index_name, vis_params['NDVI'])  # Default to NDVI params

# ✅ Function to mask clouds using Sentinel-2 L2A SCL band
def mask_clouds(image):
    """
    Mask out cloudy and shadow pixels using the SCL band.
    More permissive approach - if SCL band doesn't exist or masking fails, return original image.
    """
    try:
        # Try to use SCL if available
        if 'SCL' in image.bandNames().getInfo():
            scl = image.select('SCL')
            # Keep vegetation, non-vegetation, and water (more permissive)
            quality_mask = scl.gt(3).And(scl.lt(11))  # Keep classes 4-10
            return image.updateMask(quality_mask)
    except:
        pass
    
    # If SCL doesn't exist or masking fails, return original image
    # (We already filtered by CLOUDY_PIXEL_PERCENTAGE so clouds are limited anyway)
    return image

# ✅ NDVI Calculation Function
def calculate_ndvi(image):
    """
    Calculate NDVI as (B8 - B4) / (B8 + B4).
    """
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi).copyProperties(image, ['system:time_start'])

@app.route('/process_ndvi', methods=['POST'])
def process_ndvi():
    try:
        # ✅ Receive request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        coordinates = data.get('coordinates')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not coordinates or not start_date or not end_date:
            return jsonify({"error": "Missing required fields"}), 400

        if len(coordinates) < 3:
            return jsonify({"error": "AOI must have at least three coordinates"}), 400

        # ✅ Check if Earth Engine is available
        if not EE_INITIALIZED:
            return jsonify({"error": "Google Earth Engine is not initialized. Please check service account configuration."}), 503

        # ✅ Create AOI Polygon
        aoi = ee.Geometry.Polygon([coordinates])
        print("✅ AOI Polygon:", aoi.getInfo())

        # ✅ Load Sentinel-2 Surface Reflectance collection (COPERNICUS/S2_SR_HARMONIZED or COPERNICUS/S2_SR)
        # NOTE: Sentinel-2 SR data is already in 0-10000 range, convert to 0-1 for calculations
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .map(mask_clouds)
            .map(lambda img: img.divide(10000))  # Normalize from 0-10000 to 0-1 range
        )

        # ✅ If no images, return 404
        if collection.size().getInfo() == 0:
            return jsonify({"error": "No Sentinel-2 data available for the specified AOI and dates"}), 404

        # ✅ Compute NDVI
        ndvi_collection = collection.map(calculate_ndvi)
        mean_ndvi = ndvi_collection.mean().select('NDVI')

        # ✅ Clip NDVI to AOI to avoid entire bounding box
        mean_ndvi_clipped = mean_ndvi.clip(aoi)

        # ✅ Generate NDVI tile URL
        # Typical NDVI can range from about -0.2 (bare soil) to 1.0 (dense vegetation).
        # We can use a standard NDVI color palette from red (low) to green (high).
        vis_params = {
            'min': -0.2,     # or 0 if you only want positive NDVI
            'max': 1.0,
            'palette': [
                'blue',       # -0.2 NDVI
                'white',      # 0 NDVI
                'yellow',     # 0.3 NDVI
                'green',      # 0.6 NDVI
                'darkgreen'   # 1.0 NDVI
            ]
        }

        map_dict = mean_ndvi_clipped.getMapId(vis_params)
        tile_url = map_dict['tile_fetcher'].url_format
        print("✅ NDVI Tile URL:", tile_url)

        response = {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "coordinates": coordinates,
            "tile_url": tile_url
        }
        return jsonify(response), 200

    except ee.EEException as e:
        print("❌ Earth Engine Error:", str(e))
        return jsonify({"error": f"Earth Engine Error: {str(e)}"}), 500
    except Exception as e:
        print("❌ Internal server error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/ndvi_time_series', methods=['POST'])
def ndvi_time_series():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        coordinates = data.get('coordinates')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if not coordinates or not start_date or not end_date:
            return jsonify({"error": "Missing required fields"}), 400
        if len(coordinates) < 3:
            return jsonify({"error": "AOI must have at least three coordinates"}), 400

        # ✅ Check if Earth Engine is available
        if not EE_INITIALIZED:
            return jsonify({"error": "Google Earth Engine is not initialized. Please check service account configuration."}), 503

        # Create AOI and apply a small positive buffer or no buffer
        aoi = ee.Geometry.Polygon([coordinates])
        # Use positive buffer or no buffer to avoid geometry issues
        buffered_geom = aoi.buffer(10)  # Small positive buffer instead of negative
        print("✅ Buffered AOI:", buffered_geom.getInfo())

        # Load Sentinel-2 SR collection filtered by the buffered geometry.
        # NOTE: Sentinel-2 SR data is in 0-10000 range, divide by 10000 to normalize to 0-1
        collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                      .filterBounds(buffered_geom)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                      .filter(ee.Filter.notNull(['system:time_start']))
                      .map(mask_clouds)
                     )
        # Scale images and preserve properties.
        def scale_image(image):
            return image.divide(10000).copyProperties(image, ['system:time_start', 'system:index'])
        collection = collection.map(scale_image)

        coll_size = collection.size().getInfo()
        print("Collection size:", coll_size)
        if coll_size == 0:
            return jsonify({"error": "No Sentinel-2 data available for the specified AOI and dates"}), 404

        # Compute NDVI and preserve time property.
        def add_ndvi(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi).copyProperties(image, ['system:time_start', 'system:index'])
        ndvi_collection = collection.map(add_ndvi)

        # Mapping function: For each image, compute mean NDVI over the buffered geometry and return a feature with image ID, raw time, formatted date, and NDVI.
        def debug_feature(image):
            time_prop = image.get('system:time_start')
            image_id = image.get('system:index')
            formatted_date = ee.Algorithms.If(
                ee.Algorithms.IsEqual(time_prop, None),
                "null",
                ee.Date(time_prop).format('YYYY-MM-dd')
            )
            ndvi_dict = image.select('NDVI').reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=buffered_geom,
                scale=10,         # Sentinel-2 native resolution is 10m for visible/NIR bands
                bestEffort=True,
                maxPixels=1e9
            )
            ndvi_value = ndvi_dict.get('NDVI')
            return ee.Feature(None, {
                'id': image_id,
                'time_start': time_prop,
                'date': formatted_date,
                'ndvi': ndvi_value
            })

        # Map over the NDVI collection.
        features = ndvi_collection.map(debug_feature, dropNulls=True)
        features = ee.FeatureCollection(features)
        try:
            features_info = features.getInfo()
            print("Mapped features info retrieved successfully.")
        except Exception as inner_error:
            print("❌ Error calling getInfo on features:", inner_error)
            raise

        # Build the time series list from features with valid 'date' and 'ndvi'
        time_series = []
        for f in features_info.get('features', []):
            props = f.get('properties', {})
            if props.get('date') and props.get('ndvi') is not None:
                time_series.append({
                    'date': props.get('date'),
                    'ndvi': props.get('ndvi')
                })

        response = {
            "status": "success",
            "time_series": time_series
        }
        return jsonify(response), 200

    except ee.EEException as e:
        print("❌ Earth Engine Error:", str(e))
        return jsonify({"error": f"Earth Engine Error: {str(e)}"}), 500
    except Exception as e:
        print("❌ Internal server error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/indices/calculate', methods=['POST'])
def process_index():
    """
    Generic endpoint to calculate any vegetation index and return tile URL for visualization.
    
    Expected JSON payload:
    {
        "coordinates": [[lng, lat], [lng, lat], ...],
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD", 
        "index_name": "NDVI" | "EVI" | "SAVI" | "ARVI" | "MAVI" | "SR"
    }
    """
    try:
        # ✅ Receive request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        coordinates = data.get('coordinates')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        index_name = data.get('index_name', 'NDVI')  # Default to NDVI

        if not coordinates or not start_date or not end_date:
            return jsonify({"error": "Missing required fields: coordinates, start_date, end_date"}), 400

        if len(coordinates) < 3:
            return jsonify({"error": "AOI must have at least three coordinates"}), 400

        # ✅ Date validation - Sentinel-2 data has ~5 day delay
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            today = datetime.now()
            
            # Check if end date is too recent (less than 5 days ago)
            days_ago = (today - end_dt).days
            if days_ago < 5:
                return jsonify({
                    "error": f"End date is too recent. Satellite data is typically delayed by 4-5 days. Please select a date before {(today - timedelta(days=5)).strftime('%Y-%m-%d')}",
                    "suggested_end_date": (today - timedelta(days=5)).strftime('%Y-%m-%d')
                }), 400
                
            # Check if date range is valid
            if start_dt >= end_dt:
                return jsonify({"error": "Start date must be before end date"}), 400
                
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # ✅ Check if Earth Engine is available
        if not EE_INITIALIZED:
            return jsonify({"error": "Google Earth Engine is not initialized. Please check service account configuration."}), 503

        # ✅ Create AOI Polygon
        aoi = ee.Geometry.Polygon([coordinates])
        print(f"✅ AOI Polygon for {index_name}:", aoi.getInfo())
        
        # ✅ Load Sentinel-2 data - use harmonized collection (not deprecated)
        # Select bands FIRST to avoid issues with unavailable bands
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .select(['B2', 'B4', 'B8', 'B11'])  # Select bands early to ensure they exist
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))  # Filter clouds first
            .map(lambda img: img.divide(10000))  # Normalize reflectance to 0-1 range
        )
        
        collection_size = collection.size().getInfo()
        print(f"✅ Final collection size: {collection_size} images available")
        
        # ✅ If no images, return helpful error
        if collection_size == 0:
            today = datetime.now()
            latest_available = (today - timedelta(days=5)).strftime('%Y-%m-%d')
            
            # Diagnose which step failed
            raw_count = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(aoi).filterDate(start_date, end_date).size().getInfo()
            
            return jsonify({
                "error": "No Sentinel-2 data available for this location",
                "debugging": {
                    "total_images_in_date_range": raw_count,
                    "issue": "All images may have been filtered by cloud threshold (>20% cloudy)"
                },
                "suggestion": "Try different dates or location. Data must be older than 5 days.",
                "latest_available_date": latest_available,
                "location": f"Lat: {coordinates[0][1] if coordinates else 'unknown'}, Lng: {coordinates[0][0] if coordinates else 'unknown'}"
            }), 404

        # ✅ Get median composite and calculate the selected vegetation index
        median_image = collection.median()
        
        try:
            index_image = calculate_vegetation_index(median_image, index_name)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        # ✅ Clip index to AOI to avoid entire bounding box
        index_clipped = index_image.clip(aoi)

        # ✅ Generate index tile URL with appropriate visualization parameters
        vis_params = get_visualization_params(index_name)
        map_dict = index_clipped.getMapId(vis_params)
        tile_url = map_dict['tile_fetcher'].url_format
        print(f"✅ {index_name} Tile URL:", tile_url)

        response = {
            "status": "success",
            "index_name": index_name,
            "start_date": start_date,
            "end_date": end_date,
            "coordinates": coordinates,
            "tile_url": tile_url,
            "visualization_params": vis_params
        }
        return jsonify(response), 200

    except ee.EEException as e:
        print("❌ Earth Engine Error:", str(e))
        return jsonify({"error": f"Earth Engine Error: {str(e)}"}), 500
    except Exception as e:
        print("❌ Internal server error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/indices/timeseries', methods=['POST'])
def index_time_series():
    """
    Generic endpoint to calculate time series for any vegetation index.
    
    Expected JSON payload:
    {
        "coordinates": [[lng, lat], [lng, lat], ...],
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "index_name": "NDVI" | "EVI" | "SAVI" | "ARVI" | "MAVI" | "SR"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        coordinates = data.get('coordinates')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        index_name = data.get('index_name', 'NDVI')  # Default to NDVI

        if not coordinates or not start_date or not end_date:
            return jsonify({"error": "Missing required fields: coordinates, start_date, end_date"}), 400
        if len(coordinates) < 3:
            return jsonify({"error": "AOI must have at least three coordinates"}), 400

        # ✅ Date validation - Sentinel-2 data has ~5 day delay
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            today = datetime.now()
            
            # Check if end date is too recent (less than 5 days ago)
            days_ago = (today - end_dt).days
            if days_ago < 5:
                return jsonify({
                    "error": f"End date is too recent. Satellite data is typically delayed by 4-5 days. Please select a date before {(today - timedelta(days=5)).strftime('%Y-%m-%d')}",
                    "suggested_end_date": (today - timedelta(days=5)).strftime('%Y-%m-%d')
                }), 400
                
            # Check if date range is valid
            if start_dt >= end_dt:
                return jsonify({"error": "Start date must be before end date"}), 400
                
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # ✅ Check if Earth Engine is available
        if not EE_INITIALIZED:
            return jsonify({"error": "Google Earth Engine is not initialized. Please check service account configuration."}), 503

        # Create AOI and apply a small positive buffer
        aoi = ee.Geometry.Polygon([coordinates])
        buffered_geom = aoi.buffer(10)  # Small positive buffer
        print(f"✅ Buffered AOI for {index_name}:", buffered_geom.getInfo())

        # Load Sentinel-2 SR collection with all required bands
        # Simple and direct: filters -> scale
        collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                      .filterBounds(buffered_geom)
                      .filterDate(start_date, end_date)
                      .select(['B2', 'B4', 'B8', 'B11'])
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                      .filter(ee.Filter.notNull(['system:time_start']))
        )
        
        # Scale images and preserve properties
        def scale_image(image):
            return image.divide(10000).copyProperties(image, ['system:time_start', 'system:index'])
        collection = collection.map(scale_image)

        coll_size = collection.size().getInfo()
        print(f"✅ Time series collection size for {index_name}: {coll_size} images")
        if coll_size == 0:
            today = datetime.now()
            latest_available = (today - timedelta(days=5)).strftime('%Y-%m-%d')
            
            raw_count = ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(buffered_geom).filterDate(start_date, end_date).size().getInfo()
            
            return jsonify({
                "error": f"No Sentinel-2 data available for {index_name} time series",
                "debugging": {
                    "total_raw_images": raw_count,
                    "issue": "All images filtered by cloud or quality checks"
                },
                "suggestion": "Try different dates or location",
                "latest_available_date": latest_available
            }), 404

        # Compute the selected vegetation index for each image
        def add_index(image):
            try:
                index_img = calculate_vegetation_index(image, index_name)
                return image.addBands(index_img).copyProperties(image, ['system:time_start', 'system:index'])
            except:
                return image  # Skip if calculation fails
        
        index_collection = collection.map(add_index)

        # Extract time series data
        def extract_index_feature(image):
            time_prop = image.get('system:time_start')
            image_id = image.get('system:index')
            formatted_date = ee.Algorithms.If(
                ee.Algorithms.IsEqual(time_prop, None),
                "null",
                ee.Date(time_prop).format('YYYY-MM-dd')
            )
            
            # Using scale=10 (Sentinel-2's native resolution) instead of scale=5
            index_dict = image.select(index_name).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=buffered_geom,
                scale=10,  # Sentinel-2 native resolution is 10m for visible/NIR bands
                bestEffort=True,
                maxPixels=1e9
            )
            index_value = index_dict.get(index_name)
            
            return ee.Feature(None, {
                'id': image_id,
                'time_start': time_prop,
                'date': formatted_date,
                'index_name': index_name,
                'value': index_value
            })

        # Map over the collection
        features = index_collection.map(extract_index_feature, dropNulls=True)
        features = ee.FeatureCollection(features)
        
        try:
            features_info = features.getInfo()
            print(f"Mapped features info for {index_name} retrieved successfully.")
        except Exception as inner_error:
            print(f"❌ Error calling getInfo on {index_name} features:", inner_error)
            raise

        # Build the time series list
        time_series = []
        for f in features_info.get('features', []):
            props = f.get('properties', {})
            if props.get('date') and props.get('value') is not None:
                time_series.append({
                    'date': props.get('date'),
                    'value': props.get('value'),
                    'index_name': index_name
                })

        response = {
            "status": "success",
            "index_name": index_name,
            "time_series": time_series,
            "total_measurements": len(time_series)
        }
        return jsonify(response), 200

    except ee.EEException as e:
        print("❌ Earth Engine Error:", str(e))
        return jsonify({"error": f"Earth Engine Error: {str(e)}"}), 500
    except Exception as e:
        print("❌ Internal server error:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/indices/list', methods=['GET'])
def list_indices():
    """
    Return a list of available vegetation indices with their descriptions.
    """
    indices = {
        'NDVI': {
            'name': 'Normalized Difference Vegetation Index',
            'formula': '(NIR - Red) / (NIR + Red)',
            'description': 'Most common vegetation index, good for general vegetation health assessment',
            'range': [-1, 1],
            'optimal_range': [0.4, 0.7]
        },
        'EVI': {
            'name': 'Enhanced Vegetation Index', 
            'formula': '2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))',
            'description': 'Improved version of NDVI with atmospheric correction and reduced soil noise',
            'range': [-1, 1],
            'optimal_range': [0.3, 0.8]
        },
        'SAVI': {
            'name': 'Soil-Adjusted Vegetation Index',
            'formula': '((NIR - Red) / (NIR + Red + 0.5)) * 1.5',
            'description': 'Reduces soil brightness influence, good for sparse vegetation',
            'range': [-1, 1],
            'optimal_range': [0.2, 0.6]
        },
        'ARVI': {
            'name': 'Atmospherically Resistant Vegetation Index',
            'formula': '(NIR - (2*Red - Blue)) / (NIR + (2*Red - Blue))',
            'description': 'Reduces atmospheric effects, especially aerosol scattering',
            'range': [-1, 1],
            'optimal_range': [0.3, 0.7]
        },
        'MAVI': {
            'name': 'Moisture-Adjusted Vegetation Index',
            'formula': '(NIR - Red) / (NIR + Red + SWIR)',
            'description': 'Incorporates moisture information from SWIR band',
            'range': [-1, 1],
            'optimal_range': [0.2, 0.6]
        },
        'SR': {
            'name': 'Simple Ratio',
            'formula': 'NIR / Red', 
            'description': 'Basic ratio of NIR to Red, simple but effective',
            'range': [0, 10],
            'optimal_range': [2, 8]
        }
    }
    
    return jsonify({
        "status": "success",
        "indices": indices,
        "total_count": len(indices)
    })

@app.route('/api/crop-recommendations', methods=['POST'])
def get_ai_crop_recommendations():
    """
    Generate AI-powered crop recommendations based on field data, weather, and vegetation indices.
    Falls back to ML-based recommendations with crop dataset insights.
    
    Expected JSON payload:
    {
        "field_data": {
            "location": "Maharashtra, India",
            "area": 2.5,
            "soil_type": "Black Cotton Soil",
            "soil_ph": 7.2,
            "irrigation": "Drip irrigation",
            "experience": "5 years",
            "budget": "Rs. 50,000"
        },
        "weather_data": {
            "avg_temp": 28,
            "rainfall": 650,
            "humidity": 75,
            "pattern": "Normal monsoon expected"
        },
        "vegetation_data": {
            "ndvi": 0.65,
            "soil_health": "Good",
            "prev_performance": "Above average"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
            
        field_data = data.get('field_data', {})
        weather_data = data.get('weather_data')
        vegetation_data = data.get('vegetation_data')
        coordinates = data.get('coordinates')
        
        if not field_data:
            return jsonify({"error": "Field data is required"}), 400
        
        # Predict soil properties if not provided or if NDVI available
        predicted_soil = {}
        if SOIL_PREDICTION_AVAILABLE and vegetation_data and vegetation_data.get('ndvi'):
            try:
                ndvi = vegetation_data.get('ndvi', 0.5)
                # Estimate other indices from NDVI
                ndbi = -0.15 if ndvi > 0.5 else 0.0
                ndmi = 0.35 if ndvi > 0.5 else 0.2
                savi = ndvi * 0.7
                
                predicted_soil = soil_model.predict_soil_properties(ndvi, ndbi, ndmi, savi)
                
                # Enhance field data with predicted soil
                if not field_data.get('soil_type') or field_data.get('soil_type') == '':
                    field_data['soil_type'] = predicted_soil.get('soil_type', 'Unknown')
                if not field_data.get('soil_ph') or field_data.get('soil_ph') == '':
                    field_data['soil_ph'] = predicted_soil.get('soil_ph', 6.5)
                
            except Exception as soil_err:
                print(f"⚠️ Soil prediction error: {soil_err}")
        
        # Generate AI recommendations
        if AI_SERVICE_AVAILABLE:
            recommendations = generate_ai_crop_recommendations(
                field_data=field_data,
                weather_data=weather_data,
                vegetation_data=vegetation_data
            )
            
            # Add soil prediction data to recommendations if available
            if predicted_soil:
                recommendations['soil_prediction'] = predicted_soil
            
            # Check if AI actually generated recommendations (check for crops)
            has_valid_crops = recommendations.get('recommended_crops') and len(recommendations.get('recommended_crops', [])) > 0
            
            if has_valid_crops and recommendations.get('ai_generated'):
                # AI service worked - return success
                print(f"✅ AI-generated recommendations returned")
                return jsonify({
                    'status': 'success',
                    'recommendations': recommendations
                }), 200
            elif not has_valid_crops:
                # AI didn't generate valid recommendations - try ML service instead
                print("[+] AI service returned no crops - trying ML service")
                if ML_CROP_SERVICE_AVAILABLE and ml_crop_service and ml_inference and ml_inference.models_available:
                    input_features = {
                        'N': float(field_data.get('nitrogen', 75)),
                        'P': float(field_data.get('phosphorus', 28)),
                        'K': float(field_data.get('potassium', 51)),
                        'temperature': float(field_data.get('temperature', 25)),
                        'humidity': float(field_data.get('humidity', 65)),
                        'pH': float(field_data.get('soil_ph', 6.5)),
                        'rainfall': float(field_data.get('rainfall', 1000))
                    }
                    
                    top_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
                    if top_crops:
                        ml_recommendations = ml_crop_service.generate_ml_recommendations(top_crops, field_data)
                        if predicted_soil:
                            ml_recommendations['soil_prediction'] = predicted_soil
                        
                        print(f"✅ ML-based recommendations generated: {[c[0] for c in top_crops]}")
                        return jsonify({
                            'status': 'ml_powered',
                            'ai_generated': False,
                            'method': 'ml_ensemble_with_crop_dataset',
                            'recommendations': ml_recommendations
                        }), 200
        
        # If AI service completely failed or unavailable, try ML service
        if ML_CROP_SERVICE_AVAILABLE and ml_crop_service and ml_inference and ml_inference.models_available:
            print("[+] Using ML-based crop recommendations with crop dataset insights")
            
            # Prepare features for ML model
            input_features = {
                'N': float(field_data.get('nitrogen', 75)),
                'P': float(field_data.get('phosphorus', 28)),
                'K': float(field_data.get('potassium', 51)),
                'temperature': float(field_data.get('temperature', 25)),
                'humidity': float(field_data.get('humidity', 65)),
                'pH': float(field_data.get('soil_ph', 6.5)),
                'rainfall': float(field_data.get('rainfall', 1000))
            }
            
            # Get top 3 crops from ML ensemble
            top_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
            
            if top_crops:
                # Generate detailed recommendations using crop dataset
                ml_recommendations = ml_crop_service.generate_ml_recommendations(top_crops, field_data)
                
                if predicted_soil:
                    ml_recommendations['soil_prediction'] = predicted_soil
                
                print(f"✅ ML-based recommendations generated for: {[c[0] for c in top_crops]}")
                return jsonify({
                    'status': 'ml_powered',
                    'ai_generated': False,
                    'method': 'ml_ensemble_with_crop_dataset',
                    'recommendations': ml_recommendations
                }), 200
        
        # Final fallback if everything failed
        print("[!] All services failed - returning empty fallback")
        fallback = get_fallback_recommendations()
        if predicted_soil:
            fallback['soil_prediction'] = predicted_soil
        
        return jsonify({
            'status': 'fallback',
            'ai_generated': False,
            'message': 'No recommendations available - all services unavailable',
            'recommendations': fallback
        }), 200
        
    except Exception as e:
        print(f"❌ Error generating crop recommendations: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            # Try ML-based fallback
            if ML_CROP_SERVICE_AVAILABLE and ml_crop_service and ml_inference and ml_inference.models_available:
                input_features = {
                    'N': float(field_data.get('nitrogen', 75)),
                    'P': float(field_data.get('phosphorus', 28)),
                    'K': float(field_data.get('potassium', 51)),
                    'temperature': float(field_data.get('temperature', 25)),
                    'humidity': float(field_data.get('humidity', 65)),
                    'pH': float(field_data.get('soil_ph', 6.5)),
                    'rainfall': float(field_data.get('rainfall', 1000))
                }
                
                top_crops, _ = ml_inference.predict_best_crops(input_features)
                if top_crops:
                    ml_recommendations = ml_crop_service.generate_ml_recommendations(top_crops, field_data)
                    return jsonify({
                        'status': 'ml_fallback',
                        'ai_generated': False,
                        'error': f"Error during primary processing: {str(e)}",
                        'recommendations': ml_recommendations
                    }), 200
        except:
            pass
        
        # Final fallback to generic recommendations
        fallback = get_fallback_recommendations() if AI_SERVICE_AVAILABLE else {}
        
        return jsonify({
            'status': 'error',
            'error': f"Failed to generate recommendations: {str(e)}",
            'recommendations': fallback if fallback else None
        }), 200  # Return 200 so frontend shows something

@app.route('/debug/auth', methods=['GET'])
def debug_auth():
    """Debug endpoint to check authentication status"""
    service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
    
    debug_info = {
        "earth_engine_initialized": EE_INITIALIZED,
        "service_account_key_present": bool(service_account_key),
        "service_account_key_length": len(service_account_key) if service_account_key else 0,
    }
    
    if service_account_key:
        try:
            service_account_info = json.loads(service_account_key)
            debug_info.update({
                "service_account_email": service_account_info.get('client_email', 'N/A'),
                "project_id_from_key": service_account_info.get('project_id', 'N/A'),
                "key_type": service_account_info.get('type', 'N/A'),
                "key_has_private_key": 'private_key' in service_account_info
            })
        except Exception as e:
            debug_info["service_account_parse_error"] = str(e)
    
    return jsonify(debug_info)

@app.route('/api/debug/ndvi-stats/<float:lat>/<float:lng>', methods=['GET'])
def debug_ndvi_stats(lat, lng):
    """Debug endpoint to analyze NDVI statistics for a point"""
    try:
        # Initialize Earth Engine if not already done
        if not hasattr(app, 'ee_initialized'):
            initialize_ee()
        
        # Create point geometry with buffer
        point = ee.Geometry.Point([lng, lat])
        aoi = point.buffer(100)  # 100m buffer for analysis
        
        # Get recent date range
        end_date = ee.Date(datetime.now().strftime('%Y-%m-%d'))
        start_date = end_date.advance(-30, 'day')
        
        # Get Sentinel-2 collection
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
                      .filterBounds(aoi) \
                      .filterDate(start_date, end_date) \
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
        # Calculate NDVI for most recent image
        def calculate_ndvi_stats(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # Get various statistics
            stats = ndvi.reduceRegion(
                reducer=ee.Reducer.minMax().combine(
                    ee.Reducer.mean(), sharedInputs=True
                ).combine(
                    ee.Reducer.stdDev(), sharedInputs=True
                ).combine(
                    ee.Reducer.percentile([10, 25, 50, 75, 90]), sharedInputs=True
                ),
                geometry=aoi,
                scale=10,
                maxPixels=1e9
            )
            
            return {
                'date': image.date().format('YYYY-MM-dd').getInfo(),
                'stats': stats.getInfo()
            }
        
        # Get collection info
        collection_size = collection.size().getInfo()
        
        if collection_size == 0:
            return jsonify({
                'error': 'No Sentinel-2 images found for this location and date range',
                'location': {'lat': lat, 'lng': lng},
                'date_range': {
                    'start': start_date.format('YYYY-MM-dd').getInfo(),
                    'end': end_date.format('YYYY-MM-dd').getInfo()
                }
            })
        
        # Get stats for the most recent image
        most_recent = collection.sort('system:time_start', False).first()
        ndvi_stats = calculate_ndvi_stats(most_recent)
        
        return jsonify({
            'location': {'lat': lat, 'lng': lng},
            'date_range': {
                'start': start_date.format('YYYY-MM-dd').getInfo(),
                'end': end_date.format('YYYY-MM-dd').getInfo()
            },
            'collection_size': collection_size,
            'most_recent_image': ndvi_stats,
            'analysis': {
                'note': 'Healthy vegetation typically shows NDVI values between 0.4-0.7',
                'interpretation': 'Values below 0.3 may indicate stressed vegetation, bare soil, or water'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/data-availability/<float:lat>/<float:lng>/<start_date>/<end_date>', methods=['GET'])
def debug_data_availability(lat, lng, start_date, end_date):
    """
    Debug endpoint to check Sentinel-2 data availability for a location
    Example: /debug/data-availability/20.5937/73.7997/2026-01-01/2026-02-26
    """
    try:
        point = ee.Geometry.Point([lng, lat])
        aoi = point.buffer(1000)  # 1km buffer
        
        # Check all images
        all_images = ee.ImageCollection('COPERNICUS/S2_SR') \
                      .filterBounds(aoi) \
                      .filterDate(start_date, end_date)
        
        all_count = all_images.size().getInfo()
        
        # Check cloud-free images
        cloudfree = all_images.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        cloudfree_count = cloudfree.size().getInfo()
        
        # Check very clear images
        very_clear = all_images.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
        very_clear_count = very_clear.size().getInfo()
        
        return jsonify({
            "location": {
                "lat": lat,
                "lng": lng
            },
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "availability": {
                "total_images": all_count,
                "cloud_free_20%": cloudfree_count,
                "very_clear_5%": very_clear_count
            },
            "status": {
                "has_data": all_count > 0,
                "has_cloud_free": cloudfree_count > 0,
                "recommendation": "Use dates with very_clear_5% > 0 for best results" if very_clear_count > 0 else "Try different dates or location"
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/data', methods=['POST'])
def get_weather_data():
    """
    Fetch weather data from NASA POWER API with validation for Indian climate.
    
    Expected JSON payload:
    {
        "coordinates": [[lng, lat], [lng, lat], ...],
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }
    """
    try:
        import requests
        
        data = request.get_json()
        if not data or 'coordinates' not in data or 'start_date' not in data or 'end_date' not in data:
            return jsonify({'error': 'Missing required fields: coordinates, start_date, end_date'}), 400
        
        coordinates = data['coordinates']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # Extract center point of field for weather data
        center_lng = sum(coord[0] for coord in coordinates) / len(coordinates)
        center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        
        # Format dates for NASA POWER API (YYYYMMDD format)
        formatted_start_date = start_date.replace('-', '')
        formatted_end_date = end_date.replace('-', '')
        
        # Parameters to fetch: temperature, precipitation, humidity, solar radiation
        parameters = 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN'
        
        power_api_url = f'https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameters}&community=AG&longitude={center_lng}&latitude={center_lat}&start={formatted_start_date}&end={formatted_end_date}&format=JSON'
        
        print(f"📡 Fetching weather data from NASA POWER API for location ({center_lat}, {center_lng})")
        response = requests.get(power_api_url, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        
        # Validate and clean the data - NASA POWER API uses -999 for missing data
        cleaned_data = validate_and_clean_weather_data(api_data, center_lat)
        
        print(f"✅ Weather data validated and cleaned for Indian climate region")
        
        return jsonify(cleaned_data), 200
        
    except Exception as e:
        print(f"❌ Error fetching weather data: {e}")
        return jsonify({'error': 'Failed to fetch weather data', 'details': str(e)}), 500

def validate_and_clean_weather_data(api_data, latitude):
    """
    Validates and cleans weather data from NASA POWER API.
    Removes -999 placeholder values (missing data) and uses realistic Indian climate patterns.
    
    Args:
        api_data: Raw data from NASA POWER API
        latitude: Field latitude for regional climate patterns
        
    Returns:
        Cleaned weather data with validated values
    """
    if not api_data.get('properties') or not api_data['properties'].get('parameter'):
        return api_data

    parameter = api_data['properties']['parameter']
    cleaned_parameter = {}

    # Indian climate patterns by region (average monthly ranges)
    indian_climate_patterns = {
        'northern': {'minTemp': 12, 'maxTemp': 35, 'avgRain': 45, 'avgHumidity': 65},
        'central': {'minTemp': 18, 'maxTemp': 38, 'avgRain': 52, 'avgHumidity': 68},
        'southern': {'minTemp': 22, 'maxTemp': 32, 'avgRain': 65, 'avgHumidity': 75},
        'coastal': {'minTemp': 20, 'maxTemp': 30, 'avgRain': 85, 'avgHumidity': 80},
    }

    # Determine region based on latitude
    if latitude > 28:
        climate_region = 'northern'
    elif latitude > 20:
        climate_region = 'central'
    elif latitude > 13:
        climate_region = 'southern'
    else:
        climate_region = 'southern'

    region_climate = indian_climate_patterns[climate_region]

    # Process each parameter
    for param_name, param_data in parameter.items():
        cleaned_parameter[param_name] = {}

        for date_key, value in param_data.items():
            cleaned_value = value

            # Remove -999 (NASA's missing data placeholder) and other invalid values
            if value == -999 or value < -500:
                # Use realistic defaults for Indian climate
                if param_name == 'T2M':
                    cleaned_value = round((region_climate['minTemp'] + region_climate['maxTemp']) / 2, 2)
                elif param_name == 'T2M_MAX':
                    cleaned_value = region_climate['maxTemp']
                elif param_name == 'T2M_MIN':
                    cleaned_value = region_climate['minTemp']
                elif param_name == 'PRECTOTCORR':
                    cleaned_value = round(region_climate['avgRain'] / 30, 2)  # Convert monthly to daily
                elif param_name == 'RH2M':
                    cleaned_value = region_climate['avgHumidity']
                elif param_name == 'ALLSKY_SFC_SW_DWN':
                    cleaned_value = 18.0  # Average solar radiation in MJ/m² for India
                else:
                    cleaned_value = 0.0
            # Validate reasonable ranges for India
            else:
                if param_name in ['T2M', 'T2M_MAX', 'T2M_MIN']:
                    # India temperature range: -10°C to 50°C (extremes), typically 5-45°C
                    cleaned_value = max(-10, min(50, value))
                elif param_name == 'PRECTOTCORR':
                    # Precipitation: max ~200mm/day in monsoon season
                    cleaned_value = max(0, min(200, value))
                elif param_name == 'RH2M':
                    # Humidity: 0-100%
                    cleaned_value = max(0, min(100, value))
                elif param_name == 'ALLSKY_SFC_SW_DWN':
                    # Solar radiation: 0-30 MJ/m²
                    cleaned_value = max(0, min(30, value))
                else:
                    cleaned_value = value

            cleaned_parameter[param_name][date_key] = round(float(cleaned_value), 2)

    return {
        **api_data,
        'properties': {
            **api_data['properties'],
            'parameter': cleaned_parameter,
            'data_quality': {
                'status': 'validated',
                'missing_data_filled': True,
                'region_climate': climate_region,
                'note': 'Values validated against realistic Indian climate patterns'
            }
        }
    }

# Register soil prediction blueprint
try:
    from soil_prediction_routes import soil_bp
    app.register_blueprint(soil_bp)
    print("✅ Soil prediction routes registered")
except ImportError as e:
    print(f"⚠️ Could not register soil prediction routes: {e}")

# Import and initialize ML inference
try:
    from crop_ml_inference import get_ml_inference
    ml_inference = get_ml_inference()
    print("✅ ML inference engine initialized")
except ImportError as e:
    print(f"⚠️ ML inference not available: {e}")
    ml_inference = None

@app.route('/api/top-3-crops', methods=['POST'])
def get_top_3_crops():
    """
    Fast endpoint to get top 3 recommended crops using ML models
    Uses ensemble of trained models for quick prediction
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        field_data = data.get('field_data', {})
        
        if not field_data:
            return jsonify({"error": "Field data is required"}), 400
        
        # Check if ML models are available
        if not ml_inference or not ml_inference.models_available:
            return jsonify({
                "error": "ML models not available",
                "message": "Top 3 crops ML endpoint unavailable. Please use full crop recommendations."
            }), 503
        
        # Prepare features for ML model
        input_features = {
            'N': float(field_data.get('nitrogen', 75)),
            'P': float(field_data.get('phosphorus', 28)),
            'K': float(field_data.get('potassium', 51)),
            'temperature': float(field_data.get('temperature', 25)),
            'humidity': float(field_data.get('humidity', 65)),
            'pH': float(field_data.get('soil_ph', 6.5)),
            'rainfall': float(field_data.get('rainfall', 1000))
        }
        
        # Get top 3 crops from ML model
        top_3_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
        
        if not top_3_crops:
            return jsonify({
                "error": "Could not generate predictions",
                "message": "ML model prediction failed"
            }), 500
        
        # Format response
        recommended_crops = [
            {
                "name": crop_name,
                "confidence": confidence,
                "rank": idx + 1
            }
            for idx, (crop_name, confidence) in enumerate(top_3_crops)
        ]
        
        response = {
            "status": "success",
            "method": "fast_ml_ensemble",
            "recommended_crops": recommended_crops,
            "field_info": {
                "location": field_data.get('location'),
                "area": field_data.get('area'),
                "fertility_level": field_data.get('fertility_level')
            },
            "ensemble_details": {
                "model_predictions": ensemble_results.get('model_specific_predictions', {}),
                "top_3": top_3_crops
            },
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Top 3 crops generated: {[c['name'] for c in recommended_crops]}")
        return jsonify(response), 200
    
    except Exception as e:
        print(f"❌ Error in top-3-crops endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
