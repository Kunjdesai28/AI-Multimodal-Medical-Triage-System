"""
ECG Rhythm Analysis API Route.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from ...services.triage_service import TriageService

router = APIRouter(prefix="/ecg", tags=["ECG Analysis"])


@router.post("/analyze")
async def analyze_ecg_file(file: UploadFile = File(...)):
    """
    Analyzes an uploaded ECG CSV lead signal file using the 1D CNN model.
    Returns detected rhythm, abnormality score, and waveform interpretation.
    """
    try:
        content = await file.read()
        triage_svc = TriageService.get_instance()
        result = triage_svc.ecg_service.process_file_bytes(content)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ECG analysis failed: {str(e)}")
