"""
Test Gamification System

Quick test script to verify the gamification system works correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import database, models
from app.gamification_service import GamificationService
from datetime import datetime


def test_gamification():
    """Test the gamification system"""
    print("🧪 Testing Gamification System...")
    print("=" * 60)
    
    db = database.SessionLocal()
    
    try:
        # Get or create a test user
        test_user = db.query(models.EnhancedUser).filter(
            models.EnhancedUser.username == "test_gamer"
        ).first()
        
        if not test_user:
            print("\n👤 Creating test user...")
            test_user = models.EnhancedUser(
                username="test_gamer",
                email="test@smarty.ai",
                hashed_password="test_hash",
                full_name="Test Gamer"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Test user created: ID {test_user.id}")
        else:
            print(f"\n👤 Using existing test user: ID {test_user.id}")
        
        user_id = test_user.id
        
        # Test 1: Get initial stats
        print("\n📊 Test 1: Get User Stats")
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        print(f"   Level: {stats['points']['level']}")
        print(f"   Total Points: {stats['points']['total']}")
        print(f"   Achievements Completed: {stats['achievements']['total_completed']}")
        print(f"   Badges Earned: {stats['badges']['total_earned']}")
        
        # Test 2: Log a workout and check gamification
        print("\n💪 Test 2: Log Workout")
        workout = models.WorkoutLog(
            user_id=user_id,
            workout_name="Test Workout",
            duration_minutes=30,
            calories_burned=250,
            exercises_data={"strength": {"pushups": 20, "squats": 30}}
        )
        db.add(workout)
        db.commit()
        
        result = GamificationService.on_workout_completed(db, user_id)
        print(f"   Workout logged!")
        print(f"   New Achievements: {len(result['achievements'])}")
        for ach in result['achievements']:
            print(f"      🏆 {ach['icon']} {ach['name']} (+{ach['points']} pts)")
        
        # Test 3: Log a meal and check gamification
        print("\n🍽️  Test 3: Log Meal")
        meal = models.MealLog(
            user_id=user_id,
            meal_name="Test Meal",
            total_calories=500,
            total_protein=30,
            total_carbs=50,
            total_fats=20
        )
        db.add(meal)
        db.commit()
        
        result = GamificationService.on_meal_logged(db, user_id)
        print(f"   Meal logged!")
        print(f"   New Achievements: {len(result['achievements'])}")
        for ach in result['achievements']:
            print(f"      🏆 {ach['icon']} {ach['name']} (+{ach['points']} pts)")
        
        # Test 4: Check final stats
        print("\n📊 Test 4: Final Stats")
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        print(f"   Level: {stats['points']['level']}")
        print(f"   Total Points: {stats['points']['total']}")
        print(f"   Workout Points: {stats['points']['breakdown']['workout']}")
        print(f"   Nutrition Points: {stats['points']['breakdown']['nutrition']}")
        print(f"   Achievements Completed: {stats['achievements']['total_completed']}")
        
        # Show streaks
        if stats['streaks']:
            print(f"\n🔥 Streaks:")
            for streak in stats['streaks']:
                print(f"      {streak['streak_type']}: {streak['current_streak']} days")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_gamification()
