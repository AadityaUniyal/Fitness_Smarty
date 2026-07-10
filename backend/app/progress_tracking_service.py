"""
Progress Tracking Service

Comprehensive progress tracking with:
- Weight history
- Body measurements
- Progress photos
- Trend analysis
- Goal progress visualization data
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app import models
import logging

logger = logging.getLogger(__name__)


class ProgressTrackingService:
    """Service for comprehensive progress tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_weight(
        self,
        user_id: int,
        weight_kg: float,
        measured_at: Optional[datetime] = None
    ) -> models.BiometricReading:
        """
        Log weight measurement.
        
        Args:
            user_id: User ID
            weight_kg: Weight in kilograms
            measured_at: When measurement was taken (defaults to now)
        
        Returns:
            Created BiometricReading
        """
        if not measured_at:
            measured_at = datetime.utcnow()
        
        reading = models.BiometricReading(
            user_id=user_id,
            weight_kg=weight_kg,
            created_at=measured_at
        )
        
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        
        # Also update user's current weight
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        if user:
            user.weight_kg = weight_kg
            self.db.commit()
        
        return reading
    
    def log_measurements(
        self,
        user_id: int,
        measurements: Dict[str, float],
        measured_at: Optional[datetime] = None
    ) -> models.ProgressSnapshot:
        """
        Log body measurements.
        
        Args:
            user_id: User ID
            measurements: Dict like {"chest_cm": 100, "waist_cm": 85, "arms_cm": 35}
            measured_at: When measurement was taken
        
        Returns:
            Created ProgressSnapshot
        """
        if not measured_at:
            measured_at = datetime.utcnow()
        
        snapshot = models.ProgressSnapshot(
            user_id=user_id,
            date=measured_at,
            measurements=measurements
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    def get_weight_history(
        self,
        user_id: int,
        days: int = 90
    ) -> Dict:
        """
        Get weight history for visualization.
        
        Args:
            user_id: User ID
            days: Number of days to retrieve
        
        Returns:
            Dictionary with weight history and trend analysis
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        readings = self.db.query(models.BiometricReading).filter(
            models.BiometricReading.user_id == user_id,
            models.BiometricReading.weight_kg.isnot(None),
            models.BiometricReading.created_at >= start_date
        ).order_by(models.BiometricReading.created_at).all()
        
        if not readings:
            return {
                "user_id": user_id,
                "has_data": False,
                "message": "No weight data logged yet. Start tracking your weight!"
            }
        
        # Format for chart
        chart_data = [
            {
                "date": reading.created_at.strftime("%Y-%m-%d"),
                "weight_kg": float(reading.weight_kg),
                "timestamp": reading.created_at.isoformat()
            }
            for reading in readings
        ]
        
        # Calculate trends
        weights = [r.weight_kg for r in readings]
        start_weight = weights[0]
        current_weight = weights[-1]
        weight_change = current_weight - start_weight
        
        # Calculate average weekly change
        weeks = len(readings) / 7 if len(readings) > 7 else 1
        avg_weekly_change = weight_change / weeks if weeks > 0 else 0
        
        # Determine trend
        if weight_change < -0.5:
            trend = "losing"
            trend_emoji = "📉"
        elif weight_change > 0.5:
            trend = "gaining"
            trend_emoji = "📈"
        else:
            trend = "maintaining"
            trend_emoji = "➡️"
        
        # Calculate highest and lowest
        highest = max(weights)
        lowest = min(weights)
        
        return {
            "user_id": user_id,
            "has_data": True,
            "period_days": days,
            "total_readings": len(readings),
            "chart_data": chart_data,
            "summary": {
                "start_weight_kg": round(start_weight, 1),
                "current_weight_kg": round(current_weight, 1),
                "weight_change_kg": round(weight_change, 1),
                "highest_weight_kg": round(highest, 1),
                "lowest_weight_kg": round(lowest, 1),
                "avg_weekly_change_kg": round(avg_weekly_change, 2),
                "trend": trend,
                "trend_emoji": trend_emoji
            }
        }
    
    def get_measurement_history(
        self,
        user_id: int,
        days: int = 90
    ) -> Dict:
        """
        Get body measurement history.
        
        Args:
            user_id: User ID
            days: Number of days to retrieve
        
        Returns:
            Dictionary with measurement history
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.db.query(models.ProgressSnapshot).filter(
            models.ProgressSnapshot.user_id == user_id,
            models.ProgressSnapshot.date >= start_date,
            models.ProgressSnapshot.measurements.isnot(None)
        ).order_by(models.ProgressSnapshot.date).all()
        
        if not snapshots:
            return {
                "user_id": user_id,
                "has_data": False,
                "message": "No measurements logged yet."
            }
        
        # Organize data by measurement type
        measurements_by_type = {}
        all_measurements = []
        
        for snapshot in snapshots:
            measurements = snapshot.measurements or {}
            entry = {
                "date": snapshot.date.strftime("%Y-%m-%d"),
                "measurements": measurements
            }
            all_measurements.append(entry)
            
            for measure_name, value in measurements.items():
                if measure_name not in measurements_by_type:
                    measurements_by_type[measure_name] = []
                
                measurements_by_type[measure_name].append({
                    "date": snapshot.date.strftime("%Y-%m-%d"),
                    "value": value
                })
        
        # Calculate changes for each measurement
        changes = {}
        for measure_name, data_points in measurements_by_type.items():
            if len(data_points) >= 2:
                first = data_points[0]["value"]
                last = data_points[-1]["value"]
                change = last - first
                changes[measure_name] = {
                    "start": first,
                    "current": last,
                    "change": round(change, 1),
                    "change_percentage": round((change / first) * 100, 1) if first > 0 else 0
                }
        
        return {
            "user_id": user_id,
            "has_data": True,
            "period_days": days,
            "total_snapshots": len(snapshots),
            "all_measurements": all_measurements,
            "measurements_by_type": measurements_by_type,
            "changes": changes
        }
    
    def get_comprehensive_progress(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict:
        """
        Get comprehensive progress report.
        
        Combines:
        - Weight trends
        - Body measurements
        - Calorie tracking statistics
        - Workout statistics
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Comprehensive progress report
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Weight data
        weight_history = self.get_weight_history(user_id, days)
        
        # Measurement data
        measurement_history = self.get_measurement_history(user_id, days)
        
        # Calorie statistics
        meal_logs = self.db.query(models.MealLog).filter(
            models.MealLog.user_id == user_id,
            models.MealLog.created_at >= start_date
        ).all()
        
        workout_logs = self.db.query(models.WorkoutLog).filter(
            models.WorkoutLog.user_id == user_id,
            models.WorkoutLog.created_at >= start_date
        ).all()
        
        total_calories_consumed = sum(log.total_calories for log in meal_logs)
        total_calories_burned = sum(log.calories_burned for log in workout_logs)
        total_workouts = len(workout_logs)
        total_meals_logged = len(meal_logs)
        
        avg_daily_consumed = total_calories_consumed / days if days > 0 else 0
        avg_daily_burned = total_calories_burned / days if days > 0 else 0
        
        # Calculate consistency
        logged_days = len(set([log.created_at.date() for log in meal_logs + workout_logs]))
        consistency_percentage = (logged_days / days) * 100 if days > 0 else 0
        
        return {
            "user_id": user_id,
            "period_days": days,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "weight_progress": weight_history.get("summary", {}),
            "measurement_progress": measurement_history.get("changes", {}),
            "nutrition_stats": {
                "total_calories_consumed": round(total_calories_consumed, 0),
                "avg_daily_calories": round(avg_daily_consumed, 0),
                "total_meals_logged": total_meals_logged
            },
            "workout_stats": {
                "total_calories_burned": round(total_calories_burned, 0),
                "avg_daily_burn": round(avg_daily_burned, 0),
                "total_workouts": total_workouts
            },
            "consistency": {
                "days_logged": logged_days,
                "consistency_percentage": round(consistency_percentage, 1),
                "rating": self._get_consistency_rating(consistency_percentage)
            }
        }
    
    def _get_consistency_rating(self, percentage: float) -> str:
        """Get consistency rating based on percentage"""
        if percentage >= 90:
            return "🔥 Excellent! You're crushing it!"
        elif percentage >= 70:
            return "💪 Great consistency!"
        elif percentage >= 50:
            return "👍 Good, keep it up!"
        elif percentage >= 30:
            return "⚠️ Room for improvement"
        else:
            return "📝 Start tracking more consistently"
    
    def get_goal_progress_visualization(
        self,
        user_id: int
    ) -> Dict:
        """
        Get goal progress data for visualization.
        
        Returns:
            Progress towards goals with percentage completion
        """
        # Get active goals
        goals = self.db.query(models.UserGoal).filter(
            models.UserGoal.user_id == str(user_id),
            models.UserGoal.is_active == True
        ).all()
        
        if not goals:
            return {
                "user_id": user_id,
                "has_goals": False,
                "message": "No active goals set. Create a goal to track progress!"
            }
        
        progress_data = []
        
        for goal in goals:
            target = float(goal.target_value or 0)
            current = float(goal.current_value or 0)
            start = current  # Could track start value in future
            
            if target > 0:
                progress_pct = (current / target) * 100
            else:
                progress_pct = 0
            
            # Calculate days progress
            days_elapsed = (datetime.utcnow() - goal.start_date).days if goal.start_date else 0
            days_total = (goal.target_date - goal.start_date).days if goal.target_date and goal.start_date else 0
            days_remaining = (goal.target_date - datetime.utcnow()).days if goal.target_date else None
            
            time_progress_pct = (days_elapsed / days_total * 100) if days_total > 0 else 0
            
            # Determine if on track
            on_track = progress_pct >= time_progress_pct if time_progress_pct > 0 else True
            
            progress_data.append({
                "goal_id": goal.id,
                "goal_type": goal.goal_type,
                "target_value": target,
                "current_value": current,
                "progress_percentage": round(min(progress_pct, 100), 1),
                "time_progress_percentage": round(time_progress_pct, 1),
                "on_track": on_track,
                "days_remaining": days_remaining,
                "status": "✅ On track!" if on_track else "⚠️ Behind schedule"
            })
        
        return {
            "user_id": user_id,
            "has_goals": True,
            "total_goals": len(goals),
            "goals_progress": progress_data
        }
    
    def get_trends_visualization(
        self,
        user_id: int,
        metric: str = "weight",
        days: int = 90
    ) -> Dict:
        """
        Get trend visualization data for charts.
        
        Args:
            user_id: User ID
            metric: Metric to visualize (weight, calories, workout_frequency)
            days: Number of days
        
        Returns:
            Trend data formatted for chart libraries
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        if metric == "weight":
            return self.get_weight_history(user_id, days)
        
        elif metric == "calories":
            # Get daily calorie data
            meal_logs = self.db.query(
                func.date(models.MealLog.created_at).label('date'),
                func.sum(models.MealLog.total_calories).label('consumed')
            ).filter(
                models.MealLog.user_id == user_id,
                models.MealLog.created_at >= start_date
            ).group_by(func.date(models.MealLog.created_at)).all()
            
            workout_logs = self.db.query(
                func.date(models.WorkoutLog.created_at).label('date'),
                func.sum(models.WorkoutLog.calories_burned).label('burned')
            ).filter(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= start_date
            ).group_by(func.date(models.WorkoutLog.created_at)).all()
            
            # Combine data
            data_by_date = {}
            
            for log in meal_logs:
                date_str = str(log.date)
                data_by_date[date_str] = {
                    "date": date_str,
                    "consumed": float(log.consumed or 0),
                    "burned": 0,
                    "net": 0
                }
            
            for log in workout_logs:
                date_str = str(log.date)
                if date_str not in data_by_date:
                    data_by_date[date_str] = {
                        "date": date_str,
                        "consumed": 0,
                        "burned": 0,
                        "net": 0
                    }
                data_by_date[date_str]["burned"] = float(log.burned or 0)
            
            # Calculate net
            for date_str in data_by_date:
                data_by_date[date_str]["net"] = (
                    data_by_date[date_str]["consumed"] - 
                    data_by_date[date_str]["burned"]
                )
            
            chart_data = sorted(data_by_date.values(), key=lambda x: x["date"])
            
            return {
                "user_id": user_id,
                "metric": "calories",
                "period_days": days,
                "chart_data": chart_data
            }
        
        elif metric == "workout_frequency":
            # Get workout frequency by day
            workouts = self.db.query(
                func.date(models.WorkoutLog.created_at).label('date'),
                func.count(models.WorkoutLog.id).label('count')
            ).filter(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= start_date
            ).group_by(func.date(models.WorkoutLog.created_at)).all()
            
            chart_data = [
                {
                    "date": str(workout.date),
                    "workouts": workout.count
                }
                for workout in workouts
            ]
            
            return {
                "user_id": user_id,
                "metric": "workout_frequency",
                "period_days": days,
                "chart_data": chart_data,
                "total_workouts": sum(w.count for w in workouts)
            }
        
        else:
            raise ValueError(f"Unknown metric: {metric}")
