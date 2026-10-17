"""
TRAINING SCRIPT: ECG 1D CNN Model.

Dataset: ECG HeartBeat Categorization (mitbih_train.csv, mitbih_test.csv)
Target: 5 AAMI Arrhythmia Categories:
  0: Normal Rhythm (N)
  1: Supraventricular Ectopic (S)
  2: Ventricular Ectopic / PVC (V)
  3: Fusion Beat (F)
  4: Unknown / Paced (Q)

Evaluates: Accuracy, Precision, Recall, F1, Confusion Matrix.
Saves model to backend/trained_models/ecg_1dcnn.pt
Saves metrics report to reports/ecg/
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_class_weight

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.models.ecg_cnn import ECG1DCNN
from backend.app.preprocessing.ecg_preprocessor import ECGPreprocessor


def train_ecg_model():
    print("=" * 60)
    print("PHASE 4: TRAINING ECG 1D CNN ARRHYTHMIA MODEL")
    print("=" * 60)
    
    device = torch.device("cpu")
    print(f"Using compute device: {device}")
    
    ecg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets", "ECG_HeartBeat_Categorization"))
    train_csv = os.path.join(ecg_dir, "mitbih_train.csv")
    test_csv = os.path.join(ecg_dir, "mitbih_test.csv")
    
    if not os.path.exists(train_csv) or not os.path.exists(test_csv):
        raise FileNotFoundError(f"ECG datasets not found at {train_csv} or {test_csv}")

    # 1. Load balanced subset of training data for fast, robust CPU convergence
    print(f"Loading training data from {train_csv}...")
    # Sample up to 5,000 per class from training set to create balanced training set of ~18,000 beats
    train_df = pd.read_csv(train_csv, header=None)
    X_train_raw = train_df.iloc[:, :-1].values
    y_train_raw = train_df.iloc[:, -1].values.astype(int)

    # Class-stratified sub-sampling to balance the extreme class imbalance (Normal is 82%)
    balanced_indices = []
    max_samples_per_class = 4000
    for c in range(5):
        c_idx = np.where(y_train_raw == c)[0]
        if len(c_idx) > max_samples_per_class:
            np.random.seed(42)
            c_idx = np.random.choice(c_idx, max_samples_per_class, replace=False)
        balanced_indices.extend(c_idx)

    np.random.shuffle(balanced_indices)
    X_train_sub = X_train_raw[balanced_indices]
    y_train_sub = y_train_raw[balanced_indices]
    
    print(f"Training subset selected: {len(X_train_sub)} samples")
    for c in range(5):
        print(f"  Class {c} samples: {np.sum(y_train_sub == c)}")

    # 2. Load test data (full test set or balanced test subset)
    print(f"\nLoading test data from {test_csv}...")
    test_df = pd.read_csv(test_csv, header=None)
    X_test_raw = test_df.iloc[:, :-1].values
    y_test_raw = test_df.iloc[:, -1].values.astype(int)
    
    # Sub-sample test set for fast evaluation (~4,000 beats)
    test_indices = []
    for c in range(5):
        c_idx = np.where(y_test_raw == c)[0]
        sample_n = min(len(c_idx), 800)
        np.random.seed(42)
        test_indices.extend(np.random.choice(c_idx, sample_n, replace=False))
    X_test_sub = X_test_raw[test_indices]
    y_test_sub = y_test_raw[test_indices]
    print(f"Test evaluation set: {len(X_test_sub)} samples")

    # 3. Min-Max normalization of 187-sample signal leads
    X_train_norm = np.array([ECGPreprocessor.normalize_signal(s) for s in X_train_sub], dtype=np.float32)
    X_test_norm = np.array([ECGPreprocessor.normalize_signal(s) for s in X_test_sub], dtype=np.float32)

    # Reshape for 1D CNN: (N, C, L) = (N, 1, 187)
    X_train_tensor = torch.tensor(X_train_norm).unsqueeze(1)
    y_train_tensor = torch.tensor(y_train_sub, dtype=torch.long)
    X_test_tensor = torch.tensor(X_test_norm).unsqueeze(1)
    y_test_tensor = torch.tensor(y_test_sub, dtype=torch.long)

    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    test_dataset = TensorDataset(X_test_tensor, y_test_tensor)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 4. Initialize Model, Loss with Class Weights, Optimizer
    model = ECG1DCNN(in_channels=1, num_classes=5, latent_dim=32).to(device)
    
    class_weights = compute_class_weight('balanced', classes=np.arange(5), y=y_train_sub)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float32).to(device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

    # 5. Training Loop
    epochs = 4
    print(f"\nTraining ECG 1D CNN for {epochs} epochs...")
    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            logits, _ = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * batch_x.size(0)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)
            
        epoch_loss = running_loss / total
        epoch_acc = correct / total
        print(f"  Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc*100:.2f}%")

    # 6. Evaluation on Test Set
    print("\nEvaluating on unseen ECG test set...")
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            logits, _ = model(batch_x)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(batch_y.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    acc = accuracy_score(all_targets, all_preds)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(all_targets, all_preds, average='macro')
    prec_wt, rec_wt, f1_wt, _ = precision_recall_fscore_support(all_targets, all_preds, average='weighted')
    cm = confusion_matrix(all_targets, all_preds)
    prec_per_class, rec_per_class, f1_per_class, support_per_class = precision_recall_fscore_support(
        all_targets, all_preds, average=None
    )

    class_names = model.class_names
    print(f"\n--- TEST SET EVALUATION METRICS ---")
    print(f"Accuracy:        {acc*100:.2f}%")
    print(f"Macro Precision: {prec_macro*100:.2f}%")
    print(f"Macro Recall:    {rec_macro*100:.2f}%")
    print(f"Macro F1-Score:  {f1_macro*100:.2f}%")

    # 7. Save Model Artifact and Reports
    output_model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "trained_models"))
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports", "ecg"))
    os.makedirs(output_model_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    model_save_path = os.path.join(output_model_dir, "ecg_1dcnn.pt")
    torch.save(model.state_dict(), model_save_path)
    print(f"\nSaved ECG 1D CNN checkpoint to {model_save_path}")

    metrics = {
        "model_name": "ECG 1D Convolutional Neural Network",
        "dataset": "MIT-BIH Arrhythmia Database (PhysioNet)",
        "test_samples": int(len(all_targets)),
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(prec_macro), 4),
        "macro_recall": round(float(rec_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_f1": round(float(f1_wt), 4),
        "classes": [
            {
                "class_id": i,
                "label": class_names[i],
                "precision": round(float(prec_per_class[i]), 4),
                "recall": round(float(rec_per_class[i]), 4),
                "f1": round(float(f1_per_class[i]), 4),
                "support": int(support_per_class[i])
            }
            for i in range(5)
        ],
        "confusion_matrix": cm.tolist()
    }

    metrics_json_path = os.path.join(reports_dir, "metrics.json")
    with open(metrics_json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {metrics_json_path}")

    # Confusion matrix plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=["N", "S", "V", "F", "Q"],
        yticklabels=["N", "S", "V", "F", "Q"]
    )
    plt.title("ECG 1D CNN Arrhythmia Confusion Matrix (MIT-BIH)")
    plt.xlabel("Predicted Rhythm")
    plt.ylabel("True Expert Rhythm")
    plt.tight_layout()
    cm_plot_path = os.path.join(reports_dir, "confusion_matrix.png")
    plt.savefig(cm_plot_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to {cm_plot_path}")

    # Report text
    report_text_path = os.path.join(reports_dir, "report.txt")
    with open(report_text_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("ECG 1D CNN MODEL - EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Architecture: 4-Stage Conv1D + BatchNorm + Adaptive Pooling + Latent Projection (32-d)\n")
        f.write(f"Target: AAMI EC57 Arrhythmia Categories (5 classes)\n")
        f.write(f"Test Samples: {len(all_targets)}\n\n")
        f.write(f"Overall Accuracy: {acc*100:.2f}%\n")
        f.write(f"Macro F1-Score:   {f1_macro*100:.2f}%\n\n")
        f.write(classification_report(all_targets, all_preds, target_names=class_names))
    print(f"Saved text report to {report_text_path}")
    print("\nECG model training phase completed successfully.")
    return metrics


if __name__ == "__main__":
    train_ecg_model()
