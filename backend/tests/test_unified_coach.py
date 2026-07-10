import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, EnhancedUser, MenstrualCycleLog, DailyTask, BiometricRecord
from app.unified_coach_service import UnifiedCoachService

# SQLite in-memory test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_unified_coach_male_profile(db):
    """Verify that a male profile outputs Emerald/male configuration and standard strength splits."""
    user = EnhancedUser(
        id=10,
        clerk_user_id="clerk_male",
        username="john_doe",
        email="john@example.com",
        gender="Male",
        primary_goal="muscle_gain",
        activity_level="moderate",
        age=30,
        weight_kg=80.0,
        height_cm=180.0,
        femmecare_enabled=False
    )
    db.add(user)
    db.commit()

    service = UnifiedCoachService(db=db)
    plan = service.get_daily_coach_plan(user_id="clerk_male")

    assert plan["gender_mode"] == "male"
    assert "normal progression" in plan["workout_recommendation"]["reasoning"].lower()
    assert plan["next_action"]["route"] == "/nutrition"

def test_unified_coach_female_femmecare(db):
    """Verify that a female profile with FemmeCare active outputs cycle phase details and pink theme styling."""
    user = EnhancedUser(
        id=11,
        clerk_user_id="clerk_female",
        username="jane_doe",
        email="jane@example.com",
        gender="Female",
        primary_goal="weight_loss",
        activity_level="moderate",
        age=28,
        weight_kg=65.0,
        height_cm=165.0,
        femmecare_enabled=True
    )
    db.add(user)
    
    # Log period start 7 days ago -> follicular phase (days 6-12)
    log = MenstrualCycleLog(
        user_id=str(user.id),
        start_date=datetime.utcnow() - timedelta(days=7),
        cycle_length_days=28
    )
    db.add(log)
    db.commit()

    service = UnifiedCoachService(db=db)
    plan = service.get_daily_coach_plan(user_id="clerk_female")

    assert plan["gender_mode"] == "femmecare"
    assert "energy is rising" in plan["coach_summary"].lower()
    assert any("cycle" in c for c in plan["constraints_applied"])

def test_unified_coach_recovery_gating(db):
    """Verify that low recovery score gates workouts and alters directives."""
    user = EnhancedUser(
        id=12,
        clerk_user_id="clerk_fatigued",
        username="tired_operator",
        email="tired@example.com",
        gender="Male",
        primary_goal="athletic",
        activity_level="high",
        age=25,
        weight_kg=75.0,
        height_cm=175.0
    )
    db.add(user)
    db.commit()

    from unittest.mock import patch
    with patch("app.unified_coach_service.calculate_recovery_score") as mock_rec:
        mock_rec.return_value = {
            "score": 30.0,
            "status": "Fatigued",
            "advice": "High fatigue detected.",
            "sleep_hours_avg": 3.0,
            "calorie_balance_yesterday": 1000.0,
            "muscle_group_recovery": {},
            "last_sync": datetime.utcnow()
        }

        service = UnifiedCoachService(db=db)
        plan = service.get_daily_coach_plan(user_id="clerk_fatigued")

        # The fallback narration logic uses reasoning from workout_rec.
        # When score is < 50, it prescribes a deload session or rest.
        assert "recovery score" in plan["workout_recommendation"]["reasoning"].lower()
        assert plan["workout_recommendation"]["type"] in ["rest", "deload"]
