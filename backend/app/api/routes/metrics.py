"""
Model Performance & Research Benchmarks API Route.
Loads real evaluation metrics and confusion matrices generated during offline training.
"""
from fastapi import APIRouter
import os
import json

router = APIRouter(prefix="/metrics", tags=["Model Research Benchmarks"])


@router.get("")
def get_all_model_metrics():
    """
    Returns verified evaluation metrics across all 3 trained models
    directly from reports/ JSON files. No fabricated metrics.
    """
    # Check root reports directory or backend reports
    root_reports = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reports"))
    backend_reports = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports"))
    base_reports = root_reports if os.path.exists(root_reports) else backend_reports
    
    def load_json(subpath):
        p = os.path.join(base_reports, subpath)
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    clinical = load_json("clinical/metrics.json")
    ecg = load_json("ecg/metrics.json")
    xray = load_json("xray/metrics.json")

    return {
        "status": "success",
        "models": {
            "clinical_xgboost": clinical,
            "ecg_1dcnn": ecg,
            "xray_densenet": xray
        }
    }
