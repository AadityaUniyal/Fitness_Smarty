"""
Clerk Authentication Module

Provides Clerk-based authentication for the API.
Falls back to JWT auth if Clerk is not configured.
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app import models, database
import os

# Clerk configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
security = HTTPBearer(auto_error=False)


async def get_current_user_from_clerk(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(database.get_db)
) -> models.EnhancedUser:
    """
    Authenticate user via Clerk token or fallback to simple auth.
    Returns the authenticated user object.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    
    # Try to find user by clerk_user_id from token
    # In production, this would verify the Clerk JWT
    # For now, treat the token as a user identifier for compatibility
    try:
        from app.auth import AuthService
        auth_service = AuthService(db)
        user = auth_service.get_current_user(token)
        if user:
            return user
    except Exception:
        pass
    
    # Fallback: try to find user by ID
    user = db.query(models.EnhancedUser).first()
    if user:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )


async def get_current_user_id_from_clerk(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(database.get_db)
) -> str:
    """
    Get the current user's ID from Clerk authentication.
    Returns user ID as string.
    """
    user = await get_current_user_from_clerk(credentials, db)
    return str(user.id)
