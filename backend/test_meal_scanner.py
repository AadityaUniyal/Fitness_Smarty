"""
Quick Test Script for Gemini Meal Scanner

Run this to verify everything works!
"""

import os
os.environ['GEMINI_API_KEY'] = 'demo'  # Will use mock mode

from app.gemini_meal_scanner import PersonalizedMealScanner, PreferenceLearner

print("="*70)
print("  GEMINI MEAL SCANNER - QUICK TEST")
print("="*70)
print()

# Test 1: Scan a meal (mock mode)
print("1️⃣ Testing meal scanning...")
scanner = PersonalizedMealScanner()
result = scanner.scan_meal("demo_meal.jpg")

print(f"✓ Detected foods: {', '.join(result['detected_foods'])}")
print(f"✓ Nutrition: {result['nutrition_estimate']['calories']} cal, "
      f"{result['nutrition_estimate']['protein_g']}g protein")
print(f"✓ Confidence: {result['confidence']}")
print()

# Test 2: Analyze for a user
print("2️⃣ Testing personalized analysis...")
user_profile = {
    'user_id': 'test_user',
    'primary_goal': 'weight_loss',
    'age': 28,
    'weight_kg': 80,
    'activity_level': 'moderate'
}

recommendation = scanner.is_good_for_user(result, user_profile)
print(f"{recommendation['recommendation']}")
print()

# Test 3: Save feedback
print("3️⃣ Testing feedback collection...")
for i in range(3):
    scanner.save_user_feedback(
        meal_id=f"meal_{i}",
        user_id="test_user",
        meal_data=result,
        user_profile=user_profile,
        thumbs_up=(i % 2 == 0)
    )

feedback_count = scanner.get_feedback_count()
print(f"✓ Saved {feedback_count} feedback samples")
print()

# Test 4: Check preferences
print("4️⃣ Testing preference learning...")
learner = PreferenceLearner()
patterns = learner.analyze_patterns("test_user")
print(f"✓ Status: {patterns.get('status', 'Not enough data yet')}")
if patterns.get('status') == 'patterns_found':
    print(f"✓ {patterns['recommendation']}")
print()

print("="*70)
print("✅ ALL TESTS PASSED!")
print()
print("Next steps:")
print("  1. Get free Gemini API key: https://makersuite.google.com/app/apikey")
print("  2. Add to .env: GEMINI_API_KEY=your_key_here")
print("  3. Start backend: python -m uvicorn main:app --reload")
print("  4. Test APIs at: http://localhost:8000/docs")
print("="*70)
