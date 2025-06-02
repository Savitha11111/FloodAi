"""
Email Alert Service for FloodScope AI
Firebase and SendGrid integration for sending flood analysis reports via email
"""

import firebase_admin
from firebase_admin import credentials, firestore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import streamlit as st
import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

class EmailAlertService:
    """Service for sending email alerts and reports"""
    
    def __init__(self):
        """Initialize the email alert service"""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        self.firebase_config = os.getenv("FIREBASE_CONFIG", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@floodscope.ai")
        
        # Initialize Firebase
        self._initialize_firebase()
        
        # Initialize SendGrid
        if self.sendgrid_api_key:
            self.sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
        else:
            self.sg = None
    
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
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")
            self.db = None
    
    def subscribe_to_alerts(self, email: str, location: Dict[str, Any], 
                           alert_preferences: Dict[str, Any]) -> bool:
        """
        Subscribe user to flood alerts for a specific location
        
        Args:
            email: User's email address
            location: Location data (name, lat, lon)
            alert_preferences: User preferences for alerts
            
        Returns:
            Success status
        """
        try:
            if not self.db:
                return False
            
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
            self._send_subscription_confirmation(email, location)
            
            return True
            
        except Exception as e:
            print(f"Subscription error: {str(e)}")
            return False
    
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
            if not self.sg:
                return False
            
            location_name = location_data.get('name', 'Unknown Location')
            risk_level = analysis_data.get('risk_level', 'unknown')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
            
            # Create email subject
            subject = f"FloodScope AI Report - {location_name} ({risk_level.title()} Risk)"
            
            # Create HTML email content
            html_content = self._create_email_html(
                location_data, analysis_data, report_content, timestamp
            )
            
            # Create plain text version
            plain_content = self._create_email_text(
                location_data, analysis_data, timestamp
            )
            
            # Create email message
            message = Mail(
                from_email=self.sender_email,
                to_emails=recipient_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            # Add report as attachment
            attachment = self._create_report_attachment(report_content, location_name)
            if attachment:
                message.attachment = attachment
            
            # Send email
            response = self.sg.send(message)
            
            # Log the email sending
            if self.db:
                self._log_email_sent(recipient_email, location_data, risk_level)
            
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            return False
    
    def send_alert_notification(self, recipient_email: str, location_data: Dict[str, Any],
                               alert_data: Dict[str, Any]) -> bool:
        """
        Send immediate flood alert notification
        
        Args:
            recipient_email: Recipient's email address
            location_data: Location information
            alert_data: Alert details
            
        Returns:
            Success status
        """
        try:
            if not self.sg:
                return False
            
            location_name = location_data.get('name', 'Unknown Location')
            risk_level = alert_data.get('risk_level', 'unknown')
            
            # Create urgent alert email
            subject = f"🚨 FLOOD ALERT - {location_name} ({risk_level.title()} Risk)"
            
            html_content = self._create_alert_html(location_data, alert_data)
            plain_content = self._create_alert_text(location_data, alert_data)
            
            message = Mail(
                from_email=self.sender_email,
                to_emails=recipient_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            # Send with high priority
            message.header = {
                "X-Priority": "1",
                "X-MSMail-Priority": "High"
            }
            
            response = self.sg.send(message)
            return response.status_code in [200, 202]
            
        except Exception as e:
            print(f"Alert email error: {str(e)}")
            return False
    
    def _create_email_html(self, location_data: Dict, analysis_data: Dict, 
                          report_content: str, timestamp: str) -> str:
        """Create HTML email content"""
        
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
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>FloodScope AI Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 1.8rem; }}
                .header p {{ margin: 0.5rem 0 0 0; opacity: 0.9; }}
                .content {{ padding: 2rem; }}
                .status-badge {{ display: inline-block; padding: 0.5rem 1rem; border-radius: 8px; color: white; font-weight: 600; background-color: {risk_color}; }}
                .metrics {{ display: flex; justify-content: space-between; margin: 1.5rem 0; }}
                .metric {{ text-align: center; flex: 1; }}
                .metric-value {{ font-size: 1.5rem; font-weight: 700; color: #1e293b; }}
                .metric-label {{ font-size: 0.9rem; color: #64748b; margin-top: 0.25rem; }}
                .section {{ margin: 1.5rem 0; padding: 1rem; background: #f8fafc; border-radius: 8px; }}
                .footer {{ background: #f1f5f9; padding: 1rem 2rem; text-align: center; font-size: 0.9rem; color: #64748b; }}
                .alert-box {{ background: #fef2f2; border: 1px solid #ef4444; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
                .warning-box {{ background: #fffbeb; border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
                .success-box {{ background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
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
                            <div class="metric-value">{risk_level.title()}</div>
                            <div class="metric-label">Risk Level</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">Real-time</div>
                            <div class="metric-label">Data Source</div>
                        </div>
                    </div>
        """
        
        # Add risk-specific message
        if risk_level == 'high':
            html_content += """
                    <div class="alert-box">
                        <strong>⚠️ HIGH RISK ALERT:</strong> Significant flood conditions detected. Take immediate precautions and monitor official emergency channels.
                    </div>
            """
        elif risk_level == 'moderate':
            html_content += """
                    <div class="warning-box">
                        <strong>🟡 MODERATE RISK:</strong> Elevated flood conditions. Stay alert and avoid low-lying areas.
                    </div>
            """
        else:
            html_content += """
                    <div class="success-box">
                        <strong>✅ LOW RISK:</strong> Current conditions show minimal flood threat. Continue normal activities with standard precautions.
                    </div>
            """
        
        # Add weather data if available
        weather_data = analysis_data.get('weather_data', {})
        if weather_data:
            html_content += f"""
                    <div class="section">
                        <h3>Current Weather Conditions</h3>
                        <p><strong>Temperature:</strong> {weather_data.get('temperature', 'N/A')}°C</p>
                        <p><strong>24h Rainfall:</strong> {weather_data.get('rain_24h', 0):.1f}mm</p>
                        <p><strong>Humidity:</strong> {weather_data.get('humidity', 'N/A')}%</p>
                    </div>
            """
        
        html_content += """
                    <div class="section">
                        <h3>Next Steps</h3>
                        <ul>
                            <li>Monitor local weather and emergency alerts</li>
                            <li>Review the attached detailed report</li>
                            <li>Share this information with relevant stakeholders</li>
                            <li>Re-analyze if conditions change</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This report was generated by FloodScope AI - Advanced Flood Detection System</p>
                    <p>For emergency situations, contact local emergency services immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _create_email_text(self, location_data: Dict, analysis_data: Dict, timestamp: str) -> str:
        """Create plain text email content"""
        location_name = location_data.get('name', 'Unknown Location')
        risk_level = analysis_data.get('risk_level', 'unknown')
        confidence = analysis_data.get('confidence', 0) * 100
        
        return f"""
FloodScope AI - Flood Risk Analysis Report

Location: {location_name}
Analysis Time: {timestamp}
Risk Level: {risk_level.title()}
Confidence: {confidence:.0f}%

{risk_level.upper()} RISK DETECTED

Please review the attached detailed report for complete analysis.

For emergency situations, contact local emergency services immediately.

--
FloodScope AI - Advanced Flood Detection System
        """
    
    def _create_alert_html(self, location_data: Dict, alert_data: Dict) -> str:
        """Create HTML content for alert emails"""
        location_name = location_data.get('name', 'Unknown Location')
        risk_level = alert_data.get('risk_level', 'unknown')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #fef2f2; }}
                .alert-container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; border: 2px solid #ef4444; }}
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
    
    def _create_alert_text(self, location_data: Dict, alert_data: Dict) -> str:
        """Create plain text alert content"""
        location_name = location_data.get('name', 'Unknown Location')
        risk_level = alert_data.get('risk_level', 'unknown')
        
        return f"""
🚨 FLOOD ALERT - {location_name}

{risk_level.upper()} FLOOD RISK DETECTED

Immediate attention required.

Recommended Actions:
- Monitor official emergency channels
- Avoid low-lying areas
- Be prepared for possible evacuation
- Keep emergency supplies ready

For emergency situations, contact local emergency services immediately.
        """
    
    def _create_report_attachment(self, report_content: str, location_name: str) -> Optional[Attachment]:
        """Create email attachment from report content"""
        try:
            # Encode report content
            encoded_content = base64.b64encode(report_content.encode('utf-8')).decode()
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"floodscope_report_{location_name.replace(' ', '_')}_{timestamp}.md"
            
            attachment = Attachment(
                FileContent(encoded_content),
                FileName(filename),
                FileType('text/markdown'),
                Disposition('attachment')
            )
            
            return attachment
            
        except Exception as e:
            print(f"Attachment creation error: {str(e)}")
            return None
    
    def _send_subscription_confirmation(self, email: str, location: Dict) -> bool:
        """Send subscription confirmation email"""
        try:
            location_name = location.get('name', 'Unknown Location')
            
            subject = f"FloodScope AI - Alert Subscription Confirmed for {location_name}"
            
            html_content = f"""
            <h2>Subscription Confirmed</h2>
            <p>You have successfully subscribed to flood alerts for <strong>{location_name}</strong>.</p>
            <p>You will receive notifications when flood risk conditions change for this location.</p>
            <p>Thank you for using FloodScope AI.</p>
            """
            
            message = Mail(
                from_email=self.sender_email,
                to_emails=email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sg.send(message)
            return response.status_code in [200, 202]
            
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
    
    def get_subscription_status(self, email: str) -> List[Dict]:
        """Get user's subscription status"""
        try:
            if not self.db:
                return []
            
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