"""
Symptom-Condition Intelligence Matcher.

Uses the 41-condition clinical dictionary from symptom_Description.csv to provide
semantic condition suggestions based on patient chief complaints and symptoms.

CRITICAL DISTINCTION:
Outputs are labeled 'Potential Clinical Conditions for Triage Context'
and are strictly NOT confirmed diagnoses.
"""
import os
import pandas as pd
from typing import List, Dict, Any
import re


class SymptomMatcher:
    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            dataset_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "datasets", "symptom_disease", "symptom_Description.csv"
            )
        self.dataset_path = os.path.abspath(dataset_path)
        self.disease_df = pd.DataFrame()
        self.disease_keywords: Dict[str, List[str]] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if os.path.exists(self.dataset_path):
            STOPWORDS = {
                "and", "the", "for", "with", "appear", "appears", "body", "area", "causing", "causes",
                "pain", "severe", "disease", "condition", "most", "also", "often", "can", "may", "which",
                "part", "parts", "that", "this", "from", "some", "other", "infection", "human", "type",
                "such", "into", "their", "when", "over", "well", "your", "acute", "first", "than", "more"
            }
            self.disease_df = pd.read_csv(self.dataset_path)
            for _, row in self.disease_df.iterrows():
                disease = str(row['Disease']).strip()
                desc = str(row.get('Description', '')).lower()
                tokens = [t for t in re.findall(r'\b[a-z]{3,}\b', desc) if t not in STOPWORDS]
                name_tokens = [t for t in re.findall(r'\b[a-z]{3,}\b', disease.lower()) if t not in STOPWORDS]
                self.disease_keywords[disease] = list(set(tokens + name_tokens))
        else:
            # Fallback essential emergency conditions if path not yet resolved
            self.disease_keywords = {
                "Hypertension": ["blood", "pressure", "hypertensive", "hypertension"],
                "Angina / ACS": ["chest", "angina", "coronary", "ischemic", "infarction", "myocardial"],
                "Pneumonia / Bronchitis": ["cough", "fever", "dyspnea", "phlegm", "consolidation", "lung"],
                "Gastroenteritis / Gastritis": ["epigastric", "abdominal", "vomiting", "nausea", "diarrhea"]
            }

    def match_symptoms(self, chief_complaint: str, symptoms_text: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Calculates context match scores between patient presentation and condition descriptions.
        """
        combined_text = f"{chief_complaint} {symptoms_text}".lower()
        STOPWORDS = {"and", "the", "for", "with", "has", "had", "have", "past", "this", "that", "from"}
        input_tokens = set([t for t in re.findall(r'\b[a-z]{3,}\b', combined_text) if t not in STOPWORDS])
        
        if not input_tokens:
            return []

        results = []
        for disease, keywords in self.disease_keywords.items():
            if not keywords:
                continue
            common = input_tokens.intersection(set(keywords))
            if not common:
                continue
            score = len(common) / max(len(input_tokens), 1)
            
            # Bonus match ONLY if entire disease name or specific medical term appears in text
            if disease.lower() in combined_text:
                score += 0.35

            if score > 0.10:
                # Retrieve description if available
                desc = ""
                if not self.disease_df.empty:
                    match_row = self.disease_df[self.disease_df['Disease'] == disease]
                    if not match_row.empty:
                        desc = match_row.iloc[0].get('Description', '')
                        
                results.append({
                    "condition": disease,
                    "relevance_score": round(min(score, 1.0), 3),
                    "matched_keywords": list(common),
                    "description": desc,
                    "clinical_disclaimer": "Potential condition for triage consideration only; not a formal diagnosis."
                })

        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:top_k]
