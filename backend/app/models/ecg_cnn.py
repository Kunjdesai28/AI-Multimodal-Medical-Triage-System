"""
1D Convolutional Neural Network for ECG Arrhythmia & Abnormality Detection.

Analyzes 187-sample cardiac lead signals, classifies into AAMI heart rhythm categories,
and extracts a 32-dimensional latent representation for Multimodal Fusion.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict


class ECG1DCNN(nn.Module):
    """
    4-Stage 1D Convolutional Neural Network with Residual / Batch-Norm layers.
    Optimized for rapid CPU inference and high-fidelity cardiac representation.
    """
    def __init__(self, in_channels: int = 1, num_classes: int = 5, latent_dim: int = 32):
        super(ECG1DCNN, self).__init__()
        
        # Block 1
        self.conv1 = nn.Conv1d(in_channels, 32, kernel_size=7, stride=1, padding=3)
        self.bn1 = nn.BatchNorm1d(32)
        self.pool1 = nn.MaxPool1d(kernel_size=2)
        
        # Block 2
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, stride=1, padding=2)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool2 = nn.MaxPool1d(kernel_size=2)
        
        # Block 3
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool3 = nn.MaxPool1d(kernel_size=2)
        
        # Block 4 with Adaptive Pooling
        self.conv4 = nn.Conv1d(128, 128, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm1d(128)
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Latent Representation Projection (for Multimodal Fusion)
        self.fc_latent = nn.Sequential(
            nn.Linear(128, latent_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Classification Head
        self.classifier = nn.Linear(latent_dim, num_classes)
        
        # Class names according to AAMI EC57 standard
        self.class_names = [
            "Normal Rhythm (N)",
            "Supraventricular Ectopic (S)",
            "Ventricular Ectopic / PVC (V)",
            "Fusion Beat (F)",
            "Unknown / Paced / Unclassifiable (Q)"
        ]

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts the 32-dim latent cardiac embedding."""
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.global_pool(F.relu(self.bn4(self.conv4(x))))
        x = x.squeeze(-1)
        latent = self.fc_latent(x)
        return latent

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns (logits, latent_representation)."""
        latent = self.forward_features(x)
        logits = self.classifier(latent)
        return logits, latent
