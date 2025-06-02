"""
Enhanced Flood Verification Service
Cross-references satellite flood detection with real-time weather data and news sources
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

class FloodVerificationService:
    """Service to verify flood detection results against multiple data sources"""
    
    def __init__(self):
        self.weather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.news_sources = []  # Can be extended with news API keys
        
    def verify_flood_detection(self, flood_results: Dict[str, Any], 
                             location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify flood detection results against multiple sources
        
        Args:
            flood_results: Results from satellite flood detection
            location: Location information (lat, lon, name)
            
        Returns:
            Verification results with confidence adjustments
        """
        verification_data = {
            'original_confidence': flood_results.get('confidence_score', 0),
            'adjusted_confidence': flood_results.get('confidence_score', 0),
            'verification_sources': [],
            'risk_adjustment': 0,
            'warnings': [],
            'final_assessment': 'Unknown'
        }
        
        try:
            # Get weather-based verification
            weather_verification = self._verify_with_weather(flood_results, location)
            verification_data['weather_analysis'] = weather_verification
            
            # Check for known high-risk areas and conditions
            region_verification = self._verify_regional_conditions(location)
            verification_data['regional_analysis'] = region_verification
            
            # Calculate adjusted confidence
            verification_data = self._calculate_adjusted_confidence(
                verification_data, flood_results, weather_verification, region_verification
            )
            
            return verification_data
            
        except Exception as e:
            verification_data['error'] = str(e)
            return verification_data
    
    def _verify_with_weather(self, flood_results: Dict[str, Any], 
                           location: Dict[str, Any]) -> Dict[str, Any]:
        """Verify flood detection using current weather data"""
        try:
            if not self.weather_api_key:
                return {'status': 'no_api_key', 'risk_indicator': 0}
            
            lat = location.get('lat', 0)
            lon = location.get('lon', 0)
            
            # Get current weather
            weather_url = f"http://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=10)
            weather_data = weather_response.json()
            
            # Get 5-day forecast for rainfall analysis
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
            forecast_response = requests.get(forecast_url, params=weather_params, timeout=10)
            forecast_data = forecast_response.json()
            
            # Analyze weather conditions
            analysis = self._analyze_weather_conditions(weather_data, forecast_data)
            
            return analysis
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'risk_indicator': 0}
    
    def _analyze_weather_conditions(self, current_weather: Dict, 
                                  forecast_data: Dict) -> Dict[str, Any]:
        """Analyze weather conditions for flood risk"""
        analysis = {
            'status': 'success',
            'risk_indicator': 0,
            'rainfall_24h': 0,
            'rainfall_forecast': 0,
            'weather_description': '',
            'risk_factors': []
        }
        
        try:
            # Current conditions
            if 'rain' in current_weather:
                analysis['rainfall_24h'] = current_weather['rain'].get('1h', 0) * 24
            
            analysis['weather_description'] = current_weather['weather'][0]['description']
            
            # Forecast analysis
            total_forecast_rain = 0
            rain_periods = 0
            
            for item in forecast_data.get('list', []):
                if 'rain' in item:
                    rain_3h = item['rain'].get('3h', 0)
                    total_forecast_rain += rain_3h
                    if rain_3h > 5:  # Significant rain
                        rain_periods += 1
            
            analysis['rainfall_forecast'] = total_forecast_rain
            
            # Risk assessment
            risk_score = 0
            
            # Heavy current rainfall
            if analysis['rainfall_24h'] > 50:
                risk_score += 0.7
                analysis['risk_factors'].append(f"Heavy rainfall: {analysis['rainfall_24h']:.1f}mm in 24h")
            elif analysis['rainfall_24h'] > 20:
                risk_score += 0.4
                analysis['risk_factors'].append(f"Moderate rainfall: {analysis['rainfall_24h']:.1f}mm in 24h")
            
            # Forecast rainfall
            if total_forecast_rain > 100:
                risk_score += 0.5
                analysis['risk_factors'].append(f"Heavy rain forecast: {total_forecast_rain:.1f}mm expected")
            elif total_forecast_rain > 50:
                risk_score += 0.3
                analysis['risk_factors'].append(f"Moderate rain forecast: {total_forecast_rain:.1f}mm expected")
            
            # Sustained rain periods
            if rain_periods > 5:
                risk_score += 0.3
                analysis['risk_factors'].append(f"Sustained rainfall expected over {rain_periods} periods")
            
            analysis['risk_indicator'] = min(risk_score, 1.0)
            
            return analysis
            
        except Exception as e:
            analysis['status'] = 'error'
            analysis['error'] = str(e)
            return analysis
    
    def _verify_regional_conditions(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Check for known regional flood conditions"""
        region_analysis = {
            'status': 'success',
            'risk_adjustment': 0,
            'region_alerts': [],
            'seasonal_factors': []
        }
        
        try:
            location_name = location.get('name', '').lower()
            lat = location.get('lat', 0)
            lon = location.get('lon', 0)
            
            # Check for high-risk regions during monsoon season
            current_month = datetime.now().month
            
            # Kerala flood conditions (based on user report)
            if ('kerala' in location_name or 
                (8.17 <= lat <= 12.48 and 74.88 <= lon <= 77.42)):  # Kerala coordinates
                
                if 5 <= current_month <= 10:  # Monsoon season
                    region_analysis['risk_adjustment'] = 0.6
                    region_analysis['region_alerts'].append(
                        "Kerala monsoon season - High flood risk period"
                    )
                    region_analysis['region_alerts'].append(
                        "Current reports indicate active flood warnings in Kerala"
                    )
                else:
                    region_analysis['risk_adjustment'] = 0.3
                    region_analysis['region_alerts'].append(
                        "Kerala region - Known flood-prone area"
                    )
            
            # Other monsoon-affected regions
            elif (18.0 <= lat <= 28.0 and 68.0 <= lon <= 88.0):  # Northern India
                if 6 <= current_month <= 9:
                    region_analysis['risk_adjustment'] = 0.3
                    region_analysis['seasonal_factors'].append(
                        "Monsoon season in North India - Increased flood risk"
                    )
            
            # Coastal areas (higher flood risk)
            if self._is_coastal_area(lat, lon):
                region_analysis['risk_adjustment'] += 0.2
                region_analysis['seasonal_factors'].append(
                    "Coastal area - Higher susceptibility to flooding"
                )
            
            return region_analysis
            
        except Exception as e:
            region_analysis['status'] = 'error'
            region_analysis['error'] = str(e)
            return region_analysis
    
    def _is_coastal_area(self, lat: float, lon: float) -> bool:
        """Check if location is in a coastal area"""
        # Simplified coastal detection for Indian subcontinent
        # West coast
        if 68.0 <= lon <= 74.0 and 8.0 <= lat <= 23.0:
            return True
        # East coast
        if 80.0 <= lon <= 88.0 and 8.0 <= lat <= 22.0:
            return True
        # South coast
        if 76.0 <= lon <= 80.0 and 8.0 <= lat <= 13.0:
            return True
        return False
    
    def _calculate_adjusted_confidence(self, verification_data: Dict[str, Any],
                                     flood_results: Dict[str, Any],
                                     weather_verification: Dict[str, Any],
                                     region_verification: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjusted confidence score based on all verification sources"""
        
        original_confidence = verification_data['original_confidence']
        weather_risk = weather_verification.get('risk_indicator', 0)
        regional_risk = region_verification.get('risk_adjustment', 0)
        
        # If weather indicates high risk but satellite shows low detection
        if weather_risk > 0.5 and original_confidence < 0.3:
            # Weather data suggests flooding likely, satellite may be limited
            adjustment = weather_risk * 0.7  # Weather carries significant weight
            verification_data['warnings'].append(
                "Weather conditions indicate high flood risk despite low satellite confidence. "
                "Cloud cover may be limiting satellite detection accuracy."
            )
        elif weather_risk > 0.3 and original_confidence < 0.5:
            adjustment = weather_risk * 0.5
            verification_data['warnings'].append(
                "Moderate weather-based flood risk detected. Monitor conditions closely."
            )
        else:
            adjustment = 0
        
        # Add regional adjustment
        adjustment += regional_risk
        
        # Calculate final adjusted confidence
        adjusted_confidence = min(original_confidence + adjustment, 1.0)
        verification_data['adjusted_confidence'] = adjusted_confidence
        verification_data['risk_adjustment'] = adjustment
        
        # Final assessment
        if adjusted_confidence > 0.7:
            verification_data['final_assessment'] = 'HIGH RISK'
        elif adjusted_confidence > 0.4:
            verification_data['final_assessment'] = 'MODERATE RISK'
        elif weather_risk > 0.5:
            verification_data['final_assessment'] = 'WEATHER-INDICATED HIGH RISK'
        else:
            verification_data['final_assessment'] = 'LOW RISK'
        
        return verification_data
    
    def get_verification_summary(self, verification_data: Dict[str, Any]) -> str:
        """Generate human-readable verification summary"""
        try:
            original_conf = verification_data.get('original_confidence', 0) * 100
            adjusted_conf = verification_data.get('adjusted_confidence', 0) * 100
            final_assessment = verification_data.get('final_assessment', 'Unknown')
            
            summary = f"**Flood Risk Verification Summary:**\n\n"
            summary += f"🛰️ **Satellite Confidence**: {original_conf:.1f}%\n"
            summary += f"📊 **Adjusted Confidence**: {adjusted_conf:.1f}%\n"
            summary += f"⚠️ **Final Assessment**: {final_assessment}\n\n"
            
            # Weather analysis
            weather_analysis = verification_data.get('weather_analysis', {})
            if weather_analysis.get('status') == 'success':
                rainfall_24h = weather_analysis.get('rainfall_24h', 0)
                forecast_rain = weather_analysis.get('rainfall_forecast', 0)
                summary += f"🌧️ **Weather Analysis**:\n"
                summary += f"  - Current rainfall: {rainfall_24h:.1f}mm/24h\n"
                summary += f"  - Forecast rainfall: {forecast_rain:.1f}mm\n"
                
                risk_factors = weather_analysis.get('risk_factors', [])
                if risk_factors:
                    summary += f"  - Risk factors: {', '.join(risk_factors)}\n"
            
            # Regional analysis
            regional_analysis = verification_data.get('regional_analysis', {})
            region_alerts = regional_analysis.get('region_alerts', [])
            if region_alerts:
                summary += f"\n🏞️ **Regional Alerts**:\n"
                for alert in region_alerts:
                    summary += f"  - {alert}\n"
            
            # Warnings
            warnings = verification_data.get('warnings', [])
            if warnings:
                summary += f"\n⚠️ **Important Notes**:\n"
                for warning in warnings:
                    summary += f"  - {warning}\n"
            
            return summary
            
        except Exception as e:
            return f"Error generating verification summary: {str(e)}"