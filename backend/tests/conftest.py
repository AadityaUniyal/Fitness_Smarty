import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set testing environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test_stable_jwt_secret_key_for_unit_testing"
os.environ["SECRET_KEY"] = "test_stable_jwt_secret_key_for_unit_testing"
os.environ["DATABASE_URL"] = "sqlite:///./test_smarty_temp.db"

@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c
