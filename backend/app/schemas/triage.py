"""
Pydantic Schemas for Triage Assessment, Observations, and API Contracts.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PatientVitalsInput(BaseModel):
    # Demographics & Presentation
    age: int = Field(..., ge=0, le=125, description="Patient age in years (0 for newborns/infants)")
    sex: str = Field("Male", description="Patient biological sex ('Male' or 'Female')")
    arrival_mode: int = Field(3, ge=1, le=7, description="1: Walking, 2: 119 Ambulance, 3: Private car, 4: Other")
    injury: int = Field(1, ge=1, le=2, description="1: Non-trauma/Medical, 2: Trauma")
    chief_complaint: str = Field("Chest pain", description="Primary presenting complaint")
    symptoms: Optional[str] = Field("", description="Additional free-text symptoms described by patient")
    
    # Neurological & Pain
    mental: int = Field(1, ge=1, le=4, description="Mental Status: 1=Alert, 2=Verbal, 3=Pain, 4=Unresponsive")
    pain: int = Field(1, ge=0, le=1, description="Pain present: 1=Yes, 0=No")
    nrs_pain: int = Field(4, ge=0, le=10, description="Numerical Rating Scale pain score (0 to 10)")
    
    # Hemodynamic & Vital Signs (Universal Physiological Entry Limits)
    sbp: float = Field(120.0, ge=20.0, le=300.0, description="Systolic Blood Pressure (mmHg)")
    dbp: float = Field(80.0, ge=5.0, le=200.0, description="Diastolic Blood Pressure (mmHg)")
    hr: float = Field(75.0, ge=20.0, le=350.0, description="Heart Rate / Pulse (beats per minute)")
    rr: float = Field(18.0, ge=0.0, le=150.0, description="Respiratory Rate (breaths per minute)")
    bt: float = Field(36.8, ge=20.0, le=45.0, description="Body Temperature (degrees Celsius)")
    saturation: Optional[float] = Field(98.0, ge=10.0, le=100.0, description="Oxygen Saturation SpO2 (%)")


class AssessmentCreateRequest(BaseModel):
    patient_id: Optional[str] = Field(None, description="Optional existing patient ID")
    patient_name: Optional[str] = Field("Unknown Patient", description="Patient name / identifier")
    vitals: PatientVitalsInput
    notes: Optional[str] = ""


class AddObservationRequest(BaseModel):
    vitals: PatientVitalsInput
    timestamp: Optional[str] = None
    observation_notes: Optional[str] = None


class ModalityContribution(BaseModel):
    modality: str
    available: bool
    impact_score: float
    summary: str


class SHAPFactor(BaseModel):
    feature: str
    label: str
    shap_value: float
    magnitude: float
    direction: str
    impact: str
    value: Optional[float] = None
    formatted_value: Optional[str] = None
    unit: Optional[str] = None


class ConditionFinding(BaseModel):
    condition: str
    probability: float
    is_positive: bool


class ECGResultSchema(BaseModel):
    predicted_class: str
    abnormality_score: float
    is_abnormal: bool
    estimated_heart_rate: int
    qrs_duration_ms: float
    waveform: List[float]
    class_probabilities: Dict[str, float]
    anomalous_regions: List[Dict[str, Any]]


class XRayResultSchema(BaseModel):
    top_condition: str
    composite_abnormality_score: float
    is_abnormal: bool
    findings: Optional[List[ConditionFinding]] = None
    detected_findings: Optional[List[Dict[str, Any]]] = None
    modality: Optional[str] = None
    anatomical_region: Optional[str] = None
    emergency_severity: Optional[str] = None
    clinical_rationale: Optional[str] = None
    triage_recommendations: Optional[str] = None
    primary_findings: Optional[List[str]] = None
    ai_engine: Optional[str] = None
    original_image_b64: Optional[str] = None
    heatmap_b64: Optional[str] = None
    overlay_b64: Optional[str] = None
    disclaimer: str = "Model attention visualization — not a clinical diagnosis."


class TriageAssessmentResponse(BaseModel):
    assessment_id: str
    patient_id: str
    patient_name: str
    timestamp: str
    
    # Primary Outcome
    risk_score: float = Field(..., description="Calibrated risk percentage (0 to 100%)")
    priority: str = Field(..., description="CRITICAL, HIGH, MODERATE, LESS_URGENT, NON_URGENT")
    priority_label: str
    priority_level: int
    priority_color: str
    target_time: str
    confidence: float
    
    # Modality Breakdown
    modalities_used: Dict[str, Any]
    contributions: List[ModalityContribution]
    contributing_factors: List[str]
    safety_overrides: List[str]
    
    # Indices & Explainability
    clinical_indices: Dict[str, Any]
    potential_conditions: List[Dict[str, Any]]
    clinical_differential: Optional[Dict[str, Any]] = None
    shap_factors: List[SHAPFactor]
    ecg_analysis: Optional[ECGResultSchema] = None
    xray_analysis: Optional[XRayResultSchema] = None
    
    disclaimer: str


class TimelinePoint(BaseModel):
    observation_id: str
    timestamp: str
    vitals_summary: Dict[str, Any]
    risk_score: float
    priority: str
    priority_color: str
    delta_risk: Optional[float] = None
    delta_direction: Optional[str] = None
    modalities_count: int


class PatientTimelineResponse(BaseModel):
    patient_id: str
    patient_name: str
    total_observations: int
    trajectory: List[TimelinePoint]
    overall_trend: str  # "Deteriorating", "Stabilizing", "Improving"
    latest_risk: float
    latest_priority: str
