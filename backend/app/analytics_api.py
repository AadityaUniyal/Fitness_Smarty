"""
Analytics API Endpoints

Exposes advanced nutrition calculations and tracking
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from .database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Nutrition Analytics"])

# Lazy analytics engine initialization
_analytics = None
_meal_tracker = None
_gap_analyzer = None

def _get_analytics():
    global _analytics
    if _analytics is None:
        from app.nutrition_analytics import NutritionAnalytics
        _analytics = NutritionAnalytics()
    return _analytics

def _get_meal_tracker():
    global _meal_tracker
    if _meal_tracker is None:
        from app.nutrition_analytics import MealTracker
        _meal_tracker = MealTracker()
    return _meal_tracker

def _get_gap_analyzer():
    global _gap_analyzer
    if _gap_analyzer is None:
        from app.nutrition_analytics import NutrientGapAnalyzer
        _gap_analyzer = NutrientGapAnalyzer()
    return _gap_analyzer


class UserProfileRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_level: str
    goal: str


class MealNutrition(BaseModel):
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float

class QueryRequest(BaseModel):
    query: str
    user_id: int
    fiber_g: Optional[float] = 0


@router.post("/calculate-tdee")
async def calculate_tdee(profile: UserProfileRequest):
    """
    Calculate BMR and TDEE using Mifflin-St Jeor equation
    
    Returns personalized calorie and macro targets
    """
    try:
        # Calculate BMR
        bmr = _get_analytics().calculate_bmr(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender
        )
        
        # Calculate TDEE
        tdee = _get_analytics().calculate_tdee(
            bmr=bmr,
            activity_level=profile.activity_level
        )
        
        # Calculate macro targets
        targets = _get_analytics().calculate_macro_targets(
            tdee=tdee,
            goal=profile.goal
        )
        
        return {
            'bmr': bmr,
            'tdee': tdee,
            'daily_targets': targets,
            'explanation': {
                'bmr': f"Your body burns {bmr} calories at rest",
                'tdee': f"With {profile.activity_level} activity, you burn {tdee} calories/day",
                'target': f"For {profile.goal}, aim for {targets['target_calories']} calories/day"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score-meal")
async def score_meal(
    user_profile: UserProfileRequest,
    meal_nutrition: MealNutrition
):
    """
    Score how well a meal fits the user's targets
    
    Returns score 0-100 and detailed breakdown
    """
    try:
        # Get targets
        bmr = _get_analytics().calculate_bmr(
            user_profile.weight_kg,
            user_profile.height_cm,
            user_profile.age,
            user_profile.gender
        )
        tdee = _get_analytics().calculate_tdee(bmr, user_profile.activity_level)
        targets = _get_analytics().calculate_macro_targets(tdee, user_profile.goal)
        
        # Score the meal
        score_data = _get_analytics().calculate_meal_score(
            meal_nutrition.model_dump(),
            targets
        )
        
        # Generate recommendation
        score = score_data['score']
        if score >= 80:
            rating = "Excellent"
            emoji = "[STAR]"
        elif score >= 60:
            rating = "Good"
            emoji = "[OK]"
        elif score >= 40:
            rating = "Okay"
            emoji = "[HMM]"
        else:
            rating = "Needs Improvement"
            emoji = "[!]"
        
        return {
            **score_data,
            'rating': rating,
            'emoji': emoji,
            'targets': targets,
            'recommendation': f"{emoji} {rating} fit for your {user_profile.goal} goal (score: {score}/100)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track-meal")
async def track_meal(
    meal_nutrition: MealNutrition,
    foods: List[str],
    user_liked: bool
):
    """
    Add a meal to tracking history
    
    Builds data for pattern detection
    """
    try:
        meal_data = {
            'nutrition': meal_nutrition.model_dump(),
            'foods': foods
        }
        
        _get_meal_tracker().add_meal(meal_data, user_liked)
        
        # Get updated streak
        streak = _get_meal_tracker().calculate_streak()
        
        return {
            'message': 'Meal tracked successfully',
            'streak': streak,
            'milestone': streak['current_streak'] if streak['current_streak'] in [5, 10, 25, 50, 100] else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streak")
async def get_streak():
    """Get current meal streak statistics"""
    streak = _get_meal_tracker().calculate_streak()
    
    return {
        **streak,
        'encouragement': f"{'[FIRE]' * min(streak['current_streak'], 10)} {streak['current_streak']} meal streak!"
    }


@router.get("/patterns")
async def detect_patterns():
    """
    Detect eating patterns using statistical analysis
    
    Returns insights about consistency, timing, trends
    """
    patterns = _get_meal_tracker().detect_patterns()
    
    if patterns.get('status') == 'insufficient_data':
        return {
            'status': 'insufficient_data',
            'message': 'Track at least 5 meals to see patterns'
        }
    
    return patterns


@router.get("/weekly-summary")
async def get_weekly_summary():
    """Get 7-day summary of nutrition stats"""
    summary = _get_meal_tracker().get_weekly_summary()
    
    if summary.get('status') == 'no_recent_meals':
        return {
            'status': 'no_recent_meals',
            'message': 'No meals tracked in the past 7 days'
        }
    
    return summary


@router.post("/analyze-gaps")
async def analyze_nutrient_gaps(daily_nutrition: MealNutrition):
    """
    Analyze nutrient deficiencies and excesses
    
    Compares to RDA standards
    """
    gaps = _get_gap_analyzer().analyze_gaps(daily_nutrition.model_dump())
    
    recommendations = []
    
    for deficiency in gaps['deficiencies']:
        nutrient = deficiency['nutrient'].replace('_', ' ').title()
        recommendations.append(
            f"Increase {nutrient}: {deficiency['percentage']:.0f}% of recommended"
        )
    
    return {
        **gaps,
        'recommendations': recommendations,
        'overall_score': round(
            (len(gaps['adequate']) / len(_get_gap_analyzer().rda)) * 100, 1
        )
    }


@router.get("/health-insights/{user_id}")
async def get_health_insights(user_id: str):
    """
    Comprehensive health insights combining all analytics
    
    Returns: Streaks, patterns, weekly summary, predictions
    """
    streak = _get_meal_tracker().calculate_streak()
    patterns = _get_meal_tracker().detect_patterns()
    summary = _get_meal_tracker().get_weekly_summary()
    
    insights = {
        'user_id': user_id,
        'generated_at': datetime.utcnow().isoformat(),
        'streak': streak,
        'patterns': patterns,
        'weekly_summary': summary,
        'insights': []
    }
    
    # Generate personalized insights
    if streak['current_streak'] >= 7:
        insights['insights'].append({
            'type': 'achievement',
            'message': f"Amazing! {streak['current_streak']} meal streak!",
            'emoji': '[TROPHY]'
        })
    
    if patterns.get('status') == 'patterns_detected':
        if patterns['calorie_consistency'] > 80:
            insights['insights'].append({
                'type': 'positive',
                'message': f"Excellent consistency! {patterns['calorie_consistency']:.0f}% calorie consistency",
                'emoji': '[CHART]'
            })
        
        if patterns['calorie_trend'] == 'increasing':
            insights['insights'].append({
                'type': 'warning',
                'message': "Calorie intake trending upward. Consider portion sizes.",
                'emoji': '[!]'
            })
    
    if summary.get('success_rate', 0) > 80:
        insights['insights'].append({
            'type': 'achievement',
            'message': f"Outstanding! {summary['success_rate']:.0f}% of meals align with your goals",
            'emoji': '[GOAL]'
        })
    
@router.get("/daily-budget/{user_id}")
async def get_daily_budget(user_id: int, db: Session = Depends(get_db)):
    """Get net calories for today"""
    return _get_analytics().calculate_daily_net_budget(db, user_id)

@router.get("/db-streak/{user_id}")
async def get_db_streak(user_id: int, db: Session = Depends(get_db)):
    """Get current activity streak from DB"""
    streak = _get_analytics().calculate_db_streak(db, user_id)
    return {"streak": streak}

@router.get("/powerbi-export")
async def export_powerbi(db: Session = Depends(get_db)):
    """Flattened data for Power BI consumption"""
    from . import models
    meals = db.query(models.MealLog).all()
    workouts = db.query(models.WorkoutLog).all()
    
    # Flatten meal data
    results = []
    for m in meals:
        results.append({
            "type": "meal",
            "date": m.created_at.isoformat(),
            "calories": m.total_calories,
            "protein": m.total_protein,
            "carbs": m.total_carbs,
            "fats": m.total_fats,
            "user_id": m.user_id
        })
    
    for w in workouts:
        results.append({
            "type": "workout",
            "date": w.created_at.isoformat(),
            "calories_burned": w.calories_burned,
            "duration": w.duration_minutes,
            "user_id": w.user_id
        })
        
    return results

@router.get("/plateau-detection/{user_id}")
async def get_plateau_detection(user_id: int, db: Session = Depends(get_db)):
    """Detect potential progress plateaus"""
    return _get_analytics().detect_plateaus(db, user_id)

@router.get("/correlative-insights/{user_id}")
async def get_correlative_insights(user_id: int, db: Session = Depends(get_db)):
    """Get pattern correlations for the user"""
    return _get_analytics().get_correlative_insights(db, user_id)

@router.post("/ai-query")
async def ai_data_query(request: QueryRequest, db: Session = Depends(get_db)):
    """Natural language query processing via AI Analyst"""
    from .ai_analyst import AIAnalyst
    analyst = AIAnalyst(db)
    return await analyst.process_query(request.query, request.user_id)
