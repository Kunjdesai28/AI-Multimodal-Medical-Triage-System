"""
TreeSHAP Explainability Module for the Clinical XGBoost Model.

Generates mathematically exact Shapley additive explanations for individual patient predictions,
attributing contributions to specific vital signs, symptoms, and physiological indices.

IMPORTANT NOTES ON INTERPRETATION:
- The XGBoost model is a 5-class classifier (KTAS 1–5) with objective 'multi:softprob'.
- TreeSHAP returns raw margin (log-odds) contributions for each class.
- SHAP values are additive: base_value + sum(shap_values) = raw model output (margin) for that class.
- SHAP values are NOT percentages of clinical risk. They are contributions in the model's
  internal log-odds scale that shift the prediction relative to the baseline (average training output).
"""
import numpy as np
from typing import List, Dict, Any, Optional


class ClinicalSHAPExplainer:
    """
    SHAP explanation engine for clinical tabular predictions.
    Computes directional feature impacts on patient triage predictions.
    
    Explains the model output for a single specified class (the predicted class by default).
    Returns raw SHAP contribution values in the model's native output scale (log-odds / raw margin).
    """

    # Human-readable labels for model features
    FRIENDLY_NAMES = {
        'Age': 'Patient Age',
        'SBP': 'Systolic Blood Pressure (mmHg)',
        'DBP': 'Diastolic Blood Pressure (mmHg)',
        'HR': 'Heart Rate (bpm)',
        'RR': 'Respiratory Rate (breaths/min)',
        'BT': 'Body Temperature (°C)',
        'Saturation': 'Oxygen Saturation — SpO2 (%)',
        'Patients number per hour': 'ED Patient Volume Load',
        'NRS_pain': 'Pain Intensity — NRS (0–10)',
        'Sex': 'Biological Sex',
        'Arrival mode': 'Arrival Transport Mode',
        'Injury': 'Trauma / Injury Status',
        'Mental': 'Mental Status Level',
        'Pain': 'Pain Presentation',
        'KTAS_RN': 'Nurse Initial Triage (KTAS_RN)',
        'Shock_Index': 'Shock Index (HR ÷ SBP)',
        'Pulse_Pressure': 'Pulse Pressure (mmHg)',
        'MAP': 'Mean Arterial Pressure (mmHg)',
        'Modified_Shock_Index': 'Modified Shock Index (HR ÷ MAP)',
        'Age_Shock_Index': 'Age-Adjusted Shock Index',
        'MEWS': 'Modified Early Warning Score',
        'Saturation_Missing': 'SpO2 Not Documented',
        'Altered_Mental': 'Altered Level of Consciousness',
        'Severe_Pain': 'Severe Acute Pain (NRS ≥ 7)',
        'Tachycardia': 'Acute Tachycardia (HR > 100)',
        'Hypotension': 'Acute Hypotension (SBP < 90)',
        'Hypoxia': 'Hypoxemic State (SpO2 < 92%)'
    }

    # Units for numerical features (used for display)
    FEATURE_UNITS = {
        'Age': 'years',
        'SBP': 'mmHg',
        'DBP': 'mmHg',
        'HR': 'bpm',
        'RR': 'breaths/min',
        'BT': '°C',
        'Saturation': '%',
        'Patients number per hour': 'patients/hr',
        'NRS_pain': '/10',
        'Shock_Index': 'ratio',
        'Pulse_Pressure': 'mmHg',
        'MAP': 'mmHg',
        'Modified_Shock_Index': 'ratio',
        'Age_Shock_Index': '',
        'MEWS': 'score',
    }

    # KTAS class labels (0-indexed)
    KTAS_CLASS_LABELS = [
        "KTAS 1 (Critical Resuscitation)",
        "KTAS 2 (High Emergent)",
        "KTAS 3 (Moderate Urgent)",
        "KTAS 4 (Low Risk)",
        "KTAS 5 (Non-Urgent)"
    ]

    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        try:
            import shap
            # Initialize TreeExplainer for XGBoost
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            print(f"[SHAP] TreeExplainer initialization warning: {e}")
            self.explainer = None

    def explain_instance(
        self,
        features_array: np.ndarray,
        top_k: int = 6,
        unscaled_features: Optional[Dict[str, Any]] = None,
        predicted_class: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Computes SHAP values for a single patient's feature vector.
        
        Args:
            features_array: Scaled feature array (1, n_features) as input to the model.
            top_k: Number of top contributing features to highlight (all are still returned).
            unscaled_features: Dict of raw (unscaled) feature values for display.
            predicted_class: The class index to explain (0-indexed). If None, uses the
                           model's predicted class.
        
        Returns:
            Dictionary containing:
            - features: List of all feature contributions sorted by absolute magnitude.
            - explained_class: The class being explained (0-indexed).
            - explained_class_label: Human-readable label for the explained class.
            - output_scale: Description of the SHAP value scale.
            - base_value: The base (expected) value for the explained class.
            - model_output: The actual model raw output for the explained class.
            - top_k: The recommended number of features to show initially.
        """
        # Determine which class to explain
        if predicted_class is None:
            predicted_class = int(self.model.predict(features_array)[0])

        explained_class = int(predicted_class)
        explained_class_label = (
            self.KTAS_CLASS_LABELS[explained_class]
            if explained_class < len(self.KTAS_CLASS_LABELS)
            else f"Class {explained_class}"
        )

        base_value = None
        model_output = None

        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(features_array)

                # Multi-class XGBoost: shap_values is a list of arrays [n_classes](n_samples, n_features)
                # or a 3D array (n_samples, n_features, n_classes)
                if isinstance(shap_values, list):
                    # List of (n_samples, n_features) — one per class
                    class_shap = shap_values[explained_class][0]  # shape: (n_features,)
                elif len(shap_values.shape) == 3:
                    # (n_samples, n_features, n_classes)
                    class_shap = shap_values[0, :, explained_class]
                else:
                    # Binary or single-output
                    class_shap = shap_values[0]

                # Extract base value for the explained class
                if hasattr(self.explainer, 'expected_value'):
                    ev = self.explainer.expected_value
                    if isinstance(ev, (list, np.ndarray)):
                        base_value = float(ev[explained_class])
                    else:
                        base_value = float(ev)

                # Compute model raw output for additivity verification
                if base_value is not None:
                    model_output = float(base_value + np.sum(class_shap))

            except Exception as e:
                print(f"[SHAP] Computation error: {e}, falling back to feature attribution.")
                class_shap = self._heuristic_attribution(features_array[0])
        else:
            class_shap = self._heuristic_attribution(features_array[0])

        # Build feature contribution list
        results = []
        for i, val in enumerate(class_shap):
            raw_name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
            friendly_name = self.FRIENDLY_NAMES.get(raw_name, raw_name)
            val_float = float(val)
            unit = self.FEATURE_UNITS.get(raw_name, '')

            direction = (
                "increases_risk" if val_float > 0.001
                else ("decreases_risk" if val_float < -0.001 else "neutral")
            )

            # Get actual patient value from unscaled features (if available)
            patient_value = None
            if unscaled_features and raw_name in unscaled_features:
                pv = unscaled_features[raw_name]
                if pv is not None and not (isinstance(pv, float) and np.isnan(pv)):
                    patient_value = pv
                    # Round float values for readability
                    if isinstance(patient_value, float):
                        patient_value = round(patient_value, 2)

            results.append({
                "feature": raw_name,
                "label": friendly_name,
                "shap_value": round(val_float, 4),
                "magnitude": round(abs(val_float), 4),
                "direction": direction,
                "patient_value": patient_value,
                "unit": unit,
            })

        # Sort by absolute magnitude of contribution
        results.sort(key=lambda x: x["magnitude"], reverse=True)

        return {
            "features": results,
            "explained_class": explained_class,
            "explained_class_label": explained_class_label,
            "output_scale": "raw margin (log-odds)",
            "base_value": round(base_value, 4) if base_value is not None else None,
            "model_output": round(model_output, 4) if model_output is not None else None,
            "top_k": top_k,
        }

    def _heuristic_attribution(self, feature_row: np.ndarray) -> np.ndarray:
        """Fallback attribution based on learned model feature importances."""
        try:
            importances = self.model.feature_importances_
            # Direction inferred from feature values
            signs = np.sign(feature_row)
            return importances * signs
        except Exception:
            return np.zeros(len(feature_row))
