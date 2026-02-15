"""
SHAP Explainer for Model Interpretability

Provides SHAP values and explanations for ML model predictions
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not available. Install with: pip install shap")


class SHAPExplainer:
    """
    SHAP-based model explainer
    
    Explains why models made specific predictions
    """
    
    def __init__(self):
        """Initialize SHAP explainer"""
        self.mock_mode = not SHAP_AVAILABLE
        
        if SHAP_AVAILABLE:
            print("✓ SHAP Explainer initialized")
        else:
            print("⚠️  SHAP not installed. Using mock mode.")
    
    def explain_recommendation(
        self,
        recommendation: Dict[str, Any],
        user_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Explain why a meal was recommended
        
        Args:
            recommendation: The recommended meal
            user_features: User's profile features
            
        Returns:
            SHAP values and feature importance
        """
        if self.mock_mode:
            return self._mock_explanation(recommendation)
        
        try:
            # Mock feature importance (in production, use real SHAP)
            features = {
                'protein_match': 0.35,
                'calorie_match': 0.25,
                'user_history': 0.20,
                'similar_users': 0.15,
                'ingredient_preference': 0.05
            }
            
            return {
                'recommendation': recommendation.get('name', 'Unknown'),
                'shap_values': features,
                'feature_importance': sorted(
                    features.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                ),
                'explanation': self._generate_explanation(features),
                'confidence': 0.87,
                'model': 'shap_mock'
            }
            
        except Exception as e:
            print(f"Error in SHAP explanation: {e}")
            return self._mock_explanation(recommendation)
    
    def feature_importance(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Get feature importance for a model
        
        Args:
            model_name: Which model to explain
            
        Returns:
            Feature importance rankings
        """
        # Mock feature importance per model
        importances = {
            'collaborative_filtering': {
                'user_similarity': 0.45,
                'meal_popularity': 0.30,
                'recent_preferences': 0.15,
                'time_of_day': 0.10
            },
            'content_based': {
                'nutrition_match': 0.40,
                'ingredient_similarity': 0.35,
                'calorie_target': 0.15,
                'dietary_restrictions': 0.10
            },
            'lstm_weight': {
                'historical_trend': 0.50,
                'recent_calories': 0.25,
                'activity_level': 0.15,
                'day_of_week': 0.10
            }
        }
        
        features = importances.get(model_name, importances['collaborative_filtering'])
        
        return {
            'model': model_name,
            'features': features,
            'top_features': sorted(
                features.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'method': 'shap_mock'
        }
    
    def decision_path(
        self,
        prediction: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Show decision path that led to prediction
        
        Returns step-by-step reasoning
        """
        # Mock decision tree
        path = [
            {
                'step': 1,
                'condition': 'User needs high protein (target: 150g)',
                'action': 'Filter for protein > 30g per meal',
                'result': '15 meals remaining'
            },
            {
                'step': 2,
                'condition': 'User prefers chicken (75% of history)',
                'action': 'Prioritize chicken-based meals',
                'result': '8 meals remaining'
            },
            {
                'step': 3,
                'condition': 'Calorie limit: 500-600 cal',
                'action': 'Filter by calorie range',
                'result': '3 meals remaining'
            },
            {
                'step': 4,
                'condition': 'Similar users loved this meal',
                'action': 'Select top collaborative match',
                'result': 'Final recommendation: Grilled Chicken Bowl'
            }
        ]
        
        return {
            'decision_path': path,
            'final_prediction': prediction,
            'confidence': 0.89
        }
    
    def _generate_explanation(self, features: Dict[str, float]) -> str:
        """Generate human-readable explanation"""
        top_feature = max(features.items(), key=lambda x: x[1])
        
        explanations = {
            'protein_match': f"This meal perfectly matches your protein target ({top_feature[1]:.0%} match)",
            'calorie_match': f"Calories align with your daily goal ({top_feature[1]:.0%} match)",
            'user_history': f"Similar to meals YOU enjoyed ({top_feature[1]:.0%} similarity)",
            'similar_users': f"Users like you rated this highly ({top_feature[1]:.0%} confidence)",
            'ingredient_preference': f"Contains ingredients you prefer ({top_feature[1]:.0%} match)"
        }
        
        return explanations.get(top_feature[0], "Recommended based on your profile")
    
    def _mock_explanation(self, recommendation: Dict) -> Dict[str, Any]:
        """Mock explanation for development"""
        return {
            'recommendation': recommendation.get('name', 'Mock Meal'),
            'shap_values': {
                'protein_match': 0.40,
                'calorie_match': 0.30,
                'user_history': 0.20,
                'time_of_day': 0.10
            },
            'explanation': 'Recommended due to high protein content matching your goals',
            'confidence': 0.82,
            'model': 'shap_mock'
        }


# Singleton instance
_shap_instance: Optional[SHAPExplainer] = None

def get_shap_explainer() -> SHAPExplainer:
    """Get singleton SHAP explainer"""
    global _shap_instance
    if _shap_instance is None:
        _shap_instance = SHAPExplainer()
    return _shap_instance
