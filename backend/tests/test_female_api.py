import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_female_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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


def seed_user_and_cycle():
    db = TestingSessionLocal()
    user = models.EnhancedUser(
        id=1,
        clerk_user_id="1",
        username="femme_user",
        email="femme@example.com",
        gender="Female",
        femmecare_enabled=True,
    )
    db.add(user)
    db.add(models.MenstrualCycleLog(user_id="1", start_date=datetime.utcnow(), cycle_length_days=28))
    db.commit()
    db.close()


def test_cycle_phase_returns_phase_and_advice():
    seed_user_and_cycle()
    resp = client.get("/api/female/cycle-phase/1")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["phase"] in {"Menstrual", "Follicular", "Ovulatory", "Luteal"}
    assert "advice" in data
    assert "recommended_exercises" in data


def test_toggle_femmecare_updates_user_state():
    db = TestingSessionLocal()
    user = models.EnhancedUser(
        id=2,
        clerk_user_id="2",
        username="toggle_user",
        email="toggle@example.com",
        gender="Female",
        femmecare_enabled=False,
    )
    db.add(user)
    db.commit()
    db.close()

    resp = client.post("/api/female/update-settings/2?femmecare_enabled=true")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["settings"]["femmecare_enabled"] is True
