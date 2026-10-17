"""
Clinical Differential Service.

Integrates Google Gemini to generate evidence-grounded, multimodal clinical differentials
for emergency department decision support in Indian hospitals.

Safety & Governance Constraints:
- Output is strictly decision-support for triage; NOT an authoritative diagnosis.
- Qualitative concern levels only; NEVER fabricates numerical probability percentages.
- Every condition requires supporting patient evidence; strictly excludes unrelated diagnoses.
- De-identified input; preserves patient privacy (DPDP Act alignment).
- Safe failure handling: returns explicit unavailable message without hallucinated conditions.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import httpx
from pydantic import ValidationError

from ..schemas.differential import ClinicalDifferentialReport, DifferentialCondition
from .clinical_context_builder import ClinicalContextBuilder


class ClinicalDifferentialService:
    _instance = None

    PROMPT_VERSION = "2.1.0"

    CANDIDATE_MODELS = [
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-2.5-flash"
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self.working_model = "gemini-3.1-flash-lite"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClinicalDifferentialService()
        return cls._instance

    def _load_api_key(self) -> str:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GEMINI_API_KEY="):
                            key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                            break
        return key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """
        Constructs a structured, versioned prompt for Gemini containing de-identified clinical context.
        """
        demographics = context.get("demographics", {})
        complaint = context.get("presenting_complaint", {})
        vitals = context.get("vital_signs", {})
        hemodynamics = context.get("calculated_hemodynamics", {})
        ecg = context.get("ecg_findings", {})
        imaging = context.get("imaging_findings", {})

        prompt = f"""
You are an expert Emergency Medicine Clinical Decision Support AI for acute hospital triage in India.
Your role is to assist emergency physicians and triage officers by analyzing complete multimodal patient presentations and generating an evidence-grounded clinical differential.

PATIENT CLINICAL CONTEXT (STRICTLY DE-IDENTIFIED):
1. Demographics & Encounter:
   - Age: {demographics.get('age', 'Unknown')}
   - Sex: {demographics.get('sex', 'Unknown')}
   - Arrival Mode: {demographics.get('arrival_mode', 'Unknown')}
   - Encounter Classification: {demographics.get('injury_classification', 'Unknown')}
   - Relevant History: {demographics.get('relevant_history', 'None documented')}

2. Presenting Complaint & Symptoms:
   - Chief Complaint: {complaint.get('chief_complaint', 'None stated')}
   - Associated Symptoms: {complaint.get('associated_symptoms', 'None documented')}
   - Pain Severity: {complaint.get('pain_severity_nrs', 'Not assessed')}
   - Mental Status: {complaint.get('mental_status', 'Unknown')}

3. Vital Signs:
   - Systolic Blood Pressure: {vitals.get('systolic_bp_mmHg', 'Not measured')} mmHg
   - Diastolic Blood Pressure: {vitals.get('diastolic_bp_mmHg', 'Not measured')} mmHg
   - Heart Rate: {vitals.get('heart_rate_bpm', 'Not measured')} bpm
   - Respiratory Rate: {vitals.get('respiratory_rate_per_min', 'Not measured')} /min
   - Body Temperature: {vitals.get('body_temperature_c', 'Not measured')} °C
   - Oxygen Saturation (SpO2): {vitals.get('oxygen_saturation_spo2', 'Not measured')} %

4. Calculated Hemodynamics:
   - Shock Index (HR / SBP): {hemodynamics.get('shock_index', 'Not calculated')} (Normal: 0.5-0.7; >0.9 indicates acute occult hypoperfusion/shock)
   - Mean Arterial Pressure (MAP): {hemodynamics.get('map', 'Not calculated')} mmHg
   - Pulse Pressure (SBP - DBP): {hemodynamics.get('pulse_pressure', 'Not calculated')} mmHg

5. Diagnostic Modalities:
   - ECG Assessment: {ecg.get('status', 'Unavailable')} | Findings: {ecg.get('rhythm_classification', 'None')} | Limitations: {ecg.get('limitations', 'N/A')}
   - Medical Imaging Assessment: {imaging.get('status', 'Unavailable')} | Modality: {imaging.get('modality', 'None')} | Region: {imaging.get('anatomical_region', 'None')} | Findings: {imaging.get('primary_findings', [])} | Limitations: {imaging.get('limitations', 'N/A')}

