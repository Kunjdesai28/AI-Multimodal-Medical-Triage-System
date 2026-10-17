"""
Grad-CAM (Gradient-Weighted Class Activation Mapping) for Chest X-ray DenseNet.

Visualizes regions of the radiographic image that influenced the neural network's
abnormality prediction, producing an overlaid attention heatmap.

MANDATORY CLINICAL LABEL:
"Model attention visualization — not a clinical diagnosis."
"""
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import cv2
import io
import base64
from typing import Tuple, Dict, Any


class GradCAMExplainer:
    """
    Computes class activation maps for DenseNet121's final convolutional layer.
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

    def generate_heatmap(
        self,
        tensor_input: torch.Tensor,
        target_class_idx: int = None
    ) -> np.ndarray:
        """
        Generates 2D normalized heatmap [0, 1] for the specified class index.
        """
        self.model.zero_grad()
        
        # Track activations and gradients on the penultimate convolutional feature map
        features = self.model.features(tensor_input)
        features_activations = features.detach()
        features_gradients = []
        
        def grad_hook(grad):
            features_gradients.append(grad.detach())
            
        features.register_hook(grad_hook)
        
        # Complete remaining forward pass
        out = F.relu(features, inplace=False)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = torch.flatten(out, 1)
        latent = self.model.fc_latent(out)
        logits = self.model.classifier(latent)
        
        if target_class_idx is None:
            # Pick highest predicted abnormal class (excluding class 0 if normal)
            probs = torch.sigmoid(logits)
            if probs.shape[1] > 1:
                target_class_idx = int(torch.argmax(probs[0, 1:]).item() + 1)
            else:
                target_class_idx = int(torch.argmax(probs[0]).item())

        score = logits[0, target_class_idx]
        score.backward()

        if not features_gradients:
            return np.zeros((features_activations.shape[2], features_activations.shape[3]), dtype=np.float32)

        gradients = features_gradients[0].cpu().numpy()[0]  # (C, H, W)
        activations = features_activations.cpu().numpy()[0]  # (C, H, W)

        # Global average pooling of gradients
        weights = np.mean(gradients, axis=(1, 2))  # (C,)

        # Weighted sum of activations
        cam = np.zeros(activations.shape[1:], dtype=np.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]

        # Apply ReLU to keep features that positively correlate with the class
        cam = np.maximum(cam, 0)
        
        # Normalize
        cam_max = np.max(cam)
        if cam_max > 1e-7:
            cam = cam / cam_max
        else:
            cam = np.zeros_like(cam)

        return cam

    def generate_overlay(
        self,
        tensor_input: torch.Tensor,
        pil_image: Image.Image,
        target_class_idx: int = None
    ) -> Dict[str, Any]:
        """
        Produces side-by-side images and base64-encoded strings:
        - original_base64
        - heatmap_base64
        - overlay_base64
        """
        cam = self.generate_heatmap(tensor_input, target_class_idx)
        
        # Resize CAM to match original PIL image dimensions
        img_np = np.array(pil_image)
        cam_resized = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
        
        # Convert to 8-bit heatmap using JET colormap
        heatmap_uint8 = np.uint8(255 * cam_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # Superimpose heatmap onto original image
        overlay = cv2.addWeighted(img_np, 0.6, heatmap_color, 0.4, 0)
        
        # Encode into base64 PNGs
        def to_b64(img_arr: np.ndarray) -> str:
            pil = Image.fromarray(img_arr)
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

        return {
            "original_image_b64": to_b64(img_np),
            "heatmap_b64": to_b64(heatmap_color),
            "overlay_b64": to_b64(overlay),
            "disclaimer": "Model attention visualization — not a clinical diagnosis."
        }
