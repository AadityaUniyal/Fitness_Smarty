from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import schemas, models
from app.user_profile_service import UserProfileService, UserProfileCreate, UserProfileUpdate, GoalCreate, GoalUpdate
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id
from app.api_validation import APIValidator, ErrorHandler

router = APIRouter(prefix="/api/users", tags=["User Profile & Goals"])

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_profile(
    db: Session = Depends(get_db), 
    user_id: str = Depends(get_current_user_id)
):
    """Get current authenticated user's core profile data"""
    user = None
    try:
        user_id_int = int(user_id)
        user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_id_int).first()
    except (ValueError, TypeError):
        user = db.query(models.EnhancedUser).filter(models.EnhancedUser.clerk_user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {**{k: v for k, v in user.__dict__.items() if not k.startswith('_')}, "achievements": [], "daily_calories": 2450, "daily_steps": 12402, "heart_rate": 72}

@router.post("/{user_id}/profile", response_model=schemas.UserProfileResponse)
def create_user_profile(
    user_id: str,
    profile_data: schemas.UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a user profile"""
    service = UserProfileService(db)
    existing_profile = service.get_user_profile(user_id)
    if existing_profile:
        raise ErrorHandler.conflict_error("User profile already exists. Use PUT to update.")
    
    try:
        service_profile_data = UserProfileCreate(**profile_data.model_dump())
        profile = service.create_user_profile(user_id, service_profile_data)
        return schemas.UserProfileResponse.model_validate(profile)
    except ValueError as e:
        raise ErrorHandler.bad_request_error(str(e))

@router.get("/{user_id}/profile", response_model=schemas.UserProfileResponse)
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user profile information"""
    service = UserProfileService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return schemas.UserProfileResponse.model_validate(profile)

@router.put("/{user_id}/profile", response_model=schemas.UserProfileResponse)
def update_user_profile(
    user_id: str,
    profile_data: schemas.UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    service = UserProfileService(db)
    try:
        update_dict = profile_data.model_dump(exclude_unset=True)
        service_profile_data = UserProfileUpdate(**update_dict)
        profile = service.update_user_profile(user_id, service_profile_data)
        return schemas.UserProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}/profile/validate", response_model=schemas.ProfileValidationResponse)
def validate_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Validate user profile completeness"""
    service = UserProfileService(db)
    try:
        return service.validate_profile(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Goals
@router.post("/{user_id}/goals", response_model=schemas.UserGoalResponse)
def create_user_goal(
    user_id: str,
    goal_data: schemas.GoalCreate,
    db: Session = Depends(get_db)
):
    """Create a new fitness goal"""
    service = UserProfileService(db)
    try:
        service_goal_data = GoalCreate(**goal_data.model_dump())
        goal = service.create_goal(user_id, service_goal_data)
        return schemas.UserGoalResponse.model_validate(goal)
    except ValueError as e:
        raise ErrorHandler.bad_request_error(str(e))

@router.get("/{user_id}/goals", response_model=schemas.GoalListResponse)
def get_user_goals(
    user_id: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get all goals for a user"""
    service = UserProfileService(db)
    goals = service.get_user_goals(user_id, active_only=active_only)
    goals_response = [schemas.UserGoalResponse.model_validate(goal) for goal in goals]
    return {"goals": goals_response, "total_count": len(goals_response)}

@router.get("/{user_id}/progress", response_model=schemas.ProgressMetricsResponse)
def get_progress_metrics(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get progress metrics for active goals"""
    service = UserProfileService(db)
    try:
        metrics = service.calculate_progress_metrics(user_id)
        if metrics['goals']:
            first_goal = metrics['goals'][0]
            return first_goal
        else:
            raise HTTPException(status_code=404, detail="No active goals found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
