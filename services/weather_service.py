import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

class WeatherService:
    """Service for fetching and processing weather data for flood verification"""
    
    def __init__(self):
        """Initialize weather service with API credentials"""
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.historical_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
        
        # Weather thresholds for flood correlation
        self.heavy_rain_threshold = 10.0  # mm/hour
        self.flood_risk_rain_24h = 50.0   # mm/24h
        self.storm_wind_threshold = 15.0  # m/s
        
        if not self.api_key:
            raise ValueError("OpenWeather API key not provided. Please set OPENWEATHER_API_KEY environment variable.")
    
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather conditions for flood verification
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing current weather data and flood correlation metrics
        """
        try:
            # Fetch current weather
            current_data = self._fetch_current_weather(lat, lon)
            
            # Fetch recent precipitation data
            precipitation_data = self._fetch_precipitation_data(lat, lon)
            
            # Get forecast for flood risk assessment
            forecast_data = self._fetch_forecast_data(lat, lon)
            
            # Calculate flood verification metrics
            verification_metrics = self._calculate_verification_metrics(
                current_data, precipitation_data, forecast_data
            )
            
            # Combine all data
            weather_result = {
                'current_conditions': current_data,
                'precipitation': precipitation_data,
                'forecast': forecast_data,
                'verification_metrics': verification_metrics,
                'timestamp': datetime.now().isoformat(),
                'location': {'lat': lat, 'lon': lon}
            }
            
            # Add flood correlation analysis
            weather_result.update(self._analyze_flood_correlation(weather_result))
            
            return weather_result
            
        except Exception as e:
            raise Exception(f"Weather data fetch failed: {str(e)}")
    
    def _fetch_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch current weather conditions"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant weather information
            current_weather = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'wind_direction': data['wind'].get('deg', 0),
                'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
                'cloud_cover': data['clouds']['all'],
                'weather_condition': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'current_rain': data.get('rain', {}).get('1h', 0),  # mm/h
                'current_snow': data.get('snow', {}).get('1h', 0),  # mm/h
                'feels_like': data['main']['feels_like'],
                'timestamp': datetime.fromtimestamp(data['dt']).isoformat()
            }
            
            return current_weather
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch current weather: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected weather data format: {str(e)}")
    
    def _fetch_precipitation_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch recent and current precipitation data using multiple sources"""
        try:
            # Get comprehensive weather data including historical precipitation
            current_url = f"{self.base_url}/weather"
            forecast_url = self.forecast_url
            
            # Fetch current conditions with precipitation
            current_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            current_response = requests.get(current_url, params=current_params, timeout=10)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Fetch forecast data for 24h precipitation analysis
            forecast_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Extract current precipitation data
            rain_1h = current_data.get('rain', {}).get('1h', 0)
            rain_3h = current_data.get('rain', {}).get('3h', 0)
            
            # Calculate 24h precipitation from forecast data
            rain_24h = 0
            now = datetime.now()
            
            # Sum precipitation from last 24 hours of forecast entries
            for entry in forecast_data.get('list', []):
                entry_time = datetime.fromtimestamp(entry['dt'])
                if (now - entry_time).total_seconds() <= 86400:  # 24 hours
                    entry_rain = entry.get('rain', {}).get('3h', 0)
                    rain_24h += entry_rain
            
            # If no recent data available, use alternative calculation
            if rain_24h == 0 and rain_3h > 0:
                # Estimate 24h rainfall based on current intensity
                rain_24h = rain_3h * 8  # Rough estimate for 24h period
            elif rain_24h == 0 and rain_1h > 0:
                # Conservative estimate based on hourly rate
                rain_24h = rain_1h * 12  # Conservative 12-hour equivalent
            
            return {
                'rain_1h': rain_1h,
                'rain_3h': rain_3h,
                'rain_24h': rain_24h,
                'intensity': self._classify_rain_intensity(rain_1h),
                'flood_risk': self._assess_precipitation_flood_risk(rain_1h, rain_24h),
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'rain_1h': 0,
                'rain_3h': 0,
                'rain_24h': 0,
                'intensity': 'unknown',
                'flood_risk': 'unknown',
                'error': f"Failed to fetch precipitation data: {str(e)}"
            }
    
    def _process_precipitation_data_legacy(self, data: Dict) -> Dict[str, Any]:
        """Legacy method for processing precipitation data"""
        try:
            # Initialize rain totals
            rain_1h = 0
            rain_3h = 0
            rain_24h = 0
            current_time = datetime.now()
            
            # Process forecast data to calculate precipitation totals
            for item in data.get('list', []):
                forecast_time = datetime.fromtimestamp(item['dt'])
                time_diff = (current_time - forecast_time).total_seconds() / 3600  # hours
                
                rain_amount = item.get('rain', {}).get('3h', 0)  # 3-hour precipitation
                
                if time_diff <= 1:
                    rain_1h += rain_amount
                if time_diff <= 3:
                    rain_3h += rain_amount
                if time_diff <= 24:
                    rain_24h += rain_amount
            
            precipitation_data = {
                'rain_1h': rain_1h,
                'rain_3h': rain_3h,
                'rain_24h': rain_24h,
                'is_raining': rain_1h > 0,
                'rain_intensity': self._classify_rain_intensity(rain_1h),
                'flood_risk_level': self._assess_precipitation_flood_risk(rain_1h, rain_24h)
            }
            
            return precipitation_data
            
        except Exception as e:
            print(f"Precipitation data fetch failed: {str(e)}")
            # Return default values if fetch fails
            return {
                'rain_1h': 0,
                'rain_3h': 0,
                'rain_24h': 0,
                'is_raining': False,
                'rain_intensity': 'none',
                'flood_risk_level': 'low'
            }
    
    def _fetch_forecast_data(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        """Fetch weather forecast for flood risk assessment"""
        try:
            url = self.forecast_url
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecast_list = []
            
            # Process next 7 days of forecast
            for item in data['list'][:24]:  # Next 3 days (8 intervals per day)
                forecast_time = datetime.fromtimestamp(item['dt'])
                
                forecast_item = {
                    'date': forecast_time.strftime('%Y-%m-%d'),
                    'time': forecast_time.strftime('%H:%M'),
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'precipitation': item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0),
                    'wind_speed': item['wind']['speed'],
                    'weather_condition': item['weather'][0]['main'],
                    'cloud_cover': item['clouds']['all'],
                    'timestamp': forecast_time.isoformat()
                }
                
                forecast_list.append(forecast_item)
            
            # Aggregate daily forecasts
            daily_forecasts = self._aggregate_daily_forecasts(forecast_list)
            
            return daily_forecasts
            
        except Exception as e:
            print(f"Forecast data fetch failed: {str(e)}")
            return []
    
    def _aggregate_daily_forecasts(self, hourly_forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate hourly forecasts into daily summaries"""
        try:
            daily_data = {}
            
            for item in hourly_forecasts:
                date = item['date']
                
                if date not in daily_data:
                    daily_data[date] = {
                        'date': date,
                        'temperatures': [],
                        'precipitation': 0,
                        'humidity': [],
                        'wind_speeds': [],
                        'conditions': []
                    }
                
                daily_data[date]['temperatures'].append(item['temperature'])
                daily_data[date]['precipitation'] += item['precipitation']
                daily_data[date]['humidity'].append(item['humidity'])
                daily_data[date]['wind_speeds'].append(item['wind_speed'])
                daily_data[date]['conditions'].append(item['weather_condition'])
            
            # Create daily summaries
            daily_forecasts = []
            for date, data in daily_data.items():
                summary = {
                    'date': date,
                    'temp_min': min(data['temperatures']),
                    'temp_max': max(data['temperatures']),
                    'temp_avg': sum(data['temperatures']) / len(data['temperatures']),
                    'precipitation': data['precipitation'],
                    'humidity_avg': sum(data['humidity']) / len(data['humidity']),
                    'wind_speed_max': max(data['wind_speeds']),
                    'dominant_condition': max(set(data['conditions']), key=data['conditions'].count),
                    'flood_risk': self._assess_daily_flood_risk(data['precipitation'])
                }
                daily_forecasts.append(summary)
            
            return daily_forecasts[:7]  # Return 7 days
            
        except Exception as e:
            print(f"Daily forecast aggregation failed: {str(e)}")
            return []
    
    def _classify_rain_intensity(self, rain_rate: float) -> str:
        """Classify rain intensity based on rate"""
        if rain_rate == 0:
            return 'none'
        elif rain_rate < 2.5:
            return 'light'
        elif rain_rate < 7.5:
            return 'moderate'
        elif rain_rate < 15:
            return 'heavy'
        else:
            return 'violent'
    
    def _assess_precipitation_flood_risk(self, rain_1h: float, rain_24h: float) -> str:
        """Assess flood risk based on precipitation"""
        if rain_1h > self.heavy_rain_threshold or rain_24h > self.flood_risk_rain_24h:
            return 'high'
        elif rain_1h > 5 or rain_24h > 25:
            return 'medium'
        else:
            return 'low'
    
    def _assess_daily_flood_risk(self, precipitation: float) -> str:
        """Assess daily flood risk based on total precipitation"""
        if precipitation > 30:
            return 'high'
        elif precipitation > 15:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_verification_metrics(self, current_data: Dict[str, Any],
                                      precipitation_data: Dict[str, Any],
                                      forecast_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate flood verification metrics based on weather conditions"""
        try:
            # Current conditions score
            current_score = 0.0
            
            # Rain contribution
            current_rain = current_data.get('current_rain', 0)
            rain_24h = precipitation_data.get('rain_24h', 0)
            
            if current_rain > self.heavy_rain_threshold:
                current_score += 0.4
            elif current_rain > 5:
                current_score += 0.2
            
            if rain_24h > self.flood_risk_rain_24h:
                current_score += 0.3
            elif rain_24h > 25:
                current_score += 0.15
            
            # Atmospheric pressure (low pressure can indicate storms)
            pressure = current_data.get('pressure', 1013)
            if pressure < 1000:
                current_score += 0.1
            elif pressure < 1005:
                current_score += 0.05
            
            # Wind conditions (storms can contribute to flooding)
            wind_speed = current_data.get('wind_speed', 0)
            if wind_speed > self.storm_wind_threshold:
                current_score += 0.1
            
            # Humidity (high humidity can indicate saturated conditions)
            humidity = current_data.get('humidity', 0)
            if humidity > 85:
                current_score += 0.1
            
            # Future risk assessment
            future_risk_score = 0.0
            for forecast in forecast_data[:3]:  # Next 3 days
                if forecast.get('precipitation', 0) > 20:
                    future_risk_score += 0.2
                elif forecast.get('precipitation', 0) > 10:
                    future_risk_score += 0.1
            
            # Overall verification score
            verification_score = min(1.0, current_score + future_risk_score * 0.3)
            
            return {
                'current_conditions_score': current_score,
                'future_risk_score': future_risk_score,
                'overall_verification_score': verification_score,
                'rain_contribution': min(0.7, (current_rain + rain_24h * 0.1) / 20),
                'atmospheric_contribution': min(0.2, (1013 - pressure) / 50),
                'storm_indicators': wind_speed > 10 or pressure < 1005,
                'flood_supporting_conditions': verification_score > 0.6
            }
            
        except Exception as e:
            print(f"Verification metrics calculation failed: {str(e)}")
            return {
                'current_conditions_score': 0.0,
                'future_risk_score': 0.0,
                'overall_verification_score': 0.0,
                'rain_contribution': 0.0,
                'atmospheric_contribution': 0.0,
                'storm_indicators': False,
                'flood_supporting_conditions': False
            }
    
    def analyze_flood_correlation(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Analyze flood correlation with current weather conditions
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with flood correlation analysis
        """
        try:
            # Get current weather data
            weather_data = self.get_current_weather(lat, lon)
            current_conditions = weather_data.get('current_conditions', {})
            precipitation = weather_data.get('precipitation', {})
            
            # Extract key metrics
            rain_24h = precipitation.get('rain_24h', 0)
            current_rain = current_conditions.get('current_rain', 0)
            temperature = current_conditions.get('temperature', 20)
            humidity = current_conditions.get('humidity', 60)
            pressure = current_conditions.get('pressure', 1013)
            
            # Calculate verification score based on conditions
            verification_score = 0.0
            
            # Heavy rainfall factor (most important for flooding)
            if rain_24h > 50:
                verification_score += 0.8  # Very high flood risk
            elif rain_24h > 25:
                verification_score += 0.6  # High flood risk
            elif rain_24h > 15:
                verification_score += 0.4  # Moderate flood risk
            elif rain_24h > 10:
                verification_score += 0.2  # Low-moderate flood risk
            
            # Current rainfall intensity
            if current_rain > 10:
                verification_score += 0.2
            elif current_rain > 5:
                verification_score += 0.1
            
            # Atmospheric conditions
            if pressure < 1000:
                verification_score += 0.1
            if humidity > 85:
                verification_score += 0.1
            
            # Cap the score at 1.0
            verification_score = min(1.0, verification_score)
            
            # Generate correlation analysis
            correlation_analysis = {
                'temperature': temperature,
                'temp_change': 0,  # Placeholder for temperature trend
                'humidity': humidity,
                'humidity_change': 0,  # Placeholder for humidity trend
                'pressure': pressure,
                'pressure_change': 0,  # Placeholder for pressure trend
                'current_rain': current_rain,
                'rain_change': 0,  # Placeholder for rain trend
                'rain_24h': rain_24h,
                'rain_24h_change': 0,  # Placeholder for 24h rain trend
                'verification_score': verification_score,
                'weather_supports_flood': verification_score > 0.6,
                'confidence_level': 'high' if verification_score > 0.8 else 'medium' if verification_score > 0.6 else 'low'
            }
            
            return correlation_analysis
            
        except Exception as e:
            print(f"Flood correlation analysis failed: {str(e)}")
            return {
                'verification_score': 0.5,
                'weather_supports_flood': False,
                'confidence_level': 'low',
                'rain_24h': 0,
                'current_rain': 0,
                'temperature': 20,
                'humidity': 60,
                'pressure': 1013
            }
            
        except Exception as e:
            print(f"Verification metrics calculation failed: {str(e)}")
            return {
                'overall_verification_score': 0.5,
                'flood_supporting_conditions': False
            }
    
    def _analyze_flood_correlation(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlation between weather conditions and flood detection"""
        try:
            verification_score = weather_data['verification_metrics']['overall_verification_score']
            current_conditions = weather_data['current_conditions']
            precipitation = weather_data['precipitation']
            
            # Calculate individual change indicators (simulated trends)
            temp_change = 1.2  # Placeholder for temperature trend
            humidity_change = 5   # Placeholder for humidity trend  
            pressure_change = -2  # Placeholder for pressure trend
            rain_change = 0.5     # Placeholder for rain trend
            rain_24h_change = 2.0 # Placeholder for 24h rain trend
            
            # Generate correlation analysis
            correlation_analysis = {
                'temperature': current_conditions.get('temperature', 20),
                'temp_change': temp_change,
                'humidity': current_conditions.get('humidity', 60),
                'humidity_change': humidity_change,
                'pressure': current_conditions.get('pressure', 1013),
                'pressure_change': pressure_change,
                'current_rain': current_conditions.get('current_rain', 0),
                'rain_change': rain_change,
                'rain_24h': precipitation.get('rain_24h', 0),
                'rain_24h_change': rain_24h_change,
                'verification_score': verification_score,
                'weather_supports_flood': verification_score > 0.6,
                'confidence_level': 'high' if verification_score > 0.8 else 'medium' if verification_score > 0.6 else 'low'
            }
            
            return correlation_analysis
            
        except Exception as e:
            print(f"Flood correlation analysis failed: {str(e)}")
            return {
                'verification_score': 0.5,
                'weather_supports_flood': False,
                'confidence_level': 'low'
            }
    
    def get_historical_weather(self, lat: float, lon: float, 
                              target_date: datetime) -> Dict[str, Any]:
        """Get historical weather data for a specific date"""
        try:
            # Calculate timestamp for the target date
            timestamp = int(target_date.timestamp())
            
            url = self.historical_url
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract historical data
            historical_data = {
                'date': target_date.strftime('%Y-%m-%d'),
                'temperature': data['current']['temp'],
                'humidity': data['current']['humidity'],
                'pressure': data['current']['pressure'],
                'wind_speed': data['current']['wind_speed'],
                'cloud_cover': data['current']['clouds'],
                'precipitation': data.get('hourly', [{}])[0].get('rain', {}).get('1h', 0),
                'weather_condition': data['current']['weather'][0]['main']
            }
            
            return historical_data
            
        except Exception as e:
            print(f"Historical weather fetch failed: {str(e)}")
            # Return estimated data if API fails
            return {
                'date': target_date.strftime('%Y-%m-%d'),
                'temperature': 22,
                'humidity': 65,
                'pressure': 1013,
                'wind_speed': 3,
                'cloud_cover': 50,
                'precipitation': 0,
                'weather_condition': 'Clear'
            }
    
    def assess_flood_weather_correlation(self, weather_data: Dict[str, Any],
                                       flood_confidence: float) -> Dict[str, Any]:
        """Assess how well weather conditions correlate with flood detection"""
        try:
            verification_score = weather_data.get('verification_score', 0.5)
            
            # Calculate correlation strength
            correlation_strength = (verification_score + flood_confidence) / 2
            
            # Determine correlation quality
            if correlation_strength > 0.8:
                correlation_quality = 'excellent'
                confidence_boost = 0.1
            elif correlation_strength > 0.6:
                correlation_quality = 'good'
                confidence_boost = 0.05
            elif correlation_strength > 0.4:
                correlation_quality = 'moderate'
                confidence_boost = 0.0
            else:
                correlation_quality = 'poor'
                confidence_boost = -0.1
            
            return {
                'correlation_strength': correlation_strength,
                'correlation_quality': correlation_quality,
                'confidence_adjustment': confidence_boost,
                'weather_verification_passed': verification_score > 0.6,
                'combined_confidence': min(1.0, max(0.0, flood_confidence + confidence_boost))
            }
            
        except Exception as e:
            print(f"Weather correlation assessment failed: {str(e)}")
            return {
                'correlation_strength': 0.5,
                'correlation_quality': 'unknown',
                'confidence_adjustment': 0.0,
                'combined_confidence': flood_confidence
            }
