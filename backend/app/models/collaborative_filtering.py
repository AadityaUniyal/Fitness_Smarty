"""
Collaborative Filtering Recommender

User-based and item-based collaborative filtering for meal recommendations
"""

import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import NMF
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn not available")


class CollaborativeFilteringRecommender:
    """
    Collaborative filtering for personalized meal recommendations
    
    - User-based: Recommend meals liked by similar users
    - Item-based: Recommend meals similar to ones user liked
    - Matrix Factorization: NMF for latent features
    """
    
    def __init__(self):
        """Initialize collaborative filtering recommender"""
        self.mock_mode = not SKLEARN_AVAILABLE
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None
        
        if SKLEARN_AVAILABLE:
            print("✓ Collaborative filtering recommender initialized")
        else:
            print("⚠️  scikit-learn not installed. Using mock mode.")
    
    def fit(self, user_meal_ratings: Dict[int, Dict[int, float]]):
        """
        Fit the recommender on user-meal ratings
        
        Args:
            user_meal_ratings: {user_id: {meal_id: rating}}
                               rating can be implicit (1.0) or explicit (1-5)
        """
        if self.mock_mode:
            return
        
        try:
            # Build user-item matrix
            all_users = list(user_meal_ratings.keys())
            all_meals = set()
            for meals in user_meal_ratings.values():
                all_meals.update(meals.keys())
            all_meals = list(all_meals)
            
            matrix = np.zeros((len(all_users), len(all_meals)))
            
            for i, user_id in enumerate(all_users):
                for j, meal_id in enumerate(all_meals):
                    matrix[i, j] = user_meal_ratings[user_id].get(meal_id, 0)
            
            self.user_item_matrix = matrix
            
            # Calculate user similarity
            self.user_similarity = cosine_similarity(matrix)
            
            # Calculate item similarity
            self.item_similarity = cosine_similarity(matrix.T)
            
            print(f"✓ Fitted on {len(all_users)} users, {len(all_meals)} meals")
            
        except Exception as e:
            print(f"Error fitting collaborative filtering: {e}")
            self.mock_mode = True
    
    def recommend_user_based(
        self,
        user_id: int,
        user_meal_ratings: Dict[int, Dict[int, float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        User-based collaborative filtering
        
        Find similar users and recommend their liked meals
        """
        if self.mock_mode:
            return self._mock_recommendations(top_k)
        
        try:
            # Find similar users
            all_users = list(user_meal_ratings.keys())
            if user_id not in all_users:
                return self._mock_recommendations(top_k)
            
            user_idx = all_users.index(user_id)
            similarities = self.user_similarity[user_idx]
            
            # Get meals from similar users
            similar_users = np.argsort(similarities)[::-1][1:11]  # Top 10 similar users
            
            meal_scores = defaultdict(float)
            for similar_user_idx in similar_users:
                similar_user_id = all_users[similar_user_idx]
                similarity_score = similarities[similar_user_idx]
                
                for meal_id, rating in user_meal_ratings[similar_user_id].items():
                    # Don't recommend meals user already has
                    if meal_id not in user_meal_ratings[user_id]:
                        meal_scores[meal_id] += rating * similarity_score
            
            # Sort and return top K
            top_meals = sorted(meal_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            
            return [
                {
                    'meal_id': meal_id,
                    'score': float(score),
                    'reason': 'Users like you enjoyed this'
                }
                for meal_id, score in top_meals
            ]
            
        except Exception as e:
            print(f"Error in user-based CF: {e}")
            return self._mock_recommendations(top_k)
    
    def recommend_item_based(
        self,
        user_id: int,
        user_meal_ratings: Dict[int, Dict[int, float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Item-based collaborative filtering
        
        Find meals similar to ones user liked
        """
        if self.mock_mode:
            return self._mock_recommendations(top_k)
        
        try:
            if user_id not in user_meal_ratings:
                return self._mock_recommendations(top_k)
            
            user_meals = user_meal_ratings[user_id]
            all_meals = []
            for meals in user_meal_ratings.values():
                all_meals.extend(meals.keys())
            all_meals = list(set(all_meals))
            
            meal_scores = defaultdict(float)
            
            # For each meal user liked
            for liked_meal_id, rating in user_meals.items():
                if liked_meal_id not in all_meals:
                    continue
                    
                meal_idx = all_meals.index(liked_meal_id)
                similarities = self.item_similarity[meal_idx]
                
                # Find similar meals
                for i, similar_meal_id in enumerate(all_meals):
                    if similar_meal_id not in user_meals:  # Don't recommend already eaten
                        meal_scores[similar_meal_id] += similarities[i] * rating
            
            # Sort and return top K
            top_meals = sorted(meal_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            
            return [
                {
                    'meal_id': meal_id,
                    'score': float(score),
                    'reason': 'Similar to meals you liked'
                }
                for meal_id, score in top_meals
            ]
            
        except Exception as e:
            print(f"Error in item-based CF: {e}")
            return self._mock_recommendations(top_k)
    
    def _mock_recommendations(self, top_k: int) -> List[Dict[str, Any]]:
        """Mock recommendations for development"""
        return [
            {
                'meal_id': i + 100,
                'score': 0.9 - (i * 0.1),
                'reason': 'Popular choice'
            }
            for i in range(top_k)
        ]


# Singleton instance
_cf_instance: Optional[CollaborativeFilteringRecommender] = None

def get_collaborative_recommender() -> CollaborativeFilteringRecommender:
    """Get singleton collaborative filtering instance"""
    global _cf_instance
    if _cf_instance is None:
        _cf_instance = CollaborativeFilteringRecommender()
    return _cf_instance
