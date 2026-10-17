"""
Chest X-ray Analysis Service.

Loads the trained DenseNet121 model, runs inference on radiographic images,
detects emergency thoracic pathologies, extracts a 64-dim latent embedding,
and generates real Grad-CAM heatmaps with clinical overlays.
"""
import os
import torch
import numpy as np
from typing import Dict, Any, List, Optional
from PIL import Image

from ..models.xray_densenet import XRayDenseNet
from ..preprocessing.xray_preprocessor import XRayPreprocessor
from ..explainability.gradcam import GradCAMExplainer


class XRayService:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_models"))
        self.model_dir = model_dir
        self.device = torch.device("cpu")
        self.model = None
        self.gradcam = None
        self.is_ready = False
        self._load_model()

    def _load_model(self):
        ckpt_path = os.path.join(self.model_dir, "xray_densenet.pt")
        if os.path.exists(ckpt_path):
            try:
                self.model = XRayDenseNet(num_classes=8, latent_dim=64, pretrained=False)
                self.model.load_state_dict(torch.load(ckpt_path, map_location=self.device, weights_only=True))
                self.model.eval()
                self.gradcam = GradCAMExplainer(self.model)
                self.is_ready = True
                print("[XRayService] Successfully loaded trained DenseNet model and Grad-CAM explainer.")
            except Exception as e:
                print(f"[XRayService] Error loading model checkpoint: {e}")
                self.is_ready = False
        else:
            print(f"[XRayService] Checkpoint not found at {ckpt_path}")

    def predict_image(self, tensor_input: np.ndarray, pil_img: Image.Image) -> Dict[str, Any]:
        """
        Executes real inference on chest radiograph.
        Generates findings probabilities, abnormality score, and Grad-CAM attention heatmap.
        """
        if not self.is_ready or self.model is None:
            raise RuntimeError("Chest X-ray DenseNet model not loaded. Please train model using training/train_xray.py first.")

        tensor = torch.tensor(tensor_input, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            logits, latent = self.model(tensor)
            probs = torch.sigmoid(logits).cpu().numpy()[0]
            latent_vec = latent.cpu().numpy()[0].tolist()

        conditions = self.model.TARGET_CONDITIONS
        findings = []
        for i, cond in enumerate(conditions):
            prob = float(probs[i])
            findings.append({
                "condition": cond,
                "probability": round(prob, 4),
                "is_positive": bool(prob > 0.45 and cond != "Normal / No Finding")
            })

        # Calculate composite acute abnormality score
        # Acute conditions: Pneumothorax, Edema, Effusion carry highest emergency weights
        acute_weights = {
            "Normal / No Finding": 0.0,
            "Cardiomegaly": 0.4,
            "Pleural Effusion": 0.6,
            "Pneumothorax": 0.9,
            "Pulmonary Edema": 0.85,
            "Infiltration": 0.35,
            "Pneumonia": 0.55,
            "Atelectasis": 0.35
        }
        
        abnormality_score = 0.0
        for f in findings:
            w = acute_weights.get(f["condition"], 0.3)
            abnormality_score = max(abnormality_score, f["probability"] * w)

        is_abnormal = bool(abnormality_score > 0.35)

        # Sort findings by probability
        abnormal_findings = [f for f in findings if f["condition"] != "Normal / No Finding"]
        abnormal_findings.sort(key=lambda x: x["probability"], reverse=True)
        top_condition = abnormal_findings[0]["condition"] if is_abnormal and abnormal_findings else "Normal / No Finding"

        # Generate Real Grad-CAM Overlay
        gradcam_res = self.gradcam.generate_overlay(tensor, pil_img)

        return {
            "top_condition": top_condition,
            "composite_abnormality_score": round(abnormality_score, 4),
            "is_abnormal": is_abnormal,
            "findings": findings,
            "latent_representation": latent_vec,
            "original_image_b64": gradcam_res["original_image_b64"],
            "heatmap_b64": gradcam_res["heatmap_b64"],
            "overlay_b64": gradcam_res["overlay_b64"],
            "disclaimer": "Model attention visualization — not a clinical diagnosis."
        }

    def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Executes emergency medical imaging assessment.
        Uses Universal Medical Vision (Gemini) when configured, augmented with local Grad-CAM attention heatmap.
        """
        # 1. Base local prediction & Grad-CAM overlay
        local_res = {}
        try:
            tensor_input, pil_img = XRayPreprocessor.process_image(image_bytes)
            local_res = self.predict_image(tensor_input, pil_img)
        except Exception as e:
            print(f"[XRayService] Local DenseNet preprocessing notice: {e}")

        # 2. Universal Vision API (if configured)
        from .universal_vision_service import UniversalVisionService
        u_svc = UniversalVisionService.get_instance()
        if u_svc.is_configured:
            try:
                ai_res = u_svc.analyze_medical_image(image_bytes)
                # Combine AI clinical reasoning with local Grad-CAM visual overlays
                combined = {**local_res, **ai_res}
                combined["composite_abnormality_score"] = float(ai_res.get("abnormality_score", local_res.get("composite_abnormality_score", 0.0)))
                combined["top_condition"] = ai_res.get("top_condition", local_res.get("top_condition", "Evaluated Scan"))
                combined["is_abnormal"] = bool(ai_res.get("is_abnormal", local_res.get("is_abnormal", False)))
                if "primary_findings" in ai_res:
                    combined["detected_findings"] = [
                        {"condition": f, "probability": round(combined["composite_abnormality_score"], 2), "is_positive": True}
                        for f in ai_res["primary_findings"]
                    ]
                return combined
            except Exception as e:
                print(f"[XRayService] Universal Vision API failed, falling back to local model: {e}")

        return local_res
