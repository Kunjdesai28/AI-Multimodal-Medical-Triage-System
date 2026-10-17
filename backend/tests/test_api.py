"""
FastAPI End-to-End API Integration Tests.
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.main import app

client = TestClient(app)


def test_root_and_health_endpoints():
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["system"] == "TRIAGEAI"

    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    data = r_health.json()
    assert data["status"] == "online"
    assert data["database"]["connected"] is True


def test_clinical_assessment_json():
    payload = {
        "patient_id": "PAT-TEST-01",
        "patient_name": "Test Subject",
        "vitals": {
            "age": 62,
            "sex": "Male",
            "arrival_mode": 2,
            "injury": 1,
            "chief_complaint": "Acute severe substernal chest pressure",
            "symptoms": "Nausea, sweating, left shoulder radiation",
            "mental": 1,
            "pain": 1,
            "nrs_pain": 8,
            "sbp": 90,
            "dbp": 60,
            "hr": 118,
            "rr": 24,
            "bt": 37.0,
            "saturation": 91
        }
    }
    res = client.post("/api/assessment/json", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "assessment_id" in data
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "priority" in data
    assert "shap_factors" in data
    shap_data = data["shap_factors"]
    if isinstance(shap_data, dict):
        assert "features" in shap_data
        assert len(shap_data["features"]) > 0
    else:
        assert len(shap_data) > 0
    assert data["modalities_used"]["count"] == 2


def test_metrics_endpoint():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "clinical_xgboost" in data["models"]
    assert "ecg_1dcnn" in data["models"]


def test_patient_timeline_lifecycle():
    # 1. Post initial assessment
    p_id = "PAT-LIFECYCLE-99"
    payload = {
        "patient_id": p_id,
        "patient_name": "Lifecycle Patient",
        "vitals": {
            "age": 45,
            "sex": "Female",
            "arrival_mode": 1,
            "injury": 1,
            "chief_complaint": "Mild abdominal cramping",
            "mental": 1,
            "pain": 1,
            "nrs_pain": 4,
            "sbp": 120,
            "dbp": 80,
            "hr": 76,
            "rr": 16,
            "bt": 36.8,
            "saturation": 98
        }
    }
    r1 = client.post("/api/assessment/json", json=payload)
    assert r1.status_code == 200

    # 2. Query timeline
    r2 = client.get(f"/api/timeline/{p_id}")
    assert r2.status_code == 200
    tl = r2.json()
    assert tl["patient_id"] == p_id
    assert len(tl["trajectory"]) >= 1
