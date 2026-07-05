import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Force database URL to a local sqlite file for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_smarty_temp.db"

from fastapi.testclient import TestClient
from main import app
from app import models, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

client = TestClient(app)

print("Calling register endpoint...")
r = client.post("/api/auth/register", json={
    "email": "test_api_user@example.com",
    "password": "TestPass123!",
    "name": "Test User"
})

print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
