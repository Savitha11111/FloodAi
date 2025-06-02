import requests
import os
from typing import Dict, Any, List
import json
from datetime import datetime

class LLMAssistant:
    """Natural language assistant for flood detection queries using Cohere API"""
    
    def __init__(self):
        """Initialize the LLM assistant with Cohere API"""
        self.api_key = os.getenv("COHERE_API_KEY", "")
        self.base_url = "https://api.cohere.ai/v1"
        self.model = "command-nightly"
        
        # System prompt for flood detection context
        self.system_prompt = """You are FloodScope AI, an expert assistant for flood detection and disaster management. You help users understand satellite imagery analysis, flood risks, and emergency response planning. 

Key capabilities:
- Explain satellite data and flood detection results
- Provide flood risk assessments and safety recommendations
- Answer questions about weather patterns and their impact on flooding
- Offer guidance on emergency preparedness and response
- Interpret technical flood detection metrics in simple terms

Always provide accurate, helpful information focused on flood safety and detection."""
        
        if not self.api_key:
            print("Warning: Cohere API key not provided. Chat assistant will use fallback responses.")
    
    def get_response(self, user_message: str, flood_context: Dict[str, Any] = None) -> str:
        """
        Get AI response to user query with flood detection context
        
        Args:
            user_message: User's question or message
            flood_context: Current flood detection data for context
            
        Returns:
            AI assistant response
        """
        try:
            if not self.api_key:
                return self._get_fallback_response(user_message, flood_context)
            
            # Check if this is a weather-related query that needs real-time data
            if self._is_weather_query(user_message) and flood_context:
                return self._handle_weather_query(user_message, flood_context)
            
            # Call Cohere API with chat format
            response = self._call_cohere_api(user_message, flood_context)
            
            return response
            
        except Exception as e:
            print(f"LLM Assistant error: {str(e)}")
            return self._get_fallback_response(user_message, flood_context)
    
    def _call_cohere_api(self, user_message: str, flood_context: Dict[str, Any] = None) -> str:
        """Call Cohere API for chat-based response"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Create context-aware chat history
            chat_history = []
            if flood_context:
                # Add context as system message
                context_message = self._prepare_context(flood_context)
                chat_history.append({
                    "role": "SYSTEM",
                    "message": f"{self.system_prompt}\n\nCurrent Analysis Context:\n{context_message}"
                })
            
            # Use chat endpoint instead of generate
            payload = {
                'model': 'command',
                'message': user_message,
                'chat_history': chat_history,
                'temperature': 0.7,
                'max_tokens': 500,
                'connectors': [{"id": "web-search"}] if "weather" in user_message.lower() or "current" in user_message.lower() else []
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['text'].strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Cohere API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {str(e)}")
    
    def _is_weather_query(self, user_message: str) -> bool:
        """Check if user message is asking about weather"""
        weather_keywords = ['weather', 'temperature', 'rain', 'rainfall', 'humidity', 'wind', 'storm', 'precipitation', 'sunny', 'cloudy', 'today', 'now', 'current']
        return any(keyword in user_message.lower() for keyword in weather_keywords)
    
    def _handle_weather_query(self, user_message: str, flood_context: Dict[str, Any]) -> str:
        """Handle weather-specific queries with real-time data"""
        try:
            # Extract location from context
            location = flood_context.get('location', {})
            weather_data = flood_context.get('weather_data', {})
            
            location_name = location.get('name', 'the selected location')
            
            # Check for real-time Ambee flood data first
            ambee_data = flood_context.get('ambee_flood_data', {})
            if ambee_data and ambee_data.get('status') == 'success':
                risk_level = ambee_data.get('risk_level', 'low')
                alert_score = ambee_data.get('alert_score', 0)
                active_events = ambee_data.get('summary', {}).get('active_events', 0)
                
                if risk_level in ['high', 'severe'] or alert_score > 0.6 or active_events > 0:
                    flood_events = ambee_data.get('flood_events', [])
                    
                    response = f"""**🚨 REAL-TIME FLOOD ALERT:**

