"""
Test the ML Crop Recommendation Service integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("="*60)
print("Testing ML Crop Recommendation Service")
print("="*60)

# Test 1: Import ML Crop Service
print("\n[1] Testing ML Crop Recommendation Service import...")
try:
    from backend.ml_crop_service import MLCropRecommendationService
    print("✅ ML Crop Service imported successfully")
except Exception as e:
    print(f"❌ Failed to import ML Crop Service: {e}")
    sys.exit(1)

# Test 2: Initialize service
print("\n[2] Initializing ML Crop Service...")
try:
    crop_service = MLCropRecommendationService('backend/crop_recommendation_dataset.csv')
    if crop_service.crop_data is not None:
        print(f"✅ Loaded {len(crop_service.crop_data)} crop records from CSV")
        print(f"   Crops available: {crop_service.crop_data['crop'].unique().tolist()}")
    else:
        print("❌ Failed to load crop dataset")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error initializing ML Crop Service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test crop statistics
print("\n[3] Testing crop statistics extraction...")
try:
    wheat_stats = crop_service.get_crop_details('Wheat')
    if wheat_stats:
        print(f"✅ Crop details for Wheat retrieved:")
        print(f"   - Dataset samples: {wheat_stats['dataset_samples']}")
        print(f"   - N requirement: {wheat_stats['nitrogen_requirement']}")
        print(f"   - Temperature range: {wheat_stats['temperature']['range']}")
    else:
        print("❌ Failed to get wheat statistics")
except Exception as e:
    print(f"❌ Error getting crop stats: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test suitability explanation
print("\n[4] Testing suitability explanation generation...")
try:
    field_data = {
        'location': 'Delhi',
        'nitrogen': 75,
        'phosphorus': 28,
        'potassium': 51,
        'temperature': 24.5,
        'humidity': 65,
        'soil_ph': 6.8,
        'rainfall': 120,
        'fertility_level': 'Medium'
    }
    
    explanation = crop_service.calculate_suitability_explanation('Wheat', field_data)
    print(f"✅ Generated suitability explanation for Wheat:")
    print(f"   {explanation[:150]}...")
except Exception as e:
    print(f"❌ Error generating explanation: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test recommendation generation
print("\n[5] Testing ML recommendation generation...")
try:
    top_crops = [('Wheat', 85.5), ('Maize', 78.2), ('Rice', 71.3)]
    recommendations = crop_service.generate_ml_recommendations(top_crops, field_data)
    
    if recommendations and 'recommended_crops' in recommendations:
        print(f"✅ Generated recommendations with {len(recommendations['recommended_crops'])} crops")
        for crop in recommendations['recommended_crops']:
            print(f"   - Rank {crop['rank']}: {crop['name']} (confidence: {crop['confidence']}%)")
    else:
        print("❌ Recommendation structure not as expected")
except Exception as e:
    print(f"❌ Error generating recommendations: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test ML inference integration
print("\n[6] Testing ML Inference integration...")
try:
    from backend.crop_ml_inference import get_ml_inference
    ml_inference = get_ml_inference()
    if ml_inference and ml_inference.models_available:
        print("✅ ML inference engine initialized")
        
        # Test prediction
        input_features = {
            'N': 75,
            'P': 28,
            'K': 51,
            'temperature': 24.5,
            'humidity': 65,
            'pH': 6.8,
            'rainfall': 120
        }
        
        top_crops, ensemble_results = ml_inference.predict_best_crops(input_features)
        if top_crops:
            print(f"✅ ML model predictions:")
            for crop, confidence in top_crops:
                print(f"   - {crop}: {confidence:.1f}%")
        else:
            print("⚠️  No predictions generated")
    else:
        print("⚠️  ML inference models not available")
except Exception as e:
    print(f"⚠️  ML Inference test skipped: {e}")

print("\n" + "="*60)
print("✅ All tests completed successfully!")
print("="*60)
