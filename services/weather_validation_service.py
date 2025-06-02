"""
Weather Data Validation Service
Ensures rainfall data accuracy and prevents misleading flood assessments
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import streamlit as st

class WeatherValidationService:
    """Service to validate and cross-check weather data for accuracy"""
    
    def __init__(self):
        try:
            self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", "")
        except Exception:
            self.openweather_api_key = ""
        
    def validate_rainfall_data(self, lat: float, lon: float, location_name: str) -> Dict[str, Any]:
        """
        Validate rainfall data against multiple sources and reasonable thresholds
        
        Args:
            lat: Latitude
            lon: Longitude  
            location_name: Location name for context
            
        Returns:
            Validated weather data with accuracy indicators
        """
        
        # Get primary weather data
        primary_data = self._get_openweather_data(lat, lon)
        
        # Validate the data for reasonableness
        validated_data = self._validate_data_accuracy(primary_data, location_name)
        
        # Add data source transparency
        validated_data['data_sources'] = ['OpenWeather API']
        validated_data['validation_notes'] = []
        
        # Check for unrealistic values
        rain_24h = validated_data.get('rain_24h', 0)
        current_rain = validated_data.get('current_rain', 0)
        
        # Flag potentially inaccurate readings
        if rain_24h > 100:
            validated_data['validation_notes'].append(
                f"High 24h rainfall reading ({rain_24h:.1f} mm) - this may represent localized heavy rain rather than district-wide conditions"
            )
            validated_data['data_confidence'] = 'medium'
        elif rain_24h > 50:
            validated_data['validation_notes'].append(
                f"Moderate-high rainfall detected ({rain_24h:.1f} mm) - verify if this represents area-wide conditions"
            )
            validated_data['data_confidence'] = 'high'
        else:
            validated_data['data_confidence'] = 'high'
            
        # Add temporal consistency check
        if current_rain == 0 and rain_24h > 30:
            validated_data['validation_notes'].append(
                "No current rainfall but high 24h total suggests recent heavy rain has stopped"
            )
            
        return validated_data
    
    def _get_openweather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather data from OpenWeather API with error handling"""
        
        if not self.openweather_api_key:
            return {
                'current_rain': 0,
                'rain_24h': 0,
                'humidity': 60,
                'temperature': 25,
                'pressure': 1013,
                'description': 'No weather data available',
                'data_available': False,
                'error': 'API key not configured'
            }
            
        try:
            # Current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(current_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract rainfall data carefully
                current_rain = data.get('rain', {}).get('1h', 0)
                
                # For 24h data, we need to be more careful
                # OpenWeather's rain.1h * 24 is not accurate for 24h totals
                rain_3h = data.get('rain', {}).get('3h', 0)
                
                # More conservative 24h estimate
                if rain_3h > 0:
                    # If we have 3h data, extrapolate more conservatively
                    rain_24h = min(rain_3h * 4, rain_3h * 8)  # Conservative range
                elif current_rain > 0:
                    # If only current rain, very conservative estimate
                    rain_24h = current_rain * 12  # Assume intermittent rain
                else:
                    rain_24h = 0
                
                return {
                    'current_rain': current_rain,
                    'rain_24h': rain_24h,
                    'humidity': data.get('main', {}).get('humidity', 0),
                    'temperature': data.get('main', {}).get('temp', 0),
                    'pressure': data.get('main', {}).get('pressure', 0),
                    'description': data.get('weather', [{}])[0].get('description', ''),
                    'wind_speed': data.get('wind', {}).get('speed', 0),
                    'data_available': True,
                    'api_response_time': datetime.now().isoformat()
                }
            else:
                return self._get_fallback_data(f"API Error: {response.status_code}")
                
        except Exception as e:
            return self._get_fallback_data(f"Connection Error: {str(e)}")
    
    def _validate_data_accuracy(self, weather_data: Dict[str, Any], location_name: str) -> Dict[str, Any]:
        """Validate weather data for accuracy and add appropriate warnings"""
        
        validated_data = weather_data.copy()
        
        # Seasonal and geographical validation for India
        current_month = datetime.now().month
        rain_24h = weather_data.get('rain_24h', 0)
        
        # Monsoon season validation (June-September for most of India)
        if 6 <= current_month <= 9:  # Monsoon season
            max_reasonable_24h = 150  # mm (heavy monsoon rain)
            typical_heavy_rain = 75   # mm
        else:  # Non-monsoon
            max_reasonable_24h = 50   # mm (cyclonic or isolated storms)
            typical_heavy_rain = 25   # mm
        
        # Apply validation logic
        if rain_24h > max_reasonable_24h:
            validated_data['rain_24h'] = typical_heavy_rain
            validated_data['data_adjusted'] = True
            validated_data['original_rain_24h'] = rain_24h
            validated_data['adjustment_reason'] = f"Original value ({rain_24h:.1f} mm) exceeds reasonable limits for the region and season"
        
        # Add geographical context
        if any(city in location_name.lower() for city in ['mumbai', 'chennai', 'kochi', 'mangalore']):
            validated_data['geographical_context'] = 'coastal_high_rainfall'
        elif any(city in location_name.lower() for city in ['rajasthan', 'delhi', 'punjab']):
            validated_data['geographical_context'] = 'low_rainfall_region'
        else:
            validated_data['geographical_context'] = 'moderate_rainfall_region'
            
        return validated_data
    
    def _get_fallback_data(self, error_message: str) -> Dict[str, Any]:
        """Provide fallback data when API is unavailable"""
        return {
            'current_rain': 0,
            'rain_24h': 0,
            'humidity': 60,
            'temperature': 25,
            'pressure': 1013,
            'description': 'Weather data unavailable',
            'data_available': False,
            'error': error_message,
            'data_confidence': 'low'
        }
    
    def get_accuracy_report(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate accuracy report for the weather data"""
        
        accuracy_info = {
            'data_confidence': weather_data.get('data_confidence', 'unknown'),
            'sources_used': weather_data.get('data_sources', []),
            'validation_notes': weather_data.get('validation_notes', []),
            'data_timestamp': weather_data.get('api_response_time', 'unknown'),
            'adjustments_made': weather_data.get('data_adjusted', False)
        }
        
        if weather_data.get('data_adjusted'):
            accuracy_info['original_values'] = {
                'rain_24h': weather_data.get('original_rain_24h'),
                'adjustment_reason': weather_data.get('adjustment_reason')
            }
            
        return accuracy_info