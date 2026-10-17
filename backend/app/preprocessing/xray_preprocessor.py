"""
Chest X-ray Image Preprocessor.

Handles image loading, resizing (224x224), channel conversion (RGB/Grayscale),
and ImageNet standardization for the DenseNet model and Grad-CAM generation.
"""
import numpy as np
from PIL import Image
import io
from typing import Tuple


class XRayPreprocessor:
    TARGET_SIZE = (224, 224)
    # Standard ImageNet normalization parameters
    MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    @classmethod
    def process_image(cls, image_bytes: bytes) -> Tuple[np.ndarray, Image.Image]:
        """
        Loads image bytes, resizes to 224x224, ensures 3 RGB channels,
        and applies ImageNet normalization.
        
        Returns:
            - tensor_input: np.ndarray shape (1, 3, 224, 224)
            - pil_img: PIL Image resized for visual display and Grad-CAM overlay
        """
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to read image file: {str(e)}")
            
        pil_resized = pil_img.resize(cls.TARGET_SIZE, Image.Resampling.BILINEAR)
        
        # Convert to numpy array float32 in [0, 1]
        img_array = np.array(pil_resized, dtype=np.float32) / 255.0
        
        # Normalize
        normalized = (img_array - cls.MEAN) / cls.STD
        
        # Transpose from (H, W, C) to (C, H, W)
        chw = np.transpose(normalized, (2, 0, 1))
        tensor_input = np.expand_dims(chw, axis=0).astype(np.float32)
        
        return tensor_input, pil_resized
