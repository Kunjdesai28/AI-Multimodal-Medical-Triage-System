"""
Full End-to-End Multimodal Integration Test with real files.
"""
import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.main import app

client = TestClient(app)


def test_full_multimodal_assessment_with_files():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 1. Read real ECG sample line
    ecg_csv = os.path.join(base_dir, "datasets", "ECG_HeartBeat_Categorization", "mitbih_test.csv")
    assert os.path.exists(ecg_csv), "ECG dataset missing"
    with open(ecg_csv, "r") as f:
        ecg_sample_text = f.readline()
        
    # 2. Read real X-ray sample file
    xray_path = None
    for i in range(1, 13):
        folder = os.path.join(base_dir, "datasets", "xray_dataset", f"images_{i:03d}", "images")
        if not os.path.exists(folder):
            folder = os.path.join(base_dir, "datasets", "xray_dataset", f"images_{i:03d}")
        if os.path.exists(folder):
            pngs = [f for f in os.listdir(folder) if f.endswith(".png")]
            if pngs:
                xray_path = os.path.join(folder, pngs[0])
                break
                
    assert xray_path is not None, "NIH Chest X-ray image missing"
    with open(xray_path, "rb") as f:
        xray_bytes = f.read()

    patient_payload = {
        "patient_id": "PAT-FULL-WORKFLOW-777",
        "patient_name": "Full Workflow Subject",
        "vitals": {
            "age": 68,
            "sex": "Male",
            "arrival_mode": 2,
            "injury": 1,
            "chief_complaint": "Acute severe crushing chest pressure and diaphoresis",
            "symptoms": "Cold clammy skin, breathlessness, radiation to jaw",
            "mental": 1,
            "pain": 1,
            "nrs_pain": 9,
            "sbp": 82,
            "dbp": 52,
            "hr": 126,
            "rr": 26,
            "bt": 37.2,
            "saturation": 88
        }
    }

    files = {
        "patient_data": (None, json.dumps(patient_payload), "application/json"),
        "ecg_file": ("patient_ecg.csv", ecg_sample_text.encode("utf-8"), "text/csv"),
        "xray_file": ("patient_chest_xray.png", xray_bytes, "image/png")
    }

    response = client.post("/api/assessment", files=files)
    assert response.status_code == 200, f"Assessment failed: {response.text}"
    
    data = response.json()
    assert "assessment_id" in data
    assert data["patient_id"] == "PAT-FULL-WORKFLOW-777"
    assert data["modalities_used"]["count"] == 4
    assert data["modalities_used"]["clinical"] is True
    assert data["modalities_used"]["vitals"] is True
    assert data["modalities_used"]["ecg"] is True
    assert data["modalities_used"]["xray"] is True

    # High acuity verification: SBP 82, HR 126, SpO2 88% -> Critical/High priority
    assert data["priority"] in ["CRITICAL", "HIGH"]
    assert data["risk_score"] >= 75.0
    assert data["confidence"] >= 70.0

    # Verify SHAP factors present (new structured format or legacy list)
    shap_data = data["shap_factors"]
    if isinstance(shap_data, dict):
        assert "features" in shap_data
        assert len(shap_data["features"]) > 0
        assert "explained_class" in shap_data
        assert "explained_class_label" in shap_data
        assert "output_scale" in shap_data
        # Verify feature entries have required fields
        first_feature = shap_data["features"][0]
        assert "feature" in first_feature
        assert "label" in first_feature
        assert "shap_value" in first_feature
        assert "direction" in first_feature
    else:
        assert len(shap_data) > 0

    # Verify ECG analysis present
    assert data["ecg_analysis"] is not None
    assert "predicted_class" in data["ecg_analysis"]
    assert len(data["ecg_analysis"]["waveform"]) == 187

    # Verify X-ray Grad-CAM present
    assert data["xray_analysis"] is not None
    assert data["xray_analysis"]["overlay_b64"] is not None
    assert data["xray_analysis"]["heatmap_b64"] is not None
    assert data["xray_analysis"]["original_image_b64"] is not None
    assert "Model attention visualization" in data["xray_analysis"]["disclaimer"]
