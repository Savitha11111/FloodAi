"""
Ambee Flood API Service
Real-time flood data integration for enhanced accuracy
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

class AmbeeFloodService:
    """Service for fetching real-time flood data from Ambee API"""
    
    def __init__(self):
        self.api_key = os.getenv('AMBEE_API_KEY')
        self.base_url = "https://api.ambeedata.com"
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
    def get_current_flood_data(self, lat: float, lon: float, radius: int = 50) -> Dict[str, Any]:
        """
        Get current flood data for a location using real-time Ambee data
        
        Args:
            lat: Latitude
            lon: Longitude  
            radius: Search radius in kilometers
            
        Returns:
            Current flood data from Ambee API with enhanced accuracy
        """
        try:
            # Get comprehensive disaster data including floods
            endpoint = f"{self.base_url}/disasters/latest/by-lat-lng"
            params = {
                'lat': lat,
                'lng': lon,
                'limit': 20  # Increased limit for better coverage
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            disaster_data = response.json()
            
            # Also get weather-based flood indicators
            weather_endpoint = f"{self.base_url}/weather/latest/by-lat-lng"
            weather_params = {
                'lat': lat,
                'lng': lon
            }
            
            weather_response = requests.get(weather_endpoint, headers=self.headers, params=weather_params, timeout=30)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            # Process and combine both data sources for enhanced accuracy
            processed_data = self._process_comprehensive_flood_data(disaster_data, weather_data, lat, lon)
            
            return processed_data
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': f"API request failed: {str(e)}",
                'flood_events': [],
                'risk_level': 'unknown'
            }
        except Exception as e:
            return {
                'status': 'error', 
                'error': f"Processing error: {str(e)}",
                'flood_events': [],
                'risk_level': 'unknown'
            }
    
    def get_flood_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """
        Get flood forecast data for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast
            
        Returns:
            Flood forecast data
        """
        try:
            endpoint = f"{self.base_url}/flood/forecast/by-lat-lng"
            params = {
                'lat': lat,
                'lng': lon,
                'days': days
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            forecast_data = response.json()
            processed_forecast = self._process_forecast_response(forecast_data)
            
            return processed_forecast
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': f"Forecast API request failed: {str(e)}",
                'forecast': []
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Forecast processing error: {str(e)}",
                'forecast': []
            }
    
    def get_historical_flood_data(self, lat: float, lon: float, 
                                 start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get historical flood data for a location and time period
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            Historical flood data
        """
        try:
            endpoint = f"{self.base_url}/flood/history/by-lat-lng"
            params = {
                'lat': lat,
                'lng': lon,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            historical_data = response.json()
            processed_history = self._process_historical_response(historical_data)
            
            return processed_history
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': f"Historical API request failed: {str(e)}",
                'events': []
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Historical processing error: {str(e)}",
                'events': []
            }
    
    def _process_comprehensive_flood_data(self, disaster_data: Dict, weather_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Process comprehensive flood data from multiple Ambee sources for enhanced accuracy"""
        try:
            # Extract real-time precipitation data
            precipitation = 0
            if 'data' in weather_data and weather_data['data']:
                weather_info = weather_data['data']
                precipitation = weather_info.get('precipitation', 0)
                # Also check for rain field
                if precipitation == 0:
                    precipitation = weather_info.get('rain', 0)
            
            # Process disaster events
            active_floods = []
            flood_alerts = []
            total_affected_area = 0
            max_severity = 0
            
            if 'data' in disaster_data and disaster_data['data']:
                for event in disaster_data['data']:
                    event_type = event.get('eventType', '').upper()
                    if event_type in ['FL', 'FLOOD', 'FLOODING']:
                        active_floods.append(event)
                        severity = event.get('severity', 0)
                        max_severity = max(max_severity, severity)
                        
                        # Calculate affected area
                        area = event.get('affectedArea', 0)
                        if area > 0:
                            total_affected_area += area
            
            # Enhanced risk calculation based on real conditions
            risk_level = self._calculate_enhanced_risk_level(precipitation, active_floods, max_severity)
            confidence_score = self._calculate_confidence_score(precipitation, len(active_floods), weather_data, disaster_data)
            
            return {
                'status': 'success',
                'location': {'lat': lat, 'lon': lon},
                'flood_risk_level': risk_level,
                'precipitation_24h': precipitation,
                'active_flood_events': len(active_floods),
                'affected_area_km2': total_affected_area,
                'confidence_score': confidence_score,
                'severity_score': max_severity,
                'risk_assessment': self._get_enhanced_risk_assessment(risk_level, precipitation, active_floods),
                'data_sources': ['ambee_disasters', 'ambee_weather'],
                'timestamp': datetime.now().isoformat(),
                'raw_events': active_floods[:3]  # Include sample events for transparency
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Data processing failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_enhanced_risk_level(self, precipitation: float, active_floods: List, max_severity: float) -> str:
        """Calculate enhanced risk level based on multiple factors"""
        # High precipitation threshold (like Bengaluru's 300mm+ situation)
        if precipitation > 100:
            return 'very_high'
        elif precipitation > 50:
            return 'high'
        elif precipitation > 25:
            return 'moderate'
        
        # Active flood events override low precipitation readings
        if len(active_floods) > 0:
            if max_severity > 7 or len(active_floods) > 3:
                return 'very_high'
            elif max_severity > 5 or len(active_floods) > 1:
                return 'high'
            else:
                return 'moderate'
        
        # Moderate precipitation still indicates risk
        if precipitation > 10:
            return 'moderate'
        elif precipitation > 5:
            return 'low'
        else:
            return 'minimal'
    
    def _calculate_confidence_score(self, precipitation: float, active_events: int, weather_data: Dict, disaster_data: Dict) -> float:
        """Calculate confidence score based on data quality and consistency"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence with multiple data sources
        if weather_data.get('data') and disaster_data.get('data'):
            confidence += 0.2
        
        # Higher confidence with recent data
        if precipitation > 0 or active_events > 0:
            confidence += 0.2
        
        # Higher confidence with consistent indicators
        if precipitation > 50 and active_events > 0:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_enhanced_risk_assessment(self, risk_level: str, precipitation: float, active_floods: List) -> str:
        """Provide detailed risk assessment based on real conditions"""
        if risk_level == 'very_high':
            return f"Critical flood conditions detected. {precipitation:.1f}mm precipitation recorded with {len(active_floods)} active flood events. Immediate safety measures recommended."
        elif risk_level == 'high':
            return f"High flood risk identified. {precipitation:.1f}mm precipitation with {len(active_floods)} flood events detected. Exercise caution and monitor conditions."
        elif risk_level == 'moderate':
            return f"Moderate flood risk. {precipitation:.1f}mm precipitation recorded. Stay alert to changing conditions."
        elif risk_level == 'low':
            return f"Low flood risk. {precipitation:.1f}mm precipitation detected. Normal precautions advised."
        else:
            return "Minimal flood risk based on current conditions."

    def _process_natural_disasters_response(self, raw_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Process Natural Disasters API response for flood events"""
        try:
            events = raw_data.get('result', [])
            flood_events = []
            total_alert_score = 0.0
            max_severity = 0
            
            for event in events:
                event_type = event.get('event_type', '')
                event_name = event.get('event_name', '').lower()
                
                # Look for flood-related events including severe weather that causes flooding
                is_flood_related = (event_type == 'FL' or 
                                  'flood' in event_name or 
                                  'heavy rain' in event_name or 
                                  'extreme rain' in event_name or
                                  ('thunderstorm' in event_name and 'rain' in event_name))
                
                if is_flood_related:
                    severity_map = {'low': 1, 'medium': 2, 'moderate': 2, 'high': 3, 'severe': 4, 'extreme': 5}
                    severity_text = event.get('severity', 'low').lower()
                    severity_score = severity_map.get(severity_text, 1)
                    max_severity = max(max_severity, severity_score)
                    
                    # Calculate alert score based on severity and proximity
                    alert_contribution = min(severity_score * 0.2, 1.0)
                    total_alert_score += alert_contribution
                    
                    flood_events.append({
                        'event_name': event.get('eventName', 'Flood Event'),
                        'severity': severity_text,
                        'severity_score': severity_score,
                        'event_date': event.get('eventDate', ''),
                        'description': event.get('eventDescription', ''),
                        'location': event.get('eventPlace', ''),
                        'coordinates': event.get('latLon', []),
                        'alert_level': event.get('alertLevel', 'none'),
                        'exposed_population': event.get('exposedPopulation', 0)
                    })
            
            # Calculate overall risk metrics
            alert_score = min(total_alert_score, 1.0)
            active_events = len(flood_events)
            
            # Determine risk level
            risk_level = self._calculate_risk_level(alert_score, active_events)
            
            return {
                'status': 'success',
                'flood_events': flood_events,
                'summary': {
                    'active_events': active_events,
                    'max_severity': max_severity,
                    'total_events_analyzed': len(events)
                },
                'alert_score': alert_score,
                'risk_level': risk_level,
                'risk_assessment': self._get_risk_assessment(alert_score, active_events),
                'location': {'lat': lat, 'lon': lon},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to process Natural Disasters response: {str(e)}",
                'flood_events': [],
                'alert_score': 0.0,
                'risk_level': 'unknown'
            }
    
    def _process_flood_response(self, raw_data: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Process raw flood response from Ambee API (legacy method)"""
        processed = {
            'status': 'success',
            'timestamp': datetime.now(),
            'location': {'lat': lat, 'lon': lon},
            'flood_events': [],
            'risk_level': 'low',
            'alert_score': 0,
            'summary': {}
        }
        
        try:
            if 'data' in raw_data and raw_data['data']:
                events = raw_data['data'] if isinstance(raw_data['data'], list) else [raw_data['data']]
                
                max_severity = 0
                total_events = len(events)
                active_events = 0
                
                for event in events:
                    flood_event = {
                        'event_id': event.get('eventId', 'unknown'),
                        'severity': event.get('severity', 'unknown'),
                        'alert_score': event.get('alertScore', 0),
                        'description': event.get('description', 'No description'),
                        'start_time': event.get('startTime'),
                        'end_time': event.get('endTime'),
                        'location_name': event.get('locationName', 'Unknown'),
                        'coordinates': {
                            'lat': event.get('lat', lat),
                            'lon': event.get('lng', lon)
                        },
                        'distance_km': event.get('distance', 0),
                        'is_active': event.get('isActive', False)
                    }
                    
                    processed['flood_events'].append(flood_event)
                    
                    # Track maximum severity
                    alert_score = event.get('alertScore', 0)
                    if alert_score > max_severity:
                        max_severity = alert_score
                    
                    if event.get('isActive', False):
                        active_events += 1
                
                # Determine overall risk level
                processed['alert_score'] = max_severity
                processed['risk_level'] = self._calculate_risk_level(max_severity, active_events)
                
                processed['summary'] = {
                    'total_events': total_events,
                    'active_events': active_events,
                    'max_alert_score': max_severity,
                    'risk_assessment': self._get_risk_assessment(max_severity, active_events)
                }
            
            else:
                processed['summary'] = {
                    'total_events': 0,
                    'active_events': 0,
                    'max_alert_score': 0,
                    'risk_assessment': 'No active flood events detected in the area'
                }
            
            return processed
            
        except Exception as e:
            processed['status'] = 'error'
            processed['error'] = f"Processing error: {str(e)}"
            return processed
    
    def _process_forecast_response(self, raw_data: Dict) -> Dict[str, Any]:
        """Process flood forecast response"""
        processed = {
            'status': 'success',
            'forecast': [],
            'risk_timeline': []
        }
        
        try:
            if 'data' in raw_data and raw_data['data']:
                forecasts = raw_data['data'] if isinstance(raw_data['data'], list) else [raw_data['data']]
                
                for forecast in forecasts:
                    forecast_item = {
                        'date': forecast.get('date'),
                        'risk_score': forecast.get('riskScore', 0),
                        'severity': forecast.get('severity', 'low'),
                        'description': forecast.get('description', ''),
                        'confidence': forecast.get('confidence', 0)
                    }
                    processed['forecast'].append(forecast_item)
                
                # Create risk timeline
                processed['risk_timeline'] = [
                    {
                        'date': item['date'],
                        'risk_level': self._calculate_risk_level(item['risk_score'], 0)
                    }
                    for item in processed['forecast']
                ]
            
            return processed
            
        except Exception as e:
            processed['status'] = 'error'
            processed['error'] = f"Forecast processing error: {str(e)}"
            return processed
    
    def _process_historical_response(self, raw_data: Dict) -> Dict[str, Any]:
        """Process historical flood data response"""
        processed = {
            'status': 'success',
            'events': [],
            'statistics': {}
        }
        
        try:
            if 'data' in raw_data and raw_data['data']:
                events = raw_data['data'] if isinstance(raw_data['data'], list) else [raw_data['data']]
                
                total_events = len(events)
                severity_counts = {'low': 0, 'moderate': 0, 'high': 0, 'severe': 0}
                
                for event in events:
                    historical_event = {
                        'event_id': event.get('eventId'),
                        'date': event.get('date'),
                        'severity': event.get('severity', 'unknown'),
                        'alert_score': event.get('alertScore', 0),
                        'description': event.get('description', ''),
                        'duration_hours': event.get('durationHours', 0),
                        'affected_area_km2': event.get('affectedAreaKm2', 0)
                    }
                    processed['events'].append(historical_event)
                    
                    # Count severity levels
                    severity = event.get('severity', 'unknown').lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                
                processed['statistics'] = {
                    'total_events': total_events,
                    'severity_breakdown': severity_counts,
                    'average_duration': sum(e.get('duration_hours', 0) for e in events) / max(total_events, 1)
                }
            
            return processed
            
        except Exception as e:
            processed['status'] = 'error'
            processed['error'] = f"Historical processing error: {str(e)}"
            return processed
    
    def _calculate_risk_level(self, alert_score: float, active_events: int) -> str:
        """Calculate risk level based on alert score and active events"""
        if alert_score >= 0.8 or active_events >= 3:
            return 'severe'
        elif alert_score >= 0.6 or active_events >= 2:
            return 'high'
        elif alert_score >= 0.3 or active_events >= 1:
            return 'moderate'
        else:
            return 'low'
    
    def _get_risk_assessment(self, alert_score: float, active_events: int) -> str:
        """Get detailed risk assessment text"""
        risk_level = self._calculate_risk_level(alert_score, active_events)
        
        assessments = {
            'severe': f"SEVERE FLOOD RISK: {active_events} active events with alert score {alert_score:.2f}. Immediate action required.",
            'high': f"HIGH FLOOD RISK: {active_events} active events with alert score {alert_score:.2f}. Exercise caution and monitor closely.",
            'moderate': f"MODERATE FLOOD RISK: {active_events} active events with alert score {alert_score:.2f}. Stay informed of conditions.",
            'low': "LOW FLOOD RISK: No significant flood events detected in the immediate area."
        }
        
        return assessments.get(risk_level, "Risk assessment unavailable")
    
    def get_comprehensive_flood_report(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get comprehensive flood report combining current, forecast, and recent historical data"""
        try:
            # Get current flood data
            current_data = self.get_current_flood_data(lat, lon)
            
            # Get forecast data
            forecast_data = self.get_flood_forecast(lat, lon, days=7)
            
            # Get recent historical data (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            historical_data = self.get_historical_flood_data(lat, lon, start_date, end_date)
            
            comprehensive_report = {
                'location': {'lat': lat, 'lon': lon},
                'timestamp': datetime.now(),
                'current_conditions': current_data,
                'forecast': forecast_data,
                'recent_history': historical_data,
                'overall_assessment': self._generate_overall_assessment(
                    current_data, forecast_data, historical_data
                )
            }
            
            return comprehensive_report
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Comprehensive report error: {str(e)}",
                'location': {'lat': lat, 'lon': lon}
            }
    
    def _generate_overall_assessment(self, current: Dict, forecast: Dict, 
                                   historical: Dict) -> Dict[str, Any]:
        """Generate overall flood risk assessment"""
        assessment = {
            'current_risk': current.get('risk_level', 'unknown'),
            'forecast_trend': 'stable',
            'historical_pattern': 'normal',
            'recommendation': '',
            'confidence': 'medium'
        }
        
        try:
            # Analyze current conditions
            current_score = current.get('alert_score', 0)
            active_events = current.get('summary', {}).get('active_events', 0)
            
            # Analyze forecast trend
            forecast_data = forecast.get('forecast', [])
            if forecast_data:
                future_scores = [f.get('risk_score', 0) for f in forecast_data]
                if len(future_scores) >= 2:
                    if future_scores[-1] > future_scores[0]:
                        assessment['forecast_trend'] = 'increasing'
                    elif future_scores[-1] < future_scores[0]:
                        assessment['forecast_trend'] = 'decreasing'
            
            # Analyze historical pattern
            historical_events = historical.get('statistics', {}).get('total_events', 0)
            if historical_events > 5:
                assessment['historical_pattern'] = 'high_activity'
            elif historical_events > 2:
                assessment['historical_pattern'] = 'moderate_activity'
            
            # Generate recommendation
            if current_score >= 0.7 or active_events >= 2:
                assessment['recommendation'] = "High flood risk detected. Avoid flood-prone areas and monitor emergency alerts."
                assessment['confidence'] = 'high'
            elif assessment['forecast_trend'] == 'increasing':
                assessment['recommendation'] = "Flood risk may increase. Stay informed and prepare for potential flooding."
                assessment['confidence'] = 'medium'
            else:
                assessment['recommendation'] = "Current flood risk is manageable. Continue monitoring conditions."
                assessment['confidence'] = 'medium'
            
            return assessment
            
        except Exception as e:
            assessment['error'] = f"Assessment generation error: {str(e)}"
            return assessment