import os
import pytest
from unittest.mock import patch

def test_production_secret_key_required():
    """Verify that if ENVIRONMENT=production and no JWT_SECRET_KEY or SECRET_KEY is set,
    importing app.auth raises a RuntimeError.
    """
    env_mock = {
        "ENVIRONMENT": "production",
    }
    
    with patch.dict(os.environ, env_mock, clear=True):
        import sys
        import importlib
        
        # Unload app.auth if already imported
        if "app.auth" in sys.modules:
            del sys.modules["app.auth"]
            
        with pytest.raises(RuntimeError) as excinfo:
            importlib.import_module("app.auth")
            
        assert "must be explicitly set" in str(excinfo.value)
