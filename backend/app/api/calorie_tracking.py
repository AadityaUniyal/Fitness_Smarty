"""
Calorie Tracking API Endpoints

Automatic calorie calculations for exercise and food with daily tracking
"""

from fastapi import APIRouter, Depends, Body, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import date, datetime
from pydantic import BaseModel

from app.database import get_db
from app.calorie_tracker_service import CalorieTrackerService


from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id


router = APIRouter(prefix="/api/calorie-tracking", tags=["Calorie Tracking"])


class ExerciseLogRequest(BaseModel):
    """Request model for logging exercises with automatic calorie calculation"""
    user_id: int
    exercises: List[Dict]  # [{exercise_id, duration_minutes?, reps?, sets?}]
    workout_name: Optional[str] = None


class FoodLogRequest(BaseModel):
    """Request model for logging food with automatic calorie calculation"""
    user_id: int
    foods: List[Dict]  # [{food_id, quantity_grams}]
    meal_name: Optional[str] = None
    meal_type: Optional[str] = None  # breakfast, lunch, dinner, snack


@router.post("/calculate-exercise-calories")
def calculate_exercise_calories(
    exercise_id: int = Body(...),
    duration_minutes: Optional[int] = Body(None),
    reps: Optional[int] = Body(None),
    sets: int = Body(1),
    db: Session = Depends(get_db)
):
    """
    Calculate calories burned for a single exercise.
    """
    try:
        service = CalorieTrackerService(db)
        result = service.calculate_exercise_calories(
            exercise_id=exercise_id,
            duration_minutes=duration_minutes,
            reps=reps,
            sets=sets
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.post("/calculate-food-calories")
def calculate_food_calories(
    food_id: int = Body(...),
    quantity_grams: float = Body(...),
    db: Session = Depends(get_db)
):
    """
    Calculate calories and macros for a food item based on quantity in grams.
    """
    try:
        service = CalorieTrackerService(db)
        result = service.calculate_food_calories(
            food_id=food_id,
            quantity_grams=quantity_grams
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.post("/log-workout")
def log_workout_with_calories(
    request: ExerciseLogRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Log a complete workout with automatic calorie calculation.
    """
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = CalorieTrackerService(db)
        workout_log = service.log_exercise_with_calories(
            user_id=request.user_id,
            exercises=request.exercises,
            workout_name=request.workout_name
        )
        
        return {
            "workout_log_id": workout_log.id,
            "user_id": workout_log.user_id,
            "workout_name": workout_log.workout_name,
            "total_calories_burned": workout_log.calories_burned,
            "duration_minutes": workout_log.duration_minutes,
            "exercises": workout_log.exercises_data,
            "logged_at": workout_log.created_at.isoformat(),
            "message": f"Workout logged! You burned {workout_log.calories_burned} calories."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log workout: {str(e)}")


@router.post("/log-meal")
def log_meal_with_calories(
    request: FoodLogRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Log a meal with automatic calorie and macro calculation.
    """
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = CalorieTrackerService(db)
        meal_log = service.log_food_with_calories(
            user_id=request.user_id,
            foods=request.foods,
            meal_name=request.meal_name,
            meal_type=request.meal_type
        )
        
        return {
            "meal_log_id": meal_log.id,
            "user_id": meal_log.user_id,
            "meal_name": meal_log.meal_name,
            "total_calories": meal_log.total_calories,
            "total_protein_g": meal_log.total_protein,
            "total_carbs_g": meal_log.total_carbs,
            "total_fat_g": meal_log.total_fats,
            "foods": meal_log.detected_foods,
            "logged_at": meal_log.created_at.isoformat(),
            "message": f"Meal logged! {meal_log.total_calories} calories consumed."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log meal: {str(e)}")


@router.get("/daily-summary/{user_id}")
def get_daily_calorie_summary(
    user_id: int,
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get complete daily calorie summary with net calories.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = CalorieTrackerService(db)
        
        parsed_date = None
        if target_date:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        summary = service.get_daily_calorie_summary(
            user_id=user_id,
            target_date=parsed_date
        )
        
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/weekly-trends/{user_id}")
def get_weekly_calorie_trends(
    user_id: int,
    weeks: int = Query(1, ge=1, le=12, description="Number of weeks to analyze"),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get calorie trends over multiple weeks.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = CalorieTrackerService(db)
        trends = service.get_weekly_calorie_trends(
            user_id=user_id,
            weeks=weeks
        )
        return trends
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.get("/workout-history/{user_id}")
def get_workout_history(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """Get recent workout logs for history and reporting."""
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    workouts = (
        db.query(models.WorkoutLog)
        .filter(models.WorkoutLog.user_id == user_id)
        .order_by(models.WorkoutLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "workouts": [
            {
                "id": w.id,
                "name": w.workout_name or "Workout",
                "duration": w.duration_minutes or 0,
                "calories_burned": w.calories_burned or 0,
                "exercises_completed": len(w.exercises_data or []),
                "exercises_total": len(w.exercises_data or []),
                "timestamp": w.created_at.isoformat() if w.created_at else None,
                "goal": (w.exercises_data or {}).get("goal") if isinstance(w.exercises_data, dict) else None,
                "exercises_data": w.exercises_data,
            }
            for w in workouts
        ],
        "total_count": len(workouts)
    }


@router.get("/quick-check/{user_id}")
def quick_calorie_check(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Quick check of today's calorie status.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = CalorieTrackerService(db)
        summary = service.get_daily_calorie_summary(user_id=user_id)
        
        # Simplified response
        return {
            "calories_consumed": summary['calories_consumed'],
            "calories_burned": summary['calories_burned'],
            "net_calories": summary['net_calories'],
            "calories_remaining": summary['calories_remaining'],
            "progress_percentage": summary['progress_percentage'],
            "on_track": summary['on_track'],
            "status_message": (
                f"✅ Great! You have {summary['calories_remaining']} calories left today."
                if summary['on_track']
                else f"⚠️ Over target by {abs(summary['calories_remaining'])} calories."
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quick check: {str(e)}")