CRITICAL CLINICAL REASONING MANDATES:
1. Synthesize as a Unified Emergency Case: Integrate demographics, symptoms, vitals, hemodynamics, and modality findings.
2. Evidence Grounding: Every proposed condition MUST have direct supporting evidence from the provided patient presentation. Strictly DO NOT hallucinate symptoms, lab values, or findings that were not provided.
3. Prioritize Potentially Life-Threatening Conditions: Immediately highlight conditions requiring urgent clinical exclusion (e.g. Acute Coronary Syndrome / Acute Myocardial Infarction, Cardiogenic Shock, Pulmonary Embolism, Tension Pneumothorax, Aortic Dissection, Sepsis, Acute Heart Failure).
4. Strictly Avoid Unrelated Diagnoses: NEVER list unrelated conditions (such as Chickenpox, Dengue, Typhoid, Malaria, Common Cold) unless the patient exhibits specific, documented clinical evidence for them (e.g., vesicular rash for chickenpox, thrombocytopenia/petechiae for dengue).
5. Recognize Diagnostic Spectra: Acute Myocardial Infarction (STEMI/NSTEMI) and Unstable Angina are part of the ACS spectrum rather than unrelated diseases.
6. Acknowledge Diagnostic Modality Status:
   - If ECG is unavailable, explicitly state that ST-elevation or acute ischemia cannot be ruled out. If ECG is a single-lead arrhythmia classifier, state it only assesses rhythm.
   - If imaging is unavailable, explicitly state that thoracic/cranial pathology has not been radiologically excluded.
7. Qualitative Concern Levels Only: NEVER output numerical diagnostic probabilities, match percentages, or confidence numbers (DO NOT invent 40%, 80%, 95%, 99%).
   Use permitted qualitative concern levels:
   - "Urgent Exclusion": Life-threatening condition requiring immediate clinical rule-out.
   - "High Concern": Strongly supported by clinical presentation.
   - "Consider": Plausible differential to investigate.
   - "Lower Concern": Less likely, but clinically relevant.
8. Clinical Differentiators: Suggest specific bedside exams, lab tests, or imaging to differentiate possibilities.
9. Disclaimer: This is decision-support for triage consideration only; not a confirmed diagnosis.

