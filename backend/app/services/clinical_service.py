"""
Clinical Triage Service.

Orchestrates the Clinical XGBoost model, feature preprocessor,
TreeSHAP explainability, and symptom intelligence matcher.
"""
import os
import numpy as np
from typing import Dict, Any, List, Optional
import xgboost as xgb

from ..preprocessing.clinical_preprocessor import ClinicalPreprocessor
from ..preprocessing.symptom_matcher import SymptomMatcher
from ..explainability.shap_explainer import ClinicalSHAPExplainer


class ClinicalService:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_models"))
        self.model_dir = model_dir
        self.model = None
        self.preprocessor = None
        self.shap_explainer = None
        self.symptom_matcher = SymptomMatcher()
        self.is_ready = False
        self._load_models()

    def _load_models(self):
        model_path = os.path.join(self.model_dir, "clinical_xgboost.json")
        prep_path = os.path.join(self.model_dir, "clinical_preprocessor.joblib")

        if os.path.exists(model_path) and os.path.exists(prep_path):
            try:
                self.preprocessor = ClinicalPreprocessor.load(prep_path)
                self.model = xgb.XGBClassifier()
                self.model.load_model(model_path)
                self.shap_explainer = ClinicalSHAPExplainer(self.model, self.preprocessor.feature_names)
                self.is_ready = True
                print("[ClinicalService] Successfully loaded trained XGBoost model and preprocessor.")
            except Exception as e:
                print(f"[ClinicalService] Error loading model artifacts: {e}")
                self.is_ready = False
        else:
            print(f"[ClinicalService] Model artifacts not yet generated in {self.model_dir}")

    def predict_patient(self, patient_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes real inference on incoming patient clinical data.
        Returns probabilities, calculated indices, SHAP factors, and potential conditions.
        """
        if not self.is_ready or self.model is None:
            # If called before offline training script is run, raise informative error
            raise RuntimeError("Clinical XGBoost model not loaded. Please train model using training/train_clinical.py first.")

        # Transform features
        features, indices = self.preprocessor.transform_single_patient(patient_dict)
        
        # Predict multi-class probabilities: KTAS 1 to 5
        probs = self.model.predict_proba(features)[0]
        ktas_probs = [float(p) for p in probs]
        predicted_class = int(np.argmax(probs))
        
        # Weighted expectation of KTAS severity
        severity_weights = np.array([1.0, 0.75, 0.50, 0.25, 0.05])
        base_risk = float(np.dot(probs, severity_weights))

        # Real TreeSHAP explanation with patient feature values
        unscaled_features = indices.get('unscaled_features', {})
        shap_factors = self.shap_explainer.explain_instance(
            features,
            top_k=6,
            unscaled_features=unscaled_features,
            predicted_class=predicted_class
        )

        # Symptom context intelligence
        chief_complaint = patient_dict.get('chief_complaint', '')
        symptoms_text = patient_dict.get('symptoms', '')
        potential_conditions = self.symptom_matcher.match_symptoms(chief_complaint, symptoms_text, top_k=3)

        return {
            "ktas_probabilities": ktas_probs,
            "base_risk_score": round(base_risk, 4),
            "clinical_indices": indices,
            "shap_summary": shap_factors,
            "potential_conditions": potential_conditions
        }
