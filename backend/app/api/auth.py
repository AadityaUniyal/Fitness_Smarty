import secrets
import random
import string
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api_validation import ErrorHandler
from app.auth import (
    AuthService,
    ForgotPasswordRequest,
    PasswordChange,
    ResetPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
    consume_reset_token,
    revoke_token,
    store_reset_token,
    verify_reset_token,
)
from app.clerk_auth import get_current_user_from_clerk as get_current_user
from app.database import get_db
from app.models import EnhancedUser

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
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None


@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account"""
    auth_service = AuthService(db)
    try:
        user = auth_service.register_user(user_data)

        # Send welcome email asynchronously
        try:
            from app.email_service import send_welcome_email

            send_welcome_email(
                user_email=user.email,
                user_name=user.full_name or user_data.email.split("@")[0],
                gender=user.gender or "male",
            )
        except Exception:
            # We do not block registration on email sending failure
            pass

        login_data = UserLogin(
            email=user_data.email, password=user_data.password
        )
        tokens = auth_service.login(login_data)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Registration failed: {str(e)}")


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
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
    refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)
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
    db: Session = Depends(get_db),
):
    """Change user password"""
    auth_service = AuthService(db)
    try:
        success = auth_service.change_password(
            str(current_user.id), password_data
        )
        if success:
            return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Password change failed: {str(e)}")


@router.get("/me")
def get_current_user_info(
    current_user: EnhancedUser = Depends(get_current_user),
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
        "created_at": (
            current_user.created_at.isoformat()
            if current_user.created_at
            else None
        ),
        "updated_at": (
            current_user.updated_at.isoformat()
            if current_user.updated_at
            else None
        ),
    }


@router.put("/profile")
def update_profile(
    profile: ProfileUpdate,
    current_user: EnhancedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile fields (onboarding data)."""
    update_data = profile.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Extract UserProfile fields
    dietary_restrictions = update_data.pop("dietary_restrictions", None)
    allergies = update_data.pop("allergies", None)

    for key, value in update_data.items():
        setattr(current_user, key, value)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    # Sync UserProfile table
    from app.user_profile_service import (
        UserProfileCreate,
        UserProfileService,
        UserProfileUpdate,
    )

    profile_service = UserProfileService(db)
    user_prof = profile_service.get_user_profile(str(current_user.id))
    if not user_prof:
        profile_create = UserProfileCreate(
            age=current_user.age,
            weight_kg=current_user.weight_kg,
            height_cm=(
                int(current_user.height_cm)
                if current_user.height_cm
                else None
            ),
            activity_level=current_user.activity_level or "moderate",
            primary_goal=current_user.primary_goal or "maintenance",
            dietary_restrictions=dietary_restrictions or [],
            allergies=allergies or [],
        )
        profile_service.create_user_profile(
            str(current_user.id), profile_create
        )
    else:
        profile_update = UserProfileUpdate(
            age=current_user.age,
            weight_kg=current_user.weight_kg,
            height_cm=(
                int(current_user.height_cm)
                if current_user.height_cm
                else None
            ),
            activity_level=current_user.activity_level,
            primary_goal=current_user.primary_goal,
            dietary_restrictions=dietary_restrictions,
            allergies=allergies,
        )
        profile_service.update_user_profile(
            str(current_user.id), profile_update
        )

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
        "dietary_restrictions": dietary_restrictions or (
            user_prof.dietary_restrictions if user_prof else []
        ),
        "allergies": allergies or (user_prof.allergies if user_prof else []),
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
    user = (
        db.query(EnhancedUser).filter(EnhancedUser.email == data.email).first()
    )
    if not user:
        return {
            "message": "If that email exists, a reset token has been generated"
        }
    token = secrets.token_urlsafe(32)
    store_reset_token(data.email, token)
    return {
        "message": (
            "Reset token generated (in production, this would be emailed)"
        ),
        "reset_token": token,
    }


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(EnhancedUser).filter(EnhancedUser.email == data.email).first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_reset_token(data.email, data.token):
        raise HTTPException(
            status_code=400, detail="Invalid or expired reset token"
        )
    from app.auth import PasswordHasher

    user.hashed_password = PasswordHasher.hash_password(data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    consume_reset_token(data.email)
    return {"message": "Password reset successfully"}


# ─── Email Verification ────────────────────────────────────
# In-memory store: email -> {"code": str, "expires": datetime}


_verification_codes: dict = {}


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


@router.post("/send-verification")
def send_verification_code(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Send a 6-digit verification code to the user's email."""
    user = (
        db.query(EnhancedUser).filter(EnhancedUser.email == email).first()
    )
    if not user:
        # Don't reveal whether the email exists
        return {"message": "If that email is registered, a code has been sent"}

    code = "".join(random.choices(string.digits, k=6))
    from datetime import timedelta
    _verification_codes[email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=15),
    }

    try:
        from app.email_service import send_verification_email

        send_verification_email(
            user_email=email,
            user_name=user.full_name or email.split("@")[0],
            verification_code=code,
        )
    except Exception:
        pass

    return {
        "message": "Verification code sent",
        # In dev mode, return code for testing. Remove in production.
        **({"code": code} if not __import__("os").getenv(
            "ENVIRONMENT", "development"
        ).startswith("prod") else {}),
    }


@router.post("/verify-email")
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """Verify user email with the 6-digit code."""
    entry = _verification_codes.get(data.email)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="No verification code found. Request a new one.",
        )
    if datetime.utcnow() > entry["expires"]:
        _verification_codes.pop(data.email, None)
        raise HTTPException(
            status_code=400,
            detail="Verification code expired. Request a new one.",
        )
    if entry["code"] != data.code:
        raise HTTPException(
            status_code=400, detail="Invalid verification code"
        )

    # Mark user as verified
    _verification_codes.pop(data.email, None)
    return {"message": "Email verified successfully", "verified": True}
