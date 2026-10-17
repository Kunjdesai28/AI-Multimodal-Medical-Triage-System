"""
Clinical Preprocessor for Emergency Service Triage Data.

Handles data cleaning, non-numeric artifact sanitization, feature engineering,
imputation, scaling, and transformation for XGBoost training and real-time inference.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib
import os


class ClinicalPreprocessor:
    """
    Standardized preprocessor for clinical emergency triage data.
    Ensures identical transformations between offline training and online inference.
    """
    
    # Feature columns used for modeling (strictly excluding target leakage columns)
    NUMERICAL_COLS = [
        'Age', 'SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation', 
        'Patients number per hour', 'NRS_pain'
    ]
    
    CATEGORICAL_COLS = [
        'Sex', 'Arrival mode', 'Injury', 'Mental', 'Pain', 'KTAS_RN'
    ]
    
    # Post-admission future outcome columns that MUST NEVER be fed as features (strict anti-leakage)
    LEAKAGE_COLS = [
        'Diagnosis in ED', 'Disposition', 'Error_group',
        'Length of stay_min', 'KTAS duration_min', 'mistriage', 'Group'
    ]
    
    def __init__(self):
        self.num_imputer = SimpleImputer(strategy='median')
        self.cat_imputer = SimpleImputer(strategy='most_frequent')
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted = False
        
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitizes raw string representations and artifacts like '??', '#BO!'."""
        df = df.copy()
        
        # Replace string missingness artifacts
        replace_map = {'??': np.nan, '?': np.nan, '#BO!': np.nan, '#VALUE!': np.nan, ' ': np.nan, '': np.nan}
        df = df.replace(replace_map)
        
        # Coerce numerical columns
        for col in self.NUMERICAL_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
                
        # Coerce categorical columns to numeric/discrete
        for col in self.CATEGORICAL_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes clinically validated risk indices:
        - Shock Index (HR / SBP): >0.9 indicates acute occult shock/hypoperfusion
        - Pulse Pressure (SBP - DBP): <30 narrow or >60 widened
        - Mean Arterial Pressure (MAP): (2*DBP + SBP) / 3
        - Modified Shock Index (HR / MAP)
        - Age Shock Index (Age * Shock Index)
        - MEWS (Modified Early Warning Score)
        - Saturation Missing Indicator: missing SpO2 often correlates with acuity
        - Altered Mental Indicator: Mental > 1 (Verbal/Pain/Unresponsive)
        """
        df = df.copy()
        
        # Prevent division by zero - universal SBP min is 20.0 mmHg
        sbp_safe = df['SBP'].clip(lower=20.0)
        
        # Universal physiological limits
        df['Shock_Index'] = (df['HR'] / sbp_safe).clip(0.1, 6.0)
        df['Pulse_Pressure'] = (df['SBP'] - df['DBP']).clip(5.0, 200.0)
        df['MAP'] = ((2.0 * df['DBP'] + df['SBP']) / 3.0).clip(10.0, 250.0)
        df['Modified_Shock_Index'] = (df['HR'] / df['MAP'].clip(lower=10.0)).clip(0.1, 6.0)
        df['Age_Shock_Index'] = (df['Age'] * df['Shock_Index']).clip(0, 500)
        df['Saturation_Missing'] = df['Saturation'].isna().astype(float)
        
        df['Altered_Mental'] = (df['Mental'] > 1).astype(float)
        df['Severe_Pain'] = (df['NRS_pain'] >= 7).astype(float)
        df['Tachycardia'] = (df['HR'] > 100).astype(float)
        df['Hypotension'] = (df['SBP'] < 90).astype(float)
        df['Hypoxia'] = (df['Saturation'] < 92).astype(float)

        # Clinically validated MEWS (Modified Early Warning Score)
        mews = np.zeros(len(df))
        mews += np.where((df['SBP'] <= 70), 3, np.where((df['SBP'] <= 80), 2, np.where((df['SBP'] <= 100), 1, np.where(df['SBP'] >= 200, 2, 0))))
        mews += np.where((df['HR'] <= 40), 2, np.where((df['HR'] <= 50), 1, np.where((df['HR'] >= 130), 3, np.where((df['HR'] >= 111), 2, np.where(df['HR'] >= 101, 1, 0)))))
        mews += np.where((df['RR'] < 9), 2, np.where((df['RR'] >= 30), 3, np.where((df['RR'] >= 21), 2, np.where(df['RR'] >= 15, 1, 0))))
        mews += np.where((df['BT'] < 35.0), 2, np.where(df['BT'] >= 38.5, 2, 0))
        mews += np.where(df['Mental'] > 1, 2, 0)
        df['MEWS'] = mews
        
        return df

    def fit(self, X: pd.DataFrame) -> 'ClinicalPreprocessor':
        """Fit imputers and scalers on clean training features."""
        X_clean = self._clean_dataframe(X)
        X_eng = self._engineer_features(X_clean)
        
        # Prepare numerical columns including engineered ones
        eng_num_cols = [
            'Shock_Index', 'Pulse_Pressure', 'MAP', 
            'Modified_Shock_Index', 'Age_Shock_Index', 'MEWS',
            'Saturation_Missing', 'Altered_Mental', 'Severe_Pain',
            'Tachycardia', 'Hypotension', 'Hypoxia'
        ]
        all_num_cols = self.NUMERICAL_COLS + eng_num_cols
        
        # Fit numerical imputer
        self.num_imputer.fit(X_eng[all_num_cols])
        imputed_num = self.num_imputer.transform(X_eng[all_num_cols])
        
        # Fit categorical imputer
        self.cat_imputer.fit(X_eng[self.CATEGORICAL_COLS])
        imputed_cat = self.cat_imputer.transform(X_eng[self.CATEGORICAL_COLS])
        
        # Scale combined features
        combined = np.hstack([imputed_num, imputed_cat])
        self.scaler.fit(combined)
        
        self.feature_names = all_num_cols + self.CATEGORICAL_COLS
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform input features using fitted pipelines."""
        if not self.is_fitted:
            raise ValueError("ClinicalPreprocessor must be fitted before transform.")
            
        X_clean = self._clean_dataframe(X)
        X_eng = self._engineer_features(X_clean)
        
        eng_num_cols = [
            'Shock_Index', 'Pulse_Pressure', 'MAP', 
            'Modified_Shock_Index', 'Age_Shock_Index', 'MEWS',
            'Saturation_Missing', 'Altered_Mental', 'Severe_Pain',
            'Tachycardia', 'Hypotension', 'Hypoxia'
        ]
        all_num_cols = self.NUMERICAL_COLS + eng_num_cols
        
        # Ensure all columns exist
        for col in all_num_cols:
            if col not in X_eng.columns:
                X_eng[col] = np.nan
        for col in self.CATEGORICAL_COLS:
            if col not in X_eng.columns:
                X_eng[col] = np.nan
                
        imputed_num = self.num_imputer.transform(X_eng[all_num_cols])
        imputed_cat = self.cat_imputer.transform(X_eng[self.CATEGORICAL_COLS])
        
        combined = np.hstack([imputed_num, imputed_cat])
        scaled = self.scaler.transform(combined)
        return scaled

    def transform_single_patient(self, patient_dict: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Transforms a single patient's incoming observation dictionary from the API.
        Handles casing variations (sbp vs SBP) and maps string demographics to numerical classes.
        Returns transformed feature array for XGBoost and calculated clinical indices.
        """
        # Standardize dictionary keys to match trained model column names
        sex_val = patient_dict.get('sex', patient_dict.get('Sex', 1))
        if isinstance(sex_val, str):
            sex_numeric = 1 if sex_val.lower().startswith('m') else 2
        else:
            sex_numeric = int(sex_val or 1)

        # Determine KTAS_RN: Use explicit input if provided; otherwise estimate based on clinical presentation
        explicit_rn = patient_dict.get('ktas_rn', patient_dict.get('KTAS_RN'))
        if explicit_rn is not None and str(explicit_rn).strip():
            rn_val = int(explicit_rn)
        else:
            # Objective physiological baseline triage heuristic
            mental_v = int(patient_dict.get('mental', patient_dict.get('Mental', 1)) or 1)
            sbp_v = float(patient_dict.get('sbp', patient_dict.get('SBP', 120)) or 120)
            hr_v = float(patient_dict.get('hr', patient_dict.get('HR', 75)) or 75)
            rr_v = float(patient_dict.get('rr', patient_dict.get('RR', 18)) or 18)
            bt_v = float(patient_dict.get('bt', patient_dict.get('BT', 36.8)) or 36.8)
            spo2_v = float(patient_dict.get('saturation', patient_dict.get('Saturation', 98)) or 98)
            nrs_v = float(patient_dict.get('nrs_pain', patient_dict.get('NRS_pain', 0)) or 0)
            arr_v = int(patient_dict.get('arrival_mode', patient_dict.get('Arrival mode', 1)) or 1)
            si_v = hr_v / max(sbp_v, 30.0)

            if mental_v >= 3 or si_v >= 1.3 or spo2_v < 86 or sbp_v < 75:
                rn_val = 1
            elif mental_v == 2 or si_v >= 1.0 or sbp_v < 90 or spo2_v < 91 or rr_v >= 30 or hr_v >= 130:
                rn_val = 2
            elif nrs_v >= 5 or bt_v >= 38.3 or hr_v > 100 or rr_v >= 22 or spo2_v <= 94 or arr_v == 2:
                rn_val = 3
            elif nrs_v > 2 or arr_v == 3:
                rn_val = 4
            else:
                rn_val = 5

        std_dict = {
            'Age': patient_dict.get('age', patient_dict.get('Age', 50)),
            'Sex': sex_numeric,
            'Arrival mode': patient_dict.get('arrival_mode', patient_dict.get('Arrival mode', 3)),
            'Injury': patient_dict.get('injury', patient_dict.get('Injury', 1)),
            'Mental': patient_dict.get('mental', patient_dict.get('Mental', 1)),
            'Pain': patient_dict.get('pain', patient_dict.get('Pain', 1)),
            'NRS_pain': patient_dict.get('nrs_pain', patient_dict.get('NRS_pain', 4)),
            'KTAS_RN': rn_val,
            'SBP': patient_dict.get('sbp', patient_dict.get('SBP', 120)),
            'DBP': patient_dict.get('dbp', patient_dict.get('DBP', 80)),
            'HR': patient_dict.get('hr', patient_dict.get('HR', 75)),
            'RR': patient_dict.get('rr', patient_dict.get('RR', 18)),
            'BT': patient_dict.get('bt', patient_dict.get('BT', 36.8)),
            'Saturation': patient_dict.get('saturation', patient_dict.get('Saturation', 98)),
            'Patients number per hour': patient_dict.get('patients_number_per_hour', patient_dict.get('Patients number per hour', 8)),
        }

        df = pd.DataFrame([std_dict])
        df_clean = self._clean_dataframe(df)
        df_eng = self._engineer_features(df_clean)
        unscaled_dict = df_eng.iloc[0].to_dict()

        features = self.transform(df)
        
        # Calculate raw clinical indices for explainability display
        sbp = float(std_dict.get('SBP', 120) or 120)
        dbp = float(std_dict.get('DBP', 80) or 80)
        hr = float(std_dict.get('HR', 75) or 75)
        spo2 = float(std_dict.get('Saturation', 98) or 98) if std_dict.get('Saturation') is not None else 98.0
        
        shock_index = round(float(min(max(hr / max(sbp, 20.0), 0.1), 6.0)), 2)
        map_val = round(float(min(max((2.0 * dbp + sbp) / 3.0, 10.0), 250.0)), 1)
        pulse_pressure = round(float(min(max(sbp - dbp, 5.0), 200.0)), 1)
        
        indices = {
            'shock_index': shock_index,
            'map': map_val,
            'pulse_pressure': pulse_pressure,
            'spo2': spo2,
            'hr': hr,
            'sbp': sbp,
            'dbp': dbp,
            'altered_mental': 1.0 if float(std_dict.get('Mental', 1) or 1) > 1 else 0.0,
            'unscaled_features': unscaled_dict
        }
        return features, indices

    def save(self, filepath: str):
        """Saves fitted preprocessor state."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> 'ClinicalPreprocessor':
        """Loads fitted preprocessor state."""
        return joblib.load(filepath)
