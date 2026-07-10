"""
Gamification API - Achievements, Badges, Streaks, Points & Leaderboard

Real-time gamification endpoints for the Smarty AI platform.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import database, models
from ..gamification_service import (
    GamificationService,
    StreakManager,
    AchievementEngine,
    BadgeEngine
)

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


# ============================================================
# ===  INITIALIZATION & SYSTEM  ===
# ============================================================


@router.post("/initialize")
def initialize_gamification(db: Session = Depends(database.get_db)):
    """
    Initialize the gamification system (seeds achievements and badges).
    
    Should be called once during system setup or migration.
    """
    try:
        GamificationService.initialize_system(db)
        return {
            "status": "initialized",
            "message": "Gamification system initialized successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize gamification system: {str(e)}"
        )


# ============================================================
# ===  USER STATS & DASHBOARD  ===
# ============================================================


@router.get("/users/{user_id}/stats")
def get_user_gamification_stats(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Get complete gamification stats for a user.
    
    Returns:
    - Points, level, and XP
    - All streaks (workout, nutrition, etc.)
    - Completed and in-progress achievements
    - Earned badges
    """
    try:
        stats = GamificationService.get_user_gamification_stats(db, user_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch gamification stats: {str(e)}"
        )


@router.get("/users/{user_id}/summary")
def get_user_summary(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Get a quick summary of user's gamification status.
    
    Perfect for dashboard widgets and quick stats.
    """
    stats = GamificationService.get_user_gamification_stats(db, user_id)
    
    # Extract key metrics
    return {
        "level": stats["points"]["level"],
        "total_points": stats["points"]["total"],
        "achievements_completed": stats["achievements"]["total_completed"],
        "badges_earned": stats["badges"]["total_earned"],
        "longest_streak": max(
            [s["longest_streak"] for s in stats["streaks"]],
            default=0
        ),
        "current_workout_streak": next(
            (s["current_streak"] for s in stats["streaks"] if s["streak_type"] == "workout"),
            0
        )
    }


# ============================================================
# ===  STREAKS  ===
# ============================================================


@router.get("/users/{user_id}/streaks")
def get_user_streaks(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Get all streaks for a user.
    
    Returns workout, nutrition, hydration, and login streaks.
    """
    streaks = StreakManager.get_all_streaks(db, user_id)
    return {"streaks": streaks}


@router.post("/users/{user_id}/streaks/{streak_type}")
def update_streak(
    user_id: int,
    streak_type: str,
    db: Session = Depends(database.get_db)
):
    """
    Update a specific streak for a user.
    
    Valid streak types: workout, nutrition, hydration, login
    """
    valid_types = ["workout", "nutrition", "hydration", "login"]
    if streak_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid streak type. Must be one of: {', '.join(valid_types)}"
        )
    
    current, longest = StreakManager.update_streak(db, user_id, streak_type)
    
    return {
        "streak_type": streak_type,
        "current_streak": current,
        "longest_streak": longest,
        "message": f"Streak updated! {current} days strong! 🔥"
    }


# ============================================================
# ===  ACHIEVEMENTS  ===
# ============================================================


@router.get("/achievements")
def get_all_achievements(db: Session = Depends(database.get_db)):
    """
    Get all available achievements in the system.
    
    Useful for displaying achievement catalog or goals.
    """
    achievements = db.query(models.Achievement).all()
    
    return {
        "achievements": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "category": a.category,
                "type": a.achievement_type,
                "icon": a.icon,
                "rarity": a.rarity,
                "points": a.points,
                "criteria": a.criteria
            }
            for a in achievements
        ]
    }


@router.get("/users/{user_id}/achievements")
def get_user_achievements(
    user_id: int,
    status: Optional[str] = None,  # completed, in_progress, all
    db: Session = Depends(database.get_db)
):
    """
    Get user's achievements with progress tracking.
    
    Query params:
    - status: Filter by 'completed', 'in_progress', or 'all' (default)
    """
    query = db.query(
        models.UserAchievement, models.Achievement
    ).join(
        models.Achievement
    ).filter(
        models.UserAchievement.user_id == user_id
    )
    
    if status == "completed":
        query = query.filter(models.UserAchievement.is_completed == True)
    elif status == "in_progress":
        query = query.filter(models.UserAchievement.is_completed == False)
    
    results = query.all()
    
    return {
        "achievements": [
            {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "rarity": ach.rarity,
                "points": ach.points,
                "category": ach.category,
                "progress": ua.progress,
                "is_completed": ua.is_completed,
                "completed_at": ua.completed_at.isoformat() if ua.completed_at else None
            }
            for ua, ach in results
        ]
    }


