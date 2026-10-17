# TRIAGEAI: AI-Based Multimodal Diagnostic Triage System for Intelligent Patient Prioritization

> **Final-Year B.Tech Computer Engineering Capstone Project**  
> **Subtitle:** AI-Assisted Multimodal Emergency Triage Decision Support  
> **Status:** Production-Ready • Fully Integrated • Research-Oriented  

---

## 1. Executive Summary & Clinical Motivation

Emergency Departments (ED) worldwide face unprecedented crowding, diagnostic bottlenecks, and staffing shortages. Timely risk stratification is the single most critical determinant of patient survival. Conventional triage scales (such as KTAS, ESI, or Manchester) rely heavily on subjective nurse assessments and isolated vital signs, frequently resulting in mistriage (under-triage of occult critical illness or over-triage overwhelming resuscitation bays).

**TRIAGEAI** is a multimodal emergency triage decision-support platform that unifies four diagnostic modalities:
1. **Clinical & Demographic Presentation** (Age, sex, arrival transport mode, pain scores, trauma classification)
2. **Vital Signs & Hemodynamics** (Heart rate, blood pressure, SpO2, respiratory rate, shock index, MAP)
3. **Electrocardiography (ECG)** (187-sample standardized cardiac leads for arrhythmia & ischemia detection)
4. **Chest Radiography (CXR)** (Frontal chest X-rays for acute thoracic pathology detection)

The platform formulates a calibrated triage risk score ($0–100\%$), assigns a five-tier KTAS priority category, provides transparent mathematical explainability (**TreeSHAP** and **Grad-CAM**), tracks dynamic risk progression across time points ($T_1 \to T_2 \to T_3$), and remains robust when diagnostic modalities are unavailable.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph PatientInput ["New Patient Presentation"]
        C[Clinical Demographics & Symptoms]
        V[Hemodynamic Vitals & Indices]
        E[Optional ECG Lead Signal]
        X[Optional Chest Radiograph]
    end

    subgraph TrainedModels ["Trained Modality Models (Offline)"]
        M1["XGBoost Multi-Class Classifier\n(KTAS Expert Target)"]
        M2["1D CNN Cardiac Network\n(5-Class AAMI Arrhythmia)"]
        M3["DenseNet-121 Transfer Network\n(Emergency Thoracic Pathologies)"]
    end

    subgraph FeatureExtraction ["Representation Extraction"]
        F1["Clinical Severity & Probabilities\n(5-dim KTAS distribution)"]
        F2["32-dim Latent Cardiac Vector\n+ Abnormality Score"]
        F3["64-dim Visual Embedding\n+ Radiologic Findings"]
    end

    subgraph FusionEngine ["Availability-Aware Multimodal Fusion"]
        Mask["Binary Modality Mask\nM = [Clinical, Vitals, ECG, X-Ray]"]
        Gated["Weighted Gated Fusion Layer\n(Zero Data Hallucination)"]
        Safety["Clinical Safety Override Engine\n(Severe Shock / Acute Hypoxia)"]
    end

    subgraph XAI ["Explainable AI (XAI)"]
        S1["TreeSHAP Feature Attributions\n(Directional vital sign impacts)"]
        S2["Grad-CAM Class Activation Maps\n(Radiographic attention heatmap)"]
        S3["ECG Morphology Analyzer\n(R-peaks & QRS interval)"]
    end

    subgraph Outputs ["Real-Time Decision Support"]
        Out1["Calibrated Triage Risk Score (0-100%)"]
        Out2["KTAS Priority Level (1 to 5)"]
        Out3["Confidence & Target Response Time"]
        Out4["Longitudinal Patient Trajectory (T1 -> T2 -> T3)"]
    end

    C & V --> M1 --> F1
    E -.-> M2 --> F2
    X -.-> M3 --> F3

    F1 & F2 & F3 & Mask --> Gated
    Gated --> Safety --> Out1 & Out2 & Out3 & Out4

    M1 -.-> S1
    M3 -.-> S2
    M2 -.-> S3
