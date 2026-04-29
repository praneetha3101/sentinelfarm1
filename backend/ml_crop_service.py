"""
ML-Based Crop Recommendation Service
Uses trained ML models and crop dataset CSV to generate detailed crop recommendations
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple


class MLCropRecommendationService:
    """Generate crop recommendations using ML models and CSV dataset"""
    
    def __init__(self, csv_path='crop_recommendation_dataset.csv'):
        self.csv_path = csv_path
        self.crop_data = None
        self.crop_stats = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load and analyze the crop recommendation dataset"""
        try:
            if not os.path.exists(self.csv_path):
                print(f"[!] Dataset not found: {self.csv_path}")
                return False
            
            self.crop_data = pd.read_csv(self.csv_path)
            print(f"[+] Loaded {len(self.crop_data)} records from crop dataset")
            print(f"[+] Crops available: {self.crop_data['crop'].unique().tolist()}")
            
            # Calculate statistics per crop
            self.crop_stats = {}
            for crop in self.crop_data['crop'].unique():
                crop_records = self.crop_data[self.crop_data['crop'] == crop]
                self.crop_stats[crop] = {
                    'count': len(crop_records),
                    'N': {'mean': crop_records['N'].mean(), 'min': crop_records['N'].min(), 'max': crop_records['N'].max()},
                    'P': {'mean': crop_records['P'].mean(), 'min': crop_records['P'].min(), 'max': crop_records['P'].max()},
                    'K': {'mean': crop_records['K'].mean(), 'min': crop_records['K'].min(), 'max': crop_records['K'].max()},
                    'temperature': {'mean': crop_records['temperature'].mean(), 'min': crop_records['temperature'].min(), 'max': crop_records['temperature'].max()},
                    'humidity': {'mean': crop_records['humidity'].mean(), 'min': crop_records['humidity'].min(), 'max': crop_records['humidity'].max()},
                    'pH': {'mean': crop_records['pH'].mean(), 'min': crop_records['pH'].min(), 'max': crop_records['pH'].max()},
                    'rainfall': {'mean': crop_records['rainfall'].mean(), 'min': crop_records['rainfall'].min(), 'max': crop_records['rainfall'].max()}
                }
            
            return True
        
        except Exception as e:
            print(f"[!] Error loading dataset: {e}")
            return False
    
    def get_crop_details(self, crop_name: str) -> Dict:
        """Get detailed information about a crop from the dataset"""
        if not self.crop_stats or crop_name not in self.crop_stats:
            return None
        
        stats = self.crop_stats[crop_name]
        
        return {
            'name': crop_name,
            'dataset_samples': stats['count'],
            'nitrogen_requirement': {
                'mean': round(stats['N']['mean'], 2),
                'range': f"{round(stats['N']['min'], 2)}-{round(stats['N']['max'], 2)} kg/ha"
            },
            'phosphorus_requirement': {
                'mean': round(stats['P']['mean'], 2),
                'range': f"{round(stats['P']['min'], 2)}-{round(stats['P']['max'], 2)} kg/ha"
            },
            'potassium_requirement': {
                'mean': round(stats['K']['mean'], 2),
                'range': f"{round(stats['K']['min'], 2)}-{round(stats['K']['max'], 2)} kg/ha"
            },
            'temperature': {
                'optimal': round(stats['temperature']['mean'], 2),
                'range': f"{round(stats['temperature']['min'], 2)}-{round(stats['temperature']['max'], 2)}°C"
            },
            'humidity': {
                'optimal': round(stats['humidity']['mean'], 2),
                'range': f"{round(stats['humidity']['min'], 2)}-{round(stats['humidity']['max'], 2)}%"
            },
            'pH': {
                'optimal': round(stats['pH']['mean'], 2),
                'range': f"{round(stats['pH']['min'], 2)}-{round(stats['pH']['max'], 2)}"
            },
            'rainfall': {
                'optimal': round(stats['rainfall']['mean'], 2),
                'range': f"{round(stats['rainfall']['min'], 2)}-{round(stats['rainfall']['max'], 2)} mm"
            }
        }
    
    def calculate_suitability_explanation(self, crop_name: str, field_data: Dict) -> str:
        """Generate explanation of why a crop is suitable for the field"""
        if crop_name not in self.crop_stats:
            return "Suitable for your field conditions."
        
        stats = self.crop_stats[crop_name]
        
        # Compare field conditions with crop requirements
        temp_optimal = stats['temperature']['mean']
        humidity_optimal = stats['humidity']['mean']
        rainfall_optimal = stats['rainfall']['mean']
        n_optimal = stats['N']['mean']
        
        field_temp = float(field_data.get('temperature', 25))
        field_humidity = float(field_data.get('humidity', 65))
        field_rainfall = float(field_data.get('rainfall', 500))
        field_n = float(field_data.get('nitrogen', 75))
        
        explanation = f"{crop_name} is well-suited for your field because:\n\n"
        
        # Temperature analysis
        temp_diff = abs(field_temp - temp_optimal)
        if temp_diff < 2:
            explanation += f"🌡️ Temperature ({field_temp}°C) matches optimal requirements ({temp_optimal:.1f}°C)\n"
        elif temp_diff < 5:
            explanation += f"🌡️ Temperature ({field_temp}°C) is quite suitable (optimal: {temp_optimal:.1f}°C)\n"
        else:
            explanation += f"🌡️ Temperature ({field_temp}°C) is acceptable (optimal: {temp_optimal:.1f}°C)\n"
        
        # Humidity analysis
        humidity_diff = abs(field_humidity - humidity_optimal)
        if humidity_diff < 5:
            explanation += f"💧 Humidity ({field_humidity}%) matches optimal levels ({humidity_optimal:.1f}%)\n"
        elif humidity_diff < 15:
            explanation += f"💧 Humidity ({field_humidity}%) is suitable (optimal: {humidity_optimal:.1f}%)\n"
        else:
            explanation += f"💧 Humidity ({field_humidity}%) requires management (optimal: {humidity_optimal:.1f}%)\n"
        
        # Rainfall analysis
        rainfall_diff = abs(field_rainfall - rainfall_optimal)
        if rainfall_diff < 100:
            explanation += f"🌧️ Rainfall ({field_rainfall:.0f}mm) is well-suited (optimal: {rainfall_optimal:.0f}mm)\n"
        else:
            explanation += f"🌧️ Rainfall ({field_rainfall:.0f}mm) is manageable (optimal: {rainfall_optimal:.0f}mm)\n"
        
        # Soil nutrients analysis
        if field_n >= n_optimal * 0.8:
            explanation += f"🌱 Nitrogen availability ({field_n:.0f} kg/ha) meets crop needs ({n_optimal:.0f} kg/ha)"
        else:
            explanation += f"🌱 Nitrogen levels ({field_n:.0f} kg/ha) are below optimal ({n_optimal:.0f} kg/ha) but manageable"
        
        return explanation
    
    # Crop-specific knowledge base
    CROP_KNOWLEDGE = {
        'Rice': {
            'variety': 'IR-64, Swarna, Basmati 370',
            'market_potential': 'Staple food crop with guaranteed government procurement (MSP). Strong domestic demand year-round. Export potential for Basmati varieties. Expected yield: 40-60 quintals/hectare.',
            'investment_needed': '₹25,000-35,000 per hectare (seeds, fertilizers, irrigation, labor)',
            'expected_returns': '₹60,000-90,000 per hectare at MSP rates',
            'harvest_timeline': 'Plant: June-July (Kharif) | Harvest: October-November (120-150 days)',
            'risk_factors': 'Highly water-intensive (needs 1200-1500mm water). Susceptible to blast disease and stem borer. Price fluctuations in open market.'
        },
        'Wheat': {
            'variety': 'HD-2967, GW-322, PBW-343',
            'market_potential': 'Second largest food crop with strong MSP support. Consistent demand from flour mills and export markets. Expected yield: 35-50 quintals/hectare.',
            'investment_needed': '₹18,000-25,000 per hectare',
            'expected_returns': '₹50,000-75,000 per hectare',
            'harvest_timeline': 'Plant: October-November (Rabi) | Harvest: March-April (120-130 days)',
            'risk_factors': 'Susceptible to rust diseases. Requires cool temperatures during grain filling. Late sowing reduces yield significantly.'
        },
        'Maize': {
            'variety': 'DHM-117, HQPM-1, NK-6240',
            'market_potential': 'High demand from poultry feed, starch, and ethanol industries. Growing export market. Expected yield: 50-70 quintals/hectare.',
            'investment_needed': '₹20,000-28,000 per hectare',
            'expected_returns': '₹55,000-85,000 per hectare',
            'harvest_timeline': 'Plant: June-July or Feb-March | Harvest: 90-110 days after sowing',
            'risk_factors': 'Susceptible to fall armyworm. Waterlogging causes significant yield loss. Requires well-drained soil.'
        },
        'Cotton': {
            'variety': 'Bt Cotton Hybrid, MCU-5, Suraj',
            'market_potential': 'Major cash crop with strong textile industry demand. Export opportunities. MSP support available. Expected yield: 15-25 quintals/hectare (seed cotton).',
            'investment_needed': '₹30,000-45,000 per hectare (higher due to pest management)',
            'expected_returns': '₹80,000-1,20,000 per hectare',
            'harvest_timeline': 'Plant: May-June | Harvest: October-January (180-200 days)',
            'risk_factors': 'High pest pressure (bollworm, whitefly). Requires intensive pest management. Price volatility in international markets.'
        },
        'Sugarcane': {
            'variety': 'Co-86032, CoJ-64, Co-0238',
            'market_potential': 'Guaranteed purchase by sugar mills. Stable pricing with FRP (Fair Remunerative Price). By-products (molasses, bagasse) add value. Expected yield: 700-900 quintals/hectare.',
            'investment_needed': '₹40,000-60,000 per hectare',
            'expected_returns': '₹1,50,000-2,50,000 per hectare',
            'harvest_timeline': 'Plant: February-March or October | Harvest: 12-14 months after planting',
            'risk_factors': 'Very water-intensive. Long crop duration ties up land. Delayed payments from sugar mills common.'
        },
        'Groundnut': {
            'variety': 'TAG-24, GG-20, TG-37A',
            'market_potential': 'High demand for edible oil and confectionery. Good export potential. Expected yield: 15-25 quintals/hectare.',
            'investment_needed': '₹18,000-25,000 per hectare',
            'expected_returns': '₹45,000-70,000 per hectare',
            'harvest_timeline': 'Plant: June-July (Kharif) or Jan-Feb (Rabi) | Harvest: 100-120 days',
            'risk_factors': 'Susceptible to aflatoxin contamination in storage. Tikka leaf spot disease. Requires well-drained sandy loam soil.'
        },
        'Soybean': {
            'variety': 'JS-335, NRC-37, MACS-450',
            'market_potential': 'Rising demand for protein meal and edible oil. Good export market. Expected yield: 20-30 quintals/hectare.',
            'investment_needed': '₹15,000-22,000 per hectare',
            'expected_returns': '₹40,000-65,000 per hectare',
            'harvest_timeline': 'Plant: June-July | Harvest: September-October (90-100 days)',
            'risk_factors': 'Susceptible to yellow mosaic virus. Waterlogging sensitive. Requires inoculation with Rhizobium for nitrogen fixation.'
        },
        'Tomato': {
            'variety': 'Pusa Ruby, Arka Vikas, Hybrid varieties',
            'market_potential': 'High-value vegetable with strong urban demand. Year-round market availability. Expected yield: 200-400 quintals/hectare.',
            'investment_needed': '₹60,000-90,000 per hectare (high input cost)',
            'expected_returns': '₹1,50,000-4,00,000 per hectare (highly variable)',
            'harvest_timeline': 'Plant: June-July or Oct-Nov | Harvest: 60-80 days after transplanting',
            'risk_factors': 'Highly perishable. Price crashes during peak season. Susceptible to early/late blight and viral diseases.'
        },
        'Onion': {
            'variety': 'Nasik Red, Agrifound Dark Red, Bhima Raj',
            'market_potential': 'Essential kitchen commodity with consistent demand. Good export potential to Southeast Asia and Middle East. Expected yield: 150-250 quintals/hectare.',
            'investment_needed': '₹50,000-70,000 per hectare',
            'expected_returns': '₹80,000-2,50,000 per hectare (price-dependent)',
            'harvest_timeline': 'Plant: Oct-Nov (Rabi) | Harvest: March-May (120-130 days)',
            'risk_factors': 'Extreme price volatility. Susceptible to thrips and purple blotch disease. Storage losses can be significant.'
        },
        'Millet': {
            'variety': 'HHB-67, Pusa-383, GHB-558',
            'market_potential': 'Growing health food market demand. Government promotion under Nutri-Cereals mission. Drought-resistant and low-input crop. Expected yield: 15-25 quintals/hectare.',
            'investment_needed': '₹8,000-12,000 per hectare (low input crop)',
            'expected_returns': '₹25,000-45,000 per hectare',
            'harvest_timeline': 'Plant: June-July | Harvest: September-October (70-90 days)',
            'risk_factors': 'Lower market price compared to other cereals. Downy mildew disease. Limited processing infrastructure in some regions.'
        },
        'Barley': {
            'variety': 'RD-2552, K-572, DWRB-73',
            'market_potential': 'Demand from malt/brewery industry and animal feed. Growing health food segment. Expected yield: 30-45 quintals/hectare.',
            'investment_needed': '₹12,000-18,000 per hectare',
            'expected_returns': '₹35,000-55,000 per hectare',
            'harvest_timeline': 'Plant: October-November (Rabi) | Harvest: March-April (100-110 days)',
            'risk_factors': 'Susceptible to yellow rust. Limited MSP support. Market price depends heavily on malt industry demand.'
        },
        'Pulses': {
            'variety': 'Pusa-256 (Arhar), K-75 (Moong), RVL-31 (Masoor)',
            'market_potential': 'High protein demand with MSP support. Import substitution opportunity. Expected yield: 8-15 quintals/hectare.',
            'investment_needed': '₹10,000-16,000 per hectare',
            'expected_returns': '₹30,000-55,000 per hectare',
            'harvest_timeline': 'Varies by type: 60-180 days | Kharif or Rabi season',
            'risk_factors': 'Susceptible to pod borer and wilt diseases. Yield instability due to weather. Soil nitrogen fixation benefit for next crop.'
        },
        'Gram': {
            'variety': 'GNG-1581, RSG-963, Pusa-372',
            'market_potential': 'Highest consumed pulse in India. Strong MSP and market demand. Expected yield: 12-20 quintals/hectare.',
            'investment_needed': '₹10,000-15,000 per hectare',
            'expected_returns': '₹35,000-60,000 per hectare',
            'harvest_timeline': 'Plant: October-November (Rabi) | Harvest: February-March (90-110 days)',
            'risk_factors': 'Susceptible to Fusarium wilt and Ascochyta blight. Frost damage during flowering. Requires cool dry weather.'
        },
        'Corn': {
            'variety': 'DHM-117, P-3522, NK-6240',
            'market_potential': 'Strong demand from poultry, starch and ethanol industries. Growing processed food market. Expected yield: 50-70 quintals/hectare.',
            'investment_needed': '₹20,000-28,000 per hectare',
            'expected_returns': '₹55,000-85,000 per hectare',
            'harvest_timeline': 'Plant: June-July or Feb-March | Harvest: 90-110 days after sowing',
            'risk_factors': 'Susceptible to fall armyworm. Waterlogging causes significant yield loss. Requires well-drained fertile soil.'
        },
        'Sugarbeet': {
            'variety': 'Maribo Magnum, Kawemira, Beta-1',
            'market_potential': 'Sugar industry demand as alternative to sugarcane. Higher sugar recovery rate. Expected yield: 400-600 quintals/hectare.',
            'investment_needed': '₹35,000-50,000 per hectare',
            'expected_returns': '₹80,000-1,40,000 per hectare',
            'harvest_timeline': 'Plant: October-November | Harvest: March-April (150-180 days)',
            'risk_factors': 'Limited processing facilities in India. Requires cool climate. Cercospora leaf spot disease. Niche market.'
        },
    }

    def generate_ml_recommendations(self, top_crops: List[Tuple[str, float]], field_data: Dict) -> Dict:
        """Generate ML-based recommendations for top 3 crops with crop-specific details"""

        recommendations = {'recommended_crops': []}

        for idx, (crop_name, confidence) in enumerate(top_crops[:3]):
            crop_details = self.get_crop_details(crop_name)
            knowledge = self.CROP_KNOWLEDGE.get(crop_name, {})

            recommendation = {
                'name': crop_name,
                'rank': idx + 1,
                'confidence': round(confidence, 2),
                'variety': knowledge.get('variety', f'Select varieties suited to {field_data.get("location", "your region")}'),
                'why_suitable': self.calculate_suitability_explanation(crop_name, field_data),
                'market_potential': knowledge.get('market_potential', f'Good market demand for {crop_name}.'),
                'investment_needed': knowledge.get('investment_needed', 'Consult local agricultural office for estimates.'),
                'expected_returns': knowledge.get('expected_returns', 'Depends on market prices and yield.'),
                'growing_tips': f"Apply {crop_details['nitrogen_requirement']['mean']:.0f} kg/ha N, {crop_details['phosphorus_requirement']['mean']:.0f} kg/ha P, {crop_details['potassium_requirement']['mean']:.0f} kg/ha K. Maintain soil pH around {crop_details['pH']['optimal']:.1f}. Optimal temperature: {crop_details['temperature']['range']}." if crop_details else 'Follow standard agronomic practices.',
                'harvest_timeline': knowledge.get('harvest_timeline', 'Refer to local agricultural guidelines.'),
                'risk_factors': knowledge.get('risk_factors', 'Monitor for common pests and diseases.')
            }
            recommendations['recommended_crops'].append(recommendation)

        return recommendations
