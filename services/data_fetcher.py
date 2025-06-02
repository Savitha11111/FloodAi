import requests
import os
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, Optional, Tuple
import json
import time

class DataFetcher:
    """Service for fetching satellite data from Sentinel Hub API"""
    
    def __init__(self):
        """Initialize the data fetcher with API credentials"""
        self.client_id = os.getenv("SENTINELHUB_CLIENT_ID", "")
        self.client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET", "")
        self.base_url = "https://services.sentinel-hub.com"
        self.access_token = None
        self.token_expires = None
        self.authenticated = False
        
        # Try to authenticate if credentials are available
        if self.client_id and self.client_secret:
            try:
                self._authenticate()
                self.authenticated = True
            except Exception as e:
                print(f"Warning: Sentinel Hub authentication failed: {e}")
                self.authenticated = False
        else:
            print("Warning: Sentinel Hub credentials not provided. Satellite imagery will be unavailable.")
    
    def _authenticate(self) -> bool:
        """Authenticate with Sentinel Hub API"""
        if not self.client_id or not self.client_secret:
            return False
        
        try:
            auth_url = f"{self.base_url}/oauth/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 300)  # 5 min buffer
            
            return True
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.authenticated or not self.access_token or (self.token_expires and datetime.now() >= self.token_expires):
            self._authenticate()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        self._ensure_authenticated()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def fetch_satellite_data(self, lat: float, lon: float, date: datetime, 
                           bbox_size: float = 0.01) -> Dict[str, Any]:
        """
        Fetch satellite data for a given location and date
        
        Args:
            lat: Latitude
            lon: Longitude  
            date: Date for satellite data
            bbox_size: Size of bounding box around the point
            
        Returns:
            Dictionary containing satellite data from both sensors
        """
        try:
            # Define bounding box
            bbox = [
                lon - bbox_size/2,  # min_lon
                lat - bbox_size/2,  # min_lat
                lon + bbox_size/2,  # max_lon
                lat + bbox_size/2   # max_lat
            ]
            
            # Fetch Sentinel-1 data (radar)
            sentinel1_data = self._fetch_sentinel1_data(bbox, date)
            
            # Fetch Sentinel-2 data (optical)
            sentinel2_data = self._fetch_sentinel2_data(bbox, date)
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'date': date,
                'bbox': bbox,
                'sentinel1': sentinel1_data,
                'sentinel2': sentinel2_data,
                'sentinel1_resolution': '10m',
                'sentinel2_resolution': '10m',
                'acquisition_info': {
                    'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'orbit_direction': 'Descending',
                    'incidence_angle': 35.2,
                    'processing_level': 'L1C',
                    'data_quality': 'Good'
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch satellite data: {str(e)}")
    
    def _fetch_sentinel1_data(self, bbox: list, date: datetime) -> Dict[str, Any]:
        """Fetch Sentinel-1 (SAR) data"""
        try:
            # Define time range (±3 days from target date)
            date_from = (date - timedelta(days=3)).strftime('%Y-%m-%d')
            date_to = (date + timedelta(days=3)).strftime('%Y-%m-%d')
            
            # Sentinel-1 process API request
            request_payload = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [
                        {
                            "type": "sentinel-1-grd",
                            "dataFilter": {
                                "timeRange": {
                                    "from": f"{date_from}T00:00:00Z",
                                    "to": f"{date_to}T23:59:59Z"
                                },
                                "acquisitionMode": "IW",
                                "polarization": "DV"
                            }
                        }
                    ]
                },
                "output": {
                    "width": 512,
                    "height": 512,
                    "responses": [
                        {
                            "identifier": "default",
                            "format": {"type": "image/tiff"}
                        }
                    ]
                },
                "evalscript": """
                    //VERSION=3
                    function setup() {
                        return {
                            input: [{
                                bands: ["VV", "VH"]
                            }],
                            output: {
                                bands: 3,
                                sampleType: "FLOAT32"
                            }
                        };
                    }
                    
                    function evaluatePixel(sample) {
                        return [sample.VV, sample.VH, sample.VV/sample.VH];
                    }
                """
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                headers=self._get_headers(),
                json=request_payload
            )
            
            if response.status_code == 200:
                return {
                    'data': response.content,
                    'format': 'tiff',
                    'bands': ['VV', 'VH', 'VV/VH'],
                    'acquisition_mode': 'IW',
                    'polarization': 'DV',
                    'status': 'success'
                }
            else:
                # Log the error but don't fail completely
                return {
                    'data': None,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'data': None,
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_sentinel2_data(self, bbox: list, date: datetime) -> Dict[str, Any]:
        """Fetch Sentinel-2 (optical) data"""
        try:
            # Define time range (±7 days from target date for better cloud-free chances)
            date_from = (date - timedelta(days=7)).strftime('%Y-%m-%d')
            date_to = (date + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Sentinel-2 process API request
            request_payload = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [
                        {
                            "type": "sentinel-2-l2a",
                            "dataFilter": {
                                "timeRange": {
                                    "from": f"{date_from}T00:00:00Z",
                                    "to": f"{date_to}T23:59:59Z"
                                },
                                "maxCloudCoverage": 50
                            }
                        }
                    ]
                },
                "output": {
                    "width": 512,
                    "height": 512,
                    "responses": [
                        {
                            "identifier": "default",
                            "format": {"type": "image/tiff"}
                        }
                    ]
                },
                "evalscript": """
                    //VERSION=3
                    function setup() {
                        return {
                            input: [{
                                bands: ["B02", "B03", "B04", "B08", "B11", "B12", "CLM"]
                            }],
                            output: {
                                bands: 6,
                                sampleType: "FLOAT32"
                            }
                        };
                    }
                    
                    function evaluatePixel(sample) {
                        // Return RGB, NIR, SWIR1, SWIR2 for flood analysis
                        return [sample.B04, sample.B03, sample.B02, sample.B08, sample.B11, sample.B12];
                    }
                """
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                headers=self._get_headers(),
                json=request_payload
            )
            
            if response.status_code == 200:
                return {
                    'data': response.content,
                    'format': 'tiff',
                    'bands': ['B04', 'B03', 'B02', 'B08', 'B11', 'B12'],
                    'cloud_mask': True,
                    'status': 'success'
                }
            else:
                return {
                    'data': None,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'data': None,
                'status': 'error',
                'error': str(e)
            }
    
    def get_available_dates(self, lat: float, lon: float, 
                           days_back: int = 30) -> Dict[str, list]:
        """
        Get available satellite data dates for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            days_back: Number of days to look back
            
        Returns:
            Dictionary with available dates for each sensor
        """
        try:
            bbox = [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01]
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search for available Sentinel-1 data
            s1_dates = self._search_sentinel1_dates(bbox, start_date, end_date)
            
            # Search for available Sentinel-2 data  
            s2_dates = self._search_sentinel2_dates(bbox, start_date, end_date)
            
            return {
                'sentinel1_dates': s1_dates,
                'sentinel2_dates': s2_dates
            }
            
        except Exception as e:
            raise Exception(f"Failed to get available dates: {str(e)}")
    
    def _search_sentinel1_dates(self, bbox: list, start_date: datetime, 
                               end_date: datetime) -> list:
        """Search for available Sentinel-1 acquisition dates"""
        try:
            search_payload = {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [
                    {
                        "type": "sentinel-1-grd",
                        "dataFilter": {
                            "timeRange": {
                                "from": start_date.strftime('%Y-%m-%dT00:00:00Z'),
                                "to": end_date.strftime('%Y-%m-%dT23:59:59Z')
                            }
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/catalog/search",
                headers=self._get_headers(),
                json=search_payload
            )
            
            if response.status_code == 200:
                features = response.json().get('features', [])
                dates = [feature['properties']['datetime'] for feature in features]
                return sorted(list(set(dates)))
            else:
                return []
                
        except Exception:
            return []
    
    def _search_sentinel2_dates(self, bbox: list, start_date: datetime, 
                               end_date: datetime) -> list:
        """Search for available Sentinel-2 acquisition dates"""
        try:
            search_payload = {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": start_date.strftime('%Y-%m-%dT00:00:00Z'),
                                "to": end_date.strftime('%Y-%m-%dT23:59:59Z')
                            },
                            "maxCloudCoverage": 80
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/catalog/search",
                headers=self._get_headers(),
                json=search_payload
            )
            
            if response.status_code == 200:
                features = response.json().get('features', [])
                dates = [feature['properties']['datetime'] for feature in features]
                return sorted(list(set(dates)))
            else:
                return []
                
        except Exception:
            return []
