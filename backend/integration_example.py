"""
Food Scanning & Calculation - Integration Example

This shows how to use the Gemini + Neural Network system
in your own project.
"""

import requests
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:8000"

# Your user profile for personalized recommendations
USER_PROFILE = {
    "user_id": "demo_user",
    "primary_goal": "weight_loss",  # or muscle_gain, maintenance, athletic_performance
    "age": 28,
    "weight_kg": 75,
    "height_cm": 175,
    "gender": "male",
    "activity_level": "moderate"
}


# ============================================================================
# STEP 1: SCAN MEAL PHOTO
# ============================================================================

def scan_meal_photo(image_path: str):
    """
    Upload and scan a meal photo using Gemini Vision API
    
    Returns detected foods and nutrition estimates
    """
    print(f"📸 Scanning meal photo: {image_path}")
    
    with open(image_path, 'rb') as img_file:
        files = {'file': img_file}
        
        response = requests.post(
            f"{API_BASE}/api/meals/scan",
            files=files
        )
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ Food Detection:")
        print(f"   Detected: {', '.join(result['detected_foods'])}")
        print(f"   Confidence: {result['confidence']*100:.0f}%")
        print(f"\n📊 Nutrition Estimate:")
        nutrition = result['nutrition_estimate']
        print(f"   Calories: {nutrition['calories']:.0f} kcal")
        print(f"   Protein: {nutrition['protein_g']:.0f}g")
        print(f"   Carbs: {nutrition['carbs_g']:.0f}g")
        print(f"   Fat: {nutrition['fat_g']:.0f}g")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        return None


# ============================================================================
# STEP 2: GET PERSONALIZED RECOMMENDATION
# ============================================================================

def get_recommendation(meal_data, user_profile):
    """
    Get personalized recommendation using trained neural network
    
    Returns if meal is good for user's goals
    """
    print("\n🤖 Getting AI recommendation...")
    
    response = requests.post(
        f"{API_BASE}/api/meals/analyze-for-user",
        json={
            "user_profile": user_profile,
            "meal_data": meal_data
        }
    )
    
    if response.status_code == 200:
        recommendation = response.json()
        
        print(f"\n{recommendation['recommendation']}")
        print(f"   Confidence: {recommendation['confidence']*100:.0f}%")
        print(f"   Model: {recommendation.get('model_type', 'Unknown')}")
        
        return recommendation
    else:
        print(f"❌ Error: {response.status_code}")
        return None


# ============================================================================
# STEP 3: CALCULATE TDEE & TARGETS
# ============================================================================

