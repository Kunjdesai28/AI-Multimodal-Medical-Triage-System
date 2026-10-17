"""
Clinical Assessment Only API Route.
"""
from fastapi import APIRouter, HTTPException
from ...schemas.triage import PatientVitalsInput
from ...services.triage_service import TriageService

router = APIRouter(prefix="/clinical", tags=["Clinical Assessment"])


@router.post("")
def assess_clinical_only(vitals: PatientVitalsInput):
    """
    Evaluates patient risk strictly from clinical demographics, symptoms, and vital signs
    using the trained XGBoost model and TreeSHAP explainability.
    """
    try:
        triage_svc = TriageService.get_instance()
        result = triage_svc.assess_patient(
            patient_data=vitals.model_dump(),
            ecg_bytes=None,
            xray_bytes=None,
            patient_name=f"Patient ({vitals.chief_complaint})"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clinical assessment failed: {str(e)}")
