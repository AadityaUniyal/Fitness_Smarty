"""
PyTorch Recommendation MLP Integration Module
Provides inference interface for deep learning meal recommendation model.
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.training.train_neural_model import MealRecommendationNN, NeuralModelTrainer


class RecommendationMLP:
    """
    Inference service for PyTorch Recommendation MLP.
    Scores and ranks candidate items against user profiles.
    """
    
    def __init__(self):
        self.trainer = NeuralModelTrainer()
        self.mock_mode = not TORCH_AVAILABLE
        self.is_loaded = False
        
        if TORCH_AVAILABLE:
            try:
                self.trainer.load_model()
                self.is_loaded = True
                print("[OK] RecommendationMLP model loaded successfully")
            except Exception as e:
                print(f"[!] RecommendationMLP load notice: {e}. Will train or fallback.")
                self.is_loaded = False
                
    def predict_score(self, user_profile: Dict[str, Any], meal: Dict[str, Any]) -> float:
        """
        Predict suitability score for a user-meal pair in range [0.0, 1.0].
        Target indices align cleanly with item catalog parameters.
        """
        if not self.is_loaded:
            return self._rule_fallback_score(user_profile, meal)
            
        try:
            # Ensure meal dictionary structure is standardized
            std_meal = self._standardize_meal(meal)
            pred = self.trainer.predict(user_profile, std_meal)
            return float(pred.get('score', 0.5))
        except Exception as e:
            print(f"[!] MLP predict_score error: {e}")
            return self._rule_fallback_score(user_profile, meal)
            
    def _standardize_meal(self, meal: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FoodItem or candidate dict to expected meal structure."""
        if 'nutrition' in meal and isinstance(meal['nutrition'], dict):
            return meal
            
        calories = float(meal.get('calories') or meal.get('calories_per_min', 400))
        protein = float(meal.get('protein') or meal.get('protein_g', 30))
        carbs = float(meal.get('carbs') or meal.get('carbs_g', 40))
        fats = float(meal.get('fats') or meal.get('fat_g', 15))
        fiber = float(meal.get('fiber') or meal.get('fiber_g', 5))
        name = str(meal.get('name') or meal.get('label') or 'food')
        
        return {
            'nutrition': {
                'calories': calories,
                'protein_g': protein,
                'carbs_g': carbs,
                'fat_g': fats,
                'fiber_g': fiber
            },
            'foods': [{'name': name}]
        }
        
    def _rule_fallback_score(self, user_profile: Dict[str, Any], meal: Dict[str, Any]) -> float:
        """Fallback scoring when PyTorch is unavailable or model is uninitialized."""
        goal = str(user_profile.get('goal') or user_profile.get('primary_goal') or 'maintenance').lower()
        std_meal = self._standardize_meal(meal)
        nut = std_meal['nutrition']
        
        calories = nut['calories']
        protein = nut['protein_g']
        
        if goal == 'weight_loss':
            cal_score = max(0.0, 1.0 - (calories / 800.0))
            prot_score = min(1.0, protein / 30.0)
            return round(0.5 * cal_score + 0.5 * prot_score, 4)
        elif goal == 'muscle_gain':
            prot_score = min(1.0, protein / 40.0)
            cal_score = min(1.0, calories / 500.0)
            return round(0.6 * prot_score + 0.4 * cal_score, 4)
        else:
            return round(min(1.0, (protein * 4 + calories / 10) / 100.0), 4)

    def rank_candidates(self, user_profile: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and rank candidates using MLP model."""
        scored = []
        for cand in candidates:
            score = self.predict_score(user_profile, cand)
            scored.append({
                **cand,
                'mlp_score': score
            })
        scored.sort(key=lambda x: x['mlp_score'], reverse=True)
        return scored


# Singleton instance
_mlp_instance: Optional[RecommendationMLP] = None

def get_recommendation_mlp() -> RecommendationMLP:
    global _mlp_instance
    if _mlp_instance is None:
        _mlp_instance = RecommendationMLP()
    return _mlp_instance