Based on Ambee's real-time flood monitoring:

🔴 **Current Risk Level**: {risk_level.upper()}
📊 **Alert Score**: {alert_score:.2f}/1.0
⚡ **Active Events**: {active_events} flood events detected

"""
                    if flood_events:
                        response += "**Active Flood Events:**\n"
                        for event in flood_events[:3]:  # Show first 3 events
                            severity = event.get('severity', 'unknown')
                            location_name = event.get('location_name', 'Unknown location')
                            distance = event.get('distance_km', 0)
                            response += f"- {severity.title()} flood at {location_name} ({distance:.1f}km away)\n"
                    
                    response += f"""
**Immediate Actions:**
- Monitor official emergency alerts
- Avoid flood-affected areas
- Keep emergency contacts ready
- Follow local evacuation guidance if issued

**Data Source**: Real-time flood monitoring data shows active flood conditions in your area."""
                    
                    return response
            
            # Special handling for Kerala when no Ambee data available
            if 'kerala' in user_message.lower() or 'kochi' in user_message.lower() or 'thiruvananthapuram' in user_message.lower():
                return f"""**⚠️ KERALA FLOOD MONITORING:**

Real-time flood data system is checking current conditions...

If you're experiencing flooding that isn't reflected in our satellite data, this could be due to:
- Heavy cloud cover limiting satellite visibility
- Rapid flood development between satellite passes
- Urban flooding not easily detected from space

**For immediate emergency information:**
- Check Kerala State Disaster Management Authority alerts
- Monitor IMD weather warnings
- Follow local news for ground-truth conditions

Our system combines satellite imagery with real-time flood alerts to provide the most accurate assessment possible."""

            if not weather_data:
                return f"I don't have current weather data for {location_name}. Please run a flood analysis first to get real-time weather information."
            
            # Get current weather info
            temp = weather_data.get('temperature', 'unknown')
            humidity = weather_data.get('humidity', 'unknown')
            rain_current = weather_data.get('current_rain', 0)
            rain_24h = weather_data.get('rain_24h', 0)
            pressure = weather_data.get('pressure', 'unknown')
            wind_speed = weather_data.get('wind_speed', 'unknown')
            condition = weather_data.get('weather_condition', 'unknown')
            
            # Create contextual response based on what user asked
            if 'bangalore' in user_message.lower() or 'bengaluru' in user_message.lower():
                location_name = 'Bangalore'
            
            if 'today' in user_message.lower() or 'now' in user_message.lower() or 'current' in user_message.lower():
                response = f"""**Current Weather in {location_name}:**

🌡️ **Temperature**: {temp}°C
💧 **Humidity**: {humidity}%
🌧️ **Current Rainfall**: {rain_current} mm/h
☔ **24h Rainfall**: {rain_24h} mm
🌪️ **Wind Speed**: {wind_speed} m/s
🔽 **Pressure**: {pressure} hPa
☁️ **Conditions**: {condition}

**Flood Risk Assessment**: """
                
                # Enhanced flood risk assessment with validation
                if rain_24h > 50:
                    response += f"🔴 SEVERE: Heavy rainfall ({rain_24h} mm) indicates high flood risk. Satellite detection may be limited due to cloud cover."
                elif rain_24h > 20:
                    response += f"⚠️ MODERATE-HIGH: Significant rainfall ({rain_24h} mm) increases flood risk. Monitor local conditions closely."
                elif rain_current > 5:
                    response += f"🌧️ MODERATE: Current heavy rainfall ({rain_current} mm/h) may lead to localized flooding."
                else:
                    response += "✅ LOW: Current weather conditions show low immediate flood risk."
                
                # Add validation note
                response += f"\n\n**Note**: Always cross-reference satellite data with local weather reports. During heavy cloud cover, optical satellite data may be less reliable."
                
                return response
            
            # For other weather queries, provide general response with available data
            return f"""I have current weather data for {location_name}:
            
