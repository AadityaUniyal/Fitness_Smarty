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
    assert plan["next_action"]["route"] == "/workout"

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

    # Log very low sleep/recovery biometric records to trigger recovery constraints
    rec_record = BiometricRecord(
        user_id=str(user.id),
        category="sleep",
        value=3.5,  # 3.5 hours of sleep
        timestamp=datetime.utcnow()
    )
    db.add(rec_record)
    db.commit()

    service = UnifiedCoachService(db=db)
    plan = service.get_daily_coach_plan(user_id="clerk_fatigued")

    assert "recovery" in plan["coach_summary"].lower() or "sleep" in plan["coach_summary"].lower()
    # Check if deload/rest is prescribed
    assert plan["workout_recommendation"]["type"] in ["rest", "deload"]
