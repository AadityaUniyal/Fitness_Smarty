import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.meal_scanning_api import router, scan_tasks
import io


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_async_scan_job_flow(client):
    # Prepare dummy photo bytes
    dummy_file = io.BytesIO(b"dummy image bytes")
    
    # 1. Trigger async scan
    response = client.post(
        "/api/meals/scan",
        files={"file": ("test.jpg", dummy_file, "image/jpeg")}
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert "task_id" in json_data
    assert json_data["status"] == "pending"
    
    task_id = json_data["task_id"]
    
    # 2. Check task status polling
    poll_response = client.get(f"/api/meals/tasks/{task_id}")
    assert poll_response.status_code == 200
    poll_data = poll_response.json()
    assert poll_data["status"] in ["pending", "processing", "completed", "failed"]
