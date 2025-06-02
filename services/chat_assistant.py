"""
Enhanced Chat Assistant for FloodScope AI
Provides natural language interaction for flood-related queries
"""

import streamlit as st
import requests
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

class ChatAssistant:
    """Enhanced chat assistant for flood and weather queries"""
    
    def __init__(self):
        """Initialize the chat assistant"""
        self.api_key = os.getenv("COHERE_API_KEY", "")
        self.base_url = "https://api.cohere.ai/v1"
        
    def initialize_chat_history(self):
        """Initialize chat history in session state"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'chat_context' not in st.session_state:
            st.session_state.chat_context = {}
    
    def add_message(self, message: str, is_user: bool = True):
        """Add a message to chat history"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.chat_messages.append({
            "content": message,
            "is_user": is_user,
            "timestamp": timestamp
        })
    
    def get_ai_response(self, user_message: str) -> str:
        """Get AI response using Cohere API"""
        try:
            if not self.api_key:
                return self._get_intelligent_fallback(user_message)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Create system prompt for flood assistance
            system_prompt = """You are FloodScope AI Assistant, an expert in flood monitoring, weather analysis, and disaster preparedness. 

Your expertise includes:
- Real-time flood risk assessment
- Weather pattern analysis and flood prediction
- Emergency preparedness and safety recommendations
- Satellite imagery interpretation
- Disaster response planning

Always provide accurate, helpful, and actionable information. Focus on safety first."""
            
            # Prepare context from current analysis if available
            context_info = ""
            if hasattr(st.session_state, 'current_location') and st.session_state.current_location:
                location = st.session_state.current_location
                context_info = f"Current analysis location: {location.get('name', 'Unknown')} ({location.get('lat', 0):.4f}, {location.get('lon', 0):.4f})"
            
            if hasattr(st.session_state, 'flood_data') and st.session_state.flood_data:
                context_info += f"\nRecent flood analysis data is available for this location."
            
            payload = {
                "model": "command",
                "message": user_message,
                "chat_history": [
                    {
                        "role": "SYSTEM", 
                        "message": f"{system_prompt}\n\nContext: {context_info}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 400
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', 'I apologize, but I cannot provide a response at this time.')
            else:
                return self._get_intelligent_fallback(user_message)
                
        except Exception as e:
            return self._get_intelligent_fallback(user_message)
    
    def _get_intelligent_fallback(self, user_message: str) -> str:
        """Provide intelligent fallback responses based on query patterns"""
        message_lower = user_message.lower()
        
        # Weather-related queries
        if any(word in message_lower for word in ['weather', 'rain', 'temperature', 'forecast']):
            return """For current weather information, I recommend:

• Check the Weather Data tab in the main interface for real-time conditions
• Run a flood analysis to get location-specific weather data
• Monitor official weather services for the most up-to-date forecasts

Weather data directly impacts flood risk, so always consider current precipitation levels when assessing flood danger."""
        
        # Flood risk queries
        elif any(word in message_lower for word in ['flood', 'risk', 'danger', 'safe']):
            return """Flood risk assessment involves multiple factors:

**Current Risk Factors:**
• Recent rainfall amounts
• River and water level conditions
• Soil saturation levels
• Topographic factors

**Safety Recommendations:**
• Stay informed through official emergency alerts
• Avoid driving through flooded areas
• Keep emergency supplies ready
• Follow evacuation orders immediately if issued

Use the main analysis tool to get detailed flood risk assessment for specific locations."""
        
        # Emergency/safety queries
        elif any(word in message_lower for word in ['emergency', 'evacuation', 'help', 'what to do']):
            return """**Emergency Flood Response:**

**Immediate Actions:**
• Move to higher ground immediately
• Avoid walking or driving through flood water
• Call emergency services if in immediate danger
• Listen to emergency radio broadcasts

**Emergency Kit Essentials:**
• Water (1 gallon per person per day)
• Non-perishable food
• Battery-powered radio
• Flashlight and extra batteries
• First aid kit
• Important documents in waterproof container

**Important:** Always prioritize personal safety and follow official emergency guidance."""
        
        # Travel/location queries
        elif any(word in message_lower for word in ['travel', 'trip', 'visit', 'go to']):
            return """**Travel Safety During Flood Conditions:**

Before traveling:
• Check flood warnings for your route and destination
• Monitor weather forecasts
• Plan alternative routes
• Inform others of your travel plans

During travel:
• Turn around if you encounter flooded roads
• Stay on main roads when possible
• Keep emergency supplies in your vehicle
• Monitor emergency broadcasts

Use the location analysis feature to check conditions at your destination before traveling."""
        
        # General queries
        else:
            return """I'm here to help with flood monitoring and safety questions. I can assist with:

• Flood risk assessment and interpretation
• Weather-related flood predictions
• Emergency preparedness planning
• Safety recommendations during flood events
• Understanding satellite flood detection data

Feel free to ask specific questions about flood conditions, safety measures, or how to interpret the analysis results."""
    
    def update_context(self, location_data: Optional[Dict[str, Any]] = None, analysis_data: Optional[Dict[str, Any]] = None):
        """Update chat context with current analysis data"""
        if 'chat_context' not in st.session_state:
            st.session_state.chat_context = {}
        
        if location_data is not None:
            st.session_state.chat_context['location'] = location_data
        
        if analysis_data is not None:
            st.session_state.chat_context['analysis'] = analysis_data
            st.session_state.chat_context['last_update'] = datetime.now()
    
    def display_chat_interface(self):
        """Display the enhanced chat interface"""
        self.initialize_chat_history()
        
        # Chat header
        st.markdown("### 💬 FloodScope AI Assistant")
        st.markdown("Ask me anything about flood conditions, weather, or safety measures.")
        
        # Quick action buttons
        st.markdown("**Quick Questions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🌧️ Current Weather", key="weather_btn"):
                self._handle_quick_query("What are the current weather conditions and flood risk?")
        
        with col2:
            if st.button("🌊 Flood Status", key="flood_btn"):
                self._handle_quick_query("What is the current flood risk level?")
        
        with col3:
            if st.button("⚠️ Safety Tips", key="safety_btn"):
                self._handle_quick_query("What safety measures should I take for flood conditions?")
        
        with col4:
            if st.button("🚗 Travel Safety", key="travel_btn"):
                self._handle_quick_query("Is it safe to travel in current conditions?")
        
        # Chat messages display
        if st.session_state.chat_messages:
            st.markdown("---")
            
            # Create container for chat messages
            chat_container = st.container()
            
            with chat_container:
                for msg in st.session_state.chat_messages[-10:]:  # Show last 10 messages
                    with st.chat_message("user" if msg["is_user"] else "assistant"):
                        st.write(msg["content"])
                        st.caption(f"🕐 {msg['timestamp']}")
        
        # Chat input
        user_input = st.chat_input("Ask about flood conditions, weather, or safety...")
        
        if user_input:
            # Add user message
            self.add_message(user_input, True)
            
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
                st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")
            
            # Get and display AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = self.get_ai_response(user_input)
                    st.write(response)
                    st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")
            
            # Add AI response to history
            self.add_message(response, False)
            
            # Refresh to show new messages
            st.rerun()
        
        # Clear chat option
        if st.session_state.chat_messages:
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🗑️ Clear Chat"):
                    st.session_state.chat_messages = []
                    st.rerun()
    
    def _handle_quick_query(self, query: str):
        """Handle quick action button queries"""
        # Add user message
        self.add_message(query, True)
        
        # Get AI response
        response = self.get_ai_response(query)
        
        # Add AI response
        self.add_message(response, False)
        
        # Refresh interface
        st.rerun()
    
    def generate_conversation_report(self) -> str:
        """Generate a downloadable report of the chat conversation"""
        if not hasattr(st.session_state, 'chat_messages') or not st.session_state.chat_messages:
            return "No conversation history available."
        
        report = f"""# FloodScope AI - Chat Conversation Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Conversation Summary
Total Messages: {len(st.session_state.chat_messages)}
Date: {datetime.now().strftime('%B %d, %Y')}

---

## Full Conversation

"""
        
        for i, msg in enumerate(st.session_state.chat_messages, 1):
            sender = "User" if msg["is_user"] else "FloodScope AI"
            report += f"**{i}. {sender} ({msg['timestamp']}):**\n"
            report += f"{msg['content']}\n\n"
        
        report += """---

## About FloodScope AI
FloodScope AI provides real-time flood monitoring and risk assessment using satellite imagery and weather data. This conversation report contains AI-generated responses for informational purposes only. Always follow official emergency guidance and local authorities for actual emergency situations.

For emergency situations, contact local emergency services immediately.
"""
        
        return report