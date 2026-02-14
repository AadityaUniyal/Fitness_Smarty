
from sqlalchemy.orm import Session
from . import models

# Points awarded for different actions
XP_REWARDS = {
    "WORKOUT": 500,
    "MEAL": 100,
    "BIOMETRIC": 50,
    "DAILY_LOGIN": 25
}

def grant_xp(db: Session, user_id: str, action_type: str):
    """Adds XP to user and checks for level up events."""
    user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_id).first()
    if not user:
        return
    
    xp_to_add = XP_REWARDS.get(action_type, 10)
    user.xp += xp_to_add
    
    # Simple Level Up Logic: Every 1000 XP = 1 Level
    new_level = (user.xp // 1000) + 1
    if new_level > user.level:
        user.level = new_level
        # Create a social post for the level up
        level_post = models.SocialActivity(
            operator_name=user.name,
            activity_type="LEVEL_UP",
            content=f"Reached Neural Tier {new_level}!"
        )
        db.add(level_post)
        
        # Auto-unlock achievement for big levels
        if new_level % 5 == 0:
            unlock_achievement(db, user_id, f"Tier {new_level} Elite", "Mastered 5 Neural Tiers", "ShieldCheck")

    db.commit()

def unlock_achievement(db: Session, user_id: str, title: str, desc: str, icon: str):
    """Persists a new badge for the user."""
    # Check if already unlocked
    existing = db.query(models.Achievement).filter(
        models.Achievement.user_id == user_id,
        models.Achievement.title == title
    ).first()
    
    if not existing:
        new_badge = models.Achievement(
            user_id=user_id,
            title=title,
            description=desc,
            icon=icon
        )
        db.add(new_badge)
        db.commit()
