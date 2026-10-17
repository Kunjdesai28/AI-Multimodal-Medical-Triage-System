"""
Comprehensive Multimodal Assessment API Routes.
Enforces strict multi-tenant database isolation.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional, Dict, Any
import json

from ...schemas.triage import AssessmentCreateRequest, TriageAssessmentResponse
from ...services.triage_service import TriageService
from ...database.repository import TriageRepository
from ..deps import TenantContext, get_tenant_context, get_tenant_context_optional

router = APIRouter(prefix="/assessment", tags=["Multimodal Assessment"])


@router.post("", response_model=Dict if False else None)
async def create_multimodal_assessment(
    patient_data: str = Form(..., description="JSON string of patient vitals and demographics"),
    ecg_file: Optional[UploadFile] = File(None, description="Optional ECG lead CSV signal"),
    xray_file: Optional[UploadFile] = File(None, description="Optional Chest X-ray image"),
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Creates a comprehensive multimodal emergency triage assessment.
    Accepts clinical vitals (required) and optional ECG/Chest X-ray files.
    Strictly isolated: patient record is saved solely inside this institution's database.
    """
    try:
        data_dict = json.loads(patient_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid patient_data JSON: {str(e)}")

    vitals = data_dict.get("vitals", data_dict)
    patient_id = data_dict.get("patient_id")
    if patient_id is not None and not str(patient_id).strip():
        patient_id = None
    patient_name = data_dict.get("patient_name", "Unknown Patient")
    
    # STRICT TENANT ISOLATION: Derive institution strictly from authenticated token
    institution_id = tenant.institution_id

    ecg_bytes = await ecg_file.read() if ecg_file else None
    xray_bytes = await xray_file.read() if xray_file else None

    try:
        triage_svc = TriageService.get_instance()
        result = triage_svc.assess_patient(
            patient_data=vitals,
            ecg_bytes=ecg_bytes,
            xray_bytes=xray_bytes,
            patient_id=patient_id,
            patient_name=patient_name,
            institution_id=institution_id,
            tenant_repo=tenant.repo
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.post("/json")
def create_json_assessment(
    request: AssessmentCreateRequest,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Pure JSON endpoint for assessing patients without file uploads.
    Saves strictly inside authenticated institution's tenant database.
    """
    try:
        req_pid = request.patient_id
        if req_pid is not None and not str(req_pid).strip():
            req_pid = None

        triage_svc = TriageService.get_instance()
        result = triage_svc.assess_patient(
            patient_data=request.vitals.model_dump(),
            ecg_bytes=None,
            xray_bytes=None,
            patient_id=req_pid,
            patient_name=request.patient_name,
            institution_id=tenant.institution_id,
            tenant_repo=tenant.repo
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.get("/next-patient-id")
def get_next_patient_id(
    tenant: TenantContext = Depends(get_tenant_context_optional)
):
    """
    Returns the next sequential Patient ID for the institution (e.g. PAT-01, PAT-02, ...).
    """
    next_id = tenant.repo.get_next_patient_id()
    return {"next_patient_id": next_id}


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Retrieves a previously stored assessment by ID from the tenant database."""
    record = tenant.repo.get_assessment_by_id(assessment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found in your institution database.")
    return record


@router.get("")
def list_assessments(
    limit: int = 50,
    institution_id: Optional[str] = None,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """
    Lists recent patient triage assessments strictly isolated to this institution's database.
    Ignores any client-supplied institution_id to guarantee absolute isolation.
    """
    return tenant.repo.list_assessments(limit=limit)


@router.delete("")
def clear_all_assessments(
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Wipes all assessments and resets the triage queue for THIS institution only."""
    result = tenant.repo.clear_all()
    return {
        "status": "success",
        "message": f"All patient assessments and trajectories have been cleared for {tenant.institution_name}.",
        "cleared": result
    }


@router.get("/database/info")
def get_database_status(
    tenant: TenantContext = Depends(get_tenant_context_optional)
):
    """Returns real-time status of MongoDB storage and patient record counts for the tenant."""
    return tenant.repo.get_database_info()
