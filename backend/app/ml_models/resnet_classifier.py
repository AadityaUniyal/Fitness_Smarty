"""
ResNet Fine-Tuned Food Classifier (ResNet18 / ResNet50)
[Status: Planned / In Progress - visual/advanced ML features reserved for future vision integration]

Food classification using ResNet fine-tuned on food datasets.
When trained weights are available (weights/resnet18_food101.pth), provides real predictions.
Otherwise falls back to mock/heuristic mode.
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
    ResNet-based food classifier (ResNet18 / ResNet50).
    [Status: Planned / In Progress - visual/advanced ML features reserved for future vision integration]
    """

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
        Initialize ResNet food classifier.
        [Status: Planned / In Progress]
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
                print(f"[!] Error loading ResNet weights: {e}. Falling back to mock mode.")
                self.mock_mode = True
        else:
            self.mock_mode = True

    def _load_model(self):
        """Load fine-tuned ResNet model weights."""
        if not os.path.exists(self.model_path):
            print(f"[!] ResNet weights not found at {self.model_path}. Running in mock mode.")
            self.mock_mode = True
            return

        print(f"[AI] Loading fine-tuned ResNet from {self.model_path}...")

        weights = ResNet18_Weights.DEFAULT
        self.model = models.resnet18(weights=None)
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, len(self.FOOD_CLASSES))

        state_dict = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        self.transform = weights.transforms()
        self.mock_mode = False
        print(f"[OK] ResNet loaded successfully on {self.device}")

    def classify_image(
        self,
        image_input: Any,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Classify food image into top_k classes with confidence scores.
        """
        if self.mock_mode or self.model is None:
            return self._mock_classify(top_k)

        try:
            image = self._load_image(image_input)
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

            top_prob, top_indices = torch.topk(probabilities, top_k)

            predictions = []
            for i in range(top_k):
                idx = top_indices[i].item()
                prob = top_prob[i].item()
                class_name = self.FOOD_CLASSES[idx]
                predictions.append({
                    'class_name': class_name,
                    'food_label': class_name.replace('_', ' ').title(),
                    'confidence': round(float(prob), 4),
                })

            top_match = predictions[0]
            return {
                'top_prediction': top_match['food_label'],
                'top_class': top_match['class_name'],
                'confidence': top_match['confidence'],
                'all_predictions': predictions,
                'model': 'resnet18_fine_tuned',
                'status': 'active',
                'mock_mode': False,
            }

        except Exception as e:
            print(f"[!] ResNet classification failure: {e}")
            return self._mock_classify(top_k)

    def _load_image(self, image_input: Any) -> Image.Image:
        """Helper to load PIL Image from path, bytes, or PIL Image object."""
        if isinstance(image_input, Image.Image):
            return image_input.convert('RGB')
        elif isinstance(image_input, str):
            return Image.open(image_input).convert('RGB')
        elif isinstance(image_input, bytes):
            import io
            return Image.open(io.BytesIO(image_input)).convert('RGB')
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

    def _mock_classify(self, top_k: int = 5) -> Dict[str, Any]:
        """Mock classification response when weights are not available."""
        selected_classes = np.random.choice(self.FOOD_CLASSES, size=top_k, replace=False)
        probs = np.random.dirichlet(np.ones(top_k))
        probs = sorted(probs, reverse=True)

        predictions = [
            {
                'class_name': selected_classes[i],
                'food_label': selected_classes[i].replace('_', ' ').title(),
                'confidence': round(float(probs[i]), 4),
            }
            for i in range(top_k)
        ]

        return {
            'top_prediction': predictions[0]['food_label'],
            'top_class': predictions[0]['class_name'],
            'confidence': predictions[0]['confidence'],
            'all_predictions': predictions,
            'model': 'resnet_planned_fallback',
            'status': 'Planned / In Progress',
            'mock_mode': True,
            'notice': 'Visual feature status: Planned / In Progress (reserved for future vision integration).'
        }


# Singleton instance
_resnet_instance: Optional[ResNetFoodClassifier] = None

def get_resnet_classifier() -> ResNetFoodClassifier:
    """Get singleton ResNet food classifier instance."""
    global _resnet_instance
    if _resnet_instance is None:
        _resnet_instance = ResNetFoodClassifier()
    return _resnet_instance
