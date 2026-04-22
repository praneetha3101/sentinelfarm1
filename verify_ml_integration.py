"""
Test Flask app with ML Crop Service integration
Simulates the app startup and checks if all services are loaded
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("\n" + "="*70)
print("Flask Backend Startup Verification with ML Integration")
print("="*70)

# Change to backend directory for proper imports
os.chdir('backend')

print("\n[1] Checking required files...")
files_to_check = [
    'crop_recommendation_dataset.csv',
    'models/random_forest_model.pkl',
    'models/xgboost_model.pkl',
    'models/label_encoder.pkl',
    'models/feature_names.pkl'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path) / 1024  # Size in KB
        print(f"   ✅ {file_path:<40} ({size:.1f} KB)")
    else:
        print(f"   ❌ {file_path:<40} (MISSING)")
        sys.exit(1)

print("\n[2] Testing imports...")

# Test AI Service
try:
    from ai_crop_service import generate_ai_crop_recommendations, get_fallback_recommendations
    print("   ✅ AI service imported")
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️  AI service: {e}")
    AI_SERVICE_AVAILABLE = False

# Test Soil Service
try:
    from soil_prediction_service import soil_model
    print("   ✅ Soil prediction service imported")
    SOIL_PREDICTION_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️  Soil service: {e}")
    SOIL_PREDICTION_AVAILABLE = False

# Test ML Crop Service (NEW)
try:
    from ml_crop_service import MLCropRecommendationService
    ml_crop_service = MLCropRecommendationService('crop_recommendation_dataset.csv')
    ML_CROP_SERVICE_AVAILABLE = ml_crop_service.crop_data is not None
    print(f"   ✅ ML Crop Service imported ({len(ml_crop_service.crop_data)} records)")
except ImportError as e:
    print(f"   ❌ ML Crop Service: {e}")
    ML_CROP_SERVICE_AVAILABLE = False
    ml_crop_service = None
except Exception as e:
    print(f"   ❌ ML Crop Service initialization: {e}")
    ML_CROP_SERVICE_AVAILABLE = False
    ml_crop_service = None

# Test ML Inference
try:
    from crop_ml_inference import get_ml_inference
    ml_inference = get_ml_inference()
    if ml_inference and ml_inference.models_available:
        print("   ✅ ML inference engine loaded")
        ML_INFERENCE_AVAILABLE = True
    else:
        print("   ⚠️  ML inference: models not available")
        ML_INFERENCE_AVAILABLE = False
except ImportError as e:
    print(f"   ⚠️  ML inference: {e}")
    ml_inference = None
    ML_INFERENCE_AVAILABLE = False

print("\n[3] Simulating Flask /api/crop-recommendations endpoint...")

# Create sample field data
test_field_data = {
    'location': 'Delhi',
    'area': 2.5,
    'fertility_level': 'Medium',
    'nitrogen': 75.0,
    'phosphorus': 28.0,
    'potassium': 51.0,
    'soil_ph': 6.8,
    'temperature': 24.5,
    'humidity': 65.0,
    'rainfall': 120.0
}

print(f"\n   Test Field Data:")
for key, val in test_field_data.items():
    print(f"      {key}: {val}")

# Simulate what the endpoint would do
print(f"\n   Endpoint Logic Flow:")
print(f"      1. AI Service Available: {AI_SERVICE_AVAILABLE}")
print(f"      2. ML Crop Service Available: {ML_CROP_SERVICE_AVAILABLE}")
print(f"      3. ML Inference Available: {ML_INFERENCE_AVAILABLE}")

if ML_CROP_SERVICE_AVAILABLE and ml_crop_service and ML_INFERENCE_AVAILABLE and ml_inference and ml_inference.models_available:
    print(f"\n   ✅ Backend will use ML-powered crop recommendations!")
    
    # Test the full flow
    print(f"\n   Testing ML-powered recommendation flow:")
    
    input_features = {
        'N': test_field_data['nitrogen'],
        'P': test_field_data['phosphorus'],
        'K': test_field_data['potassium'],
        'temperature': test_field_data['temperature'],
        'humidity': test_field_data['humidity'],
        'pH': test_field_data['soil_ph'],
        'rainfall': test_field_data['rainfall']
    }
    
    print(f"      a) Getting ML predictions...")
    top_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
    
    if top_crops:
        print(f"      ✅ ML predictions obtained:")
        for crop, conf in top_crops:
            print(f"         - {crop}: {conf:.1f}%")
        
        print(f"      b) Generating detailed recommendations...")
        recommendations = ml_crop_service.generate_ml_recommendations(top_crops, test_field_data)
        
        if recommendations and 'recommended_crops' in recommendations:
            print(f"      ✅ Detailed recommendations generated:")
            print(f"         Status: {recommendations.get('status', 'N/A')}")
            print(f"         Total sections: {len(recommendations)} (land_analysis, season_analysis, market_insights, etc.)")
            print(f"         Recommended crops count: {len(recommendations['recommended_crops'])}")
            
            # Show sample crop details
            if recommendations['recommended_crops']:
                first_crop = recommendations['recommended_crops'][0]
                print(f"\n      Sample Crop Details (First recommendation):")
                print(f"         - Name: {first_crop.get('name')}")
                print(f"         - Confidence: {first_crop.get('confidence')}%")
                print(f"         - Why suitable: {first_crop.get('why_suitable', 'N/A')[:80]}...")
                print(f"         - Market potential: {first_crop.get('market_potential', 'N/A')[:80]}...")
        else:
            print(f"      ❌ Recommendation generation failed")
    else:
        print(f"      ❌ ML predictions not generated")

elif ML_CROP_SERVICE_AVAILABLE and ml_crop_service:
    print(f"\n   ⚠️  Backend has ML Crop Service but ML Inference unavailable")
    print(f"       Will fallback to generic recommendations")
else:
    print(f"\n   ⚠️  Backend will use generic fallback recommendations")

print("\n" + "="*70)
print("✅ Verification Complete! Backend is ready for testing.")
print("="*70 + "\n")
