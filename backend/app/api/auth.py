import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import AuthService, UserRegister, UserLogin, PasswordChange, Token, ForgotPasswordRequest, ResetPasswordRequest
from app.auth import revoke_token, store_reset_token, verify_reset_token, consume_reset_token
from app.clerk_auth import get_current_user_from_clerk as get_current_user
from app.models import EnhancedUser
from app.api_validation import ErrorHandler

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    primary_goal: Optional[str] = None
    femmecare_enabled: Optional[bool] = None

@router.post("/register", response_model=Token)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    auth_service = AuthService(db)
    try:
        user = auth_service.register_user(user_data)
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        tokens = auth_service.login(login_data)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login with email and password"""
    auth_service = AuthService(db)
    try:
        tokens = auth_service.login(login_data)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Login failed: {str(e)}")

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    try:
        tokens = auth_service.refresh_access_token(refresh_token)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Token refresh failed: {str(e)}")

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: EnhancedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    try:
        success = auth_service.change_password(str(current_user.id), password_data)
        if success:
            return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Password change failed: {str(e)}")

@router.get("/me")
def get_current_user_info(
    current_user: EnhancedUser = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "weight_kg": current_user.weight_kg,
        "height_cm": current_user.height_cm,
        "gender": current_user.gender,
        "activity_level": current_user.activity_level,
        "primary_goal": current_user.primary_goal,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
    }


@router.put("/profile")
def update_profile(
    profile: ProfileUpdate,
    current_user: EnhancedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile fields (onboarding data)."""
    update_data = profile.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    for key, value in update_data.items():
        setattr(current_user, key, value)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "weight_kg": current_user.weight_kg,
        "height_cm": current_user.height_cm,
        "gender": current_user.gender,
        "activity_level": current_user.activity_level,
        "primary_goal": current_user.primary_goal,
        "femmecare_enabled": current_user.femmecare_enabled,
    }

@router.post("/logout")
def logout(
    current_user: EnhancedUser = Depends(get_current_user),
    credentials: Optional[str] = Body(None, embed=True),
):
    if credentials:
        revoke_token(credentials)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = db.query(EnhancedUser).filter(EnhancedUser.email == data.email).first()
    if not user:
        return {"message": "If that email exists, a reset token has been generated"}
    token = secrets.token_urlsafe(32)
    store_reset_token(data.email, token)
    return {"message": "Reset token generated (in production, this would be emailed)", "reset_token": token}


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user = db.query(EnhancedUser).filter(EnhancedUser.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_reset_token(data.email, data.token):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    from app.auth import PasswordHasher
    user.hashed_password = PasswordHasher.hash_password(data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    consume_reset_token(data.email)
    return {"message": "Password reset successfully"}