@router.post("/users/{user_id}/achievements/check")
def check_achievements(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Manually trigger achievement check for a user.
    
    Returns any newly unlocked achievements.
    """
    newly_unlocked = AchievementEngine.check_achievements(db, user_id)
    
    return {
        "newly_unlocked": newly_unlocked,
        "count": len(newly_unlocked),
        "message": f"🎉 {len(newly_unlocked)} new achievement(s) unlocked!" if newly_unlocked else "No new achievements unlocked."
    }


# ============================================================
# ===  BADGES  ===
# ============================================================


@router.get("/badges")
def get_all_badges(db: Session = Depends(database.get_db)):
    """
    Get all available badges in the system.
    
    Shows the complete badge catalog with tiers and requirements.
    """
    badges = db.query(models.Badge).all()
    
    return {
        "badges": [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "icon": b.icon,
                "tier": b.tier,
                "category": b.category,
                "points": b.points,
                "requirements": b.requirements
            }
            for b in badges
        ]
    }


@router.get("/users/{user_id}/badges")
def get_user_badges(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Get all badges earned by a user.
    """
    user_badges = db.query(
        models.UserBadge, models.Badge
    ).join(
        models.Badge
    ).filter(
        models.UserBadge.user_id == user_id
    ).all()
    
    return {
        "badges": [
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "tier": badge.tier,
                "category": badge.category,
                "earned_at": ub.earned_at.isoformat(),
                "is_equipped": ub.is_equipped
            }
            for ub, badge in user_badges
        ]
    }


@router.post("/users/{user_id}/badges/check")
def check_badges(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Manually trigger badge check for a user.
    
    Returns any newly earned badges.
    """
    newly_earned = BadgeEngine.check_badges(db, user_id)
    
    return {
        "newly_earned": newly_earned,
        "count": len(newly_earned),
        "message": f"🎖️ {len(newly_earned)} new badge(s) earned!" if newly_earned else "No new badges earned."
    }


@router.put("/users/{user_id}/badges/{badge_id}/equip")
def equip_badge(
    user_id: int,
    badge_id: int,
    equip: bool = True,
    db: Session = Depends(database.get_db)
):
    """
    Equip or unequip a badge for display on user profile.
    """
    user_badge = db.query(models.UserBadge).filter(
        models.UserBadge.user_id == user_id,
        models.UserBadge.badge_id == badge_id
    ).first()
    
    if not user_badge:
        raise HTTPException(
            status_code=404,
            detail="Badge not earned by user"
        )
    
    user_badge.is_equipped = equip
    db.commit()
    
    return {
        "badge_id": badge_id,
        "is_equipped": equip,
        "message": "Badge equipped!" if equip else "Badge unequipped."
    }


# ============================================================
# ===  POINTS & LEVELING  ===
# ============================================================


@router.get("/users/{user_id}/points")
def get_user_points(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Get user's points, level, and XP breakdown.
    """
    user_points = db.query(models.UserPoints).filter(
        models.UserPoints.user_id == user_id
    ).first()
    
    if not user_points:
        user_points = models.UserPoints(user_id=user_id)
        db.add(user_points)
        db.commit()
        db.refresh(user_points)
    
    return {
        "user_id": user_id,
        "total_points": user_points.total_points,
        "level": user_points.level,
        "experience_points": user_points.experience_points,
        "xp_for_next_level": (user_points.level * 100),
        "progress_to_next_level": (
            (user_points.experience_points % 100) / 100 * 100
        ),
        "breakdown": {
            "workout": user_points.workout_points,
            "nutrition": user_points.nutrition_points,
            "social": user_points.social_points,
            "streak": user_points.streak_points,
            "achievement": user_points.achievement_points
        }
    }


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(database.get_db)
):
    """
    Get the global leaderboard of top users by points.
    
    Shows top 10 users (or specified limit) ranked by total points.
    """
    top_users = db.query(
        models.UserPoints,
        models.EnhancedUser
    ).join(
        models.EnhancedUser
    ).order_by(
        models.UserPoints.total_points.desc()
    ).limit(limit).all()
    
    leaderboard = []
    for rank, (points, user) in enumerate(top_users, start=1):
        leaderboard.append({
            "rank": rank,
            "user_id": user.id,
            "username": user.username or user.full_name or f"User {user.id}",
            "level": points.level,
            "total_points": points.total_points,
            "workout_points": points.workout_points,
            "nutrition_points": points.nutrition_points
        })
    
    return {
        "leaderboard": leaderboard,
        "total_entries": len(leaderboard)
    }


# ============================================================
# ===  EVENT TRIGGERS (Internal Use)  ===
# ============================================================


@router.post("/events/workout-completed")
def trigger_workout_completed(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Trigger gamification checks after a workout is completed.
    
    This should be called automatically by the workout logging endpoint.
    """
    result = GamificationService.on_workout_completed(db, user_id)
    
    return {
        "user_id": user_id,
        "event": "workout_completed",
        "newly_unlocked_achievements": result["achievements"],
        "newly_earned_badges": result["badges"]
    }


@router.post("/events/meal-logged")
def trigger_meal_logged(
    user_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Trigger gamification checks after a meal is logged.
    
    This should be called automatically by the meal logging endpoint.
    """
    result = GamificationService.on_meal_logged(db, user_id)
    
    return {
        "user_id": user_id,
        "event": "meal_logged",
        "newly_unlocked_achievements": result["achievements"],
        "newly_earned_badges": result["badges"]
    }
