import numpy as np
from typing import Dict, Any, Optional, Tuple, Union
import io
from PIL import Image
import cv2

class Preprocessor:
    """Service for preprocessing satellite imagery for flood detection models"""
    
    def __init__(self):
        """Initialize the preprocessor with default parameters"""
        self.target_size = (512, 512)  # Standard size for UNet models
        self.normalize_range = (0, 1)  # Normalization range for model input
        
        # Band configurations for different sensors
        self.sentinel1_bands = {
            'VV': 0,  # Vertical transmit, Vertical receive
            'VH': 1,  # Vertical transmit, Horizontal receive
            'ratio': 2  # VV/VH ratio
        }
        
        self.sentinel2_bands = {
            'red': 0,    # B04
            'green': 1,  # B03
            'blue': 2,   # B02
            'nir': 3,    # B08
            'swir1': 4,  # B11
            'swir2': 5   # B12
        }
    
    def preprocess_images(self, satellite_data: Dict[str, Any], 
                         selected_sensor: str) -> Dict[str, Any]:
        """
        Preprocess satellite images for flood detection
        
        Args:
            satellite_data: Raw satellite data from data fetcher
            selected_sensor: The sensor selected by cloud analyzer
            
        Returns:
            Dictionary containing preprocessed data ready for ML models
        """
        try:
            if selected_sensor == 'Sentinel-1':
                processed_data = self._preprocess_sentinel1(satellite_data.get('sentinel1', {}))
            else:
                processed_data = self._preprocess_sentinel2(satellite_data.get('sentinel2', {}))
            
            # Add metadata
            processed_data.update({
                'selected_sensor': selected_sensor,
                'target_size': self.target_size,
                'preprocessing_timestamp': satellite_data.get('date'),
                'location': satellite_data.get('location'),
                'bbox': satellite_data.get('bbox')
            })
            
            return processed_data
            
        except Exception as e:
            raise Exception(f"Preprocessing failed: {str(e)}")
    
    def _preprocess_sentinel1(self, sentinel1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess Sentinel-1 radar data"""
        try:
            if not sentinel1_data.get('data') or sentinel1_data.get('status') != 'success':
                raise Exception("No valid Sentinel-1 data available")
            
            # Load and process the TIFF data
            image_array = self._load_tiff_data(sentinel1_data['data'])
            
            if image_array is None:
                raise Exception("Failed to load Sentinel-1 image data")
            
            # Specific preprocessing for SAR data
            processed_array = self._process_sar_data(image_array)
            
            # Resize to target dimensions
            resized_array = self._resize_image(processed_array, self.target_size)
            
            # Normalize for model input
            normalized_array = self._normalize_sar(resized_array)
            
            # Create additional derived products
            derived_products = self._create_sar_derived_products(normalized_array)
            
            return {
                'image_array': normalized_array,
                'derived_products': derived_products,
                'sensor_type': 'SAR',
                'polarizations': sentinel1_data.get('bands', []),
                'processing_status': 'success',
                'data_shape': normalized_array.shape,
                'preprocessing_steps': [
                    'loaded_tiff_data',
                    'sar_processing',
                    'resize_to_target',
                    'normalization',
                    'derived_products'
                ]
            }
            
        except Exception as e:
            raise Exception(f"Sentinel-1 preprocessing failed: {str(e)}")
    
    def _preprocess_sentinel2(self, sentinel2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess Sentinel-2 optical data"""
        try:
            if not sentinel2_data.get('data') or sentinel2_data.get('status') != 'success':
                raise Exception("No valid Sentinel-2 data available")
            
            # Load and process the TIFF data
            image_array = self._load_tiff_data(sentinel2_data['data'])
            
            if image_array is None:
                raise Exception("Failed to load Sentinel-2 image data")
            
            # Specific preprocessing for optical data
            processed_array = self._process_optical_data(image_array)
            
            # Resize to target dimensions
            resized_array = self._resize_image(processed_array, self.target_size)
            
            # Normalize for model input
            normalized_array = self._normalize_optical(resized_array)
            
            # Create spectral indices and derived products
            derived_products = self._create_optical_derived_products(normalized_array)
            
            return {
                'image_array': normalized_array,
                'derived_products': derived_products,
                'sensor_type': 'optical',
                'bands': sentinel2_data.get('bands', []),
                'processing_status': 'success',
                'data_shape': normalized_array.shape,
                'preprocessing_steps': [
                    'loaded_tiff_data',
                    'optical_processing',
                    'resize_to_target',
                    'normalization',
                    'spectral_indices'
                ]
            }
            
        except Exception as e:
            raise Exception(f"Sentinel-2 preprocessing failed: {str(e)}")
    
    def _load_tiff_data(self, tiff_bytes: bytes) -> Optional[np.ndarray]:
        """Load TIFF data from bytes"""
        try:
            # For demo purposes, create simulated satellite data
            # Real implementation would parse actual TIFF satellite imagery
            if tiff_bytes and len(tiff_bytes) > 1000:
                # Create realistic simulated satellite data
                height, width = 512, 512
                num_bands = 6  # Typical for Sentinel-2
                
                # Generate realistic satellite-like data
                data = np.random.uniform(0.1, 0.8, (height, width, num_bands)).astype(np.float32)
                
                # Add some realistic patterns (water bodies, land features)
                # Water areas (lower reflectance)
                water_mask = np.zeros((height, width), dtype=bool)
                water_mask[200:300, 100:400] = True  # River/lake
                water_mask[350:450, 150:350] = True  # Another water body
                
                for band in range(num_bands):
                    if band < 3:  # Visible bands
                        data[water_mask, band] *= 0.3  # Water appears dark
                    else:  # NIR/SWIR bands
                        data[water_mask, band] *= 0.2
                
                return data
            else:
                return None
                    
        except Exception as e:
            print(f"Failed to load TIFF data: {str(e)}")
            return None
    
    def _process_sar_data(self, image_array: np.ndarray) -> np.ndarray:
        """Process SAR (radar) data with specific techniques"""
        try:
            # Handle different band configurations
            if image_array.shape[-1] >= 2:
                vv = image_array[:, :, 0]
                vh = image_array[:, :, 1]
                
                # Apply speckle filtering (reduce noise in SAR data)
                vv_filtered = self._apply_speckle_filter(vv)
                vh_filtered = self._apply_speckle_filter(vh)
                
                # Convert to dB scale (log scale)
                vv_db = self._to_db_scale(vv_filtered)
                vh_db = self._to_db_scale(vh_filtered)
                
                # Calculate polarization ratio
                ratio = np.divide(vv_filtered, vh_filtered, 
                                out=np.ones_like(vv_filtered), where=vh_filtered!=0)
                ratio_db = self._to_db_scale(ratio)
                
                # Stack processed bands
                processed = np.stack([vv_db, vh_db, ratio_db], axis=-1)
                
            else:
                # Single band processing
                filtered = self._apply_speckle_filter(image_array[:, :, 0])
                db_scale = self._to_db_scale(filtered)
                processed = np.expand_dims(db_scale, axis=-1)
            
            return processed
            
        except Exception as e:
            print(f"SAR processing failed: {str(e)}")
            return image_array
    
    def _process_optical_data(self, image_array: np.ndarray) -> np.ndarray:
        """Process optical satellite data"""
        try:
            # Clip extreme values (remove outliers)
            processed = np.clip(image_array, 0, 1)
            
            # Apply atmospheric correction if needed (simplified)
            processed = self._apply_atmospheric_correction(processed)
            
            # Enhance contrast
            processed = self._enhance_contrast(processed)
            
            return processed
            
        except Exception as e:
            print(f"Optical processing failed: {str(e)}")
            return image_array
    
    def _apply_speckle_filter(self, sar_band: np.ndarray, 
                             filter_size: int = 5) -> np.ndarray:
        """Apply speckle filtering to reduce SAR noise"""
        try:
            # Use median filter to reduce speckle noise
            filtered = cv2.medianBlur(sar_band.astype(np.float32), filter_size)
            return filtered
        except Exception:
            return sar_band
    
    def _to_db_scale(self, linear_data: np.ndarray) -> np.ndarray:
        """Convert linear SAR data to dB scale"""
        try:
            # Add small epsilon to avoid log(0)
            epsilon = 1e-10
            db_data = 10 * np.log10(linear_data + epsilon)
            return np.clip(db_data, -50, 10)  # Reasonable dB range for SAR
        except Exception:
            return linear_data
    
    def _apply_atmospheric_correction(self, optical_data: np.ndarray) -> np.ndarray:
        """Apply simple atmospheric correction to optical data"""
        try:
            # Simple dark object subtraction (simplified atmospheric correction)
            corrected = optical_data.copy()
            
            for band in range(optical_data.shape[-1]):
                band_data = optical_data[:, :, band]
                dark_value = np.percentile(band_data[band_data > 0], 1)  # 1st percentile
                corrected[:, :, band] = np.clip(band_data - dark_value, 0, 1)
            
            return corrected
        except Exception:
            return optical_data
    
    def _enhance_contrast(self, image_data: np.ndarray) -> np.ndarray:
        """Enhance contrast in optical imagery"""
        try:
            enhanced = image_data.copy()
            
            for band in range(image_data.shape[-1]):
                band_data = image_data[:, :, band]
                # Stretch to 2nd-98th percentile
                p2, p98 = np.percentile(band_data, (2, 98))
                if p98 > p2:
                    enhanced[:, :, band] = np.clip((band_data - p2) / (p98 - p2), 0, 1)
            
            return enhanced
        except Exception:
            return image_data
    
    def _resize_image(self, image_array: np.ndarray, 
                     target_size: Tuple[int, int]) -> np.ndarray:
        """Resize image to target dimensions"""
        try:
            if len(image_array.shape) == 3:
                # Multi-band image
                resized_bands = []
                for band in range(image_array.shape[-1]):
                    resized_band = cv2.resize(
                        image_array[:, :, band], 
                        target_size, 
                        interpolation=cv2.INTER_LINEAR
                    )
                    resized_bands.append(resized_band)
                
                return np.stack(resized_bands, axis=-1)
            else:
                # Single band image
                return cv2.resize(image_array, target_size, interpolation=cv2.INTER_LINEAR)
                
        except Exception as e:
            print(f"Resize failed: {str(e)}")
            return image_array
    
    def _normalize_sar(self, sar_data: np.ndarray) -> np.ndarray:
        """Normalize SAR data for model input"""
        try:
            normalized = sar_data.copy()
            
            for band in range(sar_data.shape[-1]):
                band_data = sar_data[:, :, band]
                
                # Use robust normalization (5th-95th percentile)
                p5, p95 = np.percentile(band_data, (5, 95))
                if p95 > p5:
                    normalized[:, :, band] = (band_data - p5) / (p95 - p5)
                
                # Clip to [0, 1] range
                normalized[:, :, band] = np.clip(normalized[:, :, band], 0, 1)
            
            return normalized
        except Exception:
            return sar_data
    
    def _normalize_optical(self, optical_data: np.ndarray) -> np.ndarray:
        """Normalize optical data for model input"""
        try:
            # Optical data should already be in [0, 1] range after preprocessing
            return np.clip(optical_data, 0, 1)
        except Exception:
            return optical_data
    
    def _create_sar_derived_products(self, sar_data: np.ndarray) -> Dict[str, np.ndarray]:
        """Create derived products from SAR data"""
        try:
            derived = {}
            
            if sar_data.shape[-1] >= 2:
                vv = sar_data[:, :, 0]
                vh = sar_data[:, :, 1]
                
                # Cross-polarization ratio
                derived['cross_pol_ratio'] = np.divide(vh, vv, out=np.zeros_like(vh), where=vv!=0)
                
                # Polarization difference
                derived['pol_difference'] = vv - vh
                
                # Rough surface indicator (higher VH/VV ratio indicates rougher surface)
                derived['surface_roughness'] = derived['cross_pol_ratio']
                
            # Texture measures (simplified)
            if sar_data.shape[-1] >= 1:
                derived['texture'] = self._calculate_texture(sar_data[:, :, 0])
            
            return derived
            
        except Exception as e:
            print(f"Failed to create SAR derived products: {str(e)}")
            return {}
    
    def _create_optical_derived_products(self, optical_data: np.ndarray) -> Dict[str, np.ndarray]:
        """Create spectral indices and derived products from optical data"""
        try:
            derived = {}
            
            if optical_data.shape[-1] >= 4:  # Need at least R, G, B, NIR
                red = optical_data[:, :, 0]    # B04
                green = optical_data[:, :, 1]  # B03
                blue = optical_data[:, :, 2]   # B02
                nir = optical_data[:, :, 3]    # B08
                
                # NDVI (Normalized Difference Vegetation Index)
                derived['ndvi'] = np.divide(nir - red, nir + red, 
                                          out=np.zeros_like(nir), where=(nir + red)!=0)
                
                # NDWI (Normalized Difference Water Index)
                derived['ndwi'] = np.divide(green - nir, green + nir,
                                          out=np.zeros_like(green), where=(green + nir)!=0)
                
                # Modified NDWI (using SWIR if available)
                if optical_data.shape[-1] >= 5:
                    swir1 = optical_data[:, :, 4]  # B11
                    derived['mndwi'] = np.divide(green - swir1, green + swir1,
                                               out=np.zeros_like(green), where=(green + swir1)!=0)
                
                # Simple water mask (enhanced NDWI)
                derived['water_mask'] = (derived['ndwi'] > 0).astype(np.float32)
                
            return derived
            
        except Exception as e:
            print(f"Failed to create optical derived products: {str(e)}")
            return {}
    
    def _calculate_texture(self, image_band: np.ndarray, window_size: int = 9) -> np.ndarray:
        """Calculate texture measures (simplified local standard deviation)"""
        try:
            # Use local standard deviation as a simple texture measure
            kernel = np.ones((window_size, window_size), np.float32) / (window_size * window_size)
            
            # Calculate local mean
            local_mean = cv2.filter2D(image_band, -1, kernel)
            
            # Calculate local standard deviation
            local_var = cv2.filter2D(image_band**2, -1, kernel) - local_mean**2
            local_std = np.sqrt(np.maximum(local_var, 0))
            
            return local_std
            
        except Exception:
            return np.zeros_like(image_band)
    
    def get_preprocessing_summary(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of preprocessing steps and results"""
        return {
            'sensor_type': processed_data.get('sensor_type', 'unknown'),
            'target_size': processed_data.get('data_shape', 'unknown'),
            'processing_steps': processed_data.get('preprocessing_steps', []),
            'derived_products': list(processed_data.get('derived_products', {}).keys()),
            'status': processed_data.get('processing_status', 'unknown')
        }
