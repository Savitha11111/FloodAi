"""
Email Alert Components for FloodScope AI
User interface for email subscriptions and report delivery
"""

import streamlit as st
from datetime import datetime
from services.simple_email_service import SimpleEmailService
from services.report_generator import ReportGenerator
import re

def display_email_alert_interface():
    """Display email alert subscription and report sending interface"""
    
    st.markdown("### 📧 Email Alerts & Reports")
    
    # Initialize services
    email_service = SimpleEmailService()
    
    # Create tabs for different email functions
    tab1, tab2 = st.tabs(["Send Report", "Subscribe to Alerts"])
    
    with tab1:
        display_send_report_interface(email_service)
    
    with tab2:
        display_subscription_interface(email_service)

def display_send_report_interface(email_service):
    """Interface for sending flood analysis reports via email"""
    
    st.markdown("#### Send Current Analysis Report")
    
    # Check if analysis is available
    if not st.session_state.get('analysis_complete', False):
        st.info("Run a flood analysis first to generate and send reports.")
        return
    
    # Email input
    recipient_email = st.text_input(
        "Recipient Email Address",
        placeholder="user@example.com",
        help="Enter the email address to send the flood analysis report"
    )
    
    # Validate email
    if recipient_email and not is_valid_email(recipient_email):
        st.error("Please enter a valid email address")
        return
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        include_detailed_analysis = st.checkbox("Include detailed analysis", value=True)
        include_weather_data = st.checkbox("Include weather data", value=True)
    
    with col2:
        urgent_priority = st.checkbox("Mark as urgent (high priority)", value=False)
    
    # Send button
    if st.button("Send Report via Email", type="primary"):
        if not recipient_email:
            st.error("Please enter a recipient email address")
            return
        
        with st.spinner("Generating and sending report..."):
            success = send_flood_report(
                email_service, 
                recipient_email, 
                include_detailed_analysis,
                include_weather_data,
                urgent_priority
            )
            
            if success:
                st.success(f"Report successfully sent to {recipient_email}")
                
                # Log the sent email
                if 'sent_emails' not in st.session_state:
                    st.session_state.sent_emails = []
                
                st.session_state.sent_emails.append({
                    'email': recipient_email,
                    'location': st.session_state.current_location.get('name', 'Unknown'),
                    'timestamp': datetime.now(),
                    'type': 'flood_report'
                })
            else:
                st.error("Failed to send report. Please check your email configuration.")

def display_subscription_interface(email_service):
    """Interface for subscribing to flood alerts"""
    
    st.markdown("#### Subscribe to Flood Alerts")
    
    # Check if location is selected
    if not st.session_state.get('current_location'):
        st.info("Select a location first to subscribe to alerts for that area.")
        return
    
    location = st.session_state.current_location
    location_name = location.get('name', 'Unknown Location')
    
    st.markdown(f"**Current Location:** {location_name}")
    
    # Email input
    subscriber_email = st.text_input(
        "Your Email Address",
        placeholder="your-email@example.com",
        help="Enter your email to receive flood alerts for this location"
    )
    
    # Alert preferences
    st.markdown("**Alert Preferences:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        alert_on_high_risk = st.checkbox("High risk alerts", value=True)
        alert_on_moderate_risk = st.checkbox("Moderate risk alerts", value=True)
    
    with col2:
        daily_summary = st.checkbox("Daily summary reports", value=False)
        weather_warnings = st.checkbox("Weather warnings", value=True)
    
    # Risk level threshold
    risk_threshold = st.selectbox(
        "Minimum risk level for alerts",
        ["Low", "Moderate", "High"],
        index=1,
        help="You'll receive alerts when risk level reaches or exceeds this threshold"
    )
    
    # Subscribe button
    if st.button("Subscribe to Alerts", type="primary"):
        if not subscriber_email:
            st.error("Please enter your email address")
            return
        
        if not is_valid_email(subscriber_email):
            st.error("Please enter a valid email address")
            return
        
        # Prepare subscription data
        alert_preferences = {
            'high_risk_alerts': alert_on_high_risk,
            'moderate_risk_alerts': alert_on_moderate_risk,
            'daily_summary': daily_summary,
            'weather_warnings': weather_warnings,
            'risk_threshold': risk_threshold.lower()
        }
        
        with st.spinner("Setting up your subscription..."):
            success = email_service.subscribe_to_alerts(
                subscriber_email, 
                location, 
                alert_preferences
            )
            
            if success:
                st.success(f"Successfully subscribed {subscriber_email} to alerts for {location_name}")
                st.info("You'll receive a confirmation email shortly.")
            else:
                st.error("Failed to set up subscription. Please try again.")

def send_flood_report(email_service, recipient_email, include_detailed, 
                     include_weather, urgent):
    """Send flood analysis report via email"""
    
    try:
        # Get current analysis data
        location_data = st.session_state.current_location
        analysis_data = st.session_state.flood_data
        
        # Generate report content
        report_generator = ReportGenerator()
        
        # Prepare data based on options
        weather_data = analysis_data.get('weather_data') if include_weather else None
        
        # Generate comprehensive report
        report_content = report_generator.generate_flood_analysis_report(
            location_data=location_data,
            analysis_results=analysis_data,
            weather_data=weather_data,
            satellite_data={}  # Would include satellite data if available
        )
        
        # Send email
        if urgent:
            # Send as alert
            alert_data = {
                'risk_level': analysis_data.get('risk_level', 'unknown'),
                'confidence': analysis_data.get('confidence', 0),
                'timestamp': datetime.now()
            }
            success = email_service.send_alert_notification(
                recipient_email, location_data, alert_data
            )
        else:
            # Send as regular report
            success = email_service.send_flood_report_email(
                recipient_email, location_data, analysis_data, report_content
            )
        
        return success
        
    except Exception as e:
        st.error(f"Error sending report: {str(e)}")
        return False

def is_valid_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None