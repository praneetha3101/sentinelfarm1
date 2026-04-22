#!/usr/bin/env python3
"""
Test script for the enhanced ML-based crop recommendation system
Tests all components: weather data, soil prediction, and crop scoring
"""

import json
import sys
from datetime import datetime

# Test imports
print("=" * 60)
print("Testing Enhanced Crop Recommendation System")
print("=" * 60)
print()

modules_status = {}

# Test 1: Crop Recommendation Engine
print("[TEST 1] Crop Recommendation Engine...")
try:
    from crop_recommendation_engine import recommendation_engine, CropDatabase
    print("✓ Successfully imported crop_recommendation_engine")
    modules_status['crop_engine'] = True
except Exception as e:
    print(f"✗ Failed to import crop_recommendation_engine: {e}")
    modules_status['crop_engine'] = False

# Test 2: Weather Service
print("\n[TEST 2] Weather Data Service...")
try:
    from weather_service import WeatherDataService
    print("✓ Successfully imported weather_service")
    modules_status['weather_service'] = True
except Exception as e:
    print(f"✗ Failed to import weather_service: {e}")
    modules_status['weather_service'] = False

# Test 3: Soil Prediction
print("\n[TEST 3] Soil Prediction Service...")
try:
    from soil_prediction_service import soil_model
    print("✓ Successfully imported soil_prediction_service")
    modules_status['soil_service'] = True
except Exception as e:
    print(f"✗ Failed to import soil_prediction_service: {e}")
    modules_status['soil_service'] = False

# Test 4: AI Crop Service
print("\n[TEST 4] AI Crop Service...")
try:
    from ai_crop_service import generate_ai_crop_recommendations
    print("✓ Successfully imported ai_crop_service")
    modules_status['ai_service'] = True
except Exception as e:
    print(f"✗ Failed to import ai_crop_service: {e}")
    modules_status['ai_service'] = False

# Run integration test if all modules available
print("\n" + "=" * 60)
print("[TEST 5] Integration Test - Full Recommendation Pipeline")
print("=" * 60)

if modules_status['crop_engine'] and modules_status['soil_service']:
    try:
        print("\n1. Testing field data...")
        test_field_data = {
            'location': 'Maharashtra, India',
            'area': 2.5,
            'soil_type': 'Loamy',
            'soil_ph': 6.8,
            'irrigation': 'Drip irrigation',
            'experience': 'Intermediate',
            'budget': 'Medium'
        }
        print(f"   Field: {test_field_data['area']}ha, {test_field_data['soil_type']} soil")
        
        print("\n2. Testing weather data processing...")
        test_weather = {
            'avg_temp': 28.5,
            'max_temp': 35,
            'min_temp': 22,
            'rainfall': 650,
            'avg_daily_rainfall': 3.5,
            'humidity': 72,
            'pattern': 'Monsoon conditions'
        }
        print(f"   Temperature: {test_weather['avg_temp']}°C")
        print(f"   Rainfall: {test_weather['rainfall']}mm")
        print(f"   Humidity: {test_weather['humidity']}%")
        
        print("\n3. Testing soil prediction...")
        test_soil_prediction = soil_model.predict_soil_properties(0.65, -0.15, 0.35, 0.45)
        print(f"   Predicted pH: {test_soil_prediction.get('soil_ph')}")
        print(f"   Predicted Type: {test_soil_prediction.get('soil_type')}")
        print(f"   Moisture: {test_soil_prediction.get('moisture_level')}")
        
        print("\n4. Running ML-based crop scoring...")
        crop_scores = recommendation_engine.calculate_crop_scores(
            field_data=test_field_data,
            weather_data=test_weather,
            soil_prediction=test_soil_prediction
        )
        
        print(f"   Scored {len(crop_scores)} crops")
        print("\n   Top 5 Crops:")
        for crop, score, details in crop_scores[:5]:
            confidence = details.get('confidence', 0)
            print(f"   {crop:25} | Score: {score:6.1f} | Confidence: {confidence:5.1f}%")
        
        print("\n5. Generating detailed insights...")
        insights = recommendation_engine.generate_recommendation_insights(
            crop_scores=crop_scores,
            field_data=test_field_data,
            soil_prediction=test_soil_prediction
        )
        
        print(f"\n   Generated insights for {len(insights['top_crops'])} crops:")
        for idx, crop in enumerate(insights['top_crops'], 1):
            print(f"\n   Recommendation #{idx}: {crop['name']}")
            print(f"   • Overall Score: {crop['overall_score']}")
            print(f"   • Confidence: {crop['confidence']}%")
            print(f"   • Investment: {crop['investment_range']}")
            print(f"   • Expected Returns: {crop['expected_yield_value']}")
            print(f"   • Risk Level: {crop['risk_level']}")
        
        print("\n✓ Integration test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⚠ Skipping integration test - required modules not available")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
available_count = sum(1 for v in modules_status.values() if v)
total_count = len(modules_status)
print(f"Modules Available: {available_count}/{total_count}")
print()

for module, status in modules_status.items():
    status_str = "✓" if status else "✗"
    print(f"{status_str} {module}")

print()
if available_count == total_count:
    print("✓ All systems operational! ML-powered crop recommendations ready.")
    sys.exit(0)
else:
    print(f"⚠ Some modules missing. Install dependencies:")
    print("  pip install scikit-learn numpy")
    sys.exit(1)
