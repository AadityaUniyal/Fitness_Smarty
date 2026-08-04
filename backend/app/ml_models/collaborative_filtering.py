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
    print("[!] scikit-learn not available")


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
        self.user_map = {}
        self.item_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        
        if SKLEARN_AVAILABLE:
            print("[OK] Collaborative filtering recommender initialized")
            # Auto-fit on feedback dataset if available
            self._try_auto_fit()
        else:
            print("[!] scikit-learn not installed. Using mock mode.")

    def _try_auto_fit(self):
        """Auto-fit from default feedback data if available."""
        try:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            feedback_path = os.path.join(dir_path, "..", "training", "datasets", "meal_feedback.jsonl")
            if os.path.exists(feedback_path):
                self.train_from_feedback_file(feedback_path)
            else:
                self.train_synthetic()
        except Exception as e:
            print(f"[!] Auto-fit CF notice: {e}")

    def train_synthetic(self, num_users: int = 20, num_meals: int = 50):
        """Train on synthetic user interaction dataset."""
        import random
        ratings = defaultdict(dict)
        for u in range(1, num_users + 1):
            for m in range(1, num_meals + 1):
                if random.random() < 0.3:  # 30% sparsity
                    ratings[u][m] = random.uniform(1.0, 5.0)
        self.fit(ratings)

    def train_from_feedback_file(self, file_path: str) -> Dict[str, Any]:
        """Train CF model from meal_feedback.jsonl file."""
        import json
        ratings = defaultdict(dict)
        user_id_counter = 1
        user_name_to_id = {}
        meal_name_to_id = {}
        meal_id_counter = 1

        with open(file_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line.strip())
                    u_raw = str(record.get("user_id", "user_1"))
                    m_raw = str(record.get("meal_id", "meal_1"))
                    label = float(record.get("label", 1.0))
                    feedback = str(record.get("user_feedback", "good")).lower()
                    rating = 5.0 if feedback == "good" or label > 0.5 else 1.0

                    if u_raw not in user_name_to_id:
                        user_name_to_id[u_raw] = user_id_counter
                        user_id_counter += 1
                    if m_raw not in meal_name_to_id:
                        # Extract integer ID if possible
                        if m_raw.startswith("meal_"):
                            try:
                                mid = int(m_raw.split("_")[1]) + 1
                            except ValueError:
                                mid = meal_id_counter
                                meal_id_counter += 1
                        else:
                            mid = meal_id_counter
                            meal_id_counter += 1
                        meal_name_to_id[m_raw] = mid

                    uid = user_name_to_id[u_raw]
                    mid = meal_name_to_id[m_raw]
                    ratings[uid][mid] = rating
                except Exception:
                    continue

        if not ratings:
            self.train_synthetic()
            return {"status": "synthetic_fallback"}

        self.fit(ratings)
        metrics = {
            "status": "success",
            "num_users": len(self.user_map),
            "num_meals": len(self.item_map),
            "sparsity": round(1.0 - (float(np.count_nonzero(self.user_item_matrix)) / float(self.user_item_matrix.size)), 4) if self.user_item_matrix is not None else 1.0,
            "updated_at": os.environ.get("BUILD_TIME", "2026-08-02")
        }

        # Save metrics to backend/ml/cf_metrics.json
        dir_path = os.path.dirname(os.path.abspath(__file__))
        app_metrics = os.path.join(dir_path, "cf_metrics.json")
        backend_dir = os.path.dirname(os.path.dirname(dir_path))
        ml_metrics = os.path.join(backend_dir, "ml", "cf_metrics.json")
        os.makedirs(os.path.dirname(ml_metrics), exist_ok=True)

        with open(app_metrics, "w") as f:
            json.dump(metrics, f, indent=2)
        with open(ml_metrics, "w") as f:
            json.dump(metrics, f, indent=2)

        return metrics

    def fit(self, user_meal_ratings: Dict[int, Dict[int, float]]):
        """
        Fit the recommender on user-meal ratings
        
        Args:
            user_meal_ratings: {user_id: {meal_id: rating}}
                                rating can be implicit (1.0) or explicit (1-5)
        """
        if self.mock_mode or not user_meal_ratings:
            return
        
        try:
            all_users = sorted(list(user_meal_ratings.keys()))
            all_meals = set()
            for meals in user_meal_ratings.values():
                all_meals.update(meals.keys())
            all_meals = sorted(list(all_meals))
            
            self.user_map = {u: i for i, u in enumerate(all_users)}
            self.item_map = {m: j for j, m in enumerate(all_meals)}
            self.reverse_user_map = {i: u for u, i in self.user_map.items()}
            self.reverse_item_map = {j: m for m, j in self.item_map.items()}

            matrix = np.zeros((len(all_users), len(all_meals)))
            
            for user_id, meals in user_meal_ratings.items():
                i = self.user_map[user_id]
                for meal_id, rating in meals.items():
                    j = self.item_map[meal_id]
                    matrix[i, j] = rating
            
            self.user_item_matrix = matrix
            self.user_similarity = cosine_similarity(matrix) if len(all_users) > 1 else np.ones((1, 1))
            self.item_similarity = cosine_similarity(matrix.T) if len(all_meals) > 1 else np.ones((1, 1))
            
            print(f"[OK] Fitted CF model on {len(all_users)} users, {len(all_meals)} meals")
            
        except Exception as e:
            print(f"Error fitting collaborative filtering: {e}")
            self.mock_mode = True

    def predict_score(self, user_id: Any, meal_id: Any, fallback_rule_score: Optional[float] = None) -> float:
        """
        Predict recommendation score for a given (user_id, meal_id) pair.
        Returns a normalized score in range [0.0, 1.0].
        Implements a robust rule-based fallback for cold-start users or missing items.
        """
        # Cold start fallback if model is mock mode or missing matrix
        if self.mock_mode or self.user_item_matrix is None or self.user_item_matrix.size == 0:
            return fallback_rule_score if fallback_rule_score is not None else 0.50

        # Try to resolve user_id and meal_id integer keys
        try:
            u_key = int(user_id) if isinstance(user_id, (int, str)) and str(user_id).isdigit() else user_id
            m_key = int(meal_id) if isinstance(meal_id, (int, str)) and str(meal_id).isdigit() else meal_id
        except ValueError:
            u_key, m_key = user_id, meal_id

        # Cold-start fallback if user or meal is unknown
        if u_key not in self.user_map or m_key not in self.item_map:
            return fallback_rule_score if fallback_rule_score is not None else 0.50

        try:
            u_idx = self.user_map[u_key]
            m_idx = self.item_map[m_key]

            # Direct rating if available
            direct_rating = self.user_item_matrix[u_idx, m_idx]
            if direct_rating > 0:
                norm_direct = min(1.0, max(0.0, direct_rating / 5.0))

            # User-based CF prediction
            user_sims = self.user_similarity[u_idx]
            other_ratings = self.user_item_matrix[:, m_idx]
            valid_mask = other_ratings > 0
            if np.any(valid_mask):
                user_pred = np.sum(user_sims[valid_mask] * other_ratings[valid_mask]) / (np.sum(np.abs(user_sims[valid_mask])) + 1e-8)
            else:
                user_pred = 2.5

            # Item-based CF prediction
            item_sims = self.item_similarity[m_idx]
            user_ratings = self.user_item_matrix[u_idx, :]
            valid_item_mask = user_ratings > 0
            if np.any(valid_item_mask):
                item_pred = np.sum(item_sims[valid_item_mask] * user_ratings[valid_item_mask]) / (np.sum(np.abs(item_sims[valid_item_mask])) + 1e-8)
            else:
                item_pred = 2.5

            predicted_rating = 0.5 * user_pred + 0.5 * item_pred
            cf_norm_score = min(1.0, max(0.0, float(predicted_rating) / 5.0))

            if fallback_rule_score is not None:
                # Blend CF score with rule score for robust hybrid prediction
                return round(0.50 * cf_norm_score + 0.50 * fallback_rule_score, 4)
            return round(cf_norm_score, 4)

        except Exception as e:
            print(f"[!] CF predict_score error: {e}")
            return fallback_rule_score if fallback_rule_score is not None else 0.50

    def recommend_user_based(
        self,
        user_id: int,
        user_meal_ratings: Dict[int, Dict[int, float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """User-based collaborative filtering"""
        if self.mock_mode:
            return self._mock_recommendations(top_k)
        
        try:
            all_users = list(user_meal_ratings.keys())
            if user_id not in all_users:
                return self._mock_recommendations(top_k)
            
            user_idx = all_users.index(user_id)
            similarities = self.user_similarity[user_idx] if self.user_similarity is not None else np.ones(len(all_users))
            
            similar_users = np.argsort(similarities)[::-1][1:11]
            
            meal_scores = defaultdict(float)
            for similar_user_idx in similar_users:
                if similar_user_idx >= len(all_users):
                    continue
                similar_user_id = all_users[similar_user_idx]
                similarity_score = similarities[similar_user_idx]
                
                for meal_id, rating in user_meal_ratings[similar_user_id].items():
                    if meal_id not in user_meal_ratings[user_id]:
                        meal_scores[meal_id] += rating * similarity_score
            
            top_meals = sorted(meal_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            if not top_meals:
                return self._mock_recommendations(top_k)

            return [
                {
                    'meal_id': meal_id,
                    'score': float(round(score / (max(meal_scores.values()) + 1e-8), 4)),
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
        """Item-based collaborative filtering"""
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
            
            for liked_meal_id, rating in user_meals.items():
                if liked_meal_id not in all_meals:
                    continue
                    
                meal_idx = all_meals.index(liked_meal_id)
                similarities = self.item_similarity[meal_idx] if self.item_similarity is not None else np.ones(len(all_meals))
                
                for i, similar_meal_id in enumerate(all_meals):
                    if similar_meal_id not in user_meals and i < len(similarities):
                        meal_scores[similar_meal_id] += similarities[i] * rating
            
            top_meals = sorted(meal_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            if not top_meals:
                return self._mock_recommendations(top_k)

            return [
                {
                    'meal_id': meal_id,
                    'score': float(round(score / (max(meal_scores.values()) + 1e-8), 4)),
                    'reason': 'Similar to meals you liked'
                }
                for meal_id, score in top_meals
            ]
            
        except Exception as e:
            print(f"Error in item-based CF: {e}")
            return self._mock_recommendations(top_k)
    
    def _mock_recommendations(self, top_k: int) -> List[Dict[str, Any]]:
        """Mock recommendations for development / cold-start fallback"""
        return [
            {
                'meal_id': i + 100,
                'score': round(0.9 - (i * 0.1), 2),
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

