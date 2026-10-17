"""
Unit Tests for Multimodal Fusion and Missing-Modality Resilience.
"""
import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.fusion.model import MultimodalFusionLayer


@pytest.fixture
def fusion_layer():
    return MultimodalFusionLayer()


@pytest.fixture
def sample_clinical():
    return {
        "ktas_probabilities": [0.05, 0.20, 0.40, 0.25, 0.10],
        "base_risk_score": 0.45,
        "clinical_indices": {
            "shock_index": 0.72,
            "spo2": 97.0,
            "hr": 80.0,
            "sbp": 120.0,
            "dbp": 80.0,
            "altered_mental": 0.0
        },
        "shap_summary": []
    }


@pytest.fixture
def sample_ecg():
    return {
        "predicted_class": "Ventricular Ectopic / PVC (V)",
        "abnormality_score": 0.85,
        "is_abnormal": True,
        "class_probabilities": {"Normal": 0.1, "Ventricular": 0.85}
    }


@pytest.fixture
def sample_xray():
    return {
        "detected_findings": [
            {"condition": "Pleural Effusion", "probability": 0.72, "is_positive": True},
            {"condition": "Cardiomegaly", "probability": 0.65, "is_positive": True}
        ],
        "composite_abnormality_score": 0.72,
        "is_abnormal": True
    }


def test_clinical_vitals_only_mode(fusion_layer, sample_clinical):
    """Scenario 1: Clinical + Vitals Only (ECG & X-ray missing)."""
    mask = {"clinical": True, "vitals": True, "ecg": False, "xray": False}
    result = fusion_layer.fuse(
        clinical_output=sample_clinical,
        ecg_output=None,
        xray_output=None,
        mask=mask
    )
    assert result["modalities_used"]["count"] == 2
    assert result["modalities_used"]["ecg"] is False
    assert result["modalities_used"]["xray"] is False
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["priority"] in ["CRITICAL", "HIGH", "MODERATE", "LESS_URGENT", "NON_URGENT"]
    # Check that missing modalities are explicitly labeled
    for c in result["contributions"]:
        if c["modality"] in ["ECG Rhythm", "Chest Radiography"]:
            assert c["available"] is False


def test_clinical_plus_ecg_mode(fusion_layer, sample_clinical, sample_ecg):
    """Scenario 2: Clinical + Vitals + ECG (X-ray missing)."""
    mask = {"clinical": True, "vitals": True, "ecg": True, "xray": False}
    result = fusion_layer.fuse(
        clinical_output=sample_clinical,
        ecg_output=sample_ecg,
        xray_output=None,
        mask=mask
    )
    assert result["modalities_used"]["count"] == 3
    assert result["modalities_used"]["ecg"] is True
    assert result["modalities_used"]["xray"] is False
    # Malignant ventricular ectopic beat should elevate risk
    assert result["risk_score"] > 60.0


def test_clinical_plus_xray_mode(fusion_layer, sample_clinical, sample_xray):
    """Scenario 3: Clinical + Vitals + Chest X-ray (ECG missing)."""
    mask = {"clinical": True, "vitals": True, "ecg": False, "xray": True}
    result = fusion_layer.fuse(
        clinical_output=sample_clinical,
        ecg_output=None,
        xray_output=sample_xray,
        mask=mask
    )
    assert result["modalities_used"]["count"] == 3
    assert result["modalities_used"]["xray"] is True
    assert result["modalities_used"]["ecg"] is False


def test_full_multimodal_mode(fusion_layer, sample_clinical, sample_ecg, sample_xray):
    """Scenario 4: All 4 modalities present."""
    mask = {"clinical": True, "vitals": True, "ecg": True, "xray": True}
    result = fusion_layer.fuse(
        clinical_output=sample_clinical,
        ecg_output=sample_ecg,
        xray_output=sample_xray,
        mask=mask
    )
    assert result["modalities_used"]["count"] == 4
    assert result["confidence"] >= 75.0


def test_emergency_safety_override(fusion_layer):
    """Scenario 5: Severe shock and hypoxia triggers mandatory critical override."""
    critical_clinical = {
        "ktas_probabilities": [0.30, 0.40, 0.20, 0.05, 0.05],
        "base_risk_score": 0.65,
        "clinical_indices": {
            "shock_index": 1.35,  # Acute shock threshold
            "spo2": 82.0,         # Severe hypoxia
            "hr": 135.0,
            "sbp": 75.0,
            "dbp": 45.0,
            "altered_mental": 1.0
        },
        "shap_summary": []
    }
    result = fusion_layer.fuse(
        clinical_output=critical_clinical,
        ecg_output=None,
        xray_output=None
    )
    assert result["priority"] in ["CRITICAL", "HIGH"]
    assert result["risk_score"] >= 78.0
    assert len(result["safety_overrides"]) > 0
