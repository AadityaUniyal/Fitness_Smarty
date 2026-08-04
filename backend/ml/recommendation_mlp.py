"""
Recommendation MLP Module (backend/ml/recommendation_mlp.py)
Re-exports RecommendationMLP and get_recommendation_mlp.
"""

from app.ml_models.recommendation_mlp import (
    RecommendationMLP,
    get_recommendation_mlp,
)

__all__ = ["RecommendationMLP", "get_recommendation_mlp"]
