"""
Gender-Specific Health Service

Provides gender-specific calculations and recommendations:
1. Gender-specific BMR/TDEE calculations
2. Female health tracking (FemmeCare)
3. Cycle-synced recommendations
4. Pregnancy and menopause modes
5. Personalized coaching based on gender
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app import models
import logging

logger = logging.getLogger(__name__)


class GenderSpecificService:
    """Service for gender-specific health calculations and recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_bmr_gender_specific(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str
    ) -> float:
        """
        Calculate Basal Metabolic Rate using gender-specific Mifflin-St Jeor formula.
        
        Male: BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
        Female: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161
        
        Args:
            weight_kg: Body weight in kilograms
            height_cm: Height in centimeters
            age: Age in years
            gender: "male", "female", or "other"
        
        Returns:
            BMR in calories per day
        """
        base_bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        
        gender_normalized = gender.lower().strip()
        
        if gender_normalized in ("male", "m"):
            bmr = base_bmr + 5
        elif gender_normalized in ("female", "f"):
            bmr = base_bmr - 161
        else:
            # For "other" or unspecified, use average of male and female
            bmr = base_bmr - 78  # Average of +5 and -161
        
        return round(bmr, 1)
    
    def calculate_tdee_gender_specific(
        self,
        user_id: int,
        include_femmecare_adjustments: bool = True
    ) -> Dict:
        """
        Calculate Total Daily Energy Expenditure with gender-specific adjustments.
        
        Args:
            user_id: User ID
            include_femmecare_adjustments: Whether to include cycle-based adjustments for females
        
        Returns:
            Dictionary with TDEE, BMR, and gender-specific recommendations
        """
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == str(user_id)
        ).first()
        
        # Get user data
        gender = (user.gender or "male").strip()
        age = user.age or profile.age if profile else 30
        weight_kg = user.weight_kg or profile.weight_kg if profile else 70.0
        height_cm = user.height_cm or profile.height_cm if profile else 170.0
        activity_level = (user.activity_level or profile.activity_level if profile else "moderate").lower()
        
        # Calculate BMR
        bmr = self.calculate_bmr_gender_specific(weight_kg, height_cm, age, gender)
        
        # Activity multipliers
        multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        multiplier = multipliers.get(activity_level, 1.55)
        tdee = bmr * multiplier
        
        # FemmeCare adjustments for females
        cycle_adjustment = 0
        cycle_phase = None
        femmecare_recommendations = []
        
        if gender.lower() in ("female", "f") and include_femmecare_adjustments:
            femmecare_enabled = user.femmecare_enabled or (profile.femmecare_enabled if profile else False)
            
            if femmecare_enabled:
                # Get current cycle phase
                cycle_data = self._get_current_cycle_phase(user_id)
                
                if cycle_data:
                    cycle_phase = cycle_data['phase']
                    
                    # Adjust TDEE based on menstrual cycle phase
                    # Luteal phase (post-ovulation) increases BMR by 5-10%
                    if cycle_phase == "luteal":
                        cycle_adjustment = tdee * 0.075  # 7.5% increase
                        tdee += cycle_adjustment
                        femmecare_recommendations.append(
                            "Luteal phase: Your body burns ~7.5% more calories. Increase intake slightly."
                        )
                    
                    # Menstrual phase
                    elif cycle_phase == "menstrual":
                        femmecare_recommendations.append(
                            "Menstrual phase: Focus on iron-rich foods and stay hydrated."
                        )
                    
                    # Follicular phase
                    elif cycle_phase == "follicular":
                        femmecare_recommendations.append(
                            "Follicular phase: Great time for intense workouts and strength training."
                        )
                    
                    # Ovulation
                    elif cycle_phase == "ovulation":
                        femmecare_recommendations.append(
                            "Ovulation: Peak energy levels. Perfect for high-intensity training."
                        )
                
                # Pregnancy mode
                if user.pregnancy_mode or (profile.pregnancy_mode if profile else False):
                    tdee += 300  # Additional ~300 calories during pregnancy
                    femmecare_recommendations.append(
                        "Pregnancy mode: Added 300 calories to daily target for fetal development."
                    )
                
                # Menopause mode
                if user.menopause_mode or (profile.menopause_mode if profile else False):
                    tdee -= 100  # Slight reduction due to hormonal changes
                    femmecare_recommendations.append(
                        "Menopause mode: Adjusted for metabolic changes. Focus on strength training."
                    )
        
        # Gender-specific recommendations
        gender_recommendations = []
        
        if gender.lower() in ("male", "m"):
            gender_recommendations.extend([
                "Higher muscle mass typically means higher BMR.",
                "Focus on protein intake (1.6-2.2g per kg body weight) for muscle maintenance.",
                "Compound movements (squats, deadlifts) optimize testosterone production."
            ])
        elif gender.lower() in ("female", "f"):
            gender_recommendations.extend([
                "Women typically have 10-15% lower BMR than men of same weight/height.",
                "Iron needs are higher (18mg/day vs 8mg for men) due to menstruation.",
                "Strength training is crucial for bone density and metabolism."
            ])
        
        return {
            "user_id": user_id,
            "gender": gender,
            "bmr": round(bmr, 1),
            "tdee": round(tdee, 1),
            "activity_level": activity_level,
            "activity_multiplier": multiplier,
            "cycle_adjustment": round(cycle_adjustment, 1) if cycle_adjustment else 0,
            "current_cycle_phase": cycle_phase,
            "femmecare_enabled": user.femmecare_enabled or False,
            "pregnancy_mode": user.pregnancy_mode or False,
            "menopause_mode": user.menopause_mode or False,
            "femmecare_recommendations": femmecare_recommendations,
            "gender_recommendations": gender_recommendations
        }
    
    def _get_current_cycle_phase(self, user_id: int) -> Optional[Dict]:
        """
        Determine current menstrual cycle phase based on recent logs.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with phase and days since last period, or None
        """
        # Get most recent menstrual log
        recent_log = self.db.query(models.MenstrualCycleLog).filter(
            models.MenstrualCycleLog.user_id == user_id
        ).order_by(models.MenstrualCycleLog.date.desc()).first()
        
        if not recent_log:
            return None
        
        days_since_period = (date.today() - recent_log.date.date()).days
        
        # Standard 28-day cycle phases
        if days_since_period <= 5:
            phase = "menstrual"
        elif days_since_period <= 13:
            phase = "follicular"
        elif days_since_period <= 16:
            phase = "ovulation"
        elif days_since_period <= 28:
            phase = "luteal"
        else:
            # Cycle may have reset, check if period is overdue
            phase = "unknown"
        
        return {
            "phase": phase,
            "days_since_period": days_since_period,
            "last_period_date": recent_log.date.date().isoformat()
        }
    
    def toggle_femmecare(
        self,
        user_id: int,
        enabled: bool
    ) -> Dict:
        """
        Enable or disable FemmeCare features for a female user.
        
        Args:
            user_id: User ID
            enabled: True to enable, False to disable
        
        Returns:
            Updated user profile
        """
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if user is female
        gender = (user.gender or "").lower()
        if gender not in ("female", "f"):
            raise ValueError("FemmeCare features are only available for female users")
        
        # Update user
        user.femmecare_enabled = enabled
        
        # Also update profile if exists
        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == str(user_id)
        ).first()
        
        if profile:
            profile.femmecare_enabled = enabled
        
        self.db.commit()
        
        return {
            "user_id": user_id,
            "femmecare_enabled": enabled,
            "message": f"FemmeCare {'enabled' if enabled else 'disabled'} successfully"
        }
    
    def get_femmecare_dashboard(
        self,
        user_id: int
    ) -> Dict:
        """
        Get comprehensive FemmeCare dashboard data.
        
        Args:
            user_id: User ID
        
        Returns:
            Dashboard with cycle tracking, recommendations, and health insights
        """
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        if not user or not user.femmecare_enabled:
            raise ValueError("FemmeCare is not enabled for this user")
        
        # Get cycle data
        cycle_phase_data = self._get_current_cycle_phase(user_id)
        
        # Get recent cycle logs
        recent_logs = self.db.query(models.MenstrualCycleLog).filter(
            models.MenstrualCycleLog.user_id == user_id
        ).order_by(models.MenstrualCycleLog.date.desc()).limit(90).all()
        
        # Calculate average cycle length
        cycle_lengths = []
        for i in range(len(recent_logs) - 1):
            days_between = (recent_logs[i].date.date() - recent_logs[i+1].date.date()).days
            if 20 <= days_between <= 40:  # Valid cycle length
                cycle_lengths.append(days_between)
        
        avg_cycle_length = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 28
        
        # Predict next period
        next_period_date = None
        if recent_logs:
            last_period = recent_logs[0].date.date()
            next_period_date = last_period + timedelta(days=int(avg_cycle_length))
        
        # Phase-specific recommendations
        phase_recommendations = {
            "menstrual": {
                "nutrition": ["Iron-rich foods (spinach, red meat)", "Dark chocolate (magnesium)", "Omega-3 fatty acids"],
                "exercise": ["Light yoga", "Walking", "Stretching"],
                "wellness": ["Stay hydrated", "Use heating pad for cramps", "Get adequate rest"]
            },
            "follicular": {
                "nutrition": ["High protein", "Complex carbs", "Fresh fruits and vegetables"],
                "exercise": ["Strength training", "HIIT workouts", "Cardio"],
                "wellness": ["Great time to start new habits", "Energy levels rising", "Focus on goals"]
            },
            "ovulation": {
                "nutrition": ["Antioxidant-rich foods", "Leafy greens", "Healthy fats"],
                "exercise": ["High-intensity training", "Competitive sports", "Peak performance workouts"],
                "wellness": ["Peak fertility window", "Highest energy levels", "Social activities"]
            },
            "luteal": {
                "nutrition": ["Complex carbs", "Calcium-rich foods", "B-vitamins"],
                "exercise": ["Moderate cardio", "Pilates", "Swimming"],
                "wellness": ["Listen to your body", "Manage stress", "Prepare for period"]
            }
        }
        
        current_phase = cycle_phase_data['phase'] if cycle_phase_data else "unknown"
        recommendations = phase_recommendations.get(current_phase, {})
        
        return {
            "user_id": user_id,
            "femmecare_enabled": True,
            "pregnancy_mode": user.pregnancy_mode or False,
            "menopause_mode": user.menopause_mode or False,
            "current_cycle": {
                "phase": current_phase,
                "days_since_period": cycle_phase_data['days_since_period'] if cycle_phase_data else None,
                "last_period_date": cycle_phase_data['last_period_date'] if cycle_phase_data else None,
                "next_predicted_period": next_period_date.isoformat() if next_period_date else None,
                "average_cycle_length": round(avg_cycle_length, 1)
            },
            "recommendations": recommendations,
            "cycle_history": {
                "total_logged_days": len(recent_logs),
                "cycles_tracked": len(cycle_lengths)
            }
        }
    
    def get_gender_specific_macro_targets(
        self,
        user_id: int,
        goal: str = "maintenance"
    ) -> Dict:
        """
        Calculate macro targets with gender-specific adjustments.
        
        Args:
            user_id: User ID
            goal: Fitness goal (weight_loss, muscle_gain, maintenance, athletic)
        
        Returns:
            Macro targets adjusted for gender
        """
        tdee_data = self.calculate_tdee_gender_specific(user_id)
        tdee = tdee_data['tdee']
        gender = tdee_data['gender'].lower()
        
        # Base macro distributions
        macro_ratios = {
            "weight_loss": {"protein": 0.40, "carbs": 0.30, "fat": 0.30, "deficit": 0.20},
            "muscle_gain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30, "surplus": 0.15},
            "maintenance": {"protein": 0.25, "carbs": 0.45, "fat": 0.30, "deficit": 0},
            "athletic": {"protein": 0.30, "carbs": 0.50, "fat": 0.20, "surplus": 0.05}
        }
        
        ratios = macro_ratios.get(goal, macro_ratios["maintenance"])
        
        # Calculate target calories
        if "deficit" in ratios:
            target_calories = tdee * (1 - ratios["deficit"])
        else:
            target_calories = tdee * (1 + ratios["surplus"])
        
        # Gender-specific adjustments
        if gender in ("female", "f"):
            # Females typically need slightly higher fat percentage for hormonal health
            ratios["fat"] = min(ratios["fat"] + 0.05, 0.35)
            ratios["carbs"] = ratios["carbs"] - 0.05
        
        # Calculate macros (protein/carbs = 4 cal/g, fat = 9 cal/g)
        protein_g = (target_calories * ratios["protein"]) / 4
        carbs_g = (target_calories * ratios["carbs"]) / 4
        fat_g = (target_calories * ratios["fat"]) / 9
        
        return {
            "user_id": user_id,
            "gender": gender,
            "goal": goal,
            "tdee": round(tdee, 1),
            "target_calories": round(target_calories, 1),
            "macros": {
                "protein_g": round(protein_g, 1),
                "carbs_g": round(carbs_g, 1),
                "fat_g": round(fat_g, 1)
            },
            "macro_percentages": {
                "protein": round(ratios["protein"] * 100, 1),
                "carbs": round(ratios["carbs"] * 100, 1),
                "fat": round(ratios["fat"] * 100, 1)
            },
            "gender_adjustments": "Increased healthy fats for hormonal health" if gender in ("female", "f") else "Standard macro distribution"
        }
