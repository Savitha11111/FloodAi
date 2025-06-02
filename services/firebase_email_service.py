"""
Firebase-only Email Service for FloodScope AI
Uses Firebase Functions and Gmail API for sending emails
"""

import firebase_admin
from firebase_admin import credentials, firestore, functions
import streamlit as st
import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class FirebaseEmailService:
    """Firebase-only service for sending emails and managing subscriptions"""
    
    def __init__(self):
        """Initialize the Firebase email service"""
        self.firebase_config = os.getenv("FIREBASE_CONFIG", "")
        self.gmail_user = os.getenv("GMAIL_USER", "")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        
        # Initialize Firebase
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if self.firebase_config and not firebase_admin._apps:
                # Parse Firebase config from environment variable
                config_dict = json.loads(self.firebase_config)
                cred = credentials.Certificate(config_dict)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
            elif firebase_admin._apps:
                self.db = firestore.client()
            else:
                self.db = None
                # Create a simple fallback without Firebase
                print("Firebase not configured, using basic email functionality")
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")
            self.db = None
    
    def send_flood_report_email(self, recipient_email: str, location_data: Dict[str, Any],
                               analysis_data: Dict[str, Any], report_content: str) -> bool:
        """
        Send flood analysis report via email using Gmail SMTP
        
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
                return False
            
            location_name = location_data.get('name', 'Unknown Location')
            risk_level = analysis_data.get('risk_level', 'unknown')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
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
            
            # Log the email if Firebase is available
            if self.db:
                self._log_email_sent(recipient_email, location_data, risk_level)
            
            return True
            
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            return False
    
    def subscribe_to_alerts(self, email: str, location: Dict[str, Any], 
                           alert_preferences: Dict[str, Any]) -> bool:
        """
        Subscribe user to flood alerts for a specific location
        """
        try:
            if not self.db:
                # Store in session state as fallback
                if 'email_subscriptions' not in st.session_state:
                    st.session_state.email_subscriptions = []
                
                subscription = {
                    'email': email,
                    'location': location,
                    'preferences': alert_preferences,
                    'subscribed_at': datetime.now().isoformat(),
                    'active': True
                }
                
                st.session_state.email_subscriptions.append(subscription)
                return True
            
            subscription_data = {
                'email': email,
                'location': location,
                'preferences': alert_preferences,
                'subscribed_at': datetime.now(),
                'active': True,
                'last_alert_sent': None
            }
            
            # Store subscription in Firestore
            doc_ref = self.db.collection('alert_subscriptions').document()
            doc_ref.set(subscription_data)
            
            # Send confirmation email
            self._send_confirmation_email(email, location)
            
            return True
            
        except Exception as e:
            print(f"Subscription error: {str(e)}")
            return False
    
    def get_subscription_status(self, email: str) -> List[Dict]:
        """Get user's subscription status"""
        try:
            if not self.db:
                # Return from session state
                subscriptions = st.session_state.get('email_subscriptions', [])
                return [sub for sub in subscriptions if sub['email'] == email and sub['active']]
            
            subscriptions = []
            docs = self.db.collection('alert_subscriptions').where('email', '==', email).where('active', '==', True).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                subscriptions.append(data)
            
            return subscriptions
            
        except Exception as e:
            print(f"Subscription status error: {str(e)}")
            return []
    
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
            print(f"Alert email error: {str(e)}")
            return False
    
    def _create_email_body(self, location_data: Dict, analysis_data: Dict, timestamp: str) -> str:
        """Create HTML email body"""
        
        location_name = location_data.get('name', 'Unknown Location')
        coordinates = f"({location_data.get('lat', 0):.4f}, {location_data.get('lon', 0):.4f})"
        risk_level = analysis_data.get('risk_level', 'unknown')
        confidence = analysis_data.get('confidence', 0) * 100
        
        # Risk level styling
        risk_color = {
            'high': '#ef4444',
            'moderate': '#f59e0b', 
            'low': '#10b981'
        }.get(risk_level, '#6b7280')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }}
                .content {{ padding: 2rem; }}
                .status-badge {{ display: inline-block; padding: 0.5rem 1rem; border-radius: 8px; color: white; font-weight: 600; background-color: {risk_color}; }}
                .footer {{ background: #f1f5f9; padding: 1rem; text-align: center; font-size: 0.9rem; color: #64748b; }}
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
                    <p><strong>Confidence:</strong> {confidence:.0f}%</p>
                    
                    <h3>Key Findings</h3>
                    <p>This automated analysis uses real-time data sources including weather conditions, satellite imagery, and news verification to assess flood risk.</p>
                    
                    <h3>Recommendations</h3>
                    <ul>
                        <li>Monitor local weather and emergency alerts</li>
                        <li>Review the attached detailed report</li>
                        <li>Follow official emergency guidance if conditions worsen</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Generated by FloodScope AI - Advanced Flood Detection System</p>
                    <p>For emergencies, contact local emergency services immediately.</p>
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
                        <li>Monitor official emergency channels</li>
                        <li>Avoid low-lying areas</li>
                        <li>Be prepared for possible evacuation</li>
                        <li>Keep emergency supplies ready</li>
                    </ul>
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
            <body>
                <h2>Subscription Confirmed</h2>
                <p>You have successfully subscribed to flood alerts for <strong>{location_name}</strong>.</p>
                <p>You will receive notifications when flood risk conditions change for this location.</p>
                <p>Thank you for using FloodScope AI.</p>
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
    
    def _log_email_sent(self, recipient: str, location_data: Dict, risk_level: str):
        """Log email sending to Firebase"""
        try:
            if self.db:
                log_data = {
                    'recipient': recipient,
                    'location': location_data,
                    'risk_level': risk_level,
                    'sent_at': datetime.now(),
                    'type': 'flood_report'
                }
                
                self.db.collection('email_logs').add(log_data)
                
        except Exception as e:
            print(f"Email logging error: {str(e)}")
    
    def check_service_status(self) -> Dict[str, bool]:
        """Check the status of email services"""
        return {
            'gmail_configured': bool(self.gmail_user and self.gmail_password),
            'firebase_connected': self.db is not None,
            'service_ready': bool(self.gmail_user and self.gmail_password)
        }