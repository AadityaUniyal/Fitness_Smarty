"""
Recommendation API Endpoints

Advanced features for meal planning and optimization
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.recommendation_engine import (
    GoalPredictor, MealRecommender, FoodSwapEngine, PortionOptimizer, RecommendationEngine
)

router = APIRouter(prefix="/api/recommendations", tags=["Smart Recommendations"])

# Initialize engines
goal_predictor = GoalPredictor()
meal_recommender = MealRecommender()
food_swap_engine = FoodSwapEngine()
portion_optimizer = PortionOptimizer()


class GoalPredictionRequest(BaseModel):
    current_weight_kg: float
    target_weight_kg: float
    goal: str
    avg_daily_deficit: float  # Positive for surplus, negative for deficit


class MealRecommendationRequest(BaseModel):
    daily_targets: Dict  # From TDEE calculation
    consumed_so_far: Dict
    time_of_day: Optional[str] = "lunch"


class WorkoutPlanRequest(BaseModel):
    goal: str
    difficulty: str

class WorkoutBurnRequest(BaseModel):
    exercises: List[Dict[str, Any]] # [{'exercise_id': int, 'reps': int, 'sets': int}]

class FoodCalorieRequest(BaseModel):
    items: List[Dict[str, Any]] # [{'food_id': int, 'grams': float}]

class FoodComponent(BaseModel):
    name: str
    nutrition_per_100g: Dict

@router.get("/generate-6day-plan")
async def generate_6day_plan(
    goal: str = Query(..., description="e.g. muscle_gain, weight_loss"),
    difficulty: str = Query(..., description="Beginner, Intermediate, Advanced"),
    db: Session = Depends(get_db)
):
    """Generate a custom 6-day workout split with exercises from the expanded database."""
    try:
        engine = RecommendationEngine(db=db)
        plan = engine.generate_workout_plan(goal, difficulty)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-workout-burn")
async def calculate_workout_burn(request: WorkoutBurnRequest, db: Session = Depends(get_db)):
    """Calculate total calories burned for a list of exercises with reps and sets."""
    try:
        engine = RecommendationEngine(db=db)
        result = engine.calculate_workout_burn(request.exercises)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-food-calories")
async def calculate_food_calories(request: FoodCalorieRequest, db: Session = Depends(get_db)):
    """Calculate total nutritional intake based on food items and their weights in grams."""
    try:
        from app.models import FoodItem
        from app.nutrition_engine import get_nutritional_summary
        
        items_with_grams = []
        for entry in request.items:
            food = db.query(FoodItem).filter_by(id=entry['food_id']).first()
            if food:
                items_with_grams.append((food, entry['grams']))
        
        summary = get_nutritional_summary(items_with_grams)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-goal-timeline")
async def predict_goal_timeline(request: GoalPredictionRequest):
    """
    Predict when you'll reach your goal
    
    Uses thermodynamics: 1kg fat = 7700 calories
    Returns timeline with milestones
    """
    try:
        prediction = goal_predictor.predict_timeline(
            current_weight=request.current_weight_kg,
            target_weight=request.target_weight_kg,
            goal=request.goal,
            avg_daily_deficit=request.avg_daily_deficit
        )
        
        # Generate motivational message
        weeks = prediction['estimated_weeks']
        on_track = prediction['on_track']
        
        if on_track:
            message = f"🎯 You're on track! Reach your goal in {weeks:.1f} weeks ({prediction['estimated_months']:.1f} months)"
        else:
            needed_deficit = prediction['daily_deficit_needed']
            message = f"💡 Increase daily deficit to {needed_deficit:.0f} cal to reach goal in {weeks:.1f} weeks"
        
        return {
            **prediction,
            'message': message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-next-meal")
async def suggest_next_meal(request: MealRecommendationRequest):
    """
    AI suggests what to eat next based on remaining macros
    
    Returns optimized meal recommendation
    """
    try:
        recommendation = meal_recommender.recommend_next_meal(
            daily_targets=request.daily_targets,
            consumed_so_far=request.consumed_so_far,
            time_of_day=request.time_of_day
        )
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-food-swaps")
async def suggest_food_swaps(detected_foods: List[str]):
    """
    Suggest healthier alternatives to detected foods
    
    Returns swap suggestions with benefits
    """
    try:
        swaps = food_swap_engine.suggest_swaps(detected_foods)
        
        if not swaps:
            return {
                'swaps': [],
                'message': 'Great choices! No swaps needed for these foods.'
            }
        
        return {
            'swaps': swaps,
            'count': len(swaps),
            'message': f'Found {len(swaps)} healthier alternatives'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-portions")
async def optimize_portions(
    meal_components: List[FoodComponent],
    target_calories: float,
    target_protein: float
):
    """
    Calculate optimal serving sizes for meal components
    
    Uses mathematical optimization to hit targets
    """
    try:
        components_data = [
            {
                'name': comp.name,
                'nutrition_per_100g': comp.nutrition_per_100g
            }
            for comp in meal_components
        ]
        
        result = portion_optimizer.optimize_portions(
            meal_components=components_data,
            target_calories=target_calories,
            target_protein=target_protein
        )
        
        # Format portions into user-friendly message
        portions_list = [
            f"{food}: {grams:.0f}g"
            for food, grams in result['portions_grams'].items()
        ]
        
        return {
            **result,
            'formatted_portions': portions_list,
            'message': f"Optimized to {result['total_nutrition']['calories']:.0f} cal, {result['total_nutrition']['protein_g']:.0f}g protein"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meal-ideas/{goal}")
async def get_meal_ideas_for_goal(goal: str):
    """
    Get meal ideas tailored to specific goal
    
    Returns curated meal templates
    """
    meal_ideas = {
        'weight_loss': [
            {
                'name': 'High Protein Buddha Bowl',
                'description': 'Grilled chicken, quinoa, roasted vegetables, tahini dressing',
                'calories': 420,
                'protein_g': 38,
                'why': 'High protein keeps you full, moderate calories'
            },
            {
                'name': 'Tuna Salad Wrap',
                'description': 'Tuna, whole wheat wrap, lettuce, tomato, light mayo',
                'calories': 350,
                'protein_g': 32,
                'why': 'Lean protein, controlled portions'
            }
        ],
        'muscle_gain': [
            {
                'name': 'Power Bowl',
                'description': 'Grilled steak, sweet potato, broccoli, avocado',
                'calories': 650,
                'protein_g': 48,
                'why': 'High protein + carbs for recovery'
            },
            {
                'name': 'Peanut Butter Protein Oats',
                'description': 'Oats, protein powder, peanut butter, banana',
                'calories': 550,
                'protein_g': 42,
                'why': 'Post-workout carb + protein combo'
            }
        ],
        'maintenance': [
            {
                'name': 'Mediterranean Plate',
                'description': 'Grilled fish, lemon quinoa, Greek salad',
                'calories': 480,
                'protein_g': 35,
                'why': 'Balanced macros, heart-healthy fats'
            }
        ]
    }
    
    ideas = meal_ideas.get(goal, meal_ideas['maintenance'])
    
    return {
        'goal': goal,
        'meal_ideas': ideas,
        'count': len(ideas)
    }

@router.post("/daily-strategy")
async def get_day_strategy(
    request: Dict[str, Any], # {'consumed': dict, 'targets': dict, 'time_of_day': str, 'goal': str, 'last_meal': dict}
    db: Session = Depends(get_db)
):
    """
    Analyze current day progress and provide proactive path correction.
    """
    try:
        from app.nutrition_engine import get_meal_feedback, get_daily_strategy
        
        consumed = request.get('consumed', {})
        targets = request.get('targets', {})
        goal = request.get('goal', 'athletic')
        last_meal = request.get('last_meal') # Optional
        
        strategy_data = get_daily_strategy(consumed, targets, request.get('time_of_day', 'lunch'))
        
        feedback = None
        if last_meal:
            feedback = get_meal_feedback(last_meal, goal)
            
        return {
            "strategy": strategy_data,
            "last_meal_feedback": feedback,
            "status": "diverged" if strategy_data['is_budget_critical'] else "on_track"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/foods-by-aim")
async def get_foods_by_aim(
    goal: str = None, 
    target_muscle: str = None, 
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Recommend foods based on a specific fitness goal and targeted muscle group.
    
    Returns a list of foods tailored to the aim and muscle focus.
    """
    try:
        engine = RecommendationEngine(db=db)
        foods = engine.recommend_foods_by_goal_and_muscle(goal, target_muscle, limit)
        
        if not foods:
            return {
                "message": "No specific foods found for this combination.", 
                "foods": [], 
                "count": 0
            }
            
        return {
            "goal": goal,
            "target_muscle": target_muscle,
            "foods": foods,
            "count": len(foods)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
