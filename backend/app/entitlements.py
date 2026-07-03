from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Entitlement, EnhancedUser

def has_entitlement(user_id: str, feature_code: str, db: Session) -> bool:
    """
    Check if a user is explicitly granted a premium feature flag.
    If no explicit grant is set, fall back to checking if the user is a trainer or
    has a premium badge configured.
    """
    # 1. Direct entitlement check
    ent = db.query(Entitlement).filter(
        Entitlement.user_id == user_id,
        Entitlement.feature_code == feature_code
    ).first()
    if ent:
        return ent.granted
        
    # 2. User profile level fallback check (e.g. trainer role bypasses checks)
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if user:
        if user.primary_goal and "trainer" in user.primary_goal:
            return True
            
    # Default: Premium features require explicit grant
    return False

def verify_premium_entitlement(feature_code: str):
    """
    FastAPI dependency injection wrapper to gate premium endpoints at the API layer.
    """
    def dependency(user_id: str, db: Session = Depends(get_db)):
        if not has_entitlement(user_id, feature_code, db):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Premium subscription required",
                    "feature": feature_code,
                    "reason_code": "REQUIRED_ENTITLEMENT_MISSING"
                }
            )
        return True
    return dependency
