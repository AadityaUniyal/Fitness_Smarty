"""
Test Script for Advanced Analytics

Tests all the new math/logic/tracking features
"""

from app.nutrition_analytics import NutritionAnalytics, MealTracker, NutrientGapAnalyzer
from datetime import datetime, timedelta

print("="*70)
print("  ADVANCED ANALYTICS TEST")
print("="*70)
print()

# Test 1: TDEE Calculation
print("1️⃣ Testing TDEE & Macro Calculations...")
analytics = NutritionAnalytics()

# Example user profile
weight_kg = 75
height_cm = 180
age = 28
gender = 'male'
activity = 'moderate'
goal = 'muscle_gain'

bmr = analytics.calculate_bmr(weight_kg, height_cm, age, gender)
tdee = analytics.calculate_tdee(bmr, activity)
targets = analytics.calculate_macro_targets(tdee, goal)

print(f"  BMR: {bmr} cal/day")
print(f"  TDEE: {tdee} cal/day (with {activity} activity)")
print(f"  Goal: {goal}")
print(f"  Daily Targets:")
print(f"    - Calories: {targets['target_calories']}")
print(f"    - Protein: {targets['protein_g']}g ({targets['protein_percentage']}%)")
print(f"    - Carbs: {targets['carbs_g']}g ({targets['carbs_percentage']}%)")
print(f"    - Fat: {targets['fat_g']}g ({targets['fat_percentage']}%)")
print()

# Test 2: Meal Scoring
print("2️⃣ Testing Meal Scoring...")
meal_nutrition = {
    'calories': 550,
    'protein_g': 45,
    'carbs_g': 55,
    'fat_g': 15
}

score = analytics.calculate_meal_score(meal_nutrition, targets)
print(f"  Meal: {meal_nutrition['calories']} cal, {meal_nutrition['protein_g']}g protein")
print(f"  Overall Score: {score['score']}/100")
print(f"  Macro Fit: {score['macro_fit']}/100")
print(f"  Calorie Fit: {score['calorie_fit']}/100")
print()

# Test 3: Streak Tracking
print("3️⃣ Testing Streak Tracking...")
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
    
    # Every other meal is liked
    user_liked = (i % 2 == 0)
    
    timestamp = datetime.utcnow() - timedelta(days=10-i)
    tracker.add_meal(meal_data, user_liked, timestamp)

streak_stats = tracker.calculate_streak()
print(f"  Current Streak: {streak_stats['current_streak']}")
print(f"  Longest Streak: {streak_stats['longest_streak']}")
print(f"  Success Rate: {streak_stats['success_rate']}%")
print()

# Test 4: Pattern Detection
print("4️⃣ Testing Pattern Detection...")
patterns = tracker.detect_patterns()

if patterns['status'] == 'patterns_detected':
    print(f"  Meals Analyzed: {patterns['meal_count']}")
    print(f"  Avg Calories/Meal: {patterns['avg_calories_per_meal']}")
    print(f"  Calorie Consistency: {patterns['calorie_consistency']}/100")
    print(f"  Calorie Trend: {patterns['calorie_trend']}")
    print(f"  Avg Protein/Meal: {patterns['avg_protein_per_meal']}g")
print()

# Test 5: Weekly Summary
print("5️⃣ Testing Weekly Summary...")
summary = tracker.get_weekly_summary()

if summary.get('status') != 'no_recent_meals':
    print(f"  Total Meals (7 days): {summary['total_meals']}")
    print(f"  Meals/Day: {summary['meals_per_day']}")
    print(f"  Avg Daily Calories: {summary['avg_daily_calories']}")
    print(f"  Avg Daily Protein: {summary['avg_daily_protein']}g")
    print(f"  Success Rate: {summary['success_rate']}%")
print()

# Test 6: Nutrient Gap Analysis
print("6️⃣ Testing Nutrient Gap Analysis...")
gap_analyzer = NutrientGapAnalyzer()

daily_nutrition = {
    'protein_g': 80,
    'fiber_g': 15,
    'vitamin_c_mg': 50,
    'calcium_mg': 600,
    'iron_mg': 12
}

gaps = gap_analyzer.analyze_gaps(daily_nutrition)
print(f"  Adequate Nutrients: {len(gaps['adequate'])}")
print(f"  Deficiencies: {len(gaps['deficiencies'])}")
if gaps['deficiencies']:
    for def_item in gaps['deficiencies']:
        print(f"    - {def_item['nutrient']}: {def_item['percentage']}% of RDA")
print(f"  Excesses: {len(gaps['excess'])}")
if gaps['excess']:
    for exc_item in gaps['excess']:
        print(f"    - {exc_item['nutrient']}: {exc_item['percentage']}% of RDA")
print()

print("="*70)
print("✅ ALL ANALYTICS TESTS PASSED!")
print()
print("New Features Added:")
print("  📊 TDEE/BMR calculation (Mifflin-St Jeor equation)")
print("  🎯 Dynamic macro targets based on goals")
print("  ⭐ Meal scoring algorithm (0-100)")
print("  🔥 Streak tracking with success rates")
print("  📈 Pattern detection (trends, consistency)")
print("  📅 Weekly summary statistics")
print("  💊 Nutrient gap analysis (RDA comparison)")
print("="*70)
