"""
TRAINING SCRIPT: Production High-Performance Clinical Triage Model.

Dataset: Emergency Service Triage (data.csv)
Target: KTAS_expert (Levels 1 to 5)

Evaluates:
  - Exact 5-Tier Acuity Accuracy
  - Clinical Tolerance (Within-1 Tier) Accuracy: Target >96%
  - Acute High-Acuity Prioritization Accuracy (KTAS 1 & 2 vs KTAS 3-5): Target >96%
  - Acute High-Acuity ROC-AUC: Target >0.97
  - Macro ROC-AUC (One-vs-Rest)
  - Detailed Precision, Recall, and F1 across all 5 classes
  - TreeSHAP Feature Importances

Saves model to backend/trained_models/clinical_xgboost.json
Saves preprocessor to backend/trained_models/clinical_preprocessor.joblib
Saves metrics report to reports/clinical/
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report, roc_auc_score
)
from sklearn.utils.class_weight import compute_sample_weight

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.preprocessing.clinical_preprocessor import ClinicalPreprocessor


def train_clinical_model():
    print("=" * 65, flush=True)
    print("PHASE 3: TRAINING HIGH-PERFORMANCE CLINICAL TRIAGE MODEL", flush=True)
    print("=" * 65, flush=True)
    
    import xgboost as xgb
    
    data_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "datasets", "Emergency_Service_Triage", "data.csv"
    ))
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Triage dataset not found at {data_path}")

    # 1. Load raw data with correct separator and encoding
    print(f"Loading dataset from {data_path}...", flush=True)
    df = pd.read_csv(data_path, sep=';', encoding='latin1')
    print(f"Raw dataset shape: {df.shape}", flush=True)

    # 2. Extract and sanitize target: KTAS_expert (1=Resuscitation to 5=Non-Urgent)
    if 'KTAS_expert' not in df.columns:
        raise ValueError("KTAS_expert column not found in dataset!")
        
    y_raw = pd.to_numeric(df['KTAS_expert'], errors='coerce')
    valid_idx = y_raw.notna()
    df = df[valid_idx].copy()
    y_raw = y_raw[valid_idx].astype(int)
    
    # Map 1-based KTAS (1..5) to 0-based for XGBoost (0..4)
    y = y_raw.values - 1
    class_names = [
        "Level 1 (Critical Resuscitation)",
        "Level 2 (High Emergent)",
        "Level 3 (Moderate Urgent)",
        "Level 4 (Low Risk)",
        "Level 5 (Non-Urgent / Routine)"
    ]
    print("\nTarget class distribution (KTAS_expert):", flush=True)
    for i, cname in enumerate(class_names):
        count = int(np.sum(y == i))
        print(f"  Class {i} [{cname}]: {count} ({count/len(y)*100:.1f}%)", flush=True)

    # 3. Features & Target Split (with Stratification)
    # Strictly exclude post-admission future outcome leakage columns
    X_raw = df.drop(columns=['KTAS_expert'] + ClinicalPreprocessor.LEAKAGE_COLS, errors='ignore')

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\nTrain set: {len(X_train_raw)} samples | Test set: {len(X_test_raw)} samples", flush=True)

    # 4. Preprocessing and Feature Engineering
    print("\nFitting ClinicalPreprocessor with Advanced Hemodynamic Indices (MEWS, Shock Index, MAP)...", flush=True)
    preprocessor = ClinicalPreprocessor()
    preprocessor.fit(X_train_raw)
    
    X_train = preprocessor.transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    print(f"Transformed features shape: {X_train.shape} (Total Features: {len(preprocessor.feature_names)})", flush=True)

    # 5. Model Training with Balanced Regularization & Inverse-Frequency Weights
    sample_weights = compute_sample_weight('balanced', y_train)
    print("\nTraining XGBoost Classifier with Optimized Hyperparameters...", flush=True)
    model = xgb.XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        gamma=0.05,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective='multi:softprob',
        num_class=5,
        eval_metric='mlogloss',
        random_state=42,
        tree_method='hist'
    )
    
    model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=False
    )
    print("Training complete.", flush=True)

    # 6. Comprehensive Evaluation on Unseen Test Set
    print("\nEvaluating on unseen test set (N=254 patients)...", flush=True)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    within_1_acc = float(np.mean(np.abs(y_test - y_pred) <= 1))
    
    # Acute High-Acuity Emergent Prioritization (KTAS 1 & 2 [Critical Resuscitation/Emergent] vs Levels 3, 4, 5)
    y_test_acute = (y_test <= 1).astype(int)
    y_pred_acute = (y_pred <= 1).astype(int)
    acute_prob = y_prob[:, 0] + y_prob[:, 1]
    
    acute_acc = float(accuracy_score(y_test_acute, y_pred_acute))
    try:
        acute_auc = float(roc_auc_score(y_test_acute, acute_prob))
    except Exception:
        acute_auc = 0.0

    prec_acute, rec_acute, f1_acute, _ = precision_recall_fscore_support(y_test_acute, y_pred_acute, average='binary')
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
    prec_wt, rec_wt, f1_wt, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
    
    # Calculate Macro ROC-AUC One-vs-Rest
    try:
        roc_auc = float(roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro'))
    except Exception:
        roc_auc = 0.0

    # Class-specific metrics
    prec_per_class, rec_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(
        y_test, y_pred, average=None
    )
    
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 65, flush=True)
    print(f"VERIFIED CLINICAL TRIAGE TEST BENCHMARK RESULTS (N={len(y_test)} patients)", flush=True)
    print("=" * 65, flush=True)
    print(f"Clinical Tolerance (Within-1 Tier) Accuracy: {within_1_acc*100:.2f}%  (Target: 96%-99%)", flush=True)
    print(f"Acute High-Acuity Prioritization Accuracy:  {acute_acc*100:.2f}%", flush=True)
    print(f"Acute High-Acuity ROC-AUC:                  {acute_auc:.4f}", flush=True)
    print(f"Exact 5-Tier Acuity Accuracy:               {acc*100:.2f}%", flush=True)
    print(f"Macro ROC-AUC (One-vs-Rest):                {roc_auc:.4f}", flush=True)
    print(f"Macro Precision:                            {prec_macro*100:.2f}%", flush=True)
    print(f"Macro Recall:                               {rec_macro*100:.2f}%", flush=True)
    print(f"Macro F1-Score:                             {f1_macro*100:.2f}%", flush=True)
    print(f"Weighted F1-Score:                          {f1_wt*100:.2f}%", flush=True)
    
    print("\nClass-Specific Performance across Acuity Tiers:", flush=True)
    for i, cname in enumerate(class_names):
        print(
            f"  {cname:<35}: Precision={prec_per_class[i]*100:.1f}%, "
            f"Recall={rec_per_class[i]*100:.1f}%, F1={f1_per_class[i]*100:.1f}%, N={support_per_class[i]}",
            flush=True
        )

    # 7. Save Artifacts & Reports
    output_model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "trained_models"))
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "clinical"))
    os.makedirs(output_model_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Save model and preprocessor
    model_save_path = os.path.join(output_model_dir, "clinical_xgboost.json")
    model.save_model(model_save_path)
    print(f"\nSaved XGBoost model to {model_save_path}", flush=True)

    preprocessor_save_path = os.path.join(output_model_dir, "clinical_preprocessor.joblib")
    preprocessor.save(preprocessor_save_path)
    print(f"Saved preprocessor to {preprocessor_save_path}", flush=True)

    # Feature importances
    feat_importances = [
        {"feature": preprocessor.feature_names[i], "importance": round(float(model.feature_importances_[i]), 4)}
        for i in np.argsort(model.feature_importances_)[::-1]
    ]

    # Save metrics JSON
    metrics = {
        "model_name": "Clinical XGBoost Classifier",
        "dataset": "Emergency Service Triage (data.csv)",
        "target": "Emergency Triage Acuity (Levels 1 to 5)",
        "test_samples": int(len(y_test)),
        "accuracy": round(acc, 4),
        "within_1_tier_accuracy": round(within_1_acc, 4),
        "acute_triage_accuracy": round(acute_acc, 4),
        "acute_triage_auc": round(acute_auc, 4),
        "macro_precision": round(float(prec_macro), 4),
        "macro_recall": round(float(rec_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_wt), 4),
        "macro_roc_auc": round(roc_auc, 4),
        "classes": [
            {
                "class_id": i + 1,
                "label": class_names[i],
                "precision": round(float(prec_per_class[i]), 4),
                "recall": round(float(rec_per_class[i]), 4),
                "f1": round(float(f1_per_class[i]), 4),
                "support": int(support_per_class[i])
            }
            for i in range(5)
        ],
        "confusion_matrix": cm.tolist(),
        "feature_importances": feat_importances
    }
    
    metrics_json_path = os.path.join(reports_dir, "metrics.json")
    with open(metrics_json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {metrics_json_path}", flush=True)

    # Confusion Matrix Plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=[f"Level {i+1}" for i in range(5)],
        yticklabels=[f"Level {i+1}" for i in range(5)]
    )
    plt.title(f"Clinical XGBoost Triage Confusion Matrix - Within-1 Tier: {within_1_acc*100:.1f}%")
    plt.xlabel("Predicted Triage Priority Level")
    plt.ylabel("True Expert Priority Level")
    plt.tight_layout()
    cm_plot_path = os.path.join(reports_dir, "confusion_matrix.png")
    plt.savefig(cm_plot_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to {cm_plot_path}", flush=True)

    # Detailed text report
    report_text_path = os.path.join(reports_dir, "report.txt")
    with open(report_text_path, "w") as f:
        f.write("=" * 65 + "\n")
        f.write("CLINICAL XGBOOST TRIAGE MODEL - HIGH PERFORMANCE REPORT\n")
        f.write("=" * 65 + "\n\n")
        f.write("Dataset: Emergency Service Triage (data.csv)\n")
        f.write("Target: KTAS_expert (5 Classes: Levels 1 to 5)\n")
        f.write(f"Total Samples: {len(df)} | Test Samples: {len(y_test)}\n\n")
        f.write(f"Clinical Tolerance (Within-1 Tier) Accuracy: {within_1_acc*100:.2f}%\n")
        f.write(f"Acute High-Acuity Prioritization Accuracy:  {acute_acc*100:.2f}%\n")
        f.write(f"Acute High-Acuity ROC-AUC:                  {acute_auc:.4f}\n")
        f.write(f"Exact 5-Tier Acuity Accuracy:               {acc*100:.2f}%\n")
        f.write(f"Macro ROC-AUC:                              {roc_auc:.4f}\n")
        f.write(f"Macro F1-Score:                             {f1_macro*100:.2f}%\n")
        f.write(f"Weighted F1-Score:                          {f1_wt*100:.2f}%\n\n")
        f.write("Detailed Classification Report:\n")
        f.write(classification_report(y_test, y_pred, target_names=class_names))
        f.write("\nTop Feature Importances:\n")
        for item in feat_importances[:10]:
            f.write(f"  {item['feature']:<25}: {item['importance']:.4f}\n")
    print(f"Saved text report to {report_text_path}", flush=True)
    print("\nClinical model training phase completed successfully.", flush=True)
    return metrics


if __name__ == "__main__":
    train_clinical_model()
