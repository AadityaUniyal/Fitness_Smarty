from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app import models, database, auth
from app.database import get_db, seed_exercise_database, seed_nutrition_database
from app.auth import get_current_user
from app.gamification_service import GamificationService

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(user: models.EnhancedUser = Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

@router.get("/stats", response_model=Dict[str, Any])
def get_system_stats(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve system-wide analytics for administration"""
    total_users = db.query(models.EnhancedUser).count()
    total_workouts = db.query(models.WorkoutLog).count()
    total_meals = db.query(models.MealLog).count()
    total_points = db.query(models.UserPoints).count()
    
    # Active users in the last 7 days
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db.query(models.EnhancedUser).filter(
        models.EnhancedUser.updated_at >= seven_days_ago
    ).count()

    # Calculate average workouts per user
    avg_workouts = round(total_workouts / max(total_users, 1), 1)

    # Gemini Integration Status
    from app.config import get_settings
    settings = get_settings()
    gemini_status = "ACTIVE" if settings.GEMINI_API_KEY else "MOCKED/DEACTIVATED"

    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "total_workouts": total_workouts,
        "total_meals": total_meals,
        "total_points_logs": total_points,
        "avg_workouts_per_user": avg_workouts,
        "gemini_api_status": gemini_status,
        "gemini_model": settings.GEMINI_MODEL,
        "environment": settings.ENVIRONMENT
    }

@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all registered users with profiles"""
    users = db.query(models.EnhancedUser).all()
    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": getattr(u, "is_admin", False),
            "age": u.age,
            "weight_kg": u.weight_kg,
            "height_cm": u.height_cm,
            "gender": u.gender,
            "activity_level": u.activity_level,
            "primary_goal": u.primary_goal,
            "femmecare_enabled": u.femmecare_enabled,
            "local_only": u.local_only,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return user_list

@router.put("/users/{user_id}", response_model=Dict[str, Any])
def update_user_profile(
    user_id: int,
    data: Dict[str, Any],
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Modify user settings or toggle admin privileges"""
    user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    if "age" in data:
        user.age = data["age"]
    if "weight_kg" in data:
        user.weight_kg = data["weight_kg"]
    if "height_cm" in data:
        user.height_cm = data["height_cm"]
    if "primary_goal" in data:
        user.primary_goal = data["primary_goal"]
    if "activity_level" in data:
        user.activity_level = data["activity_level"]
        
    db.commit()
    return {"success": True, "message": "User updated successfully"}

@router.delete("/users/{user_id}", response_model=Dict[str, Any])
def delete_user_data(
    user_id: int,
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Permanently delete user data for GDPR/Right-To-Be-Forgotten compliance"""
    user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Cascade delete relative logs
    db.query(models.WorkoutLog).filter(models.WorkoutLog.user_id == user_id).delete()
    db.query(models.MealLog).filter(models.MealLog.user_id == user_id).delete()
    db.query(models.UserPoints).filter(models.UserPoints.user_id == user_id).delete()
    db.query(models.UserStreak).filter(models.UserStreak.user_id == user_id).delete()
    
    db.delete(user)
    db.commit()
    return {"success": True, "message": f"User {user_id} and all related logs completely purged."}

@router.post("/system/reset-db", response_model=Dict[str, Any])
def reset_database(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """System administration utility to reseed all tables"""
    # Use global database metadata to drop/create
    from app.database import engine, Base
    try:
        # Drop all tables except auth session tables if any, or drop completely
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Seed default tables
        seed_exercise_database()
        seed_nutrition_database()
        
        # Seed gamification badges
        GamificationService.initialize_system(db)
        
        # Re-create the requesting admin account to avoid losing access
        recreate_admin = models.EnhancedUser(
            id=admin.id,
            username=admin.username,
            email=admin.email,
            hashed_password=admin.hashed_password,
            is_admin=True
        )
        db.add(recreate_admin)
        db.commit()
        
        return {"success": True, "message": "Database successfully reset and seeded!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")
