"""
Mask R-CNN Portion Estimator

Pixel-level segmentation for accurate portion size estimation
"""

import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image

try:
    import torch
    import torchvision
    from torchvision.models.detection import maskrcnn_resnet50_fpn
    from torchvision.transforms import functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch/torchvision not available")


class MaskRCNNPortionEstimator:
    """
    Mask R-CNN for food segmentation and portion estimation
    
    Uses pixel-level masks to calculate volume/weight more accurately
    """
    
    # Reference object sizes (for calibration)
    # In a real system, users would place a coin/card for scale
    REFERENCE_SIZES = {
        'plate_diameter_cm': 25,  # Standard dinner plate
        'bowl_diameter_cm': 15,   # Standard bowl
        'cup_height_cm': 10       # Standard cup
    }
    
    # Food density estimates (g/cm³)
    FOOD_DENSITIES = {
        'chicken': 1.05,
        'beef': 1.05,
        'fish': 1.05,
        'rice': 0.75,
        'pasta': 0.60,
        'vegetables': 0.50,
        'salad': 0.45,
        'soup': 1.00,
        'bread': 0.25,
        'default': 0.70
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Mask R-CNN
        
        Args:
            model_path: Path to trained weights (optional)
        """
        self.model_path = model_path or os.getenv('MASKRCNN_MODEL_PATH', 'weights/maskrcnn_portion.pth')
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.mock_mode = False
        
        if TORCH_AVAILABLE:
            try:
                # Load pretrained Mask R-CNN
                self.model = maskrcnn_resnet50_fpn(pretrained=True)
                
                # Load fine-tuned weights if available
                if os.path.exists(self.model_path):
                    self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                    print(f"✓ Loaded fine-tuned Mask R-CNN from {self.model_path}")
                else:
                    print("⚠️  Using pretrained Mask R-CNN. Fine-tune on Nutrition5k for better portions.")
                
                self.model = self.model.to(self.device)
                self.model.eval()
                
                print(f"✓ Mask R-CNN initialized on {self.device}")
                
            except Exception as e:
                print(f"⚠️  Could not load Mask R-CNN: {e}")
                self.mock_mode = True
        else:
            print("⚠️  PyTorch not installed. Using mock mode.")
            self.mock_mode = True
    
    def estimate_portions(
        self,
        image_path: str,
        food_labels: Optional[List[str]] = None,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Estimate portion sizes using pixel-level segmentation
        
        Args:
            image_path: Path to image
            food_labels: Optional list of food names to match
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            {
                'portions': [
                    {
                        'food': 'chicken',
                        'mask_area_pixels': 15000,
                        'estimated_volume_cm3': 180,
                        'estimated_weight_g': 189,
                        'confidence': 0.92
                    }
                ],
                'total_items': 3,
                'calibration_used': 'plate_diameter'
            }
        """
        if self.mock_mode:
            return self._mock_estimate(food_labels)
        
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            image_tensor = F.to_tensor(image).to(self.device)
            
            # Run Mask R-CNN
            with torch.no_grad():
                predictions = self.model([image_tensor])[0]
            
            # Filter by confidence
            scores = predictions['scores'].cpu().numpy()
            masks = predictions['masks'].cpu().numpy()
            labels = predictions['labels'].cpu().numpy()
            
            valid_indices = scores >= confidence_threshold
            
            portions = []
            for i, (score, mask, label) in enumerate(zip(scores[valid_indices], 
                                                          masks[valid_indices],
                                                          labels[valid_indices])):
                # Calculate mask area (number of pixels)
                mask_binary = mask[0] > 0.5  # Threshold mask
                mask_area = np.sum(mask_binary)
                
                # Estimate 3D volume from 2D area
                # Assuming circular cross-section and height proportional to diameter
                estimated_volume_cm3 = self._area_to_volume(mask_area, image.size)
                
                # Get food category for density
                food_name = food_labels[i] if food_labels and i < len(food_labels) else f'food_{label}'
                density = self._get_density(food_name)
                
                # Calculate weight
                estimated_weight_g = int(estimated_volume_cm3 * density)
                
                portions.append({
                    'food': food_name,
                    'mask_area_pixels': int(mask_area),
                    'estimated_volume_cm3': round(estimated_volume_cm3, 1),
                    'estimated_weight_g': estimated_weight_g,
                    'confidence': round(float(score), 3),
                    'bbox': predictions['boxes'][i].cpu().numpy().tolist()
                })
            
            return {
                'portions': portions,
                'total_items': len(portions),
                'calibration_used': 'plate_diameter',
                'image_size': list(image.size),
                'model': 'maskrcnn'
            }
            
        except Exception as e:
            print(f"Error in Mask R-CNN estimation: {e}")
            return self._mock_estimate(food_labels)
    
    def _area_to_volume(self, pixel_area: int, image_size: Tuple[int, int]) -> float:
        """
        Convert 2D pixel area to 3D volume estimate
        
        Uses plate diameter as reference (25cm standard)
        """
        # Estimate camera-to-plate distance and angle
        # For now, use simple heuristic
        
        # Assume plate takes ~40% of image width
        img_width, img_height = image_size
        plate_pixels = img_width * 0.4
        
        # pixels_per_cm ratio
        pixels_per_cm = plate_pixels / self.REFERENCE_SIZES['plate_diameter_cm']
        
        # Convert pixel area to cm²
        area_cm2 = pixel_area / (pixels_per_cm ** 2)
        
        # Estimate volume assuming cylinder with height = 0.4 * diameter
        radius_cm = np.sqrt(area_cm2 / np.pi)
        height_cm = radius_cm * 0.4
        volume_cm3 = np.pi * (radius_cm ** 2) * height_cm
        
        return volume_cm3
    
    def _get_density(self, food_name: str) -> float:
        """Get food density for weight calculation"""
        food_lower = food_name.lower()
        
        for key, density in self.FOOD_DENSITIES.items():
            if key in food_lower:
                return density
        
        return self.FOOD_DENSITIES['default']
    
    def _mock_estimate(self, food_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Mock portion estimation"""
        mock_portions = [
            {
                'food': 'chicken' if not food_labels else food_labels[0],
                'mask_area_pixels': 15000,
                'estimated_volume_cm3': 170.5,
                'estimated_weight_g': 179,
                'confidence': 0.88
            },
            {
                'food': 'rice' if not food_labels else (food_labels[1] if len(food_labels) > 1 else 'rice'),
                'mask_area_pixels': 12000,
                'estimated_volume_cm3': 160.0,
                'estimated_weight_g': 120,
                'confidence': 0.85
            }
        ]
        
        return {
            'portions': mock_portions[:len(food_labels) if food_labels else 2],
            'total_items': len(food_labels) if food_labels else 2,
            'calibration_used': 'plate_diameter',
            'image_size': [640, 480],
            'model': 'mock'
        }


# Singleton instance
_maskrcnn_instance: Optional[MaskRCNNPortionEstimator] = None

def get_portion_estimator() -> MaskRCNNPortionEstimator:
    """Get singleton Mask R-CNN instance"""
    global _maskrcnn_instance
    if _maskrcnn_instance is None:
        _maskrcnn_instance = MaskRCNNPortionEstimator()
    return _maskrcnn_instance
