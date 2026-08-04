"""
Food Swap Suggestions API Endpoints

Get healthier food alternatives and meal improvements.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..database import get_db
from ..food_swap_service import FoodSwapService
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id

router = APIRouter(prefix="/api/food-swaps", tags=["food-swaps"])


class SwapRequest(BaseModel):
    """Request model for food swap"""
    user_id: int
    food_id: int
    reason: Optional[str] = None


class MealSwapRequest(BaseModel):
    """Request model for meal swaps"""
    user_id: int
    meal_foods: List[int]


@router.post("/suggest")
async def suggest_food_swap(
    request: SwapRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Suggest a healthier alternative for a specific food
    """
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    result = service.suggest_swap(
        user_id=request.user_id,
        food_id=request.food_id,
        reason=request.reason
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/alternatives/{food_id}")
async def get_food_alternatives(
    food_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get all alternatives for a food
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    result = service.suggest_swap(user_id=user_id, food_id=food_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/by-category/{user_id}/{category}")
async def get_category_alternatives(
    user_id: int,
    category: str,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get healthy food options by category
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    result = service.get_alternatives_by_category(user_id, category)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/by-goal/{goal}")
async def get_goal_specific_swaps(
    goal: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get food swaps optimized for a specific goal
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    result = service.get_goal_specific_swaps(user_id, goal)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/meal-swaps")
async def suggest_meal_swaps(
    request: MealSwapRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Suggest swaps for an entire meal
    """
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    result = service.suggest_meal_swaps(
        user_id=request.user_id,
        meal_foods=request.meal_foods
    )
    
    return result


@router.get("/quick-swaps/{user_id}")
async def get_quick_common_swaps(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get quick common swaps for all goals
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = FoodSwapService(db)
    
    # Get swaps for all goals
    fat_loss = service.get_goal_specific_swaps(user_id, "fat_loss")
    muscle_gain = service.get_goal_specific_swaps(user_id, "muscle_gain")
    maintenance = service.get_goal_specific_swaps(user_id, "maintenance")
    
    return {
        "quick_swaps": {
            "for_fat_loss": fat_loss.get("recommended_swaps", [])[:3],
            "for_muscle_gain": muscle_gain.get("recommended_swaps", [])[:3],
            "for_maintenance": maintenance.get("recommended_swaps", [])[:3]
        },
        "universal_tips": [
            "Choose whole foods over processed",
            "Grill instead of fry",
            "Swap sugary drinks for water",
            "Add vegetables to every meal",
            "Choose lean proteins"
        ]
    }


@router.get("/smart-suggestions/{user_id}")
async def get_smart_suggestions_after_meal(
    user_id: int,
    last_meal_calories: int,
    db: Session = Depends(get_db)
):
    """
    Get smart suggestions after logging a meal
    
    Provides contextual advice based on:
    - Meal size
    - User's goals
    - Time of day
    
    Example: After logging a 800-calorie meal,
    suggests lighter options for next meal.
    """
    from ..models import EnhancedUser as User, UserGoal as UserGoals
    from datetime import datetime
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_goal = db.query(UserGoals).filter(
        UserGoals.user_id == user_id
    ).order_by(UserGoals.created_at.desc()).first()
    
    current_hour = datetime.now().hour
    
    suggestions = []
    
    # High calorie meal suggestions
    if last_meal_calories > 700:
        suggestions.append({
            "type": "portion_control",
            "message": "That was a big meal! Consider smaller portions next time.",
            "tip": "Try using a smaller plate to naturally reduce portions"
        })
        
        suggestions.append({
            "type": "next_meal",
            "message": "Balance it out with a lighter next meal",
            "tip": "Focus on vegetables and lean protein"
        })
    
    # Low calorie meal suggestions
    elif last_meal_calories < 300:
        if user_goal and user_goal.goal_type.value == "muscle_gain":
            suggestions.append({
                "type": "insufficient_calories",
                "message": "That meal might be too small for your muscle gain goal",
                "tip": "Add a protein shake or snack to hit your calorie target"
            })
    
    # Time-based suggestions
    if current_hour < 12:  # Morning
        suggestions.append({
            "type": "meal_timing",
            "message": "Great start to your day!",
            "tip": "Protein at breakfast helps control appetite all day"
        })
    elif 12 <= current_hour < 17:  # Afternoon
        suggestions.append({
            "type": "meal_timing",
            "message": "Midday fuel!",
            "tip": "Balance carbs and protein for sustained energy"
        })
    else:  # Evening
        suggestions.append({
            "type": "meal_timing",
            "message": "Evening meal logged",
            "tip": "Lighter dinners can improve sleep quality"
        })
    
    return {
        "meal_calories": last_meal_calories,
        "suggestions": suggestions,
        "quick_tip": "Remember: It's not just what you eat, but when and how much! 🍽️"
    }
