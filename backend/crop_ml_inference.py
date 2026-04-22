"""
ML Model Inference Service
Loads trained crop recommendation models and provides predictions
Handles model loading, prediction, and confidence scoring
"""

import pickle
import os
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class CropModelInference:
    """Inference engine for trained crop recommendation models"""
    
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        self.models = {}
        self.label_encoder = None
        self.feature_names = None
        self.metadata = None
        self.models_available = False
        
        # Try to load models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        if not os.path.exists(self.model_dir):
            print(f"[!] Model directory not found: {self.model_dir}")
            return False
        
        try:
            # Load label encoder
            encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
            else:
                print(f"[!] Label encoder not found")
                return False
            
            # Load feature names
            features_path = os.path.join(self.model_dir, 'feature_names.pkl')
            if os.path.exists(features_path):
                with open(features_path, 'rb') as f:
                    self.feature_names = pickle.load(f)
            else:
                print(f"[!] Feature names not found")
                return False
            
            # Load models
            model_files = {
                'random_forest': 'random_forest_model.pkl',
                'xgboost': 'xgboost_model.pkl',
                'gradient_boosting': 'gradient_boosting_model.pkl'
            }
            
            for model_name, model_file in model_files.items():
                model_path = os.path.join(self.model_dir, model_file)
                if os.path.exists(model_path):
                    try:
                        with open(model_path, 'rb') as f:
                            self.models[model_name] = pickle.load(f)
                        print(f"[+] Loaded {model_name}")
                    except Exception as e:
                        print(f"[!] Failed to load {model_name}: {e}")
            
            # Load metadata
            metadata_path = os.path.join(self.model_dir, 'metadata.pkl')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            
            if len(self.models) > 0:
                self.models_available = True
                print(f"[✓] ML models loaded successfully ({len(self.models)} models)")
                return True
            else:
                print("[!] No models found")
                return False
        
        except Exception as e:
            print(f"[!] Error loading models: {e}")
            return False
    
    def predict_best_crops(self, input_features: Dict) -> Tuple[List[Tuple[str, float]], Dict]:
        """
        Predict top 3 best crops for given field conditions
        
        Args:
            input_features: Dict with keys: N, P, K, temperature, humidity, pH, rainfall
        
        Returns:
            Tuple of ([(crop_name, confidence), ...], ensemble_predictions)
        """
        
        if not self.models_available:
            return None, None
        
        try:
            # Prepare feature array
            feature_array = np.array([
                input_features.get('N', 50),
                input_features.get('P', 30),
                input_features.get('K', 40),
                input_features.get('temperature', 25),
                input_features.get('humidity', 60),
                input_features.get('pH', 6.5),
                input_features.get('rainfall', 500)
            ]).reshape(1, -1)
            
            # Get predictions from all available models
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.models.items():
                try:
                    # Get class prediction
                    pred = model.predict(feature_array)[0]
                    pred_label = self.label_encoder.inverse_transform([pred])[0]
                    predictions[model_name] = pred_label
                    
                    # Get probabilities
                    if hasattr(model, 'predict_proba'):
                        probs = model.predict_proba(feature_array)[0]
                        probabilities[model_name] = {
                            self.label_encoder.classes_[i]: probs[i]
                            for i in range(len(self.label_encoder.classes_))
                        }
                except Exception as e:
                    print(f"[!] Prediction error with {model_name}: {e}")
            
            # Ensemble: Average probabilities from all models
            ensemble_probs = {}
            for crop in self.label_encoder.classes_:
                scores = []
                for model_name, probs in probabilities.items():
                    scores.append(probs.get(crop, 0))
                ensemble_probs[crop] = np.mean(scores)
            
            # Get top 3 crops
            top_3 = sorted(
                ensemble_probs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Convert confidence to percentage
            top_3_with_confidence = [
                (crop, round(conf * 100, 2))
                for crop, conf in top_3
            ]
            
            ensemble_results = {
                'top_3': top_3_with_confidence,
                'all_predictions': ensemble_probs,
                'model_specific_predictions': predictions,
                'model_probabilities': probabilities
            }
            
            return top_3_with_confidence, ensemble_results
        
        except Exception as e:
            print(f"[!] Prediction error: {e}")
            return None, None
    
    def predict_all_crops_ranked(self, input_features: Dict) -> List[Tuple[str, float]]:
        """
        Get all crops ranked by suitability for given conditions
        
        Returns:
            List of (crop_name, confidence_score) sorted by confidence
        """
        
        if not self.models_available:
            return []
        
        try:
            # Prepare feature array
            feature_array = np.array([
                input_features.get('N', 50),
                input_features.get('P', 30),
                input_features.get('K', 40),
                input_features.get('temperature', 25),
                input_features.get('humidity', 60),
                input_features.get('pH', 6.5),
                input_features.get('rainfall', 500)
            ]).reshape(1, -1)
            
            # Get ensemble probabilities from best model
            best_model_name = max(self.models.keys(), default='random_forest')
            best_model = self.models[best_model_name]
            
            if hasattr(best_model, 'predict_proba'):
                probs = best_model.predict_proba(feature_array)[0]
                
                # Create crop-probability pairs
                crop_probs = [
                    (self.label_encoder.classes_[i], probs[i] * 100)
                    for i in range(len(self.label_encoder.classes_))
                ]
                
                # Sort by probability
                crop_probs.sort(key=lambda x: x[1], reverse=True)
                
                return crop_probs
            else:
                return []
        
        except Exception as e:
            print(f"[!] Error getting ranked predictions: {e}")
            return []
    
    def get_metadata(self) -> Dict:
        """Return model metadata"""
        return self.metadata if self.metadata else {}


# Global inference engine instance
crop_model_inference = None

def initialize_ml_inference(model_dir='models'):
    """Initialize the ML inference engine"""
    global crop_model_inference
    crop_model_inference = CropModelInference(model_dir)
    return crop_model_inference

def get_ml_inference():
    """Get the ML inference engine instance"""
    global crop_model_inference
    if crop_model_inference is None:
        crop_model_inference = CropModelInference()
    return crop_model_inference
