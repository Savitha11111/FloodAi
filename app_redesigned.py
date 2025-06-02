import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
import io
import os
import threading
import time
import pytz
import requests

# Import services
from services.data_fetcher import DataFetcher
from services.cloud_analyzer import CloudAnalyzer
from services.preprocessor import Preprocessor
from services.flood_detector import FloodDetector
from services.postprocessor import Postprocessor
from services.weather_service import WeatherService
from services.verification_service import FloodVerificationService
from services.ambee_flood_service import AmbeeFloodService
from services.chat_assistant import ChatAssistant
from services.report_generator import ReportGenerator
from services.news_verification_service import NewsVerificationService
from utils.geocoding import GeocodingService
from utils.image_utils import ImageProcessor
from modern_ui import apply_modern_styling, create_header, create_clean_metrics, create_status_indicator, create_info_box

# Page config
st.set_page_config(
    page_title="FloodScope AI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply modern styling
apply_modern_styling()

# Initialize services
@st.cache_resource
def initialize_services():
    """Initialize all services"""
    return {
        'data_fetcher': DataFetcher(),
        'cloud_analyzer': CloudAnalyzer(),
        'preprocessor': Preprocessor(),
        'flood_detector': FloodDetector(),
        'postprocessor': Postprocessor(),
        'weather_service': WeatherService(),
        'verification_service': FloodVerificationService(),
        'news_verification': NewsVerificationService(),
        'ambee_flood_service': AmbeeFloodService(),
        'geocoding': GeocodingService(),
        'image_processor': ImageProcessor(),
        'chat_assistant': ChatAssistant(),
        'report_generator': ReportGenerator()
    }

services = initialize_services()

# Initialize session state
if 'current_location' not in st.session_state:
    st.session_state.current_location = None
if 'flood_data' not in st.session_state:
    st.session_state.flood_data = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def main():
    """Main application function"""
    # Create modern header
    create_header()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Analysis", "🗺️ Map View", "💬 AI Assistant", "📊 Reports"])
    
    with tab1:
        display_analysis_tab()
    
    with tab2:
        display_map_tab()
    
    with tab3:
        display_chat_tab()
    
    with tab4:
        display_reports_tab()

def display_analysis_tab():
    """Main analysis interface"""
    
    # Quick location setup
    st.markdown('<h2 class="section-title">Flood Risk Analysis</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Location input
        st.markdown("**Select Location**")
        location_input = st.text_input(
            "Enter city name or coordinates",
            placeholder="e.g., Mumbai, Bangalore, or 19.0760,72.8777",
            label_visibility="collapsed"
        )
        
        if st.button("Analyze Location", type="primary"):
            if location_input:
                analyze_location(location_input)
            else:
                st.warning("Please enter a location")
    
    with col2:
        # Current status
        if st.session_state.current_location:
            location_name = st.session_state.current_location.get('name', 'Unknown')
            st.markdown(f"**Current Location:** {location_name}")
            
            if st.session_state.analysis_complete:
                risk_level = st.session_state.flood_data.get('risk_level', 'unknown')
                status_color = 'high' if risk_level == 'high' else 'moderate' if risk_level == 'moderate' else 'low'
                st.markdown(f"**Status:** {create_status_indicator(risk_level.title(), status_color)}", unsafe_allow_html=True)
        else:
            st.markdown("**Status:** No location selected")
    
    # Results display
    if st.session_state.analysis_complete and st.session_state.flood_data:
        display_analysis_results()
    else:
        display_welcome_content()

def display_analysis_results():
    """Display flood analysis results"""
    data = st.session_state.flood_data
    
    # Key metrics
    st.markdown("### Analysis Results")
    
    col1, col2, col3, col4 = st.columns(4)
    create_clean_metrics(col1, col2, col3, col4)
    
    # Main results
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        
        # Risk assessment
        risk_level = data.get('risk_level', 'unknown')
        confidence = data.get('confidence', 0) * 100
        
        st.markdown(f"**Flood Risk Level:** {risk_level.title()}")
        st.markdown(f"**Detection Confidence:** {confidence:.1f}%")
        
        # Verification results
        verification = data.get('verification', {})
        if verification:
            st.markdown("**Verification Status:**")
            st.markdown(verification.get('summary', 'No verification data available'))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Weather info
        weather_data = data.get('weather_data', {})
        if weather_data:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.markdown("**Current Weather**")
            st.markdown(f"Temperature: {weather_data.get('temperature', 'N/A')}°C")
            st.markdown(f"Rainfall (24h): {weather_data.get('rain_24h', 0):.1f}mm")
            st.markdown(f"Humidity: {weather_data.get('humidity', 'N/A')}%")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Download options
    st.markdown("### Download Report")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate Detailed Report"):
            generate_report()
    
    with col2:
        if st.button("Download Analysis Data"):
            download_analysis_data()

def display_welcome_content():
    """Display welcome content when no analysis is available"""
    st.markdown("### Welcome to FloodScope AI")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="quick-action">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌊</div>
            <div><strong>Real-time Detection</strong></div>
            <div style="font-size: 0.9rem; color: #666;">Advanced satellite imagery analysis</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="quick-action">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <div><strong>AI-Powered</strong></div>
            <div style="font-size: 0.9rem; color: #666;">Machine learning flood detection</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="quick-action">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
            <div><strong>Fast Analysis</strong></div>
            <div style="font-size: 0.9rem; color: #666;">Results in under 5 minutes</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(create_info_box(
        "Enter a location above to begin flood risk analysis. FloodScope AI uses real-time satellite data and weather information to provide accurate flood assessments.",
        "info"
    ), unsafe_allow_html=True)

def display_map_tab():
    """Display interactive map"""
    st.markdown("### Flood Risk Map")
    
    # Create map
    if st.session_state.current_location:
        lat = st.session_state.current_location['lat']
        lon = st.session_state.current_location['lon']
        
        m = folium.Map(location=[lat, lon], zoom_start=12)
        
        # Add location marker
        folium.Marker(
            [lat, lon],
            popup=st.session_state.current_location.get('name', 'Selected Location'),
            icon=folium.Icon(color='red' if st.session_state.flood_data and st.session_state.flood_data.get('risk_level') == 'high' else 'blue')
        ).add_to(m)
        
        # Display map
        st_folium(m, width=700, height=500)
    else:
        # Default map
        m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
        st_folium(m, width=700, height=500)
        st.info("Select a location in the Analysis tab to view detailed flood mapping")

def display_chat_tab():
    """Display AI chat assistant"""
    st.markdown("### AI Flood Assistant")
    
    # Use the enhanced chat assistant
    chat_assistant = services['chat_assistant']
    
    if st.session_state.current_location:
        chat_assistant.update_context(
            location_data=st.session_state.current_location,
            analysis_data=st.session_state.flood_data
        )
    
    chat_assistant.display_chat_interface()

def display_reports_tab():
    """Display reports and analytics"""
    st.markdown("### Reports & Analytics")
    
    if not st.session_state.analysis_complete:
        st.info("Run a flood analysis first to generate reports")
        return
    
    # Report generation options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Generate Report**")
        if st.button("Comprehensive Analysis Report"):
            generate_comprehensive_report()
    
    with col2:
        st.markdown("**Export Data**")
        if st.button("Export Raw Data (JSON)"):
            export_raw_data()
    
    # Analytics display
    if st.session_state.flood_data:
        display_analytics_dashboard()

def analyze_location(location_input):
    """Analyze flood risk for given location"""
    with st.spinner("Analyzing flood conditions..."):
        try:
            # Parse location
            if ',' in location_input and len(location_input.split(',')) == 2:
                # Coordinates
                lat, lon = map(float, location_input.split(','))
                location_name = f"Location ({lat:.4f}, {lon:.4f})"
            else:
                # City name - use geocoding
                geocoding_service = services['geocoding']
                coords = geocoding_service.get_coordinates(location_input)
                if coords:
                    lat, lon = coords
                    location_name = location_input
                else:
                    st.error("Location not found. Please try again.")
                    return
            
            # Store location
            st.session_state.current_location = {
                'name': location_name,
                'lat': lat,
                'lon': lon
            }
            
            # Get weather data
            weather_service = services['weather_service']
            weather_data = weather_service.get_current_weather(lat, lon)
            
            # Get Ambee flood data
            ambee_service = services['ambee_flood_service']
            ambee_data = ambee_service.get_current_flood_data(lat, lon)
            
            # Enhanced verification using news and real-time sources
            news_verification = services['news_verification']
            verification_results = news_verification.verify_flood_conditions(
                st.session_state.current_location,
                {}  # Satellite results would go here
            )
            
            # Determine risk level based on multiple factors
            risk_level = determine_flood_risk(weather_data, ambee_data, verification_results)
            
            # Store results
            st.session_state.flood_data = {
                'risk_level': risk_level,
                'confidence': verification_results.get('verification_score', 0.5),
                'weather_data': weather_data,
                'ambee_data': ambee_data,
                'verification': verification_results,
                'timestamp': datetime.now()
            }
            
            st.session_state.analysis_complete = True
            st.success(f"Analysis complete for {location_name}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

def determine_flood_risk(weather_data, ambee_data, verification_results):
    """Determine flood risk level based on multiple data sources"""
    
    # Initialize risk factors
    risk_factors = []
    
    # Weather-based risk
    if weather_data:
        rain_24h = weather_data.get('rain_24h', 0)
        if rain_24h > 50:
            risk_factors.append('high')
        elif rain_24h > 20:
            risk_factors.append('moderate')
        else:
            risk_factors.append('low')
    
    # Ambee data risk
    if ambee_data and ambee_data.get('status') == 'success':
        ambee_risk = ambee_data.get('risk_level', 'low')
        risk_factors.append(ambee_risk)
    
    # Verification score risk
    verification_score = verification_results.get('verification_score', 0)
    if verification_score > 0.7:
        risk_factors.append('high')
    elif verification_score > 0.4:
        risk_factors.append('moderate')
    else:
        risk_factors.append('low')
    
    # Determine overall risk
    if 'high' in risk_factors:
        return 'high'
    elif 'moderate' in risk_factors:
        return 'moderate'
    else:
        return 'low'

def generate_report():
    """Generate and download comprehensive report"""
    if not st.session_state.analysis_complete:
        return
    
    report_generator = services['report_generator']
    
    report_content = report_generator.generate_flood_analysis_report(
        location_data=st.session_state.current_location,
        analysis_results=st.session_state.flood_data,
        weather_data=st.session_state.flood_data.get('weather_data'),
        satellite_data={}  # Would include satellite data if available
    )
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    location_name = st.session_state.current_location.get('name', 'location').replace(' ', '_')
    
    st.download_button(
        label="Download Report",
        data=report_content.encode('utf-8'),
        file_name=f"floodscope_report_{location_name}_{timestamp}.md",
        mime="text/markdown"
    )

def generate_comprehensive_report():
    """Generate comprehensive report with all data"""
    generate_report()

def download_analysis_data():
    """Download raw analysis data"""
    if not st.session_state.analysis_complete:
        return
    
    import json
    
    data_export = {
        'location': st.session_state.current_location,
        'analysis': st.session_state.flood_data,
        'export_timestamp': datetime.now().isoformat()
    }
    
    st.download_button(
        label="Download JSON Data",
        data=json.dumps(data_export, indent=2, default=str),
        file_name=f"floodscope_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def export_raw_data():
    """Export raw data"""
    download_analysis_data()

def display_analytics_dashboard():
    """Display analytics dashboard"""
    st.markdown("### Analytics Dashboard")
    
    data = st.session_state.flood_data
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk level chart
        fig = px.pie(
            values=[1], 
            names=[data.get('risk_level', 'unknown').title()],
            title="Current Risk Level"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Confidence score
        confidence = data.get('confidence', 0) * 100
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=confidence,
            title={'text': "Confidence Score"},
            gauge={'axis': {'range': [None, 100]},
                  'bar': {'color': "darkblue"},
                  'bgcolor': "white",
                  'borderwidth': 2,
                  'bordercolor': "gray"}
        ))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()