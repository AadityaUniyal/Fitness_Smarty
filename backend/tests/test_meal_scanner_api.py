import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.database import Base, get_db
from app import meal_scanning_api

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
    yield
    app.dependency_overrides.clear()


def test_scan_task_lifecycle(monkeypatch):
    monkeypatch.setattr(meal_scanning_api.scanner, "scan_meal", lambda base64_url: {
        "detected_foods": ["Chicken"],
        "nutrition_estimate": {"calories": 450, "protein_g": 35},
        "confidence": 0.91,
    })

    meal_scanning_api.perform_background_scan("task-1", "data:image/jpeg;base64,abc")
    resp = client.get("/api/meals/tasks/task-1")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "completed"
    assert data["result"]["detected_foods"] == ["Chicken"]


def test_analyze_meal_for_user_uses_scanner(monkeypatch):
    monkeypatch.setattr(meal_scanning_api.learner, "analyze_patterns", lambda user_id: {"status": "none"})
    monkeypatch.setattr(meal_scanning_api.scanner, "is_good_for_user", lambda meal_data, user_profile: {
        "recommendation": "Good for your goal",
        "is_good_for_user": True,
    })

    resp = client.post(
        "/api/meals/analyze-for-user",
        json={
            "user_profile": {"user_id": "u1", "primary_goal": "weight_loss"},
            "meal_data": {"name": "Chicken Salad"},
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_good_for_user"] is True
    assert "recommendation" in data
