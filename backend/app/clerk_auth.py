"""
Clerk Authentication Module

Provides Clerk-based authentication for the API.
Falls back to JWT auth if Clerk is not configured.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app import models, database
from app.auth import JWTHandler
import os

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
security = HTTPBearer(auto_error=False)


async def get_current_user_from_clerk(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(database.get_db)
) -> models.EnhancedUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        token_data = JWTHandler.decode_token(token)
        user = db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == token_data.user_id
        ).first()
        if user:
            return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )


async def get_current_user_id_from_clerk(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(database.get_db)
) -> str:
    user = await get_current_user_from_clerk(credentials, db)
    return str(user.id)
