"""
Dynamic Adaptive Triage and Patient Timeline API Routes.
Enforces strict multi-tenant database isolation.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import json

from ...schemas.triage import PatientVitalsInput
from ...services.triage_service import TriageService
from ...database.repository import TriageRepository
from ..deps import TenantContext, get_tenant_context

router = APIRouter(prefix="/timeline", tags=["Dynamic Adaptive Triage"])


@router.get("/{patient_id}")
def get_patient_timeline(
    patient_id: str,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Retrieves the longitudinal risk trajectory and observation history for a patient
    strictly from the authenticated institution's tenant database.
    """
    doc = tenant.repo.get_patient_timeline(patient_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Patient timeline not found in your institution database.")
        
    traj = doc.get("trajectory", [])
    latest_risk = traj[-1]["risk_score"] if traj else 0.0
    latest_priority = traj[-1]["priority"] if traj else "UNKNOWN"
    
    # Calculate overall clinical trend
    trend = "Stabilizing"
    if len(traj) >= 2:
        net_change = traj[-1]["risk_score"] - traj[0]["risk_score"]
        if net_change >= 10.0:
            trend = "Deteriorating"
        elif net_change <= -10.0:
            trend = "Improving"
        else:
            trend = "Stabilizing"

    return {
        "patient_id": patient_id,
        "patient_name": doc.get("patient_name", "Patient"),
        "total_observations": len(traj),
        "overall_trend": trend,
        "latest_risk": latest_risk,
        "latest_priority": latest_priority,
        "trajectory": traj
    }


@router.post("/{patient_id}/observation")
async def add_patient_observation(
    patient_id: str,
    patient_data: str = Form(..., description="JSON string of updated vitals"),
    ecg_file: Optional[UploadFile] = File(None),
    xray_file: Optional[UploadFile] = File(None),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Appends a new observation timestamp for an existing patient strictly inside
    the authenticated institution's database.
    Re-runs models, recalculates fused risk score, and computes delta changes.
    """
    try:
        data_dict = json.loads(patient_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    vitals = data_dict.get("vitals", data_dict)
    ecg_bytes = await ecg_file.read() if ecg_file else None
    xray_bytes = await xray_file.read() if xray_file else None

    try:
        triage_svc = TriageService.get_instance()
        assessment = triage_svc.add_patient_observation(
            patient_id=patient_id,
            vitals_dict=vitals,
            ecg_bytes=ecg_bytes,
            xray_bytes=xray_bytes,
            tenant_repo=tenant.repo,
            institution_id=tenant.institution_id
        )
        return assessment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Observation update failed: {str(e)}")
