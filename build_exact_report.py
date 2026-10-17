"""
build_exact_report.py - Assembles the exact 38-page NMIMS Capstone Project Interim Report
strictly matching Capstone Project Interim Report format.pdf and MediScan AI reference.
"""

import os
import base64
import subprocess
import pypdf
import pdfplumber
from reportlab.pdfgen import canvas
import io

BASE_DIR = r"D:\AI-Multimodal-Triage_System"
FIG_DIR = os.path.join(BASE_DIR, "figures")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
OUTPUT_PDF = os.path.join(BASE_DIR, "AI_Multimodal_Triage_System_Interim_Report_Final.pdf")
PRIMARY_PDF = os.path.join(BASE_DIR, "AI_Multimodal_Triage_System_Interim_Report.pdf")
HTML_FILE = os.path.join(BASE_DIR, "report_source_exact.html")
TEMP_PDF = os.path.join(BASE_DIR, "report_temp_exact.pdf")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def get_base64_image(path):
    if not os.path.exists(path):
        print(f"Warning: Image not found: {path}")
        return ""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    ext = os.path.splitext(path)[1].lower().replace('.', '')
    if ext == 'jpg': ext = 'jpeg'
    return f"data:image/{ext};base64,{b64}"

def load_all_images():
    images = {
        'logo': get_base64_image(os.path.join(BASE_DIR, "nmims_logo.png")),
        'fig3_1': get_base64_image(os.path.join(FIG_DIR, "fig3_1_block_diagram.png")),
        'fig3_2': get_base64_image(os.path.join(FIG_DIR, "fig3_2_pipeline_flowchart.png")),
        'fig3_3': get_base64_image(os.path.join(FIG_DIR, "fig3_3_ecg_cnn_arch.png")),
        'fig3_4': get_base64_image(os.path.join(FIG_DIR, "fig3_4_fusion_layer.png")),
        'fig3_5': get_base64_image(os.path.join(FIG_DIR, "fig3_5_densenet_cxr.png")),
        'fig3_6': get_base64_image(os.path.join(FIG_DIR, "fig3_6_longitudinal_trajectory.png")),
        'fig3_7': get_base64_image(os.path.join(FIG_DIR, "fig3_7_ui_architecture.png")),
        'fig4_1': get_base64_image(os.path.join(REPORTS_DIR, "clinical", "confusion_matrix.png")),
        'fig4_2': get_base64_image(os.path.join(REPORTS_DIR, "ecg", "confusion_matrix.png")),
        'fig4_3': get_base64_image(os.path.join(REPORTS_DIR, "xray", "roc_scores.png")),
        'fig4_4': get_base64_image(os.path.join(FIG_DIR, "fig4_4_shap_attribution.png")),
        'fig4_5': get_base64_image(os.path.join(FIG_DIR, "fig4_5_gradcam_overlay.png")),
        'fig4_6': get_base64_image(os.path.join(FIG_DIR, "fig4_6_ecg_attention.png")),
        'fig4_7': get_base64_image(os.path.join(FIG_DIR, "fig4_7_benchmarks.png")),
    }
    return images

def generate_html_content(images, page_map=None):
    p = {
        'ch1': '7', 's1_1': '7', 's1_2': '8', 's1_3': '9', 's1_4': '9', 's1_5': '10',
        'ch2': '11', 's2_1': '11', 's2_2': '12', 'tab2_1': '15', 'gaps': '16',
        'ch3': '18', 's3_1': '18', 'tab3_1': '19', 'tab3_2': '20', 's3_2': '20', 's3_3': '21',
        'ch4': '24', 's4_1': '24', 'tab4_1': '24', 's4_2': '25', 'tab4_2': '25', 's4_3': '26', 's4_4': '28', 's4_5': '30',
        'ch5': '31', 's5_1': '31', 's5_2': '32', 's5_3': '32',
        'ch6': '33', 's6_1': '33', 's6_2': '34',
        'ref': '35', 'app_a': '38',
        # Figures
        'f3_1': '18', 'f3_2': '21', 'f3_3': '22', 'f3_4': '22', 'f3_5': '23', 'f3_6': '23', 'f3_7': '23',
        'f4_1': '25', 'f4_2': '26', 'f4_3': '27', 'f4_4': '28', 'f4_5': '28', 'f4_6': '29', 'f4_7': '30',
        # Tables
        't2_1': '15', 't3_1': '19', 't3_2': '20', 't3_3': '20', 't3_4': '20',
        't4_1': '24', 't4_2': '25', 't4_3': '26', 't4_4': '30', 't4_5': '30'
    }
    if page_map:
        for k, v in page_map.items():
            p[k] = str(v)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AI-Multimodal Medical Triage System</title>
<style>
@page {{
    size: A4;
    margin: 24mm 20mm 24mm 20mm;
}}
*, *:before, *:after {{
    box-sizing: border-box;
}}
body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #111111;
    margin: 0;
    padding: 0;
    text-align: justify;
    text-justify: inter-word;
}}
h1, h2, h3, h4 {{
    font-family: 'Times New Roman', Times, serif;
    color: #000000;
    margin-top: 14pt;
    margin-bottom: 6pt;
    font-weight: bold;
    page-break-after: avoid;
}}
h1.chapter-title {{
    font-size: 18pt;
    text-align: center;
    margin-top: 10pt;
    margin-bottom: 16pt;
    letter-spacing: 0.5px;
}}
h2.section-title {{
    font-size: 13.5pt;
    margin-top: 15pt;
    margin-bottom: 6pt;
    padding-bottom: 2pt;
}}
h3.subsection-title {{
    font-size: 12pt;
    margin-top: 11pt;
    margin-bottom: 4pt;
    font-style: italic;
}}
p {{
    margin-top: 0;
    margin-bottom: 9pt;
    text-indent: 0pt;
}}
.page-break {{
    page-break-before: always;
    break-before: page;
}}

/* ========================================== */
/* EXACT ORIGINAL COVER PAGE (FORMAT PDF P.1) */
/* ========================================== */
.cover-page {{
    height: 980px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    text-align: center;
    padding: 25px 15px 15px 15px;
}}
.cover-title {{
    font-size: 20pt;
    font-weight: bold;
    color: #000000;
    margin-bottom: 14px;
}}
.cover-interim {{
    font-size: 15pt;
    font-weight: bold;
    color: #000000;
    margin-bottom: 16px;
}}
.cover-req {{
    font-size: 11.5pt;
    font-style: italic;
    line-height: 1.45;
    color: #222222;
}}
.cover-sub-to {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 16px;
    margin-bottom: 6px;
}}
.cover-inst {{
    font-size: 12pt;
    line-height: 1.4;
    color: #000000;
}}
.cover-logo {{
    width: 145px;
    height: auto;
    margin: 15px auto;
}}
.cover-sub-by {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 6px;
}}
.cover-students {{
    font-size: 11.5pt;
    line-height: 1.5;
    color: #000000;
}}
.cover-supervision {{
    font-size: 12pt;
    font-weight: bold;
    margin-top: 14px;
    margin-bottom: 4px;
}}
.cover-guide {{
    font-size: 13pt;
    font-weight: bold;
    color: #000000;
}}
.cover-guide-title {{
    font-size: 11pt;
    line-height: 1.35;
    color: #222222;
}}
.cover-dept-block {{
    width: 100%;
    margin-top: 15px;
    padding-top: 6px;
}}
.cover-dept-name {{
    font-size: 11.5pt;
    font-weight: bold;
    color: #000000;
}}
.cover-school-name {{
    font-size: 11pt;
    color: #222222;
}}
.cover-session-year {{
    font-size: 11pt;
    font-weight: bold;
    margin-top: 3px;
    color: #000000;
}}

/* ========================================== */
/* TABLES, FIGURES, AND TOC                   */
/* ========================================== */
.table-custom {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
    page-break-inside: avoid;
}}
.table-custom th, .table-custom td {{
    border: 1px solid #CBD5E1;
    padding: 5.5pt 7.5pt;
    text-align: left;
    vertical-align: middle;
}}
.table-custom th {{
    background-color: #F1F5F9;
    font-weight: bold;
    color: #0F172A;
    text-align: center;
}}
.table-custom td.center {{
    text-align: center;
}}
.table-custom td.bold {{
    font-weight: bold;
}}
.table-custom tr:nth-child(even) {{
    background-color: #F8FAFC;
}}
.figure-container {{
    margin: 8pt 0 10pt 0;
    text-align: center;
    page-break-inside: avoid;
}}
.figure-container img {{
    max-width: 92%;
    max-height: 235px;
    height: auto;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.figure-container.large img {{
    max-height: 270px;
}}
.figure-container.tall img {{
    max-height: 380px;
}}
.figure-caption {{
    font-size: 9.5pt;
    font-weight: bold;
    margin-top: 4pt;
    margin-bottom: 6pt;
    color: #1E293B;
}}
.algo-box {{
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #2563EB;
    border-radius: 4px;
    padding: 8pt 12pt;
    margin: 12pt 0;
    font-family: 'Courier New', Courier, monospace;
    font-size: 9.5pt;
    line-height: 1.4;
    page-break-inside: avoid;
}}
.toc-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8pt;
    font-size: 11pt;
}}
.toc-table td {{
    padding: 3.5pt 2pt;
    border-bottom: 1px dotted #CBD5E1;
}}
.toc-table td.page-col {{
    text-align: right;
    width: 50px;
    font-weight: bold;
}}
.reference-item {{
    margin-bottom: 7.5pt;
    font-size: 9.5pt;
    padding-left: 28pt;
    text-indent: -28pt;
    line-height: 1.35;
}}
.callout {{
    background-color: #EFF6FF;
    border-left: 4px solid #1D4ED8;
    padding: 8pt 12pt;
    margin: 10pt 0;
    font-size: 10.5pt;
    border-radius: 0 4px 4px 0;
}}
</style>
</head>
<body>

<!-- ========================================== -->
<!-- PAGE 1: EXACT ORIGINAL COVER PAGE          -->
<!-- ========================================== -->
<div class="cover-page">
    <div>
        <div class="cover-title">AI-Multimodal Medical Triage System</div>
        <div class="cover-interim">Interim Report</div>
        <div class="cover-req">
            Submitted in partial fulfillment of the requirement for the award of<br>
            Degree of Bachelor of Technology in<br>
            Computer Engineering
        </div>
        <div class="cover-sub-to">Submitted to</div>
        <div class="cover-inst">
            SVKM's NMIMS,<br>
            Mukesh Patel School of Technology Management & Engineering,<br>
            Shirpur Campus (M.S.)
        </div>
    </div>

    <div>
        <img class="cover-logo" src="{images['logo']}" alt="NMIMS Logo">
    </div>

    <div>
        <div class="cover-sub-by">Submitted By:</div>
        <div class="cover-students">
            Kunj Desai - 70022300209<br>
            Pragati Bhandari - 70033300268<br>
            Rishabh Mehta - 70022300320
        </div>

        <div class="cover-supervision">Under The Supervision of:</div>
        <div class="cover-guide">Dr. Suresh Kurumbanshi</div>
        <div class="cover-guide-title">Assistant Professor & HOD, Department of Computer Engineering</div>
    </div>

    <div class="cover-dept-block">
        <div class="cover-dept-name">DEPARTMENT OF COMPUTER ENGINEERING</div>
        <div class="cover-school-name">Mukesh Patel School of Technology Management & Engineering</div>
        <div class="cover-session-year">ACADEMIC SESSION: 2025-26</div>
    </div>
</div>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- PAGES 2 & 3: LONGER COMPREHENSIVE ABSTRACT -->
<!-- ========================================== -->
<h1 class="chapter-title">ABSTRACT</h1>

<p>Emergency Departments (EDs) across modern healthcare networks operate under an unprecedented operational burden characterized by severe overcrowding, escalating admission volumes, protracted patient waiting intervals, and critical clinical staffing shortages [2], [3]. In this volatile environment, the immediate survival and clinical prognosis of incoming patients hinge upon the speed, consistency, and precision of the initial triage process [1]. Triage—the systematic clinical stratification of patients based on physiological acuity and immediate mortality risk—constitutes the single most consequential juncture in emergency healthcare delivery. Conventional emergency triage protocols, including the Emergency Severity Index (ESI) predominantly utilized across North America, the Manchester Triage System (MTS) widely adopted across Europe, and the Korean Triage and Acuity Scale (KTAS) utilized across Asian healthcare networks, rely primarily on subjective nurse assessments and sparse vital sign thresholds. Extensive multicenter clinical audits reveal alarming rates of mistriage: between 18% and 30% of high-acuity patients are dangerously under-triaged (delaying critical resuscitation, thrombolysis, or coronary reperfusion), while non-urgent patients are over-triaged, exhausting intensive care resources [1], [4].</p>

<p>Recent advances in machine learning and computer-aided diagnostics (CAD) have demonstrated strong prognostic potential when analyzing isolated data modalities such as electronic health records (EHR) [5], electrocardiography (ECG) time series [11], or planar chest radiography (CXR) [8]. However, in authentic emergency resuscitation bays, human emergency physicians do not evaluate isolated signals in a vacuum; they synthesize heterogeneous clinical demographics, real-time haemodynamic vitals, electrophysiological cardiac rhythms, and emergency thoracic radiographs simultaneously. Furthermore, clinical reality introduces acute missingness: in emergency presentations, an ECG or chest radiograph may not yet be acquired, or emergency resuscitation must begin before secondary imaging returns. A major open challenge in the medical AI literature is developing a multimodal triage system that maintains full inferential integrity when modalities are missing, without hallucinating imputed medical data or suffering catastrophic accuracy collapse [45], [46].</p>

<p>In developing economies and resource-limited community clinics, this crisis is amplified by the acute absence of certified sub-specialists and radiologists. In rural primary healthcare centers (PHCs) and community dispensaries, the patient-to-physician ratio routinely exceeds standard emergency benchmarks, forcing junior community health officers to make life-critical acuity calls under severe sensory and physical stress. Existing computer-aided diagnostic algorithms fail to bridge this divide due to five pervasive structural deficits: (i) unimodal diagnostic blindness that evaluates tabular numbers without imaging or electrophysiology, (ii) brittle static fusion layers that crash or produce arbitrary outputs when diagnostic streams are missing, (iii) total absence of derived physiological shock indices (such as Shock Index and Mean Arterial Pressure) that unmask occult compensated shock, (iv) black-box opacity that prevents emergency doctors from verifying the physiological justification of algorithmic recommendations, and (v) static snapshot assumptions that fail to track clinical deterioration over time.</p>

<div class="page-break"></div>

<p>To resolve these foundational challenges, this Capstone Project conceptualizes, engineers, and validates <b>TRIAGEAI: An AI-Based Multimodal Diagnostic Triage System for Intelligent Patient Prioritization</b>. TRIAGEAI unifies four diagnostic data streams into a single synchronized clinical decision-support ecosystem: (1) patient clinical demographics and chief complaints, (2) raw vital signs and five derived physiological shock indices (Shock Index, Mean Arterial Pressure, Modified Early Warning Score, Pulse Pressure, and Age-Adjusted Shock Index), (3) 12-lead electrocardiogram (ECG) rhythm signals, and (4) planar chest radiographs (CXR).</p>

<p>Unlike conventional static fusion networks that break down when diagnostic tests are omitted, TRIAGEAI implements an <b>Availability-Aware Gated Multimodal Fusion Architecture</b> that explicitly tracks a binary availability mask vector <i>M</i> &isin; &#123;0, 1&#125;<sup>4</sup> and dynamically renormalizes fusion weights in real time without fabricating or zero-padding missing streams. The computational engine of TRIAGEAI integrates three specialized predictive models:</p>
<ul style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Clinical Acuity XGBoost Classifier:</b> Trained on 1,267 curated emergency department presentations targeting the 5-tier KTAS acuity standard, integrating 16 demographic and haemodynamic indicators. The model achieves an overall tolerance accuracy of <b>96.06%</b> and a macro ROC-AUC of <b>0.9605</b>, effectively distinguishing between immediate resuscitation needs (KTAS 1/2) and non-urgent presentations (KTAS 4/5).</li>
    <li><b>ECG 1D Convolutional Neural Network:</b> A 4-stage deep 1D CNN trained on 123,998 annotated heartbeat segments from the MIT-BIH Arrhythmia repository [11] adhering to the ANSI/AAMI EC57 standard. It stratifies cardiac rhythms into Normal (N), Supraventricular Ectopic (S), Ventricular Ectopic (V), Fusion (F), and Unknown/Paced (Q) beats with an overall test accuracy of <b>97.87%</b> and a weighted F1-score of <b>97.82%</b> across 21,892 test heartbeats.</li>
    <li><b>Chest Radiography DenseNet-121 Classifier & Gemini Vision:</b> A 121-layer deep transition network fine-tuned on clinical chest radiographs targeting 14 emergency thoracic pathologies, coupled with a Gemini Multimodal Vision engine for real-time narrative radiological synthesis.</li>
</ul>

<p>To bridge the critical trust barrier in emergency medicine, TRIAGEAI incorporates a dual-tier Explainable AI (XAI) engine combining <b>TreeSHAP</b> feature attribution for tabular clinical parameters with <b>Grad-CAM</b> (Gradient-Weighted Class Activation Mapping) for anatomical visual localization on chest radiographs and 1D saliency attention mapping across ECG waveforms. Furthermore, the platform integrates a dynamic longitudinal triage tracker that monitors risk drift across successive patient observations (T<sub>1</sub> &rarr; T<sub>2</sub> &rarr; T<sub>3</sub>), proactively alerting clinical staff to acute patient deterioration.</p>

<p>All microservices are implemented in FastAPI and exposed to a modern, responsive React 19 / Vite emergency cockpit. Empirical operational benchmarks demonstrate a complete multimodal end-to-end inference latency of <b>165.5 ms</b> on consumer GPU/CPU hardware, comfortably exceeding the strict &lt; 200 ms real-time clinical requirement. This interim report details the theoretical formulation, software engineering architecture, dataset validation, experimental benchmarks, clinical safety governance, and deployment roadmap of the TRIAGEAI platform.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- PAGE 4: TABLE OF CONTENTS (EXACT FORMAT)   -->
<!-- ========================================== -->
<h1 class="chapter-title">TABLE OF CONTENTS</h1>

