import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.auth import JWTHandler, PasswordHasher
from app.database import Base, get_db
from app.models import EnhancedUser, FoodTrainingSample

pytest.importorskip("torch")


def test_db_training_trigger():
    db_path = Path("test_db_training_trigger.db")
    if db_path.exists():
        db_path.unlink()
    engine = create_engine(
        "sqlite:///./test_db_training_trigger.db",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        db = TestingSessionLocal()
        admin = EnhancedUser(
            username="m4_admin",
            email="m4_admin@smarty.ai",
            hashed_password=PasswordHasher.hash_password("AdminPass123!"),
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        token = JWTHandler.create_access_token({"sub": admin.id, "email": admin.email})

        db.query(FoodTrainingSample).filter_by(verified=True).delete()
        db.add_all(
            [
                FoodTrainingSample(
                    label="Chicken Breast",
                    calories=150.0,
                    protein=30.0,
                    carbs=0.0,
                    fats=3.0,
                    verified=True,
                    source="verified_upload",
                ),
                FoodTrainingSample(
                    label="Donut",
                    calories=700.0,
                    protein=2.0,
                    carbs=50.0,
                    fats=30.0,
                    verified=True,
                    source="verified_upload",
                ),
                FoodTrainingSample(
                    label="Salad",
                    calories=100.0,
                    protein=2.0,
                    carbs=10.0,
                    fats=5.0,
                    verified=True,
                    source="verified_upload",
                ),
                FoodTrainingSample(
                    label="Beef Patties",
                    calories=400.0,
                    protein=25.0,
                    carbs=0.0,
                    fats=20.0,
                    verified=True,
                    source="verified_upload",
                ),
            ]
        )
        db.commit()
        db.close()

        with TestClient(app) as client:
            response = client.post(
                "/api/training/recommendation/train?use_db=true&epochs=1",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 202
    finally:
        app.dependency_overrides.pop(get_db, None)
