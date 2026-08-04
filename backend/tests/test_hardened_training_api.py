"""
Unit & Integration Tests for Hardened Admin Training Dashboard (Milestone 4)

Verifies:
1. Server-side admin authorization (401 for unauthenticated, 403 for non-admin users).
2. Async retraining execution via FastAPI BackgroundTasks returning 202 Accepted.
3. Concurrency locking per job returning 409 Conflict when job is already running.
4. All retraining endpoints: recommendation, vision detector, vision classifier, user clustering, forecast lstm, rl dqn, rl qlearning.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from app.database import Base, get_db
from app.models import EnhancedUser
from app.auth import PasswordHasher, JWTHandler
from app.training_api import _training_locks

# Setup SQLite in-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_hardened_training_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def setup_training_db():
    db_path = Path("test_hardened_training_api.db")
    if db_path.exists():
        db_path.unlink()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Admin user
    admin_user = EnhancedUser(
        username="m4_admin",
        email="m4_admin@smarty.ai",
        hashed_password=PasswordHasher.hash_password("AdminPass123!"),
        is_admin=True,
    )
    # Regular (non-admin) user
    regular_user = EnhancedUser(
        username="m4_regular",
        email="m4_regular@smarty.ai",
        hashed_password=PasswordHasher.hash_password("UserPass123!"),
        is_admin=False,
    )

    db.add(admin_user)
    db.add(regular_user)
    db.commit()
    db.refresh(admin_user)
    db.refresh(regular_user)

    yield {
        "admin": admin_user,
        "regular": regular_user,
        "admin_token": JWTHandler.create_access_token({"sub": admin_user.id, "email": admin_user.email}),
        "regular_token": JWTHandler.create_access_token({"sub": regular_user.id, "email": regular_user.email}),
    }

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_db_dependency():
    def _override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def cleanup_locks():
    """Ensure all locks are released before and after each test."""
    for job in [
        "recommendation",
        "vision_detector",
        "vision_classifier",
        "user_clustering",
        "forecast_lstm",
        "rl_dqn",
        "rl_qlearning",
    ]:
        _training_locks.release(job)
    yield
    for job in [
        "recommendation",
        "vision_detector",
        "vision_classifier",
        "user_clustering",
        "forecast_lstm",
        "rl_dqn",
        "rl_qlearning",
    ]:
        _training_locks.release(job)


# ─── Auth Verification Tests (401 / 403) ───────────────────────────────────

RETRAINING_ENDPOINTS = [
    ("/api/training/recommendation/train", {"epochs": 5, "use_db": False}),
    ("/api/training/vision/train-detector", {"epochs": 5}),
    ("/api/training/vision/train-classifier", {"epochs": 5}),
    ("/api/training/cluster/users", {"n_clusters": 3}),
    ("/api/training/forecast/train-lstm", {"epochs": 5}),
    ("/api/training/rl/train-dqn", {"episodes": 10}),
    ("/api/training/rl/train-qlearning", {"episodes": 10}),
]


@pytest.mark.parametrize("endpoint,payload", RETRAINING_ENDPOINTS)
def test_unauthorized_access_returns_401(client, endpoint, payload):
    """Requests without authorization header must be rejected with 401 Unauthorized."""
    response = client.post(endpoint, json=payload)
    assert response.status_code == 401, f"Expected 401 for {endpoint}, got {response.status_code}"


@pytest.mark.parametrize("endpoint,payload", RETRAINING_ENDPOINTS)
def test_non_admin_access_returns_403(client, setup_training_db, endpoint, payload):
    """Requests from non-admin users must be rejected with 403 Forbidden."""
    token = setup_training_db["regular_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(endpoint, json=payload, headers=headers)
    assert response.status_code == 403, f"Expected 403 for {endpoint}, got {response.status_code}"


def test_status_endpoint_admin_auth(client, setup_training_db):
    """GET /api/training/status requires admin auth."""
    # Unauthenticated -> 401
    res1 = client.get("/api/training/status")
    assert res1.status_code == 401

    # Non-admin -> 403
    reg_headers = {"Authorization": f"Bearer {setup_training_db['regular_token']}"}
    res2 = client.get("/api/training/status", headers=reg_headers)
    assert res2.status_code == 403

    # Admin -> 200
    admin_headers = {"Authorization": f"Bearer {setup_training_db['admin_token']}"}
    res3 = client.get("/api/training/status", headers=admin_headers)
    assert res3.status_code == 200
    data = res3.json()
    assert "datasets" in data
    assert "trained_models" in data


# ─── Async Retraining & 202 Accepted Tests ─────────────────────────────────

@pytest.mark.parametrize("endpoint,payload,job_name", [
    ("/api/training/recommendation/train", {"epochs": 1}, "recommendation"),
    ("/api/training/vision/train-detector", {"epochs": 1}, "vision_detector"),
    ("/api/training/vision/train-classifier", {"epochs": 1}, "vision_classifier"),
    ("/api/training/cluster/users", {"n_clusters": 2}, "user_clustering"),
    ("/api/training/forecast/train-lstm", {"epochs": 1}, "forecast_lstm"),
    ("/api/training/rl/train-dqn", {"episodes": 2}, "rl_dqn"),
    ("/api/training/rl/train-qlearning", {"episodes": 2}, "rl_qlearning"),
])
def test_authorized_retraining_trigger_returns_202(
    client, setup_training_db, endpoint, payload, job_name
):
    """Authorized admin request returns immediate 202 Accepted and launches background task."""
    headers = {"Authorization": f"Bearer {setup_training_db['admin_token']}"}

    # Patch heavy underlying training routines so test executes instantly
    with patch("app.training.train_neural_model.NeuralModelTrainer.train"), \
         patch("app.training.train_food_detector.FoodDetectorTrainer.train"), \
         patch("app.training.train_health_classifier.HealthClassifierTrainer.train"), \
         patch("app.training.user_clustering.UserClusterEngine.fit"), \
         patch("app.training.train_lstm.LSTMTrainer.train"), \
         patch("app.training.train_dqn.DQNTrainer.train"), \
         patch("app.training.train_qlearning.QLearningTrainer.train"):

        response = client.post(endpoint, json=payload, headers=headers)
        assert response.status_code == 202, f"Expected 202 for {endpoint}, got {response.status_code}"
        data = response.json()
        assert data["status"] == "accepted"
        assert data["job"] == job_name


# ─── Concurrency Locking (409 Conflict) Tests ──────────────────────────────

@pytest.mark.parametrize("endpoint,payload,job_name", [
    ("/api/training/recommendation/train", {"epochs": 1}, "recommendation"),
    ("/api/training/vision/train-detector", {"epochs": 1}, "vision_detector"),
    ("/api/training/vision/train-classifier", {"epochs": 1}, "vision_classifier"),
    ("/api/training/cluster/users", {"n_clusters": 2}, "user_clustering"),
    ("/api/training/forecast/train-lstm", {"epochs": 1}, "forecast_lstm"),
    ("/api/training/rl/train-dqn", {"episodes": 2}, "rl_dqn"),
    ("/api/training/rl/train-qlearning", {"episodes": 2}, "rl_qlearning"),
])
def test_concurrent_retraining_returns_409_conflict(
    client, setup_training_db, endpoint, payload, job_name
):
    """If a job is already in progress (lock held), returning 409 Conflict is required."""
    headers = {"Authorization": f"Bearer {setup_training_db['admin_token']}"}

    # Simulate lock being held by an ongoing training run
    acquired = _training_locks.try_acquire(job_name)
    assert acquired is True, f"Failed to acquire test lock for {job_name}"

    try:
        # Request while lock is held -> 409 Conflict
        response = client.post(endpoint, json=payload, headers=headers)
        assert response.status_code == 409, f"Expected 409 for locked {endpoint}, got {response.status_code}"
        data = response.json()
        assert "already in progress" in data["detail"]
    finally:
        _training_locks.release(job_name)

    # After lock release, subsequent call must succeed -> 202
    with patch("app.training.train_neural_model.NeuralModelTrainer.train"), \
         patch("app.training.train_food_detector.FoodDetectorTrainer.train"), \
         patch("app.training.train_health_classifier.HealthClassifierTrainer.train"), \
         patch("app.training.user_clustering.UserClusterEngine.fit"), \
         patch("app.training.train_lstm.LSTMTrainer.train"), \
         patch("app.training.train_dqn.DQNTrainer.train"), \
         patch("app.training.train_qlearning.QLearningTrainer.train"):

        subsequent_response = client.post(endpoint, json=payload, headers=headers)
        assert subsequent_response.status_code == 202
