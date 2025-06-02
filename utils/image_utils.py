import numpy as np
from PIL import Image
import io
import base64
from typing import Dict, Any, Optional, Tuple

class ImageProcessor:
    """Utility class for image processing and visualization"""
    
    def __init__(self):
        """Initialize image processor"""
        pass
    
    def array_to_image(self, image_array: np.ndarray) -> Optional[Image.Image]:
        """
        Convert numpy array to PIL Image
        
        Args:
            image_array: Numpy array representing image
            
        Returns:
            PIL Image object or None if conversion fails
        """
        try:
            # Normalize array to 0-255 range
            if image_array.dtype != np.uint8:
                if image_array.max() <= 1.0:
                    # Assume values are in 0-1 range
                    image_array = (image_array * 255).astype(np.uint8)
                else:
                    # Normalize to 0-255
                    image_array = ((image_array - image_array.min()) / 
                                 (image_array.max() - image_array.min()) * 255).astype(np.uint8)
            
            # Handle different array shapes
            if len(image_array.shape) == 2:
                # Grayscale
                return Image.fromarray(image_array, mode='L')
            elif len(image_array.shape) == 3:
                if image_array.shape[2] == 1:
                    # Single channel
                    return Image.fromarray(image_array[:, :, 0], mode='L')
                elif image_array.shape[2] == 3:
                    # RGB
                    return Image.fromarray(image_array, mode='RGB')
                elif image_array.shape[2] == 4:
                    # RGBA
                    return Image.fromarray(image_array, mode='RGBA')
            
            return None
            
        except Exception as e:
            print(f"Array to image conversion failed: {str(e)}")
            return None
    
    def image_to_base64(self, image: Image.Image, format: str = 'PNG') -> Optional[str]:
        """
        Convert PIL Image to base64 string
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Base64 encoded string or None if conversion fails
        """
        try:
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return image_base64
            
        except Exception as e:
            print(f"Image to base64 conversion failed: {str(e)}")
            return None
    
    def create_overlay_image(self, base_image: np.ndarray, 
                           overlay_mask: np.ndarray,
                           overlay_color: Tuple[int, int, int] = (255, 0, 0),
                           alpha: float = 0.5) -> Optional[np.ndarray]:
        """
        Create overlay image with flood mask
        
        Args:
            base_image: Base satellite image
            overlay_mask: Binary flood mask
            overlay_color: RGB color for overlay
            alpha: Transparency level
            
        Returns:
            Combined image array or None if processing fails
        """
        try:
            # Ensure base image is RGB
            if len(base_image.shape) == 2:
                base_rgb = np.stack([base_image] * 3, axis=-1)
            elif base_image.shape[-1] == 1:
                base_rgb = np.repeat(base_image, 3, axis=-1)
            else:
                base_rgb = base_image[:, :, :3]
            
            # Normalize base image
            if base_rgb.max() <= 1.0:
                base_rgb = (base_rgb * 255).astype(np.uint8)
            
            # Create overlay
            overlay = np.zeros_like(base_rgb)
            for i, color_val in enumerate(overlay_color):
                overlay[:, :, i] = overlay_mask * color_val
            
            # Blend images
            result = base_rgb.copy()
            mask_indices = overlay_mask > 0
            result[mask_indices] = (
                (1 - alpha) * base_rgb[mask_indices] + 
                alpha * overlay[mask_indices]
            ).astype(np.uint8)
            
            return result
            
        except Exception as e:
            print(f"Overlay creation failed: {str(e)}")
            return None