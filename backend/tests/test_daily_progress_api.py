import pytest
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db
from app import models
from app.clerk_auth import get_current_user_id_from_clerk

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_user_id():
    return "1"


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_overrides():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id_from_clerk] = override_user_id
    yield
    app.dependency_overrides.clear()


def create_user(db):
    user = models.EnhancedUser(
        id=1,
        clerk_user_id="1",
        username="tester",
        email="tester@example.com",
        weight_kg=80,
        height_cm=180,
        age=30,
        gender="Male",
        primary_goal="muscle_gain",
    )
    db.add(user)
    db.commit()


def test_set_logged_updates_daily_progress_row():
    db = TestingSessionLocal()
    create_user(db)
    db.close()
    resp = client.post("/api/daily-progress/set-logged", json={"user_id": 1, "sets_added": 3, "workout_planned_id": 11})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sets_completed"] == 3
    assert data["workout_status"] in {"in_progress", "done"}


def test_meal_logged_creates_or_updates_progress():
    resp = client.post("/api/daily-progress/meal-logged", json={"user_id": 1})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["calories_consumed"] >= 0
    assert "calories_remaining" in data


def test_weekly_summary_returns_rollup():
    resp = client.get("/api/daily-progress/weekly/1?days=7")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"] == 1
    assert "summary" in data
    assert "daily" in data


def test_daily_progress_get_returns_current_row():
    client.post("/api/daily-progress/refresh/1")
    resp = client.get("/api/daily-progress/1")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "calories" in data
    assert "protein" in data
    assert "carbs" in data
    assert "fats" in data
    assert "workout" in data
    assert "check_in" in data
    assert "remaining" in data["calories"]
    assert "sets_completed" in data["workout"]