def calculate_daily_targets(user_profile):
    """
    Calculate personalized TDEE and macro targets
    """
    print("\n🧮 Calculating daily targets...")
    
    response = requests.post(
        f"{API_BASE}/api/analytics/calculate-tdee",
        json=user_profile
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n📊 Your Daily Targets:")
        print(f"   BMR: {result['bmr']:.0f} cal/day (calories at rest)")
        print(f"   TDEE: {result['tdee']:.0f} cal/day (with activity)")
        
        targets = result['daily_targets']
        print(f"\n🎯 For {user_profile['primary_goal']}:")
        print(f"   Target Calories: {targets['target_calories']}")
        print(f"   Protein: {targets['protein_g']:.0f}g ({targets['protein_percentage']}%)")
        print(f"   Carbs: {targets['carbs_g']:.0f}g ({targets['carbs_percentage']}%)")
        print(f"   Fat: {targets['fat_g']:.0f}g ({targets['fat_percentage']}%)")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        return None


# ============================================================================
# STEP 4: SCORE MEAL FIT
# ============================================================================

def score_meal(meal_nutrition, user_profile):
    """
    Score how well meal fits user's targets (0-100)
    """
    print("\n⭐ Scoring meal fit...")
    
    response = requests.post(
        f"{API_BASE}/api/analytics/score-meal",
        json={
            "user_profile": user_profile,
            "meal_nutrition": meal_nutrition
        }
    )
    
    if response.status_code == 200:
        score_data = response.json()
        
        print(f"\n{score_data['recommendation']}")
        print(f"   Overall Score: {score_data['score']}/100")
        print(f"   Macro Fit: {score_data['macro_fit']}/100")
        print(f"   Calorie Fit: {score_data['calorie_fit']}/100")
        
        return score_data
    else:
        print(f"❌ Error: {response.status_code}")
        return None


# ============================================================================
# STEP 5: GET MEAL SUGGESTIONS
# ============================================================================

def get_meal_suggestions(daily_targets, consumed_so_far):
    """
    Get AI suggestion for what to eat next
    """
    print("\n💡 Getting meal suggestion...")
    
    response = requests.post(
        f"{API_BASE}/api/recommendations/suggest-next-meal",
        json={
            "daily_targets": daily_targets,
            "consumed_so_far": consumed_so_far,
            "time_of_day": "dinner"
        }
    )
    
    if response.status_code == 200:
        suggestion = response.json()
        
        meal = suggestion['recommended_meal']
        print(f"\n🍽️  Recommended: {meal['name']}")
        print(f"   Foods: {', '.join(meal['foods'])}")
        print(f"   Nutrition: {meal['macros']['calories']:.0f} cal, {meal['macros']['protein_g']:.0f}g protein")
        print(f"   Reason: {suggestion['reason']}")
        
        return suggestion
    else:
        print(f"❌ Error: {response.status_code}")
        return None


# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================

def complete_workflow_example():
    """
    Full workflow: Scan → Recommend → Calculate → Score → Suggest
    """
    print("="*70)
    print("  COMPLETE FOOD SCANNING & CALCULATION WORKFLOW")
    print("="*70)
    
    # Example meal photo (you'd use actual photo path)
    # meal_photo = "path/to/your/meal.jpg"
    # meal_data = scan_meal_photo(meal_photo)
    
    # Mock meal data for demo (if no photo available)
    meal_data = {
        'detected_foods': ['grilled_chicken', 'brown_rice', 'broccoli'],
        'nutrition_estimate': {
            'calories': 485,
            'protein_g': 42,
            'carbs_g': 48,
            'fat_g': 9,
            'fiber_g': 8
        },
        'confidence': 0.88
    }
    
    # Step 1: Get recommendation
    recommendation = get_recommendation(meal_data, USER_PROFILE)
    
    # Step 2: Calculate daily targets
    targets = calculate_daily_targets(USER_PROFILE)
    
    # Step 3: Score this meal
    if targets:
        score = score_meal(meal_data['nutrition_estimate'], USER_PROFILE)
    
    # Step 4: Get suggestion for next meal
    consumed = meal_data['nutrition_estimate']
    if targets:
        suggestion = get_meal_suggestions(
            targets['daily_targets'],
            consumed
        )
    
    print("\n" + "="*70)
    print("✅ Workflow complete!")
    print("="*70)


# ============================================================================
# SIMPLE INTEGRATION FOR YOUR PROJECT
# ============================================================================

class FoodScanningAPI:
    """
    Simple wrapper class to use in your project
    """
    
    def __init__(self, api_base="http://localhost:8000"):
        self.api_base = api_base
    
    def scan_photo(self, image_path):
        """Scan meal photo and get nutrition"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.api_base}/api/meals/scan", files=files)
            return response.json() if response.status_code == 200 else None
    
    def get_recommendation(self, meal_data, user_profile):
        """Get personalized meal recommendation"""
        response = requests.post(
            f"{self.api_base}/api/meals/analyze-for-user",
            json={"user_profile": user_profile, "meal_data": meal_data}
        )
        return response.json() if response.status_code == 200 else None
    
    def calculate_tdee(self, user_profile):
        """Calculate personalized targets"""
        response = requests.post(
            f"{self.api_base}/api/analytics/calculate-tdee",
            json=user_profile
        )
        return response.json() if response.status_code == 200 else None


# ============================================================================
# USAGE IN YOUR PROJECT
# ============================================================================

if __name__ == "__main__":
    # Example 1: Complete workflow
    complete_workflow_example()
    
    print("\n\n" + "="*70)
    print("  SIMPLE API WRAPPER EXAMPLE")
    print("="*70)
    
    # Example 2: Using the wrapper class
    api = FoodScanningAPI()
    
    # Get TDEE calculation
    targets = api.calculate_tdee(USER_PROFILE)
    if targets:
        print(f"\n✅ Your TDEE: {targets['tdee']:.0f} cal/day")
        print(f"   Target: {targets['daily_targets']['target_calories']} cal/day for {USER_PROFILE['primary_goal']}")
    
    print("\n" + "="*70)
    print("\n💡 Integration Tips:")
    print("   1. Copy the FoodScanningAPI class to your project")
    print("   2. Make sure backend server is running (start.py)")
    print("   3. Use api.scan_photo(image_path) to scan meals")
    print("   4. Use api.get_recommendation() for AI analysis")
    print("   5. All 18 endpoints are available via REST API")
    print("\n" + "="*70)
