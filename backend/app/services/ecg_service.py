"""
ECG Analysis Service.

Loads the trained 1D CNN model, runs inference on cardiac leads,
computes rhythm category probabilities, extracts a 32-dim latent embedding,
and generates morphological signal interpretations.
"""
import os
import torch
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from ..models.ecg_cnn import ECG1DCNN
from ..preprocessing.ecg_preprocessor import ECGPreprocessor
from ..explainability.ecg_analyzer import ECGSignalAnalyzer


class ECGService:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_models"))
        self.model_dir = model_dir
        self.device = torch.device("cpu")
        self.model = None
        self.is_ready = False
        self._load_model()

    def _load_model(self):
        ckpt_path = os.path.join(self.model_dir, "ecg_1dcnn.pt")
        if os.path.exists(ckpt_path):
            try:
                self.model = ECG1DCNN(in_channels=1, num_classes=5, latent_dim=32)
                self.model.load_state_dict(torch.load(ckpt_path, map_location=self.device, weights_only=True))
                self.model.eval()
                self.is_ready = True
                print("[ECGService] Successfully loaded trained 1D CNN model.")
            except Exception as e:
                print(f"[ECGService] Error loading model checkpoint: {e}")
                self.is_ready = False
        else:
            print(f"[ECGService] Checkpoint not found at {ckpt_path}")

    def predict_signal(self, signal_tensor: np.ndarray, raw_waveform: List[float]) -> Dict[str, Any]:
        """
        Executes real inference on 187-sample signal lead.
        
        Args:
            signal_tensor: np.ndarray of shape (1, 1, 187)
            raw_waveform: List[float] length 187
        """
        if not self.is_ready or self.model is None:
            raise RuntimeError("ECG 1D CNN model not loaded. Please train model using training/train_ecg.py first.")

        tensor = torch.tensor(signal_tensor, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            logits, latent = self.model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            latent_vec = latent.cpu().numpy()[0].tolist()

        pred_idx = int(np.argmax(probs))
        class_names = self.model.class_names
        pred_label = class_names[pred_idx]

        # Normal rhythm is class 0; classes 1, 2, 3, 4 are arrhythmias
        is_abnormal = bool(pred_idx != 0)
        
        # Abnormality score: weighted probability of non-normal beats
        # Ventricular (class 2) carries highest acute clinical risk
        abnormality_score = float(probs[1] * 0.5 + probs[2] * 0.95 + probs[3] * 0.6 + probs[4] * 0.4)
        abnormality_score = min(max(abnormality_score, 0.0), 1.0)

        # Morphology & R-peak interpretation
        morph_info = ECGSignalAnalyzer.analyze_waveform(np.array(raw_waveform), pred_label)

        prob_dict = {class_names[i]: round(float(probs[i]), 4) for i in range(len(class_names))}

        return {
            "predicted_class": pred_label,
            "class_index": pred_idx,
            "abnormality_score": round(abnormality_score, 4),
            "is_abnormal": is_abnormal,
            "class_probabilities": prob_dict,
            "latent_representation": latent_vec,
            "estimated_heart_rate": morph_info["estimated_heart_rate"],
            "qrs_duration_ms": morph_info["qrs_duration_ms"],
            "anomalous_regions": morph_info["anomalous_regions"],
            "waveform": raw_waveform,
            "interpretation_summary": morph_info["interpretation_summary"]
        }

    def process_file_bytes(self, file_bytes: bytes) -> Dict[str, Any]:
        """Convenience method to parse uploaded CSV and execute prediction."""
        tensor_input, waveform = ECGPreprocessor.parse_uploaded_csv(file_bytes)
        return self.predict_signal(tensor_input, waveform)
