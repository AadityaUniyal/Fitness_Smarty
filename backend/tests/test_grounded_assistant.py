import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup in-memory SQLite for assistant tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_assistant.db"
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

@pytest.fixture(autouse=True)
def force_dependency_overrides():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_grounded_faq_explainer_routing():
    # Test checking the explanation trace returns the rules trace text successfully
    # When entitlement exists, it returns access granted
    resp = client.post("/api/extensions/grant-entitlement?user_id=user-1&feature_code=RULE_TRACE&granted=true")
    assert resp.status_code == 200

    resp = client.get("/api/extensions/premium-explain/user-1")
    assert resp.status_code == 200
    assert "detailed_trace" in resp.json()
