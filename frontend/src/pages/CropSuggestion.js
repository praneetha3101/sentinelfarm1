import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { getFlaskApiUrl } from '../config/api';
import FieldList from '../components/FieldList';
import '../styles/CropSuggestion.css';
import { getApiUrl } from "../config/api";

const CropSuggestion = () => {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        location: '',
        area: '',
        fertility_level: '',
        soil_ph: '',
        temperature: '',
        humidity: '',
        rainfall: '',
        nitrogen: '',
        phosphorus: '',
        potassium: ''
    });

    const [aoiCoordinates, setAoiCoordinates] = useState(null);
    const [drawnArea, setDrawnArea] = useState(null);
    const [weatherDataLoading, setWeatherDataLoading] = useState(false);
    const [weatherDataFetched, setWeatherDataFetched] = useState(false);

    const [recommendations, setRecommendations] = useState(null);
    const [loading, setLoading] = useState(false); // v2
    const [error, setError] = useState('');

    // Field selection state
    const [fields, setFields] = useState([]);
    const [selectedField, setSelectedField] = useState(null);
    const [fieldsLoading, setFieldsLoading] = useState(true);

    // Get user email from localStorage
    const getUserEmail = () => {
        const userData = localStorage.getItem('user');
        if (userData) {
            try {
                const { email } = JSON.parse(userData);
                return email;
            } catch (err) {
                console.error('Error parsing user data:', err);
            }
        }
        navigate('/login');
        return null;
    };

    // Fetch user fields on component mount
    useEffect(() => {
        const fetchFields = async () => {
            try {
                const email = getUserEmail();
                if (!email) return;

                const response = await axios.get(`${getApiUrl()}/api/fields?email=${email}`);
                console.log('Fields response:', response.data);
                
                if (response.data.fields && Array.isArray(response.data.fields)) {
                    setFields(response.data.fields);
                } else {
                    console.error('Invalid field data format:', response.data);
                    setError('Error loading saved fields');
                }
            } catch (err) {
                console.error('Error fetching fields:', err);
                setError(`Error loading saved fields: ${err.message || 'Unknown error'}`);
            } finally {
                setFieldsLoading(false);
            }
        };

        fetchFields();
    }, []);

    // Fertility level to N, P, K mapping
    const fertilityLevels = {
        'low': { nitrogen: 35, phosphorus: 24, potassium: 40, label: 'Low Fertility' },
        'medium': { nitrogen: 75, phosphorus: 28, potassium: 51, label: 'Medium Fertility' },
        'high': { nitrogen: 125, phosphorus: 42, potassium: 74, label: 'High Fertility' }
    };

    // Factors needed for crop recommendation
    const recommendationFactors = [
        {
            category: 'Field Information',
            factors: [
                { name: 'Location', description: 'Geographic coordinates and region', status: aoiCoordinates ? 'complete' : 'pending' },
                { name: 'Field Area', description: 'Size of the field in hectares', status: formData.area ? 'complete' : 'pending' }
            ]
        },
        {
            category: 'Soil Properties',
            factors: [
                { name: 'Soil Fertility Level', description: 'Low, Medium, or High fertility', status: formData.fertility_level ? 'complete' : 'pending' },
                { name: 'Soil pH', description: 'pH level indicating soil acidity/alkalinity (manual entry)', status: formData.soil_ph ? 'complete' : 'pending' }
            ]
        },
        {
            category: 'Weather & Climate',
            factors: [
                { name: 'Temperature', description: 'Temperature data from weather API', status: formData.temperature ? 'complete' : 'pending' },
                { name: 'Humidity', description: 'Humidity data from weather API', status: formData.humidity ? 'complete' : 'pending' },
                { name: 'Rainfall', description: 'Rainfall data from weather API', status: formData.rainfall ? 'complete' : 'pending' }
            ]
        },

    ];

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        
        // If fertility level changes, auto-populate N, P, K
        if (name === 'fertility_level' && value && fertilityLevels[value]) {
            const fertilityData = fertilityLevels[value];
            setFormData(prevState => ({
                ...prevState,
                [name]: value,
                nitrogen: fertilityData.nitrogen.toString(),
                phosphorus: fertilityData.phosphorus.toString(),
                potassium: fertilityData.potassium.toString()
            }));
        } else {
            setFormData(prevState => ({
                ...prevState,
                [name]: value
            }));
        }
    };

    const generateAIRecommendations = async (e) => {
        e.preventDefault();
        
        // Validate required fields
        const requiredFields = ['location', 'area', 'fertility_level', 'soil_ph', 'temperature', 'humidity', 'rainfall'];
        const missingFields = requiredFields.filter(field => !formData[field]);
        
        if (missingFields.length > 0) {
            setError(`Please fill in all required fields: ${missingFields.join(', ')}`);
            return;
        }

        setLoading(true);
        setError('');
        setRecommendations(null);

        try {
            // Get current N/P/K from fertility level if set
            const n = formData.nitrogen ? parseFloat(formData.nitrogen) : 75;
            const p = formData.phosphorus ? parseFloat(formData.phosphorus) : 28;
            const k = formData.potassium ? parseFloat(formData.potassium) : 51;

            const response = await axios.post(`${getFlaskApiUrl()}/api/crop-recommendations`, {
                field_data: {
                    location: formData.location,
                    area: parseFloat(formData.area),
                    fertility_level: formData.fertility_level,
                    nitrogen: n,
                    phosphorus: p,
                    potassium: k,
                    soil_ph: parseFloat(formData.soil_ph),
                    temperature: parseFloat(formData.temperature),
                    humidity: parseFloat(formData.humidity),
                    rainfall: parseFloat(formData.rainfall)
                },
                coordinates: aoiCoordinates
            });

            console.log('Full API response:', response.data);

            if (response.data && response.data.recommendations) {
                const recs = response.data.recommendations;
                console.log('Setting recommendations:', recs);
                setRecommendations(recs);
                
                // Show status message if it's not a full success
                if (response.data.status === 'partial') {
                    setError('Using fallback recommendations. AI service may be initializing.');
                }
            } else if (response.data && response.data.fallback) {
                // Legacy fallback handling
                console.log('Using legacy fallback:', response.data.fallback);
                setRecommendations(response.data.fallback);
                setError('Using fallback recommendations. AI service may be initializing.');
            } else {
                setError(response.data?.error || 'Failed to get recommendations');
                console.error('Unexpected response structure:', response.data);
            }
        } catch (err) {
            console.error('Error getting AI recommendations:', err);
            setError('Failed to connect to recommendation service. Make sure the backend is running on port 5001.');
        } finally {
            setLoading(false);
        }
    };

    const renderAnalysisSection = (title, data, icon) => {
        if (!data) return null;

        return (
            <div className="analysis-section">
                <h3 className="analysis-title">
                    <span className="analysis-icon">{icon}</span>
                    {title}
                </h3>
                <div className="analysis-content">
                    {Object.entries(data).map(([key, value]) => (
                        <div key={key} className="analysis-item">
                            <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                            <p>{value}</p>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    // Handle field selection from dropdown
    const handleFieldSelect = async (field) => {
        if (!field) {
            setError('No field selected');
            return;
        }
        
        // Clear previous selections
        setSelectedField(null);
        setFormData({});
        setRecommendations(null);
        setError('');
        
        // Now set the newly selected field
        setSelectedField(field);
        console.log('=== SINGLE FIELD SELECTED ===');
        console.log('Selected field:', field.plot_name || field.id);
        console.log('Field ID:', field.id || field._id);
        console.log('Full field object:', field);
        
        // Extract coordinates from various possible formats
        let coordinates = null;
        
        try {
            // Format 1: Direct coordinates array
            if (field.coordinates && Array.isArray(field.coordinates)) {
                coordinates = field.coordinates;
            } 
            // Format 2: GeoJSON geometry object
            else if (field.geometry && field.geometry.coordinates) {
                const geomCoord = field.geometry.coordinates;
                // For Polygon: [[[lon, lat], [lon, lat], ...]]
                if (geomCoord[0] && Array.isArray(geomCoord[0]) && geomCoord[0][0] && Array.isArray(geomCoord[0][0])) {
                    coordinates = geomCoord[0];
                } else if (geomCoord[0] && Array.isArray(geomCoord[0])) {
                    coordinates = geomCoord;
                }
            } 
            // Format 3: GeoJSON data as object or string
            else if (field.geojson_data) {
                let geoJson = field.geojson_data;
                
                // Parse if it's a string
                if (typeof geoJson === 'string') {
                    geoJson = JSON.parse(geoJson);
                }
                
                console.log('Parsed GeoJSON:', geoJson);
                
                // Extract coordinates from GeoJSON
                if (geoJson.type === 'Polygon' && geoJson.coordinates) {
                    // Polygon format: [[[lon, lat], [lon, lat], ...]]
                    const polygonCoords = geoJson.coordinates;
                    if (polygonCoords[0] && Array.isArray(polygonCoords[0])) {
                        coordinates = polygonCoords[0];
                    }
                } else if (geoJson.geometry && geoJson.geometry.coordinates) {
                    // Feature format with geometry
                    const geomCoord = geoJson.geometry.coordinates;
                    if (geomCoord[0] && Array.isArray(geomCoord[0]) && geomCoord[0][0] && Array.isArray(geomCoord[0][0])) {
                        coordinates = geomCoord[0];
                    } else if (geomCoord[0] && Array.isArray(geomCoord[0])) {
                        coordinates = geomCoord;
                    }
                }
            } 
            // Format 4: Polygon property
            else if (field.polygon && Array.isArray(field.polygon)) {
                coordinates = field.polygon;
            }
            
            console.log('Extracted coordinates:', coordinates);
            
            // Validate coordinates
            if (!coordinates || !Array.isArray(coordinates) || coordinates.length < 3) {
                throw new Error('Field polygon must have at least 3 points');
            }
            
            // Verify first coordinate is valid [lon, lat]
            if (!Array.isArray(coordinates[0]) || coordinates[0].length < 2) {
                throw new Error('Invalid coordinate format');
            }
            
            setAoiCoordinates(coordinates);
            console.log('✅ Coordinates validated and set');
            
            // Calculate area
            const area = calculatePolygonArea(coordinates);
            setDrawnArea(area);
            console.log('📏 Area calculated:', area);
            
            // Calculate center (assuming [lon, lat] format - standard GeoJSON)
            const centerLng = coordinates.reduce((sum, coord) => sum + coord[0], 0) / coordinates.length;
            const centerLat = coordinates.reduce((sum, coord) => sum + coord[1], 0) / coordinates.length;
            
            console.log('📍 Center location:', centerLat, centerLng);
            
            // Auto-fill form
            setFormData(prevState => ({
                ...prevState,
                location: `${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}`,
                area: area.toFixed(2)
            }));
            
            console.log('🌤️ Fetching weather data...');
            const weatherResult = await fetchWeatherData(coordinates);

            // ✅ FIXED: Don't auto-generate crops on field selection
            // Wait for user to fill soil pH, fertility level, and click button
            // Clear any previous recommendations
            setRecommendations(null);

            console.log('✅ Field selection completed successfully!');
            console.log('📝 Please fill in Soil Fertility Level, Soil pH, and click "Get Crop Recommendations"');
            setError('');
        } catch (err) {
            console.error('❌ Error during field selection:', err);
            setError(`Error: ${err.message}`);
        }
    };

    // Calculate polygon area in hectares
    const calculatePolygonArea = (coordinates) => {
        if (!coordinates || coordinates.length < 3) return 0;
        
        let area = 0;
        const n = coordinates.length;
        
        for (let i = 0; i < n; i++) {
            const j = (i + 1) % n;
            area += coordinates[i][0] * coordinates[j][1];
            area -= coordinates[j][0] * coordinates[i][1];
        }
        
        area = Math.abs(area) / 2;
        // Convert square degrees to hectares (approximate)
        const areaHectares = area * 12321;
        
        return areaHectares;
    };

    // Auto-generate top 3 crops based on field information - called after weather data is fetched
    const generateTop3Crops = async (coordinates, centerLat, centerLng, areaHectares, weatherTemp, weatherHumidity, weatherRainfall) => {
        try {
            const response = await axios.post(`${getFlaskApiUrl()}/api/top-3-crops`, {
                field_data: {
                    location: `${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}`,
                    area: parseFloat(areaHectares.toFixed(2)),
                    fertility_level: 'medium',
                    nitrogen: 75,
                    phosphorus: 28,
                    potassium: 51,
                    soil_ph: 6.5,
                    temperature: weatherTemp,
                    humidity: weatherHumidity,
                    rainfall: weatherRainfall
                },
                coordinates: coordinates
            });

            if (response.data?.recommendations) {
                setRecommendations(response.data.recommendations);
            }
        } catch (err) {
            console.warn('Could not auto-generate top 3 crops:', err);
        }
    };

    // Fetch weather data - returns the computed values so generateTop3Crops can use them
    const fetchWeatherData = async (coordinates) => {
        if (!coordinates || coordinates.length === 0) return { temp: 25, humidity: 65, rainfall: 60 };

        setWeatherDataLoading(true);
        let avgTemp = 25, avgHumidity = 65, totalRainfall = 60;

        try {
            const endDate = new Date();
            endDate.setDate(endDate.getDate() - 5);
            const startDate = new Date(endDate);
            startDate.setMonth(startDate.getMonth() - 6);

            const response = await axios.post(`${getApiUrl()}/api/weather/data`, {
                coordinates,
                start_date: startDate.toISOString().split('T')[0],
                end_date: endDate.toISOString().split('T')[0]
            });

            const weatherData = response.data?.properties?.parameter || response.data?.parameter;

            if (weatherData) {
                if (weatherData.T2M) {
                    const vals = Object.values(weatherData.T2M);
                    avgTemp = vals.reduce((a, b) => a + b, 0) / vals.length;
                }
                if (weatherData.RH2M) {
                    const vals = Object.values(weatherData.RH2M);
                    avgHumidity = vals.reduce((a, b) => a + b, 0) / vals.length;
                }
                if (weatherData.PRECTOTCORR) {
                    totalRainfall = Object.values(weatherData.PRECTOTCORR).reduce((a, b) => a + b, 0);
                }
            }
        } catch (err) {
            console.warn('Weather fetch failed, using defaults:', err.message);
        } finally {
            setFormData(prev => ({
                ...prev,
                temperature: avgTemp.toFixed(2),
                humidity: avgHumidity.toFixed(2),
                rainfall: totalRainfall.toFixed(2)
            }));
            setWeatherDataFetched(true);
            setWeatherDataLoading(false);
        }

        return { temp: parseFloat(avgTemp.toFixed(2)), humidity: parseFloat(avgHumidity.toFixed(2)), rainfall: parseFloat(totalRainfall.toFixed(2)) };
    };


    const renderCropRecommendations = (crops) => {
        if (!crops || !Array.isArray(crops)) return null;

        const rankingSymbols = ['🥇', '🥈', '🥉'];

        return (
            <div className="crop-recommendations-section">
                <h3 className="section-title">
                    <span className="section-icon">🤖</span>
                    ML-Recommended Crops
                </h3>
                <div className="crops-grid">
                    {crops.map((crop, index) => (
                        <div key={index} className="crop-recommendation-card">
                            <div className="crop-header">
                                <span className="ranking-badge">{rankingSymbols[index] || '⭐'}</span>
                                <h4 className="crop-name">{crop.name}</h4>
                            </div>
                            {crop.variety && (
                                <p className="crop-variety"><strong>Variety:</strong> {crop.variety}</p>
                            )}
                            
                            <div className="crop-details">
                                <div className="crop-detail-item">
                                    <strong>Why Suitable:</strong>
                                    <p>{crop.why_suitable}</p>
                                </div>
                                
                                <div className="crop-detail-item">
                                    <strong>Market Potential:</strong>
                                    <p>{crop.market_potential}</p>
                                </div>
                                
                                {crop.investment_needed && (
                                    <div className="crop-detail-item">
                                        <strong>Investment Needed:</strong>
                                        <p>{crop.investment_needed}</p>
                                    </div>
                                )}
                                
                                {crop.expected_returns && (
                                    <div className="crop-detail-item">
                                        <strong>Expected Returns:</strong>
                                        <p>{crop.expected_returns}</p>
                                    </div>
                                )}
                                
                                {crop.growing_tips && (
                                    <div className="crop-detail-item">
                                        <strong>Growing Tips:</strong>
                                        <p>{crop.growing_tips}</p>
                                    </div>
                                )}
                                
                                {crop.harvest_timeline && (
                                    <div className="crop-detail-item">
                                        <strong>Timeline:</strong>
                                        <p>{crop.harvest_timeline}</p>
                                    </div>
                                )}
                                
                                {crop.risk_factors && (
                                    <div className="crop-detail-item">
                                        <strong>Risk Factors:</strong>
                                        <p>{crop.risk_factors}</p>
                                    </div>
                                )}

                                {crop.ai_full_response && (
                                    <div className="crop-detail-item">
                                        <strong>Complete AI Analysis:</strong>
                                        <div className="ai-response-text">
                                            <pre>{crop.ai_full_response}</pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const getCompletionPercentage = () => {
        const totalFactors = recommendationFactors.reduce((sum, category) => sum + category.factors.length, 0);
        const completeFactors = recommendationFactors.reduce((sum, category) => 
            sum + category.factors.filter(f => f.status === 'complete').length, 0
        );
        return Math.round((completeFactors / totalFactors) * 100);
    };

    const completionPercentage = getCompletionPercentage();

    return (
        <div className="crop-suggestion-container">
            <div className="crop-suggestion-header">
                <h1>🚜 Crop Recommendations</h1>
                <p className="subtitle">Draw your field on the map and get intelligent farming advice tailored to your land</p>
            </div>

            <div className="crop-suggestion-content">
                {/* Field Selector Section */}
                <div className="field-selector-section">
                    <div className="field-selector-header">
                        <h2>🌾 Select Your Field</h2>
                        <p className="field-selector-instruction">Choose from your saved fields or draw a new one</p>
                    </div>

                    {fieldsLoading ? (
                        <div className="loading-fields">Loading your fields...</div>
                    ) : fields.length > 0 ? (
                        <div className="field-selector-wrapper">
                            <div style={{marginBottom: '1rem', fontSize: '0.9rem', color: '#666'}}>
                                <p>📌 Total fields found: <strong>{fields.length}</strong></p>
                            </div>
                            <FieldList 
                                fields={fields}
                                selectedField={selectedField}
                                onFieldSelect={handleFieldSelect}
                                compact={true}
                            />
                        </div>
                    ) : (
                        <div className="no-fields-message">
                            <p>No saved fields found. Please go to Monitor Field to create one.</p>
                        </div>
                    )}
                </div>

                {/* Factors Required Section */}
                <div className="factors-section">
                    <div className="factors-header">
                        <h2>📋 Factors Needed for Recommendation</h2>
                        <div className="completion-bar">
                            <div className="completion-progress" style={{ width: `${completionPercentage}%` }}></div>
                            <span className="completion-text">{completionPercentage}% Complete</span>
                        </div>
                    </div>

                    <div className="factors-list">
                        {recommendationFactors.map((category, idx) => (
                            <div key={idx} className="factor-category">
                                <h3 className="category-title">{category.category}</h3>
                                <div className="category-factors">
                                    {category.factors.map((factor, fidx) => (
                                        <div key={fidx} className={`factor-item ${factor.status}`}>
                                            <div className="factor-status">
                                                {factor.status === 'complete' ? '✓' : '○'}
                                            </div>
                                            <div className="factor-details">
                                                <strong>{factor.name}</strong>
                                                <p>{factor.description}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Form Section */}
            <form onSubmit={generateAIRecommendations} className="crop-form">
                <div className="form-section">
                    <h3>📝 Field Details</h3>
                    <div className="form-grid">
                        <div className="form-group">
                            <label htmlFor="location">Location *</label>
                            <input
                                type="text"
                                id="location"
                                name="location"
                                value={formData.location}
                                onChange={handleInputChange}
                                placeholder="Auto-filled from map"
                                required
                                disabled
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="area">Field Size (hectares) *</label>
                            <input
                                type="number"
                                id="area"
                                name="area"
                                value={formData.area}
                                onChange={handleInputChange}
                                placeholder="Auto-calculated from map"
                                step="0.1"
                                required
                                disabled
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="fertility_level">Soil Fertility Level *</label>
                            <select
                                id="fertility_level"
                                name="fertility_level"
                                value={formData.fertility_level}
                                onChange={handleInputChange}
                                required
                            >
                                <option value="">Select Fertility Level</option>
                                <option value="low">Low Fertility (Poor Soil)</option>
                                <option value="medium">Medium Fertility (Average Soil)</option>
                                <option value="high">High Fertility (Rich Soil)</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="soil_ph">Soil pH (Manual Entry) *</label>
                            <input
                                type="number"
                                id="soil_ph"
                                name="soil_ph"
                                value={formData.soil_ph}
                                onChange={handleInputChange}
                                placeholder="e.g., 6.5"
                                step="0.1"
                                min="0"
                                max="14"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="temperature">Temperature (°C) *</label>
                            <input
                                type="number"
                                id="temperature"
                                name="temperature"
                                value={formData.temperature}
                                onChange={handleInputChange}
                                placeholder="Auto-filled from weather API"
                                step="0.1"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="humidity">Humidity (%) *</label>
                            <input
                                type="number"
                                id="humidity"
                                name="humidity"
                                value={formData.humidity}
                                onChange={handleInputChange}
                                placeholder="Auto-filled from weather API"
                                step="0.1"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="rainfall">Rainfall (mm) *</label>
                            <input
                                type="number"
                                id="rainfall"
                                name="rainfall"
                                value={formData.rainfall}
                                onChange={handleInputChange}
                                placeholder="Auto-filled from weather API"
                                step="0.1"
                                required
                            />
                        </div>

                        {/* Display N, P, K values based on fertility level */}
                        {formData.fertility_level && (
                            <>
                                <div className="form-group">
                                    <label htmlFor="nitrogen">Nitrogen (N) kg/ha</label>
                                    <input
                                        type="number"
                                        id="nitrogen"
                                        name="nitrogen"
                                        value={formData.nitrogen}
                                        onChange={handleInputChange}
                                        step="0.1"
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="phosphorus">Phosphorus (P) kg/ha</label>
                                    <input
                                        type="number"
                                        id="phosphorus"
                                        name="phosphorus"
                                        value={formData.phosphorus}
                                        onChange={handleInputChange}
                                        step="0.1"
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="potassium">Potassium (K) kg/ha</label>
                                    <input
                                        type="number"
                                        id="potassium"
                                        name="potassium"
                                        value={formData.potassium}
                                        onChange={handleInputChange}
                                        step="0.1"
                                    />
                                </div>
                            </>
                        )}


                    </div>
                </div>

                <button 
                    type="submit" 
                    className="generate-btn"
                    disabled={loading}
                >
                    {loading ? '🤖 Analyzing...' : '🚀 Get Crop Recommendations'}
                </button>
                {weatherDataLoading && (
                    <p className="form-hint">🔄 Fetching 6-month weather data (temperature, humidity, rainfall)...</p>
                )}
                {!weatherDataFetched && !weatherDataLoading && (
                    <p className="form-hint">📍 Please select a field from the list to fetch weather data</p>
                )}
                {weatherDataFetched && !weatherDataLoading && (
                    <p className="form-hint">✅ Weather data loaded for last 6 months - Ready to generate recommendations!</p>
                )}
            </form>

            {error && (
                <div className="error-message">
                    <span className="error-icon">⚠️</span>
                    {error}
                </div>
            )}

           {recommendations && (
    <div className="recommendations-container">
        {recommendations?.recommended_crops?.length > 0 &&
            renderCropRecommendations(recommendations.recommended_crops)
        }
        <div className="analysis-cards">
            {recommendations.land_analysis && renderAnalysisSection('Land Analysis', recommendations.land_analysis, '🌍')}
            {recommendations.season_analysis && renderAnalysisSection('Season Analysis', recommendations.season_analysis, '🌤️')}
            {recommendations.market_insights && renderAnalysisSection('Market Insights', recommendations.market_insights, '📈')}
        </div>
        <div className="analysis-cards">
            {recommendations.action_plan && renderAnalysisSection('Action Plan', recommendations.action_plan, '📋')}
            {recommendations.sustainability_advice && renderAnalysisSection('Sustainability Advice', recommendations.sustainability_advice, '♻️')}
        </div>
    </div>
)}
        </div>
    );
};

export default CropSuggestion;
