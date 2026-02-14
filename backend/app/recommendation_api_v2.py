"""
Recommendation API Router

Endpoints for personalized meal recommendations
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/api/recommend", tags=["recommendations"])


class UserRating(BaseModel):
    """User rating for a meal"""
    user_id: int
    meal_id: int
    rating: float = 1.0  # Implicit (1.0) or explicit (1-5)


class NutritionTarget(BaseModel):
    """Target nutrition for recommendations"""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@router.post("/collaborative/user-based")
async def recommend_user_based(
    user_id: int,
    top_k: int = 5
):
    """
    User-based collaborative filtering
    
    Recommends meals liked by similar users
    """
    try:
        from app.models.collaborative_filtering import get_collaborative_recommender
        recommender = get_collaborative_recommender()
        
        # Mock user-meal ratings (in production: fetch from DB)
        user_meal_ratings = {
            1: {101: 5.0, 102: 4.0, 103: 3.0},
            2: {101: 4.0, 104: 5.0, 105: 4.0},
            3: {102: 5.0, 104: 4.0, 106: 5.0},
            4: {103: 3.0, 105: 4.0, 106: 5.0}
        }
        
        # Fit the model
        recommender.fit(user_meal_ratings)
        
        # Get recommendations
        recommendations = recommender.recommend_user_based(user_id, user_meal_ratings, top_k)
        
        return {
            'user_id': user_id,
            'method': 'user-based_collaborative_filtering',
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User-based CF failed: {str(e)}")


@router.post("/collaborative/item-based")
async def recommend_item_based(
    user_id: int,
    top_k: int = 5
):
    """
    Item-based collaborative filtering
    
    Recommends meals similar to ones user liked
    """
    try:
        from app.models.collaborative_filtering import get_collaborative_recommender
        recommender = get_collaborative_recommender()
        
        # Mock data
        user_meal_ratings = {
            1: {101: 5.0, 102: 4.0, 103: 3.0},
            2: {101: 4.0, 104: 5.0, 105: 4.0},
            3: {102: 5.0, 104: 4.0, 106: 5.0}
        }
        
        recommender.fit(user_meal_ratings)
        recommendations = recommender.recommend_item_based(user_id, user_meal_ratings, top_k)
        
        return {
            'user_id': user_id,
            'method': 'item-based_collaborative_filtering',
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Item-based CF failed: {str(e)}")


@router.post("/content/by-nutrition")
async def recommend_by_nutrition(
    target: NutritionTarget,
    top_k: int = 5
):
    """
    Content-based filtering by nutrition
    
    Recommends meals with similar nutritional profile
    """
    try:
        from app.models.content_based import get_content_recommender
        recommender = get_content_recommender()
        
        # Add mock meals
        meals_data = [
            (101, 450, 35, 45, 12, "chicken, rice, broccoli"),
            (102, 520, 15, 68, 18, "pasta, tomato, basil, olive oil"),
            (103, 380, 25, 40, 10, "salmon, quinoa, spinach"),
            (104, 420, 30, 42, 14, "turkey, sweet potato, asparagus"),
            (105, 490, 20, 55, 20, "beef, pasta, cheese")
        ]
        
        for meal_id, cal, prot, carbs, fat, ingredients in meals_data:
            recommender.add_meal(meal_id, cal, prot, carbs, fat, ingredients)
        
        recommender.fit()
        
        # Get recommendations
        recommendations = recommender.recommend_by_nutrition(
            target.calories, target.protein_g, target.carbs_g, target.fat_g, top_k
        )
        
        return {
            'target': target.dict(),
            'method': 'content-based_nutrition',
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content-based nutrition failed: {str(e)}")


@router.post("/content/by-ingredients")
async def recommend_by_ingredients(
    favorite_ingredients: List[str],
    top_k: int = 5
):
    """
    Content-based filtering by ingredients
    
    Recommends meals with similar ingredients
    """
    try:
        from app.models.content_based import get_content_recommender
        recommender = get_content_recommender()
        
        # Add meals (same as above)
        meals_data = [
            (101, 450, 35, 45, 12, "chicken, rice, broccoli"),
            (102, 520, 15, 68, 18, "pasta, tomato, basil, olive oil"),
            (103, 380, 25, 40, 10, "salmon, quinoa, spinach"),
            (104, 420, 30, 42, 14, "turkey, sweet potato, asparagus"),
            (105, 490, 20, 55, 20, "beef, pasta, cheese")
        ]
        
        for meal_id, cal, prot, carbs, fat, ingredients in meals_data:
            recommender.add_meal(meal_id, cal, prot, carbs, fat, ingredients)
        
        recommender.fit()
        
        # Get recommendations
        recommendations = recommender.recommend_by_ingredients(favorite_ingredients, top_k)
        
        return {
            'favorite_ingredients': favorite_ingredients,
            'method': 'content-based_ingredients',
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingredient-based recommendations failed: {str(e)}")


@router.get("/similar-meals/{meal_id}")
async def find_similar_meals(
    meal_id: int,
    top_k: int = 5
):
    """
    Find meals similar to a specific meal
    
    Combines nutrition + ingredient similarity
    """
    try:
        from app.models.content_based import get_content_recommender
        recommender = get_content_recommender()
        
        # Add meals
        meals_data = [
            (101, 450, 35, 45, 12, "chicken, rice, broccoli"),
            (102, 520, 15, 68, 18, "pasta, tomato, basil, olive oil"),
            (103, 380, 25, 40, 10, "salmon, quinoa, spinach"),
            (104, 420, 30, 42, 14, "turkey, sweet potato, asparagus"),
            (105, 490, 20, 55, 20, "beef, pasta, cheese")
        ]
        
        for mid, cal, prot, carbs, fat, ingredients in meals_data:
            recommender.add_meal(mid, cal, prot, carbs, fat, ingredients)
        
        recommender.fit()
        
        # Find similar
        recommendations = recommender.recommend_similar_meal(meal_id, top_k)
        
        return {
            'meal_id': meal_id,
            'method': 'content-based_similarity',
            'recommendations': recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar meal search failed: {str(e)}")


@router.get("/models/status")
async def get_recommendation_models_status():
    """
    Check recommendation model availability
    """
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        SKLEARN_AVAILABLE = True
    except:
        SKLEARN_AVAILABLE = False
    
    status = {
        'collaborative_filtering': {
            'available': SKLEARN_AVAILABLE,
            'status': 'ready' if SKLEARN_AVAILABLE else 'not_installed',
            'description': 'User-based and item-based recommendations'
        },
        'content_based': {
            'available': SKLEARN_AVAILABLE,
            'status': 'ready' if SKLEARN_AVAILABLE else 'not_installed',
            'description': 'Nutrition and ingredient-based matching'
        }
    }
    
    available_count = sum(1 for model in status.values() if model['available'])
    
    return {
        'models': status,
        'available_count': available_count,
        'total_count': len(status),
        'recommended_setup': 'Install scikit-learn',
        'phase': 4
    }
