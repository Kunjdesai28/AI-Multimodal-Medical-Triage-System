"""
DenseNet121 Architecture for Chest X-ray Abnormality Detection and Grad-CAM Explainability.

Uses transfer learning (ImageNet pretrained backbone), extracts a 64-dimensional
latent visual representation for Multimodal Fusion, and classifies acute thoracic pathologies.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from typing import Tuple, List, Dict


class XRayDenseNet(nn.Module):
    """
    DenseNet-121 adapted for emergency radiological finding detection
    and visual attention gradient extraction.
    """
    TARGET_CONDITIONS = [
        "Normal / No Finding",
        "Cardiomegaly",
        "Pleural Effusion",
        "Pneumothorax",
        "Pulmonary Edema",
        "Infiltration",
        "Pneumonia",
        "Atelectasis"
    ]

    def __init__(self, num_classes: int = 8, latent_dim: int = 64, pretrained: bool = False):
        super(XRayDenseNet, self).__init__()
        
        # Load torchvision densenet121
        weights = models.DenseNet121_Weights.DEFAULT if pretrained else None
        densenet = models.densenet121(weights=weights)
        
        self.features = densenet.features
        num_features = densenet.classifier.in_features  # 1024
        
        # Latent projection for Multimodal Fusion
        self.fc_latent = nn.Sequential(
            nn.Linear(num_features, latent_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Multi-label / Multi-condition classification head
        self.classifier = nn.Linear(latent_dim, num_classes)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the penultimate feature map from denseblock4."""
        features = self.features(x)
        out = F.relu(features, inplace=False)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = torch.flatten(out, 1)
        return out

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass returning (logits, latent_representation).
        Logits can be passed through sigmoid for multi-label abnormality probabilities.
        """
        pooled = self.extract_features(x)
        latent = self.fc_latent(pooled)
        logits = self.classifier(latent)
        return logits, latent
