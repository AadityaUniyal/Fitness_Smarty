"""
Workout Recommendations API Endpoints

Provides intelligent workout suggestions, rest day checks,
muscle balance analysis, and progressive overload tracking.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..workout_recommendation_service import WorkoutRecommendationService

router = APIRouter(prefix="/api/workout-recommendations", tags=["workout-recommendations"])


@router.get("/suggest/{user_id}")
async def get_workout_suggestion(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get personalized workout suggestion for today
    
    Analyzes user's workout history, muscle balance, and recovery needs
    to provide an intelligent workout recommendation.
    
    Returns:
    - Rest day recommendation if needed
    - Targeted workout with exercises, sets, reps
    - Muscle groups to focus on
    - Progressive overload suggestions
    """
    service = WorkoutRecommendationService(db)
    result = service.suggest_workout(user_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/rest-day-check/{user_id}")
async def check_rest_day(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if user needs a rest day
    
    Analyzes:
    - Consecutive workout days
    - Weekly workout volume
    - Recovery time since last workout
    
    Returns recommendation with reason.
    """
    service = WorkoutRecommendationService(db)
    result = service.check_rest_day_needed(user_id)
    return result


@router.get("/muscle-balance/{user_id}")
async def analyze_muscle_balance(
    user_id: int,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """
    Analyze muscle group distribution over time
    
    Shows which muscle groups are:
    - Neglected (< 10% of workouts)
    - Overworked (> 30% of workouts)
    - Balanced
    
    Includes balance score (0-100) and recommendations.
    """
    service = WorkoutRecommendationService(db)
    result = service.analyze_muscle_balance(user_id, days=days)
    return result


@router.get("/progressive-overload/{user_id}/{exercise_name}")
async def get_progressive_overload(
    user_id: int,
    exercise_name: str,
    db: Session = Depends(get_db)
):
    """
    Get progressive overload suggestions for a specific exercise
    
    Analyzes recent performance and suggests:
    - Weight increases
    - Rep increases
    - Set adjustments
    
    Helps ensure continuous strength progression.
    """
    service = WorkoutRecommendationService(db)
    result = service.get_progressive_overload_suggestions(user_id, exercise_name)
    return result


@router.get("/variety-check/{user_id}")
async def check_exercise_variety(
    user_id: int,
    days: Optional[int] = 14,
    db: Session = Depends(get_db)
):
    """
    Check exercise variety and suggest new exercises
    
    Prevents workout staleness by:
    - Identifying repeated exercises
    - Suggesting alternatives
    - Ensuring exercise variety
    """
    service = WorkoutRecommendationService(db)
    
    # Get recent workouts
    recent_workouts = service._get_recent_workouts(user_id, days=days)
    
    # Count exercise frequency
    exercise_frequency = {}
    for workout in recent_workouts:
        if workout.exercise_name:
            exercises = [e.strip() for e in workout.exercise_name.split(',')]
            for ex in exercises:
                exercise_frequency[ex] = exercise_frequency.get(ex, 0) + 1
    
    # Find repeated exercises
    total_workouts = len(recent_workouts)
    repeated_exercises = {
        ex: count for ex, count in exercise_frequency.items()
        if count > (total_workouts / 2)  # Done in more than half of workouts
    }
    
    return {
        "period_days": days,
        "total_workouts": total_workouts,
        "unique_exercises": len(exercise_frequency),
        "exercise_frequency": exercise_frequency,
        "repeated_exercises": repeated_exercises,
        "variety_score": min(100, len(exercise_frequency) * 5),  # More variety = higher score
        "suggestion": "Try mixing in new exercises!" if repeated_exercises else "Great variety!"
    }
