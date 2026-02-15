"""
Content-Based Filtering Recommender

Recommend meals based on nutritional profile and ingredients
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn not available")


class ContentBasedRecommender:
    """
    Content-based filtering for meal recommendations
    
    Recommends meals based on:
    - Nutritional similarity (calories, protein, carbs, fat)
    - Ingredient similarity (TF-IDF)
    - Dietary preferences
    """
    
    def __init__(self):
        """Initialize content-based recommender"""
        self.mock_mode = not SKLEARN_AVAILABLE
        self.meal_features = {}
        self.nutrition_matrix = None
        self.ingredient_vectorizer = None
        self.ingredient_matrix = None
        
        if SKLEARN_AVAILABLE:
            self.ingredient_vectorizer = TfidfVectorizer(max_features=100)
            print("✓ Content-based recommender initialized")
        else:
            print("⚠️  scikit-learn not installed. Using mock mode.")
    
    def add_meal(
        self,
        meal_id: int,
        calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        ingredients: str
    ):
        """
        Add meal to the recommendation system
        
        Args:
            meal_id: Unique meal identifier
            calories, protein_g, carbs_g, fat_g: Nutritional info
            ingredients: Comma-separated ingredient list
        """
        self.meal_features[meal_id] = {
            'nutrition': [calories, protein_g, carbs_g, fat_g],
            'ingredients': ingredients
        }
    
    def fit(self):
        """Build feature matrices from added meals"""
        if self.mock_mode or not self.meal_features:
            return
        
        try:
            # Build nutrition matrix
            meal_ids = list(self.meal_features.keys())
            nutrition_data = [self.meal_features[mid]['nutrition'] for mid in meal_ids]
            self.nutrition_matrix = np.array(nutrition_data)
            
            # Normalize nutrition values
            max_vals = self.nutrition_matrix.max(axis=0)
            max_vals[max_vals == 0] = 1  # Avoid division by zero
            self.nutrition_matrix = self.nutrition_matrix / max_vals
            
            # Build ingredient matrix
            ingredient_texts = [self.meal_features[mid]['ingredients'] for mid in meal_ids]
            self.ingredient_matrix = self.ingredient_vectorizer.fit_transform(ingredient_texts)
            
            print(f"✓ Fitted on {len(meal_ids)} meals")
            
        except Exception as e:
            print(f"Error fitting content-based filtering: {e}")
            self.mock_mode = True
    
    def recommend_by_nutrition(
        self,
        target_calories: float,
        target_protein: float,
        target_carbs: float,
        target_fat: float,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend meals with similar nutritional profile
        """
        if self.mock_mode:
            return self._mock_recommendations(top_k)
        
        try:
            # Normalize target
            target = np.array([target_calories, target_protein, target_carbs, target_fat])
            max_vals = self.nutrition_matrix.max(axis=0)
            max_vals[max_vals == 0] = 1
            target_normalized = target / max_vals
            
            # Calculate similarity
            similarities = cosine_similarity([target_normalized], self.nutrition_matrix)[0]
            
            # Get top K
            meal_ids = list(self.meal_features.keys())
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            return [
                {
                    'meal_id': meal_ids[idx],
                    'score': float(similarities[idx]),
                    'reason': 'Similar nutrition profile'
                }
                for idx in top_indices
            ]
            
        except Exception as e:
            print(f"Error in nutrition-based recommendations: {e}")
            return self._mock_recommendations(top_k)
    
    def recommend_by_ingredients(
        self,
        favorite_ingredients: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend meals with similar ingredients
        """
        if self.mock_mode:
            return self._mock_recommendations(top_k)
        
        try:
            # Vectorize favorite ingredients
            ingredient_query = ", ".join(favorite_ingredients)
            query_vector = self.ingredient_vectorizer.transform([ingredient_query])
            
            # Calculate similarity
            similarities = cosine_similarity(query_vector, self.ingredient_matrix)[0]
            
            # Get top K
            meal_ids = list(self.meal_features.keys())
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            return [
                {
                    'meal_id': meal_ids[idx],
                    'score': float(similarities[idx]),
                    'reason': 'Contains ingredients you like'
                }
                for idx in top_indices
            ]
            
        except Exception as e:
            print(f"Error in ingredient-based recommendations: {e}")
            return self._mock_recommendations(top_k)
    
    def recommend_similar_meal(
        self,
        meal_id: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find meals similar to a specific meal
        
        Combines nutrition + ingredient similarity
        """
        if self.mock_mode or meal_id not in self.meal_features:
            return self._mock_recommendations(top_k)
        
        try:
            meal_ids = list(self.meal_features.keys())
            meal_idx = meal_ids.index(meal_id)
            
            # Nutrition similarity
            nutrition_sim = cosine_similarity([self.nutrition_matrix[meal_idx]], self.nutrition_matrix)[0]
            
            # Ingredient similarity
            ingredient_sim = cosine_similarity(
                self.ingredient_matrix[meal_idx],
                self.ingredient_matrix
            )[0]
            
            # Combine (weighted average)
            combined_sim = 0.6 * nutrition_sim + 0.4 * ingredient_sim
            
            # Get top K (excluding the meal itself)
            top_indices = np.argsort(combined_sim)[::-1][1:top_k+1]
            
            return [
                {
                    'meal_id': meal_ids[idx],
                    'score': float(combined_sim[idx]),
                    'reason': 'Similar meal'
                }
                for idx in top_indices
            ]
            
        except Exception as e:
            print(f"Error finding similar meals: {e}")
            return self._mock_recommendations(top_k)
    
    def _mock_recommendations(self, top_k: int) -> List[Dict[str, Any]]:
        """Mock recommendations for development"""
        return [
            {
                'meal_id': i + 200,
                'score': 0.85 - (i * 0.08),
                'reason': 'Content-based match'
            }
            for i in range(top_k)
        ]


# Singleton instance
_content_instance: Optional[ContentBasedRecommender] = None

def get_content_recommender() -> ContentBasedRecommender:
    """Get singleton content-based instance"""
    global _content_instance
    if _content_instance is None:
        _content_instance = ContentBasedRecommender()
    return _content_instance