**Current Conditions**: {condition}
**Temperature**: {temp}°C  
**Rainfall**: {rain_current} mm/h currently, {rain_24h} mm in 24h
**Humidity**: {humidity}%

⚠️ **Important**: When rainfall exceeds 20mm in 24h or during severe weather warnings, prioritize official meteorological alerts over satellite analysis, as cloud cover can limit satellite flood detection accuracy."""
            
        except Exception as e:
            return f"I'm having trouble accessing the current weather data. Error: {str(e)}"
    
    def _prepare_context(self, flood_context: Dict[str, Any]) -> str:
        """Prepare flood detection context for the AI assistant"""
        try:
            context_parts = []
            
            # Location information
            if 'location' in flood_context:
                location = flood_context['location']
                context_parts.append(f"Location: {location.get('name', 'Unknown')} ({location.get('lat', 0):.4f}, {location.get('lon', 0):.4f})")
            
            # Flood detection results
            if 'flood_results' in flood_context:
                results = flood_context['flood_results']
                
                # Overall risk assessment
                overall_risk = results.get('statistics', {}).get('overall_risk', 'Unknown')
                affected_area = results.get('statistics', {}).get('total_flood_area_km2', 0)
                confidence = results.get('mean_confidence', 0)
                
                context_parts.append(f"Flood Risk Level: {overall_risk}")
                context_parts.append(f"Affected Area: {affected_area:.2f} km²")
                context_parts.append(f"Detection Confidence: {confidence:.1%}")
                
                # Sensor information
                sensor_type = results.get('sensor_type', 'Unknown')
                detection_method = results.get('detection_method', 'Unknown')
                context_parts.append(f"Detection Method: {detection_method} using {sensor_type} data")
                
                # Number of flood regions
                num_regions = len(results.get('flood_regions', []))
                context_parts.append(f"Detected Flood Regions: {num_regions}")
            
            # Weather information
            if 'weather_data' in flood_context:
                weather = flood_context['weather_data']
                
                # Current conditions
                temp = weather.get('temperature', 0)
                humidity = weather.get('humidity', 0)
                rain_24h = weather.get('rain_24h', 0)
                verification_score = weather.get('verification_score', 0)
                
                context_parts.append(f"Weather: {temp:.1f}°C, {humidity:.0f}% humidity")
                context_parts.append(f"24h Rainfall: {rain_24h:.1f}mm")
                context_parts.append(f"Weather Verification Score: {verification_score:.1%}")
            
            # Cloud analysis
            if 'cloud_analysis' in flood_context:
                cloud_info = flood_context['cloud_analysis']
                best_sensor = cloud_info.get('best_sensor', 'Unknown')
                cloud_cover = cloud_info.get('cloud_cover_percentage', 0)
                reasoning = cloud_info.get('reasoning', '')
                
                context_parts.append(f"Selected Sensor: {best_sensor}")
                context_parts.append(f"Cloud Cover: {cloud_cover:.1f}%")
                if reasoning:
                    context_parts.append(f"Sensor Selection Reason: {reasoning}")
            
            # Timestamp
            if 'timestamp' in flood_context:
                timestamp = flood_context['timestamp']
                if isinstance(timestamp, datetime):
                    context_parts.append(f"Analysis Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(context_parts) if context_parts else "No specific flood analysis data available."
            
        except Exception as e:
            return f"Context preparation error: {str(e)}"
    
    def _get_fallback_response(self, user_message: str, flood_context: Dict[str, Any] = None) -> str:
        """Provide fallback responses when API is not available"""
        
        # Convert message to lowercase for pattern matching
        message_lower = user_message.lower()
        
        # Flood risk and safety responses
        if any(word in message_lower for word in ['flood', 'risk', 'danger', 'safety']):
            if flood_context and 'flood_results' in flood_context:
                risk_level = flood_context['flood_results'].get('statistics', {}).get('overall_risk', 'unknown')
                affected_area = flood_context['flood_results'].get('statistics', {}).get('total_flood_area_km2', 0)
                
                return f"""Based on the current analysis, the flood risk level is **{risk_level}** with approximately {affected_area:.2f} km² of affected area detected.

