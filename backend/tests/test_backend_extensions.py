import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database import Base, get_db
from app.models import EnhancedUser
from app.nlp_parser import parse_meal_text
from app.wearable_importer import import_wearable_csv

# Setup in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_extensions.db"
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
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Seed a dummy user for role & GDPR checks
    db = TestingSessionLocal()
    dummy = EnhancedUser(
        clerk_user_id="user_test_ext",
        username="Tester",
        email="test@smarty.com",
        age=25,
        gender="Male",
        primary_goal="Gain Muscle",
        weight_kg=75.0,
        height_cm=180.0
    )
    db.add(dummy)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_nlp_parsing_fallback():
    db = TestingSessionLocal()
    # Test unrecognized items parser fallback
    res = parse_meal_text("200g synthetic protein powder", db)
    assert len(res) == 1
    assert res[0]["matched"] is False
    assert res[0]["weight_g"] == 200.0
    assert res[0]["calories"] == 240.0 # 1.2 * 200

def test_barcode_lookup_api():
    # Test valid mock lookup
    response = client.get("/api/extensions/barcode/012000000133")
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["name"] == "Pepsi Zero Sugar"

    # Test unknown fallback lookup
    response = client.get("/api/extensions/barcode/999999999999")
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False

def test_scheduler_api():
    response = client.post("/api/extensions/schedule-reminder/user_test_ext?interval_seconds=10")
    assert response.status_code == 200
    assert response.json()["ok"] is True

    response = client.delete("/api/extensions/cancel-reminder/user_test_ext")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_gdpr_export_and_delete_api():
    # Test export
    response = client.get("/api/extensions/export/user_test_ext")
    assert response.status_code == 200
    data = response.json()
    assert data["user_profile"]["email"] == "test@smarty.com"

    # Test delete
    response = client.delete("/api/extensions/delete/user_test_ext")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_wearable_importer_parser():
    csv_data = """date,steps,calories burned,weight (kg)
2026-07-02T10:00:00Z,10000,450.0,78.5
"""
    records = import_wearable_csv(csv_data)
    assert len(records) == 1
    assert records[0]["steps"] == 10000
    assert records[0]["calories_burned"] == 450.0
    assert records[0]["weight_kg"] == 78.5

def test_streak_calculations_and_freezes():
    # 1. Log activity for a user
    resp = client.post("/api/extensions/log-activity/user_streak_test?event_type=meal_log&offset_minutes=60")
    assert resp.status_code == 200

    # 2. Get streak count
    resp = client.get("/api/extensions/streak/user_streak_test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_streak"] == 1
    assert data["freezes_remaining"] == 3

def test_premium_entitlements_gating():
    # 1. Accessing gated premium details without subscription entitlement should return 402 Payment Required
    resp = client.get("/api/extensions/premium-explain/user_ext_premium")
    assert resp.status_code == 402

    # 2. Grant subscription entitlement
    resp = client.post("/api/extensions/grant-entitlement?user_id=user_ext_premium&feature_code=RULE_TRACE&granted=true")
    assert resp.status_code == 200

    # 3. Accessing gated premium details now succeeds
    resp = client.get("/api/extensions/premium-explain/user_ext_premium")
    assert resp.status_code == 200
    assert resp.json()["status"] == "access_granted"

def test_product_event_tracking_and_funnel():
    # 1. Track onboarding milestones
    client.post("/api/extensions/track-event?user_id=user_f&event_name=onboarding_start")
    client.post("/api/extensions/track-event?user_id=user_f&event_name=onboarding_profile_save")
    client.post("/api/extensions/track-event?user_id=user_f&event_name=onboarding_complete")

    # 2. Get funnel stats
    resp = client.get("/api/extensions/onboarding-funnel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["funnel_milestones"]["1_start"] >= 1
    assert data["conversion_rates"]["total_completion_pct"] > 0

def test_feature_flags_rollout():
    # Test deterministic hash rollout value
    resp = client.get("/api/extensions/feature-flag/new_recommender?user_id=user_a&rollout_pct=100")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True

    resp = client.get("/api/extensions/feature-flag/new_recommender?user_id=user_a&rollout_pct=0")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

def test_web_push_registration():
    sub_payload = {"endpoint": "https://fcm.googleapis.com/fcm/send/fake", "keys": {"p256dh": "key", "auth": "auth"}}
    
    # 1. Register subscription
    resp = client.post("/api/extensions/register-push-subscription/user_push_test", json=sub_payload)
    assert resp.status_code == 200
    assert resp.json()["registered"] is True

    # 2. Trigger push notification
    resp = client.post("/api/extensions/trigger-push-notification/user_push_test?title=Hi&body=Test")
    assert resp.status_code == 200
    assert resp.json()["dispatched"] is True

def test_prometheus_metrics_endpoint():
    resp = client.get("/api/extensions/metrics")
    assert resp.status_code == 200
    assert "smarty_db_users_total" in resp.text




