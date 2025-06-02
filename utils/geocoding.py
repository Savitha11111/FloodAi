import requests
from typing import Optional, Tuple, Dict, Any
import time

class GeocodingService:
    """Service for converting place names to coordinates"""
    
    def __init__(self):
        """Initialize geocoding service with Nominatim (free, no API key required)"""
        self.base_url = "https://nominatim.openstreetmap.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FloodScope/1.0 (flood detection application)'
        })
        
    def geocode(self, place_name: str) -> Optional[Tuple[float, float]]:
        """
        Convert place name to coordinates
        
        Args:
            place_name: Name of the place to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            # Rate limiting - be respectful to free service
            time.sleep(1)
            
            params = {
                'q': place_name,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(
                f"{self.base_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            
            if results and len(results) > 0:
                result = results[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                return (lat, lon)
            else:
                return None
                
        except Exception as e:
            print(f"Geocoding failed: {str(e)}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Convert coordinates to place name
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Place name string or None if not found
        """
        try:
            # Rate limiting
            time.sleep(1)
            
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = self.session.get(
                f"{self.base_url}/reverse",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'display_name' in result:
                return result['display_name']
            else:
                return None
                
        except Exception as e:
            print(f"Reverse geocoding failed: {str(e)}")
            return None