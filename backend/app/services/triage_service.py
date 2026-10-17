"""
Core Multimodal Triage Orchestration Service.

Integrates the 3 trained models (XGBoost, 1D CNN, DenseNet) via the
Availability-Aware Multimodal Fusion Layer, coordinates dynamic longitudinal updates,
and persists patient assessments to the database.
"""
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from .clinical_service import ClinicalService
from .ecg_service import ECGService
from .xray_service import XRayService
from .clinical_context_builder import ClinicalContextBuilder
from .clinical_differential_service import ClinicalDifferentialService
from ..fusion.model import MultimodalFusionLayer
from ..database.repository import TriageRepository


class TriageService:
    _instance = None

    def __init__(self, model_dir: Optional[str] = None):
        self.clinical_service = ClinicalService(model_dir)
        self.ecg_service = ECGService(model_dir)
        self.xray_service = XRayService(model_dir)
        self.differential_service = ClinicalDifferentialService.get_instance()
        self.fusion_layer = MultimodalFusionLayer()
        self.repository = TriageRepository()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TriageService()
        return cls._instance

    def assess_patient(
        self,
        patient_data: Dict[str, Any],
        ecg_bytes: Optional[bytes] = None,
        xray_bytes: Optional[bytes] = None,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = "Unknown Patient",
        institution_id: Optional[str] = None,
        tenant_repo: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Runs the full multimodal triage assessment pipeline.
        Explicitly handles missing modalities without fabricating data.
        """
        if not patient_id or not str(patient_id).strip():
            if tenant_repo and hasattr(tenant_repo, "get_next_patient_id"):
                patient_id = tenant_repo.get_next_patient_id()
            else:
                from ..database.repository import TriageRepository
                active_repo = TriageRepository.for_institution(institution_id)
                patient_id = active_repo.get_next_patient_id()
        assessment_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"

        # 1. Clinical Model Inference (Mandatory Modality)
        clinical_output = self.clinical_service.predict_patient(patient_data)

        # 2. ECG Model Inference (Optional Modality)
        ecg_output = None
        if ecg_bytes is not None and len(ecg_bytes) > 0:
            try:
                ecg_output = self.ecg_service.process_file_bytes(ecg_bytes)
            except Exception as e:
                print(f"[TriageService] Warning: ECG processing failed ({e}). Proceeding without ECG.")
                ecg_output = None

        # 3. Chest X-ray Model Inference (Optional Modality)
        xray_output = None
        if xray_bytes is not None and len(xray_bytes) > 0:
            try:
                xray_output = self.xray_service.process_image_bytes(xray_bytes)
            except Exception as e:
                print(f"[TriageService] Warning: X-ray processing failed ({e}). Proceeding without X-ray.")
                xray_output = None

        # 4. Availability-Aware Multimodal Fusion
        modality_mask = {
            "clinical": True,
            "vitals": True,
            "ecg": ecg_output is not None,
            "xray": xray_output is not None
        }

        fusion_result = self.fusion_layer.fuse(
            clinical_output=clinical_output,
            ecg_output=ecg_output,
            xray_output=xray_output,
            mask=modality_mask
        )

        # 5. Build Unified Clinical Context & Generate Evidence-Grounded Differential
        clinical_context = ClinicalContextBuilder.build_context(
            patient_data=patient_data,
            clinical_indices=clinical_output.get("clinical_indices"),
            ecg_output=ecg_output,
            xray_output=xray_output
        )
        differential_report = self.differential_service.generate_differential(clinical_context)

        # Format evidence-grounded conditions with full backward compatibility
        if differential_report.status == "success" and differential_report.conditions:
            potential_conditions = [
                {
                    "condition": c.condition_name,
                    "condition_name": c.condition_name,
                    "clinical_category": c.clinical_category,
                    "concern_level": c.concern_level,
                    "reason_for_consideration": c.reason_for_consideration,
                    "supporting_evidence": c.supporting_evidence,
                    "contradictory_evidence": c.contradictory_evidence,
                    "missing_information": c.missing_information,
                    "urgent_exclusion": c.urgent_exclusion,
                    "evidence_sources": c.evidence_sources,
                    "description": c.reason_for_consideration,
                    "clinical_disclaimer": c.clinical_disclaimer
                }
                for c in differential_report.conditions
            ]
        else:
            # Fallback or unavailable: return empty conditions, never fabricate unrelated conditions
            potential_conditions = []

        # 6. Assemble Full Clinical Response
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "assessment_id": assessment_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "institution_id": institution_id or patient_data.get("institution_id") or "DEFAULT_HOSPITAL",
            "timestamp": now_str,
            "risk_score": fusion_result["risk_score"],
            "priority": fusion_result["priority"],
            "priority_label": fusion_result["priority_label"],
            "priority_level": fusion_result["priority_level"],
            "priority_color": fusion_result["priority_color"],
            "target_time": fusion_result["target_time"],
            "confidence": fusion_result["confidence"],
            "modalities_used": fusion_result["modalities_used"],
            "contributions": fusion_result["contributions"],
            "contributing_factors": fusion_result["contributing_factors"],
            "safety_overrides": fusion_result["safety_overrides"],
            "clinical_indices": clinical_output["clinical_indices"],
            "potential_conditions": potential_conditions,
            "clinical_differential": differential_report.model_dump(),
            "shap_factors": clinical_output["shap_summary"],
            "ecg_analysis": ecg_output,
            "xray_analysis": xray_output,
            "disclaimer": "This system is an AI-assisted research prototype intended to support triage decision-making. It is not a substitute for professional medical judgment, diagnosis, or treatment."
        }

        # 6. Save Assessment and update Patient Timeline in dedicated tenant database
        active_repo = tenant_repo or self.repository
        saved_record = active_repo.save_assessment(record)
        return saved_record

    def add_patient_observation(
        self,
        patient_id: str,
        vitals_dict: Dict[str, Any],
        ecg_bytes: Optional[bytes] = None,
        xray_bytes: Optional[bytes] = None,
        tenant_repo: Optional[Any] = None,
        institution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adds a new longitudinal observation point (T2, T3...) for an existing patient.
        Recalculates risk and dynamic delta trajectory strictly inside tenant database.
        """
        active_repo = tenant_repo or self.repository
        # Retrieve existing patient timeline if present
        existing_timeline = active_repo.get_patient_timeline(patient_id)
        patient_name = existing_timeline.get("patient_name", "Patient") if existing_timeline else "Patient"

        # Run fresh assessment
        new_assessment = self.assess_patient(
            patient_data=vitals_dict,
            ecg_bytes=ecg_bytes,
            xray_bytes=xray_bytes,
            patient_id=patient_id,
            patient_name=patient_name,
            institution_id=institution_id,
            tenant_repo=active_repo
        )
        return new_assessment

