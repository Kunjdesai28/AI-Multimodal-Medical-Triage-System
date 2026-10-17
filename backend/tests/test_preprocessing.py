"""
Unit Tests for Preprocessing Modules.
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.preprocessing.clinical_preprocessor import ClinicalPreprocessor
from backend.app.preprocessing.ecg_preprocessor import ECGPreprocessor
from backend.app.preprocessing.xray_preprocessor import XRayPreprocessor
from backend.app.preprocessing.symptom_matcher import SymptomMatcher


def test_clinical_sanitization_and_engineering():
    # Raw row with dirty strings '??', '#BO!'
    raw_dict = {
        'Age': 60,
        'Sex': 1,
        'Arrival mode': 2,
        'Injury': 1,
        'Chief_complain': 'chest pain',
        'Mental': 1,
        'Pain': 1,
        'NRS_pain': '#BO!',  # Dirty excel artifact
        'SBP': '??',        # Missing artifact
        'DBP': 80,
        'HR': 110,
        'RR': 20,
        'BT': 37.0,
        'Saturation': '??', # Missing
        'Patients number per hour': 5
    }
    df = pd.DataFrame([raw_dict])
    prep = ClinicalPreprocessor()
    df_clean = prep._clean_dataframe(df)
    
    assert pd.isna(df_clean['NRS_pain'].iloc[0])
    assert pd.isna(df_clean['SBP'].iloc[0])
    assert pd.isna(df_clean['Saturation'].iloc[0])
    assert df_clean['HR'].iloc[0] == 110.0

    df_eng = prep._engineer_features(df_clean)
    assert 'Shock_Index' in df_eng.columns
    assert 'Pulse_Pressure' in df_eng.columns
    assert 'MAP' in df_eng.columns
    assert df_eng['Saturation_Missing'].iloc[0] == 1.0


def test_ecg_preprocessor():
    # Test random lead signal
    sig = np.sin(np.linspace(0, 10, 187))
    norm_sig = ECGPreprocessor.normalize_signal(sig)
    assert np.min(norm_sig) >= 0.0
    assert np.max(norm_sig) <= 1.0

    # Test padding shorter signals
    short_sig = [0.1, 0.5, 0.9, 0.2]
    padded = ECGPreprocessor.process_raw_lead(short_sig)
    assert len(padded) == 187
    assert padded[0] == 0.0 or padded[0] <= 1.0

    # Test parsing CSV format bytes
    csv_bytes = b"0.1,0.2,0.3,0.4,0.5\n" + b"\n".join([b"0.1" for _ in range(185)])
    tensor_input, waveform = ECGPreprocessor.parse_uploaded_csv(csv_bytes)
    assert tensor_input.shape == (1, 1, 187)
    assert len(waveform) == 187


def test_symptom_matcher():
    matcher = SymptomMatcher()
    results = matcher.match_symptoms("Severe crushing retrosternal chest pain", top_k=3)
    assert isinstance(results, list)
    # Check that matched conditions are labeled as potential conditions
    for r in results:
        assert "condition" in r
        assert "relevance_score" in r
        assert "clinical_disclaimer" in r
