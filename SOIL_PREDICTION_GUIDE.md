# Soil Property Prediction from Satellite Data - Complete Guide

## Overview

Instead of manual soil input, the system now uses **Machine Learning models** to automatically predict soil properties from satellite imagery indices.

## How It Works

### Step 1: User Draws Field on Map
- User draws polygon on the map
- System calculates field area automatically

### Step 2: Fetch NDVI from Satellite Data
- Backend fetches Sentinel-2 or Landsat NDVI data for the field
- NDVI = (NIR - Red) / (NIR + Red)
- Range: -1 to 1
  - **> 0.6** = Healthy vegetation, good soil
  - **0.3-0.6** = Moderate vegetation
  - **< 0.3** = Poor vegetation/bare soil

### Step 3: Calculate Other Satellite Indices
From the same satellite imagery:
- **NDBI** (Normalized Difference Built-up Index) = (SWIR - NIR) / (SWIR + NIR)
- **NDMI** (Moisture Index) = (NIR - SWIR) / (NIR + SWIR)
- **SAVI** (Soil-Adjusted Vegetation Index) = ((NIR - Red) / (NIR + Red + L)) * (1 + L)

### Step 4: ML Model Predicts Soil Properties

**Input:** [NDVI, NDBI, NDMI, SAVI, Elevation]

**Model:** Random Forest Regressor (100 trees)

**Outputs:**
- **Soil pH** (0-14 scale)
- **Soil Type** (Clay, Sandy, Loamy, Silt, Chalky, Peaty)
- **Moisture Level** (High, Medium, Low)
- **Organic Matter %** (0-4%)
- **Confidence Score** (0-1)

## Example Output

### Input: NDVI = 0.65
```json
{
  "soil_ph": 6.8,
  "soil_ph_range": "6.5-7.1",
  "ph_confidence": 0.92,
  "soil_type": "Loamy",
  "soil_type_confidence": 0.87,
  "moisture_level": "High - Well irrigated",
  "organic_matter": "2.3%",
  "indices": {
    "ndvi": 0.650,
    "ndbi": -0.150,
    "ndmi": 0.350,
    "savi": 0.455
  },
  "recommendation": "pH level suitable for most crops | Loamy soil - Ideal for most crops",
  "data_source": "Satellite Imagery ML Prediction"
}
```

## What Satellites Provide These Indices?

### Sentinel-2 (Free, High Resolution)
- Resolution: 10-20m
- Bands: RGB, NIR, SWIR
- Update: Every 5 days
- **Best for**: Farm-level soil monitoring

### Landsat 8/9 (Free, Medium Resolution)
- Resolution: 30m
- Bands: Similar to Sentinel
- Update: Every 16 days
- **Good for**: Larger areas

### MODIS (Free, Low Resolution)
- Resolution: 250m
- Update: Daily
- **Good for**: Quick monitoring

## The ML Model Relationships

```
High NDVI (0.6+) → Healthy vegetation → Good organic matter → Higher pH stability
Low NDVI (<0.3)  → Sparse vegetation → Low organic matter → Variable pH

High NDMI (0.3+) → High moisture → Clay/loamy soil → Better water retention
Low NDMI (<0.1)  → Low moisture → Sandy soil → Poor retention

High NDBI (>0)   → Built-up/barren → Compacted soil → Lower productivity
Low NDBI (<0)    → Vegetated → Better soil structure
```

## Satellite Data Integration in Backend

### Add to `app.py`:
```python
from soil_prediction_routes import soil_bp

# Register blueprint
app.register_blueprint(soil_bp)
```

### Available Endpoints:

**1. Predict from NDVI (Quick)**
```
POST /api/soil/ndvi-to-properties
Body: {"ndvi": 0.65}
```

**2. Full Soil Prediction**
```
POST /api/soil/predict
Body: {"coordinates": [[lat,lng],...], "start_date": "2024-01-01", "end_date": "2024-12-31"}
```

**3. Calculate Indices from Raw Bands**
```
POST /api/soil/indices
Body: {"red": 0.1, "nir": 0.3, "swir1": 0.15, "blue": 0.05}
```

## Current Data Flow in CropSuggestion Page

```
1. User Draws Field
     ↓
2. System Calculates Area (Auto-filled)
     ↓
3. System Fetches NDVI from Sentinel-2 (Last 6 months)
     ↓
4. ML Model Predicts Soil Properties from NDVI
     ↓
5. Auto-populate soil_ph and soil_type fields
     ↓
6. Show Predicted Soil Data on Map Panel
     ↓
7. User Can Override with Manual Data
     ↓
8. Submit Form for Crop Recommendations
```

## Output Page Shows

### When User Submits:
1. **Land Analysis**
   - Field size, location
   - Predicted vs. actual soil data
   - Organic matter percentage

2. **Season Analysis**
   - Current season suitability
   - Rainfall patterns
   - Temperature compatibility

3. **Market Insights**
   - Top crops' prices
   - Demand trends
   - Export opportunities

4. **Recommended Crops**
   - Top 3-5 crops ranked by suitability
   - Why each crop is suitable
   - Expected returns
   - Investment needed
   - Growing tips

5. **Action Plan**
   - Soil amendments needed
   - Irrigation recommendations
   - Fertilizer requirements
   - Planting schedule

6. **Sustainability Advice**
   - Water conservation tips
   - Organic farming options
   - Crop rotation suggestions

## How to Improve the Model

### Current: Random Forest with NDVI only
### Future Improvements:

1. **Add more training data**
   - Ground truth soil samples
   - Lab-tested soil properties
   - Multiple growing seasons

2. **Use Deep Learning**
   - CNN for satellite image segmentation
   - LSTM for temporal patterns
   - Attention mechanisms for field zones

3. **Integrate more data sources**
   - Weather data (precipitation, temperature)
   - Terrain elevation (DEM)
   - Landform classification
   - Previous crop records

4. **Fine-tune for regions**
   - Train separate models for each climate zone
   - Account for local soil variations
   - Regional crop preferences

## Example: How NDVI Predicts Soil pH

```
High NDVI (0.7)  → Healthy vegetation
                 → Good nutrient cycling
                 → Established pH buffering
                 → Predicted pH: 6.8-7.2 (Neutral) ✓

Low NDVI (0.3)   → Poor vegetation
                 → Limited organic matter
                 → Weak pH buffering
                 → Predicted pH: 5.5-6.2 (Acidic) ✓
                 → Recommendation: Add lime

NDVI 0.6 + NDMI 0.35 + SAVI 0.45
                 → Mixed signals
                 → Moderate conditions
                 → Predicted pH: 6.5-7.0
                 → Recommendation: Standard fertilization
```

## Next Steps

1. ✅ ML model for soil prediction
2. ✅ Auto-populate soil from satellite data
3. ⏳ Integrate real Sentinel-2 API
4. ⏳ Add ground truth validation
5. ⏳ Train model on your region's data
6. ⏳ Improve accuracy with field surveys
