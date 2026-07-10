"""
Gamification Service - Streaks, Achievements, Badges, and Points

Real-time threshold-based achievement system that monitors database activity
and automatically unlocks badges when milestones are reached.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from . import models

logger = logging.getLogger(__name__)


# ============================================================
# ===  ACHIEVEMENT & BADGE DEFINITIONS  ===
# ============================================================

ACHIEVEMENT_TEMPLATES = [
    # Workout Achievements
    {
        "name": "First Steps",
        "description": "Complete your first workout",
        "category": "workout",
        "achievement_type": "count",
        "icon": "🎯",
        "rarity": "common",
        "points": 10,
        "criteria": {"type": "workout_count", "target": 1}
    },
    {
        "name": "Iron Will",
        "description": "Complete 10 workouts",
        "category": "workout",
        "achievement_type": "count",
        "icon": "💪",
        "rarity": "common",
        "points": 25,
        "criteria": {"type": "workout_count", "target": 10}
    },
    {
        "name": "Warrior Spirit",
        "description": "Complete 50 workouts",
        "category": "workout",
        "achievement_type": "count",
        "icon": "⚔️",
        "rarity": "rare",
        "points": 100,
        "criteria": {"type": "workout_count", "target": 50}
    },
    {
        "name": "Titan",
        "description": "Complete 100 workouts",
        "category": "workout",
        "achievement_type": "count",
        "icon": "🏆",
        "rarity": "epic",
        "points": 250,
        "criteria": {"type": "workout_count", "target": 100}
    },
    {
        "name": "Legend",
        "description": "Complete 500 workouts",
        "category": "workout",
        "achievement_type": "count",
        "icon": "👑",
        "rarity": "legendary",
        "points": 1000,
        "criteria": {"type": "workout_count", "target": 500}
    },
    
    # Calorie Burn Achievements
    {
        "name": "Calorie Crusher",
        "description": "Burn 1,000 total calories",
        "category": "workout",
        "achievement_type": "count",
        "icon": "🔥",
        "rarity": "common",
        "points": 15,
        "criteria": {"type": "calories_burned", "target": 1000}
    },
    {
        "name": "Inferno",
        "description": "Burn 10,000 total calories",
        "category": "workout",
        "achievement_type": "count",
        "icon": "🌋",
        "rarity": "rare",
        "points": 100,
        "criteria": {"type": "calories_burned", "target": 10000}
    },
    {
        "name": "Supernova",
        "description": "Burn 50,000 total calories",
        "category": "workout",
        "achievement_type": "count",
        "icon": "💥",
        "rarity": "epic",
        "points": 500,
        "criteria": {"type": "calories_burned", "target": 50000}
    },
    
    # Streak Achievements
    {
        "name": "Consistency Starter",
        "description": "3-day workout streak",
        "category": "streak",
        "achievement_type": "streak",
        "icon": "📅",
        "rarity": "common",
        "points": 20,
        "criteria": {"type": "streak_days", "streak_type": "workout", "target": 3}
    },
    {
        "name": "Week Warrior",
        "description": "7-day workout streak",
        "category": "streak",
        "achievement_type": "streak",
        "icon": "🔥",
        "rarity": "common",
        "points": 50,
        "criteria": {"type": "streak_days", "streak_type": "workout", "target": 7}
    },
    {
        "name": "Unstoppable",
        "description": "30-day workout streak",
        "category": "streak",
        "achievement_type": "streak",
        "icon": "⚡",
        "rarity": "rare",
        "points": 200,
        "criteria": {"type": "streak_days", "streak_type": "workout", "target": 30}
    },
    {
        "name": "Iron Discipline",
        "description": "100-day workout streak",
        "category": "streak",
        "achievement_type": "streak",
        "icon": "💎",
        "rarity": "epic",
        "points": 500,
        "criteria": {"type": "streak_days", "streak_type": "workout", "target": 100}
    },
    
    # Nutrition Achievements
    {
        "name": "Meal Logger",
        "description": "Log 10 meals",
        "category": "nutrition",
        "achievement_type": "count",
        "icon": "🍽️",
        "rarity": "common",
        "points": 15,
        "criteria": {"type": "meal_count", "target": 10}
    },
    {
        "name": "Nutrition Tracker",
        "description": "Log 50 meals",
        "category": "nutrition",
        "achievement_type": "count",
        "icon": "📊",
        "rarity": "rare",
        "points": 75,
        "criteria": {"type": "meal_count", "target": 50}
    },
    {
        "name": "Macro Master",
        "description": "Log 200 meals",
        "category": "nutrition",
        "achievement_type": "count",
        "icon": "🎖️",
        "rarity": "epic",
        "points": 300,
        "criteria": {"type": "meal_count", "target": 200}
    },
    {
        "name": "Nutrition Streak",
        "description": "7-day meal logging streak",
        "category": "streak",
        "achievement_type": "streak",
        "icon": "🥗",
        "rarity": "common",
        "points": 40,
        "criteria": {"type": "streak_days", "streak_type": "nutrition", "target": 7}
    },
    
    # Milestone Achievements
    {
        "name": "Community Member",
        "description": "Join the Smarty AI community",
        "category": "milestone",
        "achievement_type": "special",
        "icon": "👋",
        "rarity": "common",
        "points": 5,
        "criteria": {"type": "registration", "target": 1}
    },
    {
        "name": "30-Day Champion",
        "description": "Active for 30 days",
        "category": "milestone",
        "achievement_type": "goal",
        "icon": "📆",
        "rarity": "rare",
        "points": 100,
        "criteria": {"type": "days_active", "target": 30}
    },
    {
        "name": "Year of Excellence",
        "description": "Active for 365 days",
        "category": "milestone",
        "achievement_type": "goal",
        "icon": "🎊",
        "rarity": "legendary",
        "points": 1000,
        "criteria": {"type": "days_active", "target": 365}
    },
]


BADGE_TEMPLATES = [
    # Strength Badges
    {
        "name": "Bronze Strength",
        "description": "Complete 25 strength workouts",
        "icon": "🥉",
        "tier": "bronze",
        "category": "strength",
        "points": 30,
        "requirements": {"workout_type": "strength", "count": 25}
    },
    {
        "name": "Silver Strength",
        "description": "Complete 75 strength workouts",
        "icon": "🥈",
        "tier": "silver",
        "category": "strength",
        "points": 75,
        "requirements": {"workout_type": "strength", "count": 75}
    },
    {
        "name": "Gold Strength",
        "description": "Complete 150 strength workouts",
        "icon": "🥇",
        "tier": "gold",
        "category": "strength",
        "points": 150,
        "requirements": {"workout_type": "strength", "count": 150}
    },
    
    # Cardio Badges
    {
        "name": "Bronze Cardio",
        "description": "Complete 25 cardio workouts",
        "icon": "🥉",
        "tier": "bronze",
        "category": "cardio",
        "points": 30,
        "requirements": {"workout_type": "cardio", "count": 25}
    },
    {
        "name": "Silver Cardio",
        "description": "Complete 75 cardio workouts",
        "icon": "🥈",
        "tier": "silver",
        "category": "cardio",
        "points": 75,
        "requirements": {"workout_type": "cardio", "count": 75}
    },
    {
        "name": "Gold Cardio",
        "description": "Complete 150 cardio workouts",
        "icon": "🥇",
        "tier": "gold",
        "category": "cardio",
        "points": 150,
        "requirements": {"workout_type": "cardio", "count": 150}
    },
    
    # Nutrition Badges
    {
        "name": "Bronze Nutrition",
        "description": "Log 50 nutritious meals",
        "icon": "🥉",
        "tier": "bronze",
        "category": "nutrition",
        "points": 30,
        "requirements": {"meal_logs": 50}
    },
    {
        "name": "Silver Nutrition",
        "description": "Log 150 nutritious meals",
        "icon": "🥈",
        "tier": "silver",
        "category": "nutrition",
        "points": 75,
        "requirements": {"meal_logs": 150}
    },
    {
        "name": "Gold Nutrition",
        "description": "Log 300 nutritious meals",
        "icon": "🥇",
        "tier": "gold",
        "category": "nutrition",
        "points": 150,
        "requirements": {"meal_logs": 300}
    },
    
    # Consistency Badges
    {
        "name": "Bronze Consistency",
        "description": "Maintain a 7-day streak",
        "icon": "🥉",
        "tier": "bronze",
        "category": "consistency",
        "points": 40,
        "requirements": {"streak_days": 7}
    },
    {
        "name": "Silver Consistency",
        "description": "Maintain a 30-day streak",
        "icon": "🥈",
        "tier": "silver",
        "category": "consistency",
        "points": 100,
        "requirements": {"streak_days": 30}
    },
    {
        "name": "Gold Consistency",
        "description": "Maintain a 90-day streak",
        "icon": "🥇",
        "tier": "gold",
        "category": "consistency",
        "points": 250,
        "requirements": {"streak_days": 90}
    },
    {
        "name": "Platinum Consistency",
        "description": "Maintain a 180-day streak",
        "icon": "💍",
        "tier": "platinum",
        "category": "consistency",
        "points": 500,
        "requirements": {"streak_days": 180}
    },
    {
        "name": "Diamond Consistency",
        "description": "Maintain a 365-day streak",
        "icon": "💎",
        "tier": "diamond",
        "category": "consistency",
        "points": 1000,
        "requirements": {"streak_days": 365}
    },
]


# ============================================================
# ===  STREAK MANAGEMENT  ===
# ============================================================


class StreakManager:
    """Manages user activity streaks"""
    
    @staticmethod
    def update_streak(
        db: Session,
        user_id: int,
        streak_type: str
    ) -> Tuple[int, int]:
        """
        Update a user's streak for a specific activity type.
        
        Returns: (current_streak, longest_streak)
        """
        streak = db.query(models.UserStreak).filter(
            and_(
                models.UserStreak.user_id == user_id,
                models.UserStreak.streak_type == streak_type
            )
        ).first()
        
        now = datetime.utcnow()
        today = now.date()
        
        if not streak:
            # Create new streak
            streak = models.UserStreak(
                user_id=user_id,
                streak_type=streak_type,
                current_streak=1,
                longest_streak=1,
                last_activity_date=now
            )
            db.add(streak)
            db.commit()
            return (1, 1)
        
        last_date = streak.last_activity_date.date() if streak.last_activity_date else None
        
        if last_date == today:
            # Already logged today, no change
            return (streak.current_streak, streak.longest_streak)
        
        yesterday = today - timedelta(days=1)
        
        if last_date == yesterday:
            # Continuing streak
            streak.current_streak += 1
        elif last_date and last_date < yesterday:
            # Streak broken, restart
            streak.current_streak = 1
        else:
            # First time
            streak.current_streak = 1
        
        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        streak.last_activity_date = now
        streak.updated_at = now
        
        db.commit()
        db.refresh(streak)
        
        return (streak.current_streak, streak.longest_streak)
    
    @staticmethod
    def get_all_streaks(db: Session, user_id: int) -> List[Dict]:
        """Get all streaks for a user"""
        streaks = db.query(models.UserStreak).filter(
            models.UserStreak.user_id == user_id
        ).all()
        
        return [
            {
                "streak_type": s.streak_type,
                "current_streak": s.current_streak,
                "longest_streak": s.longest_streak,
                "last_activity_date": s.last_activity_date.isoformat() if s.last_activity_date else None
            }
            for s in streaks
        ]


# ============================================================
# ===  ACHIEVEMENT ENGINE  ===
# ============================================================


class AchievementEngine:
    """Checks and awards achievements based on user activity"""
    
    @staticmethod
    def initialize_achievements(db: Session):
        """Seed achievement templates into the database"""
        for template in ACHIEVEMENT_TEMPLATES:
            existing = db.query(models.Achievement).filter(
                models.Achievement.name == template["name"]
            ).first()
            
            if not existing:
                achievement = models.Achievement(**template)
                db.add(achievement)
        
        db.commit()
        logger.info(f"Initialized {len(ACHIEVEMENT_TEMPLATES)} achievements")
    
    @staticmethod
    def check_achievements(db: Session, user_id: int) -> List[Dict]:
        """
        Check all achievements for a user and award any newly completed ones.
        
        Returns list of newly unlocked achievements.
        """
        newly_unlocked = []
        
        # Get all achievements
        achievements = db.query(models.Achievement).all()
        
        for achievement in achievements:
            # Check if user already has this achievement
            user_achievement = db.query(models.UserAchievement).filter(
                and_(
                    models.UserAchievement.user_id == user_id,
                    models.UserAchievement.achievement_id == achievement.id
                )
            ).first()
            
            if user_achievement and user_achievement.is_completed:
                # Already completed
                continue
            
            # Check if criteria is met
            is_met, progress = AchievementEngine._check_criteria(
                db, user_id, achievement.criteria
            )
            
            if not user_achievement:
                # Create new user achievement record
                user_achievement = models.UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    progress=progress,
                    is_completed=is_met
                )
                db.add(user_achievement)
            else:
                # Update progress
                user_achievement.progress = progress
                user_achievement.is_completed = is_met
            
            if is_met and not user_achievement.completed_at:
                # Newly completed!
                user_achievement.completed_at = datetime.utcnow()
                
                # Award points
                AchievementEngine._award_points(
                    db, user_id, achievement.points, "achievement"
                )
                
                newly_unlocked.append({
                    "id": achievement.id,
                    "name": achievement.name,
                    "description": achievement.description,
                    "icon": achievement.icon,
                    "rarity": achievement.rarity,
                    "points": achievement.points,
                    "category": achievement.category
                })
                
                logger.info(
                    f"🏆 User {user_id} unlocked achievement: {achievement.name}"
                )
        
        db.commit()
        return newly_unlocked
    
    @staticmethod
    def _check_criteria(
        db: Session,
        user_id: int,
        criteria: Dict
    ) -> Tuple[bool, float]:
        """
        Check if achievement criteria is met.
        
        Returns: (is_met, progress_percentage)
        """
        criteria_type = criteria.get("type")
        target = criteria.get("target", 1)
        
        if criteria_type == "workout_count":
            count = db.query(func.count(models.WorkoutLog.id)).filter(
                models.WorkoutLog.user_id == user_id
            ).scalar() or 0
            progress = min(100, (count / target) * 100)
            return (count >= target, progress)
        
        elif criteria_type == "calories_burned":
            total = db.query(
                func.sum(models.WorkoutLog.calories_burned)
            ).filter(
                models.WorkoutLog.user_id == user_id
            ).scalar() or 0
            progress = min(100, (total / target) * 100)
            return (total >= target, progress)
        
        elif criteria_type == "streak_days":
            streak_type = criteria.get("streak_type", "workout")
            streak = db.query(models.UserStreak).filter(
                and_(
                    models.UserStreak.user_id == user_id,
                    models.UserStreak.streak_type == streak_type
                )
            ).first()
            
            if not streak:
                return (False, 0.0)
            
            current = streak.current_streak
            progress = min(100, (current / target) * 100)
            return (current >= target, progress)
        
        elif criteria_type == "meal_count":
            count = db.query(func.count(models.MealLog.id)).filter(
                models.MealLog.user_id == user_id
            ).scalar() or 0
            progress = min(100, (count / target) * 100)
            return (count >= target, progress)
        
        elif criteria_type == "days_active":
            user = db.query(models.EnhancedUser).filter(
                models.EnhancedUser.id == user_id
            ).first()
            
            if not user:
                return (False, 0.0)
            
            days = (datetime.utcnow() - user.created_at).days
            progress = min(100, (days / target) * 100)
            return (days >= target, progress)
        
        elif criteria_type == "registration":
            # Auto-complete for all registered users
            return (True, 100.0)
        
        return (False, 0.0)
    
    @staticmethod
    def _award_points(
        db: Session,
        user_id: int,
        points: int,
        source: str
    ):
        """Award points to a user"""
        user_points = db.query(models.UserPoints).filter(
            models.UserPoints.user_id == user_id
        ).first()
        
        if not user_points:
            user_points = models.UserPoints(
                user_id=user_id,
                total_points=0
            )
            db.add(user_points)
        
        user_points.total_points += points
        user_points.experience_points += points
        
        # Update source-specific points
        if source == "workout":
            user_points.workout_points += points
        elif source == "nutrition":
            user_points.nutrition_points += points
        elif source == "social":
            user_points.social_points += points
        elif source == "streak":
            user_points.streak_points += points
        elif source == "achievement":
            user_points.achievement_points += points
        
        # Level up logic (100 XP per level)
        xp_per_level = 100
        new_level = (user_points.experience_points // xp_per_level) + 1
        user_points.level = new_level
        
        db.commit()


# ============================================================
# ===  BADGE ENGINE  ===
# ============================================================


class BadgeEngine:
    """Manages badge awarding"""
    
    @staticmethod
    def initialize_badges(db: Session):
        """Seed badge templates into the database"""
        for template in BADGE_TEMPLATES:
            existing = db.query(models.Badge).filter(
                models.Badge.name == template["name"]
            ).first()
            
            if not existing:
                badge = models.Badge(**template)
                db.add(badge)
        
        db.commit()
        logger.info(f"Initialized {len(BADGE_TEMPLATES)} badges")
    
    @staticmethod
    def check_badges(db: Session, user_id: int) -> List[Dict]:
        """
        Check all badges for a user and award any newly earned ones.
        
        Returns list of newly earned badges.
        """
        newly_earned = []
        
        badges = db.query(models.Badge).all()
        
        for badge in badges:
            # Check if user already has this badge
            user_badge = db.query(models.UserBadge).filter(
                and_(
                    models.UserBadge.user_id == user_id,
                    models.UserBadge.badge_id == badge.id
                )
            ).first()
            
            if user_badge:
                # Already earned
                continue
            
            # Check requirements
            is_met = BadgeEngine._check_requirements(
                db, user_id, badge.requirements
            )
            
            if is_met:
                # Award badge
                user_badge = models.UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    earned_at=datetime.utcnow()
                )
                db.add(user_badge)
                
                # Award points
                AchievementEngine._award_points(
                    db, user_id, badge.points, "achievement"
                )
                
                newly_earned.append({
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "tier": badge.tier,
                    "category": badge.category,
                    "points": badge.points
                })
                
                logger.info(
                    f"🎖️ User {user_id} earned badge: {badge.name}"
                )
        
        db.commit()
        return newly_earned
    
    @staticmethod
    def _check_requirements(
        db: Session,
        user_id: int,
        requirements: Dict
    ) -> bool:
        """Check if badge requirements are met"""
        
        if "workout_type" in requirements:
            # Check workout type count
            # For now, count all workouts (can be enhanced later with workout type filtering)
            target_count = requirements.get("count", 1)
            
            count = db.query(func.count(models.WorkoutLog.id)).filter(
                models.WorkoutLog.user_id == user_id
            ).scalar() or 0
            
            return count >= target_count
        
        elif "meal_logs" in requirements:
            count = db.query(func.count(models.MealLog.id)).filter(
                models.MealLog.user_id == user_id
            ).scalar() or 0
            
            return count >= requirements["meal_logs"]
        
        elif "streak_days" in requirements:
            # Check any streak type
            streak = db.query(models.UserStreak).filter(
                models.UserStreak.user_id == user_id
            ).order_by(models.UserStreak.longest_streak.desc()).first()
            
            if not streak:
                return False
            
            return streak.longest_streak >= requirements["streak_days"]
        
        return False


# ============================================================
# ===  MAIN GAMIFICATION SERVICE  ===
# ============================================================


class GamificationService:
    """Main service for all gamification features"""
    
    @staticmethod
    def initialize_system(db: Session):
        """Initialize the gamification system"""
        AchievementEngine.initialize_achievements(db)
        BadgeEngine.initialize_badges(db)
        logger.info("✨ Gamification system initialized")
    
    @staticmethod
    def on_workout_completed(db: Session, user_id: int):
        """Called when a workout is completed"""
        # Update workout streak
        StreakManager.update_streak(db, user_id, "workout")
        
        # Award workout points
        AchievementEngine._award_points(db, user_id, 5, "workout")
        
        # Check achievements and badges
        achievements = AchievementEngine.check_achievements(db, user_id)
        badges = BadgeEngine.check_badges(db, user_id)
        
        return {
            "achievements": achievements,
            "badges": badges
        }
    
    @staticmethod
    def on_meal_logged(db: Session, user_id: int):
        """Called when a meal is logged"""
        # Update nutrition streak
        StreakManager.update_streak(db, user_id, "nutrition")
        
        # Award nutrition points
        AchievementEngine._award_points(db, user_id, 3, "nutrition")
        
        # Check achievements and badges
        achievements = AchievementEngine.check_achievements(db, user_id)
        badges = BadgeEngine.check_badges(db, user_id)
        
        return {
            "achievements": achievements,
            "badges": badges
        }
    
    @staticmethod
    def get_user_gamification_stats(db: Session, user_id: int) -> Dict:
        """Get complete gamification stats for a user"""
        # Points and level
        user_points = db.query(models.UserPoints).filter(
            models.UserPoints.user_id == user_id
        ).first()
        
        if not user_points:
            user_points = models.UserPoints(user_id=user_id)
            db.add(user_points)
            db.commit()
        
        # Streaks
        streaks = StreakManager.get_all_streaks(db, user_id)
        
        # Achievements
        user_achievements = db.query(
            models.UserAchievement, models.Achievement
        ).join(
            models.Achievement
        ).filter(
            models.UserAchievement.user_id == user_id
        ).all()
        
        completed_achievements = []
        in_progress_achievements = []
        
        for ua, ach in user_achievements:
            ach_data = {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "rarity": ach.rarity,
                "points": ach.points,
                "category": ach.category,
                "progress": ua.progress,
                "completed": ua.is_completed,
                "completed_at": ua.completed_at.isoformat() if ua.completed_at else None
            }
            
            if ua.is_completed:
                completed_achievements.append(ach_data)
            else:
                in_progress_achievements.append(ach_data)
        
        # Badges
        user_badges = db.query(
            models.UserBadge, models.Badge
        ).join(
            models.Badge
        ).filter(
            models.UserBadge.user_id == user_id
        ).all()
        
        earned_badges = [
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
        
        return {
            "points": {
                "total": user_points.total_points,
                "level": user_points.level,
                "experience_points": user_points.experience_points,
                "next_level_xp": (user_points.level * 100),
                "breakdown": {
                    "workout": user_points.workout_points,
                    "nutrition": user_points.nutrition_points,
                    "social": user_points.social_points,
                    "streak": user_points.streak_points,
                    "achievement": user_points.achievement_points
                }
            },
            "streaks": streaks,
            "achievements": {
                "completed": completed_achievements,
                "in_progress": in_progress_achievements,
                "total_completed": len(completed_achievements)
            },
            "badges": {
                "earned": earned_badges,
                "total_earned": len(earned_badges)
            }
        }
