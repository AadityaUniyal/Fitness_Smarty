"""
Hydration Tracking Service

Tracks water intake, calculates daily hydration goals,
and provides insights for optimal hydration.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from .models import EnhancedUser as User, WorkoutLog
from .database import Base
from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey


class HydrationLog(Base):
    """Model for tracking daily hydration"""
    __tablename__ = "hydration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today)
    water_ml = Column(Float)  # Water intake in milliliters
    glasses = Column(Float)  # Equivalent glasses (250ml each)
    logged_at = Column(DateTime, default=datetime.now)


class HydrationService:
    """Service for managing hydration tracking and goals"""
    
    def __init__(self, db: Session):
        self.db = db
        self.glass_size_ml = 250  # Standard glass size
    
    def log_water(
        self, 
        user_id: int, 
        amount_ml: Optional[float] = None,
        glasses: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Log water intake
        
        Args:
            user_id: User ID
            amount_ml: Water amount in milliliters
            glasses: Water amount in glasses (250ml each)
        
        Either amount_ml or glasses must be provided.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Calculate both ml and glasses
        if amount_ml:
            ml = amount_ml
            glass_count = amount_ml / self.glass_size_ml
        elif glasses:
            glass_count = glasses
            ml = glasses * self.glass_size_ml
        else:
            return {"error": "Must provide either amount_ml or glasses"}
        
        # Check if log exists for today
        today = date.today()
        existing_log = self.db.query(HydrationLog).filter(
            and_(
                HydrationLog.user_id == user_id,
                HydrationLog.date == today
            )
        ).first()
        
        if existing_log:
            # Update existing log
            existing_log.water_ml += ml
            existing_log.glasses += glass_count
            existing_log.logged_at = datetime.now()
        else:
            # Create new log
            new_log = HydrationLog(
                user_id=user_id,
                date=today,
                water_ml=ml,
                glasses=glass_count
            )
            self.db.add(new_log)
        
        self.db.commit()
        
        # Get updated daily summary
        daily_summary = self.get_daily_summary(user_id)
        
        return {
            "success": True,
            "logged_ml": ml,
            "logged_glasses": round(glass_count, 1),
            "daily_summary": daily_summary
        }
    
    def get_daily_summary(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Get hydration summary for a specific day"""
        if not target_date:
            target_date = date.today()
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get today's hydration log
        log = self.db.query(HydrationLog).filter(
            and_(
                HydrationLog.user_id == user_id,
                HydrationLog.date == target_date
            )
        ).first()
        
        current_ml = log.water_ml if log else 0
        current_glasses = log.glasses if log else 0
        
        # Calculate daily goal
        goal_data = self.calculate_daily_goal(user_id, target_date)
        goal_ml = goal_data["goal_ml"]
        goal_glasses = goal_data["goal_glasses"]
        
        # Calculate progress
        progress_percentage = min(100, (current_ml / goal_ml * 100)) if goal_ml > 0 else 0
        remaining_ml = max(0, goal_ml - current_ml)
        remaining_glasses = max(0, goal_glasses - current_glasses)
        
        # Generate status message
        if progress_percentage >= 100:
            status = "goal_achieved"
            message = "🎉 Great job! You've hit your hydration goal!"
        elif progress_percentage >= 75:
            status = "almost_there"
            message = f"Almost there! Just {round(remaining_glasses, 1)} more glasses to go!"
        elif progress_percentage >= 50:
            status = "on_track"
            message = f"You're doing well! {round(remaining_glasses, 1)} glasses remaining."
        elif progress_percentage >= 25:
            status = "needs_attention"
            message = f"Don't forget to hydrate! {round(remaining_glasses, 1)} glasses needed."
        else:
            status = "just_started"
            message = f"Time to start hydrating! Aim for {round(goal_glasses, 1)} glasses today."
        
        return {
            "date": str(target_date),
            "current_ml": round(current_ml, 1),
            "current_glasses": round(current_glasses, 1),
            "goal_ml": round(goal_ml, 1),
            "goal_glasses": round(goal_glasses, 1),
            "progress_percentage": round(progress_percentage, 1),
            "remaining_ml": round(remaining_ml, 1),
            "remaining_glasses": round(remaining_glasses, 1),
            "status": status,
            "message": message,
            "last_logged": log.logged_at.strftime("%I:%M %p") if log else None
        }
    
    def calculate_daily_goal(self, user_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate daily hydration goal based on:
        - Body weight (30-35ml per kg)
        - Activity level (add 500ml per workout)
        - Gender (males typically need more)
        - Climate (can be adjusted)
        """
        if not target_date:
            target_date = date.today()
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Base calculation: 35ml per kg of body weight
        base_ml = user.weight * 35
        
        # Check if user worked out today
        workout = self.db.query(WorkoutLog).filter(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date == target_date
            )
        ).first()
        
        # Add 500ml per workout (to replace sweat loss)
        workout_bonus_ml = 500 if workout else 0
        
        # Gender adjustment (males typically need slightly more)
        gender_multiplier = 1.1 if user.gender == "male" else 1.0
        
        # Total goal
        total_ml = (base_ml + workout_bonus_ml) * gender_multiplier
        total_glasses = total_ml / self.glass_size_ml
        
        return {
            "goal_ml": round(total_ml, 1),
            "goal_glasses": round(total_glasses, 1),
            "base_ml": round(base_ml, 1),
            "workout_bonus_ml": workout_bonus_ml,
            "factors": {
                "weight_kg": user.weight,
                "workout_today": workout is not None,
                "gender": user.gender
            },
            "recommendation": self._get_hydration_recommendation(total_glasses)
        }
    
    def get_weekly_trends(self, user_id: int) -> Dict[str, Any]:
        """Get hydration trends for the past 7 days"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get last 7 days of logs
        seven_days_ago = date.today() - timedelta(days=6)
        logs = self.db.query(HydrationLog).filter(
            and_(
                HydrationLog.user_id == user_id,
                HydrationLog.date >= seven_days_ago
            )
        ).order_by(HydrationLog.date).all()
        
        # Create daily data
        daily_data = []
        total_ml = 0
        days_goal_met = 0
        
        for i in range(7):
            check_date = date.today() - timedelta(days=6-i)
            log = next((l for l in logs if l.date == check_date), None)
            
            goal_data = self.calculate_daily_goal(user_id, check_date)
            goal_ml = goal_data["goal_ml"]
            
            current_ml = log.water_ml if log else 0
            total_ml += current_ml
            
            achieved = current_ml >= goal_ml
            if achieved:
                days_goal_met += 1
            
            daily_data.append({
                "date": str(check_date),
                "day_name": check_date.strftime("%A"),
                "water_ml": round(current_ml, 1),
                "glasses": round(current_ml / self.glass_size_ml, 1),
                "goal_ml": round(goal_ml, 1),
                "goal_achieved": achieved,
                "percentage": round(min(100, current_ml / goal_ml * 100), 1) if goal_ml > 0 else 0
            })
        
        # Calculate averages
        avg_ml = total_ml / 7
        avg_glasses = avg_ml / self.glass_size_ml
        consistency_score = (days_goal_met / 7) * 100
        
        return {
            "period": "last_7_days",
            "daily_data": daily_data,
            "summary": {
                "total_ml": round(total_ml, 1),
                "average_ml_per_day": round(avg_ml, 1),
                "average_glasses_per_day": round(avg_glasses, 1),
                "days_goal_met": days_goal_met,
                "consistency_score": round(consistency_score, 1),
                "trend": self._analyze_trend(daily_data)
            }
        }
    
    def get_hydration_reminders(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized hydration reminders
        """
        daily_summary = self.get_daily_summary(user_id)
        
        if "error" in daily_summary:
            return daily_summary
        
        current_hour = datetime.now().hour
        progress = daily_summary["progress_percentage"]
        
        reminders = []
        
        # Morning reminder (6am-12pm)
        if 6 <= current_hour < 12:
            if progress < 25:
                reminders.append({
                    "time": "morning",
                    "message": "Start your day with 2 glasses of water! ☀️",
                    "glasses": 2
                })
        
        # Afternoon reminder (12pm-5pm)
        elif 12 <= current_hour < 17:
            if progress < 50:
                reminders.append({
                    "time": "afternoon",
                    "message": "Halfway through the day - stay hydrated! 💧",
                    "glasses": 2
                })
        
        # Evening reminder (5pm-9pm)
        elif 17 <= current_hour < 21:
            if progress < 75:
                reminders.append({
                    "time": "evening",
                    "message": "Evening hydration check! Don't forget to drink water. 🌙",
                    "glasses": 1
                })
        
        # Before bed (9pm+)
        else:
            if progress < 100:
                reminders.append({
                    "time": "night",
                    "message": "One more glass before bed to meet your goal! 🛌",
                    "glasses": 1
                })
        
        return {
            "current_time": datetime.now().strftime("%I:%M %p"),
            "current_progress": daily_summary["progress_percentage"],
            "reminders": reminders,
            "motivational_message": self._get_motivational_message(progress)
        }
    
    def _get_hydration_recommendation(self, glasses: float) -> str:
        """Get recommendation based on goal"""
        if glasses < 6:
            return "Aim to drink water consistently throughout the day"
        elif glasses < 8:
            return "Good goal! Spread your intake evenly across the day"
        elif glasses < 12:
            return "Great goal! Consider drinking more after workouts"
        else:
            return "High goal - make sure you're drinking comfortably"
    
    def _analyze_trend(self, daily_data: List[Dict]) -> str:
        """Analyze if hydration is improving or declining"""
        if len(daily_data) < 3:
            return "insufficient_data"
        
        # Compare first half vs second half
        first_half_avg = sum(d["water_ml"] for d in daily_data[:3]) / 3
        second_half_avg = sum(d["water_ml"] for d in daily_data[4:]) / 3
        
        if second_half_avg > first_half_avg * 1.1:
            return "improving"
        elif second_half_avg < first_half_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _get_motivational_message(self, progress: float) -> str:
        """Get motivational message based on progress"""
        if progress >= 100:
            return "Amazing! You're fully hydrated! 🌊"
        elif progress >= 75:
            return "You're so close! Keep it up! 💪"
        elif progress >= 50:
            return "Halfway there! You're doing great! ⭐"
        elif progress >= 25:
            return "Good start! Keep drinking throughout the day! 🚰"
        else:
            return "Remember: Your body needs water to perform at its best! 💧"