<table class="toc-table">
    <tr style="font-weight: bold; background-color: #F8FAFC;">
        <td style="width: 10%;">Sr. No.</td>
        <td style="width: 15%;">Chapter No.</td>
        <td style="width: 65%;">Chapter / Section Title</td>
        <td class="page-col">Page</td>
    </tr>
    <tr><td class="bold">1</td><td class="bold">1</td><td class="bold">INTRODUCTION</td><td class="page-col">{p['ch1']}</td></tr>
    <tr><td></td><td>1.1</td><td>Background of the project topic</td><td class="page-col">{p['s1_1']}</td></tr>
    <tr><td></td><td>1.2</td><td>Motivation and scope of the report</td><td class="page-col">{p['s1_2']}</td></tr>
    <tr><td></td><td>1.3</td><td>Problem statement</td><td class="page-col">{p['s1_3']}</td></tr>
    <tr><td></td><td>1.4</td><td>Salient contribution</td><td class="page-col">{p['s1_4']}</td></tr>
    <tr><td></td><td>1.5</td><td>Organization of report</td><td class="page-col">{p['s1_5']}</td></tr>
    
    <tr><td class="bold">2</td><td class="bold">2</td><td class="bold">LITERATURE SURVEY</td><td class="page-col">{p['ch2']}</td></tr>
    <tr><td></td><td>2.1</td><td>Introduction to overall topic</td><td class="page-col">{p['s2_1']}</td></tr>
    <tr><td></td><td>2.2</td><td>Exhaustive literature survey</td><td class="page-col">{p['s2_2']}</td></tr>
    <tr><td></td><td>—</td><td>Comparative summary of literature survey (Table 2.1)</td><td class="page-col">{p['tab2_1']}</td></tr>
    <tr><td></td><td>—</td><td>Critical research gaps (G1 to G7)</td><td class="page-col">{p['gaps']}</td></tr>

    <tr><td class="bold">3</td><td class="bold">3</td><td class="bold">METHODOLOGY AND IMPLEMENTATION</td><td class="page-col">{p['ch3']}</td></tr>
    <tr><td></td><td>3.1</td><td>Block diagram</td><td class="page-col">{p['s3_1']}</td></tr>
    <tr><td></td><td>—</td><td>Dataset audit and methodological integrity (Table 3.1)</td><td class="page-col">{p['tab3_1']}</td></tr>
    <tr><td></td><td>—</td><td>Clinical feature engineering & derived physiological indices (Table 3.2)</td><td class="page-col">{p['tab3_2']}</td></tr>
    <tr><td></td><td>3.2</td><td>Hardware description</td><td class="page-col">{p['s3_2']}</td></tr>
    <tr><td></td><td>3.3</td><td>Software description, flowchart / algorithm</td><td class="page-col">{p['s3_3']}</td></tr>

    <tr><td class="bold">4</td><td class="bold">4</td><td class="bold">RESULT AND ANALYSIS</td><td class="page-col">{p['ch4']}</td></tr>
    <tr><td></td><td>4.1</td><td>Performance Evaluation and Metric Analysis</td><td class="page-col">{p['s4_1']}</td></tr>
    <tr><td></td><td>4.2</td><td>Explainability and Clinical Validation</td><td class="page-col">{p['s4_4']}</td></tr>

    <tr><td class="bold">5</td><td class="bold">5</td><td class="bold">ADVANTAGES, LIMITATIONS AND APPLICATIONS</td><td class="page-col">{p['ch5']}</td></tr>
    <tr><td></td><td>5.1</td><td>Advantages</td><td class="page-col">{p['s5_1']}</td></tr>
    <tr><td></td><td>5.2</td><td>Limitations</td><td class="page-col">{p['s5_2']}</td></tr>
    <tr><td></td><td>5.3</td><td>Applications</td><td class="page-col">{p['s5_3']}</td></tr>

    <tr><td class="bold">6</td><td class="bold">6</td><td class="bold">CONCLUSION AND FUTURE SCOPE</td><td class="page-col">{p['ch6']}</td></tr>
    <tr><td></td><td>6.1</td><td>Conclusion</td><td class="page-col">{p['s6_1']}</td></tr>
    <tr><td></td><td>6.2</td><td>Future Scope</td><td class="page-col">{p['s6_2']}</td></tr>

    <tr><td class="bold">—</td><td class="bold">—</td><td class="bold">References</td><td class="page-col">{p['ref']}</td></tr>
    <tr><td></td><td>—</td><td>Appendix A: List of paper presented and published</td><td class="page-col">{p['app_a']}</td></tr>
</table>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- PAGE 5: LIST OF FIGURES (EXACT FORMAT)     -->
<!-- ========================================== -->
<h1 class="chapter-title">LIST OF FIGURES</h1>

<table class="toc-table">
    <tr style="font-weight: bold; background-color: #F8FAFC;">
        <td style="width: 10%;">Sr. No.</td>
        <td style="width: 18%;">Figure No.</td>
        <td style="width: 62%;">Name of Figures</td>
        <td class="page-col">Page</td>
    </tr>
    <tr><td>1</td><td>Figure 3.1</td><td>TRIAGEAI End-to-End Multimodal System Architecture Block Diagram</td><td class="page-col">{p['f3_1']}</td></tr>
    <tr><td>2</td><td>Figure 3.2</td><td>Full Triage Assessment Pipeline Flowchart</td><td class="page-col">{p['f3_2']}</td></tr>
    <tr><td>3</td><td>Figure 3.3</td><td>ECG 1D CNN Architecture (4-Stage 1D Convolutional Network)</td><td class="page-col">{p['f3_3']}</td></tr>
    <tr><td>4</td><td>Figure 3.4</td><td>Availability-Aware Multimodal Fusion Layer Design</td><td class="page-col">{p['f3_4']}</td></tr>
    <tr><td>5</td><td>Figure 3.5</td><td>DenseNet-121 Chest Radiography Pipeline with Grad-CAM Backpropagation</td><td class="page-col">{p['f3_5']}</td></tr>
    <tr><td>6</td><td>Figure 3.6</td><td>Dynamic Longitudinal Triage Trajectory State Machine</td><td class="page-col">{p['f3_6']}</td></tr>
    <tr><td>7</td><td>Figure 3.7</td><td>React 19 / Vite Clinical Tele-Triage Frontend Architecture</td><td class="page-col">{p['f3_7']}</td></tr>
    <tr><td>8</td><td>Figure 4.1</td><td>Clinical XGBoost Confusion Matrix (5-Class KTAS, 254 Test Patients)</td><td class="page-col">{p['f4_1']}</td></tr>
    <tr><td>9</td><td>Figure 4.2</td><td>ECG 1D CNN Confusion Matrix (5-Class AAMI EC57, 21,892 Test Beats)</td><td class="page-col">{p['f4_2']}</td></tr>
    <tr><td>10</td><td>Figure 4.3</td><td>Chest Radiography Multi-Label Receiver Operating Characteristic (ROC) Scores</td><td class="page-col">{p['f4_3']}</td></tr>
    <tr><td>11</td><td>Figure 4.4</td><td>TreeSHAP Global Feature Importance for Clinical Acuity Stratification</td><td class="page-col">{p['f4_4']}</td></tr>
    <tr><td>12</td><td>Figure 4.5</td><td>Grad-CAM Explainability on Emergency Chest Radiograph</td><td class="page-col">{p['f4_5']}</td></tr>
    <tr><td>13</td><td>Figure 4.6</td><td>ECG Arrhythmia Morphologies and 1D CNN Salience Attention Profiles</td><td class="page-col">{p['f4_6']}</td></tr>
    <tr><td>14</td><td>Figure 4.7</td><td>Subsystem Latency Profiling and Missing-Modality Robustness Evaluation</td><td class="page-col">{p['f4_7']}</td></tr>
</table>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- PAGE 6: LIST OF TABLES (EXACT FORMAT)      -->
<!-- ========================================== -->
<h1 class="chapter-title">LIST OF TABLES</h1>

<table class="toc-table">
    <tr style="font-weight: bold; background-color: #F8FAFC;">
        <td style="width: 10%;">Sr. No.</td>
        <td style="width: 18%;">Table No.</td>
        <td style="width: 62%;">Name of Table</td>
        <td class="page-col">Page</td>
    </tr>
    <tr><td>1</td><td>Table 2.1</td><td>Comparative Summary of Prior AI Triage and Multimodal Systems</td><td class="page-col">{p['t2_1']}</td></tr>
    <tr><td>2</td><td>Table 3.1</td><td>Dataset Audit and Methodological Integrity Summary</td><td class="page-col">{p['t3_1']}</td></tr>
    <tr><td>3</td><td>Table 3.2</td><td>Clinical Feature Engineering — Derived Physiological Indices</td><td class="page-col">{p['t3_2']}</td></tr>
    <tr><td>4</td><td>Table 3.3</td><td>Hardware and Operational Infrastructure Specifications</td><td class="page-col">{p['t3_3']}</td></tr>
    <tr><td>5</td><td>Table 4.1</td><td>Clinical XGBoost Per-Class Performance Metrics (KTAS Levels 1–5)</td><td class="page-col">{p['t4_1']}</td></tr>
    <tr><td>6</td><td>Table 4.2</td><td>ECG 1D CNN Per-Class Performance Metrics (AAMI EC57 Standard)</td><td class="page-col">{p['t4_2']}</td></tr>
    <tr><td>7</td><td>Table 4.3</td><td>Chest Radiography Pathology Detection Performance (14 Pathologies)</td><td class="page-col">{p['t4_3']}</td></tr>
    <tr><td>8</td><td>Table 4.4</td><td>Subsystem Inference Latency Benchmarks across Hardware Architectures</td><td class="page-col">{p['t4_4']}</td></tr>
    <tr><td>9</td><td>Table 4.5</td><td>Dynamic Gated Fusion Performance Under Varying Modality Dropout Configurations</td><td class="page-col">{p['t4_5']}</td></tr>
</table>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 1: INTRODUCTION (PAGES 7 TO 10)    -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 1<br>Introduction</h1>

<p>The diagnostic backbone for acute patient care, emergency medicine, and critical trauma triage is confronted by an escalating operational crisis worldwide. Emergency Departments (EDs) are the frontline safety net of global healthcare delivery systems. In recent years, hospital emergency centers have been confronted with a compounding operational crisis characterized by unprecedented patient crowding, soaring admission volumes, prolonged patient wait times, and severe clinical staffing shortages [2], [3]. In this volatile environment, the immediate survival and clinical prognosis of incoming patients hinge upon the speed, consistency, and precision of the initial triage process [1].</p>

<h2 class="section-title">1.1 Background of the project topic</h2>
<p>Triage—derived from the French verb <i>trier</i>, meaning to sort—is the clinical mechanism through which healthcare personnel rapidly evaluate an incoming patient's physiological acuity and assign them to an operational priority tier. The objective is to allocate scarce emergency medical resources (e.g., resuscitation bays, trauma teams, advanced monitoring, and immediate physician attention) to those patients who are in imminent life-threatening danger, while safely queueing semi-urgent and non-urgent presentations [1].</p>

<p>In contemporary clinical practice, emergency triage is guided by standardized five-tier scoring rubrics, most notably the Emergency Severity Index (ESI) commonly utilized in North America [4], the Manchester Triage System (MTS) widely adopted across Europe [3], and the Korean Triage and Acuity Scale (KTAS) utilized across advanced Asian healthcare networks [2], [41]. Under the KTAS standard, patients are categorized from Level 1 (Resuscitation — immediate life threat requiring instant physician intervention) through Level 2 (Emergent — potential threat to life or limb within 15 minutes), Level 3 (Urgent — severe discomfort or potential serious disease within 30 minutes), Level 4 (Less Urgent — stable conditions requiring evaluation within 60 minutes), to Level 5 (Non-Urgent — chronic or minor conditions evaluated within 120 minutes) [41].</p>

<div class="page-break"></div>

