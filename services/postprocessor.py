import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import cv2
from scipy import ndimage
from scipy.ndimage import binary_fill_holes, binary_opening, binary_closing, label
from skimage import morphology, segmentation, measure
from sklearn.cluster import DBSCAN

class Postprocessor:
    """Service for post-processing and enhancing flood detection results"""
    
    def __init__(self):
        """Initialize the postprocessor with enhancement parameters"""
        self.min_flood_area = 50  # Minimum area in pixels for valid flood region
        self.max_hole_size = 20   # Maximum hole size to fill within flood regions
        self.smoothing_iterations = 2  # Number of morphological smoothing iterations
        self.edge_smoothing_kernel = 3  # Kernel size for edge smoothing
        self.confidence_threshold = 0.6  # Minimum confidence for region validation
        
    def enhance_flood_mask(self, flood_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance and clean up flood detection results
        
        Args:
            flood_results: Raw flood detection results from FloodDetector
            
        Returns:
            Enhanced flood detection results with cleaned masks and improved accuracy
        """
        try:
            # Extract components from flood results
            flood_mask = flood_results.get('flood_mask')
            flood_probability = flood_results.get('flood_probability')
            confidence_map = flood_results.get('confidence_map')
            
            if flood_mask is None or flood_probability is None:
                raise Exception("Missing required flood detection data")
            
            # Apply morphological cleaning
            cleaned_mask = self._apply_morphological_cleaning(flood_mask)
            
            # Remove small isolated regions
            filtered_mask = self._remove_small_regions(cleaned_mask, flood_probability, confidence_map)
            
            # Fill holes in flood regions
            filled_mask = self._fill_flood_holes(filtered_mask)
            
            # Smooth boundaries
            smoothed_mask = self._smooth_boundaries(filled_mask)
            
            # Enhance probability map based on cleaned mask
            enhanced_probability = self._enhance_probability_map(flood_probability, smoothed_mask)
            
            # Update confidence map
            updated_confidence = self._update_confidence_map(confidence_map, smoothed_mask, enhanced_probability)
            
            # Recalculate flood regions with enhanced data
            enhanced_regions = self._recalculate_flood_regions(smoothed_mask, enhanced_probability)
            
            # Calculate enhancement metrics
            enhancement_metrics = self._calculate_enhancement_metrics(
                flood_mask, smoothed_mask, flood_probability, enhanced_probability
            )
            
            # Generate enhanced flood zones
            enhanced_zones = self._generate_enhanced_flood_zones(enhanced_regions, enhancement_metrics)
            
            # Create final results dictionary
            enhanced_results = {
                'flood_mask': smoothed_mask,
                'flood_probability': enhanced_probability,
                'confidence_map': updated_confidence,
                'flood_regions': enhanced_regions,
                'flood_zones': enhanced_zones,
                'enhancement_metrics': enhancement_metrics,
                'original_results': flood_results,
                'postprocessing_applied': True,
                'processing_steps': [
                    'morphological_cleaning',
                    'small_region_removal',
                    'hole_filling',
                    'boundary_smoothing',
                    'probability_enhancement',
                    'confidence_update'
                ]
            }
            
            # Preserve original metadata
            for key in ['detection_method', 'sensor_type', 'statistics']:
                if key in flood_results:
                    enhanced_results[key] = flood_results[key]
            
            # Update statistics with enhanced data
            enhanced_results['statistics'] = self._update_statistics(enhanced_results)
            
            return enhanced_results
            
        except Exception as e:
            raise Exception(f"Post-processing enhancement failed: {str(e)}")
    
    def _apply_morphological_cleaning(self, flood_mask: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up the flood mask"""
        try:
            # Convert to binary if needed
            binary_mask = (flood_mask > 0).astype(np.uint8)
            
            # Define morphological kernels
            small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            medium_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            
            # Remove noise with opening operation
            cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, small_kernel)
            
            # Fill small gaps with closing operation
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, medium_kernel)
            
            # Apply additional smoothing iterations
            for _ in range(self.smoothing_iterations):
                cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, small_kernel)
                cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, small_kernel)
            
            return cleaned
            
        except Exception as e:
            print(f"Morphological cleaning failed: {str(e)}")
            return flood_mask
    
    def _remove_small_regions(self, flood_mask: np.ndarray, 
                             flood_probability: np.ndarray,
                             confidence_map: Optional[np.ndarray] = None) -> np.ndarray:
        """Remove small isolated flood regions based on size and confidence"""
        try:
            # Find connected components
            num_labels, labels = cv2.connectedComponents(flood_mask)
            
            # Create output mask
            filtered_mask = np.zeros_like(flood_mask)
            
            for label_id in range(1, num_labels):  # Skip background (0)
                region_mask = (labels == label_id)
                region_size = np.sum(region_mask)
                
                # Check size threshold
                if region_size < self.min_flood_area:
                    continue
                
                # Check average probability in region
                avg_probability = np.mean(flood_probability[region_mask])
                if avg_probability < 0.3:  # Low probability threshold
                    continue
                
                # Check confidence if available
                if confidence_map is not None:
                    avg_confidence = np.mean(confidence_map[region_mask])
                    if avg_confidence < self.confidence_threshold:
                        continue
                
                # Region passes all tests - keep it
                filtered_mask[region_mask] = 1
            
            return filtered_mask
            
        except Exception as e:
            print(f"Small region removal failed: {str(e)}")
            return flood_mask
    
    def _fill_flood_holes(self, flood_mask: np.ndarray) -> np.ndarray:
        """Fill small holes within flood regions"""
        try:
            # Fill holes using binary fill holes
            filled_mask = binary_fill_holes(flood_mask).astype(np.uint8)
            
            # Alternatively, use morphological closing for more control
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                             (self.max_hole_size, self.max_hole_size))
            filled_mask = cv2.morphologyEx(flood_mask, cv2.MORPH_CLOSE, kernel)
            
            return filled_mask
            
        except Exception as e:
            print(f"Hole filling failed: {str(e)}")
            return flood_mask
    
    def _smooth_boundaries(self, flood_mask: np.ndarray) -> np.ndarray:
        """Smooth flood region boundaries"""
        try:
            # Apply Gaussian smoothing followed by thresholding
            smoothed = cv2.GaussianBlur(flood_mask.astype(np.float32), 
                                      (self.edge_smoothing_kernel, self.edge_smoothing_kernel), 
                                      1.0)
            
            # Re-threshold to binary
            smoothed_binary = (smoothed > 0.5).astype(np.uint8)
            
            # Apply morphological smoothing
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            smoothed_binary = cv2.morphologyEx(smoothed_binary, cv2.MORPH_CLOSE, kernel)
            smoothed_binary = cv2.morphologyEx(smoothed_binary, cv2.MORPH_OPEN, kernel)
            
            return smoothed_binary
            
        except Exception as e:
            print(f"Boundary smoothing failed: {str(e)}")
            return flood_mask
    
    def _enhance_probability_map(self, flood_probability: np.ndarray, 
                                enhanced_mask: np.ndarray) -> np.ndarray:
        """Enhance probability map based on cleaned mask"""
        try:
            enhanced_prob = flood_probability.copy()
            
            # Boost probabilities within confirmed flood regions
            flood_regions = enhanced_mask > 0
            enhanced_prob[flood_regions] = np.maximum(
                enhanced_prob[flood_regions], 
                0.7  # Minimum probability for confirmed regions
            )
            
            # Reduce probabilities outside flood regions but close to edges
            distance_from_flood = cv2.distanceTransform(1 - enhanced_mask, cv2.DIST_L2, 5)
            edge_proximity = np.exp(-distance_from_flood / 10.0)  # Decay function
            
            non_flood_regions = enhanced_mask == 0
            enhanced_prob[non_flood_regions] *= (1 - 0.3 * edge_proximity[non_flood_regions])
            
            # Apply spatial smoothing to the probability map
            enhanced_prob = cv2.GaussianBlur(enhanced_prob, (5, 5), 1.0)
            
            return np.clip(enhanced_prob, 0, 1)
            
        except Exception as e:
            print(f"Probability map enhancement failed: {str(e)}")
            return flood_probability
    
    def _update_confidence_map(self, confidence_map: Optional[np.ndarray],
                              enhanced_mask: np.ndarray,
                              enhanced_probability: np.ndarray) -> np.ndarray:
        """Update confidence map based on post-processing results"""
        try:
            if confidence_map is None:
                confidence_map = np.ones_like(enhanced_mask, dtype=np.float32) * 0.7
            
            updated_confidence = confidence_map.copy()
            
            # Boost confidence in well-defined flood regions
            flood_regions = enhanced_mask > 0
            region_consistency = self._calculate_region_consistency(enhanced_mask, enhanced_probability)
            updated_confidence[flood_regions] = np.maximum(
                updated_confidence[flood_regions],
                region_consistency[flood_regions]
            )
            
            # Reduce confidence in areas with low probability but high original confidence
            low_prob_areas = (enhanced_probability < 0.3) & (confidence_map > 0.7)
            updated_confidence[low_prob_areas] *= 0.5
            
            return np.clip(updated_confidence, 0, 1)
            
        except Exception as e:
            print(f"Confidence map update failed: {str(e)}")
            return confidence_map if confidence_map is not None else np.ones_like(enhanced_mask) * 0.7
    
    def _calculate_region_consistency(self, mask: np.ndarray, 
                                    probability: np.ndarray) -> np.ndarray:
        """Calculate consistency metric for each pixel based on neighborhood"""
        try:
            # Calculate local consistency using neighborhood analysis
            kernel = np.ones((5, 5), np.float32) / 25
            local_mask_mean = cv2.filter2D(mask.astype(np.float32), -1, kernel)
            local_prob_mean = cv2.filter2D(probability, -1, kernel)
            
            # Consistency is high when local mask and probability agree
            consistency = 1.0 - np.abs(local_mask_mean - local_prob_mean)
            
            return np.clip(consistency, 0.5, 1.0)
            
        except Exception:
            return np.ones_like(mask, dtype=np.float32) * 0.8
    
    def _recalculate_flood_regions(self, enhanced_mask: np.ndarray,
                                  enhanced_probability: np.ndarray) -> List[Dict[str, Any]]:
        """Recalculate flood regions with enhanced data"""
        try:
            # Find connected components in enhanced mask
            num_labels, labels = cv2.connectedComponents(enhanced_mask)
            
            regions = []
            
            for label_id in range(1, num_labels):  # Skip background
                region_mask = (labels == label_id)
                region_area = np.sum(region_mask)
                
                if region_area < self.min_flood_area:
                    continue
                
                # Calculate enhanced region properties
                y_coords, x_coords = np.where(region_mask)
                region_prob = np.mean(enhanced_probability[region_mask])
                region_std = np.std(enhanced_probability[region_mask])
                
                # Calculate shape properties
                contours, _ = cv2.findContours(region_mask.astype(np.uint8), 
                                             cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    contour = contours[0]
                    perimeter = cv2.arcLength(contour, True)
                    compactness = (4 * np.pi * region_area) / (perimeter ** 2) if perimeter > 0 else 0
                else:
                    compactness = 0
                
                # Determine severity based on multiple factors
                if region_prob > 0.8 and region_area > 200:
                    severity = 'high'
                elif region_prob > 0.6 and region_area > 100:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                region_info = {
                    'region_id': label_id,
                    'area_pixels': int(region_area),
                    'centroid': (float(np.mean(x_coords)), float(np.mean(y_coords))),
                    'bbox': (int(np.min(x_coords)), int(np.min(y_coords)),
                            int(np.max(x_coords)), int(np.max(y_coords))),
                    'mean_probability': float(region_prob),
                    'probability_std': float(region_std),
                    'severity': severity,
                    'compactness': float(compactness),
                    'enhanced': True
                }
                
                regions.append(region_info)
            
            return regions
            
        except Exception as e:
            print(f"Region recalculation failed: {str(e)}")
            return []
    
    def _calculate_enhancement_metrics(self, original_mask: np.ndarray,
                                     enhanced_mask: np.ndarray,
                                     original_prob: np.ndarray,
                                     enhanced_prob: np.ndarray) -> Dict[str, Any]:
        """Calculate metrics showing the impact of post-processing"""
        try:
            # Basic statistics
            original_flood_pixels = np.sum(original_mask)
            enhanced_flood_pixels = np.sum(enhanced_mask)
            
            # Change in flood area
            area_change = enhanced_flood_pixels - original_flood_pixels
            area_change_percent = (area_change / max(original_flood_pixels, 1)) * 100
            
            # Probability improvements
            original_mean_prob = np.mean(original_prob[original_mask > 0]) if np.any(original_mask) else 0
            enhanced_mean_prob = np.mean(enhanced_prob[enhanced_mask > 0]) if np.any(enhanced_mask) else 0
            prob_improvement = enhanced_mean_prob - original_mean_prob
            
            # Noise reduction (based on region count)
            original_regions = self._count_regions(original_mask)
            enhanced_regions = self._count_regions(enhanced_mask)
            noise_reduction = original_regions - enhanced_regions
            
            # Boundary smoothness improvement
            original_boundary_roughness = self._calculate_boundary_roughness(original_mask)
            enhanced_boundary_roughness = self._calculate_boundary_roughness(enhanced_mask)
            smoothness_improvement = original_boundary_roughness - enhanced_boundary_roughness
            
            return {
                'area_change_pixels': int(area_change),
                'area_change_percent': float(area_change_percent),
                'probability_improvement': float(prob_improvement),
                'noise_reduction': int(noise_reduction),
                'smoothness_improvement': float(smoothness_improvement),
                'original_flood_pixels': int(original_flood_pixels),
                'enhanced_flood_pixels': int(enhanced_flood_pixels),
                'original_mean_probability': float(original_mean_prob),
                'enhanced_mean_probability': float(enhanced_mean_prob),
                'enhancement_quality': self._assess_enhancement_quality(area_change_percent, prob_improvement, noise_reduction)
            }
            
        except Exception as e:
            print(f"Enhancement metrics calculation failed: {str(e)}")
            return {
                'area_change_pixels': 0,
                'area_change_percent': 0.0,
                'probability_improvement': 0.0,
                'noise_reduction': 0,
                'smoothness_improvement': 0.0,
                'enhancement_quality': 'unknown'
            }
    
    def _count_regions(self, mask: np.ndarray) -> int:
        """Count the number of connected regions in a mask"""
        try:
            num_labels, _ = cv2.connectedComponents(mask)
            return num_labels - 1  # Subtract 1 for background
        except Exception:
            return 0
    
    def _calculate_boundary_roughness(self, mask: np.ndarray) -> float:
        """Calculate boundary roughness metric"""
        try:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return 0.0
            
            total_roughness = 0.0
            for contour in contours:
                if len(contour) > 10:  # Minimum points for meaningful calculation
                    perimeter = cv2.arcLength(contour, True)
                    area = cv2.contourArea(contour)
                    
                    if area > 0:
                        # Roughness based on perimeter to area ratio
                        roughness = perimeter / (2 * np.sqrt(np.pi * area))
                        total_roughness += roughness
            
            return total_roughness / len(contours) if contours else 0.0
            
        except Exception:
            return 0.0
    
    def _assess_enhancement_quality(self, area_change_percent: float,
                                   prob_improvement: float,
                                   noise_reduction: int) -> str:
        """Assess the overall quality of enhancement"""
        score = 0
        
        # Penalize excessive area changes
        if abs(area_change_percent) < 5:
            score += 1
        elif abs(area_change_percent) < 15:
            score += 0.5
        
        # Reward probability improvements
        if prob_improvement > 0.1:
            score += 1
        elif prob_improvement > 0:
            score += 0.5
        
        # Reward noise reduction
        if noise_reduction > 5:
            score += 1
        elif noise_reduction > 0:
            score += 0.5
        
        if score >= 2.5:
            return 'excellent'
        elif score >= 1.5:
            return 'good'
        elif score >= 0.5:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_enhanced_flood_zones(self, enhanced_regions: List[Dict[str, Any]],
                                     enhancement_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate enhanced flood zones with additional metadata"""
        try:
            zones = []
            
            for region in enhanced_regions:
                zone = {
                    'lat': 0,  # Will be filled by calling service with proper coordinates
                    'lon': 0,  # Will be filled by calling service with proper coordinates
                    'severity': region['mean_probability'],
                    'risk_level': region['severity'].title(),
                    'area_km2': region['area_pixels'] * 1e-4,  # Rough conversion
                    'confidence': min(1.0, region['mean_probability'] + 0.1),  # Boost for enhanced regions
                    'enhanced': True,
                    'compactness': region.get('compactness', 0),
                    'region_id': region['region_id']
                }
                zones.append(zone)
            
            return zones
            
        except Exception as e:
            print(f"Enhanced zone generation failed: {str(e)}")
            return []
    
    def _update_statistics(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Update statistics with enhanced data"""
        try:
            flood_mask = enhanced_results['flood_mask']
            total_pixels = flood_mask.size
            flood_pixels = np.sum(flood_mask)
            flood_percentage = (flood_pixels / total_pixels) * 100
            
            # Estimate area in km² (assuming 10m pixel size)
            pixel_area_m2 = 100  # 10m x 10m pixel
            flood_area_km2 = (flood_pixels * pixel_area_m2) / 1e6
            
            # Risk distribution
            regions = enhanced_results.get('flood_regions', [])
            risk_distribution = {'Low': 0, 'Medium': 0, 'High': 0}
            
            for region in regions:
                severity = region['severity'].title()
                if severity in risk_distribution:
                    risk_distribution[severity] += region['area_pixels']
            
            # Convert to percentages
            total_flood_pixels = sum(risk_distribution.values())
            if total_flood_pixels > 0:
                for key in risk_distribution:
                    risk_distribution[key] = (risk_distribution[key] / total_flood_pixels) * 100
            
            # Determine overall risk with enhanced criteria
            confidence = enhanced_results.get('confidence_map', np.array([0.7]))
            mean_confidence = np.mean(confidence)
            
            if flood_percentage > 10 and mean_confidence > 0.8:
                overall_risk = 'High'
            elif flood_percentage > 3 and mean_confidence > 0.6:
                overall_risk = 'Medium'
            else:
                overall_risk = 'Low'
            
            return {
                'total_pixels': total_pixels,
                'flood_pixels': flood_pixels,
                'flood_percentage': flood_percentage,
                'affected_area_km2': flood_area_km2,
                'risk_distribution': risk_distribution,
                'overall_risk': overall_risk,
                'confidence': mean_confidence,
                'enhanced': True,
                'risk_change': '+0.1%',  # Placeholder for trend
                'area_change': 0.1,      # Placeholder for trend
                'confidence_change': 0.05,  # Placeholder for trend
                'level_change': 0.1,     # Placeholder for water level trend
                'water_level_m': flood_percentage * 0.1  # Rough estimate
            }
            
        except Exception as e:
            print(f"Statistics update failed: {str(e)}")
            return {
                'total_pixels': 0,
                'flood_pixels': 0,
                'flood_percentage': 0,
                'affected_area_km2': 0,
                'enhanced': True
            }
