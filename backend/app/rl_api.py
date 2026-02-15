"""
Reinforcement Learning API Router

Endpoints for RL-based meal optimization and habit formation
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/rl", tags=["reinforcement-learning"])


class UserGoals(BaseModel):
    """User goals for meal planning"""
    daily_calories: float = 2000
    protein_target: float = 150
    goal_type: str = "weight_loss"  # weight_loss, muscle_gain, maintenance


class CurrentNutrition(BaseModel):
    """Current nutrition state"""
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@router.post("/optimize-meal-plan")
async def optimize_meal_plan(
    user_goals: UserGoals,
    time_horizon_days: int = 7
):
    """
    Use DQN to optimize meal sequence
    
    Returns optimal meal plan for next N days
    """
    try:
        from app.ml_models.reinforcement_learning import get_dqn_sequencer
        dqn = get_dqn_sequencer()
        
        # Mock current nutrition
        current_nutrition = {
            'calories': 1500,
            'protein_g': 100,
            'carbs_g': 180,
            'fat_g': 50
        }
        
        plan = dqn.optimize_meal_plan(
            user_goals.dict(),
            current_nutrition,
            time_horizon_days
        )
        
        return plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meal optimization failed: {str(e)}")


@router.post("/suggest-next-meal")
async def suggest_next_meal(
    meals_today: List[Dict],
    remaining_calories: float,
    remaining_protein: float
):
    """
    DQN-based next meal suggestion
    
    Given current state, what should you eat next?
    """
    try:
        from app.ml_models.reinforcement_learning import get_dqn_sequencer
        dqn = get_dqn_sequencer()
        
        remaining_targets = {
            'calories': remaining_calories,
            'protein_g': remaining_protein,
            'carbs_g': 50,
            'fat_g': 20
        }
        
        suggestion = dqn.suggest_next_meal(meals_today, remaining_targets)
        
        return suggestion
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Next meal suggestion failed: {str(e)}")


@router.post("/build-habit")
async def build_habit_plan(
    target_habit: str,
    current_streak: int = 0
):
    """
    Q-learning habit formation plan
    
    Create personalized habit-building strategy
    """
    try:
        from app.ml_models.reinforcement_learning import get_habit_former
        habit_former = get_habit_former()
        
        plan = habit_former.build_habit_plan(target_habit, current_streak)
        
        return plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Habit plan failed: {str(e)}")


@router.get("/models/status")
async def get_rl_models_status():
    """Check RL model status"""
    
    status = {
        'dqn': {
            'available': True,
            'status': 'mock',
            'description': 'Deep Q-Network for meal sequencing'
        },
        'q_learning': {
            'available': True,
            'status': 'mock',
            'description': 'Q-Learning for habit formation'
        }
    }
    
    return {
        'models': status,
        'available_count': 2,
        'total_count': 2,
        'note': 'Mock implementations - production training requires historical data',
        'phase': 5
    }
