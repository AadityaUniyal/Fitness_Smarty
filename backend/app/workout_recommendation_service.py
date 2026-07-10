"""
Personalized Workout Recommendation Service

Provides intelligent workout suggestions based on:
- User workout history
- Muscle balance analysis
- Rest day recommendations
- Progressive overload tracking
- Exercise variety and difficulty adjustment
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict

from .models import (
    EnhancedUser as User, WorkoutLog, ExerciseItem as Exercise, UserGoal as UserGoals, 
    ExerciseCategory
)

class DifficultyLevel:
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
from .gender_specific_service import GenderSpecificService


class WorkoutRecommendationService:
    """Service for generating personalized workout recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gender_service = GenderSpecificService(db)
    
    def suggest_workout(self, user_id: int) -> Dict[str, Any]:
        """
        Generate intelligent workout suggestion based on user history
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Check if rest day is needed
        rest_check = self.check_rest_day_needed(user_id)
        if rest_check["should_rest"]:
            return {
                "recommendation_type": "rest_day",
                "message": rest_check["message"],
                "reason": rest_check["reason"],
                "suggested_activities": [
                    "Light stretching",
                    "Walking",
                    "Yoga",
                    "Foam rolling",
                    "Active recovery"
                ]
            }
        
        # Analyze muscle balance
        muscle_balance = self.analyze_muscle_balance(user_id)
        
        # Get workout history
        recent_workouts = self._get_recent_workouts(user_id, days=7)
        
        # Determine which muscle groups to target
        target_groups = self._determine_target_muscle_groups(muscle_balance)
        
        # Get exercise suggestions
        exercises = self._suggest_exercises(
            user_id=user_id,
            target_groups=target_groups,
            recent_workouts=recent_workouts
        )
        
        # Calculate recommended sets and reps
        recommendations = self._calculate_progressive_overload(user_id, exercises)
        
        return {
            "recommendation_type": "workout",
            "target_muscle_groups": target_groups,
            "exercises": recommendations,
            "estimated_duration_minutes": len(recommendations) * 8,  # ~8 min per exercise
            "difficulty": self._determine_difficulty(user_id),
            "tips": self._generate_workout_tips(target_groups, user.gender),
            "muscle_balance_status": muscle_balance
        }
    
    def check_rest_day_needed(self, user_id: int) -> Dict[str, Any]:
        """
        Check if user needs a rest day based on workout frequency
        """
        # Get workouts in last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_workouts = self.db.query(WorkoutLog).filter(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= seven_days_ago
            )
        ).all()
        
        # Get last workout date
        last_workout = self.db.query(WorkoutLog).filter(
            WorkoutLog.user_id == user_id
        ).order_by(WorkoutLog.date.desc()).first()
        
        if not last_workout:
            return {
                "should_rest": False,
                "message": "Ready to start your fitness journey!",
                "reason": "no_workout_history"
            }
        
        days_since_last = (datetime.now().date() - last_workout.date).days
        workouts_this_week = len(recent_workouts)
        
        # Rest if worked out 6+ days in a row
        if days_since_last == 0 and workouts_this_week >= 6:
            return {
                "should_rest": True,
                "message": "Time for a rest day! You've been crushing it.",
                "reason": "consecutive_workouts",
                "days_worked_out": workouts_this_week
            }
        
        # Calculate average intensity
        total_exercises = sum(len(w.exercises) if hasattr(w, 'exercises') else 0 for w in recent_workouts)
        avg_exercises_per_workout = total_exercises / max(workouts_this_week, 1)
        
        if workouts_this_week >= 5 and avg_exercises_per_workout > 8:
            return {
                "should_rest": True,
                "message": "Your body needs recovery time.",
                "reason": "high_volume",
                "days_worked_out": workouts_this_week
            }
        
        return {
            "should_rest": False,
            "message": "You're ready for a workout!",
            "reason": "adequate_recovery",
            "days_since_last_workout": days_since_last
        }
    
    def analyze_muscle_balance(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze which muscle groups have been worked recently
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all workouts with exercises
        workouts = self.db.query(WorkoutLog).filter(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= cutoff_date
            )
        ).all()
        
        # Count exercises by muscle group
        muscle_group_count = defaultdict(int)
        total_exercises = 0
        
        for workout in workouts:
            # Parse exercise names and categorize
            if workout.exercise_name:
                exercises = workout.exercise_name.split(',')
                for ex_name in exercises:
                    ex_name = ex_name.strip()
                    total_exercises += 1
                    
                    # Find exercise in database
                    exercise = self.db.query(Exercise).filter(
                        Exercise.name.ilike(f"%{ex_name}%")
                    ).first()
                    
                    if exercise:
                        muscle_group_count[exercise.muscle_group] += 1
                    else:
                        # Categorize by keywords
                        ex_lower = ex_name.lower()
                        if any(word in ex_lower for word in ['chest', 'bench', 'push-up', 'press']):
                            muscle_group_count['Chest'] += 1
                        elif any(word in ex_lower for word in ['back', 'row', 'pull', 'lat']):
                            muscle_group_count['Back'] += 1
                        elif any(word in ex_lower for word in ['shoulder', 'lateral', 'overhead']):
                            muscle_group_count['Shoulders'] += 1
                        elif any(word in ex_lower for word in ['leg', 'squat', 'lunge', 'quad']):
                            muscle_group_count['Legs'] += 1
                        elif any(word in ex_lower for word in ['bicep', 'curl']):
                            muscle_group_count['Arms'] += 1
                        elif any(word in ex_lower for word in ['tricep', 'dip', 'extension']):
                            muscle_group_count['Arms'] += 1
                        elif any(word in ex_lower for word in ['core', 'abs', 'plank', 'crunch']):
                            muscle_group_count['Core'] += 1
        
        if total_exercises == 0:
            return {
                "status": "no_data",
                "message": "No workout history to analyze",
                "muscle_groups": {},
                "recommendations": ["Start with a full-body routine"]
            }
        
        # Calculate percentages
        muscle_percentages = {
            muscle: (count / total_exercises * 100)
            for muscle, count in muscle_group_count.items()
        }
        
        # Identify neglected muscle groups
        all_muscle_groups = ['Chest', 'Back', 'Shoulders', 'Legs', 'Arms', 'Core']
        neglected = [m for m in all_muscle_groups if muscle_percentages.get(m, 0) < 10]
        overworked = [m for m, pct in muscle_percentages.items() if pct > 30]
        
        return {
            "status": "analyzed",
            "total_exercises_analyzed": total_exercises,
            "muscle_distribution": muscle_percentages,
            "neglected_groups": neglected,
            "overworked_groups": overworked,
            "balance_score": self._calculate_balance_score(muscle_percentages),
            "recommendations": self._generate_balance_recommendations(neglected, overworked)
        }
    
    def get_progressive_overload_suggestions(self, user_id: int, exercise_name: str) -> Dict[str, Any]:
        """
        Suggest progressive overload for a specific exercise
        """
        # Get last 5 performances of this exercise
        recent_logs = self.db.query(WorkoutLog).filter(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.exercise_name.ilike(f"%{exercise_name}%")
            )
        ).order_by(WorkoutLog.date.desc()).limit(5).all()
        
        if not recent_logs:
            return {
                "exercise": exercise_name,
                "suggestion": "baseline",
                "message": "Start with a comfortable weight for 8-12 reps"
            }
        
        # Analyze progression
        latest = recent_logs[0]
        
        # Calculate suggested increase
        if latest.sets and latest.reps:
            suggested_sets = latest.sets
            suggested_reps = min(latest.reps + 1, 15)  # Increase reps up to 15
            suggested_weight_increase = 2.5  # kg increase
            
            if latest.reps >= 12:
                # If hitting 12+ reps, suggest weight increase
                return {
                    "exercise": exercise_name,
                    "suggestion": "increase_weight",
                    "current_weight": latest.weight if latest.weight else "bodyweight",
                    "suggested_weight_increase_kg": suggested_weight_increase,
                    "suggested_reps": 8,
                    "message": f"You're crushing it! Time to increase the weight by {suggested_weight_increase}kg"
                }
            else:
                # Otherwise increase reps
                return {
                    "exercise": exercise_name,
                    "suggestion": "increase_reps",
                    "current_reps": latest.reps,
                    "suggested_reps": suggested_reps,
                    "suggested_sets": suggested_sets,
                    "message": f"Aim for {suggested_reps} reps this time!"
                }
        
        return {
            "exercise": exercise_name,
            "suggestion": "maintain",
            "message": "Keep up the good work! Focus on form."
        }
    
    def _get_recent_workouts(self, user_id: int, days: int = 7) -> List[WorkoutLog]:
        """Get recent workout logs"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return self.db.query(WorkoutLog).filter(
            and_(
                WorkoutLog.user_id == user_id,
                WorkoutLog.date >= cutoff_date
            )
        ).order_by(WorkoutLog.date.desc()).all()
    
    def _determine_target_muscle_groups(self, muscle_balance: Dict[str, Any]) -> List[str]:
        """Determine which muscle groups to target today"""
        if muscle_balance["status"] == "no_data":
            return ["Chest", "Back", "Legs"]  # Full body for beginners
        
        neglected = muscle_balance.get("neglected_groups", [])
        if neglected:
            return neglected[:2]  # Focus on top 2 neglected groups
        
        # If balanced, do a split routine
        all_groups = ['Chest', 'Back', 'Shoulders', 'Legs', 'Arms', 'Core']
        return [all_groups[datetime.now().weekday() % len(all_groups)]]
    
    def _suggest_exercises(
        self, 
        user_id: int, 
        target_groups: List[str], 
        recent_workouts: List[WorkoutLog]
    ) -> List[Exercise]:
        """Suggest exercises for target muscle groups"""
        
        # Get recently done exercises to ensure variety
        recent_exercise_names = set()
        for workout in recent_workouts:
            if workout.exercise_name:
                recent_exercise_names.update([e.strip() for e in workout.exercise_name.split(',')])
        
        suggested_exercises = []
        
        for muscle_group in target_groups:
            # Query exercises for this muscle group
            exercises = self.db.query(Exercise).filter(
                Exercise.muscle_group == muscle_group
            ).all()
            
            # Filter out recently done exercises
            varied_exercises = [
                ex for ex in exercises 
                if ex.name not in recent_exercise_names
            ]
            
            # If all were recent, use all
            if not varied_exercises:
                varied_exercises = exercises
            
            # Pick 2-3 exercises per muscle group
            import random
            selected = random.sample(varied_exercises, min(3, len(varied_exercises)))
            suggested_exercises.extend(selected)
        
        return suggested_exercises[:6]  # Limit to 6 exercises total
    
    def _calculate_progressive_overload(
        self, 
        user_id: int, 
        exercises: List[Exercise]
    ) -> List[Dict[str, Any]]:
        """Calculate recommended sets, reps, and weight for exercises"""
        recommendations = []
        
        for exercise in exercises:
            # Get user's history with this exercise
            last_log = self.db.query(WorkoutLog).filter(
                and_(
                    WorkoutLog.user_id == user_id,
                    WorkoutLog.exercise_name.ilike(f"%{exercise.name}%")
                )
            ).order_by(WorkoutLog.date.desc()).first()
            
            if last_log and last_log.sets and last_log.reps:
                # Progressive overload
                suggested_reps = min(last_log.reps + 1, 12)
                suggested_sets = last_log.sets
                weight_note = "Increase weight if hitting 12+ reps easily"
            else:
                # Default for new exercise
                suggested_sets = 3
                suggested_reps = 10
                weight_note = "Start with a comfortable weight"
            
            recommendations.append({
                "exercise_id": exercise.id,
                "exercise_name": exercise.name,
                "muscle_group": exercise.muscle_group,
                "difficulty": exercise.difficulty.value if exercise.difficulty else "intermediate",
                "suggested_sets": suggested_sets,
                "suggested_reps": suggested_reps,
                "rest_seconds": 60 if exercise.difficulty == DifficultyLevel.BEGINNER else 90,
                "notes": weight_note,
                "instructions": exercise.instructions
            })
        
        return recommendations
    
    def _determine_difficulty(self, user_id: int) -> str:
        """Determine user's fitness level based on workout history"""
        total_workouts = self.db.query(WorkoutLog).filter(
            WorkoutLog.user_id == user_id
        ).count()
        
        if total_workouts < 10:
            return "beginner"
        elif total_workouts < 50:
            return "intermediate"
        else:
            return "advanced"
    
    def _generate_workout_tips(self, target_groups: List[str], gender: str) -> List[str]:
        """Generate helpful workout tips"""
        tips = [
            "Warm up for 5-10 minutes before starting",
            "Focus on proper form over heavy weight",
            "Rest 60-90 seconds between sets",
            "Stay hydrated throughout your workout",
        ]
        
        if 'Legs' in target_groups:
            tips.append("Leg day is the best day! Your legs are your foundation.")
        
        if 'Core' in target_groups:
            tips.append("Engage your core in every exercise for stability")
        
        if gender == "female":
            tips.append("Don't be afraid of weights - they won't make you bulky!")
        
        return tips
    
    def _calculate_balance_score(self, muscle_percentages: Dict[str, float]) -> int:
        """Calculate balance score 0-100"""
        if not muscle_percentages:
            return 0
        
        # Ideal is around 16.6% per muscle group (6 major groups)
        ideal_percentage = 16.6
        
        # Calculate deviation from ideal
        total_deviation = sum(
            abs(pct - ideal_percentage) 
            for pct in muscle_percentages.values()
        )
        
        # Convert to score (lower deviation = higher score)
        max_possible_deviation = ideal_percentage * len(muscle_percentages) * 2
        score = max(0, 100 - (total_deviation / max_possible_deviation * 100))
        
        return int(score)
    
    def _generate_balance_recommendations(
        self, 
        neglected: List[str], 
        overworked: List[str]
    ) -> List[str]:
        """Generate recommendations for muscle balance"""
        recommendations = []
        
        if neglected:
            recommendations.append(
                f"Focus more on: {', '.join(neglected)}"
            )
        
        if overworked:
            recommendations.append(
                f"Reduce volume on: {', '.join(overworked)}"
            )
        
        if not neglected and not overworked:
            recommendations.append("Great balance! Keep it up!")
        
        return recommendations
