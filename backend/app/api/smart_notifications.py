"""
Smart Notifications API
Intelligent reminders based on user behavior, schedule, and cycle phase
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app import database, models
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["Smart Notifications"])


class NotificationPreferences(BaseModel):
    user_id: str
    meal_reminders: bool = True
    hydration_reminders: bool = True
    workout_reminders: bool = True
    cycle_reminders: bool = False
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "07:00"


@router.post("/preferences/update")
def update_notification_preferences(
    prefs: NotificationPreferences,
    db: Session = Depends(database.get_db),
):
    """
    Update user notification preferences.
    (In production, store in a user_notification_preferences table)
    """
    try:
        return {
            "user_id": prefs.user_id,
            "preferences_updated": True,
            "active_notifications": {
                "meal_reminders": prefs.meal_reminders,
                "hydration_reminders": prefs.hydration_reminders,
                "workout_reminders": prefs.workout_reminders,
                "cycle_reminders": prefs.cycle_reminders
            },
            "quiet_hours": {
                "start": prefs.quiet_hours_start,
                "end": prefs.quiet_hours_end
            }
        }
    except Exception as e:
        logger.error(f"Notification preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/{user_id}")
def get_notification_schedule(
    user_id: str,
    db: Session = Depends(database.get_db),
):
    """
    Get intelligent notification schedule based on user's activity patterns.
    """
    try:
        # Get user's recent meal times to establish pattern
        recent_meals = db.query(models.MealLog).filter(
            and_(
                models.MealLog.user_id == user_id,
                models.MealLog.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).order_by(desc(models.MealLog.created_at)).limit(30).all()
        
        # Get user's recent workout times
        recent_workouts = db.query(models.WorkoutLog).filter(
            and_(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).order_by(desc(models.WorkoutLog.created_at)).limit(20).all()
        
        # Analyze meal patterns
        meal_hours = {}
        for meal in recent_meals:
            hour = meal.created_at.hour
            meal_hours[hour] = meal_hours.get(hour, 0) + 1
        
        # Find peak meal times
        breakfast_hours = [h for h in range(6, 11) if h in meal_hours]
        lunch_hours = [h for h in range(11, 15) if h in meal_hours]
        dinner_hours = [h for h in range(17, 21) if h in meal_hours]
        
        typical_breakfast = max(breakfast_hours, key=lambda h: meal_hours[h]) if breakfast_hours else 8
        typical_lunch = max(lunch_hours, key=lambda h: meal_hours[h]) if lunch_hours else 12
        typical_dinner = max(dinner_hours, key=lambda h: meal_hours[h]) if dinner_hours else 19
        
        # Analyze workout patterns
        workout_hours = {}
        for workout in recent_workouts:
            hour = workout.created_at.hour
            workout_hours[hour] = workout_hours.get(hour, 0) + 1
        
        typical_workout_hour = max(workout_hours.keys(), key=lambda h: workout_hours[h]) if workout_hours else 17
        
        # Build smart schedule
        schedule = []
        
        # Meal reminders based on patterns
        schedule.append({
            "type": "meal_reminder",
            "time": f"{typical_breakfast:02d}:00",
            "message": "Time for a nutritious breakfast!",
            "priority": "high",
            "adaptive": True,
            "note": f"Based on your usual breakfast time around {typical_breakfast}:00"
        })
        
        schedule.append({
            "type": "meal_reminder",
            "time": f"{typical_lunch:02d}:00",
            "message": "Lunch time! Don't skip meals to maintain energy.",
            "priority": "medium",
            "adaptive": True,
            "note": f"Based on your usual lunch time around {typical_lunch}:00"
        })
        
        schedule.append({
            "type": "meal_reminder",
            "time": f"{typical_dinner:02d}:00",
            "message": "Time for dinner. Keep it balanced!",
            "priority": "medium",
            "adaptive": True,
            "note": f"Based on your usual dinner time around {typical_dinner}:00"
        })
        
        # Hydration reminders (every 2 hours during active hours)
        for hour in range(8, 20, 2):
            schedule.append({
                "type": "hydration_reminder",
                "time": f"{hour:02d}:00",
                "message": "💧 Time to hydrate! Drink a glass of water.",
                "priority": "low",
                "adaptive": False
            })
        
        # Pre-workout reminder
        pre_workout_hour = (typical_workout_hour - 1) % 24
        schedule.append({
            "type": "workout_reminder",
            "time": f"{pre_workout_hour:02d}:30",
            "message": "Workout coming up! Have a light snack if needed.",
            "priority": "medium",
            "adaptive": True,
            "note": f"30 min before your typical workout at {typical_workout_hour}:00"
        })
        
        # Workout reminder
        schedule.append({
            "type": "workout_reminder",
            "time": f"{typical_workout_hour:02d}:00",
            "message": "🏋️ Time for your workout! Let's crush it!",
            "priority": "high",
            "adaptive": True,
            "note": f"Based on your usual workout time around {typical_workout_hour}:00"
        })
        
        # Evening wind-down
        schedule.append({
            "type": "wellness_reminder",
            "time": "21:00",
            "message": "Wind down time. Consider light stretching and hydration.",
            "priority": "low",
            "adaptive": False
        })
        
        # Sort by time
        schedule.sort(key=lambda x: x["time"])
        
        return {
            "user_id": user_id,
            "schedule": schedule,
            "insights": {
                "meal_pattern_detected": len(recent_meals) > 0,
                "workout_pattern_detected": len(recent_workouts) > 0,
                "typical_breakfast_time": f"{typical_breakfast:02d}:00",
                "typical_workout_time": f"{typical_workout_hour:02d}:00",
                "schedule_confidence": "high" if len(recent_meals) > 10 else "medium"
            },
            "note": "Schedule adapts based on your activity patterns. More data improves accuracy."
        }
        
    except Exception as e:
        logger.error(f"Notification schedule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cycle-notifications/{user_id}")
def get_cycle_notifications(
    user_id: str,
    db: Session = Depends(database.get_db),
):
    """
    Get menstrual cycle-aware notifications for female users.
    Provides phase-specific reminders and tips.
    """
    try:
        # Check if user has FemmeCare enabled
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == user_id
        ).first()
        
        if not profile or not profile.femmecare_enabled:
            return {
                "user_id": user_id,
                "femmecare_enabled": False,
                "message": "Enable FemmeCare in settings to receive cycle-aware notifications"
            }
        
        # Get latest cycle entry
        latest_entry = db.query(models.FemaleCycleEntry).filter(
            models.FemaleCycleEntry.user_id == user_id
        ).order_by(desc(models.FemaleCycleEntry.date)).first()
        
        # Get menstrual cycle log
        latest_cycle = db.query(models.MenstrualCycleLog).filter(
            models.MenstrualCycleLog.user_id == user_id
        ).order_by(desc(models.MenstrualCycleLog.start_date)).first()
        
        current_phase = latest_entry.phase if latest_entry else "unknown"
        cycle_day = None
        
        if latest_cycle and latest_cycle.start_date:
            days_since_start = (datetime.utcnow() - latest_cycle.start_date).days
            cycle_length = latest_cycle.cycle_length_days or 28
            cycle_day = (days_since_start % cycle_length) + 1
            
            # Determine phase based on cycle day
            if cycle_day <= 5:
                current_phase = "menstrual"
            elif cycle_day <= 13:
                current_phase = "follicular"
            elif cycle_day <= 17:
                current_phase = "ovulatory"
            else:
                current_phase = "luteal"
        
        # Phase-specific notifications
        phase_notifications = {
            "menstrual": [
                {
                    "type": "wellness",
                    "message": "💗 Menstrual phase: Focus on rest and iron-rich foods",
                    "tips": [
                        "Stay hydrated to reduce bloating",
                        "Light exercise like yoga or walking",
                        "Increase iron intake (spinach, red meat, lentils)",
                        "Magnesium can help with cramps"
                    ]
                },
                {
                    "type": "nutrition",
                    "message": "Nutrition tip: Boost iron and B-vitamins",
                    "recommendations": ["Dark leafy greens", "Red meat", "Lentils", "Dark chocolate"]
                }
            ],
            "follicular": [
                {
                    "type": "energy",
                    "message": "⚡ Follicular phase: High energy period - great time for intense workouts!",
                    "tips": [
                        "Energy levels are rising",
                        "Perfect for trying new exercises",
                        "Focus on strength training",
                        "Social activities feel easier"
                    ]
                },
                {
                    "type": "workout",
                    "message": "Workout boost: Your body is primed for high-intensity training",
                    "recommendations": ["HIIT workouts", "Heavy lifting", "New PR attempts"]
                }
            ],
            "ovulatory": [
                {
                    "type": "peak",
                    "message": "🌟 Ovulatory phase: Peak energy and strength!",
                    "tips": [
                        "Peak physical performance window",
                        "Maximum strength potential",
                        "High confidence and social energy",
                        "Great time for competitions or PR attempts"
                    ]
                },
                {
                    "type": "nutrition",
                    "message": "Nutrition focus: Support hormone balance",
                    "recommendations": ["Fiber-rich foods", "Antioxidants", "Healthy fats"]
                }
            ],
            "luteal": [
                {
                    "type": "adjustment",
                    "message": "🌙 Luteal phase: Listen to your body, adjust intensity",
                    "tips": [
                        "Energy may fluctuate",
                        "Focus on moderate-intensity workouts",
                        "Prioritize sleep and recovery",
                        "Manage stress with meditation"
                    ]
                },
                {
                    "type": "nutrition",
                    "message": "Nutrition tip: Complex carbs help stabilize mood",
                    "recommendations": ["Sweet potatoes", "Quinoa", "Oats", "Magnesium-rich foods"]
                }
            ]
        }
        
        notifications = phase_notifications.get(current_phase, [])
        
        # Add phase transition notification if approaching new phase
        next_phase_day = None
        if cycle_day:
            if current_phase == "menstrual" and cycle_day >= 4:
                next_phase_day = 6
                notifications.append({
                    "type": "transition",
                    "message": f"Follicular phase approaching in {next_phase_day - cycle_day} days",
                    "preparation": "Energy will start increasing soon"
                })
            elif current_phase == "follicular" and cycle_day >= 12:
                next_phase_day = 14
                notifications.append({
                    "type": "transition",
                    "message": f"Ovulation approaching in {next_phase_day - cycle_day} days",
                    "preparation": "Peak performance window coming"
                })
        
        return {
            "user_id": user_id,
            "femmecare_enabled": True,
            "current_phase": current_phase,
            "cycle_day": cycle_day,
            "notifications": notifications,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cycle notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
def send_notification(
    notification: dict = Body(...),
    db: Session = Depends(database.get_db),
):
    """
    Send a notification to a user and log it.
    """
    try:
        user_id = notification.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        # Create notification log
        notif_log = models.NotificationLog(
            user_id=user_id,
            title=notification.get("title", "Smarty Notification"),
            body=notification.get("body", ""),
            icon=notification.get("icon", "bell"),
            source=notification.get("source", "system"),
            read=False
        )
        
        db.add(notif_log)
        db.commit()
        db.refresh(notif_log)
        
        return {
            "notification_id": notif_log.id,
            "sent": True,
            "user_id": user_id,
            "timestamp": notif_log.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
def get_notification_history(
    user_id: str,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(database.get_db),
):
    """
    Get notification history for a user.
    """
    try:
        query = db.query(models.NotificationLog).filter(
            models.NotificationLog.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(models.NotificationLog.read == False)
        
        notifications = query.order_by(
            desc(models.NotificationLog.created_at)
        ).limit(limit).all()
        
        return {
            "user_id": user_id,
            "count": len(notifications),
            "unread_count": sum(1 for n in notifications if not n.read),
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "body": n.body,
                    "icon": n.icon,
                    "source": n.source,
                    "read": n.read,
                    "created_at": n.created_at.isoformat()
                }
                for n in notifications
            ]
        }
        
    except Exception as e:
        logger.error(f"Notification history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-read/{notification_id}")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(database.get_db),
):
    """
    Mark a notification as read.
    """
    try:
        notification = db.query(models.NotificationLog).filter(
            models.NotificationLog.id == notification_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification.read = True
        db.commit()
        
        return {
            "notification_id": notification_id,
            "marked_read": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
