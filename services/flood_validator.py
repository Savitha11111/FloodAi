"""
Enhanced Flood Data Validator
Cross-references multiple sources for accurate flood detection
"""

import requests
import os
from datetime import datetime
from typing import Dict, Any, List
import json

class FloodDataValidator:
    """Validates flood data across multiple sources for enhanced accuracy"""
    
    def __init__(self):
        self.ambee_api_key = os.getenv('AMBEE_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        
    def validate_flood_conditions(self, lat: float, lon: float, location_name: str = None) -> Dict[str, Any]:
        """
        Cross-validate flood conditions using multiple data sources
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Optional location name for better context
            
        Returns:
            Comprehensive flood validation results
        """
        validation_results = {
            'location': {'lat': lat, 'lon': lon, 'name': location_name},
            'timestamp': datetime.now().isoformat(),
            'sources_checked': [],
            'validation_score': 0,
            'flood_indicators': [],
            'final_assessment': {}
        }
        
        # Source 1: Enhanced precipitation analysis
        precip_data = self._validate_precipitation_levels(lat, lon)
        validation_results['sources_checked'].append('precipitation_analysis')
        
        # Source 2: Multi-source weather alerts
        weather_alerts = self._check_weather_alerts(lat, lon)
        validation_results['sources_checked'].append('weather_alerts')
        
        # Source 3: Regional disaster patterns
        disaster_patterns = self._analyze_regional_patterns(lat, lon)
        validation_results['sources_checked'].append('disaster_patterns')
        
        # Source 4: Precipitation intensity validation
        intensity_check = self._validate_precipitation_intensity(lat, lon)
        validation_results['sources_checked'].append('precipitation_intensity')
        
        # Combine all indicators
        all_indicators = []
        all_indicators.extend(precip_data.get('indicators', []))
        all_indicators.extend(weather_alerts.get('indicators', []))
        all_indicators.extend(disaster_patterns.get('indicators', []))
        all_indicators.extend(intensity_check.get('indicators', []))
        
        validation_results['flood_indicators'] = all_indicators
        
        # Calculate comprehensive validation score
        validation_score = self._calculate_validation_score(
            precip_data, weather_alerts, disaster_patterns, intensity_check
        )
        validation_results['validation_score'] = validation_score
        
        # Generate final flood assessment
        final_assessment = self._generate_final_assessment(
            validation_score, all_indicators, precip_data, weather_alerts
        )
        validation_results['final_assessment'] = final_assessment
        
        return validation_results
    
    def _validate_precipitation_levels(self, lat: float, lon: float) -> Dict[str, Any]:
        """Validate precipitation levels using multiple weather sources"""
        try:
            # Primary weather data
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            current_data = response.json()
            
            # Forecast data for 24h precipitation
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
            forecast_response = requests.get(forecast_url, params=params, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Calculate enhanced precipitation metrics
            current_rain = current_data.get('rain', {}).get('1h', 0)
            
            # Calculate 24h total from forecast
            total_24h = 0
            for entry in forecast_data.get('list', [])[:8]:  # 24 hours
                rain_3h = entry.get('rain', {}).get('3h', 0)
                total_24h += rain_3h
            
            # Enhanced precipitation analysis
            indicators = []
            if total_24h > 100:
                indicators.append('critical_rainfall_detected')
            elif total_24h > 50:
                indicators.append('heavy_rainfall_detected')
            elif total_24h > 25:
                indicators.append('moderate_rainfall_detected')
            
            if current_rain > 10:
                indicators.append('intense_current_rainfall')
            
            return {
                'precipitation_24h': total_24h,
                'current_intensity': current_rain,
                'indicators': indicators,
                'confidence': 0.8 if total_24h > 0 else 0.3
            }
            
        except Exception as e:
            return {
                'precipitation_24h': 0,
                'current_intensity': 0,
                'indicators': ['precipitation_data_unavailable'],
                'confidence': 0.1,
                'error': str(e)
            }
    
    def _check_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Check for weather alerts and warnings"""
        try:
            # Use Ambee weather API for alerts
            url = f"https://api.ambeedata.com/weather/latest/by-lat-lng"
            headers = {
                'x-api-key': self.ambee_api_key,
                'Content-Type': 'application/json'
            }
            params = {'lat': lat, 'lng': lon}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            
            indicators = []
            confidence = 0.5
            
            # Analyze weather conditions
            if 'data' in weather_data:
                data = weather_data['data']
                
                # Check for high precipitation
                precipitation = data.get('precipitation', 0)
                if precipitation > 50:
                    indicators.append('high_precipitation_alert')
                    confidence = 0.9
                elif precipitation > 25:
                    indicators.append('moderate_precipitation_alert')
                    confidence = 0.7
                
                # Check humidity and pressure
                humidity = data.get('humidity', 0)
                if humidity > 90:
                    indicators.append('extreme_humidity_conditions')
                
            return {
                'indicators': indicators,
                'confidence': confidence,
                'weather_data': weather_data.get('data', {})
            }
            
        except Exception as e:
            return {
                'indicators': ['weather_alerts_unavailable'],
                'confidence': 0.2,
                'error': str(e)
            }
    
    def _analyze_regional_patterns(self, lat: float, lon: float) -> Dict[str, Any]:
        """Analyze regional disaster patterns"""
        try:
            # Check for nearby disaster events
            url = f"https://api.ambeedata.com/disasters/latest/by-lat-lng"
            headers = {
                'x-api-key': self.ambee_api_key,
                'Content-Type': 'application/json'
            }
            params = {'lat': lat, 'lng': lon, 'limit': 20}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            disaster_data = response.json()
            
            indicators = []
            confidence = 0.3
            
            if 'result' in disaster_data:
                events = disaster_data['result']
                
                # Count flood-related events
                flood_events = 0
                severe_weather_events = 0
                
                for event in events:
                    event_type = event.get('event_type', '').upper()
                    event_name = event.get('event_name', '').lower()
                    
                    if 'flood' in event_name or event_type == 'FL':
                        flood_events += 1
                    
                    if any(term in event_name for term in ['heavy rain', 'thunderstorm', 'cyclone']):
                        severe_weather_events += 1
                
                if flood_events > 0:
                    indicators.append('flood_events_in_region')
                    confidence = 0.8
                
                if severe_weather_events > 2:
                    indicators.append('multiple_severe_weather_events')
                    confidence = max(confidence, 0.6)
            
            return {
                'indicators': indicators,
                'confidence': confidence,
                'events_analyzed': len(disaster_data.get('result', []))
            }
            
        except Exception as e:
            return {
                'indicators': ['regional_analysis_unavailable'],
                'confidence': 0.1,
                'error': str(e)
            }
    
    def _validate_precipitation_intensity(self, lat: float, lon: float) -> Dict[str, Any]:
        """Validate precipitation intensity patterns"""
        try:
            # Get detailed forecast for intensity analysis
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            forecast_data = response.json()
            
            indicators = []
            max_intensity = 0
            sustained_periods = 0
            
            # Analyze hourly patterns
            for entry in forecast_data.get('list', [])[:16]:  # 48 hours
                rain_3h = entry.get('rain', {}).get('3h', 0)
                hourly_rate = rain_3h / 3  # Convert to hourly
                
                max_intensity = max(max_intensity, hourly_rate)
                
                if hourly_rate > 10:  # Heavy rain threshold
                    sustained_periods += 1
            
            if max_intensity > 20:
                indicators.append('extreme_intensity_detected')
            elif max_intensity > 10:
                indicators.append('high_intensity_detected')
            
            if sustained_periods > 4:
                indicators.append('sustained_heavy_rainfall')
            
            confidence = min(0.9, max_intensity / 25) if max_intensity > 0 else 0.2
            
            return {
                'max_intensity_mm_h': max_intensity,
                'sustained_periods': sustained_periods,
                'indicators': indicators,
                'confidence': confidence
            }
            
        except Exception as e:
            return {
                'max_intensity_mm_h': 0,
                'sustained_periods': 0,
                'indicators': ['intensity_analysis_unavailable'],
                'confidence': 0.1,
                'error': str(e)
            }
    
    def _calculate_validation_score(self, precip_data: Dict, weather_alerts: Dict, 
                                  disaster_patterns: Dict, intensity_check: Dict) -> float:
        """Calculate comprehensive validation score"""
        base_score = 0.0
        
        # Precipitation weight (40%)
        precip_confidence = precip_data.get('confidence', 0)
        precip_24h = precip_data.get('precipitation_24h', 0)
        precip_score = min(1.0, precip_24h / 100) * precip_confidence
        base_score += precip_score * 0.4
        
        # Weather alerts weight (25%)
        alert_confidence = weather_alerts.get('confidence', 0)
        alert_indicators = len(weather_alerts.get('indicators', []))
        alert_score = min(1.0, alert_indicators / 3) * alert_confidence
        base_score += alert_score * 0.25
        
        # Regional patterns weight (20%)
        pattern_confidence = disaster_patterns.get('confidence', 0)
        pattern_indicators = len(disaster_patterns.get('indicators', []))
        pattern_score = min(1.0, pattern_indicators / 2) * pattern_confidence
        base_score += pattern_score * 0.2
        
        # Intensity validation weight (15%)
        intensity_confidence = intensity_check.get('confidence', 0)
        intensity_indicators = len(intensity_check.get('indicators', []))
        intensity_score = min(1.0, intensity_indicators / 2) * intensity_confidence
        base_score += intensity_score * 0.15
        
        return min(1.0, base_score)
    
    def _generate_final_assessment(self, validation_score: float, indicators: List[str], 
                                 precip_data: Dict, weather_alerts: Dict) -> Dict[str, Any]:
        """Generate final flood risk assessment with enhanced accuracy"""
        
        # Enhanced risk determination with lower thresholds for better detection
        precipitation = precip_data.get('precipitation_24h', 0)
        
        # Lower thresholds for more sensitive flood detection
        if (validation_score > 0.6 or 
            precipitation > 75 or 
            any('critical' in i or 'extreme' in i for i in indicators)):
            risk_level = 'very_high'
            risk_color = '🔴'
        elif (validation_score > 0.3 or 
              precipitation > 40 or 
              any('heavy' in i or 'high' in i for i in indicators)):
            risk_level = 'high'
            risk_color = '🟠'
        elif (validation_score > 0.15 or 
              precipitation > 20 or 
              any('moderate' in i for i in indicators)):
            risk_level = 'moderate'
            risk_color = '🟡'
        elif validation_score > 0.05 or precipitation > 5:
            risk_level = 'low'
            risk_color = '🟢'
        else:
            risk_level = 'minimal'
            risk_color = '⚪'
        
        # Calculate affected area estimate
        precipitation = precip_data.get('precipitation_24h', 0)
        affected_area = max(1.0, precipitation / 10, validation_score * 50)
        
        # Generate description
        critical_indicators = [i for i in indicators if 'critical' in i or 'extreme' in i]
        description = f"Validation score: {validation_score:.2f} based on {len(indicators)} indicators"
        
        if critical_indicators:
            description += f". Critical conditions detected: {', '.join(critical_indicators)}"
        
        return {
            'risk_level': risk_level,
            'risk_color': risk_color,
            'validation_score': validation_score,
            'confidence_percentage': int(validation_score * 100),
            'affected_area_km2': round(affected_area, 1),
            'precipitation_24h': precip_data.get('precipitation_24h', 0),
            'description': description,
            'critical_indicators': critical_indicators,
            'total_indicators': len(indicators)
        }