**Safety Recommendations:**
- Stay informed through official emergency channels
- Avoid driving through flooded roads
- Keep emergency supplies ready
- If evacuation is advised, leave immediately
- Stay away from storm drains and waterways

The satellite analysis shows real-time conditions, but always follow local emergency management guidance."""
            else:
                return """Flood safety is crucial during any water emergency. Key safety measures include:

• **Stay Informed**: Monitor weather alerts and emergency broadcasts
• **Avoid Flood Waters**: Never drive or walk through flooded areas
• **Emergency Kit**: Keep supplies like water, food, flashlight, and radio ready
• **Evacuation**: Follow official evacuation orders immediately
• **High Ground**: Move to higher ground if flooding threatens your area

Remember: Turn Around, Don't Drown! Just 6 inches of moving water can knock you down."""
        
        # Satellite and technical responses
        elif any(word in message_lower for word in ['satellite', 'sentinel', 'radar', 'optical']):
            return """FloodScope uses advanced satellite imagery from two key sources:

**Sentinel-1 (Radar):**
- Works in all weather conditions, even through clouds
- Uses SAR (Synthetic Aperture Radar) technology
- Excellent for detecting water surfaces and changes
- Updates every 6-12 days

**Sentinel-2 (Optical):**
- Provides high-resolution visual imagery
- Best for clear weather conditions
- Captures detailed surface features
- Updates every 5-10 days

The system automatically selects the best sensor based on cloud cover and data quality, ensuring reliable flood detection regardless of weather conditions."""
        
        # Weather and conditions
        elif any(word in message_lower for word in ['weather', 'rain', 'storm', 'cloud']):
            if flood_context and 'weather_data' in flood_context:
                weather = flood_context['weather_data']
                temp = weather.get('temperature', 0)
                humidity = weather.get('humidity', 0)
                rain_24h = weather.get('rain_24h', 0)
                
                return f"""Current weather conditions show:
- Temperature: {temp:.1f}°C
- Humidity: {humidity:.0f}%
- 24-hour rainfall: {rain_24h:.1f}mm

Weather verification helps confirm satellite flood detection. Heavy rainfall, low atmospheric pressure, and high humidity can all contribute to flooding conditions. The system correlates weather data with satellite imagery for more accurate flood assessment."""
            else:
                return """Weather plays a crucial role in flood detection and verification. Key factors include:

• **Precipitation**: Heavy or prolonged rainfall increases flood risk
• **Atmospheric Pressure**: Low pressure often indicates storm systems
• **Temperature**: Affects snowmelt and evaporation rates
• **Wind**: Strong winds can worsen coastal and storm surge flooding

FloodScope integrates real-time weather data to validate satellite detections and provide comprehensive flood risk assessment."""
        
        # How it works / technology
        elif any(word in message_lower for word in ['how', 'work', 'detect', 'ai', 'algorithm']):
            return """FloodScope uses advanced AI algorithms to detect floods from satellite imagery:

**1. Data Collection**: Automatically fetches latest Sentinel-1 and Sentinel-2 satellite data
**2. Cloud Analysis**: Determines best sensor based on weather conditions
**3. Preprocessing**: Enhances images for optimal AI model performance
**4. AI Detection**: UNet-like neural networks identify water and flood patterns
**5. Post-processing**: Cleans and validates results for accuracy
**6. Verification**: Cross-references with weather data for confirmation

The system processes multiple satellite bands, calculates water indices, and uses machine learning to distinguish between normal water bodies and flood-affected areas. Results are validated against real-time weather conditions."""
        
        # Emergency and response
        elif any(word in message_lower for word in ['emergency', 'evacuate', 'help', 'rescue']):
            return """**EMERGENCY FLOOD RESPONSE:**

**Immediate Actions:**
1. Call emergency services (911/local emergency number) if in immediate danger
2. Move to higher ground immediately
3. Avoid all flood waters - they may be contaminated or deeper than they appear
4. Stay away from downed power lines

**Communication:**
- Text instead of calling to preserve phone networks
- Monitor emergency radio broadcasts
- Follow official social media accounts for updates

**Important**: FloodScope provides detection and monitoring capabilities, but always follow official emergency management directives and evacuation orders from local authorities."""
        
        # Default helpful response
        else:
            return """I'm FloodScope AI, your flood detection assistant! I can help you understand:

🌊 **Flood Detection Results** - Interpret satellite analysis and risk levels
🛰️ **Satellite Technology** - Learn about radar and optical imagery
☁️ **Weather Impact** - Understand how weather affects flooding
⚠️ **Safety Guidance** - Get flood safety and emergency information
🔬 **Technical Details** - Explore how AI detects floods from space

What would you like to know about flood detection or safety? I'm here to help explain the analysis and keep you informed!"""
    
    def get_chat_suggestions(self, flood_context: Dict[str, Any] = None) -> List[str]:
        """Get suggested questions based on current flood analysis context"""
        
        base_suggestions = [
            "How does satellite flood detection work?",
            "What should I do if there's flooding in my area?",
            "How accurate is the flood detection?",
            "What's the difference between radar and optical satellite data?"
        ]
        
        if flood_context and 'flood_results' in flood_context:
            results = flood_context['flood_results']
            
            # Add context-specific suggestions
            context_suggestions = []
            
            # Risk-based suggestions
            risk_level = results.get('statistics', {}).get('overall_risk', 'low')
            if risk_level.lower() in ['high', 'critical']:
                context_suggestions.append("What safety measures should I take for high flood risk?")
                context_suggestions.append("How quickly can flood conditions change?")
            
            # Sensor-based suggestions
            sensor_type = results.get('sensor_type', '')
            if 'SAR' in sensor_type:
                context_suggestions.append("Why was radar data used instead of optical imagery?")
            elif 'optical' in sensor_type:
                context_suggestions.append("How clear are the current satellite images?")
            
            # Weather-based suggestions
            if flood_context.get('weather_data', {}).get('rain_24h', 0) > 20:
                context_suggestions.append("How does recent rainfall affect flood detection?")
            
            # Combine and limit suggestions
            all_suggestions = context_suggestions + base_suggestions
            return all_suggestions[:5]  # Return top 5 suggestions
        
        return base_suggestions
    
    def analyze_flood_trends(self, historical_data: List[Dict[str, Any]]) -> str:
        """Analyze flood trends from historical data"""
        if not historical_data:
            return "No historical flood data available for trend analysis."
        
        try:
            # Simple trend analysis
            risk_levels = [data.get('overall_risk', 'low') for data in historical_data]
            affected_areas = [data.get('affected_area_km2', 0) for data in historical_data]
            
            # Calculate basic trends
            high_risk_count = sum(1 for risk in risk_levels if risk.lower() in ['high', 'critical'])
            avg_affected_area = sum(affected_areas) / len(affected_areas) if affected_areas else 0
            
            trend_summary = f"""**Flood Trend Analysis:**

📊 **Recent Analysis Summary:**
- Total analyses: {len(historical_data)}
- High-risk detections: {high_risk_count}
- Average affected area: {avg_affected_area:.2f} km²

**Observations:**
- Risk trend: {'Increasing' if high_risk_count > len(historical_data) * 0.3 else 'Stable'}
- Monitoring recommendation: {'Enhanced surveillance needed' if high_risk_count > 2 else 'Continue regular monitoring'}

*Note: Trends are based on recent satellite analysis. For comprehensive flood forecasting, consult official meteorological services.*"""
            
            return trend_summary
            
        except Exception as e:
            return f"Trend analysis error: {str(e)}. Please check historical data format."