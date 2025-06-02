"""
Simple Email Service for FloodScope AI
Uses Gmail SMTP to send flood analysis reports
"""

import streamlit as st
import os
from datetime import datetime
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re

class SimpleEmailService:
    """Simple email service using Gmail SMTP"""
    
    def __init__(self):
        """Initialize the email service"""
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.firebase_api_key = os.getenv("FIREBASE_API_KEY", "AIzaSyB-TQQduf1kJg1I_ZmETu-BzIe75CyvOXU")
    
    def send_flood_report_email(self, recipient_email: str, location_data: Dict[str, Any],
                               analysis_data: Dict[str, Any], report_content: str) -> bool:
        """
        Send flood analysis report via email
        
        Args:
            recipient_email: Recipient's email address
            location_data: Location information
            analysis_data: Flood analysis results
            report_content: Generated report content
            
        Returns:
            Success status
        """
        try:
            if not self.gmail_user or not self.gmail_password:
                st.error("Email service not configured. Please contact administrator.")
                return False
            
            location_name = location_data.get('name', 'Unknown Location')
            
            # Extract correct risk level from flood results
            flood_results = analysis_data.get('flood_results', {})
            risk_level = flood_results.get('overall_risk', 'Unknown')
            
            # Get accurate IST time
            import pytz
            ist_tz = pytz.timezone('Asia/Kolkata')
            ist_time = datetime.now(ist_tz)
            timestamp = ist_time.strftime('%Y-%m-%d %H:%M:%S IST')
            
            # Create email with noreply format
            msg = MIMEMultipart()
            msg['From'] = f"FloodScope AI <{self.gmail_user}>"
            msg['Reply-To'] = "noreply@floodscope.ai"
            msg['To'] = recipient_email
            msg['Subject'] = f"FloodScope AI Report - {location_name} ({risk_level.title()} Risk)"
            
            # Create email body
            body = self._create_email_body(location_data, analysis_data, timestamp)
            msg.attach(MIMEText(body, 'html'))
            
            # Add report as attachment
            self._add_report_attachment(msg, report_content, location_name)
            
            # Send email using Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, recipient_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_alert_notification(self, recipient_email: str, location_data: Dict[str, Any],
                               alert_data: Dict[str, Any]) -> bool:
        """Send immediate flood alert notification"""
        try:
            if not self.gmail_user or not self.gmail_password:
                return False
            
            location_name = location_data.get('name', 'Unknown Location')
            risk_level = alert_data.get('risk_level', 'unknown')
            
            # Create urgent alert email
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 FLOOD ALERT - {location_name} ({risk_level.title()} Risk)"
            msg['X-Priority'] = '1'
            
            # Create alert body
            body = self._create_alert_body(location_data, alert_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, recipient_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to send alert: {str(e)}")
            return False
    
    def subscribe_to_alerts(self, email: str, location: Dict[str, Any], 
                           alert_preferences: Dict[str, Any]) -> bool:
        """Store subscription in session state (simple version)"""
        try:
            if 'email_subscriptions' not in st.session_state:
                st.session_state.email_subscriptions = []
            
            subscription = {
                'email': email,
                'location': location,
                'preferences': alert_preferences,
                'subscribed_at': datetime.now().isoformat(),
                'active': True
            }
            
            # Check if already subscribed
            existing = [sub for sub in st.session_state.email_subscriptions 
                       if sub['email'] == email and sub['location']['name'] == location['name']]
            
            if existing:
                st.warning("Already subscribed to alerts for this location")
                return False
            
            st.session_state.email_subscriptions.append(subscription)
            
            # Send confirmation email
            self._send_confirmation_email(email, location)
            
            return True
            
        except Exception as e:
            st.error(f"Subscription error: {str(e)}")
            return False
    
    def get_subscription_status(self, email: str) -> List[Dict]:
        """Get user's subscription status from session state"""
        try:
            subscriptions = st.session_state.get('email_subscriptions', [])
            return [sub for sub in subscriptions if sub['email'] == email and sub['active']]
            
        except Exception as e:
            return []
    
    def _create_email_body(self, location_data: Dict, analysis_data: Dict, timestamp: str) -> str:
        """Create HTML email body"""
        
        location_name = location_data.get('name', 'Unknown Location')
        coordinates = f"({location_data.get('lat', 0):.4f}, {location_data.get('lon', 0):.4f})"
        
        # Extract correct risk level and confidence from the actual analysis data structure
        flood_results = analysis_data.get('flood_results', {})
        risk_level = flood_results.get('overall_risk', 'Unknown')
        confidence = flood_results.get('confidence', 0) * 100
        affected_area = flood_results.get('affected_area_km2', 0)
        flood_percentage = flood_results.get('flood_percentage', 0)
        
        # Risk level styling and normalization
        risk_level_lower = risk_level.lower()
        risk_colors = {
            'high': '#ef4444',
            'very_high': '#ef4444',
            'severe': '#ef4444',
            'moderate': '#f59e0b', 
            'low': '#10b981',
            'minimal': '#10b981',
            'very_low': '#10b981'
        }
        risk_color = risk_colors.get(risk_level_lower, '#6b7280')
        
        # Get weather data if available
        weather_data = analysis_data.get('weather_data', {})
        weather_section = ""
        if weather_data:
            weather_section = f"""
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <h3 style="color: #374151;">Current Weather Conditions</h3>
                        <p><strong>Temperature:</strong> {weather_data.get('temperature', 'N/A')}°C</p>
                        <p><strong>24h Rainfall:</strong> {weather_data.get('rain_24h', 0):.1f}mm</p>
                        <p><strong>Humidity:</strong> {weather_data.get('humidity', 'N/A')}%</p>
                    </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }}
                .content {{ padding: 2rem; }}
                .status-badge {{ display: inline-block; padding: 0.5rem 1rem; border-radius: 8px; color: white; font-weight: 600; background-color: {risk_color}; }}
                .footer {{ background: #f1f5f9; padding: 1rem; text-align: center; font-size: 0.9rem; color: #64748b; }}
                .metrics {{ display: flex; justify-content: space-between; margin: 1.5rem 0; }}
                .metric {{ text-align: center; flex: 1; }}
                .metric-value {{ font-size: 1.5rem; font-weight: 700; color: #1e293b; }}
                .metric-label {{ font-size: 0.9rem; color: #64748b; margin-top: 0.25rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌊 FloodScope AI Report</h1>
                    <p>Flood Risk Analysis for {location_name}</p>
                </div>
                
                <div class="content">
                    <h2>Analysis Summary</h2>
                    <p><strong>Location:</strong> {location_name} {coordinates}</p>
                    <p><strong>Analysis Time:</strong> {timestamp}</p>
                    <p><strong>Risk Level:</strong> <span class="status-badge">{risk_level.title()}</span></p>
                    
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">{confidence:.0f}%</div>
                            <div class="metric-label">Confidence</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{affected_area:.1f} km²</div>
                            <div class="metric-label">Affected Area</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{flood_percentage:.1f}%</div>
                            <div class="metric-label">Flood Coverage</div>
                        </div>
                    </div>
                    
                    {weather_section}
                    
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <h3 style="color: #374151;">Key Findings</h3>
                        <p>This analysis combines real-time weather data, satellite verification, and multiple data sources to provide accurate flood risk assessment for {location_name}.</p>
                        
                        <h3 style="color: #374151;">Data Sources Used</h3>
                        <ul>
                            <li>Real-time weather monitoring</li>
                            <li>Multi-source flood data validation</li>
                            <li>News and emergency alert verification</li>
                            <li>Historical pattern analysis</li>
                        </ul>
                        
                        <h3 style="color: #374151;">Recommended Actions</h3>
                        <ul>
                            <li>Monitor local weather and emergency alerts</li>
                            <li>Review the attached detailed report</li>
                            <li>Follow official emergency guidance if conditions worsen</li>
                            <li>Share this information with relevant stakeholders</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>FloodScope AI</strong> - Advanced Flood Detection System</p>
                    <p>For emergency situations, contact local emergency services immediately.</p>
                    <p style="font-size: 0.8rem; margin-top: 1rem;">This report was generated using real-time data sources and should be used alongside official emergency information.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_alert_body(self, location_data: Dict, alert_data: Dict) -> str:
        """Create HTML body for alert emails"""
        location_name = location_data.get('name', 'Unknown Location')
        risk_level = alert_data.get('risk_level', 'unknown')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #fef2f2; }}
                .alert-container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; border: 2px solid #ef4444; }}
                .alert-header {{ background: #ef4444; color: white; padding: 1.5rem; text-align: center; }}
                .alert-content {{ padding: 1.5rem; }}
                .urgent {{ font-size: 1.2rem; font-weight: bold; color: #dc2626; }}
            </style>
        </head>
        <body>
            <div class="alert-container">
                <div class="alert-header">
                    <h1>🚨 FLOOD ALERT</h1>
                    <p>{location_name}</p>
                </div>
                <div class="alert-content">
                    <p class="urgent">{risk_level.upper()} FLOOD RISK DETECTED</p>
                    <p>Immediate attention required for {location_name}.</p>
                    <p><strong>Recommended Actions:</strong></p>
                    <ul>
                        <li>Monitor official emergency channels immediately</li>
                        <li>Avoid low-lying and flood-prone areas</li>
                        <li>Be prepared for possible evacuation</li>
                        <li>Keep emergency supplies and communication devices ready</li>
                        <li>Follow local emergency management guidance</li>
                    </ul>
                    <p><strong>Stay Safe:</strong> If you are in immediate danger, contact emergency services right away.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _add_report_attachment(self, msg, report_content: str, location_name: str):
        """Add report as email attachment"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"floodscope_report_{location_name.replace(' ', '_')}_{timestamp}.md"
            
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(report_content.encode('utf-8'))
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(attachment)
            
        except Exception as e:
            print(f"Attachment error: {str(e)}")
    
    def _send_confirmation_email(self, email: str, location: Dict) -> bool:
        """Send subscription confirmation email"""
        try:
            if not self.gmail_user or not self.gmail_password:
                return False
            
            location_name = location.get('name', 'Unknown Location')
            
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = email
            msg['Subject'] = f"FloodScope AI - Alert Subscription Confirmed for {location_name}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; border-radius: 12px;">
                    <h1>🌊 Subscription Confirmed</h1>
                </div>
                <div style="padding: 2rem; background: white; border-radius: 0 0 12px 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <h2>Welcome to FloodScope AI Alerts!</h2>
                    <p>You have successfully subscribed to flood alerts for <strong>{location_name}</strong>.</p>
                    <p>You will receive notifications when flood risk conditions change for this location.</p>
                    <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <p><strong>What you'll receive:</strong></p>
                        <ul>
                            <li>Real-time flood risk alerts</li>
                            <li>Detailed analysis reports</li>
                            <li>Weather and verification data</li>
                            <li>Safety recommendations</li>
                        </ul>
                    </div>
                    <p>Thank you for using FloodScope AI for flood monitoring and safety.</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Confirmation email error: {str(e)}")
            return False
    
    def check_service_status(self) -> Dict[str, bool]:
        """Check the status of email service"""
        return {
            'gmail_configured': bool(self.gmail_user and self.gmail_password),
            'service_ready': bool(self.gmail_user and self.gmail_password)
        }
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None