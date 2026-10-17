"""
Clinical Context Builder.

Aggregates available clinical information from the current assessment into a
de-identified, multimodal clinical context payload for evidence-grounded differential analysis.

Strictly protects patient privacy:
- Excludes patient names, patient IDs, contact information, and institutional identifiers.
- Preserves clinical fidelity (demographics, complaints, vitals, hemodynamics, ECG, scans).
"""
from typing import Dict, Any, Optional


class ClinicalContextBuilder:
    """
    Constructs de-identified multimodal clinical context objects.
    """

    ARRIVAL_MODE_MAP = {
        1: "Walking / Self-Presentation",
        2: "Ambulance / Emergency Medical Services (EMS)",
        3: "Private Transport / Other Hospital Transfer",
        4: "Other / Unspecified"
    }

    INJURY_MAP = {
        1: "Non-Trauma / Acute Medical Illness",
        2: "Trauma / Acute Physical Injury"
    }

    MENTAL_STATUS_MAP = {
        1: "Alert",
        2: "Verbal (responds to verbal stimuli)",
        3: "Pain (responds to painful stimuli)",
        4: "Unresponsive"
    }

    @classmethod
    def calculate_hemodynamics(cls, sbp: Optional[float], dbp: Optional[float], hr: Optional[float]) -> Dict[str, Any]:
        """
        Calculates verified hemodynamic indices with defensive boundary handling:
        - Shock Index = HR / SBP (HR/SBP ratio; >0.9 indicates acute occult hypoperfusion)
        - MAP = (SBP + 2 * DBP) / 3 (Mean Arterial Pressure)
        - Pulse Pressure = SBP - DBP (Narrowed if <30, widened if >60)
        """
        sbp_val = float(sbp) if sbp is not None else None
        dbp_val = float(dbp) if dbp is not None else None
        hr_val = float(hr) if hr is not None else None

        shock_index = None
        if hr_val is not None and sbp_val is not None:
            sbp_safe = max(sbp_val, 20.0)
            shock_index = round(min(max(hr_val / sbp_safe, 0.1), 6.0), 2)

        map_val = None
        if sbp_val is not None and dbp_val is not None:
            map_val = round(min(max((sbp_val + 2.0 * dbp_val) / 3.0, 10.0), 250.0), 1)

        pulse_pressure = None
        if sbp_val is not None and dbp_val is not None:
            pulse_pressure = round(min(max(sbp_val - dbp_val, 5.0), 200.0), 1)

        return {
            "shock_index": shock_index,
            "map": map_val,
            "pulse_pressure": pulse_pressure
        }

    @classmethod
    def build_context(
        cls,
        patient_data: Dict[str, Any],
        clinical_indices: Optional[Dict[str, Any]] = None,
        ecg_output: Optional[Dict[str, Any]] = None,
        xray_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive, strictly de-identified clinical context dictionary.
        """
        # A. Demographics & Encounter Details (DE-IDENTIFIED)
        age = patient_data.get("age", patient_data.get("Age"))
        sex = patient_data.get("sex", patient_data.get("Sex", "Unspecified"))
        arrival_code = patient_data.get("arrival_mode", patient_data.get("Arrival mode", 1))
        injury_code = patient_data.get("injury", patient_data.get("Injury", 1))
        past_history = patient_data.get("past_history", patient_data.get("history", "None documented"))

        demographics = {
            "age": int(age) if age is not None else "Unknown",
            "sex": str(sex),
            "arrival_mode": cls.ARRIVAL_MODE_MAP.get(int(arrival_code), f"Mode {arrival_code}"),
            "injury_classification": cls.INJURY_MAP.get(int(injury_code), f"Type {injury_code}"),
            "relevant_history": str(past_history)
        }

        # B. Presenting Complaint & Symptoms
        chief_complaint = patient_data.get("chief_complaint", patient_data.get("Chief_complaint", "")).strip()
        symptoms = patient_data.get("symptoms", patient_data.get("Symptoms", "")).strip()
        nrs_pain = patient_data.get("nrs_pain", patient_data.get("NRS_pain", patient_data.get("pain", 0)))
        mental_code = patient_data.get("mental", patient_data.get("Mental", 1))

        presenting_complaint = {
            "chief_complaint": chief_complaint,
            "associated_symptoms": symptoms if symptoms else "None explicitly documented",
            "pain_severity_nrs": f"{nrs_pain}/10" if nrs_pain is not None else "Not assessed",
            "mental_status": cls.MENTAL_STATUS_MAP.get(int(mental_code), f"Score {mental_code}")
        }

        # C. Vital Signs
        sbp = patient_data.get("sbp", patient_data.get("SBP"))
        dbp = patient_data.get("dbp", patient_data.get("DBP"))
        hr = patient_data.get("hr", patient_data.get("HR"))
        rr = patient_data.get("rr", patient_data.get("RR"))
        bt = patient_data.get("bt", patient_data.get("BT"))
        spo2 = patient_data.get("saturation", patient_data.get("Saturation"))

        vitals = {
            "systolic_bp_mmHg": float(sbp) if sbp is not None else None,
            "diastolic_bp_mmHg": float(dbp) if dbp is not None else None,
            "heart_rate_bpm": float(hr) if hr is not None else None,
            "respiratory_rate_per_min": float(rr) if rr is not None else None,
            "body_temperature_c": float(bt) if bt is not None else None,
            "oxygen_saturation_spo2": float(spo2) if spo2 is not None else None
        }

        # D. Calculated Hemodynamics
        if clinical_indices and "shock_index" in clinical_indices and "map" in clinical_indices:
            hemodynamics = {
                "shock_index": clinical_indices.get("shock_index"),
                "map": clinical_indices.get("map"),
                "pulse_pressure": clinical_indices.get("pulse_pressure")
            }
        else:
            hemodynamics = cls.calculate_hemodynamics(vitals["systolic_bp_mmHg"], vitals["diastolic_bp_mmHg"], vitals["heart_rate_bpm"])

        # E. ECG Modality Assessment
        if ecg_output is not None and isinstance(ecg_output, dict):
            ecg_context = {
                "available": True,
                "status": "Available and processed",
                "rhythm_classification": ecg_output.get("predicted_class", "Evaluated Tracing"),
                "abnormality_score": ecg_output.get("abnormality_score"),
                "is_abnormal": ecg_output.get("is_abnormal", False),
                "limitations": "Automated single-lead rhythm classifier; does not evaluate acute ST-elevation/depression, ischemia, or QT intervals."
            }
        else:
            ecg_context = {
                "available": False,
                "status": "Not recorded / unavailable at triage",
                "limitations": "No ECG signal provided; cardiac electrical activity and rhythm cannot be evaluated."
            }

        # F. Medical Imaging Modality Assessment
        if xray_output is not None and isinstance(xray_output, dict):
            detected = [
                f["condition"] for f in xray_output.get("detected_findings", [])
                if isinstance(f, dict) and f.get("condition")
            ]
            primary = xray_output.get("primary_findings", detected)
            top_cond = xray_output.get("top_condition", "Evaluated Study")
            modality = xray_output.get("modality", "Chest Radiography")
            region = xray_output.get("anatomical_region", "Thorax")
            abnormality = xray_output.get("composite_abnormality_score", xray_output.get("abnormality_score", 0.0))

            imaging_context = {
                "available": True,
                "status": "Available and processed",
                "modality": modality,
                "anatomical_region": region,
                "top_condition": top_cond,
                "primary_findings": primary,
                "composite_abnormality_score": abnormality,
                "clinical_rationale": xray_output.get("clinical_rationale", "Radiographic screening performed."),
                "limitations": "Screening triage AI interpretation; requires formal radiologist reading."
            }
        else:
            imaging_context = {
                "available": False,
                "status": "Not performed / unavailable at triage",
                "limitations": "No diagnostic imaging study submitted; acute pulmonary, thoracic, or intracranial pathology cannot be radiologically evaluated."
            }

        return {
            "demographics": demographics,
            "presenting_complaint": presenting_complaint,
            "vital_signs": vitals,
            "calculated_hemodynamics": hemodynamics,
            "ecg_findings": ecg_context,
            "imaging_findings": imaging_context
        }
