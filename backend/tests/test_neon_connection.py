import os
import pytest
from app.neon_config import get_connection_manager

def test_neon_connection_check():
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url or "sqlite" in database_url:
        pytest.skip("Skipping Neon connection check since we are using local SQLite")

    manager = get_connection_manager()
    # Test connection manager setup
    assert manager is not None
