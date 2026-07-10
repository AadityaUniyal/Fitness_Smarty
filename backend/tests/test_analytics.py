"""
Test Script for Advanced Analytics
"""

import pytest
pytest.importorskip("numpy")
from app.nutrition_analytics import NutritionAnalytics, MealTracker, NutrientGapAnalyzer
from datetime import datetime, timedelta

def test_analytics_all():
    # Test 1: TDEE Calculation
    analytics = NutritionAnalytics()

    weight_kg = 75
    height_cm = 180
    age = 28
    gender = 'male'
    activity = 'moderate'
    goal = 'muscle_gain'

    bmr = analytics.calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = analytics.calculate_tdee(bmr, activity)
    targets = analytics.calculate_macro_targets(tdee, goal)

    assert bmr > 0
    assert tdee > bmr
    assert targets['target_calories'] > 0
    assert 'protein_g' in targets

    # Test 2: Meal Scoring
    meal_nutrition = {
        'calories': 550,
        'protein_g': 45,
        'carbs_g': 55,
        'fat_g': 15
    }

    score = analytics.calculate_meal_score(meal_nutrition, targets)
    assert score['score'] >= 0 and score['score'] <= 100

    # Test 3: Streak Tracking
    tracker = MealTracker()

    # Simulate 10 meals
    for i in range(10):
        meal_data = {
            'nutrition': {
                'calories': 450 + (i * 10),
                'protein_g': 30 + i,
                'carbs_g': 45,
                'fat_g': 12
            },
            'foods': ['chicken', 'rice', 'vegetables']
        }
        user_liked = (i % 2 == 0)
        timestamp = datetime.utcnow() - timedelta(days=10-i)
        tracker.add_meal(meal_data, user_liked, timestamp)

    streak_stats = tracker.calculate_streak()
    assert streak_stats['longest_streak'] >= 0

    # Test 4: Pattern Detection
    patterns = tracker.detect_patterns()
    assert 'status' in patterns

    # Test 5: Weekly Summary
    summary = tracker.get_weekly_summary()
    assert 'period' in summary

    # Test 6: Nutrient Gap Analysis
    gap_analyzer = NutrientGapAnalyzer()
    daily_nutrition = {
        'protein_g': 80,
        'fiber_g': 15,
        'vitamin_c_mg': 50,
        'calcium_mg': 600,
        'iron_mg': 12
    }
    gaps = gap_analyzer.analyze_gaps(daily_nutrition)
    assert 'adequate' in gaps
    assert 'deficiencies' in gaps
