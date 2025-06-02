import numpy as np
from typing import Dict, Any, Optional, Tuple
import io
from PIL import Image

class CloudAnalyzer:
    """Service for analyzing cloud cover and selecting optimal sensor data"""
    
    def __init__(self):
        """Initialize the cloud analyzer"""
        self.cloud_threshold = 0.3  # 30% cloud cover threshold
        self.quality_weights = {
            'cloud_cover': 0.4,
            'data_availability': 0.3,
            'temporal_distance': 0.2,
            'spatial_coverage': 0.1
        }
    
    def analyze_cloud_cover(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze cloud cover and determine the best sensor to use
        
        Args:
            satellite_data: Dictionary containing Sentinel-1 and Sentinel-2 data
            
        Returns:
            Dictionary with cloud analysis results and sensor recommendation
        """
        try:
            # Analyze Sentinel-2 cloud cover (optical sensor)
            s2_analysis = self._analyze_sentinel2_clouds(satellite_data.get('sentinel2', {}))
            
            # Analyze Sentinel-1 quality (radar - not affected by clouds)
            s1_analysis = self._analyze_sentinel1_quality(satellite_data.get('sentinel1', {}))
            
            # Calculate overall quality scores
            s1_quality = self._calculate_quality_score('sentinel1', s1_analysis, s2_analysis)
            s2_quality = self._calculate_quality_score('sentinel2', s1_analysis, s2_analysis)
            
            # Determine best sensor
            best_sensor = 'Sentinel-1' if s1_quality >= s2_quality else 'Sentinel-2'
            
            # Generate recommendation reasoning
            reasoning = self._generate_reasoning(s1_analysis, s2_analysis, best_sensor)
            
            return {
                'cloud_cover_percentage': s2_analysis.get('cloud_percentage', 0),
                'sentinel1_quality': s1_quality,
                'sentinel2_quality': s2_quality,
                'best_sensor': best_sensor,
                'cloud_threshold_exceeded': s2_analysis.get('cloud_percentage', 0) > self.cloud_threshold * 100,
                'reasoning': reasoning,
                'analysis_details': {
                    'sentinel1': s1_analysis,
                    'sentinel2': s2_analysis
                },
                'recommendation_confidence': abs(s1_quality - s2_quality)
            }
            
        except Exception as e:
            # Fallback to Sentinel-1 if analysis fails
            return {
                'cloud_cover_percentage': 100,
                'sentinel1_quality': 0.7,
                'sentinel2_quality': 0.0,
                'best_sensor': 'Sentinel-1',
                'cloud_threshold_exceeded': True,
                'reasoning': f"Cloud analysis failed, defaulting to radar sensor: {str(e)}",
                'analysis_details': {},
                'recommendation_confidence': 0.7
            }
    
    def _analyze_sentinel2_clouds(self, sentinel2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cloud cover in Sentinel-2 optical data"""
        try:
            if not sentinel2_data.get('data') or sentinel2_data.get('status') != 'success':
                return {
                    'cloud_percentage': 100,
                    'clear_pixels': 0,
                    'data_available': False,
                    'analysis_status': 'no_data'
                }
            
            # Try to process the satellite image data
            image_data = sentinel2_data['data']
            
            # If we have actual TIFF data, process it
            if isinstance(image_data, bytes):
                cloud_percentage = self._calculate_cloud_percentage_from_tiff(image_data)
            else:
                # Fallback estimation based on metadata or other indicators
                cloud_percentage = self._estimate_cloud_coverage(sentinel2_data)
            
            clear_pixels = max(0, 100 - cloud_percentage)
            
            return {
                'cloud_percentage': cloud_percentage,
                'clear_pixels': clear_pixels,
                'data_available': True,
                'quality_rating': 'excellent' if cloud_percentage < 10 else 'good' if cloud_percentage < 30 else 'poor',
                'analysis_status': 'success'
            }
            
        except Exception as e:
            return {
                'cloud_percentage': 75,  # Conservative estimate
                'clear_pixels': 25,
                'data_available': False,
                'analysis_status': f'error: {str(e)}'
            }
    
    def _calculate_cloud_percentage_from_tiff(self, tiff_data: bytes) -> float:
        """Calculate cloud percentage from TIFF image data"""
        try:
            # For now, estimate cloud coverage based on data availability
            # In production, this would use proper satellite image processing
            if tiff_data and len(tiff_data) > 1000:
                # Simple heuristic based on data size and content
                return 35.0  # Moderate cloud cover estimate
            else:
                return 80.0  # High cloud cover if no good data
                        
        except Exception:
            return 50  # Default cloud percentage if processing fails
    
    def _estimate_cloud_coverage(self, sentinel2_data: Dict[str, Any]) -> float:
        """Estimate cloud coverage from metadata or other indicators"""
        # This would typically use metadata from the satellite acquisition
        # For now, we'll use a conservative estimate
        
        # Check if there are any error indicators that might suggest cloudy conditions
        if sentinel2_data.get('status') == 'error':
            return 80  # High cloud cover likely if data fetch failed
        
        # Default moderate cloud cover estimate
        return 35
    
    def _analyze_sentinel1_quality(self, sentinel1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality of Sentinel-1 radar data"""
        try:
            if not sentinel1_data.get('data') or sentinel1_data.get('status') != 'success':
                return {
                    'data_available': False,
                    'signal_quality': 0.0,
                    'polarization_available': False,
                    'analysis_status': 'no_data'
                }
            
            # Analyze radar data quality
            quality_score = self._assess_radar_quality(sentinel1_data)
            
            return {
                'data_available': True,
                'signal_quality': quality_score,
                'polarization_available': sentinel1_data.get('polarization') == 'DV',
                'acquisition_mode': sentinel1_data.get('acquisition_mode', 'IW'),
                'quality_rating': 'excellent' if quality_score > 0.8 else 'good' if quality_score > 0.6 else 'fair',
                'analysis_status': 'success'
            }
            
        except Exception as e:
            return {
                'data_available': False,
                'signal_quality': 0.5,
                'polarization_available': False,
                'analysis_status': f'error: {str(e)}'
            }
    
    def _assess_radar_quality(self, sentinel1_data: Dict[str, Any]) -> float:
        """Assess the quality of radar data"""
        quality_score = 0.0
        
        # Base quality from data availability
        if sentinel1_data.get('data'):
            quality_score += 0.5
        
        # Quality from polarization
        if sentinel1_data.get('polarization') == 'DV':  # Dual polarization
            quality_score += 0.2
        
        # Quality from acquisition mode
        if sentinel1_data.get('acquisition_mode') == 'IW':  # Interferometric Wide swath
            quality_score += 0.2
        
        # Additional quality factors
        if sentinel1_data.get('bands') and len(sentinel1_data['bands']) >= 2:
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _calculate_quality_score(self, sensor: str, s1_analysis: Dict[str, Any], 
                                s2_analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score for a sensor"""
        if sensor == 'sentinel1':
            # Sentinel-1 quality factors
            data_quality = 0.8 if s1_analysis.get('data_available', False) else 0.0
            signal_quality = s1_analysis.get('signal_quality', 0.0)
            weather_independence = 0.9  # Radar works in all weather
            
            # Cloud cover doesn't affect radar, but optical cloud cover info is useful for context
            cloud_penalty = 0.0  # No penalty for radar
            
        else:  # sentinel2
            # Sentinel-2 quality factors
            data_quality = 0.8 if s2_analysis.get('data_available', False) else 0.0
            cloud_cover = s2_analysis.get('cloud_percentage', 100)
            weather_independence = max(0.0, 1.0 - (cloud_cover / 100))  # Heavily affected by clouds
            signal_quality = weather_independence  # For optical, clear conditions = good signal
            
            # Heavy penalty for high cloud cover
            cloud_penalty = (cloud_cover / 100) * 0.5
        
        # Calculate weighted score
        base_score = (
            data_quality * self.quality_weights['data_availability'] +
            signal_quality * self.quality_weights['spatial_coverage'] +
            weather_independence * self.quality_weights['cloud_cover']
        )
        
        # Apply cloud penalty for optical data
        final_score = max(0.0, base_score - cloud_penalty)
        
        return min(1.0, final_score)
    
    def _generate_reasoning(self, s1_analysis: Dict[str, Any], 
                          s2_analysis: Dict[str, Any], best_sensor: str) -> str:
        """Generate human-readable reasoning for sensor selection"""
        cloud_percentage = s2_analysis.get('cloud_percentage', 0)
        
        if best_sensor == 'Sentinel-1':
            if cloud_percentage > 50:
                return f"Sentinel-1 (radar) selected due to high cloud cover ({cloud_percentage:.1f}%). Radar can penetrate clouds for reliable flood detection."
            elif not s2_analysis.get('data_available', False):
                return "Sentinel-1 (radar) selected due to unavailable optical data. Radar provides consistent coverage regardless of weather conditions."
            else:
                return f"Sentinel-1 (radar) selected for superior data quality and weather independence. Cloud cover: {cloud_percentage:.1f}%."
        else:
            return f"Sentinel-2 (optical) selected due to excellent visibility conditions (cloud cover: {cloud_percentage:.1f}%). Optical imagery provides high-resolution surface detail."
    
    def get_cloud_mask(self, satellite_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Generate a cloud mask for the satellite data
        
        Args:
            satellite_data: Satellite data dictionary
            
        Returns:
            Numpy array representing cloud mask (1 = cloud, 0 = clear)
        """
        try:
            sentinel2_data = satellite_data.get('sentinel2', {})
            
            if not sentinel2_data.get('data') or sentinel2_data.get('status') != 'success':
                return None
            
            # Process the TIFF data to create cloud mask
            tiff_data = sentinel2_data['data']
            
            if isinstance(tiff_data, bytes):
                return self._create_cloud_mask_from_tiff(tiff_data)
            else:
                return None
                
        except Exception:
            return None
    
    def _create_cloud_mask_from_tiff(self, tiff_data: bytes) -> Optional[np.ndarray]:
        """Create cloud mask from TIFF data"""
        try:
            # Simplified cloud mask creation for demo purposes
            # Real implementation would process actual TIFF satellite data
            if tiff_data and len(tiff_data) > 1000:
                # Create a basic cloud mask pattern
                mask_size = (512, 512)
                cloud_mask = np.zeros(mask_size, dtype=np.uint8)
                # Add some simulated cloud patterns
                cloud_mask[100:200, 150:300] = 1
                cloud_mask[300:400, 200:350] = 1
                return cloud_mask
            else:
                return None
                        
        except Exception:
            return None
