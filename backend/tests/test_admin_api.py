import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import EnhancedUser, WorkoutLog, MealLog
from app.auth import PasswordHasher
from main import app

# Setup local SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test admin
    admin = EnhancedUser(
        username="test_admin",
        email="test_admin@smarty.ai",
        hashed_password=PasswordHasher.hash_password("AdminPass123!"),
        is_admin=True
    )
    # Create test normal user
    regular = EnhancedUser(
        username="test_regular",
        email="test_regular@smarty.ai",
        hashed_password=PasswordHasher.hash_password("UserPass123!"),
        is_admin=False,
        age=30,
        weight_kg=75.0,
        height_cm=180
    )
    db.add(admin)
    db.add(regular)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def force_dependency_overrides():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="module")
def client(setup_db):
    with TestClient(app) as c:
        yield c

def test_admin_dashboard_stats(client):
    # Log in as admin
    login_res = client.post("/api/auth/login", json={
        "email": "test_admin@smarty.ai",
        "password": "AdminPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get dashboard stats
    stats_res = client.get("/api/admin/stats", headers=headers)
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["total_users"] >= 2
    assert "active_users_7d" in data
    assert "gemini_api_status" in data

def test_admin_list_users(client):
    login_res = client.post("/api/auth/login", json={
        "email": "test_admin@smarty.ai",
        "password": "AdminPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    list_res = client.get("/api/admin/users", headers=headers)
    assert list_res.status_code == 200
    users = list_res.json()
    assert len(users) >= 2
    assert any(u["email"] == "test_regular@smarty.ai" for u in users)

def test_regular_user_forbidden(client):
    # Log in as regular user
    login_res = client.post("/api/auth/login", json={
        "email": "test_regular@smarty.ai",
        "password": "UserPass123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Attempt to request stats
    stats_res = client.get("/api/admin/stats", headers=headers)
    assert stats_res.status_code == 403
    assert stats_res.json()["detail"] == "Admin privileges required"

def test_update_and_delete_user(client):
    login_res = client.post("/api/auth/login", json={
        "email": "test_admin@smarty.ai",
        "password": "AdminPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get regular user ID
    list_res = client.get("/api/admin/users", headers=headers)
    regular_user = next(u for u in list_res.json() if u["email"] == "test_regular@smarty.ai")
    user_id = regular_user["id"]
    
    # Update regular user metrics
    update_res = client.put(f"/api/admin/users/{user_id}", headers=headers, json={
        "age": 31,
        "weight_kg": 76.5
    })
    assert update_res.status_code == 200
    assert update_res.json()["success"] is True
    
    # Delete regular user
    delete_res = client.delete(f"/api/admin/users/{user_id}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True
