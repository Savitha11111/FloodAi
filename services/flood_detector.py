import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import cv2
from sklearn.cluster import KMeans
from scipy import ndimage
from scipy.ndimage import binary_fill_holes, binary_opening, binary_closing

class FloodDetector:
    """AI-powered flood detection service using simplified UNet-like algorithms"""
    
    def __init__(self):
        """Initialize the flood detector with model parameters"""
        self.water_threshold_sar = 0.3  # Threshold for SAR-based water detection
        self.water_threshold_optical = 0.4  # Threshold for optical-based water detection
        self.min_flood_area = 100  # Minimum area in pixels to consider as flood
        self.confidence_threshold = 0.6  # Minimum confidence for flood detection
        
        # Model simulation parameters (representing trained UNet models)
        self.sar_model_weights = self._initialize_sar_weights()
        self.optical_model_weights = self._initialize_optical_weights()
    
    def detect_floods(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect floods in preprocessed satellite imagery
        
        Args:
            preprocessed_data: Preprocessed satellite data
            
        Returns:
            Dictionary containing flood detection results
        """
        try:
            sensor_type = preprocessed_data.get('sensor_type', 'unknown')
            image_array = preprocessed_data.get('image_array')
            
            if image_array is None:
                raise Exception("No image data available for flood detection")
            
            if sensor_type == 'SAR':
                flood_results = self._detect_floods_sar(preprocessed_data)
            elif sensor_type == 'optical':
                flood_results = self._detect_floods_optical(preprocessed_data)
            else:
                raise Exception(f"Unsupported sensor type: {sensor_type}")
            
            # Post-process results
            processed_results = self._post_process_detection(flood_results, preprocessed_data)
            
            return processed_results
            
        except Exception as e:
            raise Exception(f"Flood detection failed: {str(e)}")
    
    def _detect_floods_sar(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect floods using SAR (radar) data with UNet-like processing"""
        try:
            image_array = preprocessed_data['image_array']
            derived_products = preprocessed_data.get('derived_products', {})
            
            # Simulate SAR UNet model inference
            flood_probability = self._simulate_sar_unet(image_array, derived_products)
            
            # Create binary flood mask
            flood_mask = (flood_probability > self.water_threshold_sar).astype(np.uint8)
            
            # Calculate confidence metrics
            confidence_map = self._calculate_sar_confidence(image_array, flood_probability)
            mean_confidence = np.mean(confidence_map[flood_mask == 1]) if np.any(flood_mask) else 0.0
            
            # Identify flood regions
            flood_regions = self._identify_flood_regions(flood_mask, flood_probability)
            
            return {
                'flood_mask': flood_mask,
                'flood_probability': flood_probability,
                'confidence_map': confidence_map,
                'mean_confidence': mean_confidence,
                'flood_regions': flood_regions,
                'detection_method': 'SAR_UNet',
                'sensor_type': 'SAR'
            }
            
        except Exception as e:
            raise Exception(f"SAR flood detection failed: {str(e)}")
    
    def _detect_floods_optical(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect floods using optical data with UNet-like processing"""
        try:
            image_array = preprocessed_data['image_array']
            derived_products = preprocessed_data.get('derived_products', {})
            
            # Simulate Optical UNet model inference
            flood_probability = self._simulate_optical_unet(image_array, derived_products)
            
            # Create binary flood mask
            flood_mask = (flood_probability > self.water_threshold_optical).astype(np.uint8)
            
            # Calculate confidence metrics
            confidence_map = self._calculate_optical_confidence(image_array, flood_probability, derived_products)
            mean_confidence = np.mean(confidence_map[flood_mask == 1]) if np.any(flood_mask) else 0.0
            
            # Identify flood regions
            flood_regions = self._identify_flood_regions(flood_mask, flood_probability)
            
            return {
                'flood_mask': flood_mask,
                'flood_probability': flood_probability,
                'confidence_map': confidence_map,
                'mean_confidence': mean_confidence,
                'flood_regions': flood_regions,
                'detection_method': 'Optical_UNet',
                'sensor_type': 'optical'
            }
            
        except Exception as e:
            raise Exception(f"Optical flood detection failed: {str(e)}")
    
    def _simulate_sar_unet(self, image_array: np.ndarray, 
                          derived_products: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Simulate SAR UNet model for flood detection
        This represents the core AI model processing
        """
        try:
            height, width = image_array.shape[:2]
            flood_probability = np.zeros((height, width), dtype=np.float32)
            
            # Feature extraction (simulating UNet encoder)
            features = self._extract_sar_features(image_array, derived_products)
            
            # Multi-scale processing (simulating UNet architecture)
            for scale_factor in [1.0, 0.5, 0.25]:
                scaled_features = self._apply_scale_processing(features, scale_factor)
                scale_probability = self._apply_sar_classification(scaled_features)
                
                # Resize back to original size and combine
                if scale_factor != 1.0:
                    scale_probability = cv2.resize(scale_probability, (width, height))
                
                flood_probability += scale_probability * self.sar_model_weights[scale_factor]
            
            # Apply contextual refinement (simulating UNet decoder)
            flood_probability = self._apply_contextual_refinement(flood_probability, features)
            
            # Normalize to [0, 1] range
            flood_probability = np.clip(flood_probability, 0, 1)
            
            return flood_probability
            
        except Exception as e:
            print(f"SAR UNet simulation failed: {str(e)}")
            return np.zeros(image_array.shape[:2], dtype=np.float32)
    
    def _simulate_optical_unet(self, image_array: np.ndarray,
                              derived_products: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Simulate Optical UNet model for flood detection
        """
        try:
            height, width = image_array.shape[:2]
            flood_probability = np.zeros((height, width), dtype=np.float32)
            
            # Feature extraction using spectral information
            features = self._extract_optical_features(image_array, derived_products)
            
            # Multi-scale processing
            for scale_factor in [1.0, 0.5, 0.25]:
                scaled_features = self._apply_scale_processing(features, scale_factor)
                scale_probability = self._apply_optical_classification(scaled_features)
                
                # Resize back to original size and combine
                if scale_factor != 1.0:
                    scale_probability = cv2.resize(scale_probability, (width, height))
                
                flood_probability += scale_probability * self.optical_model_weights[scale_factor]
            
            # Apply spectral enhancement
            if 'ndwi' in derived_products:
                ndwi_boost = np.clip(derived_products['ndwi'], 0, 1)
                flood_probability = flood_probability * (1 + 0.3 * ndwi_boost)
            
            # Apply contextual refinement
            flood_probability = self._apply_contextual_refinement(flood_probability, features)
            
            # Normalize to [0, 1] range
            flood_probability = np.clip(flood_probability, 0, 1)
            
            return flood_probability
            
        except Exception as e:
            print(f"Optical UNet simulation failed: {str(e)}")
            return np.zeros(image_array.shape[:2], dtype=np.float32)
    
    def _extract_sar_features(self, image_array: np.ndarray,
                             derived_products: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Extract features from SAR data for flood detection"""
        features = {}
        
        try:
            if image_array.shape[-1] >= 2:
                vv = image_array[:, :, 0]
                vh = image_array[:, :, 1]
                
                # Backscatter features
                features['vv_intensity'] = vv
                features['vh_intensity'] = vh
                features['total_power'] = vv + vh
                
                # Polarimetric features
                if 'cross_pol_ratio' in derived_products:
                    features['cross_pol_ratio'] = derived_products['cross_pol_ratio']
                
                # Texture features
                if 'texture' in derived_products:
                    features['texture'] = derived_products['texture']
                
                # Water-specific SAR features
                features['water_indicator'] = self._calculate_sar_water_indicator(vv, vh)
                
            return features
            
        except Exception as e:
            print(f"SAR feature extraction failed: {str(e)}")
            return {'dummy': np.zeros(image_array.shape[:2])}
    
    def _extract_optical_features(self, image_array: np.ndarray,
                                 derived_products: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Extract features from optical data for flood detection"""
        features = {}
        
        try:
            # Basic spectral bands
            if image_array.shape[-1] >= 4:
                features['red'] = image_array[:, :, 0]
                features['green'] = image_array[:, :, 1]
                features['blue'] = image_array[:, :, 2]
                features['nir'] = image_array[:, :, 3]
                
                if image_array.shape[-1] >= 6:
                    features['swir1'] = image_array[:, :, 4]
                    features['swir2'] = image_array[:, :, 5]
            
            # Spectral indices
            for key, value in derived_products.items():
                if key in ['ndvi', 'ndwi', 'mndwi']:
                    features[key] = value
            
            # Water-specific optical features
            if 'ndwi' in features:
                features['water_probability'] = np.clip(features['ndwi'], 0, 1)
            
            return features
            
        except Exception as e:
            print(f"Optical feature extraction failed: {str(e)}")
            return {'dummy': np.zeros(image_array.shape[:2])}
    
    def _calculate_sar_water_indicator(self, vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """Calculate water indicator from SAR polarizations"""
        try:
            # Water typically has low backscatter and low cross-pol ratio
            low_backscatter = 1.0 - np.clip(vv, 0, 1)  # Invert VV (water = low VV)
            low_cross_pol = 1.0 - np.clip(vh, 0, 1)    # Invert VH (water = low VH)
            
            # Combine indicators
            water_indicator = (low_backscatter + low_cross_pol) / 2.0
            
            return water_indicator
            
        except Exception:
            return np.zeros_like(vv)
    
    def _apply_scale_processing(self, features: Dict[str, np.ndarray],
                               scale_factor: float) -> Dict[str, np.ndarray]:
        """Apply multi-scale processing to features"""
        if scale_factor == 1.0:
            return features
        
        scaled_features = {}
        
        for key, feature in features.items():
            try:
                if scale_factor < 1.0:
                    # Downsample
                    new_size = (int(feature.shape[1] * scale_factor),
                               int(feature.shape[0] * scale_factor))
                    scaled_features[key] = cv2.resize(feature, new_size)
                else:
                    scaled_features[key] = feature
            except Exception:
                scaled_features[key] = feature
        
        return scaled_features
    
    def _apply_sar_classification(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """Apply SAR-specific classification logic"""
        try:
            # Get the main features
            if 'water_indicator' in features:
                base_probability = features['water_indicator']
            elif 'vv_intensity' in features:
                # Fallback: use low VV backscatter as water indicator
                base_probability = 1.0 - np.clip(features['vv_intensity'], 0, 1)
            else:
                return np.zeros(list(features.values())[0].shape, dtype=np.float32)
            
            # Enhance with additional features
            if 'cross_pol_ratio' in features:
                # Low cross-pol ratio indicates water
                cross_pol_enhancement = 1.0 - np.clip(features['cross_pol_ratio'], 0, 1)
                base_probability = (base_probability + cross_pol_enhancement) / 2.0
            
            # Apply texture constraints (water should have low texture)
            if 'texture' in features:
                texture_mask = features['texture'] < 0.3  # Low texture threshold
                base_probability = base_probability * texture_mask.astype(np.float32)
            
            return np.clip(base_probability, 0, 1)
            
        except Exception as e:
            print(f"SAR classification failed: {str(e)}")
            return np.zeros(list(features.values())[0].shape, dtype=np.float32)
    
    def _apply_optical_classification(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """Apply optical-specific classification logic"""
        try:
            # Primary water detection using NDWI
            if 'ndwi' in features:
                base_probability = np.clip(features['ndwi'], 0, 1)
            elif 'water_probability' in features:
                base_probability = features['water_probability']
            else:
                # Fallback: use spectral characteristics
                if 'blue' in features and 'nir' in features:
                    # Water typically has higher blue reflectance than NIR
                    blue_nir_ratio = np.divide(features['blue'], features['nir'] + 0.001)
                    base_probability = np.clip(blue_nir_ratio - 0.5, 0, 1)
                else:
                    return np.zeros(list(features.values())[0].shape, dtype=np.float32)
            
            # Enhance with MNDWI if available
            if 'mndwi' in features:
                mndwi_boost = np.clip(features['mndwi'], 0, 1)
                base_probability = (base_probability + mndwi_boost) / 2.0
            
            # Suppress vegetation (using NDVI)
            if 'ndvi' in features:
                vegetation_mask = features['ndvi'] < 0.3  # Low vegetation threshold
                base_probability = base_probability * vegetation_mask.astype(np.float32)
            
            return np.clip(base_probability, 0, 1)
            
        except Exception as e:
            print(f"Optical classification failed: {str(e)}")
            return np.zeros(list(features.values())[0].shape, dtype=np.float32)
    
    def _apply_contextual_refinement(self, probability_map: np.ndarray,
                                    features: Dict[str, np.ndarray]) -> np.ndarray:
        """Apply contextual refinement to probability map"""
        try:
            refined = probability_map.copy()
            
            # Apply spatial smoothing (simulate UNet decoder upsampling)
            refined = cv2.GaussianBlur(refined, (5, 5), 1.0)
            
            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel)
            refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, kernel)
            
            # Edge-aware refinement
            if len(features) > 0:
                reference_feature = list(features.values())[0]
                edges = cv2.Canny((reference_feature * 255).astype(np.uint8), 50, 150)
                edge_mask = edges == 0  # Non-edge areas
                
                # Apply stronger smoothing in non-edge areas
                smooth_refined = cv2.GaussianBlur(refined, (7, 7), 2.0)
                refined = refined * (1 - edge_mask.astype(np.float32)) + smooth_refined * edge_mask.astype(np.float32)
            
            return np.clip(refined, 0, 1)
            
        except Exception as e:
            print(f"Contextual refinement failed: {str(e)}")
            return probability_map
    
    def _calculate_sar_confidence(self, image_array: np.ndarray,
                                 flood_probability: np.ndarray) -> np.ndarray:
        """Calculate confidence map for SAR flood detection"""
        try:
            confidence = np.ones_like(flood_probability)
            
            # Higher confidence for stronger water signatures
            if image_array.shape[-1] >= 2:
                vv = image_array[:, :, 0]
                vh = image_array[:, :, 1]
                
                # Confidence based on polarization characteristics
                pol_confidence = np.abs(vv - vh)  # Higher difference = higher confidence
                confidence *= np.clip(pol_confidence, 0.3, 1.0)
            
            # Higher confidence for clustered detections
            clustering_confidence = self._calculate_clustering_confidence(flood_probability)
            confidence *= clustering_confidence
            
            return np.clip(confidence, 0, 1)
            
        except Exception:
            return np.ones_like(flood_probability) * 0.7
    
    def _calculate_optical_confidence(self, image_array: np.ndarray,
                                     flood_probability: np.ndarray,
                                     derived_products: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate confidence map for optical flood detection"""
        try:
            confidence = np.ones_like(flood_probability)
            
            # Higher confidence for strong water indices
            if 'ndwi' in derived_products:
                ndwi_confidence = np.abs(derived_products['ndwi'])
                confidence *= np.clip(ndwi_confidence, 0.3, 1.0)
            
            # Lower confidence in vegetation areas
            if 'ndvi' in derived_products:
                veg_penalty = np.clip(derived_products['ndvi'], 0, 0.5) * 0.5
                confidence *= (1.0 - veg_penalty)
            
            # Higher confidence for clustered detections
            clustering_confidence = self._calculate_clustering_confidence(flood_probability)
            confidence *= clustering_confidence
            
            return np.clip(confidence, 0, 1)
            
        except Exception:
            return np.ones_like(flood_probability) * 0.7
    
    def _calculate_clustering_confidence(self, probability_map: np.ndarray) -> np.ndarray:
        """Calculate confidence based on spatial clustering of detections"""
        try:
            # Create binary mask for high probability areas
            binary_mask = (probability_map > 0.5).astype(np.uint8)
            
            # Calculate distance to nearest water pixel
            distance_transform = cv2.distanceTransform(1 - binary_mask, cv2.DIST_L2, 5)
            
            # Higher confidence for pixels closer to other water pixels
            clustering_confidence = 1.0 / (1.0 + distance_transform / 10.0)
            
            return clustering_confidence
            
        except Exception:
            return np.ones_like(probability_map)
    
    def _identify_flood_regions(self, flood_mask: np.ndarray,
                               flood_probability: np.ndarray) -> List[Dict[str, Any]]:
        """Identify individual flood regions and their properties"""
        try:
            # Find connected components
            num_labels, labels = cv2.connectedComponents(flood_mask)
            
            regions = []
            
            for label in range(1, num_labels):  # Skip background (label 0)
                region_mask = (labels == label)
                region_area = np.sum(region_mask)
                
                # Skip small regions
                if region_area < self.min_flood_area:
                    continue
                
                # Calculate region properties
                region_prob = np.mean(flood_probability[region_mask])
                y_coords, x_coords = np.where(region_mask)
                
                region_info = {
                    'region_id': label,
                    'area_pixels': int(region_area),
                    'centroid': (float(np.mean(x_coords)), float(np.mean(y_coords))),
                    'bbox': (int(np.min(x_coords)), int(np.min(y_coords)),
                            int(np.max(x_coords)), int(np.max(y_coords))),
                    'mean_probability': float(region_prob),
                    'severity': 'high' if region_prob > 0.7 else 'medium' if region_prob > 0.4 else 'low'
                }
                
                regions.append(region_info)
            
            return regions
            
        except Exception as e:
            print(f"Region identification failed: {str(e)}")
            return []
    
    def _post_process_detection(self, flood_results: Dict[str, Any],
                               preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process flood detection results"""
        try:
            # Calculate statistics
            flood_mask = flood_results['flood_mask']
            total_pixels = flood_mask.size
            flood_pixels = np.sum(flood_mask)
            flood_percentage = (flood_pixels / total_pixels) * 100
            
            # Estimate area in km² (assuming 10m pixel size)
            pixel_area_m2 = 100  # 10m x 10m pixel
            flood_area_km2 = (flood_pixels * pixel_area_m2) / 1e6
            
            # Determine overall risk level
            if flood_percentage > 10:
                risk_level = 'High'
            elif flood_percentage > 3:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            # Generate flood zones for mapping
            flood_zones = self._generate_flood_zones(flood_results, preprocessed_data)
            
            # Calculate final confidence
            overall_confidence = flood_results['mean_confidence']
            
            return {
                'flood_mask': flood_mask,
                'flood_probability': flood_results['flood_probability'],
                'confidence_map': flood_results['confidence_map'],
                'flood_regions': flood_results['flood_regions'],
                'flood_zones': flood_zones,
                'statistics': {
                    'total_pixels': total_pixels,
                    'flood_pixels': flood_pixels,
                    'flood_percentage': flood_percentage,
                    'affected_area_km2': flood_area_km2
                },
                'overall_risk': risk_level,
                'confidence': overall_confidence,
                'detection_method': flood_results['detection_method'],
                'sensor_type': flood_results['sensor_type']
            }
            
        except Exception as e:
            raise Exception(f"Post-processing failed: {str(e)}")
    
    def _generate_flood_zones(self, flood_results: Dict[str, Any],
                             preprocessed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate flood zones for map visualization"""
        try:
            zones = []
            location = preprocessed_data.get('location', {})
            bbox = preprocessed_data.get('bbox', [])
            
            if not location or not bbox:
                return zones
            
            base_lat = location.get('lat', 0)
            base_lon = location.get('lon', 0)
            
            # Convert image coordinates to geographic coordinates
            for region in flood_results.get('flood_regions', []):
                centroid_x, centroid_y = region['centroid']
                
                # Simple coordinate transformation (assuming small area)
                lat_offset = (centroid_y / 512) * (bbox[3] - bbox[1])
                lon_offset = (centroid_x / 512) * (bbox[2] - bbox[0])
                
                zone_lat = bbox[1] + lat_offset
                zone_lon = bbox[0] + lon_offset
                
                zone = {
                    'lat': zone_lat,
                    'lon': zone_lon,
                    'severity': region['mean_probability'],
                    'risk_level': region['severity'].title(),
                    'area_km2': region['area_pixels'] * 1e-4  # Rough conversion
                }
                
                zones.append(zone)
            
            return zones
            
        except Exception as e:
            print(f"Zone generation failed: {str(e)}")
            return []
    
    def _initialize_sar_weights(self) -> Dict[float, float]:
        """Initialize weights for SAR model simulation"""
        return {
            1.0: 0.6,   # Full resolution
            0.5: 0.3,   # Half resolution
            0.25: 0.1   # Quarter resolution
        }
    
    def _initialize_optical_weights(self) -> Dict[float, float]:
        """Initialize weights for optical model simulation"""
        return {
            1.0: 0.7,   # Full resolution
            0.5: 0.2,   # Half resolution  
            0.25: 0.1   # Quarter resolution
        }
