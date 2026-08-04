"""
User Clustering Module (backend/ml/user_clustering.py)
Re-exports UserClusterEngine, UserProfile, and ClusterInfo from app.training.user_clustering.
"""

from app.training.user_clustering import (
    UserClusterEngine,
    UserProfile,
    ClusterInfo,
    generate_sample_profiles,
)

__all__ = ["UserClusterEngine", "UserProfile", "ClusterInfo", "generate_sample_profiles"]
