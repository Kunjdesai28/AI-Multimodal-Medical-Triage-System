"""
Clinical Differential Schemas.

Defines evidence-grounded differential analysis data models
for emergency triage decision support.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator


class DifferentialCondition(BaseModel):
    condition_name: str = Field(..., description="Standard clinical disease/syndrome name")
    condition: Optional[str] = Field(None, description="Backward-compatible alias for condition_name")
    clinical_category: str = Field(..., description="Cardiovascular, Respiratory, Neurological, etc.")
    concern_level: Literal["Urgent Exclusion", "High Concern", "Consider", "Lower Concern"] = Field(
        ..., description="Qualitative clinical concern level (NOT a probability percentage)"
    )
    reason_for_consideration: str = Field(..., description="Pathophysiological/clinical rationale")
    supporting_evidence: List[str] = Field(
        default_factory=list, description="Patient symptoms, vitals, or modality findings directly supporting this"
    )
    contradictory_evidence: List[str] = Field(
        default_factory=list, description="Patient findings inconsistent with this condition"
    )
    missing_information: List[str] = Field(
        default_factory=list, description="Bedside examinations, labs, or imaging needed to confirm or rule out"
    )
    urgent_exclusion: bool = Field(
        default=False, description="True if condition is immediately life-threatening requiring urgent exclusion"
    )
    evidence_sources: List[str] = Field(
        default_factory=list,
        description="Sources providing evidence (e.g. Patient-reported symptoms, Recorded vital signs, ECG, etc.)"
    )
    description: Optional[str] = Field(None, description="Backward-compatible alias for reason_for_consideration")
    clinical_disclaimer: str = Field(
        default="AI-assisted clinical differential for triage consideration only; not a formal diagnosis."
    )

    @model_validator(mode="after")
    def populate_backward_compat_fields(self):
        if not self.condition:
            self.condition = self.condition_name
        if not self.description:
            self.description = self.reason_for_consideration
        return self


class ClinicalDifferentialReport(BaseModel):
    status: Literal["success", "unavailable", "fallback"] = Field(
        ..., description="Generation status of the differential report"
    )
    version: str = Field(default="1.0.0", description="Differential prompt and schema version")
    generated_at: str = Field(..., description="Timestamp of differential generation")
    clinical_summary: Optional[str] = Field(
        None, description="Concise clinical synthesis of the multimodal presentation"
    )
    urgent_action_required: bool = Field(
        default=False, description="True if life-threatening findings warrant immediate resuscitation/action"
    )
    conditions: List[DifferentialCondition] = Field(
        default_factory=list, description="Evidence-grounded differential conditions"
    )
    recommended_investigations: List[str] = Field(
        default_factory=list, description="Recommended bedside or emergent diagnostic investigations"
    )
    modalities_consulted: Dict[str, bool] = Field(
        default_factory=dict, description="Record of which modalities were available and consulted"
    )
    clinical_disclaimer: str = Field(
        default="AI-assisted clinical differential based on available assessment data. Not an authoritative diagnosis."
    )
    error_message: Optional[str] = Field(
        None, description="Detailed error explanation if status is unavailable"
    )
