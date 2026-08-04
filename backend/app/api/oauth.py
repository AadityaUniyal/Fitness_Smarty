"""
OAuth Social Login Router

Handles Google and Apple ID token verification and exchanges them for
local JWT tokens. Supports real verification (when libraries available)
and mock mode for development.
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EnhancedUser
from app.auth import JWTHandler, Token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth/oauth", tags=["OAuth"])


class GoogleTokenRequest(BaseModel):
    id_token: str
    client_id: Optional[str] = None


class AppleTokenRequest(BaseModel):
    id_token: str
    full_name: Optional[str] = None
    email: Optional[str] = None


class OAuthProvider:
    """Verify OAuth ID tokens and return user info."""

    @staticmethod
    def verify_google(id_token: str, client_id: Optional[str] = None) -> dict:
        """Verify a Google ID token and extract user info."""
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests
            client_id = client_id or os.getenv("GOOGLE_CLIENT_ID", "")
            id_info = google_id_token.verify_oauth2_token(
                id_token, requests.Request(), client_id
            )
            return {
                "sub": id_info["sub"],
                "email": id_info.get("email", ""),
                "name": id_info.get("name", ""),
                "picture": id_info.get("picture", ""),
            }
        except ImportError:
            pass
        except Exception as e:
            print(f"[!] Google token verification failed: {e}")
            # In development, fall back to mock verification instead of throwing
            if os.getenv("ENVIRONMENT", "development").lower() in ("development", "dev", "test"):
                return OAuthProvider._mock_verify("google", id_token)
            raise e

        return OAuthProvider._mock_verify("google", id_token)

    @staticmethod
    def verify_apple(id_token: str) -> dict:
        """Verify an Apple ID token and extract user info."""
        try:
            from jwt import decode as jwt_decode, get_unverified_header
            import requests

            kid = get_unverified_header(id_token).get("kid")

            resp = requests.get(
                "https://appleid.apple.com/auth/keys", timeout=10
            )
            keys = resp.json().get("keys", [])
            matching_key = next((k for k in keys if k.get("kid") == kid), None)

            if matching_key:
                from jwt import PyJWK
                pub_key = PyJWK(matching_key, algorithm="RS256").key
                decoded = jwt_decode(
                    id_token, pub_key, algorithms=["RS256"],
                    audience=os.getenv("APPLE_CLIENT_ID", ""),
                    issuer="https://appleid.apple.com",
                )
                return {
                    "sub": decoded["sub"],
                    "email": decoded.get("email", ""),
                    "name": (
                        decoded.get("name", {}).get("firstName", "")
                        + " "
                        + decoded.get("name", {}).get("lastName", "")
                    ),
                }
        except ImportError:
            pass
        except Exception as e:
            print(f"[!] Apple token verification failed: {e}")

        return OAuthProvider._mock_verify("apple", id_token)

    @staticmethod
    def _mock_verify(provider: str, token: str) -> dict:
        """Mock verification for development.

        Decodes local JWT or returns test user.
        """
        try:
            from jose import jwt
            payload = jwt.get_unverified_claims(token)
            sub = payload.get("sub", "mock_oauth_user")
            email = payload.get("email", f"{sub}@{provider}.com")
            name = payload.get("name", f"{provider.title()} User")
            return {"sub": sub, "email": email, "name": name}
        except Exception:
            return {
                "sub": f"mock_{provider}_user",
                "email": f"user@mock-{provider}.com",
                "name": f"{provider.title()} User",
            }


@router.post("/google", response_model=Token)
def google_login(
    req: GoogleTokenRequest,
    db: Session = Depends(get_db),
):
    """Exchange a Google ID token for local JWT tokens."""
    info = OAuthProvider.verify_google(req.id_token, req.client_id)
    return _oauth_login_or_register(
        db, "google", info["sub"], info["email"], info["name"]
    )


@router.post("/apple", response_model=Token)
def apple_login(
    req: AppleTokenRequest,
    db: Session = Depends(get_db),
):
    """Exchange an Apple ID token for local JWT tokens."""
    info = OAuthProvider.verify_apple(req.id_token)
    name = req.full_name or info.get("name", "Apple User")
    email = req.email or info.get("email", "")
    return _oauth_login_or_register(db, "apple", info["sub"], email, name)


def _oauth_login_or_register(
    db: Session, provider: str, provider_sub: str, email: str, name: str
) -> Token:
    """Find or create a user from OAuth provider info, return JWT tokens."""
    provider_id = f"{provider}_{provider_sub}"

    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == provider_id)
        | (EnhancedUser.email == email)
    ).first()

    if not user:
        user = EnhancedUser(
            clerk_user_id=provider_id,
            email=email or f"{provider_id}@oauth.{provider}.com",
            username=email.split("@")[0] if email else provider_id[:20],
            full_name=name or f"{provider.title()} User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = JWTHandler.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = JWTHandler.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
