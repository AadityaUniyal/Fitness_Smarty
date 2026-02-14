"""
Analytics API Endpoints

Exposes advanced nutrition calculations and tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from app.nutrition_analytics import NutritionAnalytics, MealTracker, NutrientGapAnalyzer

router = APIRouter(prefix="/api/analytics", tags=["Nutrition Analytics"])

# Initialize analytics engines
analytics = NutritionAnalytics()
meal_tracker = MealTracker()
gap_analyzer = NutrientGapAnalyzer()


class UserProfileRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_level: str
    goal: str


class MealNutrition(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = 0


@router.post("/calculate-tdee")
async def calculate_tdee(profile: UserProfileRequest):
    """
    Calculate BMR and TDEE using Mifflin-St Jeor equation
    
    Returns personalized calorie and macro targets
    """
    try:
        # Calculate BMR
        bmr = analytics.calculate_bmr(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            gender=profile.gender
        )
        
        # Calculate TDEE
        tdee = analytics.calculate_tdee(
            bmr=bmr,
            activity_level=profile.activity_level
        )
        
        # Calculate macro targets
        targets = analytics.calculate_macro_targets(
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
        bmr = analytics.calculate_bmr(
            user_profile.weight_kg,
            user_profile.height_cm,
            user_profile.age,
            user_profile.gender
        )
        tdee = analytics.calculate_tdee(bmr, user_profile.activity_level)
        targets = analytics.calculate_macro_targets(tdee, user_profile.goal)
        
        # Score the meal
        score_data = analytics.calculate_meal_score(
            meal_nutrition.dict(),
            targets
        )
        
        # Generate recommendation
        score = score_data['score']
        if score >= 80:
            rating = "Excellent"
            emoji = "🌟"
        elif score >= 60:
            rating = "Good"
            emoji = "👍"
        elif score >= 40:
            rating = "Okay"
            emoji = "🤔"
        else:
            rating = "Needs Improvement"
            emoji = "⚠️"
        
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
            'nutrition': meal_nutrition.dict(),
            'foods': foods
        }
        
        meal_tracker.add_meal(meal_data, user_liked)
        
        # Get updated streak
        streak = meal_tracker.calculate_streak()
        
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
    streak = meal_tracker.calculate_streak()
    
    return {
        **streak,
        'encouragement': f"{'🔥' * min(streak['current_streak'], 10)} {streak['current_streak']} meal streak!"
    }


@router.get("/patterns")
async def detect_patterns():
    """
    Detect eating patterns using statistical analysis
    
    Returns insights about consistency, timing, trends
    """
    patterns = meal_tracker.detect_patterns()
    
    if patterns.get('status') == 'insufficient_data':
        return {
            'status': 'insufficient_data',
            'message': 'Track at least 5 meals to see patterns'
        }
    
    return patterns


@router.get("/weekly-summary")
async def get_weekly_summary():
    """Get 7-day summary of nutrition stats"""
    summary = meal_tracker.get_weekly_summary()
    
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
    gaps = gap_analyzer.analyze_gaps(daily_nutrition.dict())
    
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
            (len(gaps['adequate']) / len(gap_analyzer.rda)) * 100, 1
        )
    }


@router.get("/health-insights/{user_id}")
async def get_health_insights(user_id: str):
    """
    Comprehensive health insights combining all analytics
    
    Returns: Streaks, patterns, weekly summary, predictions
    """
    streak = meal_tracker.calculate_streak()
    patterns = meal_tracker.detect_patterns()
    summary = meal_tracker.get_weekly_summary()
    
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
            'emoji': '🏆'
        })
    
    if patterns.get('status') == 'patterns_detected':
        if patterns['calorie_consistency'] > 80:
            insights['insights'].append({
                'type': 'positive',
                'message': f"Excellent consistency! {patterns['calorie_consistency']:.0f}% calorie consistency",
                'emoji': '📊'
            })
        
        if patterns['calorie_trend'] == 'increasing':
            insights['insights'].append({
                'type': 'warning',
                'message': "Calorie intake trending upward. Consider portion sizes.",
                'emoji': '⚠️'
            })
    
    if summary.get('success_rate', 0) > 80:
        insights['insights'].append({
            'type': 'achievement',
            'message': f"Outstanding! {summary['success_rate']:.0f}% of meals align with your goals",
            'emoji': '🎯'
        })
    
    return insights
