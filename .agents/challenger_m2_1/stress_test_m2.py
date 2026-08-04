import os
import sys
import io
import subprocess
from unittest.mock import patch
from contextlib import redirect_stdout
import pytest

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.join(repo_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

test_db_path = os.path.join(backend_dir, "test_m2_stress.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from app.database import engine, SessionLocal
from app.models import Base, EnhancedUser
from app.auth import PasswordHasher
from app.config import Settings
from seed_data import seed_admin_user

def reset_db():
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_special_chars_password():
    print("\n--- STRESS TEST 1: Password with special characters & symbols ---")
    reset_db()
    special_pass = "P@ssw0rd!# $ % ^ & * () _ + - = ~ ` { } [ ] : ; < > , . ? / | \\"
    os.environ["ADMIN_PASSWORD"] = special_pass
    seed_admin_user()
    
    db = SessionLocal()
    admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
    assert admin is not None
    assert PasswordHasher.verify_password(special_pass, admin.hashed_password)
    assert not PasswordHasher.verify_password("P@ssw0rd!", admin.hashed_password)
    db.close()
    print("PASS: Special characters password handled correctly!")

def test_empty_string_password():
    print("\n--- STRESS TEST 2: Empty string vs spaces-only ADMIN_PASSWORD ---")
    reset_db()
    os.environ["ADMIN_PASSWORD"] = ""
    f = io.StringIO()
    with redirect_stdout(f):
        seed_admin_user()
    output = f.getvalue()
    assert "SECURITY NOTICE: No ADMIN_PASSWORD environment variable specified." in output
    print("PASS: Empty string ADMIN_PASSWORD triggers secure random fallback.")

def test_very_long_password():
    print("\n--- STRESS TEST 3: Very long ADMIN_PASSWORD (>72 chars bcrypt boundary) ---")
    reset_db()
    long_pass = "A" * 500
    os.environ["ADMIN_PASSWORD"] = long_pass
    seed_admin_user()
    
    db = SessionLocal()
    admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
    assert admin is not None
    is_valid = PasswordHasher.verify_password(long_pass, admin.hashed_password)
    db.close()
    print(f"PASS: 500-char long password processed without crashing (verify_password={is_valid}).")

def test_prod_env_fail_fast():
    print("\n--- STRESS TEST 4: Production Fail-Fast Validation ---")
    # Test missing JWT_SECRET_KEY
    env_missing_jwt = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "FEMME_SECRET_KEY": "femme_secret_key_123",
        "CORS_ORIGINS": "https://app.smarty.ai",
    }
    with patch.dict(os.environ, env_missing_jwt, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings()
        assert "JWT_SECRET_KEY or SECRET_KEY" in str(exc.value)

    # Test SQLite in production
    env_sqlite = {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": "jwt_secret_key_123",
        "FEMME_SECRET_KEY": "femme_secret_key_123",
        "DATABASE_URL": "sqlite:///./prod.db",
        "CORS_ORIGINS": "https://app.smarty.ai",
    }
    with patch.dict(os.environ, env_sqlite, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings()
        assert "DATABASE_URL (must be a PostgreSQL connection string" in str(exc.value)

    # Test Wildcard CORS in production
    env_cors = {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": "jwt_secret_key_123",
        "FEMME_SECRET_KEY": "femme_secret_key_123",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
        "CORS_ORIGINS": "*",
    }
    with patch.dict(os.environ, env_cors, clear=True):
        with pytest.raises(ValueError) as exc:
            Settings()
        assert "CORS_ORIGINS (wildcard or empty origins not allowed" in str(exc.value)

    print("PASS: All production fail-fast settings validation guards verified!")

if __name__ == "__main__":
    try:
        test_special_chars_password()
        test_empty_string_password()
        test_very_long_password()
        test_prod_env_fail_fast()
        print("\n================ ALL ADVERSARIAL STRESS TESTS PASSED ================")
    except Exception as e:
        print(f"\nSTRESS TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
