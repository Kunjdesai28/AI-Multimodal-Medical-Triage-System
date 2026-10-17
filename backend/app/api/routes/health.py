"""
Health Check and System Status API Route.
"""
from fastapi import APIRouter
from datetime import datetime
from ...services.triage_service import TriageService
from ...database.connection import DatabaseManager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    triage_svc = TriageService.get_instance()
    db_mgr = DatabaseManager.get_db()
    
    return {
        "status": "online",
        "service": "TRIAGEAI - AI-Based Multimodal Diagnostic Triage System",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "type": "MongoDB" if db_mgr.is_mongo else "Local Atomic JSON Storage",
            "connected": True,
            "database_name": db_mgr.db_name if db_mgr.is_mongo else "backend/data",
            "uri": db_mgr.mongo_uri if db_mgr.is_mongo else "local_file_system",
            "total_assessments": db_mgr.get_assessment_count(),
            "total_patients": db_mgr.get_patient_count()
        },
        "models": {
            "clinical_xgboost": triage_svc.clinical_service.is_ready,
            "ecg_1dcnn": triage_svc.ecg_service.is_ready,
            "xray_densenet": triage_svc.xray_service.is_ready,
            "multimodal_fusion": True
        }
    }
