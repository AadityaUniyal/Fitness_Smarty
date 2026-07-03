"""
Comprehensive API tests for all new backend endpoints.
Runs via TestClient (in-process) for speed under pytest.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from main import app
from app import models, database

# Ensure tables are created
models.Base.metadata.create_all(bind=database.engine)

client = TestClient(app)
API_BASE = ""  # TestClient uses relative paths

TEST_EMAIL = "test_api_user@example.com"
TEST_PASSWORD = "TestPass123!"
ACCESS_TOKEN = None
USER_ID = None


def api_request(method, path, json_data=None):
    headers = {}
    if ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
    fn = getattr(client, method)
    kwargs = {"headers": headers}
    if json_data is not None:
        kwargs["json"] = json_data
    return fn(path, **kwargs)


def setup_module():
    global ACCESS_TOKEN, USER_ID
    # Try login first
    r = api_request("post", "/api/auth/login", {
        "email": TEST_EMAIL, "password": TEST_PASSWORD,
    })
    if r.status_code == 200:
        ACCESS_TOKEN = r.json().get("access_token")
    else:
        r = api_request("post", "/api/auth/register", {
            "email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User",
        })
        if r.status_code == 200:
            ACCESS_TOKEN = r.json().get("access_token")
    if ACCESS_TOKEN:
        r = api_request("get", "/api/auth/me")
        if r.status_code == 200:
            USER_ID = r.json().get("id")
    return ACCESS_TOKEN is not None


# ============= SOCIAL FEED TESTS =============

def test_social_create_post():
    r = api_request("post", "/api/social/posts", {
        "text": "Test workout post!",
        "post_type": "workout",
        "workout_data": {"type": "Running", "duration": 30, "calories": 300},
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["text"] == "Test workout post!"
    assert data["post_type"] == "workout"
    assert data["workout_data"]["calories"] == 300
    return data["id"]


def test_social_get_feed():
    r = api_request("get", "/api/social/posts?page=1&page_size=10")
    assert r.status_code == 200
    data = r.json()
    assert "posts" in data
    assert "total_count" in data
    assert len(data["posts"]) >= 1


def test_social_like_post():
    post_id = test_social_create_post()
    r = api_request("post", f"/api/social/posts/{post_id}/like")
    assert r.status_code == 200
    assert r.json()["liked"] is True
    # Toggle off
    r = api_request("post", f"/api/social/posts/{post_id}/like")
    assert r.json()["liked"] is False


def test_social_comment():
    post_id = test_social_create_post()
    r = api_request("post", f"/api/social/posts/{post_id}/comments", {"text": "Great work!"})
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["text"] == "Great work!"
    # Get comments
    r = api_request("get", f"/api/social/posts/{post_id}/comments")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_social_follow():
    # Get other users
    r = api_request("get", "/api/social/users")
    assert r.status_code == 200
    users = r.json()
    if len(users) > 0:
        target_id = users[0]["id"]
        r = api_request("post", f"/api/social/follow/{target_id}")
        assert r.status_code == 200
        assert r.json()["following"] is True
        # Get following list
        r = api_request("get", "/api/social/following")
        assert r.status_code == 200
        assert any(u["id"] == target_id for u in r.json())
        # Unfollow
        r = api_request("post", f"/api/social/follow/{target_id}")
        assert r.json()["following"] is False


def test_social_delete_post():
    post_id = test_social_create_post()
    r = api_request("delete", f"/api/social/posts/{post_id}")
    assert r.status_code == 204


# ============= ACTIVITY TRACKER TESTS =============

def test_activity_create_session():
    r = api_request("post", "/api/activities/sessions", {
        "activity_type": "running",
        "duration_seconds": 1860,
        "distance_km": 5.2,
        "calories": 420,
        "avg_pace": "5:58",
        "avg_speed": 10.1,
        "label": "Morning run",
        "route_points": [
            {"lat": 51.5074, "lng": -0.1278},
            {"lat": 51.5075, "lng": -0.1276},
            {"lat": 51.5077, "lng": -0.1273},
        ],
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["activity_type"] == "running"
    assert data["distance_km"] == 5.2
    assert len(data["route_points"]) == 3
    return data["id"]


def test_activity_list_sessions():
    test_activity_create_session()
    r = api_request("get", "/api/activities/sessions?page=1&page_size=10")
    assert r.status_code == 200
    data = r.json()
    assert data["total_count"] >= 1
    assert len(data["sessions"]) >= 1


def test_activity_get_session():
    session_id = test_activity_create_session()
    r = api_request("get", f"/api/activities/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["id"] == session_id


def test_activity_delete_session():
    session_id = test_activity_create_session()
    r = api_request("delete", f"/api/activities/sessions/{session_id}")
    assert r.status_code == 204


# ============= MEAL PLANNER TESTS =============

def test_meal_plan_create():
    r = api_request("post", "/api/meal-plans/plans", {
        "week_start": "2026-05-25",
        "entries": [
            {"day_of_week": 0, "meal_slot": "breakfast", "food_name": "Oatmeal", "calories": 350, "protein": 12, "carbs": 58, "fats": 6},
            {"day_of_week": 0, "meal_slot": "lunch", "food_name": "Chicken Salad", "calories": 420, "protein": 35, "carbs": 12, "fats": 18},
            {"day_of_week": 1, "meal_slot": "dinner", "food_name": "Salmon & Rice", "calories": 520, "protein": 42, "carbs": 50, "fats": 16},
        ],
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert len(data["entries"]) == 3
    return data["id"]


def test_meal_plan_list():
    test_meal_plan_create()
    r = api_request("get", "/api/meal-plans/plans")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_meal_plan_get():
    plan_id = test_meal_plan_create()
    r = api_request("get", f"/api/meal-plans/plans/{plan_id}")
    assert r.status_code == 200
    assert r.json()["id"] == plan_id


def test_meal_plan_delete():
    plan_id = test_meal_plan_create()
    r = api_request("delete", f"/api/meal-plans/plans/{plan_id}")
    assert r.status_code == 204


def test_meal_plan_generate():
    r = api_request("post", "/api/meal-plans/generate", {
        "week_start": "2026-06-01",
        "daily_calories": 2000,
        "goal": "muscle_gain",
        "dietary_preferences": ["high_protein"],
        "allergies": [],
        "exclude_foods": [],
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert len(data["entries"]) == 28, f"Expected 28 entries, got {len(data['entries'])}"
    assert data["entries"][0]["day_of_week"] == 0
    assert data["entries"][0]["meal_slot"] in ("breakfast", "lunch", "dinner", "snack")
    assert data["entries"][0]["calories"] > 0


# ============= FORM COACH TESTS =============

def test_form_coach_create():
    r = api_request("post", "/api/form-coach/sessions", {
        "exercise": "squat",
        "duration_seconds": 300,
        "rep_count": 15,
        "feedback_summary": "Good depth, minor knee cave",
        "feedback_logs": [
            {"message": "Go deeper - bend knees more", "feedback_type": "bad"},
            {"message": "Good squat depth!", "feedback_type": "good"},
        ],
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["exercise"] == "squat"
    assert len(data["feedback_logs"]) == 2
    return data["id"]


def test_form_coach_list():
    test_form_coach_create()
    r = api_request("get", "/api/form-coach/sessions")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_form_coach_get():
    session_id = test_form_coach_create()
    r = api_request("get", f"/api/form-coach/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["id"] == session_id


# ============= WEARABLE INTEGRATION TESTS =============

def test_wearable_connect():
    r = api_request("post", "/api/wearables/connections", {
        "device_id": "apple_health",
        "device_name": "Apple Health",
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["device_id"] == "apple_health"
    assert data["connected"] is True
    return data["id"]


def test_wearable_list():
    test_wearable_connect()
    r = api_request("get", "/api/wearables/connections")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_wearable_sync():
    conn_id = test_wearable_connect()
    r = api_request("post", f"/api/wearables/connections/{conn_id}/sync", [
        {"metric_type": "steps", "value": 8432, "unit": "steps"},
        {"metric_type": "heart_rate", "value": 72, "unit": "bpm"},
        {"metric_type": "sleep", "value": 7.5, "unit": "hrs"},
    ])
    assert r.status_code == 200
    assert r.json()["synced"] == 3


def test_wearable_aggregated():
    conn_id = test_wearable_connect()
    api_request("post", f"/api/wearables/connections/{conn_id}/sync", [
        {"metric_type": "steps", "value": 7500, "unit": "steps"},
        {"metric_type": "heart_rate", "value": 68, "unit": "bpm"},
    ])
    r = api_request("get", "/api/wearables/metrics/aggregated?days=7")
    assert r.status_code == 200
    data = r.json()
    assert "metrics" in data
    assert data["days"] == 7


def test_wearable_disconnect():
    conn_id = test_wearable_connect()
    r = api_request("delete", f"/api/wearables/connections/{conn_id}")
    assert r.status_code == 204


# ============= REMINDER TESTS =============

def test_reminder_create():
    r = api_request("post", "/api/reminders/reminders", {
        "label": "Morning Workout",
        "description": "Time to train!",
        "time": "07:00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "enabled": True,
        "icon": "strength",
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["label"] == "Morning Workout"
    assert data["time"] == "07:00"
    return data["id"]


def test_reminder_list():
    test_reminder_create()
    r = api_request("get", "/api/reminders/reminders")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_reminder_update():
    reminder_id = test_reminder_create()
    r = api_request("put", f"/api/reminders/reminders/{reminder_id}", {
        "enabled": False, "time": "08:00",
    })
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    assert r.json()["time"] == "08:00"


def test_reminder_delete():
    reminder_id = test_reminder_create()
    r = api_request("delete", f"/api/reminders/reminders/{reminder_id}")
    assert r.status_code == 204


# ============= NOTIFICATION TESTS =============

def test_notification_list():
    r = api_request("get", "/api/reminders/notifications")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_notification_mark_read():
    r = api_request("get", "/api/reminders/notifications")
    notifs = r.json()
    if len(notifs) > 0:
        nid = notifs[0]["id"]
        r = api_request("post", f"/api/reminders/notifications/{nid}/read")
        assert r.status_code == 200
        assert r.json()["read"] is True


def test_notification_mark_all_read():
    r = api_request("post", "/api/reminders/notifications/read-all")
    assert r.status_code == 200
    assert r.json()["read_all"] is True
