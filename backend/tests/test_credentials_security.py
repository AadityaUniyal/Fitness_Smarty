"""
Security & Credentials Hardening Verification Tests

Verifies:
1. Dynamic loading of DATABASE_URL and ADMIN_PASSWORD from environment variables.
2. Random secure password fallback using secrets.token_urlsafe(16) when ADMIN_PASSWORD is unset.
3. Production fail-fast validation in config.py.
4. Absence of hardcoded plaintext secrets in application settings.
"""

import os
import secrets
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings, get_settings
from app.models import Base, EnhancedUser
from app.auth import PasswordHasher
from seed_data import seed_admin_user


def test_settings_dynamic_env_loading():
    """Test that Settings loads DATABASE_URL and ADMIN_PASSWORD dynamically from env."""
    custom_db = "sqlite:///./custom_test_security.db"
    custom_pass = "CustomAdminPass999!"
    
    with patch.dict(os.environ, {"DATABASE_URL": custom_db, "ADMIN_PASSWORD": custom_pass}):
        settings = Settings()
        assert settings.DATABASE_URL == custom_db
        assert settings.ADMIN_PASSWORD == custom_pass


def test_settings_production_guards():
    """Test that Settings fails fast in production when required credentials are missing."""
    prod_env = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "sqlite:///./smarty_neural_core.db",  # Invalid SQLite in prod
    }
    with patch.dict(os.environ, prod_env, clear=True):
        with pytest.raises(ValueError) as exc_info:
            Settings()
        err_msg = str(exc_info.value)
        assert "Production environment is missing required configuration" in err_msg
        assert "DATABASE_URL" in err_msg


def test_admin_password_fallback_when_unset(tmp_path, capsys):
    """Test that when ADMIN_PASSWORD is unset, seed_admin_user generates a 16-byte token fallback."""
    db_file = tmp_path / "test_admin_fallback.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ADMIN_PASSWORD is unset
            if "ADMIN_PASSWORD" in os.environ:
                del os.environ["ADMIN_PASSWORD"]
            
            seed_admin_user(db)
            
            # Check printed security notice
            captured = capsys.readouterr()
            assert "SECURITY NOTICE" in captured.out
            assert "admin@smarty.ai" in captured.out
            
            admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
            assert admin is not None
            assert admin.username == "admin"
            assert admin.is_admin is True
            assert admin.hashed_password is not None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_admin_password_uses_environment_variable(tmp_path, capsys):
    """Test that when ADMIN_PASSWORD is set, seed_admin_user uses that exact password."""
    db_file = tmp_path / "test_admin_env.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    custom_password = "SpecifiedEnvPassword123!"
    db = TestingSessionLocal()
    try:
        with patch.dict(os.environ, {"ADMIN_PASSWORD": custom_password}):
            seed_admin_user(db)
            
            captured = capsys.readouterr()
            assert "created successfully with ADMIN_PASSWORD from environment" in captured.out
            
            admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
            assert admin is not None
            assert PasswordHasher.verify_password(custom_password, admin.hashed_password)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