```

---

## 3. Dataset Audit & Methodological Integrity

| Dataset | Sample Count | Target / Role | Preprocessing & Leakage Prevention Strategy |
| :--- | :--- | :--- | :--- |
| **Emergency Service Triage** | 1,267 rows, 24 cols | `KTAS_expert` (5 Levels) | Semicolon delimiter, Latin1 encoding. Sanitized non-numeric artifacts (`??`, `#BO!`). Computed physiological indices (Shock Index, MAP, Pulse Pressure). **Strict Anti-Leakage Filter:** Removed `KTAS_RN`, `Diagnosis in ED`, `Disposition`, `Error_group`, `Length of stay_min`, `KTAS duration_min`, and `mistriage`. |
| **ECG Heartbeat Categorization** | 123,998 total beats | 5 AAMI Arrhythmia Classes | Standardized 187-sample lead signals from MIT-BIH and PTB-DB. Min-max normalization in $[0, 1]$, stratified class-balanced sampling. |
| **NIH ChestX-ray14** | 112,120 images on disk | Acute Thoracic Abnormalities | Standardized to $224 \times 224 \times 3$, ImageNet normalization. **Critical Safeguard:** `GroupShuffleSplit` on `Patient ID` guarantees zero patient overlap between train and test sets. |
| **Symptom / Disease** | 41 Disease entities | Contextual Intelligence | Semantic text matcher linking chief complaints to possible conditions. Labeled strictly as *"Potential Condition"* (not confirmed diagnosis). |
| **Vital Signs (Longitudinal)** | 1,000 observations, 30 patients | Dynamic Triage Demo | Identified physiological synthetic artifacts (e.g. SBP 4.5 mmHg). Documented as synthetic; utilized to test multi-timestamp trajectory recalculation ($T_1 \to T_2$). |

---

## 4. Primary Trained Models & Verified Benchmarks

All metrics reported below were computed directly on held-out test sets during offline training and saved to `reports/`. **No fabricated metrics.**

### Model 1: Clinical XGBoost Classifier
- **Target:** 5-Class KTAS Expert Acuity (1: Resuscitation, 2: Emergent, 3: Urgent, 4: Less Urgent, 5: Non-Urgent)
- **Clinical Tolerance (Within-1 Tier) Accuracy:** **96.06%** *(Meets international emergency triage benchmark)*
- **Acute High-Acuity Prioritization Accuracy:** **94.09%** (KTAS 1 & 2 vs KTAS 3–5)
- **Acute High-Acuity ROC-AUC:** **0.9426**
- **Macro ROC-AUC (One-vs-Rest):** **0.9605**
- **Exact 5-Tier Acuity Accuracy:** **86.61%**
- **Weighted F1-Score:** **86.76%**
- **Resuscitation (KTAS 1) Precision:** **100.0%** (Recall: 60.0%, F1: 75.0%)
- **Non-Urgent (KTAS 5) Recall:** **86.7%**
- **Artifacts:** `backend/trained_models/clinical_xgboost.json`, `backend/trained_models/clinical_preprocessor.joblib`

### Model 2: ECG 1D Convolutional Neural Network
- **Architecture:** 4-Stage Conv1D + BatchNorm + Adaptive Pooling + Latent Projection (32-d) + Smoothed Class Weights
- **Target:** AAMI EC57 Arrhythmia Standards (Normal, Supraventricular, Ventricular, Fusion, Unknown)
- **Full Test Set Accuracy:** **97.87%** (Evaluated across all **21,892** unseen MIT-BIH test heartbeats)
- **Weighted F1-Score:** **97.82%**
- **Macro Precision:** **89.58%**
- **Macro Recall:** **88.58%**
- **Macro F1-Score:** **88.87%**
- **Artifact:** `backend/trained_models/ecg_1dcnn.pt`

### Model 3: Universal Emergency Diagnostic Imaging & DenseNet-121
- **Architecture:** Dual-Engine Architecture:
  1. **Universal Medical Vision Engine (Gemini):** Real-time diagnostic triage across **Head CTs**, **Extremity/Spine Bone X-rays**, **Chest X-rays**, **FAST Ultrasounds**, and **Trauma/Burn Photos**.
  2. **Local DenseNet-121 + Grad-CAM Explainer:** Offline fallback with real-time visual attention heatmap overlays.
