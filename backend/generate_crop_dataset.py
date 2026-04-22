"""
Realistic Crop Recommendation Dataset Generator
Based on popular Kaggle "Crop Recommendation Dataset"
Generates training data with features that influence crop suitability
Features: N (Nitrogen), P (Phosphorus), K (Potassium), Temperature, Humidity, pH, Rainfall
Target: Best crop for those conditions
"""

import numpy as np
import pandas as pd
from datetime import datetime

class CropDatasetGenerator:
    """Generate realistic crop recommendation dataset"""
    
    CROPS = [
        'Rice', 'Wheat', 'Corn', 'Cotton', 'Sugarcane', 'Soybean', 
        'Groundnut', 'Gram', 'Sugarbeet', 'Tomato', 'Onion',
        'Pulses', 'Barley', 'Millet', 'Maize'
    ]
    
    # Crop-specific optimal conditions
    CROP_PROFILES = {
        'Rice': {
            'N_range': (40, 120), 'P_range': (20, 40), 'K_range': (40, 60),
            'temp_range': (25, 35), 'humidity_range': (70, 100), 'pH_range': (5.5, 7.5),
            'rainfall_range': (600, 2100)
        },
        'Wheat': {
            'N_range': (40, 100), 'P_range': (20, 40), 'K_range': (40, 60),
            'temp_range': (15, 25), 'humidity_range': (40, 70), 'pH_range': (6.0, 8.0),
            'rainfall_range': (200, 400)
        },
        'Corn': {
            'N_range': (60, 150), 'P_range': (20, 40), 'K_range': (40, 80),
            'temp_range': (20, 30), 'humidity_range': (50, 80), 'pH_range': (5.5, 8.0),
            'rainfall_range': (300, 600)
        },
        'Cotton': {
            'N_range': (60, 120), 'P_range': (20, 40), 'K_range': (40, 80),
            'temp_range': (25, 35), 'humidity_range': (40, 70), 'pH_range': (6.0, 8.0),
            'rainfall_range': (400, 800)
        },
        'Sugarcane': {
            'N_range': (100, 200), 'P_range': (40, 80), 'K_range': (80, 120),
            'temp_range': (21, 27), 'humidity_range': (60, 90), 'pH_range': (5.5, 8.0),
            'rainfall_range': (600, 1500)
        },
        'Soybean': {
            'N_range': (20, 80), 'P_range': (20, 40), 'K_range': (40, 60),
            'temp_range': (20, 30), 'humidity_range': (50, 80), 'pH_range': (6.0, 7.5),
            'rainfall_range': (400, 600)
        },
        'Groundnut': {
            'N_range': (20, 60), 'P_range': (10, 30), 'K_range': (30, 50),
            'temp_range': (24, 28), 'humidity_range': (40, 70), 'pH_range': (5.5, 7.5),
            'rainfall_range': (350, 500)
        },
        'Gram': {
            'N_range': (20, 60), 'P_range': (15, 35), 'K_range': (30, 50),
            'temp_range': (15, 25), 'humidity_range': (40, 70), 'pH_range': (5.8, 8.0),
            'rainfall_range': (200, 350)
        },
        'Sugarbeet': {
            'N_range': (100, 150), 'P_range': (40, 60), 'K_range': (60, 100),
            'temp_range': (15, 25), 'humidity_range': (50, 80), 'pH_range': (6.5, 8.0),
            'rainfall_range': (300, 600)
        },
        'Tomato': {
            'N_range': (60, 120), 'P_range': (20, 40), 'K_range': (40, 80),
            'temp_range': (21, 28), 'humidity_range': (60, 90), 'pH_range': (6.0, 7.5),
            'rainfall_range': (300, 500)
        },
        'Onion': {
            'N_range': (60, 120), 'P_range': (20, 40), 'K_range': (40, 80),
            'temp_range': (15, 25), 'humidity_range': (50, 80), 'pH_range': (6.0, 7.5),
            'rainfall_range': (200, 400)
        },
        'Pulses': {
            'N_range': (20, 60), 'P_range': (15, 35), 'K_range': (30, 50),
            'temp_range': (15, 25), 'humidity_range': (40, 70), 'pH_range': (5.5, 8.0),
            'rainfall_range': (200, 400)
        },
        'Barley': {
            'N_range': (40, 80), 'P_range': (15, 35), 'K_range': (30, 50),
            'temp_range': (15, 25), 'humidity_range': (40, 70), 'pH_range': (6.0, 8.0),
            'rainfall_range': (250, 400)
        },
        'Millet': {
            'N_range': (30, 70), 'P_range': (10, 30), 'K_range': (20, 40),
            'temp_range': (25, 35), 'humidity_range': (30, 60), 'pH_range': (5.5, 8.0),
            'rainfall_range': (300, 700)
        },
        'Maize': {
            'N_range': (60, 150), 'P_range': (20, 40), 'K_range': (40, 80),
            'temp_range': (20, 30), 'humidity_range': (50, 80), 'pH_range': (5.5, 8.0),
            'rainfall_range': (300, 600)
        }
    }
    
    @staticmethod
    def generate_dataset(n_samples=2200):
        """Generate synthetic crop recommendation dataset"""
        
        data = []
        
        # Generate samples with higher probability near crop's optimal ranges
        samples_per_crop = n_samples // len(CropDatasetGenerator.CROPS)
        
        for crop in CropDatasetGenerator.CROPS:
            profile = CropDatasetGenerator.CROP_PROFILES[crop]
            
            for _ in range(samples_per_crop):
                # Generate values with some randomness around optimal ranges
                N = np.random.normal(
                    (profile['N_range'][0] + profile['N_range'][1]) / 2,
                    15
                )
                P = np.random.normal(
                    (profile['P_range'][0] + profile['P_range'][1]) / 2,
                    5
                )
                K = np.random.normal(
                    (profile['K_range'][0] + profile['K_range'][1]) / 2,
                    10
                )
                temperature = np.random.normal(
                    (profile['temp_range'][0] + profile['temp_range'][1]) / 2,
                    2
                )
                humidity = np.random.normal(
                    (profile['humidity_range'][0] + profile['humidity_range'][1]) / 2,
                    8
                )
                pH = np.random.normal(
                    (profile['pH_range'][0] + profile['pH_range'][1]) / 2,
                    0.3
                )
                rainfall = np.random.normal(
                    (profile['rainfall_range'][0] + profile['rainfall_range'][1]) / 2,
                    50
                )
                
                # Clamp to realistic ranges
                N = np.clip(N, 0, 200)
                P = np.clip(P, 0, 100)
                K = np.clip(K, 0, 100)
                temperature = np.clip(temperature, 5, 45)
                humidity = np.clip(humidity, 20, 100)
                pH = np.clip(pH, 4, 10)
                rainfall = np.clip(rainfall, 20, 2500)
                
                data.append({
                    'N': round(N, 2),
                    'P': round(P, 2),
                    'K': round(K, 2),
                    'temperature': round(temperature, 2),
                    'humidity': round(humidity, 2),
                    'pH': round(pH, 2),
                    'rainfall': round(rainfall, 2),
                    'crop': crop
                })
        
        # Shuffle and create DataFrame
        df = pd.DataFrame(data)
        df = df.sample(frac=1).reset_index(drop=True)
        
        return df
    
    @staticmethod
    def save_dataset(df, filename='crop_recommendation_dataset.csv'):
        """Save dataset to CSV file"""
        df.to_csv(filename, index=False)
        print(f"[+] Dataset saved to {filename}")
        print(f"    Shape: {df.shape}")
        print(f"    Columns: {df.columns.tolist()}")
        print(f"\nDataset Summary:")
        print(df.groupby('crop').size())
        return filename


# Generate and save the dataset
if __name__ == '__main__':
    print("=" * 60)
    print("Generating Crop Recommendation Dataset")
    print("(Based on Kaggle Crop Recommendation Dataset)")
    print("=" * 60)
    print()
    
    # Generate 2200 samples (150 per crop roughly)
    df = CropDatasetGenerator.generate_dataset(n_samples=2200)
    
    print("\nDataset Preview:")
    print(df.head(10))
    print()
    
    # Save dataset
    CropDatasetGenerator.save_dataset(df)
    
    print("\n[✓] Dataset generation complete!")
    print("Use this dataset to train crop recommendation models")