RETURN STRICT JSON ONLY MATCHING THIS SCHEMA:
{{
  "clinical_summary": "1-2 sentence concise clinical synthesis of this acute presentation",
  "urgent_action_required": true or false,
  "conditions": [
    {{
      "condition_name": "Standard medical condition name",
      "clinical_category": "Cardiovascular" | "Respiratory" | "Neurological" | "Infectious" | "Gastrointestinal" | "Trauma" | "Metabolic" | "Other",
      "concern_level": "Urgent Exclusion" | "High Concern" | "Consider" | "Lower Concern",
      "reason_for_consideration": "Clinical reasoning linking patient presentation to this condition",
      "supporting_evidence": ["Direct patient findings supporting this condition"],
      "contradictory_evidence": ["Patient findings arguing against this condition, or empty list"],
      "missing_information": ["Essential diagnostic tests or exams needed to confirm or exclude"],
      "urgent_exclusion": true or false,
      "evidence_sources": ["Patient-reported symptoms" | "Recorded vital signs" | "Calculated hemodynamics" | "ECG analysis" | "Medical imaging analysis" | "Clinical observations"]
    }}
  ],
  "recommended_investigations": [
    "Recommended bedside test or laboratory investigation"
  ]
}}
"""
        return prompt

    def generate_differential(
        self,
        context: Dict[str, Any],
        mock_response: Optional[Dict[str, Any]] = None
    ) -> ClinicalDifferentialReport:
        """
        Generates an evidence-grounded differential analysis from clinical context.
        Supports mock_response for isolated deterministic automated tests.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modalities_consulted = {
            "symptoms": bool(context.get("presenting_complaint", {}).get("chief_complaint")),
            "vitals": bool(context.get("vital_signs", {}).get("systolic_bp_mmHg")),
            "hemodynamics": bool(context.get("calculated_hemodynamics", {}).get("shock_index")),
            "ecg": bool(context.get("ecg_findings", {}).get("available")),
            "imaging": bool(context.get("imaging_findings", {}).get("available"))
        }

        # 1. Handle mock injection for deterministic testing
        if mock_response is not None:
            return self._parse_and_validate(mock_response, now_str, modalities_consulted)

        # 2. Check configuration
        if not self.is_configured:
            return ClinicalDifferentialReport(
                status="unavailable",
                version=self.PROMPT_VERSION,
                generated_at=now_str,
                modalities_consulted=modalities_consulted,
                error_message="Clinical differential currently unavailable. Emergency triage assessment remains available.",
                conditions=[]
            )

        # 3. Build structured prompt
        prompt = self._build_prompt(context)

        # 4. Invoke Gemini with candidate model fallbacks and bounded timeouts
        ordered_models = [self.working_model] + [m for m in self.CANDIDATE_MODELS if m != self.working_model]
        last_error = None

        for model_name in ordered_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            }

            try:
                resp = httpx.post(url, json=payload, timeout=18.0)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw_text)
                    self.working_model = model_name
                    report = self._parse_and_validate(parsed, now_str, modalities_consulted)
                    if report.status == "success":
                        return report
                elif resp.status_code in [429, 503]:
                    last_error = f"Model {model_name} rate limit / capacity (HTTP {resp.status_code})"
                    continue
                else:
                    last_error = f"Model {model_name} HTTP {resp.status_code}: {resp.text[:120]}"
            except Exception as e:
                last_error = f"Exception calling {model_name}: {str(e)}"
                continue

        # 5. Graceful failure handling
        return ClinicalDifferentialReport(
            status="unavailable",
            version=self.PROMPT_VERSION,
            generated_at=now_str,
            modalities_consulted=modalities_consulted,
            error_message="Clinical differential currently unavailable. Emergency triage assessment remains available.",
            conditions=[]
        )

    def _parse_and_validate(
        self,
        raw_dict: Dict[str, Any],
        generated_at: str,
        modalities_consulted: Dict[str, bool]
    ) -> ClinicalDifferentialReport:
        """
        Validates raw dictionary into a strictly typed ClinicalDifferentialReport.
        Rejects malformed structures.
        """
        try:
            raw_conditions = raw_dict.get("conditions", [])
            valid_conditions = []

            for cond in raw_conditions:
                if not isinstance(cond, dict) or not cond.get("condition_name"):
                    continue

                # Ensure concern level is valid
                concern = cond.get("concern_level", "Consider")
                if concern not in ["Urgent Exclusion", "High Concern", "Consider", "Lower Concern"]:
                    concern = "High Concern" if cond.get("urgent_exclusion") else "Consider"

                # Sanitize supporting evidence
                supp = cond.get("supporting_evidence", [])
                if isinstance(supp, str):
                    supp = [supp]

                contra = cond.get("contradictory_evidence", [])
                if isinstance(contra, str):
                    contra = [contra]

                missing = cond.get("missing_information", [])
                if isinstance(missing, str):
                    missing = [missing]

                sources = cond.get("evidence_sources", [])
                if isinstance(sources, str):
                    sources = [sources]

                dc = DifferentialCondition(
                    condition_name=str(cond["condition_name"]).strip(),
                    condition=str(cond.get("condition") or cond["condition_name"]).strip(),
                    clinical_category=str(cond.get("clinical_category", "General Medical")).strip(),
                    concern_level=concern,
                    reason_for_consideration=str(cond.get("reason_for_consideration", "")).strip(),
                    supporting_evidence=[str(s).strip() for s in supp if s],
                    contradictory_evidence=[str(c).strip() for c in contra if c],
                    missing_information=[str(m).strip() for m in missing if m],
                    urgent_exclusion=bool(cond.get("urgent_exclusion", concern == "Urgent Exclusion")),
                    evidence_sources=[str(src).strip() for src in sources if src],
                    description=str(cond.get("reason_for_consideration", "")).strip()
                )
                valid_conditions.append(dc)

            return ClinicalDifferentialReport(
                status="success" if valid_conditions else "unavailable",
                version=self.PROMPT_VERSION,
                generated_at=generated_at,
                clinical_summary=raw_dict.get("clinical_summary"),
                urgent_action_required=bool(raw_dict.get("urgent_action_required", False)),
                conditions=valid_conditions,
                recommended_investigations=raw_dict.get("recommended_investigations", []),
                modalities_consulted=modalities_consulted
            )
        except Exception as e:
            return ClinicalDifferentialReport(
                status="unavailable",
                version=self.PROMPT_VERSION,
                generated_at=generated_at,
                modalities_consulted=modalities_consulted,
                error_message="Clinical differential currently unavailable. Emergency triage assessment remains available.",
                conditions=[]
            )
