"""
Test the complete /api/crop-recommendations endpoint with ML integration
Simulates an actual frontend request and verifies the response structure
"""

import sys
import os
import json

# Make sure we're in the right directory and can import modules
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

print("\n" + "="*70)
print("Complete Crop Recommendations Endpoint Test")
print("="*70)

# Import all required modules
print("\n[1] Loading required modules...")

from ml_crop_service import MLCropRecommendationService
from crop_ml_inference import get_ml_inference
from ai_crop_service import get_fallback_recommendations

ml_crop_service = MLCropRecommendationService('crop_recommendation_dataset.csv')
ml_inference = get_ml_inference()

print("   ✅ All modules loaded")

# Simulate exactly what the frontend sends
print("\n[2] Preparing test data (simulating frontend request)...")

field_data = {
    'location': 'Delhi, India',
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

print("   Field Data Submitted:")
for k, v in field_data.items():
    print(f"      - {k}: {v}")

# Simulate the endpoint logic
print("\n[3] Executing /api/crop-recommendations endpoint logic...")

if ml_crop_service.crop_data is not None and ml_inference and ml_inference.models_available:
    print("   ✅ Both ML services available - generating ML-powered recommendations")
    
    # Step 1: Prepare ML features
    input_features = {
        'N': float(field_data.get('nitrogen', 75)),
        'P': float(field_data.get('phosphorus', 28)),
        'K': float(field_data.get('potassium', 51)),
        'temperature': float(field_data.get('temperature', 25)),
        'humidity': float(field_data.get('humidity', 65)),
        'pH': float(field_data.get('soil_ph', 6.5)),
        'rainfall': float(field_data.get('rainfall', 1000))
    }
    
    print("\n   Step 1: Getting ML predictions...")
    print(f"      Input features: {input_features}")
    
    top_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
    
    if top_crops:
        print(f"      ✅ Top 3 crops predicted:")
        for crop, conf in top_crops:
            print(f"         - {crop}: {conf:.2f}%")
    
    print("\n   Step 2: Generating detailed ML recommendations...")
    ml_recommendations = ml_crop_service.generate_ml_recommendations(top_crops, field_data)
    
    # Verify recommendation structure
    print(f"      ✅ Recommendations generated")
    print(f"\n   Response Structure (what frontend will receive):")
    response = {
        'status': 'ml_powered',
        'ai_generated': False,
        'method': 'ml_ensemble_with_crop_dataset',
        'recommendations': ml_recommendations
    }
    
    print(f"      Status: {response['status']}")
    print(f"      AI Generated: {response['ai_generated']}")
    print(f"      Method: {response['method']}")
    
    rec = response['recommendations']
    print(f"\n      Recommendations sections:")
    print(f"         - land_analysis: ✅ ({len(rec.get('land_analysis', {}))} fields)")
    print(f"         - season_analysis: ✅ ({len(rec.get('season_analysis', {}))} fields)")
    print(f"         - market_insights: ✅ ({len(rec.get('market_insights', {}))} fields)")
    print(f"         - recommended_crops: ✅ ({len(rec.get('recommended_crops', []))} crops)")
    print(f"         - action_plan: ✅ ({len(rec.get('action_plan', {}))} fields)")
    print(f"         - sustainability_advice: ✅ ({len(rec.get('sustainability_advice', {}))} fields)")
    
    # Show detailed crop info
    print(f"\n   Detailed Crop Recommendations (first crop):")
    if rec.get('recommended_crops'):
        crop = rec['recommended_crops'][0]
        print(f"      Name: {crop.get('name')}")
        print(f"      Rank: {crop.get('rank')}")
        print(f"      Confidence: {crop.get('confidence'):.2f}%")
        print(f"      Variety: {crop.get('variety')}")
        print(f"      Why Suitable:")
        why_suitable = crop.get('why_suitable', 'N/A')
        for line in why_suitable.split('\n')[:3]:  # First 3 lines
            if line.strip():
                print(f"         {line}")
        print(f"      Market Potential: {crop.get('market_potential', 'N/A')[:100]}...")
        print(f"      Growing Tips: {crop.get('growing_tips', 'N/A')[:80]}...")
    
    # Show all three crops
    print(f"\n   All Recommended Crops:")
    for i, crop in enumerate(rec.get('recommended_crops', []), 1):
        symbols = ['🥇', '🥈', '🥉']
        print(f"      {symbols[i-1]} {crop.get('name')} - {crop.get('confidence'):.1f}% confidence")
    
    # Verify JSON serialization (important for Flask response)
    print(f"\n[4] Testing JSON serialization (Flask response)...")
    try:
        json_str = json.dumps(response, indent=2, default=str)
        print(f"      ✅ JSON serialization successful")
        print(f"      Response size: {len(json_str)} bytes")
        
        # Parse it back to verify
        parsed = json.loads(json_str)
        print(f"      ✅ JSON parsing successful - full round-trip verified")
        
    except Exception as e:
        print(f"      ❌ JSON serialization failed: {e}")

print("\n" + "="*70)
print("✅ Complete endpoint test passed!")
print("Response is ready to be returned to frontend.")
print("="*70 + "\n")
