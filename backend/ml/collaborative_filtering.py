"""
Collaborative Filtering Module (backend/ml/collaborative_filtering.py)
Re-exports CollaborativeFilteringRecommender and get_collaborative_recommender.
"""

from app.ml_models.collaborative_filtering import (
    CollaborativeFilteringRecommender,
    get_collaborative_recommender,
)

__all__ = ["CollaborativeFilteringRecommender", "get_collaborative_recommender"]
