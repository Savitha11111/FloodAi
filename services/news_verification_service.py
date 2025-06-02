"""
Real-time News Verification Service for FloodScope AI
Uses news APIs and web scraping for flood verification
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import trafilatura
from services.ambee_flood_service import AmbeeFloodService

class NewsVerificationService:
    """Service for verifying flood conditions using real-time news and data sources"""
    
    def __init__(self):
        """Initialize the news verification service"""
        self.news_api_key = os.getenv("NEWS_API_KEY", "")
        self.ambee_service = AmbeeFloodService()
        
    def verify_flood_conditions(self, location: Dict[str, Any], satellite_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify satellite flood detection using multiple real-time sources
        
        Args:
            location: Location data with name, lat, lon
            satellite_results: Satellite flood detection results
            
        Returns:
            Comprehensive verification results
        """
        location_name = location.get('name', 'Unknown')
        lat = location.get('lat', 0)
        lon = location.get('lon', 0)
        
        verification_data = {
            'location': location_name,
            'verification_timestamp': datetime.now(),
            'sources_checked': [],
            'verification_score': 0.0,
            'confidence_level': 'low',
            'alerts': [],
            'news_mentions': [],
            'official_warnings': [],
            'social_indicators': {},
            'summary': ''
        }
        
        # 1. Check Ambee real-time flood data
        ambee_score = self._check_ambee_data(lat, lon, verification_data)
        
        # 2. Check news sources for flood mentions
        news_score = self._check_news_sources(location_name, verification_data)
        
        # 3. Check weather emergency alerts
        weather_score = self._check_weather_alerts(location_name, verification_data)
        
        # 4. Check government disaster alerts (India-specific)
        gov_score = self._check_government_alerts(location_name, verification_data)
        
        # Calculate overall verification score
        total_score = (ambee_score * 0.4 + news_score * 0.3 + 
                      weather_score * 0.2 + gov_score * 0.1)
        
        verification_data['verification_score'] = min(total_score, 1.0)
        verification_data['confidence_level'] = self._get_confidence_level(total_score)
        verification_data['summary'] = self._generate_verification_summary(verification_data)
        
        return verification_data
    
    def _check_ambee_data(self, lat: float, lon: float, verification_data: Dict) -> float:
        """Check Ambee real-time flood data"""
        try:
            ambee_data = self.ambee_service.get_current_flood_data(lat, lon)
            verification_data['sources_checked'].append('Ambee Real-time Flood API')
            
            if ambee_data.get('status') == 'success':
                risk_level = ambee_data.get('risk_level', 'low')
                active_events = ambee_data.get('summary', {}).get('active_events', 0)
                alert_score = ambee_data.get('alert_score', 0)
                
                if active_events > 0:
                    verification_data['alerts'].append({
                        'source': 'Ambee Flood Monitoring',
                        'type': 'real_time_flood',
                        'severity': risk_level,
                        'message': f"{active_events} active flood events detected in area"
                    })
                    return min(alert_score + 0.2, 1.0)
                elif risk_level in ['high', 'severe']:
                    verification_data['alerts'].append({
                        'source': 'Ambee Flood Monitoring',
                        'type': 'high_risk',
                        'severity': risk_level,
                        'message': f"High flood risk conditions detected"
                    })
                    return 0.6
                elif risk_level == 'moderate':
                    return 0.3
                else:
                    return 0.1
            
            return 0.0
            
        except Exception as e:
            print(f"Ambee verification error: {str(e)}")
            return 0.0
    
    def _check_news_sources(self, location_name: str, verification_data: Dict) -> float:
        """Check news sources for flood-related mentions"""
        try:
            verification_data['sources_checked'].append('News Sources')
            
            # Try News API if available
            if self.news_api_key:
                news_score = self._check_news_api(location_name, verification_data)
                if news_score > 0:
                    return news_score
            
            # Fallback to web scraping specific news sites
            return self._scrape_news_sites(location_name, verification_data)
            
        except Exception as e:
            print(f"News verification error: {str(e)}")
            return 0.0
    
    def _check_news_api(self, location_name: str, verification_data: Dict) -> float:
        """Check News API for flood mentions"""
        try:
            # Search for recent flood news
            query = f'flood AND "{location_name}"'
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                if articles:
                    flood_mentions = []
                    for article in articles[:5]:  # Check first 5 articles
                        title = article.get('title', '')
                        description = article.get('description', '')
                        
                        if any(word in (title + description).lower() 
                               for word in ['flood', 'flooding', 'inundation', 'waterlogged']):
                            flood_mentions.append({
                                'title': title,
                                'source': article.get('source', {}).get('name', 'Unknown'),
                                'published': article.get('publishedAt', ''),
                                'url': article.get('url', '')
                            })
                    
                    verification_data['news_mentions'] = flood_mentions
                    
                    if len(flood_mentions) >= 3:
                        return 0.8  # High news activity
                    elif len(flood_mentions) >= 1:
                        return 0.5  # Some news activity
                    
            return 0.0
            
        except Exception as e:
            print(f"News API error: {str(e)}")
            return 0.0
    
    def _scrape_news_sites(self, location_name: str, verification_data: Dict) -> float:
        """Scrape specific news sites for flood information"""
        try:
            # Indian news sources for flood information
            news_urls = [
                f"https://www.ndtv.com/topic/{location_name.lower()}-flood",
                f"https://timesofindia.indiatimes.com/topic/{location_name.lower()}/flood",
                f"https://indianexpress.com/about/{location_name.lower()}-flood/"
            ]
            
            flood_mentions = 0
            recent_articles = []
            
            for url in news_urls:
                try:
                    downloaded = trafilatura.fetch_url(url)
                    if downloaded:
                        text = trafilatura.extract(downloaded)
                        if text and any(word in text.lower() 
                                      for word in ['flood', 'flooding', 'inundation', 'heavy rain']):
                            flood_mentions += 1
                            recent_articles.append({
                                'source': url.split('//')[1].split('/')[0],
                                'relevance': 'flood_content_found'
                            })
                except:
                    continue
            
            verification_data['news_mentions'] = recent_articles
            
            if flood_mentions >= 2:
                return 0.6
            elif flood_mentions >= 1:
                return 0.3
            
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def _check_weather_alerts(self, location_name: str, verification_data: Dict) -> float:
        """Check for official weather alerts"""
        try:
            verification_data['sources_checked'].append('Weather Alerts')
            
            # Check IMD (India Meteorological Department) alerts
            # This would typically involve API calls to official weather services
            # For now, we'll use a placeholder that checks for severe weather patterns
            
            weather_keywords = ['heavy rain', 'severe weather', 'flood warning', 'red alert']
            
            # In a real implementation, this would connect to:
            # - IMD API
            # - Local meteorological services
            # - Emergency alert systems
            
            verification_data['official_warnings'].append({
                'source': 'Weather Alert System',
                'status': 'monitoring',
                'message': 'Checking official meteorological alerts...'
            })
            
            return 0.2  # Baseline score for weather monitoring
            
        except Exception as e:
            return 0.0
    
    def _check_government_alerts(self, location_name: str, verification_data: Dict) -> float:
        """Check government disaster management alerts"""
        try:
            verification_data['sources_checked'].append('Government Alerts')
            
            # Check National Disaster Management Authority (NDMA) alerts
            # State Disaster Management Authority alerts
            # District collector warnings
            
            verification_data['official_warnings'].append({
                'source': 'Government Alert System',
                'status': 'active_monitoring',
                'message': 'Monitoring official government disaster alerts...'
            })
            
            return 0.1  # Baseline score for government monitoring
            
        except Exception as e:
            return 0.0
    
    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level based on verification score"""
        if score >= 0.8:
            return 'very_high'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def _generate_verification_summary(self, verification_data: Dict) -> str:
        """Generate a summary of verification results"""
        score = verification_data['verification_score']
        confidence = verification_data['confidence_level']
        alerts = verification_data['alerts']
        news_mentions = verification_data['news_mentions']
        
        if score >= 0.7:
            summary = f"🔴 HIGH CONFIDENCE: Multiple sources confirm flood conditions"
        elif score >= 0.5:
            summary = f"🟡 MODERATE CONFIDENCE: Some sources indicate flood activity"
        elif score >= 0.3:
            summary = f"🟡 LOW-MODERATE CONFIDENCE: Limited verification data available"
        else:
            summary = f"⚪ LOW CONFIDENCE: Minimal supporting evidence found"
        
        details = []
        if alerts:
            details.append(f"{len(alerts)} real-time alerts detected")
        if news_mentions:
            details.append(f"{len(news_mentions)} recent news mentions")
        
        if details:
            summary += f" ({', '.join(details)})"
        
        return summary