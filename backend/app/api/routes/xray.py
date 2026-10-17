"""
Chest X-ray Abnormality Analysis API Route.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from ...services.triage_service import TriageService

router = APIRouter(prefix="/xray", tags=["Chest X-ray Analysis"])


@router.post("/analyze")
async def analyze_xray_image(file: UploadFile = File(...)):
    """
    Analyzes an uploaded chest radiograph using the DenseNet model.
    Detects acute thoracic findings (Pneumothorax, Edema, Effusion, Cardiomegaly, etc.)
    and returns a Grad-CAM attention heatmap overlay.
    """
    try:
        content = await file.read()
        triage_svc = TriageService.get_instance()
        result = triage_svc.xray_service.process_image_bytes(content)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Chest X-ray analysis failed: {str(e)}")
