"""
Calorie Tracker Service

Comprehensive calorie tracking with automatic calculations for:
1. Exercise calories burned (from Neon database)
2. Food calories consumed (from Neon database)
3. Net daily calories (consumed - burned)
4. Daily progress tracking
5. Gender-specific calculations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
import logging

logger = logging.getLogger(__name__)


class CalorieTrackerService:
    """Service for automatic calorie tracking and calculations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_exercise_calories(
        self,
        exercise_id: int,
        duration_minutes: Optional[int] = None,
        reps: Optional[int] = None,
        sets: Optional[int] = 1
    ) -> Dict:
        """
        Calculate calories burned for an exercise based on quantity.
        
        Args:
            exercise_id: ID of the exercise from database
            duration_minutes: Duration in minutes (for cardio/timed exercises)
            reps: Number of repetitions (for strength exercises)
            sets: Number of sets (default 1)
        
        Returns:
            Dictionary with exercise details and calculated calories
        """
        exercise = self.db.query(models.ExerciseItem).filter(
            models.ExerciseItem.id == exercise_id
        ).first()
        
        if not exercise:
            raise ValueError(f"Exercise with ID {exercise_id} not found")
        
        calories_burned = 0
        calculation_type = ""
        
        # Calculate based on available metrics
        if duration_minutes and exercise.calories_per_min:
            calories_burned = duration_minutes * exercise.calories_per_min
            calculation_type = "time_based"
        elif reps and exercise.calories_per_rep:
            calories_burned = reps * sets * exercise.calories_per_rep
            calculation_type = "rep_based"
        elif duration_minutes:
            # Fallback to default calorie burn rate
            calories_burned = duration_minutes * 5.0
            calculation_type = "time_based_default"
        else:
            raise ValueError("Either duration_minutes or reps must be provided")
        
        return {
            "exercise_id": exercise.id,
            "exercise_name": exercise.name,
            "category": exercise.category.name if exercise.category else None,
            "targeted_muscle": exercise.targeted_muscle,
            "duration_minutes": duration_minutes,
            "reps": reps,
            "sets": sets,
            "calories_burned": round(calories_burned, 1),
            "calculation_type": calculation_type
        }
    
    def calculate_food_calories(
        self,
        food_id: int,
        quantity_grams: float
    ) -> Dict:
        """
        Calculate calories and macros for a food item based on quantity.
        
        Args:
            food_id: ID of the food from database
            quantity_grams: Quantity in grams
        
        Returns:
            Dictionary with food details and calculated nutrition
        """
        food = self.db.query(models.FoodItem).filter(
            models.FoodItem.id == food_id
        ).first()
        
        if not food:
            raise ValueError(f"Food with ID {food_id} not found")
        
        # All food items are stored per 100g, so calculate ratio
        ratio = quantity_grams / 100.0
        
        return {
            "food_id": food.id,
            "food_name": food.name,
            "category": food.category.name if food.category else None,
            "quantity_grams": quantity_grams,
            "calories": round((food.calories or 0) * ratio, 1),
            "protein_g": round((food.protein or 0) * ratio, 1),
            "carbs_g": round((food.carbs or 0) * ratio, 1),
            "fat_g": round((food.fats or 0) * ratio, 1),
            "is_elite": food.is_elite or False
        }
    
    def log_exercise_with_calories(
        self,
        user_id: int,
        exercises: List[Dict],
        workout_name: Optional[str] = None
    ) -> models.WorkoutLog:
        """
        Log a workout with automatic calorie calculation.
        
        Args:
            user_id: User ID
            exercises: List of exercise dicts with {exercise_id, duration_minutes?, reps?, sets?}
            workout_name: Optional workout name
        
        Returns:
            Created WorkoutLog with calculated calories
        """
        total_calories = 0
        total_duration = 0
        exercise_details = []
        
        # Calculate calories for each exercise
        for ex_data in exercises:
            try:
                calculated = self.calculate_exercise_calories(
                    exercise_id=ex_data['exercise_id'],
                    duration_minutes=ex_data.get('duration_minutes'),
                    reps=ex_data.get('reps'),
                    sets=ex_data.get('sets', 1)
                )
                
                total_calories += calculated['calories_burned']
                if calculated['duration_minutes']:
                    total_duration += calculated['duration_minutes']
                
                exercise_details.append(calculated)
                
            except Exception as e:
                logger.error(f"Error calculating calories for exercise: {e}")
                continue
        
        # Create workout log
        workout_log = models.WorkoutLog(
            user_id=user_id,
            workout_name=workout_name or f"Workout on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            duration_minutes=total_duration or 30,  # Default if no duration
            calories_burned=round(total_calories, 1),
            exercises_data=exercise_details,
            created_at=datetime.utcnow()
        )
        
        self.db.add(workout_log)
        self.db.commit()
        self.db.refresh(workout_log)
        
        return workout_log
    
    def log_food_with_calories(
        self,
        user_id: int,
        foods: List[Dict],
        meal_name: Optional[str] = None,
        meal_type: Optional[str] = None
    ) -> models.MealLog:
        """
        Log a meal with automatic calorie calculation.
        
        Args:
            user_id: User ID
            foods: List of food dicts with {food_id, quantity_grams}
            meal_name: Optional meal name
            meal_type: Optional meal type (breakfast, lunch, dinner, snack)
        
        Returns:
            Created MealLog with calculated nutrition
        """
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        food_details = []
        
        # Calculate nutrition for each food item
        for food_data in foods:
            try:
                calculated = self.calculate_food_calories(
                    food_id=food_data['food_id'],
                    quantity_grams=food_data['quantity_grams']
                )
                
                total_calories += calculated['calories']
                total_protein += calculated['protein_g']
                total_carbs += calculated['carbs_g']
                total_fats += calculated['fat_g']
                
                food_details.append(calculated)
                
            except Exception as e:
                logger.error(f"Error calculating calories for food: {e}")
                continue
        
        # Create meal log
        meal_log = models.MealLog(
            user_id=user_id,
            meal_name=meal_name or f"{meal_type or 'Meal'} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fats=round(total_fats, 1),
            detected_foods=food_details,
            created_at=datetime.utcnow()
        )
        
        self.db.add(meal_log)
        self.db.commit()
        self.db.refresh(meal_log)
        
        return meal_log
    
    def get_daily_calorie_summary(
        self,
        user_id: int,
        target_date: Optional[date] = None
    ) -> Dict:
        """
        Get complete calorie summary for a day with net calories.
        
        Args:
            user_id: User ID
            target_date: Date to get summary for (defaults to today)
        
        Returns:
            Dictionary with consumed, burned, and net calories
        """
        if not target_date:
            target_date = date.today()
        
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Get consumed calories from meals
        meal_logs = self.db.query(models.MealLog).filter(
            models.MealLog.user_id == user_id,
            models.MealLog.created_at >= start_datetime,
            models.MealLog.created_at <= end_datetime
        ).all()
        
        calories_consumed = sum(log.total_calories for log in meal_logs)
        protein_consumed = sum(log.total_protein for log in meal_logs)
        carbs_consumed = sum(log.total_carbs for log in meal_logs)
        fats_consumed = sum(log.total_fats for log in meal_logs)
        
        # Get burned calories from workouts
        workout_logs = self.db.query(models.WorkoutLog).filter(
            models.WorkoutLog.user_id == user_id,
            models.WorkoutLog.created_at >= start_datetime,
            models.WorkoutLog.created_at <= end_datetime
        ).all()
        
        calories_burned = sum(log.calories_burned for log in workout_logs)
        total_exercise_duration = sum(log.duration_minutes for log in workout_logs)
        
        # Get user's daily target from profile
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == str(user_id)
        ).first()
        
        daily_calorie_target = (profile.daily_calorie_target if profile and profile.daily_calorie_target 
                               else 2200.0)
        
        # Calculate net calories
        net_calories = calories_consumed - calories_burned
        calories_remaining = daily_calorie_target - net_calories
        
        return {
            "date": target_date.isoformat(),
            "user_id": user_id,
            "calories_consumed": round(calories_consumed, 1),
            "calories_burned": round(calories_burned, 1),
            "net_calories": round(net_calories, 1),
            "daily_target": round(daily_calorie_target, 1),
            "calories_remaining": round(calories_remaining, 1),
            "progress_percentage": round((net_calories / daily_calorie_target) * 100, 1) if daily_calorie_target > 0 else 0,
            "on_track": net_calories <= daily_calorie_target,
            "nutrition_consumed": {
                "protein_g": round(protein_consumed, 1),
                "carbs_g": round(carbs_consumed, 1),
                "fat_g": round(fats_consumed, 1)
            },
            "activity_summary": {
                "total_workouts": len(workout_logs),
                "total_exercise_duration_minutes": total_exercise_duration,
                "total_meals": len(meal_logs)
            }
        }
    
    def get_weekly_calorie_trends(
        self,
        user_id: int,
        weeks: int = 1
    ) -> Dict:
        """
        Get calorie trends over specified weeks.
        
        Args:
            user_id: User ID
            weeks: Number of weeks to analyze (default 1)
        
        Returns:
            Dictionary with daily summaries and trend analysis
        """
        today = date.today()
        start_date = today - timedelta(days=weeks * 7)
        
        daily_summaries = []
        
        for i in range(weeks * 7):
            target_date = start_date + timedelta(days=i)
            summary = self.get_daily_calorie_summary(user_id, target_date)
            daily_summaries.append(summary)
        
        # Calculate averages
        avg_consumed = sum(d['calories_consumed'] for d in daily_summaries) / len(daily_summaries)
        avg_burned = sum(d['calories_burned'] for d in daily_summaries) / len(daily_summaries)
        avg_net = sum(d['net_calories'] for d in daily_summaries) / len(daily_summaries)
        
        # Count days on track
        days_on_track = sum(1 for d in daily_summaries if d['on_track'])
        
        return {
            "period": f"{weeks} week(s)",
            "start_date": start_date.isoformat(),
            "end_date": today.isoformat(),
            "daily_summaries": daily_summaries,
            "averages": {
                "calories_consumed": round(avg_consumed, 1),
                "calories_burned": round(avg_burned, 1),
                "net_calories": round(avg_net, 1)
            },
            "adherence": {
                "days_on_track": days_on_track,
                "total_days": len(daily_summaries),
                "adherence_percentage": round((days_on_track / len(daily_summaries)) * 100, 1)
            }
        }