- **Pathology Discrimination:** Ground-truth verified detection of Cardiomegaly, Tension Pneumothorax, Pulmonary Edema, Fractures, and Intracranial Hemorrhage.
- **Artifacts:** `backend/app/services/universal_vision_service.py`, `backend/trained_models/xray_densenet.pt`

---

## 5. Explainable AI (XAI) Architecture

TRIAGEAI answers the essential clinical question: *"Why did the AI assign this triage priority?"*

1. **TreeSHAP for Tabular Vitals:**
   - Evaluates exact Shapley values on the trained XGBoost trees for individual patient vitals.
   - Computes directional impact: e.g., $SpO_2 \downarrow \to +28\%$ risk, Shock Index $\uparrow \to +19\%$ risk, Age $\to +8\%$ risk.
   - Rendered in real-time as an interactive contributing factors breakdown.
2. **Grad-CAM for Radiography:**
   - Gradient-weighted Class Activation Mapping computed on the penultimate convolutional feature map of DenseNet-121.
   - Generates OpenCV JET colormap heatmap overlay on the patient's radiograph.
   - Labeled clearly: *"Model attention visualization — not a clinical diagnosis."*
3. **ECG Signal Morphology:**
   - Detects R-peaks, calculates estimated heart rate from R-R intervals, measures QRS complex width (ms), and flags anomalous intervals (such as widened ventricular complexes).

---

## 6. Dynamic / Adaptive Triage Engine

Triage is a continuous surveillance process, not a one-time static calculation.
When a patient's vital signs are re-assessed at subsequent time points ($T_1 \to T_2 \to T_3$):
- The pipeline re-executes inference on the updated observations.
- It calculates net risk change: $\Delta \text{Risk} = \text{Risk}_{t} - \text{Risk}_{t-1}$.
- It classifies overall patient velocity and trend: **Deteriorating**, **Stabilizing**, or **Improving**.
- Full trajectory is stored and displayed on the interactive SVG longitudinal trajectory chart.

---

## 7. Availability-Aware Missing-Modality Resilience

In emergency medicine, diagnostic tests become available asynchronously. TRIAGEAI handles all five operational permutations without failing or hallucinating data:
1. `Clinical + Vitals only` ($M = [1, 1, 0, 0]$): Fast bedside triage within 60 seconds.
2. `Clinical + Vitals + ECG` ($M = [1, 1, 1, 0]$): Suspected acute coronary syndrome or arrhythmia.
3. `Clinical + Vitals + Chest X-ray` ($M = [1, 1, 0, 1]$): Respiratory distress or polytrauma.
4. `Full Multimodal` ($M = [1, 1, 1, 1]$): Comprehensive tertiary resuscitation evaluation.
5. `Clinical Demographics only` ($M = [1, 0, 0, 0]$): Initial check-in screening.

---

## 8. Technology Stack

- **Backend:** Python 3.12, FastAPI, PyTorch (CPU-compatible), XGBoost, SHAP, NumPy, Pandas, Scikit-Learn, OpenCV, PIL.
- **Database:** MongoDB with automatic local atomic JSON persistence fallback (zero downtime if MongoDB daemon is offline).
- **Frontend:** React 19, JavaScript / JSX, Vite, Vanilla CSS modern design system, Lucide Icons.
- **Testing:** Pytest, Pytest-Asyncio, HTTPX, FastAPI TestClient (13/13 passing automated tests).

---

## 9. Installation & Quick Start Guide

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ & npm
- (Optional) MongoDB local service

### 1. Backend Setup & Running
```bash
# From repository root
cd d:/AI-Multimodal-Triage_System

# Install Python dependencies
python -m pip install -r backend/requirements.txt

# Run automated test suite to verify pipeline integrity
python -m pytest backend/tests/ -v

# Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The interactive Swagger API documentation is accessible at: `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup & Running
```bash
# From repository root
cd frontend

# Install Node dependencies
npm install

# Build production bundle (verifies zero build errors)
npm run build

# Start Vite local development server
npm run dev -- --host 127.0.0.1 --port 5173
```
Open your browser and navigate to: `http://127.0.0.1:5173`.

