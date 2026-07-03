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


from app import models
from collections import defaultdict

def get_real_user_meal_ratings(db: Session) -> Dict[int, Dict[int, float]]:
    """
    Extract user ratings for food items from the database.
    Ratings are derived from MealLog feedback:
    - user_feedback = True -> 5.0 (Like)
    - user_feedback = False -> 1.0 (Dislike)
    - user_feedback = None -> 3.0 (Neutral/Logged)
    """
    user_meal_ratings = defaultdict(dict)
    
    # Fetch all meal logs
    logs = db.query(models.MealLog).all()
    if not logs:
        return {}
        
    # Get all food items to map names to IDs
    food_items = db.query(models.FoodItem).all()
    food_name_to_id = {f.name.lower().strip(): f.id for f in food_items}
    
    for log in logs:
        if not log.user_id:
            continue
            
        # Determine rating
        if log.user_feedback is True:
            rating = 5.0
        elif log.user_feedback is False:
            rating = 1.0
        else:
            rating = 3.0
            
        # If detected_foods exists, map each detected food name to a FoodItem ID
        foods_logged = []
        if log.detected_foods:
            for food_info in log.detected_foods:
                if isinstance(food_info, dict) and 'food_name' in food_info:
                    name = food_info['food_name'].lower().strip()
                    if name in food_name_to_id:
                        foods_logged.append(food_name_to_id[name])
                        
        # Fallback to parsing from meal_name if no detected_foods matched
        if not foods_logged and log.meal_name:
            meal_words = [w.lower().strip() for w in log.meal_name.replace(":", " ").replace(",", " ").split()]
            for word in meal_words:
                if word in food_name_to_id:
                    foods_logged.append(food_name_to_id[word])
                    
        # Update user ratings
        for food_id in foods_logged:
            current = user_meal_ratings[log.user_id].get(food_id, 0.0)
            user_meal_ratings[log.user_id][food_id] = max(current, rating)
            
    return dict(user_meal_ratings)


@router.post("/collaborative/user-based")
async def recommend_user_based(
    user_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    User-based collaborative filtering
    
    Recommends meals liked by similar users
    """
    try:
        from app.ml_models.collaborative_filtering import get_collaborative_recommender
        recommender = get_collaborative_recommender()
        
        # Get real ratings from database
        user_meal_ratings = get_real_user_meal_ratings(db)
        
        # Fallback to mock ratings if database is empty or insufficient
        if len(user_meal_ratings) < 2 or sum(len(ratings) for ratings in user_meal_ratings.values()) < 3:
            user_meal_ratings = {
                1: {1: 5.0, 2: 4.0, 3: 3.0},
                2: {1: 4.0, 4: 5.0, 5: 4.0},
                3: {2: 5.0, 4: 4.0, 6: 5.0},
                4: {3: 3.0, 5: 4.0, 6: 5.0}
            }
            is_mock_fallback = True
        else:
            is_mock_fallback = False
        
        # Fit the model
        recommender.fit(user_meal_ratings)
        
        # Get recommendations
        recommendations = recommender.recommend_user_based(user_id, user_meal_ratings, top_k)
        
        # Enrich recommendations with database FoodItem details
        enriched_recommendations = []
        for rec in recommendations:
            meal_id = rec.get('meal_id')
            food_item = db.query(models.FoodItem).filter(models.FoodItem.id == meal_id).first()
            if food_item:
                enriched_recommendations.append({
                    'meal_id': meal_id,
                    'name': food_item.name,
                    'calories': food_item.calories,
                    'protein': food_item.protein,
                    'carbs': food_item.carbs,
                    'fats': food_item.fats,
                    'score': rec.get('score'),
                    'reason': rec.get('reason')
                })
            else:
                enriched_recommendations.append(rec)
        
        return {
            'user_id': user_id,
            'method': 'user-based_collaborative_filtering',
            'is_mock_fallback': is_mock_fallback,
            'recommendations': enriched_recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User-based CF failed: {str(e)}")


@router.post("/collaborative/item-based")
async def recommend_item_based(
    user_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Item-based collaborative filtering
    
    Recommends meals similar to ones user liked
    """
    try:
        from app.ml_models.collaborative_filtering import get_collaborative_recommender
        recommender = get_collaborative_recommender()
        
        # Get real ratings from database
        user_meal_ratings = get_real_user_meal_ratings(db)
        
        # Fallback to mock ratings if database is empty or insufficient
        if len(user_meal_ratings) < 2 or sum(len(ratings) for ratings in user_meal_ratings.values()) < 3:
            user_meal_ratings = {
                1: {1: 5.0, 2: 4.0, 3: 3.0},
                2: {1: 4.0, 4: 5.0, 5: 4.0},
                3: {2: 5.0, 4: 4.0, 6: 5.0},
                4: {3: 3.0, 5: 4.0, 6: 5.0}
            }
            is_mock_fallback = True
        else:
            is_mock_fallback = False
        
        recommender.fit(user_meal_ratings)
        recommendations = recommender.recommend_item_based(user_id, user_meal_ratings, top_k)
        
        # Enrich recommendations with database FoodItem details
        enriched_recommendations = []
        for rec in recommendations:
            meal_id = rec.get('meal_id')
            food_item = db.query(models.FoodItem).filter(models.FoodItem.id == meal_id).first()
            if food_item:
                enriched_recommendations.append({
                    'meal_id': meal_id,
                    'name': food_item.name,
                    'calories': food_item.calories,
                    'protein': food_item.protein,
                    'carbs': food_item.carbs,
                    'fats': food_item.fats,
                    'score': rec.get('score'),
                    'reason': rec.get('reason')
                })
            else:
                enriched_recommendations.append(rec)
        
        return {
            'user_id': user_id,
            'method': 'item-based_collaborative_filtering',
            'is_mock_fallback': is_mock_fallback,
            'recommendations': enriched_recommendations
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
        from app.ml_models.content_based import get_content_recommender
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
            'target': target.model_dump(),
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
        from app.ml_models.content_based import get_content_recommender
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
        from app.ml_models.content_based import get_content_recommender
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