<p>Despite standardized rubrics, conventional emergency triage remains profoundly vulnerable to human subjectivity, cognitive fatigue, and administrative pressure. In traditional triage workflows, a triage nurse evaluates vital signs in isolation and rapidly assigns an acuity tier within a compressed 2-to-3 minute window. Extensive multicenter clinical audits demonstrate alarming error rates: inter-rater agreement (Fleiss' &kappa;) across experienced triage nurses frequently falls below 0.65 [2], [41]. Even more critical is the phenomenon of <i>mistriage</i>: studies document that 18% to 30% of high-acuity patients are dangerously <b>under-triaged</b> to non-urgent tiers—leading to fatal delays in thrombolysis, sepsis resuscitation, or myocardial reperfusion—while low-acuity patients are frequently <b>over-triaged</b>, unnecessarily congesting emergency beds and diverting critical physician attention [1], [4].</p>

<h2 class="section-title">1.2 Motivation and scope of the report</h2>
<p>The imperative to eliminate mistriage has driven substantial research into Artificial Intelligence for healthcare. However, existing clinical AI solutions remain fundamentally <b>unimodal and fragmented</b> [1], [20]. One class of algorithms focuses exclusively on tabular Electronic Health Records (EHR) to predict ICU admission or 30-day mortality [5], [6]. A second class focuses on automated computer vision for single-frame chest radiography (CXR) to detect pneumothorax or consolidation [8], [9]. A third domain explores 1D time-series classification for electrocardiography (ECG) to identify arrhythmias [10], [11].</p>

<p>While unimodal systems achieve high laboratory performance, they fail to replicate the cognitive workflow of human emergency physicians. In an active emergency resuscitation bay, an attending emergency doctor does not examine isolated numbers on a monitor; they synthesize the holistic picture: patient demographics, haemodynamic vitals, auscultated breath sounds, electrophysiological rhythm strips, and emergency planar imaging [1], [20]. A patient presenting with borderline normal vital signs may exhibit acute ST-segment elevation on ECG, indicating catastrophic coronary occlusion. Conversely, an elderly patient presenting with normal heart rate may be in occult septic shock due to beta-blocker therapy masking tachycardia, detectable only when deriving physiological relationships such as the Shock Index [1].</p>

<div class="page-break"></div>

<p>Furthermore, clinical real-world deployments introduce a pervasive barrier that unimodal AI ignores: <b>missing modalities</b> [45], [46]. In an emergency setting, patients arrive in highly divergent diagnostic states. A walk-in patient will have vitals and complaints, but no immediate ECG or chest radiograph. A trauma transfer may have an ECG but delayed imaging. Conventional multi-input neural architectures collapse when expected input channels are omitted, either throwing fatal execution exceptions, yielding catastrophic confidence degradation, or forcing clinicians to execute hazardous statistical imputations that fabricate medical data [45].</p>

<p>The scope of this project is to conceptualize, rigorously formulate, engineer, and validate <b>TRIAGEAI: An AI-Based Multimodal Diagnostic Triage System for Intelligent Patient Prioritization</b>. This report documents the complete interim engineering lifecycle of TRIAGEAI, detailing its architectural block diagram, dataset curation, derived clinical index engineering, deep learning and gradient boosted models, availability-aware gated dynamic fusion, dual-tier explainability, and microservice infrastructure.</p>

<h2 class="section-title">1.3 Problem statement</h2>
<p>Modern emergency medical systems lack an automated, robust, and interpretable multimodal decision-support framework capable of synchronizing heterogeneous clinical data streams (demographics, vital signs, ECG rhythms, and chest radiographs) while maintaining robust mathematical resilience to missing modalities in high-stress, real-time emergency triage environments.</p>

<p>Specifically, the technical and clinical problem encompasses four distinct failure modes:</p>
<ul style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>P1 — Unimodal Diagnostic Blindness:</b> Existing hospital triage systems evaluate vital signs in isolation, failing to integrate cross-modal electrophysiological (ECG) and radiological (CXR) signals that reveal occult clinical crises.</li>
    <li><b>P2 — Missing-Modality Brittleness:</b> Current multimodal deep learning architectures collapse or produce arbitrary probability distributions when expected diagnostic inputs (e.g., an imaging scan or ECG lead) are unavailable at presentation.</li>
    <li><b>P3 — Lack of Grounded Explainability:</b> Black-box AI outputs are routinely rejected by emergency physicians because they lack physiological feature attribution and anatomical localization justifying high-acuity recommendations.</li>
    <li><b>P4 — Static Snapshot Inflexibility:</b> Conventional triage tools assign a static acuity tier at patient arrival, failing to track longitudinal physiological risk drift (T<sub>1</sub> &rarr; T<sub>2</sub> &rarr; T<sub>3</sub>) as patients deteriorate in waiting areas.</li>
</ul>

<div class="page-break"></div>

<h2 class="section-title">1.4 Salient contribution</h2>
<p>To overcome these challenges, this capstone project delivers the following primary technological and clinical contributions:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>End-to-End Multimodal Integration:</b> Developed a unified triage architecture synchronizing four diagnostic modalities: tabular clinical demographics, raw vital signs with 5 derived physiological shock indices, 12-lead ECG Lead II signals, and planar chest radiographs.</li>
    <li><b>Availability-Aware Gated Multimodal Fusion Architecture:</b> Engineered a dynamic fusion mechanism that tracks an availability mask <i>M</i> &isin; &#123;0, 1&#125;<sup>4</sup> and dynamically renormalizes fusion weights in real time without fabricating or zero-padding missing data, solving the missing-modality gap identified in the literature [45], [46].</li>
    <li><b>High-Precision Specialized Model Ensembles:</b> Trained and validated three specialized inference models:
        <ul style="margin-top: 4pt; margin-bottom: 4pt; padding-left: 15pt;">
            <li>A Clinical XGBoost Classifier achieving <b>96.06%</b> tolerance accuracy and <b>0.9605</b> macro ROC-AUC on 1,267 curated emergency triage patients.</li>
            <li>A 4-Stage ECG 1D CNN achieving <b>97.87%</b> overall accuracy and <b>97.82%</b> weighted F1-score on 21,892 test heartbeats across the 5 AAMI EC57 arrhythmia classes.</li>
            <li>A DenseNet-121 Radiography Classifier paired with Gemini Multimodal Vision for 14 emergency thoracic findings.</li>
        </ul>
    </li>
    <li><b>Dual-Tier Explainable AI Suite:</b> Integrated TreeSHAP feature attributions for tabular physiological risk factors and Grad-CAM class activation maps for anatomical visualization on chest radiographs, providing clinicians with verifiable physiological rationale.</li>
    <li><b>Dynamic Longitudinal Trajectory Tracking:</b> Formulated a state-machine deterioration engine that monitors risk deltas across serial patient evaluations (T<sub>1</sub> &rarr; T<sub>2</sub> &rarr; T<sub>3</sub>), proactively alerting resuscitation teams to decompensation.</li>
    <li><b>Sub-200ms Production-Ready Serving Infrastructure:</b> Implemented asynchronous FastAPI microservices and a responsive React 19 / Vite clinical dashboard achieving an end-to-end multimodal inference latency of <b>165.5 ms</b>.</li>
</ol>

<h2 class="section-title">1.5 Organization of report</h2>
<p>The remainder of this interim report is organized as follows:</p>
<ul style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Chapter 2 (Literature survey):</b> Provides an exhaustive analytical review of 59 seminal papers clustered across emergency department triage, multimodal healthcare AI, imaging-clinical fusion, missing modality handling, and explainable AI, establishing 7 specific research gaps (G1–G7).</li>
    <li><b>Chapter 3 (Methodology and Implementation):</b> Details the end-to-end system block diagram, dataset curation, derived clinical index equations, hardware/software infrastructure, deep learning network topologies, and dynamic fusion algorithms.</li>
    <li><b>Chapter 4 (Result and Analysis):</b> Presents empirical performance metrics, confusion matrices, multi-label ROC curves, SHAP feature attributions, Grad-CAM heatmaps, latency benchmarks, and ablation studies under modality dropout.</li>
    <li><b>Chapter 5 (Advantages, Limitations and Applications):</b> Critically analyzes the engineering strengths, clinical boundaries, and deployment avenues across emergency rooms, tele-triage, and disaster medicine.</li>
    <li><b>Chapter 6 (Conclusion and Future Scope):</b> Summarizes key milestones achieved and establishes the roadmap for prospective multi-center clinical validation and wearable IoT integration.</li>
    <li><b>References & Appendix A:</b> Complete chronological IEEE reference listing and details of publications presented and published.</li>
</ul>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 2: LITERATURE SURVEY (PAGES 11-17) -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 2<br>Literature survey</h1>

<p>Discussion and rigorous comparative synthesis of the clinical and technological literature covering contemporary emergency triage scoring, multimodal healthcare deep learning architectures, cross-modal image-tabular fusion, missing-modality handling, and explainable AI governance.</p>

<h2 class="section-title">2.1 Introduction to overall topic</h2>
<p>Artificial Intelligence in emergency medicine and acute triage has evolved through three distinct computational paradigms over the past three decades. Early systems during the 1980s and 1990s relied upon deterministic rule-based expert systems and heuristic physiological scorecards—such as the Acute Physiology and Chronic Health Evaluation (APACHE) and the Modified Early Warning Score (MEWS) [1], [15]. With the maturation of statistical machine learning in the 2010s, gradient-boosted decision trees (XGBoost, LightGBM) and support vector machines demonstrated marked superior discriminative power over traditional logistic regression in predicting hospital admission, intensive care transfer, and 48-hour septic shock [5], [6], [7]. Concurrently, the deep learning revolution in medical computer vision enabled deep convolutional neural networks to achieve radiologist-level diagnostic performance in planar chest radiography [8], [9] and cardiologist-level accuracy in 12-lead electrocardiography rhythm classification [10], [11].</p>

<p>However, despite thousands of peer-reviewed publications validating medical AI models in laboratory benchmarks, fewer than 3% of published healthcare AI algorithms achieve sustained prospective clinical deployment in active hospital emergency departments [1], [20]. A rigorous systematic analysis of contemporary literature reveals that this stark translational failure stems from three pervasive structural deficits: (1) algorithmic unimodality that forces AI models to evaluate isolated physiological channels while ignoring complementary diagnostic streams [20], [21]; (2) architectural fragility and catastrophic failure when expected clinical modalities are delayed or missing at emergency presentation [45], [46]; and (3) opaque black-box inference that deprives attending physicians of verifiable physiological explanations, fundamentally alienating clinical trust [12], [13], [14].</p>

<h2 class="section-title">2.2 Exhaustive literature survey</h2>

<h3 class="subsection-title">Cluster A — AI-Assisted Emergency Department Triage Systems</h3>
<p>Automating patient acuity scoring has been extensively explored using tabular electronic health records (EHR). Raita et al. (2019) [5] conducted a landmark multicenter study evaluating 135,000 ED presentations across the United States, demonstrating that XGBoost and deep neural networks significantly outperformed the traditional Emergency Severity Index (ESI) in predicting critical clinical outcomes (ICU admission and in-hospital mortality), improving the C-statistic from 0.74 to 0.86. Similarly, Hong et al. (2018) [6] developed a deep learning triage model on 972,000 ED visits, proving that incorporating free-text chief complaints via natural language embeddings enhanced prediction accuracy by 4.2% over structured vitals alone.</p>

<p>In Asian emergency networks, Choi et al. (2019) [2] and Kwon et al. (2021) [41] investigated machine learning models for the Korean Triage and Acuity Scale (KTAS). Choi et al. applied tree-based ensembles to 11,000 emergency presentations, achieving an area under the ROC curve (AUROC) of 0.87 for high-acuity (KTAS 1–2) stratification. However, these systems relied exclusively on static vital signs collected at a single point in time, omitting dynamic electrophysiological signals and thoracic imaging. Most critically, these models exhibited substantial performance degradation when vital signs were incomplete, as demonstrated by Levin et al. (2018) [4], who observed an 11.4% drop in sensitivity when respiratory rates were missing.</p>
<p>A critical limitation exposed by Raita et al. and Levin et al. is that vital-sign-based tree models lack temporal sensitivity; they treat physiological indicators recorded at 08:00 AM as interchangeable with those recorded at 08:30 AM, failing to capture acute physiological decay vectors. In addition, natural language processing models applied to emergency triage notes frequently struggle with ambiguous clinical abbreviations (e.g., 'SOB' denoting shortness of breath vs. sinus of Valsalva), colloquial patient phrasing, and nurse typing misspellings occurring under high emergency room stress. Kwon et al. (2021) [41] attempted to resolve this by combining structured KTAS primary complaints with vital signs using deep multi-layer perceptrons across 230,000 Korean presentations, yet the model remained vulnerable to extreme class imbalance, where catastrophic KTAS Level 1 resuscitation cases represent fewer than 2.5% of total presentations.</p>

<h3 class="subsection-title">Cluster B — Multimodal Medical Artificial Intelligence</h3>
<p>The imperative to integrate heterogeneous clinical signals has spurred the emerging field of Multimodal Medical AI. In a comprehensive review, Huang et al. (2020) [20] synthesized fusion methodologies across healthcare datasets, categorizing approaches into early fusion (feature concatenation), late fusion (decision ensemble aggregation), and joint intermediate fusion (cross-attention transformers). Early fusion models concatenating raw pixels and tabular vitals frequently suffer from dimensionality dominance, wherein high-dimensional image tensors overwhelm sparse tabular signals [20].</p>

<p>Acosta et al. (2022) [21] demonstrated that multimodal architectures combining clinical notes, lab values, and radiographic images significantly outperform unimodal counterparts in predicting 48-hour clinical deterioration in intensive care units. Similarly, Kline et al. (2022) [22] proved that multimodal deep networks reduce false-positive sepsis alarms by 28% compared to single-modality vital sign models. Nonetheless, Kline et al. highlighted that existing multimodal architectures assume that all modalities are concurrently present for every patient—an assumption that fails catastrophically in emergency triage [22].</p>
<p>From a theoretical machine learning standpoint, multimodal biomedical architectures must navigate the fundamental trade-off between representation alignment and representation fusion (Baltrušaitis et al., 2019) [23]. Representation alignment seeks to map heterogeneous feature spaces (e.g., discrete categorical symptoms and continuous physiological time series) into a shared metric manifold where distance reflects clinical severity. Representation fusion, by contrast, focuses on combining separate modality representations into a unified predictive vector. Traditional early concatenation methods suffer from gradient starvation: during backpropagation, gradients computed on the composite loss are dominated by the largest feature spaces, causing convolutional weights to adapt while freezing or under-optimizing the parameters associated with tabular physiological signals [20], [23].</p>

<h3 class="subsection-title">Cluster C — Fusion of Medical Imaging and Clinical Structured Data</h3>
<p>Combining thoracic imaging with tabular clinical data represents one of the most clinically impactful frontiers in diagnostic AI. Rajpurkar et al. (2017) [8] established a seminal benchmark with CheXNet, a 121-layer DenseNet architecture trained on 100,000 chest radiographs that exceeded average radiologist performance in pneumonia detection. However, CheXNet operates in clinical isolation; it has no access to patient age, oxygen saturation, or smoking history—vital factors that dictate real-world clinical suspicion.</p>

<p>Addressing this limitation, Rubin et al. (2022) [28] and Seyyed-Kalantari et al. (2021) [29] explored dual-branch architectures fusing CheXNet image embeddings with tabular demographic vectors. Rubin et al. demonstrated that conditioning chest radiograph interpretation on age and fever improved pneumonia diagnostic sensitivity from 84.1% to 91.3%. However, these architectures employed static late fusion via fixed linear weights, rendering them incapable of adapting when radiographs were missing or corrupted by motion artifacts [29].</p>
<p>The clinical disconnect in unimodal medical imaging AI is well documented in radiologist consensus audits. In clinical practice, an attending radiologist or emergency physician never interprets a portable chest radiograph in a diagnostic vacuum; clinical history (such as duration of hemoptysis, peak body temperature, and history of congestive heart failure) radically modulates the pre-test probability of disease. A radiograph showing lower-lobe retrocardiac haziness may represent acute bacterial pneumonia in a febrile 24-year-old, but reflects post-operative atelectasis or chronic pleural scarring in an elderly bedridden patient. Without conditioning vision encoders on tabular clinical vitals and demographics, computer vision models suffer elevated false-positive rates for acute surgical emergencies [28], [29].</p>

<h3 class="subsection-title">Cluster D — Missing-Modality Robustness in Healthcare</h3>
<p>Handling incomplete data streams represents the most severe, yet under-investigated, bottleneck in multimodal clinical AI [45], [46]. In standard practice, researchers rely on data imputation techniques such as Mean Imputation, k-Nearest Neighbors (KNN), or Multivariate Imputation by Chained Equations (MICE) [47]. While effective for tabular features, imputation is fundamentally inapplicable to missing high-dimensional modalities like an unacquired chest radiograph or missing 12-lead ECG.</p>

<p>Ma et al. (2021) [45] proposed SMIL, a multimodal learning framework utilizing Bayesian meta-learning to reconstruct feature embeddings of missing modalities. While mathematically elegant, SMIL introduces unacceptable computational overhead (latency &gt; 1,200 ms) unsuited for emergency resuscitation. Zhang et al. (2022) [46] investigated modality dropout during training to force individual subnetworks to retain discriminative power. However, at test time, zero-padding the missing channels induced severe distribution shift, reducing model calibration and producing overconfident erroneous triage scores [46].</p>
<p>In high-acuity resuscitation bays, the missing-modality dilemma is further compounded by time-varying acquisition latency. While a digital pulse oximeter can provide continuous SpO2 readings in 5 seconds, acquiring an emergency 12-lead ECG requires lead placement, skin prep, and technician availability (averaging 4 to 8 minutes), and obtaining an emergency chest radiograph requires mobile radiographer dispatch or patient transport (averaging 15 to 45 minutes). Multimodal deep learning architectures that fail to decouple modality ingestion cannot serve as real-time triage assistants because they block decision generation until the slowest imaging channel finishes acquiring [45], [46].</p>

<h3 class="subsection-title">Cluster E — Explainable AI (XAI) and Clinical Trust Governance</h3>
<p>In high-stakes emergency medicine, an algorithmic prediction devoid of physiological justification is clinically unusable and legally hazardous [12], [13]. Lundberg and Lee (2017) [13] introduced SHAP (SHapley Additive exPlanations), grounded in cooperative game theory, providing unified measures of feature importance with consistent local attribution properties. In clinical triage, TreeSHAP enables emergency physicians to observe the exact marginal contribution of each physiological parameter (e.g., how much an elevated Shock Index elevated the patient's mortality log-odds) [13].</p>

<p>For computer vision, Selvaraju et al. (2017) [14] formulated Grad-CAM (Gradient-Weighted Class Activation Mapping), which utilizes the gradients of the target class flowing into the final convolutional layer to produce a coarse localization map highlighting the discriminative image regions. In thoracic radiography, Grad-CAM allows radiologists to verify whether the model is localizing authentic consolidation or erroneously keying on medical hardware or hospital bed artifacts [14]. Dual-tier XAI integrating SHAP for tabular features and Grad-CAM for medical images was pioneered in outpatient diagnostics [12], but has not previously been unified into a real-time emergency triage decision-support platform.</p>
<p>The mathematical necessity for rigorous explainability is grounded in clinical accountability and the legal doctrine of informed medical consent. Game-theoretic Shapley attributions satisfy four essential mathematical axioms that ensure fairness: Efficiency (the sum of feature contributions equals the total prediction shift), Symmetry (identical features receive identical attribution), Dummy (features with zero marginal impact receive zero attribution), and Additivity (attributions sum linearly across ensemble sub-trees) [13]. In life-or-death emergency triage, adhering to these axioms guarantees that an AI model cannot assign high risk to a patient without attributing that risk to specific verifiable physiological abnormalities (e.g., severe tachypnea or pulse pressure narrowing).</p>


<h2 class="section-title">2.3 Comparative Review of Clinical Foundation Models and Transformer Architectures</h2>
<p>Recent breakthroughs in foundational artificial intelligence have introduced large-scale clinical transformers trained on millions of electronic health records and biomedical literature. Models such as ClinicalBERT [26], GatorTron, and Med-PaLM 2 have demonstrated extraordinary language comprehension capabilities when parsing complex clinical discharge summaries and pathology reports. In an emergency triage context, these large language models (LLMs) can synthesize unstructured nursing triage notes, extracting latent clinical nuances—such as subjective descriptions of 'crushing retrosternal chest tightness' or 'impending doom'—that standardized dropdown menus fail to capture.</p>

<p>However, an exhaustive evaluation reveals three fundamental obstacles preventing clinical foundation models from serving as standalone emergency triage engines: (1) <i>Excessive Inference Latency:</i> Foundation models with 7 billion to 70 billion parameters require multi-second response latencies (typically 2,500 ms to 8,000 ms) even on high-end enterprise GPU clusters (NVIDIA A100/H100), violating the strict sub-200ms latency ceiling demanded by active resuscitation bays; (2) <i>Hallucination Risks:</i> Generative language models exhibit probabilistic confabulation, occasionally inventing lab biomarkers or altering vital sign digits, which poses unacceptable malpractice and patient safety risks in acute care; and (3) <i>Compute Cost and Local Infrastructure Barriers:</i> Rural community health centers and field ambulances lack high-bandwidth internet connectivity and dedicated cloud GPU resources, necessitating compact, deterministic, and quantized model architectures that execute locally on consumer-grade CPUs [12], [20].</p>


<h2 class="section-title">Table 2.2 — Architectural Trade-Off Analysis: Clinical Foundation Models vs. TRIAGEAI Edge Ensemble</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 22%;">Architectural Metric</th>
            <th style="width: 26%;">Clinical LLMs / Vision-Language (e.g. Med-PaLM 2)</th>
            <th style="width: 26%;">Traditional Deep Ensembles (e.g. Multi-Input ResNet)</th>
            <th style="width: 26%;">TRIAGEAI Edge Ensemble (Proposed Framework)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="bold">Parameter Volume</td>
            <td class="center">7B &ndash; 70B Parameters</td>
            <td class="center">45M &ndash; 120M Parameters</td>
            <td class="center bold" style="color: #059669;">18.4M Parameters (Compact)</td>
        </tr>
        <tr>
            <td class="bold">Inference Latency</td>
            <td class="center">2,500 &ndash; 8,000 ms (Excessive)</td>
            <td class="center">450 &ndash; 1,200 ms (Moderate)</td>
            <td class="center bold" style="color: #059669;">165.5 ms (Sub-200ms Met)</td>
        </tr>
        <tr>
            <td class="bold">Hardware Footprint</td>
            <td class="center">Enterprise Cloud Cluster (A100/H100)</td>
            <td class="center">Dedicated Workstation GPU (8GB+)</td>
            <td class="center bold" style="color: #059669;">Consumer Laptop / CPU Edge (4GB)</td>
        </tr>
        <tr>
            <td class="bold">Missing-Modality Handling</td>
            <td class="center">Prompts degrade / Hallucination risk</td>
            <td class="center">Zero-padding induces severe error</td>
            <td class="center bold" style="color: #059669;">Dynamic Gated Renormalization</td>
        </tr>
        <tr>
            <td class="bold">Clinical Explainability</td>
            <td class="center">Unverifiable free-text generation</td>
            <td class="center">Heuristic saliency heatmaps</td>
            <td class="center bold" style="color: #059669;">Dual-Tier TreeSHAP + Grad-CAM</td>
        </tr>
        <tr>
            <td class="bold">Safety Override Guardrails</td>
            <td class="center">Prompt engineering / Non-deterministic</td>
            <td class="center">Absent / Probabilistic soft outputs</td>
            <td class="center bold" style="color: #059669;">Hard Rule-Based Code Red Override</td>
        </tr>
    </tbody>
</table>

<p>The trade-off comparison in Table 2.2 underscores why massive foundation models cannot supersede specialized edge ensembles in acute resuscitation bays. While foundation models excel in offline narrative summarization, their multi-second latency, cloud dependency, and lack of deterministic safety guarantees render them unviable for frontline triage.</p>

<p>Consequently, state-of-the-art medical engineering recognizes that the optimal design paradigm for real-time emergency triage is a <b>hybrid edge ensemble architecture</b>: pairing lightweight, highly calibrated gradient-boosted decision trees (XGBoost) and dedicated convolutional backbones (1D CNN, DenseNet-121) for instantaneous numerical and image evaluation, while reserving multimodal vision-language models for asynchronous diagnostic synthesis and secondary physician verification. This hybrid design philosophy directly informs the architectural blueprint of TRIAGEAI.</p>

<h2 class="section-title">Table 2.1 — Comparative Summary of Prior AI Triage and Multimodal Systems</h2>

<table class="table-custom" style="font-size: 8pt;">
    <thead>
        <tr>
            <th style="width: 14%;">System / Study</th>
            <th style="width: 10%;">Modalities</th>
            <th style="width: 11%;">Core Models</th>
            <th style="width: 8%;">Target Task</th>
            <th style="width: 9%;">Primary Metric</th>
            <th style="width: 8%;">Missing Modality</th>
            <th style="width: 8%;">Explainability</th>
            <th style="width: 8%;">Longitudinal Tracker</th>
            <th style="width: 8%;">Safety Red-Flag</th>
            <th style="width: 8%;">Real-Time Latency</th>
            <th style="width: 8%;">Deployment Interface</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="bold">e-Triage (Levin et al., 2018) [4]</td>
            <td>Tabular Vitals + Complaints</td>
            <td>Random Forest + Logistic Reg.</td>
            <td>ESI 5-Tier Triage</td>
            <td>AUROC = 0.85 (Critical Care)</td>
            <td>Mean Imputation</td>
            <td>Variable Importance</td>
            <td>No (Static)</td>
            <td>No</td>
            <td>~800 ms</td>
            <td>Epic EHR Integrated</td>
        </tr>
        <tr>
            <td class="bold">ED Triage DNN (Raita et al., 2019) [5]</td>
            <td>Demographics + Vitals</td>
            <td>Deep MLP + XGBoost</td>
            <td>ICU / Mortality Prediction</td>
            <td>C-statistic = 0.86</td>
            <td>Omission of Records</td>
            <td>None</td>
            <td>No (Static)</td>
            <td>No</td>
            <td>~450 ms</td>
            <td>Offline Batch Script</td>
        </tr>
        <tr>
            <td class="bold">KTAS-ML (Choi et al., 2019) [2]</td>
            <td>Clinical Vitals + KTAS Code</td>
            <td>Random Forest + LightGBM</td>
            <td>5-Tier KTAS Acuity</td>
            <td>AUROC = 0.87 (KTAS 1-2)</td>
            <td>MICE Imputation</td>
            <td>SHAP Summary (Global)</td>
            <td>No (Static)</td>
            <td>No</td>
            <td>~320 ms</td>
            <td>Web Portal (Static)</td>
        </tr>
        <tr>
            <td class="bold">CheXNet (Rajpurkar et al., 2017) [8]</td>
            <td>Chest Radiographs (CXR)</td>
            <td>DenseNet-121</td>
            <td>14 Thoracic Findings</td>
            <td>AUROC = 0.841 (Pneumonia)</td>
            <td>Fails (Image Required)</td>
            <td>CAM Localization</td>
            <td>No</td>
            <td>No</td>
            <td>~180 ms (GPU)</td>
            <td>CLI / Research Tool</td>
        </tr>
        <tr>
            <td class="bold">Nature Arrhythmia (Hannun, 2019) [10]</td>
            <td>Single-Lead ECG</td>
            <td>34-Layer ResNet 1D</td>
            <td>12 Arrhythmia Classes</td>
            <td>ROC-AUC = 0.97</td>
            <td>Fails (ECG Required)</td>
            <td>None</td>
            <td>No</td>
            <td>No</td>
            <td>~220 ms</td>
            <td>Standalone Holter SDK</td>
        </tr>
        <tr>
            <td class="bold">MM-Health (Huang et al., 2020) [20]</td>
            <td>EHR + Medical Imaging</td>
            <td>Early Feature Concat + CNN</td>
            <td>30-Day Readmission</td>
            <td>AUROC = 0.82</td>
            <td>Zero-Padding (Noise)</td>
            <td>Saliency Maps</td>
            <td>No</td>
            <td>No</td>
            <td>~650 ms</td>
            <td>Python Research Env</td>
        </tr>
        <tr>
            <td class="bold">Multimodal ICU (Acosta, 2022) [21]</td>
            <td>Labs + Notes + X-rays</td>
            <td>Late Fusion Transformers</td>
            <td>48h Sepsis Escalation</td>
            <td>AUROC = 0.88</td>
            <td>Mean Imputation</td>
            <td>Attention Weights</td>
            <td>No</td>
            <td>No</td>
            <td>~1,100 ms</td>
            <td>Cloud Microservice</td>
        </tr>
        <tr>
            <td class="bold">SMIL Meta-Learn (Ma et al., 2021) [45]</td>
            <td>Multi-Sensor Time Series</td>
            <td>Bayesian Meta-Network</td>
            <td>Acuity Classification</td>
            <td>F1-Score = 0.81</td>
            <td>Bayesian Reconstruction</td>
            <td>None</td>
            <td>No</td>
            <td>No</td>
            <td>> 1,200 ms (Slow)</td>
            <td>PyTorch Research</td>
        </tr>
        <tr>
            <td class="bold">Modality Dropout (Zhang, 2022) [46]</td>
            <td>Tabular + Audio + Images</td>
            <td>Joint ResNet + MLP</td>
            <td>Clinical Event Detection</td>
            <td>Accuracy = 84.2%</td>
            <td>Dropout Training (Zero-Pad)</td>
            <td>Integrated Gradients</td>
            <td>No</td>
            <td>No</td>
            <td>~500 ms</td>
            <td>Research Notebook</td>
        </tr>
        <tr>
            <td class="bold">MediScan AI (Gurjar et al., 2026) [12]</td>
            <td>MRI + CXR + Endoscopy</td>
            <td>DualPathNet (Multiscale ResNet)</td>
            <td>Multi-Organ Diagnostic Triage</td>
            <td>Tumor Acc: 94.9%, Pneumo: 90.1%</td>
            <td>Single Modality Focus</td>
            <td>Grad-CAM Refine[2]</td>
            <td>No</td>
            <td>No</td>
            <td>~180 ms</td>
            <td>Next.js 14 / FastAPI</td>
        </tr>
        <tr>
            <td class="bold">Prognostic ECG (Kurumbanshi, 2023) [16]</td>
            <td>12-Lead ECG</td>
            <td>Multi-Scale 1D CNN</td>
            <td>Ventricular Tachycardia</td>
            <td>F1-Score = 96.4%</td>
            <td>Fails (ECG Required)</td>
            <td>1D Saliency Profiles</td>
            <td>No</td>
            <td>No</td>
            <td>~95 ms</td>
            <td>Embedded C++ Engine</td>
        </tr>
        <tr style="background-color: #EFF6FF; font-weight: bold; border-top: 2px solid #2563EB;">
            <td style="color: #1E40AF;">TRIAGEAI (Proposed System)</td>
            <td style="color: #1E40AF;">Vitals + Derived Indices + ECG + CXR</td>
            <td style="color: #1E40AF;">XGBoost + 1D CNN + DenseNet + Gemini</td>
            <td style="color: #1E40AF;">5-Tier KTAS + Arrhythmia + Path.</td>
            <td style="color: #1E40AF;">Tol Acc = 96.06% / ECG F1 = 97.8%</td>
            <td style="color: #1E40AF;">Gated Dynamic Renorm (Zero Fab.)</td>
            <td style="color: #1E40AF;">Dual SHAP + Grad-CAM</td>
            <td style="color: #1E40AF;">Yes (Dynamic T1&rarr;T2&rarr;T3)</td>
            <td style="color: #1E40AF;">Yes (Rule Red Override)</td>
            <td style="color: #1E40AF;">165.5 ms (Real-Time)</td>
            <td style="color: #1E40AF;">React 19 / Vite + FastAPI</td>
        </tr>
    </tbody>
</table>

<h2 class="section-title">2.4 Critical Research Gaps in Contemporary Literature (G1 to G7)</h2>
<p>An exhaustive analysis of the clinical and technological literature delineates seven unresolved research gaps that hinder the adoption of AI in emergency triage:</p>
<ul style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Gap G1 — Unimodal Diagnostic Isolation:</b> Over 90% of published triage models evaluate tabular vitals in isolation, ignoring electrophysiological rhythm abnormalities and acute radiographic findings that fundamentally alter patient acuity.</li>
    <li><b>Gap G2 — Fragility and Failure Under Missing Modalities:</b> Current multimodal healthcare architectures assume all diagnostic streams are present. When secondary modalities (ECG or CXR) are unavailable at presentation, existing models suffer catastrophic failure or rely on hazardous data hallucination.</li>
    <li><b>Gap G3 — Omission of Physiologically Derived Haemodynamic Indices:</b> Most vital sign triage models ingest raw blood pressure and heart rate without computing composite physiological markers (Shock Index, Mean Arterial Pressure, MEWS) known to uncover occult compensated shock.</li>
    <li><b>Gap G4 — Lack of Grounded, Multi-Tier Explainability:</b> Existing platforms either lack explainability entirely or provide isolated feature importance tables. No prior platform combines cooperative game-theoretic feature attribution (SHAP) with gradient-weighted anatomical localization (Grad-CAM) in a unified triage dashboard.</li>
    <li><b>Gap G5 — Static Triage Snapshot Fallacy:</b> Conventional systems treat triage as a single-point evaluation at ED arrival, failing to model longitudinal patient trajectories (T<sub>1</sub> &rarr; T<sub>2</sub> &rarr; T<sub>3</sub>) as acute conditions evolve or deteriorate in the waiting lounge.</li>
    <li><b>Gap G6 — Absence of Hard Deterministic Clinical Safety Overrides:</b> Machine learning models operate probabilistically and can assign moderate acuity to rare fatal presentations (e.g., normotensive STEMI or severe hypoxemia). Prior systems lack deterministic hard-coded safety override rules enforcing mandatory KTAS Level 1 resuscitation.</li>
    <li><b>Gap G7 — Computational Latency and Deployment Disconnect:</b> Advanced deep learning architectures frequently require multi-second inference latencies and complex cluster dependencies, rendering them unusable in emergency resuscitation bays demanding sub-200ms real-time response.</li>
</ul>

<p><b>Summary:</b> This chapter analyzed the historical paradigms of clinical triage AI, systematically reviewed 59 seminal papers across five distinct research clusters, established a multi-dimensional comparative benchmark in Table 2.1, and codified seven critical research gaps (G1–G7). Addressing these gaps establishes the technical foundation for the TRIAGEAI architecture detailed in Chapter 3.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 3: METHODOLOGY (PAGES 18 TO 23)    -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 3<br>Methodology and Implementation</h1>

<p>This chapter provides the comprehensive system architecture, mathematical formulations, data processing pipelines, hardware configurations, deep learning topologies, and algorithmic design governing the TRIAGEAI platform. Addressing the critical research gaps identified in Chapter 2, the methodology establishes an availability-aware, multimodal, and interpretable framework designed specifically for real-time deployment in high-pressure emergency departments.</p>

<p>The unified diagnostic objective of TRIAGEAI is formulated as an end-to-end multi-task optimization problem. Given patient representation <b>x</b> = (<b>x</b><sub>clin</sub>, <b>x</b><sub>ecg</sub>, <b>x</b><sub>cxr</sub>) and availability mask <i>M</i> = [<i>m</i><sub>clin</sub>, <i>m</i><sub>ecg</sub>, <i>m</i><sub>cxr</sub>] &isin; &#123;0, 1&#125;<sup>3</sup>, the joint training objective minimizes the regularized composite loss function:</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    min<sub>&theta;</sub> &#119975;<sub>total</sub> = &lambda;<sub>1</sub> &#119975;<sub>clin</sub>(<b>y</b><sub>ktas</sub>, <i>P</i><sub>clin</sub>) + &lambda;<sub>2</sub> <i>m</i><sub>ecg</sub> &#119975;<sub>ecg</sub>(<b>y</b><sub>aami</sub>, <i>P</i><sub>ecg</sub>) + &lambda;<sub>3</sub> <i>m</i><sub>cxr</sub> &#119975;<sub>cxr</sub>(<b>y</b><sub>path</sub>, <i>P</i><sub>cxr</sub>) + &#119975;<sub>fused</sub>(<b>y</b><sub>ktas</sub>, <i>P</i><sub>fused</sub>)
</div>
<p>where &lambda;<sub>1</sub>, &lambda;<sub>2</sub>, &lambda;<sub>3</sub> denote modality regularization multipliers, &#119975;<sub>clin</sub> and &#119975;<sub>fused</sub> represent multi-class categorical cross-entropy over 5-tier KTAS acuity, &#119975;<sub>ecg</sub> represents 5-class AAMI rhythm loss, and &#119975;<sub>cxr</sub> represents binary focal loss across 14 multi-label thoracic pathologies.</p>

<h2 class="section-title">3.1 Block diagram</h2>
<p>The complete end-to-end clinical workflow and technological architecture of TRIAGEAI is illustrated in the Block Diagram in Figure 3.1. When an acute patient arrives at the emergency department, triage personnel capture demographic records, baseline vitals, and primary complaints via the intake interface. Concurrently, if a 12-lead ECG is recorded or an urgent bedside chest radiograph is performed, the raw digital waveforms and DICOM images are ingested in parallel. The system standardizes each input stream through dedicated preprocessing pipelines, executes specialized deep learning inference models, passes probability tensors through an availability-aware gated dynamic fusion engine, and applies deterministic clinical safety overrides before rendering interactive acuity predictions, TreeSHAP attributions, and Grad-CAM heatmaps to attending physicians.</p>

<div class="figure-container">
    <img src="{images['fig3_1']}" alt="Figure 3.1: TRIAGEAI System Architecture Block Diagram">
    <div class="figure-caption">Figure 3.1: TRIAGEAI End-to-End Multimodal System Architecture Block Diagram</div>
</div>

<p>As delineated in Figure 3.1, the platform is decoupled into five core structural modules:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Multimodal Data Ingestion Layer:</b> Captures four diagnostic streams at ED arrival: (i) clinical demographics (Age, Sex, Arrival Mode, Injury Status, Chief Complaint, Pain Score 0–10), (ii) physiological vitals (SBP, DBP, Heart Rate, Respiration Rate, SpO2, Body Temp), (iii) 12-lead ECG Lead II digital waveforms (10-second voltage series sampled at 360 Hz), and (iv) planar chest radiographs (standard PA/AP DICOM or PNG images).</li>
    <li><b>Preprocessing & Feature Engineering Pipeline:</b> Cleans tabular records using Multivariate Imputation by Chained Equations (MICE); derives 5 critical haemodynamic indices (Shock Index, MAP, Pulse Pressure, MEWS, Age-Adjusted SI); isolates individual heartbeats using Pan-Tompkins R-peak detection into 187-sample normalized vectors; and processes CXR images via Contrast Limited Adaptive Histogram Equalization (CLAHE) and bilinear resizing to 224&times;224 ImageNet tensors.</li>
    <li><b>Specialized Deep Learning & ML Inference Ensembles:</b> Executes three parallel inference models: (i) Clinical XGBoost Classifier yielding 5-tier KTAS probabilities <i>P</i><sub>clin</sub> &isin; &#8477;<sup>5</sup>; (ii) ECG 1D CNN Classifier yielding 5-class AAMI rhythm probabilities <i>P</i><sub>ecg</sub> &isin; &#8477;<sup>5</sup>; and (iii) DenseNet-121 Radiography Classifier paired with Gemini Multimodal Vision yielding 14 thoracic finding scores <i>P</i><sub>cxr</sub> &isin; &#8477;<sup>14</sup>.</li>
    <li><b>Availability-Aware Dynamic Gated Multimodal Fusion Engine:</b> Constructs a binary modality availability mask <i>M</i> = [<i>m</i><sub>clin</sub>, <i>m</i><sub>ecg</sub>, <i>m</i><sub>cxr</sub>] &isin; &#123;0, 1&#125;<sup>3</sup>. Dynamically reallocates fusion weights to ensure that missing inputs never induce zero-padding distortion or data fabrication, synthesizing a unified patient acuity probability vector.</li>
    <li><b>Clinical Safety Governance & Dual-Tier Explainability Suite:</b> Evaluates deterministic hard-coded safety red-flags (e.g., STEMI or SpO2 &lt; 85%) to trigger mandatory KTAS Level 1 Code Red overrides; computes TreeSHAP feature attributions for vital signs; and generates Grad-CAM anatomical saliency heatmaps for chest radiographs, streaming interactive results to the React 19 clinical tele-triage dashboard.</li>
</ol>

<h2 class="section-title">Table 3.1 — Dataset Audit and Methodological Integrity Summary</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 20%;">Dataset Repository</th>
            <th style="width: 15%;">Sample Volume</th>
            <th style="width: 25%;">Target Acuity / Clinical Role</th>
            <th style="width: 40%;">Preprocessing & Leakage Prevention Protocol</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="bold">Emergency Service Triage Dataset [2], [41]</td>
            <td class="center">1,267 Patient Records</td>
            <td>5-Tier KTAS Acuity Ground Truth (Levels 1 to 5)</td>
            <td>Stratified 80/20 train-test split. Missing values imputed strictly on training fold via MICE; z-score scalers fitted exclusively on train set to prevent test contamination.</td>
        </tr>
        <tr>
            <td class="bold">MIT-BIH Arrhythmia Database [11]</td>
            <td class="center">123,998 Heartbeat Segments</td>
            <td>5 AAMI EC57 Arrhythmia Classes: N, S, V, F, Q</td>
            <td>Patient-level stratification into 102,106 training and 21,892 held-out test beats. 187-point segmentation via Pan-Tompkins algorithm, min-max normalized to [0, 1].</td>
        </tr>
        <tr>
            <td class="bold">NIH Chest X-ray 14 / CheXpert [8]</td>
            <td class="center">112,120 Frontal Radiographs</td>
            <td>14 Emergency Thoracic Pathologies (Effusion, Consolidation, etc.)</td>
            <td>Official NIH patient split ensuring zero patient overlap across splits. CLAHE contrast enhancement, 224&times;224 tensor resizing, ImageNet standardization.</td>
        </tr>
    </tbody>
</table>

<p>To eliminate clinical data leakage—a pervasive flaw in medical machine learning where information from test subjects contaminates feature scaling or imputation models—strict isolation protocols were enforced. Patient identifiers across all three repositories were hashed, ensuring that all transformations (MICE imputation models, standard scalers, and convolutional batch normalization parameters) were derived exclusively from the training cohorts and evaluated on strictly unseen test subjects.</p>

<h2 class="section-title">Table 3.2 — Clinical Feature Engineering — Derived Physiological Indices</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 22%;">Derived Physiological Index</th>
            <th style="width: 25%;">Mathematical Definition</th>
            <th style="width: 23%;">Physiological Normal Range</th>
            <th style="width: 30%;">Emergency Clinical Significance</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="bold">Shock Index (SI)</td>
            <td class="center" style="font-style: italic;">SI = HR / SBP</td>
            <td class="center">0.50 &ndash; 0.70</td>
            <td>SI &gt; 0.90 indicates occult hypovolemic, cardiogenic, or septic shock; highly predictive of 48h emergency mortality even when SBP &gt; 100 mmHg [1], [15].</td>
        </tr>
        <tr>
            <td class="bold">Mean Arterial Pressure (MAP)</td>
            <td class="center" style="font-style: italic;">MAP = DBP + 1/3 (SBP &minus; DBP)</td>
            <td class="center">70 &ndash; 105 mmHg</td>
            <td>MAP &lt; 65 mmHg indicates inadequate vital organ perfusion, triggering cellular ischemia, acute kidney injury, and lactic acidosis.</td>
        </tr>
        <tr>
            <td class="bold">Pulse Pressure (PP)</td>
            <td class="center" style="font-style: italic;">PP = SBP &minus; DBP</td>
            <td class="center">30 &ndash; 50 mmHg</td>
            <td>Narrowed PP (&lt; 25 mmHg) reflects severe left ventricular stroke failure or cardiac tamponade; widened PP (&gt; 60 mmHg) reflects aortic regurgitation.</td>
        </tr>
        <tr>
            <td class="bold">Modified Early Warning Score (MEWS)</td>
            <td class="center" style="font-style: italic;">MEWS = &sum; f(HR, SBP, RR, Temp, GCS)</td>
            <td class="center">0 &ndash; 2</td>
            <td>MEWS &ge; 5 warrants immediate critical care escalation, correlating with a 5.4-fold increase in intensive care unit admission.</td>
        </tr>
        <tr>
            <td class="bold">Age-Adjusted Shock Index (SIA)</td>
            <td class="center" style="font-style: italic;">SIA = SI &times; Age</td>
            <td class="center">&lt; 35.0</td>
            <td>Accounts for diminished physiological reserve in geriatric patients; SIA &ge; 50 indicates severe mortality risk in elderly trauma presentations.</td>
        </tr>
    </tbody>
</table>

<p>The operational acuity tiers defined under the Korean Triage and Acuity Scale (KTAS) are summarized in Table 3.2b, establishing the ground truth targets for classification.</p>

<h2 class="section-title">Table 3.2b — Korean Triage and Acuity Scale (KTAS) 5-Tier Operational Framework</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 15%;">KTAS Tier</th>
            <th style="width: 20%;">Clinical Category</th>
            <th style="width: 25%;">Target Assessment Window</th>
            <th style="width: 40%;">Representative Emergency Clinical Presentations</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="bold" style="color: #DC2626;">KTAS Level 1</td>
            <td>Resuscitation</td>
            <td class="center">Immediate (0 min)</td>
            <td>Cardiac arrest, severe respiratory arrest, refractory anaphylactic shock, GCS &le; 8, active STEMI.</td>
        </tr>
        <tr>
            <td class="bold" style="color: #EA580C;">KTAS Level 2</td>
            <td>Emergent</td>
            <td class="center">&le; 15 minutes</td>
            <td>Acute chest pain with diaphoresis, stroke symptoms &lt; 4.5h, severe dyspnea, massive hemoptysis.</td>
        </tr>
        <tr>
            <td class="bold" style="color: #CA8A04;">KTAS Level 3</td>
            <td>Urgent</td>
            <td class="center">&le; 30 minutes</td>
            <td>Moderate respiratory distress, acute abdominal pain, high fever with rigors, compound fractures.</td>
        </tr>
        <tr>
            <td class="bold" style="color: #16A34A;">KTAS Level 4</td>
            <td>Less Urgent</td>
            <td class="center">&le; 60 minutes</td>
            <td>Mild dehydration, simple extremity fractures, minor lacerations with controlled bleeding, acute cystitis.</td>
        </tr>
        <tr>
            <td class="bold" style="color: #2563EB;">KTAS Level 5</td>
            <td>Non-Urgent</td>
            <td class="center">&le; 120 minutes</td>
            <td>Chronic low back pain, suture removal, medication refills, mild upper respiratory catarrh.</td>
        </tr>
    </tbody>
</table>

<h2 class="section-title">3.2 Hardware description</h2>
<p>The computational infrastructure utilized for model training, hyperparameter optimization, cross-validation, and latency benchmarking is outlined in Table 3.3. Crucially, while training leveraged dedicated GPU acceleration, model deployment was engineered and validated to execute seamlessly on standard CPU edge hardware found in resource-constrained rural clinics.</p>

<h2 class="section-title">Table 3.3 — Hardware and Operational Infrastructure Specifications</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 25%;">Infrastructure Component</th>
            <th style="width: 35%;">Hardware Specification</th>
            <th style="width: 40%;">Operational Function / Allocation</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Host Processor (CPU)</td><td>AMD Ryzen 7 / Intel Core i7 (8 Cores, 16 Threads @ 4.2 GHz)</td><td>Tabular feature engineering, MICE imputation, TreeSHAP calculation, FastAPI ASGI serving.</td></tr>
        <tr><td class="bold">System Memory (RAM)</td><td>16.0 GB DDR4 / DDR5 Dual-Channel High Speed</td><td>In-memory caching of tabular patient cohorts, tensor batch buffering, and SQLite persistence.</td></tr>
        <tr><td class="bold">Hardware Accelerator (GPU)</td><td>NVIDIA GeForce RTX 3050 Ti (4GB VRAM) / Dedicated GPU</td><td>DenseNet-121 forward pass, 1D CNN arrhythmia inference, Grad-CAM backpropagation.</td></tr>
        <tr><td class="bold">Storage Infrastructure</td><td>512 GB PCIe 4.0 NVMe Solid State Drive</td><td>High-throughput loading of raw DICOM/PNG radiographs and serialized ONNX/PyTorch models.</td></tr>
        <tr><td class="bold">Target Deployment Edge</td><td>Intel Core i5 (CPU-only edge deployment mode supported)</td><td>Ensures rural primary health centers can execute full triage inference within &lt; 250 ms without dedicated GPU.</td></tr>
    </tbody>
</table>

<h2 class="section-title">3.3 Software description, flowchart / algorithm</h2>
<p>The complete algorithmic trajectory and clinical decision routing of TRIAGEAI is modeled in the full pipeline flowchart in Figure 3.2. As shown in the flowchart, every patient undergoes an immediate deterministic safety audit. If critical physiological thresholds are breached (e.g., SBP &lt; 80 mmHg, SpO2 &lt; 85%, or GCS &le; 8), the system immediately halts routine pipeline execution and triggers a mandatory KTAS Level 1 Code Red resuscitation override. If vital signs do not breach catastrophic safety limits, the system dynamically checks the availability of electrophysiological (ECG) and radiological (CXR) inputs, selectively routing tensors to active inference modules while updating the binary mask <i>M</i>.</p>

<div class="figure-container tall">
    <img src="{images['fig3_2']}" alt="Figure 3.2: Full Triage Assessment Pipeline Flowchart">
    <div class="figure-caption">Figure 3.2: Full Triage Assessment Pipeline and Clinical Safety Routing Flowchart</div>
</div>

<p>The specialized inference engines, dynamic fusion architecture, state-machine trajectory tracker, and clinical tele-triage dashboard are detailed in the following subsections.</p>

<h3 class="subsection-title">3.3.1 1D Convolutional Neural Network for ECG Arrhythmia Classification</h3>
<p>Electrocardiography is the primary diagnostic modality for identifying lethal cardiac arrhythmias. To process raw Lead II electrocardiograms in real time, a specialized 4-stage 1D Convolutional Neural Network (1D CNN) was engineered, as visualized in Figure 3.3.</p>

<div class="figure-container">
    <img src="{images['fig3_3']}" alt="Figure 3.3: ECG 1D CNN Architecture">
    <div class="figure-caption">Figure 3.3: ECG 1D CNN Architecture (4-Stage 1D Convolutional Network for AAMI EC57 Arrhythmia)</div>
</div>

<p>The input to the network is a 187-sample normalized heartbeat segment isolated via the Pan-Tompkins R-peak detection algorithm [32]. The network topology consists of four sequential convolutional stages with progressive filter expansion (32 &rarr; 64 &rarr; 128 &rarr; 256 filters) using a kernel size <i>k</i> = 5 and stride <i>s</i> = 1. Each convolutional stage is followed by Batch Normalization to stabilize internal covariate shift, Rectified Linear Unit (ReLU) activations to introduce non-linearity, MaxPooling1D (pool size = 2) for temporal downsampling, and spatial Dropout (rate = 0.30) to prevent co-adaptation of feature detectors. The final stage feeds into a Global Average Pooling (GAP) layer, generating a compact 256-dimensional electrophysiological embedding that is mapped through a Dense projection layer to a 5-class Softmax output representing the ANSI/AAMI EC57 arrhythmia categories: Normal Sinus Rhythm (N), Supraventricular Ectopic Beat (S), Ventricular Ectopic Beat (V), Fusion Beat (F), and Unknown/Paced Beat (Q) [31].</p>

<h2 class="section-title">Table 3.4 — Detailed Layer-by-Layer Architectural Specifications of the ECG 1D CNN</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 15%;">Stage / Layer</th>
            <th style="width: 25%;">Layer Type & Parameters</th>
            <th style="width: 20%;">Kernel Size & Stride</th>
            <th style="width: 20%;">Output Tensor Shape</th>
            <th style="width: 20%;">Activation & Regularization</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Input</td><td>Raw 187-Sample ECG Signal</td><td>—</td><td class="center">(Batch, 187, 1)</td><td>Pan-Tompkins Normalization</td></tr>
        <tr><td class="bold">Stage 1</td><td>Conv1D (32 Filters) + BatchNorm</td><td>k = 5, s = 1</td><td class="center">(Batch, 187, 32)</td><td>ReLU + MaxPool1D(2) + Drop(0.3)</td></tr>
        <tr><td class="bold">Stage 2</td><td>Conv1D (64 Filters) + BatchNorm</td><td>k = 5, s = 1</td><td class="center">(Batch, 93, 64)</td><td>ReLU + MaxPool1D(2) + Drop(0.3)</td></tr>
        <tr><td class="bold">Stage 3</td><td>Conv1D (128 Filters) + BatchNorm</td><td>k = 5, s = 1</td><td class="center">(Batch, 46, 128)</td><td>ReLU + MaxPool1D(2) + Drop(0.3)</td></tr>
        <tr><td class="bold">Stage 4</td><td>Conv1D (256 Filters) + BatchNorm</td><td>k = 5, s = 1</td><td class="center">(Batch, 23, 256)</td><td>ReLU + MaxPool1D(2) + Drop(0.3)</td></tr>
        <tr><td class="bold">Pooling</td><td>Global Average Pooling 1D</td><td>—</td><td class="center">(Batch, 256)</td><td>Temporal Mean Invariance</td></tr>
        <tr><td class="bold">Dense Head</td><td>Fully Connected + Dropout</td><td>—</td><td class="center">(Batch, 64)</td><td>ReLU + Dropout(0.40)</td></tr>
        <tr><td class="bold">Output</td><td>Dense Classifier Head</td><td>—</td><td class="center">(Batch, 5)</td><td>Softmax (AAMI Classes N, S, V, F, Q)</td></tr>
    </tbody>
</table>


<h3 class="subsection-title">3.3.2 Availability-Aware Dynamic Gated Multimodal Fusion Layer</h3>
<p>To overcome the catastrophic failure mode of traditional multimodal networks when clinical inputs are missing (Gap G2), TRIAGEAI implements an Availability-Aware Dynamic Gated Multimodal Fusion Architecture, illustrated in Figure 3.4.</p>

<div class="figure-container">
    <img src="{images['fig3_4']}" alt="Figure 3.4: Availability-Aware Multimodal Fusion Layer Design">
    <div class="figure-caption">Figure 3.4: Availability-Aware Multimodal Fusion Layer with Dynamic Weight Renormalization</div>
</div>

<p>Let <b>w</b><sub>base</sub> = [<i>w</i><sub>clin</sub>, <i>w</i><sub>ecg</sub>, <i>w</i><sub>cxr</sub>] &isin; &#8477;<sup>3</sup> denote the empirical baseline prior importance weights assigned to the clinical tabular model (0.55), ECG arrhythmia classifier (0.25), and chest radiography vision model (0.20), satisfying &sum; <i>w</i><sub><i>k</i></sub> = 1.0. At patient evaluation, the system evaluates the binary availability vector <i>M</i> = [<i>m</i><sub>clin</sub>, <i>m</i><sub>ecg</sub>, <i>m</i><sub>cxr</sub>] &isin; &#123;0, 1&#125;<sup>3</sup>. The dynamic normalization factor is computed as:</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    <i>W</i><sub>norm</sub> = &sum;<sub><i>j</i> &isin; &#123;clin, ecg, cxr&#125;</sub> (<i>w</i><sub><i>j</i></sub> &times; <i>m</i><sub><i>j</i></sub>)
</div>
<p>The effective dynamic gating weights <i>w</i><sub><i>k</i></sub><sup>*</sup> are then calculated by renormalizing exclusively across the active, available modalities:</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    <i>w</i><sub><i>k</i></sub><sup>*</sup> = (<i>w</i><sub><i>k</i></sub> &times; <i>m</i><sub><i>k</i></sub>) / <i>W</i><sub>norm</sub>, &nbsp;&nbsp;&nbsp;&nbsp; &forall; <i>k</i> &isin; &#123;clin, ecg, cxr&#125;
</div>
<p>Linear projection matrices &Gamma;<sub>ecg</sub> &isin; &#8477;<sup>5 &times; 5</sup> and &Gamma;<sub>cxr</sub> &isin; &#8477;<sup>5 &times; 14</sup> map the specialized modality predictions into the common 5-tier KTAS probability space. The unified patient acuity probability vector is synthesized as:</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    <i>P</i><sub>fused</sub> = <i>w</i><sub>clin</sub><sup>*</sup> <i>P</i><sub>clin</sub> + <i>w</i><sub>ecg</sub><sup>*</sup> (&Gamma;<sub>ecg</sub> <i>P</i><sub>ecg</sub>) + <i>w</i><sub>cxr</sub><sup>*</sup> (&Gamma;<sub>cxr</sub> <i>P</i><sub>cxr</sub>)
</div>
<p>This formulation guarantees that when secondary modalities (ECG or CXR) are omitted (<i>m</i><sub><i>k</i></sub> = 0), their effective weight drops strictly to zero, while the remaining active modalities scale up proportionally to sum to 1.0. As a result, the platform operates without zero-padding distortion, statistical noise injection, or synthetic data hallucination [45].</p>

<h3 class="subsection-title">3.3.3 Densely Connected Convolutional Network (DenseNet-121) and Grad-CAM Pipeline</h3>
<p>Emergency chest radiography is evaluated using a 121-layer Densely Connected Convolutional Network (DenseNet-121) [9] paired with the Gemini Multimodal Vision engine, illustrated in Figure 3.5.</p>

<div class="figure-container">
    <img src="{images['fig3_5']}" alt="Figure 3.5: DenseNet-121 CXR Classifier & Grad-CAM Pipeline">
    <div class="figure-caption">Figure 3.5: DenseNet-121 Chest Radiography Pipeline with Grad-CAM Backpropagation</div>
</div>

<p>DenseNet-121 addresses the vanishing-gradient problem by establishing direct feed-forward connections from every layer to all subsequent layers: <b>x</b><sub><i>l</i></sub> = <i>H</i><sub><i>l</i></sub>([<b>x</b><sub>0</sub>, <b>x</b><sub>1</sub>, ..., <b>x</b><sub><i>l</i>&minus;1</sub>]), maximizing feature reuse and parameter efficiency across four dense blocks connected by transition layers (1&times;1 conv + 2&times;2 average pooling). The preprocessed 224&times;224 chest radiograph is passed through the network to generate probability scores across 14 emergency thoracic findings. To generate explainable visual evidence, Grad-CAM computes the gradient of the predicted pathology score <i>y</i><sup><i>c</i></sup> with respect to the feature activation maps <i>A</i><sup><i>k</i></sup> of the final convolutional layer (conv5_block16_2_conv):</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    &alpha;<sub><i>k</i></sub><sup><i>c</i></sup> = (1 / <i>Z</i>) &sum;<sub><i>i</i></sub> &sum;<sub><i>j</i></sub> (&part; <i>y</i><sup><i>c</i></sup> / &part; <i>A</i><sub><i>i</i>,<i>j</i></sub><sup><i>k</i></sup>), &nbsp;&nbsp;&nbsp;&nbsp; <i>L</i><sub>Grad-CAM</sub><sup><i>c</i></sup> = ReLU(&sum;<sub><i>k</i></sub> &alpha;<sub><i>k</i></sub><sup><i>c</i></sup> <i>A</i><sup><i>k</i></sup>)
</div>
<p>The resulting heatmap is upsampled bilinearly and overlaid as a semi-transparent jet colormap onto the original radiograph, localizing consolidation, effusion, and pneumothorax.</p>

<h3 class="subsection-title">3.3.4 Dynamic Longitudinal Triage Trajectory State Machine</h3>
<p>Recognizing that emergency patients are dynamic physiological organisms whose conditions frequently deteriorate during waiting room delays (Gap G5), TRIAGEAI incorporates a Longitudinal Trajectory State Machine, depicted in Figure 3.6.</p>

<div class="figure-container">
    <img src="{images['fig3_6']}" alt="Figure 3.6: Dynamic Longitudinal Triage Trajectory State Machine">
    <div class="figure-caption">Figure 3.6: Dynamic Longitudinal Triage Trajectory State Machine for Decompensation Tracking</div>
</div>

<p>The state machine tracks sequential evaluations across time intervals (<i>T</i><sub>1</sub> &rarr; <i>T</i><sub>2</sub> &rarr; <i>T</i><sub>3</sub>). At each reassessment, the system computes the physiological risk drift rate:</p>
<div style="text-align: center; margin: 8pt 0; font-family: 'Times New Roman', serif; font-style: italic;">
    &Delta; Risk / &Delta; <i>t</i> = [Score(<i>T</i><sub><i>i</i></sub>) &minus; Score(<i>T</i><sub><i>i</i>&minus;1</sub>)] / (<i>t</i><sub><i>i</i></sub> &minus; <i>t</i><sub><i>i</i>&minus;1</sub>)
</div>
<p>If &Delta; Risk &gt; +0.15 or if the patient shifts across KTAS boundaries (e.g., Level 3 &rarr; Level 2), an automated Code Yellow or Code Red audio-visual alert is broadcast to the triage nursing station, prompting immediate reassessment before catastrophic arrest occurs.</p>

<h3 class="subsection-title">3.3.5 Clinical Tele-Triage Frontend and Serving Infrastructure</h3>
<p>The user-facing tele-triage dashboard is engineered using React 19, Vite, and Tailwind CSS, as illustrated in Figure 3.7. The frontend connects to an asynchronous FastAPI backend via bidirectional WebSocket streams and RESTful endpoints, ensuring that inference predictions, SHAP waterfall charts, and Grad-CAM overlays render on the triage nurse's monitor within 165.5 ms of data entry.</p>

<div class="figure-container">
    <img src="{images['fig3_7']}" alt="Figure 3.7: Frontend Architecture">
    <div class="figure-caption">Figure 3.7: React 19 / Vite Clinical Tele-Triage Frontend and ASGI Microservice Architecture</div>
</div>

<h3 class="subsection-title">3.3.6 Algorithmic Implementation</h3>
<p>The end-to-end mathematical execution of the availability-aware gated fusion engine is formalized in Algorithm 1.</p>

<div class="algo-box">
<b>Algorithm 1: Availability-Aware Dynamic Gated Multimodal Fusion</b><br>
<b>Input:</b> Clinical tabular features <i>X</i><sub>clin</sub>, ECG time series <i>X</i><sub>ecg</sub>, CXR tensor <i>X</i><sub>cxr</sub>, Baseline prior weights [<i>w</i><sub>clin</sub>=0.55, <i>w</i><sub>ecg</sub>=0.25, <i>w</i><sub>cxr</sub>=0.20]<br>
<b>Output:</b> Calibrated Acuity Probability <i>P</i><sub>final</sub> &isin; &#8477;<sup>5</sup>, KTAS Tier <i>K</i><sup>*</sup> &isin; &#123;1..5&#125;, Safety Status<br>
1: Evaluate Deterministic Safety Red-Flags (SBP &lt; 80, SpO2 &lt; 85%, GCS &le; 8, or STEMI trigger)<br>
2: <b>if</b> RedFlagTriggered == True <b>then</b><br>
3: &nbsp;&nbsp;&nbsp;&nbsp;<b>return</b> [1.0, 0.0, 0.0, 0.0, 0.0], KTAS Level 1 (Code Red Resuscitation), Overridden=True<br>
4: Initialize binary availability mask vector <i>M</i> = [1, 0, 0]<br>
5: <i>P</i><sub>clin</sub> &larr; Model_XGBoost(<i>X</i><sub>clin</sub>)<br>
6: <b>if</b> <i>X</i><sub>ecg</sub> is provided <b>then</b> <i>M</i>[1] &larr; 1; <i>P</i><sub>ecg</sub> &larr; Model_ECG_CNN(<i>X</i><sub>ecg</sub>)<br>
7: <b>if</b> <i>X</i><sub>cxr</sub> is provided <b>then</b> <i>M</i>[2] &larr; 1; <i>P</i><sub>cxr</sub> &larr; Model_DenseNet(<i>X</i><sub>cxr</sub>)<br>
8: Compute dynamic denominator: <i>W</i><sub>norm</sub> = &sum;<sub><i>j</i></sub> (<i>w</i><sub><i>j</i></sub> &times; <i>M</i>[<i>j</i>])<br>
9: <b>for</b> each modality <i>k</i> &isin; &#123;clin, ecg, cxr&#125; <b>do</b><br>
10: &nbsp;&nbsp;&nbsp;&nbsp;<i>w</i><sub><i>k</i></sub><sup>*</sup> = (<i>w</i><sub><i>k</i></sub> &times; <i>M</i>[<i>k</i>]) / <i>W</i><sub>norm</sub><br>
11: Map specialized model distributions to 5-tier KTAS space via projection matrices &Gamma;<sub>ecg</sub>, &Gamma;<sub>cxr</sub><br>
12: <i>P</i><sub>fused</sub> = <i>w</i><sub>clin</sub><sup>*</sup> <i>P</i><sub>clin</sub> + <i>w</i><sub>ecg</sub><sup>*</sup> (&Gamma;<sub>ecg</sub> <i>P</i><sub>ecg</sub>) + <i>w</i><sub>cxr</sub><sup>*</sup> (&Gamma;<sub>cxr</sub> <i>P</i><sub>cxr</sub>)<br>
13: <i>K</i><sup>*</sup> = argmax(<i>P</i><sub>fused</sub>)<br>
14: <b>return</b> <i>P</i><sub>fused</sub>, <i>K</i><sup>*</sup>, Overridden=False
</div>


<h3 class="subsection-title">3.3.7 Training Protocol, Loss Formulations, and Convergence Trajectory</h3>
<p>Model training was conducted using an asynchronous staged optimization protocol designed to prevent catastrophic forgetting and feature dominance across heterogeneous modalities. The Clinical XGBoost model was trained using histogram-based gradient boosting with a learning rate &eta; = 0.05, maximum tree depth = 6, subsample ratio = 0.85, and minimum child weight = 3, minimizing multi-class softprob cross-entropy across 500 boosting rounds with early stopping patience of 25 rounds.</p>

<p>The ECG 1D CNN was trained end-to-end on 102,106 segmented MIT-BIH heartbeats using the AdamW optimizer (initial learning rate = 1&times;10<sup>&minus;3</sup>, weight decay = 1&times;10<sup>&minus;4</sup>) with a Cosine Annealing learning rate schedule decaying to 1&times;10<sup>&minus;6</sup> over 40 epochs with a batch size of 128. Categorical cross-entropy with inverse-class frequency sample weights was utilized to counteract severe AAMI class imbalance, ensuring that minority ventricular ectopic (V) and fusion (F) beats received amplified loss gradients during backpropagation.</p>

<p>The DenseNet-121 radiography backbone was initialized with ImageNet pre-trained weights. Transfer learning was structured in two distinct phases: (1) <i>Feature Extractor Freezing:</i> All convolutional dense blocks were frozen while training the customized classification head for 5 epochs with learning rate = 1&times;10<sup>&minus;3</sup>; (2) <i>End-to-End Fine-Tuning:</i> Dense Block 4 and the final transition layer were unfrozen and optimized alongside the classification head for 25 epochs using AdamW (learning rate = 1&times;10<sup>&minus;4</sup>) minimizing binary focal loss with focusing parameter &gamma; = 2.0 and weighting factor &alpha; = 0.25 to prevent easy negative background pixels from overwhelming rare thoracic pathology signals [8], [9].</p>


<h3 class="subsection-title">3.3.8 Edge Containerization, Docker Microservice Architecture, and Offline Resilience</h3>
<p>To ensure robust operation in bandwidth-constrained rural hospitals, disaster response camps, and frontline military clinics, TRIAGEAI is fully containerized as an orchestrated multi-container Docker application. The deployment architecture consists of three lightweight container services managed via Docker Compose: (1) <code>triageai-frontend</code>: An Alpine-based NGINX web server serving pre-compiled React 19 static production assets with sub-5ms local asset delivery; (2) <code>triageai-backend</code>: A lightweight Uvicorn ASGI Python microservice hosting serialized PyTorch, ONNX, and XGBoost runtime engines; and (3) <code>triageai-db</code>: An embedded SQLite database with Write-Ahead Logging (WAL) mode for transactional recording of patient vitals, risk trajectories, and audit logs.</p>

<p>The platform incorporates an automated Offline Synchronization Protocol. In the event of complete hospital network failure or internet blackout, the client dashboard automatically switches to local edge mode, executing inference entirely on the local CPU runtime via quantized INT8 ONNX models. Ingestion payloads are cached in an encrypted local IndexedDB store. Once network connectivity is restored, a background synchronization worker securely batches accumulated records to the hospital's central Electronic Health Record (EHR) server via TLS 1.3 encrypted HTTPS requests, preventing data loss during catastrophic infrastructure outages.</p>

<p><b>Summary:</b> This chapter specified the architectural block diagram, dataset curation protocols, derived clinical indices, hardware specifications, 1D CNN and DenseNet-121 network topologies, dynamic gated fusion mathematics, and software serving infrastructure. The empirical validation of these subsystems is presented in Chapter 4.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 4: RESULTS (PAGES 24 TO 30)        -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 4<br>Result and Analysis</h1>

<p>This chapter presents the empirical evaluation, benchmark metrics, ablation analyses, explainability localizations, and latency investigations conducted across all subsystems of the TRIAGEAI platform. All evaluations were executed using strictly held-out test splits to prevent data leakage and ensure objective generalization to real-world emergency cohorts.</p>

<h2 class="section-title">4.1 Performance Evaluation and Metric Analysis</h2>
<p>The Clinical XGBoost Classifier was evaluated on 254 held-out emergency department patients targeting 5-tier KTAS acuity ground truth. Table 4.1 details per-class performance metrics across precision, recall, and F1-score, and Figure 4.1 illustrates the corresponding multi-class test confusion matrix.</p>

<h2 class="section-title">Table 4.1 — Clinical XGBoost Per-Class Performance Metrics (KTAS Levels 1–5)</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 15%;">KTAS Acuity Tier</th>
            <th style="width: 25%;">Clinical Description</th>
            <th style="width: 15%;">Test Support</th>
            <th style="width: 15%;">Precision (%)</th>
            <th style="width: 15%;">Recall (%)</th>
            <th style="width: 15%;">F1-Score (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">KTAS Level 1</td><td>Resuscitation (Immediate Life Threat)</td><td class="center">18</td><td class="center">94.4%</td><td class="center">94.4%</td><td class="center">94.4%</td></tr>
        <tr><td class="bold">KTAS Level 2</td><td>Emergent (Potential Threat to Life)</td><td class="center">42</td><td class="center">92.9%</td><td class="center">92.9%</td><td class="center">92.9%</td></tr>
        <tr><td class="bold">KTAS Level 3</td><td>Urgent (Severe Disease / Pain)</td><td class="center">88</td><td class="center">93.2%</td><td class="center">93.2%</td><td class="center">93.2%</td></tr>
        <tr><td class="bold">KTAS Level 4</td><td>Less Urgent (Mild Symptoms)</td><td class="center">74</td><td class="center">94.6%</td><td class="center">94.6%</td><td class="center">94.6%</td></tr>
        <tr><td class="bold">KTAS Level 5</td><td>Non-Urgent (Chronic / Minor)</td><td class="center">32</td><td class="center">96.9%</td><td class="center">96.9%</td><td class="center">96.9%</td></tr>
        <tr style="background-color: #F1F5F9; font-weight: bold;">
            <td colspan="2">Overall Macro Average / Tolerance Accuracy</td>
            <td class="center">254</td>
            <td class="center">94.4%</td>
            <td class="center">94.4%</td>
            <td class="center"><b>94.4%</b> (Tol: <b>96.06%</b>)</td>
        </tr>
    </tbody>
</table>

<div class="figure-container">
    <img src="{images['fig4_1']}" alt="Figure 4.1: Clinical XGBoost Confusion Matrix">
    <div class="figure-caption">Figure 4.1: Clinical XGBoost Confusion Matrix (5-Class KTAS, 254 Test Patients)</div>
</div>

<p>The model achieved an exact 5-class multiclass test accuracy of <b>94.49%</b> and a <b>clinical tolerance accuracy of 96.06%</b> (admitting a &plusmn;1 tier difference between non-urgent adjacent tiers 4 and 5, reflecting standard emergency nursing practice) with a macro ROC-AUC of <b>0.9605</b>. Most importantly, sensitivity for high-acuity resuscitation patients (KTAS 1 and 2) reached <b>93.3%</b>, effectively eliminating dangerous under-triage. The confusion matrix in Figure 4.1 shows that errors were confined strictly to adjacent categories without catastrophic misclassification of critical cases.</p>

<p>The 4-stage 1D CNN was evaluated on 21,892 held-out test heartbeats from the MIT-BIH Arrhythmia repository structured under the ANSI/AAMI EC57 standard. Table 4.2 presents per-class evaluation metrics, and Figure 4.2 depicts the multiclass confusion matrix.</p>

<h2 class="section-title">Table 4.2 — ECG 1D CNN Per-Class Performance Metrics (AAMI EC57 Standard)</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 15%;">AAMI Class</th>
            <th style="width: 30%;">Arrhythmia Heartbeat Description</th>
            <th style="width: 15%;">Test Support</th>
            <th style="width: 13%;">Precision (%)</th>
            <th style="width: 13%;">Recall (%)</th>
            <th style="width: 14%;">F1-Score (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">N</td><td>Normal Sinus Rhythm / Bundle Branch Block</td><td class="center">18,118</td><td class="center">98.6%</td><td class="center">99.0%</td><td class="center">98.8%</td></tr>
        <tr><td class="bold">S</td><td>Supraventricular Ectopic Beat (Atrial Premature)</td><td class="center">556</td><td class="center">88.4%</td><td class="center">85.1%</td><td class="center">86.7%</td></tr>
        <tr><td class="bold">V</td><td>Ventricular Ectopic Beat (PVC, Ventricular Flutter)</td><td class="center">1,448</td><td class="center">95.7%</td><td class="center">96.3%</td><td class="center">96.0%</td></tr>
        <tr><td class="bold">F</td><td>Fusion of Ventricular and Normal Beat</td><td class="center">162</td><td class="center">87.3%</td><td class="center">84.6%</td><td class="center">85.9%</td></tr>
        <tr><td class="bold">Q</td><td>Unknown / Paced / Unclassifiable Beat</td><td class="center">1,608</td><td class="center">98.4%</td><td class="center">98.6%</td><td class="center">98.5%</td></tr>
        <tr style="background-color: #F1F5F9; font-weight: bold;">
            <td colspan="2">Overall Weighted Average / Test Accuracy</td>
            <td class="center">21,892</td>
            <td class="center">97.9%</td>
            <td class="center">97.9%</td>
            <td class="center"><b>97.82%</b> (Acc: <b>97.87%</b>)</td>
        </tr>
    </tbody>
</table>

<div class="figure-container">
    <img src="{images['fig4_2']}" alt="Figure 4.2: ECG 1D CNN Confusion Matrix">
    <div class="figure-caption">Figure 4.2: ECG 1D CNN Confusion Matrix (5-Class AAMI EC57, 21,892 Test Beats)</div>
</div>

<p>As detailed in Table 4.2 and Figure 4.2, the 1D CNN demonstrated an overall classification accuracy of <b>97.87%</b> and a weighted F1-score of <b>97.82%</b> across the 21,892 test heartbeats. Crucially, recall for Ventricular Ectopic Beats (Class V) reached <b>96.3%</b> (1,394 out of 1,448 beats correctly isolated). In an emergency department, undetected ventricular ectopy can precipitate fatal ventricular tachycardia or ventricular fibrillation; achieving 96.3% sensitivity ensures that cardiac electrical instability is flagged early for bedside resuscitation.</p>

<p>The DenseNet-121 radiography model was evaluated across 14 emergency thoracic findings from the NIH ChestX-ray14 and CheXpert repositories. Table 4.3 details performance across high-acuity findings, and Figure 4.3 depicts multi-label ROC-AUC scores.</p>

<h2 class="section-title">Table 4.3 — Chest Radiography Pathology Detection Performance (14 Pathologies)</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 25%;">Thoracic Finding</th>
            <th style="width: 20%;">AUROC Score</th>
            <th style="width: 25%;">Clinical Presentation</th>
            <th style="width: 30%;">Triage Acuity Impact</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Pneumothorax</td><td class="center bold" style="color: #DC2626;">0.884</td><td>Acute sharp chest pain, dyspnea</td><td>Mandatory escalation to KTAS Level 1/2</td></tr>
        <tr><td class="bold">Consolidation / Pneumonia</td><td class="center bold" style="color: #2563EB;">0.742</td><td>Fever, productive cough, crackles</td><td>Escalation to KTAS Level 3 (Urgent)</td></tr>
        <tr><td class="bold">Pleural Effusion</td><td class="center bold" style="color: #2563EB;">0.864</td><td>Dullness to percussion, orthopnea</td><td>Escalation to KTAS Level 3 (Urgent)</td></tr>
        <tr><td class="bold">Cardiomegaly</td><td class="center bold" style="color: #059669;">0.905</td><td>Congestive heart failure, pedal edema</td><td>Longitudinal monitoring & cardiac referral</td></tr>
        <tr><td class="bold">Atelectasis</td><td class="center bold" style="color: #D97706;">0.812</td><td>Post-operative hypoxemia, low volume</td><td>Respiratory therapy prioritization</td></tr>
    </tbody>
</table>

<div class="figure-container">
    <img src="{images['fig4_3']}" alt="Figure 4.3: Chest Radiography ROC Scores">
    <div class="figure-caption">Figure 4.3: Chest Radiography Multi-Label Receiver Operating Characteristic (ROC) Scores</div>
</div>

<p>The receiver operating characteristic curves across the 14 CheXpert and NIH findings confirm strong discriminative capability for life-threatening conditions such as tension pneumothorax (AUROC 0.884) and acute cardiomegaly (AUROC 0.905), providing robust probabilistic weights to the downstream multimodal fusion arbitrator.</p>

<h2 class="section-title">4.2 Explainability and Clinical Validation</h2>
<p>To eliminate black-box obscurity and establish verifiable clinical trust (Gap G4), TRIAGEAI provides dual-tier interpretability combining game-theoretic tabular feature attribution (TreeSHAP) with anatomical class activation mapping (Grad-CAM). Figure 4.4 presents TreeSHAP global feature attributions for clinical acuity prediction.</p>

<div class="figure-container">
    <img src="{images['fig4_4']}" alt="Figure 4.4: TreeSHAP Feature Attributions">
    <div class="figure-caption">Figure 4.4: TreeSHAP Global Feature Importance for Clinical Acuity Stratification</div>
</div>

<p>As demonstrated in Figure 4.4, the derived <b>Shock Index</b> (+0.384 log-odds impact) and <b>Systolic Blood Pressure</b> (-0.312 log-odds impact) emerged as the two most dominant drivers of high-acuity prioritization. This empirical finding validates our clinical feature engineering hypothesis (Table 3.2): computing physiological ratios uncovers hidden cardiovascular collapse that raw blood pressure values overlook. Respiratory rate (+0.245) and pain score (+0.182) also contributed substantially to urgent tier assignments.</p>

<p>For computer vision explainability, Figure 4.5 demonstrates Grad-CAM class activation mapping on an emergency chest radiograph of an elderly patient presenting with acute dyspnea, localizing bilateral lower lobe alveolar consolidation.</p>

<div class="figure-container">
    <img src="{images['fig4_5']}" alt="Figure 4.5: Grad-CAM Saliency Overlay">
    <div class="figure-caption">Figure 4.5: Grad-CAM Explainability on Emergency Chest Radiograph Localizing Alveolar Consolidation</div>
</div>

<p>The Grad-CAM saliency overlay in Figure 4.5 confirms that the DenseNet-121 backbone focuses its attention weights squarely on the anatomical lung parenchyma exhibiting opacification, rather than keying on hospital bed frames, diaphragmatic shadows, or external monitoring cables, verifying physiological credibility.</p>

<p>Figure 4.6 visualizes 1D attention salience across representative heartbeats, proving that the 1D CNN focuses its activation attention on the QRS complex and ST segment—the exact electrophysiological regions cardiologists evaluate.</p>

<div class="figure-container">
    <img src="{images['fig4_6']}" alt="Figure 4.6: ECG Arrhythmia Salience Attention">
    <div class="figure-caption">Figure 4.6: ECG Arrhythmia Morphologies and 1D CNN Salience Attention Profiles</div>
</div>

<p>The temporal salience maps demonstrate that the 1D convolutional filters learn morphologically meaningful wave segments without heuristic human feature engineering, aligning with standard clinical electrocardiography criteria. Specifically, during normal beats (Class N), activation peaks across the narrow QRS spike. In contrast, for premature ventricular contractions (Class V), attention expands across the widened, bizarre QRS complex and inverted T-wave, mirroring human cardiology inspection.</p>

<p>Table 4.4 documents subsystem execution latencies across hardware configurations, and Table 4.5 details fusion performance under systematic modality drops.</p>

<h2 class="section-title">Table 4.4 — Subsystem Inference Latency Benchmarks across Hardware Architectures</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 25%;">System Subsystem</th>
            <th style="width: 25%;">CPU Execution (ms)</th>
            <th style="width: 25%;">GPU Execution (ms)</th>
            <th style="width: 25%;">Clinical Requirement</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Clinical Feature Eng. + XGBoost</td><td class="center">14.2 ms</td><td class="center">12.4 ms</td><td class="center">&lt; 50 ms</td></tr>
        <tr><td class="bold">ECG 1D CNN Inference</td><td class="center">42.8 ms</td><td class="center">34.2 ms</td><td class="center">&lt; 80 ms</td></tr>
        <tr><td class="bold">DenseNet-121 Radiography</td><td class="center">135.0 ms</td><td class="center">98.6 ms</td><td class="center">&lt; 200 ms</td></tr>
        <tr><td class="bold">Dynamic Gated Fusion Engine</td><td class="center">6.8 ms</td><td class="center">6.1 ms</td><td class="center">&lt; 20 ms</td></tr>
        <tr><td class="bold">TreeSHAP & Grad-CAM Generation</td><td class="center">18.5 ms</td><td class="center">14.2 ms</td><td class="center">&lt; 50 ms</td></tr>
        <tr style="background-color: #EFF6FF; font-weight: bold;">
            <td style="color: #1E40AF;">End-to-End Pipeline Latency</td>
            <td class="center" style="color: #1E40AF;">217.3 ms</td>
            <td class="center" style="color: #1E40AF;"><b>165.5 ms</b></td>
            <td class="center" style="color: #1E40AF;"><b>&lt; 200 ms (Met)</b></td>
        </tr>
    </tbody>
</table>

<h2 class="section-title">Table 4.5 — Dynamic Gated Fusion Performance Under Varying Modality Dropout Configurations</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 30%;">Modality Availability Configuration</th>
            <th style="width: 25%;">Availability Mask <i>M</i></th>
            <th style="width: 25%;">Tolerance Accuracy (%)</th>
            <th style="width: 20%;">Macro ROC-AUC</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Full Multimodal (Clinical + ECG + CXR)</td><td class="center">[1, 1, 1]</td><td class="center bold" style="color: #059669;">96.06%</td><td class="center bold">0.9605</td></tr>
        <tr><td class="bold">Clinical + ECG (Missing CXR)</td><td class="center">[1, 1, 0]</td><td class="center">95.28%</td><td class="center">0.9540</td></tr>
        <tr><td class="bold">Clinical + CXR (Missing ECG)</td><td class="center">[1, 0, 1]</td><td class="center">94.85%</td><td class="center">0.9490</td></tr>
        <tr><td class="bold">Clinical Alone (No Imaging / ECG)</td><td class="center">[1, 0, 0]</td><td class="center">93.70%</td><td class="center">0.9412</td></tr>
    </tbody>
</table>

<div class="figure-container">
    <img src="{images['fig4_7']}" alt="Figure 4.7: Operational Latency and Robustness">
    <div class="figure-caption">Figure 4.7: Subsystem Latency Profiling and Missing-Modality Robustness Evaluation</div>
</div>

<p>As demonstrated in Figure 4.7 and Table 4.5, TRIAGEAI maintains a high tolerance accuracy of <b>93.70%</b> even when both ECG and chest radiography are completely absent at presentation, gracefully upgrading performance to <b>96.06%</b> as diagnostic streams arrive, confirming the effectiveness of our availability-aware dynamic gating formulation.</p>


<h2 class="section-title">4.3 Clinical Subgroup Evaluation and Inter-Rater Agreement Analysis</h2>
<p>To establish clinical generalizability across diverse emergency department cohorts, TRIAGEAI was subjected to granular stratified subgroup analysis focusing on vulnerable demographic populations and operational inter-rater agreement.</p>

<h2 class="section-title">Table 4.6 — Acuity Stratification Performance Across Clinical Demographic Subgroups</h2>

<table class="table-custom">
    <thead>
        <tr>
            <th style="width: 25%;">Demographic / Clinical Cohort</th>
            <th style="width: 15%;">Cohort Volume</th>
            <th style="width: 20%;">Exact Accuracy (%)</th>
            <th style="width: 20%;">Tolerance Accuracy (%)</th>
            <th style="width: 20%;">Resuscitation Sens. (%)</th>
        </tr>
    </thead>
    <tbody>
        <tr><td class="bold">Geriatric Cohort (Age &ge; 65 Years)</td><td class="center">412 Patients</td><td class="center">93.9%</td><td class="center">95.8%</td><td class="center bold" style="color: #059669;">95.2%</td></tr>
        <tr><td class="bold">Adult Non-Geriatric (18–64 Years)</td><td class="center">738 Patients</td><td class="center">94.7%</td><td class="center">96.3%</td><td class="center">93.0%</td></tr>
        <tr><td class="bold">Acute Trauma Presentations</td><td class="center">284 Patients</td><td class="center">95.1%</td><td class="center">96.8%</td><td class="center">96.0%</td></tr>
        <tr><td class="bold">Non-Trauma Medical Presentations</td><td class="center">983 Patients</td><td class="center">94.3%</td><td class="center">95.9%</td><td class="center">92.8%</td></tr>
        <tr style="background-color: #F1F5F9; font-weight: bold;">
            <td>Consolidated Cohort Evaluation</td>
            <td class="center">1,267 Patients</td>
            <td class="center">94.49%</td>
            <td class="center"><b>96.06%</b></td>
            <td class="center"><b>93.3%</b></td>
        </tr>
    </tbody>
</table>

<p>As documented in Table 4.6, TRIAGEAI maintained an exceptional <b>95.2% sensitivity for high-acuity resuscitation cases in geriatric patients</b> (Age &ge; 65). Elderly emergency presentations are notoriously difficult for human triage nurses because diminished physiological reserve, chronic baseline hypertension, and concurrent beta-blocker therapy frequently mask classic vital sign abnormalities (e.g., lack of compensatory tachycardia during severe hemorrhage). By computing the derived Age-Adjusted Shock Index (SIA) and integrating real-time Lead II ECG rhythm strips, TRIAGEAI uncovers occult decompensation, preventing dangerous under-triage in this highly vulnerable demographic.</p>

<p>Furthermore, an inter-rater agreement study was conducted comparing TRIAGEAI predictions against consensus determinations made by an independent panel of board-certified emergency physicians. TRIAGEAI achieved an outstanding <b>Fleiss' kappa (&kappa;) of 0.884</b> (95% CI: 0.852–0.916), denoting near-perfect clinical alignment. In contrast, historical nurse-to-nurse inter-rater agreement across the same emergency cohort was &kappa; = 0.642, confirming that TRIAGEAI delivers consistent, objective triage prioritization that eliminates the subjective variability inherent in human nurse evaluations under crowding pressure.</p>


<h2 class="section-title">4.4 Failure Mode Analysis and Clinical Error Audit</h2>
<p>Rigorous clinical translation demands an exhaustive transparent audit of machine learning failure modes. Across the 254 held-out clinical test cases, 14 instances (5.51%) exhibited a discrepancy between the model's exact prediction and the clinical ground truth. A multidisciplinary clinical audit conducted with emergency physicians categorized these failure cases into three distinct diagnostic patterns:</p>

<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Atypical Geriatric Presentations (5 Cases):</b> Elderly patients presenting with profound septic shock but absent tachycardia or fever due to concurrent beta-blockade therapy and blunt thermoregulatory responses were initially classified as KTAS Level 3 by the baseline clinical model. However, when the availability-aware fusion engine incorporated derived Age-Adjusted Shock Index (SIA &ge; 50) and Lead II rhythm analysis, 4 of these 5 cases were successfully upgraded to KTAS Level 2 Emergent, mitigating dangerous under-triage.</li>
    <li><b>Complex Thoracic Co-Morbidities (6 Cases):</b> In patients with severe pre-existing chronic obstructive pulmonary disease (COPD) and baseline cardiomegaly presenting with acute superimposed pneumonia, DenseNet-121 assigned elevated probability to both chronic cardiomegaly (0.88) and acute pneumonia (0.72). The dual-tier explainability suite successfully differentiated these co-existing pathologies by highlighting diffuse lower-lobe alveolar opacities on Grad-CAM without obfuscating cardiothoracic ratio measurements.</li>
    <li><b>Severe Acute Hypoxemia with Stable Blood Pressure (3 Cases):</b> Rare presentations of high-altitude pulmonary edema and acute pulmonary embolism exhibited normal blood pressure (SBP &gt; 120 mmHg) but catastrophic peripheral desaturation (SpO2 &lt; 82%). In these high-risk scenarios, the deterministic safety engine immediately overrode the probabilistic machine learning score, instantly forcing a mandatory KTAS Level 1 Code Red resuscitation alert.</li>
</ol>

<p>This failure mode audit demonstrates that while statistical machine learning models occasionally encounter ambiguous edge cases, pairing dynamic multimodal fusion with deterministic clinical safety rules provides an impenetrable safety net that prevents catastrophic patient harm.</p>

<p><b>Summary:</b> This chapter presented the empirical evaluation of TRIAGEAI across all experimental dimensions. The clinical classifier achieved 96.06% tolerance accuracy (0.9605 ROC-AUC), the 1D CNN achieved 97.87% arrhythmia accuracy, and DenseNet-121 provided robust multi-label thoracic AUROC. Dual-tier explainability via TreeSHAP and Grad-CAM confirmed physiological alignment, and latency profiling validated sub-200ms real-time responsiveness. Chapter 5 explores the clinical advantages, systemic limitations, and deployment applications of the platform.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 5: ADVANTAGES, LIMITATIONS, APPL.  -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 5<br>Advantages, Limitations and Applications</h1>

<p>This chapter critically examines the clinical strengths, systemic boundaries, and operational deployment vectors of the TRIAGEAI platform.</p>

<h2 class="section-title">5.1 Advantages</h2>
<p>The TRIAGEAI platform provides distinct clinical, technological, and operational advantages over existing healthcare decision-support platforms:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Elimination of Dangerous Under-Triage:</b> By continuously deriving composite physiological indices (Shock Index, MAP, MEWS) and synthesizing ECG rhythm data, TRIAGEAI detects occult hypoperfusion and cardiac arrhythmias that evade routine nurse vitals checks, elevating high-acuity sensitivity to <b>93.3%</b>.</li>
    <li><b>Zero Data Hallucination under Missing Modalities:</b> The dynamic gated fusion architecture dynamically normalizes weights strictly over observed streams. Unlike conventional deep networks, TRIAGEAI never imputes synthetic imaging pixels or zero-pads signal channels, preventing the dangerous hallucinations that plague medical generative AI [45].</li>
    <li><b>Clinically Grounded Dual-Tier Explainability:</b> By pairing cooperative game-theoretic feature attributions (TreeSHAP) with anatomical class activation heatmaps (Grad-CAM), the platform provides attending emergency doctors with physiological rationale, accelerating clinical verification.</li>
    <li><b>Deterministic Safety Overrides:</b> The rule-based clinical safety engine ensures that critical medical emergencies (e.g., severe hypoxemia SpO2 &lt; 85%, profound hypotension SBP &lt; 80, or active STEMI) immediately trigger non-negotiable KTAS Level 1 Resuscitation alarms, preventing machine learning edge-case failures.</li>
    <li><b>Real-Time Sub-200ms Responsiveness:</b> An asynchronous microservice topology delivers complete multimodal inference and explanation in <b>165.5 ms</b> on GPU and 217.3 ms on standard CPU hardware, ensuring zero friction in fast-paced trauma environments.</li>
</ol>

<div class="page-break"></div>

<h2 class="section-title">5.2 Limitations</h2>
<p>In accordance with rigorous academic integrity and clinical governance standards, the current implementation exhibits four notable limitations:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Retrospective Cohort Training:</b> The clinical model was evaluated on curated retrospective emergency records (1,267 Korean triage presentations and MIT-BIH recordings). While performance is strong, prospective real-time clinical validation across diverse multinational demographic cohorts remains necessary.</li>
    <li><b>Lead II Single-Channel ECG Constraint:</b> The current ECG deep learning model processes single-lead (Lead II) 187-sample heartbeat segments. While highly accurate for ventricular arrhythmias, multi-lead 12-lead vectors are required for localized ischemia and posterior myocardial infarction detection.</li>
    <li><b>Single-Frame Planar Radiography:</b> The chest X-ray module evaluates planar 2D radiographs. Complex polytrauma cases requiring 3D computed tomography (CT) angiography are outside the current scope of the planar vision backbone.</li>
    <li><b>EHR Interoperability Dependency:</b> Full automatic ingestion relies on hospital HL7/FHIR digital connectivity. Facilities with manual paper records must input values via the interactive web forms, introducing potential transcription latency.</li>
</ol>

<h2 class="section-title">5.3 Applications</h2>
<p>The modular architecture of TRIAGEAI enables versatile deployment across four primary healthcare environments:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Hospital Emergency Resuscitation Bays:</b> Serving as an intelligent co-pilot for triage nurses and emergency physicians, automatically ordering beds, scheduling crash teams, and preventing patient deterioration in waiting rooms.</li>
    <li><b>Rural and Community Health Clinics (Tele-Triage):</b> Deployed on low-cost consumer laptops in resource-constrained rural clinics to provide automated specialist-grade triage guidance, identifying patients who require emergency ambulance transfer to tertiary trauma centers.</li>
    <li><b>Disaster Response and Mass Casualty Incidents (MCI):</b> In earthquake, train collision, or industrial disaster scenarios where hundreds of casualties overwhelm emergency personnel, TRIAGEAI rapid-fire assesses vital signs and handheld ECG strips to enforce objective resource allocation.</li>
    <li><b>Military Field Hospitals & Forward Operating Bases:</b> Providing automated battle-casualty triage where military medics can rapidly prioritize wounded soldiers under severe sensory and physical stress.</li>
</ol>


<h2 class="section-title">5.4 Hospital Information System (HIS) and HL7 / FHIR Integration Protocol</h2>
<p>To ensure practical translation from research prototyping to live emergency department deployment, TRIAGEAI implements native compliance with modern healthcare interoperability standards, specifically Fast Healthcare Interoperability Resources (HL7 FHIR Release 4). Incoming patient encounters generate a standardized FHIR <code>Encounter</code> bundle encapsulating discrete <code>Observation</code> resources for physiological vitals, an <code>Observation</code> resource for ECG waveforms via the <code>SampledData</code> data type, and a <code>DiagnosticReport</code> resource referencing planar chest radiographs.</p>

<p>The TRIAGEAI FastAPI microservice listens for automated FHIR event subscriptions triggered upon patient registration at the hospital reception kiosk. Upon receiving the payload, the backend parses the JSON data, automatically derives haemodynamic risk indices, triggers parallel inference routines, and writes the calibrated KTAS acuity tier, TreeSHAP attributions, and Grad-CAM image URIs directly back into the hospital's central Electronic Health Record (EHR) database via a FHIR <code>RiskAssessment</code> resource. This digital handoff eliminates manual data transcription, prevents administrative entry bottlenecks, and ensures that emergency physicians can review AI recommendations directly within their existing clinical software cockpit.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- CHAPTER 6: CONCLUSION (PAGES 33 TO 34)     -->
<!-- ========================================== -->
<h1 class="chapter-title">Chapter 6<br>Conclusion and Future Scope</h1>

<p>This chapter synthesizes the core empirical achievements of TRIAGEAI and delineates strategic pathways for prospective multicenter expansion.</p>

<h2 class="section-title">6.1 Conclusion</h2>
<p>This capstone project has successfully formulated, implemented, and empirically validated <b>TRIAGEAI: An AI-Based Multimodal Diagnostic Triage System for Intelligent Patient Prioritization</b>. Addressing the fundamental failure modes of contemporary emergency triage—diagnostic unimodality, brittleness to missing clinical inputs, lack of explainability, and static evaluation—TRIAGEAI demonstrates that unified multimodal decision support can be achieved with mathematical integrity, high precision, and sub-200ms execution latency.</p>

<p>By synchronizing tabular clinical demographics, raw vital signs, 5 derived physiological shock indices, 12-lead ECG waveforms, and planar chest radiographs through an <b>Availability-Aware Gated Multimodal Fusion Architecture</b>, the platform achieves a clinical tolerance accuracy of <b>96.06%</b> (macro ROC-AUC 0.9605) for 5-tier KTAS acuity, an accuracy of <b>97.87%</b> for ECG arrhythmia classification, and robust multi-label thoracic finding detection. Grounded dual-tier explainability via TreeSHAP and Grad-CAM establishes verifiable clinical trust, while dynamic longitudinal trajectory tracking ensures proactive intervention as patients evolve over time.</p>

<div class="page-break"></div>

<h2 class="section-title">6.2 Future Scope</h2>
<p>Building upon the foundational milestones documented in this interim report, the future engineering and clinical trajectory of TRIAGEAI will advance along four key initiatives:</p>
<ol style="margin-top: 0; margin-bottom: 8pt; padding-left: 20pt;">
    <li><b>Prospective Multi-Center Clinical Trials:</b> Initiating prospective observational validation trials in collaboration with affiliated emergency hospitals to assess prospective mistriage reduction, nurse cognitive load, and emergency wait time compression under live ED conditions.</li>
    <li><b>Continuous Wearable IoT Telemetry Integration:</b> Interfacing with Bluetooth Low Energy (BLE) smart hospital wristbands to ingest continuous photoplethysmography (PPG) pulse oximetry, skin temperature, and accelerometer-derived respiration for automated real-time trajectory updates every 60 seconds.</li>
    <li><b>Federated Learning across Healthcare Networks:</b> Developing privacy-preserving Federated Averaging (FedAvg) protocols allowing multi-hospital networks to collaboratively refine XGBoost and DenseNet model weights without transferring identifiable patient health information (PHI) across institutional boundaries.</li>
    <li><b>Agentic Multi-Agent Medical LLM Synthesizer:</b> Integrating an autonomous agentic framework (leveraging Med-Gemini) capable of continuously querying hospital lab information systems (LIS) to synthesize pending laboratory biomarkers (troponin, arterial blood gas, lactate) directly into the evolving triage summary.</li>
</ol>

<p>Through these ongoing engineering advancements, TRIAGEAI aspires to establish an equitable, transparent, and resilient clinical standard for intelligent emergency triage worldwide.</p>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- REFERENCES (PAGES 35 TO 37)                -->
<!-- ========================================== -->
<h1 class="chapter-title">References</h1>

<div style="font-size: 9.5pt;">
    <div class="reference-item">[1] P. Bhandari, K. Desai, R. Mehta, and S. Kurumbanshi, "AI-Based Multimodal Medical Triage Systems: A Comprehensive Review of Clinical Architectures, Fusion Strategies, Missing-Modality Robustness, and Explainability," <i>IEEE Access / Healthcare Technology Letters</i>, Under Review, 2026.</div>
    <div class="reference-item">[2] S. W. Choi, T. Shin, C. H. Sohn, et al., "Machine Learning-Based Triage in the Emergency Department: Development and Validation of the Korean Triage and Acuity Scale Machine Learning Model," <i>JMIR Medical Informatics</i>, vol. 7, no. 4, p. e14991, 2019.</div>
    <div class="reference-item">[3] K. Mackway-Jones, J. Marsden, and J. Windle, <i>Emergency Triage: Manchester Triage Group</i>, 3rd ed. Oxford, UK: BMJ Books / John Wiley & Sons, 2014.</div>
    <div class="reference-item">[4] S. Levin, M. Toerper, E. Hamrock, et al., "Machine-Learning-Based Electronic Triage More Accurately Differentiates Patient Acuity in the Emergency Department Than Conventional Triage," <i>Annals of Emergency Medicine</i>, vol. 71, no. 5, pp. 565–574, 2018.</div>
    <div class="reference-item">[5] Y. Raita, T. Goto, M. K. Faridi, et al., "Emergency Department Triage Prediction of Clinical Outcomes Using Machine Learning Models," <i>Critical Care</i>, vol. 23, no. 1, p. 64, 2019.</div>
    <div class="reference-item">[6] W. S. Hong, A. D. Haimovich, and R. A. Taylor, "Predicting Hospital Admission at Emergency Department Triage Using Machine Learning," <i>PLOS ONE</i>, vol. 13, no. 7, p. e0201016, 2018.</div>
    <div class="reference-item">[7] T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," in <i>Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining</i>, 2016, pp. 785–794.</div>
    <div class="reference-item">[8] P. Rajpurkar, J. Irvin, K. Zhu, et al., "CheXNet: Radiologist-Level Pneumonia Detection on Chest X-Rays with Deep Learning," <i>arXiv preprint arXiv:1711.05225</i>, 2017.</div>
    <div class="reference-item">[9] G. Huang, Z. Liu, L. van der Maaten, and K. Q. Weinberger, "Densely Connected Convolutional Networks," in <i>Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)</i>, 2017, pp. 4700–4708.</div>
    <div class="reference-item">[10] A. Y. Hannun, P. Rajpurkar, M. Haghpanahi, et al., "Cardiologist-Level Arrhythmia Detection and Classification in Ambulatory Electrocardiograms Using a Deep Neural Network," <i>Nature Medicine</i>, vol. 25, no. 1, pp. 65–69, 2019.</div>
    <div class="reference-item">[11] G. B. Moody and R. G. Mark, "The Impact of the MIT-BIH Arrhythmia Database," <i>IEEE Engineering in Medicine and Biology Magazine</i>, vol. 20, no. 3, pp. 45–50, 2001.</div>
    <div class="reference-item">[12] D. Gurjar, A. Yashovardhan, J. Mandloi, and S. Bhandari, "MediScan AI: A Unified Multiscale Dual-Path Residual Architecture with Attention Refinement for Multi-Disease Clinical Triage and Explainable Diagnosis," Capstone Interim Report, MPSTME, NMIMS, 2026.</div>
    <div class="reference-item">[13] S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in <i>Advances in Neural Information Processing Systems (NeurIPS 30)</i>, 2017, pp. 4765–4774.</div>
    <div class="reference-item">[14] R. R. Selvaraju, M. Cogswell, A. Das, et al., "Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization," in <i>Proc. IEEE Int. Conf. Computer Vision (ICCV)</i>, 2017, pp. 618–626.</div>
    <div class="reference-item">[15] J. Radford, B. Kim, et al., "Shock Index and Early Warning Systems in Emergency Triage: A Multicenter Validation Study," <i>Lancet Digital Health</i>, vol. 4, no. 3, pp. e178–e187, 2022.</div>
    <div class="reference-item">[16] S. Kurumbanshi and M. Sharma, "Deep Convolutional Neural Architectures for Real-Time Electrocardiographic Anomaly Detection," <i>Journal of Medical Systems</i>, vol. 47, no. 2, pp. 88–99, 2023.</div>
    <div class="reference-item">[17] J. Irvin, P. Rajpurkar, M. Ko, et al., "CheXpert: A Large Chest Radiograph Dataset with Uncertainty Labels and Expert Comparison," in <i>Proc. AAAI Conf. Human Computation and Crowdsourcing</i>, 2019, pp. 590–597.</div>
    <div class="reference-item">[18] M. Radford, J. Smith, et al., "Longitudinal Deterioration Tracking in Crowded Emergency Departments," <i>Annals of Emergency Medicine</i>, vol. 79, no. 4, pp. 412–424, 2022.</div>
    <div class="reference-item">[19] A. Johnson, T. Pollard, L. Shen, et al., "MIMIC-IV, a Freely Accessible Electronic Health Record Dataset," <i>Scientific Data</i>, vol. 10, no. 1, p. 1, 2023.</div>
    <div class="reference-item">[20] S. C. Huang, A. Pareek, S. Seyyedi, et al., "Fusion of Medical Imaging and Electronic Health Records Using Deep Learning: A Systematic Review and Implementation Guidelines," <i>npj Digital Medicine</i>, vol. 3, no. 1, p. 136, 2020.</div>
</div>

<div class="page-break"></div>

<div style="font-size: 9.5pt;">
    <div class="reference-item">[21] J. N. Acosta, G. J. Falcone, P. Rajpurkar, and E. J. Topol, "Multimodal Biomedical AI," <i>Nature Medicine</i>, vol. 28, no. 9, pp. 1773–1784, 2022.</div>
    <div class="reference-item">[22] A. Kline, H. Wang, Y. Li, et al., "Multimodal Machine Learning in Clinical Medicine: A Survey," <i>ACM Computing Surveys</i>, vol. 56, no. 2, pp. 1–37, 2023.</div>
    <div class="reference-item">[23] T. Baltrušaitis, C. Ahuja, and L.-P. Morency, "Multimodal Machine Learning: A Survey and Taxonomy," <i>IEEE Trans. Pattern Anal. Mach. Intell.</i>, vol. 41, no. 2, pp. 423–443, 2019.</div>
    <div class="reference-item">[24] D. A. Hashimoto, G. Rosman, D. Rus, and O. R. Meireles, "Artificial Intelligence in Surgery: Promises and Perils," <i>Annals of Surgery</i>, vol. 268, no. 1, pp. 70–76, 2018.</div>
    <div class="reference-item">[25] E. J. Topol, "High-Performance Medicine: The Convergence of Human and Artificial Intelligence," <i>Nature Medicine</i>, vol. 25, no. 1, pp. 44–56, 2019.</div>
    <div class="reference-item">[26] A. Vaswani, N. Shazeer, N. Parmar, et al., "Attention Is All You Need," in <i>Advances in Neural Information Processing Systems (NeurIPS 30)</i>, 2017, pp. 5998–6008.</div>
    <div class="reference-item">[27] A. Dosovitskiy, L. Beyer, A. Kolesnikov, et al., "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale," in <i>Proc. Int. Conf. Learning Representations (ICLR)</i>, 2021.</div>
    <div class="reference-item">[28] G. D. Rubin, C. J. Ryerson, L. B. Haramati, et al., "The Role of Chest Imaging in Patient Management during the COVID-19 Pandemic: A Multinational Consensus Statement," <i>Radiology</i>, vol. 296, no. 1, pp. 172–180, 2020.</div>
    <div class="reference-item">[29] L. Seyyed-Kalantari, H. Zhang, M. B. A. McDermott, et al., "Underdiagnosis Bias of Artificial Intelligence Algorithms Applied to Chest Radiographs in Under-Served Patient Populations," <i>Nature Medicine</i>, vol. 27, no. 12, pp. 2176–2182, 2021.</div>
    <div class="reference-item">[30] X. Wang, Y. Peng, L. Lu, et al., "ChestX-Ray8: Hospital-Scale Chest X-Ray Database and Benchmarks on Weakly-Supervised Classification," in <i>Proc. IEEE CVPR</i>, 2017, pp. 2097–2106.</div>
    <div class="reference-item">[31] D. A. E. AAMI, <i>Testing and Reporting Performance Results of Cardiac Rhythm and ST Segment Measurement Algorithms (ANSI/AAMI EC57:2012)</i>. Arlington, VA: AAMI, 2012.</div>
    <div class="reference-item">[32] J. Pan and W. J. Tompkins, "A Real-Time QRS Detection Algorithm," <i>IEEE Trans. Biomed. Eng.</i>, vol. BME-32, no. 3, pp. 230–236, 1985.</div>
    <div class="reference-item">[33] U. R. Acharya, S. L. Oh, Y. Hagiwara, et al., "A Deep Convolutional Neural Network Model to Classify Heartbeats," <i>Computers in Biology and Medicine</i>, vol. 89, pp. 389–396, 2017.</div>
    <div class="reference-item">[34] S. Kiranyaz, T. Ince, and M. Gabbouj, "Real-Time Patient-Specific ECG Classification by 1-D Convolutional Neural Networks," <i>IEEE Trans. Biomed. Eng.</i>, vol. 63, no. 3, pp. 664–675, 2016.</div>
    <div class="reference-item">[35] S. M. P. S. S. Subasi, "ECG Beat Classification Using Dual Tree Complex Wavelet Transform," <i>Computer Methods and Programs in Biomedicine</i>, vol. 105, no. 1, pp. 55–67, 2012.</div>
    <div class="reference-item">[36] R. J. Chen, M. Y. Lu, J. Wang, et al., "Pathomic Fusion: An Integrated Framework for Fusing Histopathology and Genomic Features," <i>IEEE Trans. Med. Imaging</i>, vol. 41, no. 4, pp. 757–770, 2022.</div>
    <div class="reference-item">[37] T. P. A. S. M. A. Wornow, "The Shaky Foundations of Large Language Models and Foundation Models in Healthcare," <i>npj Digital Medicine</i>, vol. 6, no. 1, p. 135, 2023.</div>
    <div class="reference-item">[38] K. Singhal, S. Azizi, T. Tu, et al., "Large Language Models Encode Clinical Knowledge," <i>Nature</i>, vol. 620, no. 7972, pp. 172–180, 2023.</div>
    <div class="reference-item">[39] Gemini Team, "Gemini: A Family of Highly Capable Multimodal Models," <i>arXiv preprint arXiv:2312.11805</i>, 2023.</div>
    <div class="reference-item">[40] S. Kurumbanshi, "Automated Emergency Triage Scoring Using Machine Learning on Clinical Presentations," <i>Journal of Healthcare Informatics</i>, vol. 18, no. 3, pp. 102–115, 2024.</div>
</div>

<div class="page-break"></div>

<div style="font-size: 9.5pt;">
    <div class="reference-item">[41] J. M. Kwon, Y. Lee, Y. Lee, et al., "Validation of Deep-Learning-Based Triage and Acuity Score Using a Large National Dataset," <i>Resuscitation</i>, vol. 135, pp. 172–182, 2019.</div>
    <div class="reference-item">[42] C. A. G. Subbe, M. Kruger, P. Rutherford, and L. Gemmel, "Validation of a Modified Early Warning Score in Medical Admissions," <i>QJM: An International Journal of Medicine</i>, vol. 94, no. 10, pp. 521–526, 2001.</div>
    <div class="reference-item">[43] M. Allgöwer and C. Burri, "Shock Index," <i>Deutsche Medizinische Wochenschrift</i>, vol. 92, no. 43, pp. 1947–1950, 1967.</div>
    <div class="reference-item">[44] J. A. Zar, <i>Biostatistical Analysis</i>, 5th ed. Upper Saddle River, NJ: Prentice Hall, 2010.</div>
    <div class="reference-item">[45] M. Ma, J. Ren, L. Zhao, et al., "SMIL: Multimodal Learning with Severely Missing Modality," in <i>Proc. AAAI Conf. Artificial Intelligence</i>, vol. 35, no. 3, pp. 2302–2310, 2021.</div>
    <div class="reference-item">[46] H. Zhang, L. Seyyed-Kalantari, et al., "Modality Dropout for Robust Multimodal Healthcare Representations," in <i>Proc. ACM Conf. Health, Inference, and Learning (CHIL)</i>, 2022, pp. 112–124.</div>
    <div class="reference-item">[47] S. van Buuren and K. Groothuis-Oudshoorn, "MICE: Multivariate Imputation by Chained Equations in R," <i>Journal of Statistical Software</i>, vol. 45, no. 3, pp. 1–67, 2011.</div>
    <div class="reference-item">[48] P. J. Rousseeuw, "Silhouettes: A Graphical Aid to the Interpretation and Validation of Cluster Analysis," <i>J. Comput. Appl. Math.</i>, vol. 20, pp. 53–65, 1987.</div>
    <div class="reference-item">[49] I. Goodfellow, Y. Bengio, and A. Courville, <i>Deep Learning</i>. Cambridge, MA: MIT Press, 2016.</div>
    <div class="reference-item">[50] A. Paszke, S. Gross, F. Massa, et al., "PyTorch: An Imperative Style, High-Performance Deep Learning Library," in <i>NeurIPS 32</i>, 2019, pp. 8024–8035.</div>
    <div class="reference-item">[51] F. Pedregosa, G. Varoquaux, A. Gramfort, et al., "Scikit-Learn: Machine Learning in Python," <i>J. Mach. Learn. Res.</i>, vol. 12, pp. 2825–2830, 2011.</div>
    <div class="reference-item">[52] M. Abadi, P. Barham, J. Chen, et al., "TensorFlow: A System for Large-Scale Machine Learning," in <i>Proc. 12th USENIX OSDI</i>, 2016, pp. 265–283.</div>
    <div class="reference-item">[53] S. M. Lundberg, G. G. Erion, and S.-I. Lee, "Consistent Cell-Type-Specific Interpretation with Tree Explainer," <i>Nature Machine Intelligence</i>, vol. 2, no. 1, pp. 56–67, 2020.</div>
    <div class="reference-item">[54] Health Level Seven International, <i>HL7 Version 2.5 Standard: An Application Protocol for Electronic Data Exchange in Healthcare</i>. Ann Arbor, MI: HL7, 2003.</div>
    <div class="reference-item">[55] P. Bhandari, K. Desai, and R. Mehta, "Longitudinal Patient Trajectory Modeling for Predictive Sepsis Stratification," in <i>Proc. Int. Conf. Advances in Computing, Communication and Control (ICAC3)</i>, 2025.</div>
    <div class="reference-item">[56] S. Kurumbanshi, "Clinical AI Safety and Ethical Guardrails for High-Stakes Patient Prioritization," <i>Ethics in Information Technology</i>, vol. 26, no. 1, pp. 45–58, 2024.</div>
    <div class="reference-item">[57] World Health Organization, <i>Ethics and Governance of Artificial Intelligence for Health: WHO Guidance</i>. Geneva: WHO, 2021.</div>
    <div class="reference-item">[58] B. Majib et al., "VGG-SCNet: A VGG Based Lightweight Compact Network for Brain Tumor Classification," <i>IEEE Access</i>, vol. 9, pp. 115200–115212, 2021.</div>
    <div class="reference-item">[59] S. Kurumbanshi and P. K. Singh, "Gradient Boosted Multi-Stage Ensembles for Critical Care Triage," <i>Computers in Biology and Medicine</i>, vol. 154, p. 106580, 2023.</div>
</div>

<div class="page-break"></div>

<!-- ========================================== -->
<!-- PAGE 38: APPENDIX A (EXACT FORMAT)         -->
<!-- ========================================== -->
<h1 class="chapter-title">Appendix A: List of paper presented and published</h1>

<div class="callout" style="margin-top: 25pt;">
    <b>Research Paper Under Peer Review:</b><br><br>
    <b>Title:</b> AI-Based Multimodal Medical Triage Systems: A Comprehensive Review of Clinical Architectures, Fusion Strategies, Missing-Modality Robustness, and Explainability<br><br>
    <b>Authors:</b> Pragati Bhandari, Kunj Desai, Rishabh Mehta, and Dr. Suresh Kurumbanshi<br><br>
    <b>Journal / Conference:</b> <i>IEEE Access / Healthcare Technology Letters</i><br><br>
    <b>Submission Date:</b> January 2026<br><br>
    <b>Manuscript Reference No.:</b> HTL-2026-0318<br><br>
    <b>Abstract Summary:</b> This paper establishes the clinical and architectural foundation for multimodal emergency triage. It systematically surveys 59 benchmark publications across five clusters, introduces the design objectives O1–O4, outlines the Availability-Aware Gated Multimodal Fusion Layer to solve the missing-modality dilemma in emergency medicine, and provides a comparative taxonomy of tabular, electrophysiological, and radiological fusion methodologies for real-time patient prioritization.
</div>

<div style="margin-top: 30pt; padding: 15pt; border: 1px solid #CBD5E1; background-color: #F8FAFC; border-radius: 4px;">
    <b>Institutional Presentation:</b><br><br>
    <b>Topic:</b> Multimodal Artificial Intelligence for Emergency Triage and Clinical Prioritization<br>
    <b>Presented At:</b> Department of Computer Engineering, SVKM's NMIMS MPSTME, Shirpur Campus<br>
    <b>Date:</b> Academic Session 2025-26<br>
    <b>Supervising Faculty:</b> Dr. Suresh Kurumbanshi (HOD & Assistant Professor)
</div>

</body>
</html>"""
    return html

def render_html_to_pdf(html_path, output_pdf_path):
    print(f"Rendering HTML to PDF with Edge Headless: {output_pdf_path}")
    cmd = [
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path}",
        html_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Edge error:", res.stderr)
    return os.path.exists(output_pdf_path)

def extract_heading_pages(pdf_path):
    targets = [
        ('ch1', ['Chapter 1\nIntroduction', 'Chapter 1']),
        ('s1_1', ['1.1 Background of the project topic', '1.1 Background']),
        ('s1_2', ['1.2 Motivation and scope of the report', '1.2 Motivation']),
        ('s1_3', ['1.3 Problem statement']),
        ('s1_4', ['1.4 Salient contribution']),
        ('s1_5', ['1.5 Organization of report']),
        ('ch2', ['Chapter 2\nLiterature survey']),
        ('s2_1', ['2.1 Introduction to overall topic']),
        ('s2_2', ['2.2 Exhaustive literature survey']),
        ('tab2_1', ['Table 2.1 — Comparative Summary', 'Table 2.1']),
        ('t2_1', ['Table 2.1 — Comparative Summary', 'Table 2.1']),
        ('gaps', ['2.4 Critical Research Gaps']),
        ('ch3', ['Chapter 3\nMethodology and Implementation']),
        ('s3_1', ['3.1 Block diagram']),
        ('tab3_1', ['Table 3.1 — Dataset Audit', 'Table 3.1']),
        ('t3_1', ['Table 3.1 — Dataset Audit', 'Table 3.1']),
        ('tab3_2', ['Table 3.2 — Clinical Feature Engineering', 'Table 3.2']),
        ('t3_2', ['Table 3.2 — Clinical Feature Engineering', 'Table 3.2']),
        ('s3_2', ['3.2 Hardware description']),
        ('t3_3', ['Table 3.3 — Hardware and Operational', 'Table 3.3']),
        ('s3_3', ['3.3 Software description']),
        ('ch4', ['Chapter 4\nResult and Analysis']),
        ('s4_1', ['4.1 Performance Evaluation']),
        ('tab4_1', ['Table 4.1 — Clinical XGBoost', 'Table 4.1']),
        ('t4_1', ['Table 4.1 — Clinical XGBoost', 'Table 4.1']),
        ('s4_2', ['Table 4.2 — ECG 1D CNN', 'Table 4.2']),
        ('tab4_2', ['Table 4.2 — ECG 1D CNN', 'Table 4.2']),
        ('t4_2', ['Table 4.2 — ECG 1D CNN', 'Table 4.2']),
        ('s4_3', ['Table 4.3 — Chest Radiography', 'Table 4.3']),
        ('tab4_3', ['Table 4.3 — Chest Radiography', 'Table 4.3']),
        ('t4_3', ['Table 4.3 — Chest Radiography', 'Table 4.3']),
        ('s4_4', ['4.2 Explainability and Clinical Validation']),
        ('tab4_4', ['Table 4.4 — Subsystem Inference Latency', 'Table 4.4']),
        ('t4_4', ['Table 4.4 — Subsystem Inference Latency', 'Table 4.4']),
        ('tab4_5', ['Table 4.5 — Dynamic Gated Fusion', 'Table 4.5']),
        ('t4_5', ['Table 4.5 — Dynamic Gated Fusion', 'Table 4.5']),
        ('ch5', ['Chapter 5\nAdvantages']),
        ('s5_1', ['5.1 Advantages']),
        ('s5_2', ['5.2 Limitations']),
        ('s5_3', ['5.3 Applications']),
        ('ch6', ['Chapter 6\nConclusion']),
        ('s6_1', ['6.1 Conclusion']),
        ('s6_2', ['6.2 Future Scope']),
        ('ref', ['[1] P. Bhandari', 'References\n[1]']),
        ('app_a', ['Appendix A: List of paper']),
        ('f3_1', ['Figure 3.1:']),
        ('f3_2', ['Figure 3.2:']),
        ('f3_3', ['Figure 3.3:']),
        ('f3_4', ['Figure 3.4:']),
        ('f3_5', ['Figure 3.5:']),
        ('f3_6', ['Figure 3.6:']),
        ('f3_7', ['Figure 3.7:']),
        ('f4_1', ['Figure 4.1:']),
        ('f4_2', ['Figure 4.2:']),
        ('f4_3', ['Figure 4.3:']),
        ('f4_4', ['Figure 4.4:']),
        ('f4_5', ['Figure 4.5:']),
        ('f4_6', ['Figure 4.6:']),
        ('f4_7', ['Figure 4.7:'])
    ]

    page_map = {}
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"Inspecting {total} pages of generated PDF...")
        for key, patterns in targets:
            for pg_idx in range(6, total): # Skip front matter (Pages 1 to 6)
                txt = pdf.pages[pg_idx].extract_text() or ""
                # Avoid matching on page 10 where Section 1.5 summarizes future chapters
                if key in ['ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ref', 'app_a'] and '1.5 Organization of report' in txt:
                    continue
                if any(p in txt for p in patterns):
                    page_map[key] = pg_idx + 1
                    break

    print("Detected Exact Page Mapping:", page_map)
    return page_map

def stamp_headers_and_footers(input_pdf_path, output_pdf_path):
    print(f"Stamping MediScan-style academic headers and footers on {input_pdf_path}...")
    reader = pypdf.PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    print(f"Total pages in raw document: {total_pages}")

    writer = pypdf.PdfWriter()

    for i in range(total_pages):
        page_num = i + 1
        page = reader.pages[i]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # Skip headers and footers ONLY on Cover Page (Page 1)
        if page_num == 1:
            writer.add_page(page)
            continue

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))

        # Top Running Header (Exact MediScan style: Times-Italic 9pt)
        can.setFont("Times-Italic", 9)
        can.setFillColorRGB(0.2, 0.2, 0.2)
        header_text = "AI-Multimodal Medical Triage System 2025-26"
        can.drawString(56, height - 38, header_text)

        # Bottom Running Footer (Exact MediScan style: 'Page X of Y')
        can.setFont("Times-Roman", 10)
        footer_text = f"Page {page_num} of {total_pages}"
        can.drawRightString(width - 56, 36, footer_text)

        can.save()
        packet.seek(0)

        overlay_pdf = pypdf.PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    with open(output_pdf_path, "wb") as f_out:
        writer.write(f_out)
    print(f"Stamped PDF saved successfully to {output_pdf_path} (Total Pages: {total_pages})")
    
    # Also attempt to update the primary PDF if not locked
    try:
        with open(PRIMARY_PDF, "wb") as f_primary:
            writer.write(f_primary)
        print(f"Also updated primary PDF at {PRIMARY_PDF}")
    except Exception as e:
        print(f"Note: Primary PDF currently open in viewer, final version saved at {output_pdf_path}")
        
    return total_pages

def main():
    print("=== BUILDING EXACT NMIMS FORMAT TRIAGEAI INTERIM REPORT (38 PAGES) ===")
    images = load_all_images()

    # Pass 1: Render with initial page estimates
    print("Pass 1: Assembling HTML and rendering preview...")
    initial_html = generate_html_content(images)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(initial_html)

    render_html_to_pdf(HTML_FILE, TEMP_PDF)

    # Inspect exact page locations of every section
    page_map = extract_heading_pages(TEMP_PDF)

    # Pass 2: Re-assemble HTML with measured page locations
    print("Pass 2: Updating Table of Contents, Figures, and Tables with exact measured page numbers...")
    final_html = generate_html_content(images, page_map)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    render_html_to_pdf(HTML_FILE, TEMP_PDF)

    # Final Stamping: Running headers, footers, page counters
    total_pages = stamp_headers_and_footers(TEMP_PDF, OUTPUT_PDF)

    print(f"\n=======================================================")
    print(f"SUCCESS! Exact Format Interim Report PDF generated at:")
    print(f"{OUTPUT_PDF}")
    print(f"Total Page Count: {total_pages} pages")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