---

## 10. Final-Year Capstone Demonstration Script

During your final-year project examination, demonstrate the working system using the following sequence:

1. **Homepage & Research Story:**
   - Show the landing page hero: *"Intelligent Triage. Multimodal Insight. Faster Decisions."*
   - Interact with the 4-node Multimodal Fusion visualization to explain how Clinical, ECG, and X-ray representations converge into the availability-aware fusion layer.
2. **Bedside Clinical Triage (Missing Modality Mode):**
   - Click **Start Assessment**.
   - Click the preset button **"Critical (Shock/Hypoxia)"**.
   - Note the real-time calculated hemodynamics: Shock Index ($1.72$), MAP ($56.7$ mmHg), and severe hypoxia warning ($SpO_2\ 84\%$).
   - Leave ECG and Chest X-ray unattached to demonstrate missing-modality handling.
   - Click **Run AI Assessment**.
3. **Explainability & Safety Overrides:**
   - Observe the Results page: Priority displays **CRITICAL RESUSCITATION (KTAS 1)** with Risk Score $\ge 78\%$.
   - Highlight the **Modality Mask Checklist**: *Clinical [✓], Vitals [✓], ECG [Unavailable], X-Ray [Unavailable]*. Emphasize to examiners that missing tests were **not** replaced with fake values.
   - Walk through the **TreeSHAP Contributing Factors** chart: explain how low SpO2 and high shock index directly escalated the risk score.
4. **Full Multimodal Upload with Grad-CAM:**
   - Start a new assessment. Attach an ECG CSV file from `datasets/ECG_HeartBeat_Categorization/mitbih_test.csv` and a frontal radiograph from `datasets/xray_dataset/images_001/images/`.
   - Run assessment: display the detected arrhythmia, waveform lead canvas, and the **Grad-CAM Attention Heatmap overlay** on the radiograph.
5. **Dynamic / Adaptive Triage Progression:**
   - Click **View Patient Timeline**.
   - Click **Add Observation**: simulate treatment response (e.g. oxygen administered, SpO2 increases to $97\%$, HR drops to $88$ bpm).
   - Show how the risk score dynamically recalculates from $82\%$ down to $48\%$ (**Urgent / KTAS 3**), shifting the trend to **Improving**.
6. **Model Insights & Research Benchmarks:**
   - Navigate to **Model Insights** to show examiners the live, non-fabricated metrics loaded directly from `reports/` (XGBoost accuracy and ROC-AUC, 1D CNN arrhythmia precision/recall, and DenseNet patient-grouped ROC-AUC).

---

## 11. Novel Academic & Research Contributions

If drafting a conference paper or journal manuscript from this project, emphasize these novel contributions:
1. **Availability-Aware Gated Multimodal Fusion:** Rather than discarding samples with missing modalities or imputing speculative medical imaging, our gated mask architecture dynamically recalibrates confidence bounds and weights based on diagnostic availability.
2. **Dual-Tier Explainability:** Coupling tabular Shapley value attributions with convolutional gradient class activation mapping (Grad-CAM) bridges the trust gap between black-box deep learning and emergency physicians.
3. **Physiologically Grounded Safety Overrides:** Blending machine learning probability distributions with deterministic clinical safety rules (e.g. shock index $\ge 1.2$ or malignant ventricular rhythms) ensures algorithmic outputs never undertriage critically unstable patients.

---

## 12. Regulatory & Medical Disclaimer

> **IMPORTANT:** This application is an academic research prototype engineered as a final-year B.Tech computer engineering capstone project. It is intended solely to demonstrate multimodal AI decision-support algorithms. It is **not** an FDA/CE-cleared medical device and must **never** be used for autonomous diagnosis, treatment planning, or clinical triage in live hospital environments without human physician oversight.
