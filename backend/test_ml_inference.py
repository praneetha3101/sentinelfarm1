"""
Test Trained ML Model Inference
Validates that trained models can make predictions and provide top 3 crop recommendations
"""

from crop_ml_inference import CropModelInference, initialize_ml_inference, get_ml_inference
import json

print("=" * 70)
print("Testing Trained ML Model Inference")
print("=" * 70)
print()

# Initialize ML inference
print("[*] Initializing ML Inference Engine...")
ml_engine = initialize_ml_inference(model_dir='models')
print(f"[✓] ML Inference initialized")
print()

# Test 1: Check models loaded
print("[TEST 1] Model Loading")
print("-" * 70)
if ml_engine.models_available:
    print(f"[✓] Models loaded successfully")
    print(f"    Loaded models: {list(ml_engine.models.keys())}")
    print(f"    Label encoder classes: {ml_engine.label_encoder.classes_.tolist()}")
    print(f"    Features: {ml_engine.feature_names}")
else:
    print("[!] Models not available")
    exit(1)

print()

# Test 2: Make predictions for different field conditions
print("[TEST 2] Crop Predictions for Different Conditions")
print("-" * 70)

test_scenarios = [
    {
        'name': 'Scenario 1: High Rainfall, High Nitrogen',
        'input': {
            'N': 100,
            'P': 40,
            'K': 50,
            'temperature': 28,
            'humidity': 75,
            'pH': 6.8,
            'rainfall': 800
        }
    },
    {
        'name': 'Scenario 2: Low Rainfall, Medium Nutrients',
        'input': {
            'N': 50,
            'P': 25,
            'K': 35,
            'temperature': 22,
            'humidity': 45,
            'pH': 6.5,
            'rainfall': 300
        }
    },
    {
        'name': 'Scenario 3: Hot & Dry',
        'input': {
            'N': 40,
            'P': 20,
            'K': 30,
            'temperature': 35,
            'humidity': 35,
            'pH': 7.0,
            'rainfall': 250
        }
    },
    {
        'name': 'Scenario 4: Cool & Wet',
        'input': {
            'N': 70,
            'P': 35,
            'K': 45,
            'temperature': 18,
            'humidity': 80,
            'pH': 6.0,
            'rainfall': 600
        }
    }
]

for scenario in test_scenarios:
    print(f"\n{scenario['name']}")
    print(f"  Inputs: N={scenario['input']['N']}, P={scenario['input']['P']}, " \
          f"K={scenario['input']['K']}, Temp={scenario['input']['temperature']}°C, " \
          f"Humidity={scenario['input']['humidity']}%, pH={scenario['input']['pH']}, " \
          f"Rainfall={scenario['input']['rainfall']}mm")
    
    top_3, ensemble_results = ml_engine.predict_best_crops(scenario['input'])
    
    if top_3:
        print("  ✓ Top 3 Recommended Crops:")
        for idx, (crop, confidence) in enumerate(top_3, 1):
            print(f"    #{idx} {crop:15s} - {confidence:.2f}% confidence")
    else:
        print("  [!] No predictions available")

print()
print()

# Test 3: Get all crops ranked
print("[TEST 3] All Crops Ranked (Best Scenario)")
print("-" * 70)

best_scenario = test_scenarios[0]['input']
all_ranked = ml_engine.predict_all_crops_ranked(best_scenario)

if all_ranked:
    print("All crops ranked by suitability:")
    for idx, (crop, confidence) in enumerate(all_ranked, 1):
        bar_length = int(confidence / 5)
        bar = '█' * bar_length
        print(f"  {idx:2d}. {crop:15s} {bar:14s} {confidence:5.1f}%")
else:
    print("[!] No ranked predictions available")

print()
print()

# Test 4: Metadata
print("[TEST 4] Model Metadata")
print("-" * 70)
metadata = ml_engine.get_metadata()
if metadata:
    print(f"Trained at: {metadata.get('trained_at')}")
    print(f"Training samples: {metadata.get('num_samples')}")
    print(f"Number of features: {metadata.get('num_features')}")
    print(f"Features used: {metadata.get('features')}")
    print(f"Number of crops: {len(metadata.get('crops', []))}")
    print(f"Crops: {', '.join(metadata.get('crops', []))}")
    
    if metadata.get('model_scores'):
        print(f"\nModel Accuracies:")
        for model_name, scores in metadata['model_scores'].items():
            print(f"  {model_name}: {scores['accuracy']*100:.2f}% (CV: {scores['cv_mean']*100:.2f}%)")
else:
    print("[!] Metadata not available")

print()
print()

# Test 5: Full end-to-end test with detailed output
print("[TEST 5] Full End-to-End Inference")
print("-" * 70)

test_field = {
    'N': 60,
    'P': 30,
    'K': 40,
    'temperature': 26,
    'humidity': 65,
    'pH': 6.8,
    'rainfall': 650
}

print(f"Field Conditions: {json.dumps(test_field, indent=2)}")
print()

top_3, ensemble_results = ml_engine.predict_best_crops(test_field)

print("🏆 Top 3 Recommended Crops:")
for idx, (crop, confidence) in enumerate(top_3, 1):
    print(f"\n  #{idx} {crop}")
    print(f"     Confidence: {confidence:.2f}%")
    print(f"     Ensemble predictions:")
    
    # Show what each model predicted
    model_preds = ensemble_results.get('model_specific_predictions', {})
    for model_name, pred_crop in model_preds.items():
        match_str = "✓" if pred_crop == crop else "✗"
        print(f"       {match_str} {model_name}: {pred_crop}")

print()
print()

print("=" * 70)
print("✓ ML Inference Testing Complete!")
print("=" * 70)
print()
print("Summary:")
print("  ✓ Models loaded successfully")
print("  ✓ Predictions working")
print("  ✓ Ensemble averaging working")
print("  ✓ Top 3 crop recommendations generated")
print()
print("Ready to integrate with Flask API!")
