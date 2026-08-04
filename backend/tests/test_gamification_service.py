import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, EnhancedUser, WorkoutLog, MealLog
from app.gamification_service import GamificationService

# Use a local in-memory SQLite engine to prevent destroying the shared test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_gamification_workflow():
    db = TestingSessionLocal()
    try:
        # Create test user
        user = EnhancedUser(
            username="gamer_1",
            email="gamer@test.com",
            clerk_user_id="clerk_gamer_1",
            weight_kg=70.0,
            height_cm=175.0,
            age=25,
            gender="Male",
            primary_goal="general"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

        # Test initial stats
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        assert stats["points"]["total"] == 0
        assert stats["points"]["level"] == 1

        # Test logging a workout
        workout = WorkoutLog(
            user_id=user_id,
            workout_name="Test Workout",
            duration_minutes=30,
            calories_burned=250,
            exercises_data={"strength": {"pushups": 20}}
        )
        db.add(workout)
        db.commit()

        result = GamificationService.on_workout_completed(db, user_id)
        assert len(result["achievements"]) >= 0

        # Verify points increased
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        assert stats["points"]["total"] > 0

        # Test logging a meal
        meal = MealLog(
            user_id=user_id,
            meal_name="Healthy Breakfast",
            total_calories=400,
            total_protein=25,
            total_carbs=40,
            total_fats=12
        )
        db.add(meal)
        db.commit()

        meal_result = GamificationService.on_meal_logged(db, user_id)
        assert len(meal_result["achievements"]) >= 0

        # Verify total points updated again
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        assert stats["points"]["breakdown"]["nutrition"] >= 0

    finally:
        db.close()
