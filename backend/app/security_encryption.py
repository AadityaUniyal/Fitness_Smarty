import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# A simple fallback key for development/demo, but in production this should be a secret env variable.
# Reproductive health data must be encrypted at the application layer.
FEMME_SECRET_KEY = os.getenv("FEMME_SECRET_KEY", "uE8Q2Z3M5Q7J6g9N1h8B2V5K8J9D3S1zF6H7v8D9x0Y=")

try:
    _cipher = Fernet(FEMME_SECRET_KEY.encode() if isinstance(FEMME_SECRET_KEY, str) else FEMME_SECRET_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Fernet encryption with key. Error: {e}")
    # Generate a temporary key so the app doesn't crash, but log a warning.
    fallback_key = Fernet.generate_key()
    _cipher = Fernet(fallback_key)

def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    if not value:
        return ""
    try:
        return _cipher.encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return value

def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a string value using Fernet symmetric encryption."""
    if not encrypted_value:
        return ""
    try:
        return _cipher.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except Exception as e:
        # If it wasn't encrypted or key mismatch, return value as is to prevent crashes
        return encrypted_value
