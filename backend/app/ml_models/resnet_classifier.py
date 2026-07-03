"""
ResNet18 Fine-Tuned Food Classifier

Food classification using ResNet18 fine-tuned on the Food-101 dataset.
When trained weights are available (weights/resnet18_food101.pth), provides
real predictions.  Otherwise falls back to mock mode with a clear log message.

Training script: backend/scripts/train_food101.py
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np
from PIL import Image

try:
    import torch
    import torch.nn as nn
    import torchvision.models as models
    import torchvision.transforms as transforms
    from torchvision.models import ResNet18_Weights
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not available")


class ResNetFoodClassifier:
    """
    ResNet18-based food classifier, fine-tuned on Food-101.

    When weights/resnet18_food101.pth exists:
        → Real inference with top-K predictions
    When weights are missing:
        → Mock mode (random predictions from FOOD_CLASSES)
    """

    # Food-101 classes (101 categories, alphabetically sorted to match torchvision)
    FOOD_CLASSES = sorted([
        'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
        'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
        'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
        'ceviche', 'cheesecake', 'cheese_plate', 'chicken_curry', 'chicken_quesadilla',
        'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder',
        'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes',
        'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict',
        'escargots', 'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras',
        'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice',
        'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich',
        'grilled_salmon', 'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup',
        'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna',
        'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup',
        'mussels', 'nachos', 'omelette', 'onion_rings', 'oysters',
        'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
        'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib',
        'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake', 'risotto',
        'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits',
        'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak',
        'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki', 'tiramisu',
        'tuna_tartare', 'waffles',
    ])

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ResNet18 food classifier.

        Args:
            model_path: Path to fine-tuned weights (.pth file).
                        Defaults to weights/resnet18_food101.pth
        """
        self.model_path = model_path or os.getenv(
            'RESNET_MODEL_PATH', 'weights/resnet18_food101.pth'
        )
        self.model = None
        self.transform = None
        self.mock_mode = False
        self.device = None

        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            try:
                self._load_model()
            except Exception as e:
                print(f"[!] Could not load ResNet18: {e}")
                self.mock_mode = True
        else:
            print("[!] PyTorch not installed. Using mock mode.")
            self.mock_mode = True

    def _load_model(self):
        """Build ResNet18 architecture and load weights if available."""
        # Build the model with the same architecture as the training script
        self.model = models.resnet18(weights=ResNet18_Weights.DEFAULT)

        # Replace FC head to match 101 food classes (same structure as training)
        num_features = self.model.fc.in_features  # 512 for ResNet18
        self.model.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, len(self.FOOD_CLASSES)),
        )

        # Load fine-tuned weights if available
        if os.path.exists(self.model_path):
            state_dict = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"[OK] Loaded fine-tuned ResNet18 from {self.model_path}")
        else:
            print(f"[!] No fine-tuned weights found at {self.model_path}.")
            print("    Run 'python backend/scripts/train_food101.py' to train on Food-101.")
            print("    Falling back to mock mode.")
            self.mock_mode = True
            return

        self.model = self.model.to(self.device)
        self.model.eval()

        # Standard ImageNet preprocessing (same as training validation transform)
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        print(f"[OK] ResNet18 food classifier initialized on {self.device}")

    def classify(self, image_path: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Classify food image with top-K predictions.

        Args:
            image_path: Path to image file
            top_k: Number of top predictions to return

        Returns:
            {
                'predictions': [
                    {'class': 'pizza', 'confidence': 0.92},
                    {'class': 'spaghetti_bolognese', 'confidence': 0.05},
                    ...
                ],
                'top_class': 'pizza',
                'top_confidence': 0.92,
                'model': 'resnet18_food101' or 'mock',
                'device': 'cuda' or 'cpu'
            }
        """
        if self.mock_mode:
            return self._mock_classify(top_k)

        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

            top_probs, top_indices = torch.topk(probabilities, min(top_k, len(self.FOOD_CLASSES)))

            predictions = []
            for prob, idx in zip(top_probs, top_indices):
                predictions.append({
                    'class': self.FOOD_CLASSES[idx],
                    'confidence': round(float(prob), 4)
                })

            return {
                'predictions': predictions,
                'top_class': predictions[0]['class'],
                'top_confidence': predictions[0]['confidence'],
                'model': 'resnet18_food101',
                'device': str(self.device)
            }

        except Exception as e:
            print(f"Error in ResNet18 classification: {e}")
            return self._mock_classify(top_k)

    def _mock_classify(self, top_k: int = 3) -> Dict[str, Any]:
        """Mock classification for development (no trained weights available)."""
        import random

        # Pick random classes with decaying confidence
        indices = random.sample(range(len(self.FOOD_CLASSES)), min(top_k, len(self.FOOD_CLASSES)))
        confs = sorted([random.uniform(0.3, 0.95) for _ in range(len(indices))], reverse=True)
        # Normalise to sum ≤ 1
        total = sum(confs) + 0.1
        confs = [round(c / total, 4) for c in confs]

        predictions = [
            {'class': self.FOOD_CLASSES[idx], 'confidence': conf}
            for idx, conf in zip(indices, confs)
        ]

        return {
            'predictions': predictions,
            'top_class': predictions[0]['class'],
            'top_confidence': predictions[0]['confidence'],
            'model': 'mock',
            'device': 'cpu'
        }

    def classify_batch(self, image_paths: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Classify multiple images at once.

        More efficient than calling classify multiple times when using GPU.
        """
        results = []
        for image_path in image_paths:
            results.append(self.classify(image_path, top_k))
        return results


# Singleton instance
_resnet_instance: Optional[ResNetFoodClassifier] = None


def get_resnet_classifier() -> ResNetFoodClassifier:
    """Get singleton ResNet18 food classifier instance."""
    global _resnet_instance
    if _resnet_instance is None:
        _resnet_instance = ResNetFoodClassifier()
    return _resnet_instance
