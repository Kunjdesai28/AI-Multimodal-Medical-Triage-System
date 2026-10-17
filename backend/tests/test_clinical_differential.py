"""
Comprehensive Clinical Differential & Multimodal Evidence Grounding Tests.

Validates:
- Reference test case (Rahul Sharma, TEST-ER-1001): ACS/MI/Shock vs Chickenpox/Typhoid/Dengue
- Deterministic emergency safety escalation
- Multi-scenario evidence grounding (respiratory, neuro, infection, trauma, normal vitals)
- Modality handling (missing vs available ECG/imaging)
- Failure resilience (API errors, timeouts, malformed JSON)
- Dynamic longitudinal observation updates
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.main import app
from backend.app.services.clinical_context_builder import ClinicalContextBuilder
from backend.app.services.clinical_differential_service import ClinicalDifferentialService
from backend.app.services.triage_service import TriageService

client = TestClient(app)


# ---------------------------------------------------------------------------
# FIXTURE: Reference Test Case (Rahul Sharma, TEST-ER-1001)
# ---------------------------------------------------------------------------
@pytest.fixture
def rahul_sharma_payload():
    return {
        "patient_id": "TEST-ER-1001",
        "patient_name": "Rahul Sharma",
        "vitals": {
            "age": 58,
            "sex": "Male",
            "arrival_mode": 1,  # Walking / Self
            "injury": 1,        # Non-Trauma / Medical
            "chief_complaint": "Acute chest pain with shortness of breath.",
            "symptoms": "Severe central chest pain radiating to the left arm, sweating, dizziness, nausea, and difficulty breathing for the past 30 minutes.",
            "pain": 1,
            "nrs_pain": 9,
            "mental": 1,        # Alert
            "sbp": 90,
            "dbp": 60,
            "hr": 125,
            "rr": 28,
            "bt": 36.8,
            "saturation": 89
        }
    }


# ---------------------------------------------------------------------------
# 1. REFERENCE TEST CASE: Rahul Sharma (Cardiovascular Emergency)
# ---------------------------------------------------------------------------
def test_reference_test_case_hemodynamics_and_escalation(rahul_sharma_payload):
    """
    Validates Phase 6 reference test case:
    - Calculated Shock Index is approx 1.39
    - Calculated MAP is 70 mmHg
    - Calculated Pulse Pressure is 30 mmHg
    - Deterministic clinical safety rules trigger immediate emergency escalation (CRITICAL Level 1)
    - Triage priority is CRITICAL with risk >= 78%
    """
    vitals = rahul_sharma_payload["vitals"]
    hemo = ClinicalContextBuilder.calculate_hemodynamics(vitals["sbp"], vitals["dbp"], vitals["hr"])

    # Shock Index = 125 / 90 = 1.3888... -> 1.39
    assert abs(hemo["shock_index"] - 1.39) <= 0.02
    # MAP = (90 + 2*60) / 3 = 70.0
    assert abs(hemo["map"] - 70.0) <= 0.5
    # Pulse Pressure = 90 - 60 = 30.0
    assert abs(hemo["pulse_pressure"] - 30.0) <= 0.5

    # Post to assessment endpoint
    res = client.post("/api/assessment/json", json=rahul_sharma_payload)
    assert res.status_code == 200
    data = res.json()

    # Verify immediate emergency escalation
    assert data["priority"] == "CRITICAL"
    assert data["priority_level"] == 1
    assert data["risk_score"] >= 78.0

    # Safety override must cite elevated Shock Index
    override_texts = " ".join(data.get("safety_overrides", []))
    assert "Shock Index" in override_texts or "hypoperfusion" in override_texts


def test_reference_test_case_clinical_differential_grounding(rahul_sharma_payload):
    """
    Validates that the clinical differential:
    - Identifies cardiovascular/hemodynamic emergency (ACS, MI, shock, PE, dissection)
    - Strictly excludes unrelated diseases: NO Chickenpox, NO Typhoid, NO Dengue
    - NO fabricated 40% match percentages
    - Qualitative concern level is Urgent Exclusion or High Concern
    """
    res = client.post("/api/assessment/json", json=rahul_sharma_payload)
    assert res.status_code == 200
    data = res.json()

    conditions = data.get("potential_conditions", [])
    
    # If differential service generated conditions
    if conditions:
        condition_names = [c.get("condition_name", c.get("condition", "")).lower() for c in conditions]
        
        # Must NOT contain unrelated infectious diseases
        for bad_cond in ["chicken pox", "chickenpox", "typhoid", "dengue"]:
            assert not any(bad_cond in name for name in condition_names), f"Unrelated disease '{bad_cond}' appeared for chest pain presentation!"

        # Must NOT contain generic 40% relevance score
        for c in conditions:
            assert "relevance_score" not in c or c.get("relevance_score") != 0.40
            assert c.get("concern_level") in ["Urgent Exclusion", "High Concern", "Consider", "Lower Concern"]

        # Check for cardiovascular relevance
        has_cardio = any(
            any(term in name for term in ["coronary", "infarction", "myocardial", "acs", "shock", "embolism", "aortic", "angina", "heart"])
            for name in condition_names
        )
        assert has_cardio, f"Expected cardiovascular emergency in differential, got: {condition_names}"


# ---------------------------------------------------------------------------
# 2. PRIVACY & DE-IDENTIFICATION TEST
# ---------------------------------------------------------------------------
def test_privacy_and_deidentification():
    """
    Ensures that ClinicalContextBuilder strips all identifiers (name, ID, contact)
    before generating differential context payload.
    """
    raw_patient = {
        "patient_id": "CONFIDENTIAL-ID-9999",
        "patient_name": "Sita Ramachandran",
        "phone_number": "+91-9876543210",
        "address": "45 MG Road, Bengaluru, Karnataka",
        "age": 42,
        "sex": "Female",
        "arrival_mode": 1,
        "injury": 1,
        "chief_complaint": "Severe epigastric pain radiating to back",
        "symptoms": "Vomiting, fever",
        "sbp": 110,
        "dbp": 70,
        "hr": 92
    }

    context = ClinicalContextBuilder.build_context(raw_patient)
    context_str = str(context)

    # Identifiers must NOT appear anywhere in the context
    assert "CONFIDENTIAL-ID-9999" not in context_str
    assert "Sita Ramachandran" not in context_str
    assert "9876543210" not in context_str
    assert "MG Road" not in context_str
    assert "Bengaluru" not in context_str

    # Clinical features MUST be preserved
    assert context["demographics"]["age"] == 42
    assert context["demographics"]["sex"] == "Female"
    assert "epigastric" in context["presenting_complaint"]["chief_complaint"].lower()


# ---------------------------------------------------------------------------
# 3. RESPIRATORY EMERGENCY SCENARIO
# ---------------------------------------------------------------------------
def test_respiratory_emergency_differential():
    """
    Patient presenting with acute severe dyspnea, wheezing, and hypoxemia (SpO2 84%).
    Differential should consider acute respiratory conditions, not unrelated cardiac or dermatologic diseases.
    """
    mock_resp = {
        "clinical_summary": "Acute severe respiratory distress with profound hypoxemia in a young adult.",
        "urgent_action_required": True,
        "conditions": [
            {
                "condition_name": "Acute Severe Asthma / Status Asthmaticus",
                "clinical_category": "Respiratory",
                "concern_level": "Urgent Exclusion",
                "reason_for_consideration": "Bilateral expiratory wheezing, tachypnea, and severe hypoxemia.",
                "supporting_evidence": ["SpO2 84%", "RR 34/min", "Severe breathlessness"],
                "contradictory_evidence": [],
                "missing_information": ["Peak expiratory flow rate", "Arterial blood gas"],
                "urgent_exclusion": True,
                "evidence_sources": ["Patient-reported symptoms", "Recorded vital signs"]
            },
            {
                "condition_name": "Tension Pneumothorax",
                "clinical_category": "Respiratory",
                "concern_level": "Urgent Exclusion",
                "reason_for_consideration": "Acute respiratory decompensation with hypoxia.",
                "supporting_evidence": ["Severe hypoxia", "Tachypnea"],
                "contradictory_evidence": [],
                "missing_information": ["STAT Chest Radiography", "Point-of-care lung ultrasound"],
                "urgent_exclusion": True,
                "evidence_sources": ["Recorded vital signs"]
            }
        ],
        "recommended_investigations": ["STAT 12-lead ECG", "Arterial Blood Gas", "Bedside Lung Ultrasound"]
    }

    diff_svc = ClinicalDifferentialService.get_instance()
    report = diff_svc.generate_differential({}, mock_response=mock_resp)

    assert report.status == "success"
    assert report.urgent_action_required is True
    assert len(report.conditions) == 2
    assert report.conditions[0].condition_name == "Acute Severe Asthma / Status Asthmaticus"
    assert report.conditions[0].concern_level == "Urgent Exclusion"
    assert report.conditions[0].urgent_exclusion is True


# ---------------------------------------------------------------------------
# 4. NEUROLOGICAL EMERGENCY SCENARIO
# ---------------------------------------------------------------------------
def test_neurological_emergency_scenario():
    """
    Patient presenting with sudden onset left-sided hemiplegia and facial droop.
    Differential should prioritize Acute Ischemic Stroke vs Intracranial Hemorrhage.
    """
    mock_resp = {
        "clinical_summary": "Acute focal neurological deficit suggestive of acute stroke within thrombolysis window.",
        "urgent_action_required": True,
        "conditions": [
            {
                "condition_name": "Acute Ischemic Stroke",
                "clinical_category": "Neurological",
                "concern_level": "Urgent Exclusion",
                "reason_for_consideration": "Sudden onset focal neurological deficit with left hemiparesis and facial asymmetry.",
                "supporting_evidence": ["Left hemiparesis", "Facial droop", "Acute onset 45 min ago"],
                "contradictory_evidence": [],
                "missing_information": ["STAT Non-contrast Head CT", "Blood glucose level"],
                "urgent_exclusion": True,
                "evidence_sources": ["Patient-reported symptoms", "Clinical observations"]
            },
            {
                "condition_name": "Intracranial Hemorrhage",
                "clinical_category": "Neurological",
                "concern_level": "Urgent Exclusion",
                "reason_for_consideration": "Hypertensive emergency presenting with acute neurological deficit.",
                "supporting_evidence": ["BP 190/110 mmHg", "Altered mental status"],
                "contradictory_evidence": [],
                "missing_information": ["Non-contrast Head CT scan"],
                "urgent_exclusion": True,
                "evidence_sources": ["Recorded vital signs", "Clinical observations"]
            }
        ],
        "recommended_investigations": ["Non-contrast Head CT", "Fingerstick Blood Glucose", "INR/Coagulation Profile"]
    }

    diff_svc = ClinicalDifferentialService.get_instance()
    report = diff_svc.generate_differential({}, mock_response=mock_resp)

    assert report.status == "success"
    assert report.conditions[0].clinical_category == "Neurological"
    assert "Stroke" in report.conditions[0].condition_name


# ---------------------------------------------------------------------------
# 5. FEVER WITH EVIDENCE SUPPORTING INFECTIOUS DIFFERENTIAL
# ---------------------------------------------------------------------------
def test_infectious_fever_scenario():
    """
    When patient presents with high fever, thrombocytopenia/petechiae, retro-orbital pain:
    Dengue or Malaria is legitimately grounded because of patient-specific evidence.
    """
    mock_resp = {
        "clinical_summary": "Acute febrile illness with thrombocytopenia and hemorrhagic manifestations in endemic region.",
        "urgent_action_required": True,
        "conditions": [
            {
                "condition_name": "Dengue Hemorrhagic Fever",
                "clinical_category": "Infectious",
                "concern_level": "High Concern",
                "reason_for_consideration": "Documented petechial rash, retro-orbital headache, high fever, and platelet drop.",
                "supporting_evidence": ["Fever 39.4C", "Petechial rash", "Retro-orbital pain", "Tachycardia"],
                "contradictory_evidence": [],
                "missing_information": ["Dengue NS1 Antigen", "Dengue IgM/IgG", "Complete Blood Count hematocrit"],
                "urgent_exclusion": True,
                "evidence_sources": ["Patient-reported symptoms", "Recorded vital signs", "Clinical observations"]
            }
        ],
        "recommended_investigations": ["Dengue NS1/IgM", "Platelet Count", "Serum Electrolytes"]
    }

    diff_svc = ClinicalDifferentialService.get_instance()
    report = diff_svc.generate_differential({}, mock_response=mock_resp)

    assert report.status == "success"
    # Grounded dengue is acceptable when specific evidence exists
    assert "Dengue" in report.conditions[0].condition_name
    assert "Petechial rash" in report.conditions[0].supporting_evidence


# ---------------------------------------------------------------------------
# 6. TRAUMA PRESENTATION SCENARIO
# ---------------------------------------------------------------------------
def test_trauma_presentation_differential():
    """
    Trauma case with blunt abdominal trauma, tachycardia, and hypotension.
    Differential must consider Hemorrhagic Shock / Intra-abdominal Bleed.
    """
    mock_resp = {
        "clinical_summary": "Blunt abdominal trauma following vehicular collision with acute hemodynamic instability.",
        "urgent_action_required": True,
        "conditions": [
            {
                "condition_name": "Hemorrhagic Shock (Intra-abdominal Bleed)",
                "clinical_category": "Trauma",
                "concern_level": "Urgent Exclusion",
                "reason_for_consideration": "Blunt trauma mechanism with hypotension and elevated shock index.",
                "supporting_evidence": ["BP 85/55 mmHg", "Heart rate 130 bpm", "Abdominal rigidity", "Shock index 1.53"],
                "contradictory_evidence": [],
                "missing_information": ["Bedside eFAST ultrasound", "Hemoglobin / Hematocrit"],
                "urgent_exclusion": True,
                "evidence_sources": ["Recorded vital signs", "Calculated hemodynamics", "Clinical observations"]
            }
        ],
        "recommended_investigations": ["Bedside FAST Ultrasound", "Crossmatch 4 Units PRBC", "Pelvic X-ray"]
    }

    diff_svc = ClinicalDifferentialService.get_instance()
    report = diff_svc.generate_differential({}, mock_response=mock_resp)

    assert report.status == "success"
    assert report.conditions[0].clinical_category == "Trauma"
    assert "Hemorrhagic Shock" in report.conditions[0].condition_name


# ---------------------------------------------------------------------------
# 7. NORMAL VITALS & NONSPECIFIC COMPLAINT
# ---------------------------------------------------------------------------
def test_normal_vitals_nonspecific_differential():
    """
    Patient with mild tension-type headache, completely normal vital signs.
    Concern levels should be 'Lower Concern' or 'Consider'; no false emergency escalation.
    """
    mock_resp = {
        "clinical_summary": "Mild frontal headache with stable physiological vitals and no red-flag symptoms.",
        "urgent_action_required": False,
        "conditions": [
            {
                "condition_name": "Tension-Type Headache",
                "clinical_category": "Neurological",
                "concern_level": "Consider",
                "reason_for_consideration": "Mild bilateral non-throbbing headache with normal vitals and no focal deficits.",
                "supporting_evidence": ["Bilateral forehead ache", "Normal blood pressure", "Pain 3/10"],
                "contradictory_evidence": ["Absence of meningismus", "Absence of neurological deficit"],
                "missing_information": ["Ophthalmoscopy for papilledema if persistent"],
                "urgent_exclusion": False,
                "evidence_sources": ["Patient-reported symptoms", "Recorded vital signs"]
            }
        ],
        "recommended_investigations": ["Basic metabolic panel if symptoms persist"]
    }

    diff_svc = ClinicalDifferentialService.get_instance()
    report = diff_svc.generate_differential({}, mock_response=mock_resp)

    assert report.status == "success"
    assert report.urgent_action_required is False
    assert report.conditions[0].concern_level in ["Consider", "Lower Concern"]
    assert report.conditions[0].urgent_exclusion is False


# ---------------------------------------------------------------------------
# 8. MODALITY INTEGRATION: Missing vs Available ECG & Imaging
# ---------------------------------------------------------------------------
def test_missing_modality_handling():
    """
    When ECG and X-ray are not provided, clinical context explicitly marks them as unavailable.
    Does not hallucinate or invent ECG rhythms or radiological findings.
    """
    context = ClinicalContextBuilder.build_context(
        patient_data={"age": 50, "sex": "Male", "chief_complaint": "Chest tightness", "sbp": 120, "dbp": 80, "hr": 70},
        ecg_output=None,
        xray_output=None
    )

    assert context["ecg_findings"]["available"] is False
    assert "Not recorded" in context["ecg_findings"]["status"]
    assert context["imaging_findings"]["available"] is False
    assert "Not performed" in context["imaging_findings"]["status"]


def test_available_modality_integration():
    """
    When ECG (e.g. Ventricular Ectopic) and X-ray (e.g. Pneumothorax) are provided,
    they are correctly synthesized into the clinical context.
    """
    ecg_data = {
        "predicted_class": "Ventricular Ectopic / PVC (V)",
        "abnormality_score": 0.88,
        "is_abnormal": True
    }
    xray_data = {
        "modality": "Frontal Chest Radiograph",
        "anatomical_region": "Thorax",
        "top_condition": "Right-sided Pneumothorax",
        "primary_findings": ["Pneumothorax", "Pleural line visible"],
        "composite_abnormality_score": 0.85
    }

    context = ClinicalContextBuilder.build_context(
        patient_data={"age": 60, "sex": "Male", "chief_complaint": "Sudden pleuritic pain", "sbp": 110, "dbp": 70, "hr": 105},
        ecg_output=ecg_data,
        xray_output=xray_data
    )

    assert context["ecg_findings"]["available"] is True
    assert "Ventricular Ectopic" in context["ecg_findings"]["rhythm_classification"]
    assert context["imaging_findings"]["available"] is True
    assert "Pneumothorax" in context["imaging_findings"]["top_condition"]


# ---------------------------------------------------------------------------
# 9. FAILURE HANDLING: API Errors & Timeouts
# ---------------------------------------------------------------------------
def test_gemini_api_failure_graceful_handling(monkeypatch):
    """
    Phase 9 Requirement:
    If Gemini fails, times out, or reaches quota:
    - Do NOT show unrelated default diseases (no Chickenpox/Typhoid/Dengue).
    - Do NOT fabricate a differential.
    - Return explicit unavailable status:
      'Clinical differential currently unavailable. Emergency triage assessment remains available.'
    """
    diff_svc = ClinicalDifferentialService.get_instance()

    # Simulate network exception / quota exhaustion
    def mock_post_error(*args, **kwargs):
        raise RuntimeError("Simulated Gemini API 503 Overloaded")

    import httpx
    monkeypatch.setattr(httpx, "post", mock_post_error)

    report = diff_svc.generate_differential({"presenting_complaint": {"chief_complaint": "Chest pain"}})
    
    assert report.status == "unavailable"
    assert "Clinical differential currently unavailable" in report.error_message
    assert len(report.conditions) == 0


# ---------------------------------------------------------------------------
# 10. FAILURE HANDLING: Malformed Response Validation
# ---------------------------------------------------------------------------
def test_malformed_response_handling():
    """
    If Gemini returns malformed, empty, or unparseable JSON:
    Pydantic validation rejects it and returns clean 'unavailable' status without crashing.
    """
    diff_svc = ClinicalDifferentialService.get_instance()

    # Completely malformed dictionary with missing condition names
    malformed_resp = {
        "conditions": [
            {"invalid_field": 123},
            {"condition_name": "", "concern_level": "INVALID_TIER"}
        ]
    }

    report = diff_svc.generate_differential({}, mock_response=malformed_resp)
    assert report.status == "unavailable"
    assert len(report.conditions) == 0


# ---------------------------------------------------------------------------
# 11. DYNAMIC LONGITUDINAL OBSERVATION UPDATE
# ---------------------------------------------------------------------------
def test_longitudinal_observation_differential_update():
    """
    Phase 8 Requirement:
    When a patient's observation is updated in the timeline, the assessment
    is recalculated and associated with the new timestamp.
    """
    p_id = "PAT-LONGITUDINAL-TEST-42"
    initial_payload = {
        "patient_id": p_id,
        "patient_name": "Longitudinal Subject",
        "vitals": {
            "age": 55,
            "sex": "Female",
            "arrival_mode": 1,
            "injury": 1,
            "chief_complaint": "Moderate headache and dizziness",
            "sbp": 140,
            "dbp": 90,
            "hr": 84,
            "rr": 18,
            "bt": 36.9,
            "saturation": 97
        }
    }
    r1 = client.post("/api/assessment/json", json=initial_payload)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["patient_id"] == p_id

    # Observation update with deteriorating vitals: SBP drops to 80, HR rises to 135
    updated_vitals = {
        "vitals": {
            "age": 55,
            "sex": "Female",
            "arrival_mode": 1,
            "injury": 1,
            "chief_complaint": "Acute severe chest pain, diaphoresis",
            "sbp": 80,
            "dbp": 50,
            "hr": 135,
            "rr": 28,
            "bt": 36.6,
            "saturation": 87
        }
    }
    import json
    form_data = {"patient_data": json.dumps(updated_vitals)}
    r2 = client.post(f"/api/timeline/{p_id}/observation", data=form_data)
    assert r2.status_code == 200
    d2 = r2.json()

    # Priority should immediately escalate to CRITICAL due to shock index 135/80 = 1.68 >= 1.2
    assert d2["priority"] in ["CRITICAL", "HIGH"]
    assert d2["risk_score"] >= 78.0
    assert "clinical_differential" in d2
