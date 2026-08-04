"""
Smart Meal Recommendation API Endpoints

Intelligent meal suggestions based on daily calorie status
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.smart_meal_service import SmartMealService


from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id


router = APIRouter(prefix="/api/smart-meals", tags=["Smart Meal Recommendations"])


@router.get("/recommend/{user_id}")
def get_meal_recommendation(
    user_id: int,
    meal_type: Optional[str] = Query(
        None, 
        description="Meal type: breakfast, lunch, dinner, snack"
    ),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get intelligent meal recommendation based on current daily status.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = SmartMealService(db)
        recommendation = service.get_meal_recommendation(
            user_id=user_id,
            meal_type=meal_type
        )
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate recommendation: {str(e)}"
        )


@router.get("/post-workout/{user_id}")
def get_post_workout_meal(
    user_id: int,
    calories_burned: float = Query(
        ..., 
        description="Calories burned in workout"
    ),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get post-workout meal recommendation.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = SmartMealService(db)
        recommendation = service.get_post_workout_meal(
            user_id=user_id,
            calories_burned=calories_burned
        )
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate post-workout meal: {str(e)}"
        )


@router.get("/quick-suggestions/{user_id}")
def get_quick_meal_suggestions(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get quick meal suggestions without detailed analysis.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        from app.models import EnhancedUser
        
        user = db.query(EnhancedUser).filter(
            EnhancedUser.id == user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        goal = user.primary_goal or "maintenance"
        
        # Simple goal-based suggestions
        suggestions_map = {
            "fat_loss": [
                "Grilled Chicken Salad (400 cal)",
                "Tuna & Vegetables (380 cal)",
                "Egg White Omelette (300 cal)",
                "Greek Yogurt & Berries (200 cal)"
            ],
            "muscle_gain": [
                "Chicken & Rice Bowl (700 cal)",
                "Steak & Sweet Potato (750 cal)",
                "Protein Shake + Oats (500 cal)",
                "Eggs & Avocado Toast (550 cal)"
            ],
            "maintenance": [
                "Mediterranean Bowl (550 cal)",
                "Grilled Fish & Quinoa (500 cal)",
                "Chicken Wrap (480 cal)",
                "Balanced Buddha Bowl (520 cal)"
            ]
        }
        
        suggestions = suggestions_map.get(goal, suggestions_map["maintenance"])
        
        return {
            "user_id": user_id,
            "goal": goal,
            "quick_suggestions": suggestions,
            "tip": "These are quick ideas. For personalized recommendations, use /recommend endpoint."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/meal-timing-guide/{user_id}")
def get_meal_timing_guide(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get optimal meal timing guide for the day.
    
    Provides:
    - When to eat each meal
    - Pre/post workout meal timing
    - Calorie distribution across meals
    """
    try:
        from app.models import EnhancedUser
        from app.gender_specific_service import GenderSpecificService
        
        user = db.query(EnhancedUser).filter(
            EnhancedUser.id == user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        goal = user.primary_goal or "maintenance"
        
        # Get TDEE for daily target
        gender_service = GenderSpecificService(db)
        tdee_data = gender_service.calculate_tdee_gender_specific(user_id)
        daily_target = tdee_data['tdee']
        
        # Meal timing recommendations
        timing_guide = {
            "breakfast": {
                "time_range": "6:00 AM - 9:00 AM",
                "calories_percentage": 25,
                "calories": round(daily_target * 0.25, 0),
                "priority": "High protein + moderate carbs",
                "reason": "Kickstart metabolism and fuel morning"
            },
            "mid_morning_snack": {
                "time_range": "10:00 AM - 11:00 AM",
                "calories_percentage": 10,
                "calories": round(daily_target * 0.10, 0),
                "priority": "Light protein snack",
                "reason": "Maintain energy until lunch"
            },
            "lunch": {
                "time_range": "12:00 PM - 2:00 PM",
                "calories_percentage": 30,
                "calories": round(daily_target * 0.30, 0),
                "priority": "Balanced meal - protein + carbs + fats",
                "reason": "Main meal of the day, sustained energy"
            },
            "afternoon_snack": {
                "time_range": "3:00 PM - 4:00 PM",
                "calories_percentage": 10,
                "calories": round(daily_target * 0.10, 0),
                "priority": "Fruit + nuts or protein bar",
                "reason": "Pre-workout fuel or afternoon boost"
            },
            "dinner": {
                "time_range": "6:00 PM - 8:00 PM",
                "calories_percentage": 25,
                "calories": round(daily_target * 0.25, 0),
                "priority": "Lean protein + vegetables",
                "reason": "Recovery meal, lighter for sleep"
            }
        }
        
        # Add workout-specific timing if applicable
        workout_timing = {
            "pre_workout": {
                "timing": "30-60 minutes before workout",
                "suggestion": "Light carbs + protein (200-300 cal)",
                "examples": ["Banana + Peanut Butter", "Protein Shake", "Oats"]
            },
            "post_workout": {
                "timing": "Within 30-60 minutes after workout",
                "suggestion": "Protein + fast carbs for recovery",
                "examples": ["Protein Shake + Banana", "Chicken + Rice", "Greek Yogurt + Berries"]
            }
        }
        
        return {
            "user_id": user_id,
            "goal": goal,
            "daily_calorie_target": round(daily_target, 0),
            "meal_timing_guide": timing_guide,
            "workout_nutrition": workout_timing,
            "tips": [
                "Eat breakfast within 1 hour of waking",
                "Space meals 3-4 hours apart",
                "Stop eating 2-3 hours before bed",
                "Hydrate between meals"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate timing guide: {str(e)}"
        )
