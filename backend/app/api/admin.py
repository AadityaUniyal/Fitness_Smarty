import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user
from app.database import (
    get_db,
    seed_exercise_database,
    seed_nutrition_database,
)
from app.gamification_service import GamificationService

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(
    user: models.EnhancedUser = Depends(get_current_user),
) -> models.EnhancedUser:
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


@router.get("/stats", response_model=Dict[str, Any])
def get_system_stats(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve system-wide analytics for administration"""
    total_users = db.query(models.EnhancedUser).count()
    total_workouts = db.query(models.WorkoutLog).count()
    total_meals = db.query(models.MealLog).count()
    total_points = db.query(models.UserPoints).count()

    # Active users in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_users = (
        db.query(models.EnhancedUser)
        .filter(models.EnhancedUser.updated_at >= seven_days_ago)
        .count()
    )

    # Calculate average workouts per user
    avg_workouts = round(total_workouts / max(total_users, 1), 1)

    # Gemini Integration Status
    from app.config import get_settings

    settings = get_settings()
    gemini_status = (
        "ACTIVE" if settings.GEMINI_API_KEY else "MOCKED/DEACTIVATED"
    )

    return {
        "total_users": total_users,
        "active_users_7d": active_users,
        "total_workouts": total_workouts,
        "total_meals": total_meals,
        "total_points_logs": total_points,
        "avg_workouts_per_user": avg_workouts,
        "gemini_api_status": gemini_status,
        "gemini_model": settings.GEMINI_MODEL,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all registered users with profiles"""
    users = db.query(models.EnhancedUser).all()
    user_list = []
    for u in users:
        user_list.append(
            {
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
                "created_at": u.created_at.isoformat()
                if u.created_at
                else None,
            }
        )
    return user_list


@router.put("/users/{user_id}", response_model=Dict[str, Any])
def update_user_profile(
    user_id: int,
    data: Dict[str, Any],
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Modify user settings or toggle admin privileges"""
    user = (
        db.query(models.EnhancedUser)
        .filter(models.EnhancedUser.id == user_id)
        .first()
    )
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
    db: Session = Depends(get_db),
):
    """Permanently delete user data for GDPR Right-To-Be-Forgotten"""
    user = (
        db.query(models.EnhancedUser)
        .filter(models.EnhancedUser.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cascade delete relative logs
    db.query(models.WorkoutLog).filter(
        models.WorkoutLog.user_id == user_id
    ).delete()
    db.query(models.MealLog).filter(
        models.MealLog.user_id == user_id
    ).delete()
    db.query(models.UserPoints).filter(
        models.UserPoints.user_id == user_id
    ).delete()
    db.query(models.UserStreak).filter(
        models.UserStreak.user_id == user_id
    ).delete()

    db.delete(user)
    db.commit()
    return {
        "success": True,
        "message": f"User {user_id} and all related logs completely purged.",
    }


@router.post("/system/reset-db", response_model=Dict[str, Any])
def reset_database(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """System administration utility to reseed all tables"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    allow_reset = os.getenv("ALLOW_DB_RESET", "false").lower() == "true"
    if not allow_reset and env not in {"development", "dev", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Database reset is disabled in server configuration. "
                "Set ALLOW_DB_RESET=true to enable."
            ),
        )

    # Use global database metadata to drop/create
    from app.database import Base, engine

    try:
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
            is_admin=True,
        )
        db.add(recreate_admin)
        db.commit()

        return {
            "success": True,
            "message": "Database successfully reset and seeded!",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database reset failed: {str(e)}"
        )


# ─── Web App Controllable System Configuration & Telemetry ─────────────────

DEFAULT_SYSTEM_CONFIGS = {
    "ai_provider": "gemini-3.6-flash",
    "ai_temperature": 0.6,
    "ai_system_prompt": (
        "You are SMARTY AI, an elite personal fitness and nutrition coach. "
        "Be concise, scientific, and encouraging."
    ),
    "feature_flags": {
        "femmecare": True,
        "vision_scanner": True,
        "social_feed": True,
        "wearable_sync": True,
        "form_coach": True,
    },
    "gamification": {"xp_multiplier": 1.0, "streak_grace_days": 1},
}


def get_or_init_system_config(db: Session, key: str, default_val: Any) -> Any:
    cfg = (
        db.query(models.SystemConfig)
        .filter(models.SystemConfig.key == key)
        .first()
    )
    if not cfg:
        cfg = models.SystemConfig(key=key, value=default_val)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg.value


@router.get("/system-config", response_model=Dict[str, Any])
def get_system_config(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve all web-app controllable backend settings"""
    result = {}
    for k, default_v in DEFAULT_SYSTEM_CONFIGS.items():
        result[k] = get_or_init_system_config(db, k, default_v)
    return result


@router.put("/system-config", response_model=Dict[str, Any])
def update_system_config(
    payload: Dict[str, Any],
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update dynamic backend configuration live from Web App Admin UI"""
    updated_keys = []
    for key, val in payload.items():
        if key in DEFAULT_SYSTEM_CONFIGS:
            cfg = (
                db.query(models.SystemConfig)
                .filter(models.SystemConfig.key == key)
                .first()
            )
            if not cfg:
                cfg = models.SystemConfig(key=key, value=val)
                db.add(cfg)
            else:
                cfg.value = val
            updated_keys.append(key)
    db.commit()

    current_state = {}
    for k, default_v in DEFAULT_SYSTEM_CONFIGS.items():
        current_state[k] = get_or_init_system_config(db, k, default_v)

    return {"success": True, "updated": updated_keys, "config": current_state}


@router.get("/telemetry", response_model=Dict[str, Any])
def get_system_telemetry(
    admin: models.EnhancedUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Real-time database, Redis, active users, and system health metrics"""
    import psutil

    # Table counts
    total_users = db.query(models.EnhancedUser).count()
    active_users_24h = (
        db.query(models.EnhancedUser)
        .filter(
            models.EnhancedUser.updated_at
            >= (datetime.utcnow() - timedelta(hours=24))
        )
        .count()
    )

    total_meals = db.query(models.MealLog).count()
    total_workouts = db.query(models.WorkoutLog).count()
    total_social_posts = db.query(models.SocialPost).count()

    # Memory and CPU metrics
    process = psutil.Process(os.getpid())
    memory_mb = round(process.memory_info().rss / (1024 * 1024), 2)
    cpu_percent = psutil.cpu_percent(interval=None)

    # Redis Status
    redis_status = "DISCONNECTED"
    try:
        from app.auth import _redis_client

        if _redis_client and _redis_client.ping():
            redis_status = "CONNECTED"
    except Exception:
        pass

    # AI Key Configurations
    ai_status = {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "deepgram": bool(os.getenv("DEEPGRAM_API_KEY")),
    }

    db_url = os.getenv("DATABASE_URL", "").lower()
    db_type = "PostgreSQL" if "postgresql" in db_url else "SQLite"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_type": db_type,
        "system_metrics": {
            "memory_usage_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "redis_status": redis_status,
        },
        "table_counts": {
            "total_users": total_users,
            "active_users_24h": active_users_24h,
            "total_meals": total_meals,
            "total_workouts": total_workouts,
            "total_social_posts": total_social_posts,
        },
        "ai_keys_configured": ai_status,
    }
