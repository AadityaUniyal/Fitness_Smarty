import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, EnhancedUser, MenstrualCycleLog, FoodItem, FoodCategory
from app.security_encryption import encrypt_value, decrypt_value
from app.recommendation_engine import RecommendationEngine

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_encryption_decryption():
    """Verify application-layer field-level encryption behaves correctly."""
    secret_text = "Severe cramps and fatigue"
    enc = encrypt_value(secret_text)
    assert enc != secret_text
    dec = decrypt_value(enc)
    assert dec == secret_text

def test_adaptive_cycle_length(db_session):
    """Verify cycle sync learns user's average cycle length and flags outliers."""
    # Create test user
    user = EnhancedUser(id=1, clerk_user_id="test_user_1", username="testuser", email="test@test.com", femmecare_enabled=True)
    db_session.add(user)
    db_session.commit()

    # Log 3 cycles: Day 1 (today), 27 days ago (diff=27), 57 days ago (diff=30)
    # Rolling intervals: [27, 30] -> avg = 28.5 -> rounded = 29
    now = datetime.utcnow()
    log1 = MenstrualCycleLog(user_id="test_user_1", start_date=now)
    log2 = MenstrualCycleLog(user_id="test_user_1", start_date=now - timedelta(days=27))
    log3 = MenstrualCycleLog(user_id="test_user_1", start_date=now - timedelta(days=57))
    
    db_session.add_all([log1, log2, log3])
    db_session.commit()

    engine = RecommendationEngine(db=db_session)
    advice = engine.get_cycle_sync_advice(now, cycle_length=28, user_id="test_user_1")
    
    assert advice["learned_cycle_length"] == 29
    assert advice["cycle_history_stats"]["average_cycle_length"] == 28.5
    assert advice["cycle_history_stats"]["logged_cycles_count"] == 3

def test_symptom_aware_adaptation(db_session):
    """Verify symptom inputs dynamically adjust training advices."""
    engine = RecommendationEngine(db=db_session)
    
    # Restorative follicular phase advice modified by fatigue symptom
    advice = engine.get_cycle_sync_advice(
        datetime.utcnow(), 
        cycle_length=28, 
        user_id="test_user_1", 
        symptoms=["Fatigue", "Cramps"]
    )
    assert "Lighter session suggested today" in advice["advice"]["training"]
    assert advice["advice"]["intensity_limit"] == "Low-Moderate"

def test_iron_aware_nutrition_weighting(db_session):
    """Verify food recommendations prioritize iron-rich choices in menstrual phase."""
    # Create food category & items
    cat = FoodCategory(name="Proteins", description="Proteins")
    db_session.add(cat)
    db_session.commit()

    # Spinach (iron rich), Apple (general)
    f1 = FoodItem(category_id=cat.id, name="Apple", calories=50, protein=1, carbs=10, fats=0)
    f2 = FoodItem(category_id=cat.id, name="Spinach Salad", calories=30, protein=2, carbs=5, fats=0)
    f3 = FoodItem(category_id=cat.id, name="Lean Ground Beef", calories=250, protein=26, carbs=0, fats=15)
    
    db_session.add_all([f1, f2, f3])
    
    # Create user in menstrual phase
    user = EnhancedUser(id=2, clerk_user_id="test_user_2", username="testuser2", email="test2@test.com", femmecare_enabled=True)
    db_session.add(user)
    
    # Log period today (user is in Menstrual phase, days 1-5)
    log = MenstrualCycleLog(user_id="test_user_2", start_date=datetime.utcnow(), cycle_length_days=28)
    db_session.add(log)
    db_session.commit()

    engine = RecommendationEngine(db=db_session)
    
    # Recommend foods during Menstrual phase -> should prioritize Spinach and Beef
    recommended = engine.recommend_foods_by_goal_and_muscle(
        goal="maintenance", 
        target_muscle="full_body", 
        limit=3, 
        user_id="test_user_2"
    )
    names = [f.name for f in recommended]
    assert "Spinach Salad" in names or "Lean Ground Beef" in names
