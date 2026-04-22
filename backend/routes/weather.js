// backend/routes/weather.js
const express = require('express');
const axios = require('axios');
const router = express.Router();

// GET /api/weather - Fetches weather data from NASA POWER API with validation
router.post('/data', async (req, res) => {
  try {
    const { coordinates, start_date, end_date } = req.body;
    
    if (!coordinates || !start_date || !end_date) {
      return res.status(400).json({ message: 'Coordinates and date range are required' });
    }
    
    // Extract center point of field for weather data
    const centerLng = coordinates.reduce((sum, coord) => sum + coord[0], 0) / coordinates.length;
    const centerLat = coordinates.reduce((sum, coord) => sum + coord[1], 0) / coordinates.length;
    
    // Format dates for NASA POWER API (YYYYMMDD format)
    const formattedStartDate = start_date.replace(/-/g, '');
    const formattedEndDate = end_date.replace(/-/g, '');
    
    // Parameters to fetch: temperature, precipitation, humidity, solar radiation
    const parameters = 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN';
    
    const powerApiUrl = `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=${parameters}&community=AG&longitude=${centerLng}&latitude=${centerLat}&start=${formattedStartDate}&end=${formattedEndDate}&format=JSON`;
    
    const response = await axios.get(powerApiUrl);
    
    // Validate and clean the data - NASA POWER API uses -999 for missing data
    const cleanedData = validateAndCleanWeatherData(response.data, centerLat);
    
    res.json(cleanedData);
  } catch (error) {
    console.error('Error fetching weather data:', error);
    res.status(500).json({ message: 'Failed to fetch weather data', error: error.message });
  }
});

/**
 * Validates and cleans weather data from NASA POWER API
 * Removes -999 placeholder values (missing data) and uses realistic Indian climate patterns
 * @param {Object} apiData - Raw data from NASA POWER API
 * @param {number} latitude - Field latitude for regional climate patterns
 * @returns {Object} Cleaned weather data
 */
function validateAndCleanWeatherData(apiData, latitude) {
  if (!apiData.properties || !apiData.properties.parameter) {
    return apiData;
  }

  const parameter = apiData.properties.parameter;
  const cleanedParameter = {};

  // Indian climate patterns by region (average monthly ranges)
  const indianClimatePatterns = {
    northern: { minTemp: 12, maxTemp: 35, avgRain: 45, avgHumidity: 65 },
    central: { minTemp: 18, maxTemp: 38, avgRain: 52, avgHumidity: 68 },
    southern: { minTemp: 22, maxTemp: 32, avgRain: 65, avgHumidity: 75 },
    coastal: { minTemp: 20, maxTemp: 30, avgRain: 85, avgHumidity: 80 },
  };

  // Determine region based on latitude
  let climateRegion = 'central';
  if (latitude > 28) climateRegion = 'northern';
  else if (latitude > 20) climateRegion = 'central';
  else if (latitude > 13) climateRegion = 'southern';
  else climateRegion = 'southern';

  const regionClimate = indianClimatePatterns[climateRegion];

  // Process each parameter
  for (const [paramName, paramData] of Object.entries(parameter)) {
    cleanedParameter[paramName] = {};

    for (const [dateKey, value] of Object.entries(paramData)) {
      let cleanedValue = value;

      // Remove -999 (NASA's missing data placeholder)
      if (value === -999 || value < -500) {
        // Use realistic defaults for Indian climate
        switch (paramName) {
          case 'T2M':
            cleanedValue = (regionClimate.minTemp + regionClimate.maxTemp) / 2;
            break;
          case 'T2M_MAX':
            cleanedValue = regionClimate.maxTemp;
            break;
          case 'T2M_MIN':
            cleanedValue = regionClimate.minTemp;
            break;
          case 'PRECTOTCORR':
            cleanedValue = regionClimate.avgRain / 30; // Convert monthly to daily
            break;
          case 'RH2M':
            cleanedValue = regionClimate.avgHumidity;
            break;
          case 'ALLSKY_SFC_SW_DWN':
            cleanedValue = 18; // Average solar radiation in MJ/m² for India
            break;
          default:
            cleanedValue = 0;
        }
      }
      // Validate reasonable ranges for India
      else {
        switch (paramName) {
          case 'T2M':
          case 'T2M_MAX':
          case 'T2M_MIN':
            // India temperature range: -10°C to 50°C (extremes), but typically 5-45°C
            cleanedValue = Math.max(-10, Math.min(50, value));
            break;
          case 'PRECTOTCORR':
            // Precipitation: max ~200mm/day in monsoon season
            cleanedValue = Math.max(0, Math.min(200, value));
            break;
          case 'RH2M':
            // Humidity: 0-100%
            cleanedValue = Math.max(0, Math.min(100, value));
            break;
          case 'ALLSKY_SFC_SW_DWN':
            // Solar radiation: 0-30 MJ/m²
            cleanedValue = Math.max(0, Math.min(30, value));
            break;
        }
      }

      cleanedParameter[paramName][dateKey] = parseFloat(cleanedValue.toFixed(2));
    }
  }

  return {
    ...apiData,
    properties: {
      ...apiData.properties,
      parameter: cleanedParameter,
      data_quality: {
        status: 'validated',
        missing_data_filled: true,
        region_climate: climateRegion,
        note: 'Values validated against realistic Indian climate patterns'
      }
    }
  };
}

module.exports = router;