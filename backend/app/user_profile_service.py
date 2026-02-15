"""
User Profile Management Service

Provides comprehensive user profile management including:
- Profile creation and updates
- Goal setting and validation
- Preference tracking
- Profile validation and guidance
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from . import models
from pydantic import BaseModel, validator, Field


# Pydantic schemas for user profile management
class UserProfileCreate(BaseModel):
    """Schema for creating a new user profile"""
    age: Optional[int] = Field(None, ge=13, le=120)
    weight_kg: Optional[Decimal] = Field(None, ge=20, le=500)
    height_cm: Optional[int] = Field(None, ge=50, le=300)
    activity_level: str = Field(..., pattern="^(sedentary|light|moderate|active|very_active)$")
    primary_goal: str = Field(..., pattern="^(weight_loss|weight_gain|muscle_gain|maintenance|athletic_performance)$")
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)

    @validator('dietary_restrictions', 'allergies')
    def validate_lists(cls, v):
        if v is None:
            return []
        return [item.strip() for item in v if item.strip()]


class UserProfileUpdate(BaseModel):
    """Schema for updating an existing user profile"""
    age: Optional[int] = Field(None, ge=13, le=120)
    weight_kg: Optional[Decimal] = Field(None, ge=20, le=500)
    height_cm: Optional[int] = Field(None, ge=50, le=300)
    activity_level: Optional[str] = Field(None, pattern="^(sedentary|light|moderate|active|very_active)$")
    primary_goal: Optional[str] = Field(None, pattern="^(weight_loss|weight_gain|muscle_gain|maintenance|athletic_performance)$")
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None


class GoalCreate(BaseModel):
    """Schema for creating a new goal"""
    goal_type: str = Field(..., pattern="^(daily_calories|weekly_exercise|weight_target|protein_target|steps_target)$")
    target_value: Decimal = Field(..., ge=0)
    target_date: Optional[datetime] = None

    @validator('target_date')
    def validate_target_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("Target date must be in the future")
        return v


class GoalUpdate(BaseModel):
    """Schema for updating a goal"""
    target_value: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ProfileValidationResult(BaseModel):
    """Result of profile validation"""
    is_complete: bool
    missing_fields: List[str]
    warnings: List[str]
    suggestions: List[str]


class GoalValidationResult(BaseModel):
    """Result of goal validation"""
    is_realistic: bool
    warnings: List[str]
    suggestions: List[str]
    recommended_timeline: Optional[str] = None


class UserProfileService:
    """Service for managing user profiles and goals"""

    def __init__(self, db: Session):
        self.db = db

    def create_user_profile(self, user_id: str, profile_data: UserProfileCreate) -> models.UserProfile:
        """
        Create a new user profile with validation
        
        Args:
            user_id: UUID of the user
            profile_data: Profile creation data
            
        Returns:
            Created UserProfile model
        """
        # Check if profile already exists
        existing_profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            raise ValueError("User profile already exists")
        
        # Create new profile
        profile = models.UserProfile(
            user_id=user_id,
            age=profile_data.age,
            weight_kg=profile_data.weight_kg,
            height_cm=profile_data.height_cm,
            activity_level=profile_data.activity_level,
            primary_goal=profile_data.primary_goal,
            dietary_restrictions=profile_data.dietary_restrictions,
            allergies=profile_data.allergies
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        return profile

    def get_user_profile(self, user_id: str) -> Optional[models.UserProfile]:
        """Get user profile by user ID"""
        # Convert string UUID to UUID object if using PostgreSQL
        try:
            import uuid as uuid_module
            user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, AttributeError):
            user_uuid = user_id
            
        return self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == user_uuid
        ).first()

    def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> models.UserProfile:
        """
        Update existing user profile
        
        Args:
            user_id: UUID of the user
            profile_data: Profile update data
            
        Returns:
            Updated UserProfile model
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            raise ValueError("User profile not found")
        
        # Update only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        
        return profile

    def validate_profile(self, user_id: str) -> ProfileValidationResult:
        """
        Validate user profile completeness and provide guidance
        
        Args:
            user_id: UUID of the user
            
        Returns:
            ProfileValidationResult with validation details
        """
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return ProfileValidationResult(
                is_complete=False,
                missing_fields=["profile"],
                warnings=["No profile found"],
                suggestions=["Create a user profile to get started"]
            )
        
        missing_fields = []
        warnings = []
        suggestions = []
        
        # Check required fields
        if profile.age is None:
            missing_fields.append("age")
            suggestions.append("Add your age for personalized recommendations")
        
        if profile.weight_kg is None:
            missing_fields.append("weight_kg")
            suggestions.append("Add your weight for accurate calorie calculations")
        
        if profile.height_cm is None:
            missing_fields.append("height_cm")
            suggestions.append("Add your height for BMI and calorie calculations")
        
        # Validate data ranges
        if profile.age and (profile.age < 13 or profile.age > 120):
            warnings.append("Age seems unusual, please verify")
        
        if profile.weight_kg and (profile.weight_kg < 20 or profile.weight_kg > 500):
            warnings.append("Weight seems unusual, please verify")
        
        if profile.height_cm and (profile.height_cm < 50 or profile.height_cm > 300):
            warnings.append("Height seems unusual, please verify")
        
        # Check for dietary information
        if not profile.dietary_restrictions:
            suggestions.append("Consider adding dietary restrictions if applicable")
        
        if not profile.allergies:
            suggestions.append("Consider adding food allergies for safer meal recommendations")
        
        is_complete = len(missing_fields) == 0
        
        return ProfileValidationResult(
            is_complete=is_complete,
            missing_fields=missing_fields,
            warnings=warnings,
            suggestions=suggestions
        )

    def create_goal(self, user_id: str, goal_data: GoalCreate) -> models.UserGoal:
        """
        Create a new goal for a user
        
        Args:
            user_id: UUID of the user
            goal_data: Goal creation data
            
        Returns:
            Created UserGoal model
        """
        # Validate goal against user profile
        validation = self.validate_goal(user_id, goal_data)
        
        # Create goal
        goal = models.UserGoal(
            user_id=user_id,
            goal_type=goal_data.goal_type,
            target_value=goal_data.target_value,
            current_value=Decimal(0),
            target_date=goal_data.target_date,
            is_active=True
        )
        
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        
        return goal

    def get_user_goals(self, user_id: str, active_only: bool = True) -> List[models.UserGoal]:
        """Get all goals for a user"""
        query = self.db.query(models.UserGoal).filter(
            models.UserGoal.user_id == user_id
        )
        
        if active_only:
            query = query.filter(models.UserGoal.is_active == True)
        
        return query.all()

    def update_goal(self, goal_id: str, goal_data: GoalUpdate) -> models.UserGoal:
        """Update an existing goal"""
        goal = self.db.query(models.UserGoal).filter(
            models.UserGoal.id == goal_id
        ).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        # Update only provided fields
        update_data = goal_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        
        goal.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(goal)
        
        return goal

    def validate_goal(self, user_id: str, goal_data: GoalCreate) -> GoalValidationResult:
        """
        Validate goal for realism based on user profile
        
        Args:
            user_id: UUID of the user
            goal_data: Goal data to validate
            
        Returns:
            GoalValidationResult with validation details
        """
        profile = self.get_user_profile(user_id)
        warnings = []
        suggestions = []
        is_realistic = True
        recommended_timeline = None
        
        if not profile:
            warnings.append("No user profile found - cannot validate goal realism")
            return GoalValidationResult(
                is_realistic=False,
                warnings=warnings,
                suggestions=["Create a user profile first"],
                recommended_timeline=None
            )
        
        # Validate based on goal type
        if goal_data.goal_type == "weight_target":
            if profile.weight_kg:
                weight_diff = abs(float(goal_data.target_value) - float(profile.weight_kg))
                
                # Safe weight loss/gain is 0.5-1 kg per week
                safe_weekly_change = 1.0
                recommended_weeks = int(weight_diff / safe_weekly_change)
                recommended_timeline = f"{recommended_weeks} weeks"
                
                if goal_data.target_date:
                    days_until_target = (goal_data.target_date - datetime.utcnow()).days
                    weeks_until_target = days_until_target / 7
                    
                    if weeks_until_target < recommended_weeks:
                        is_realistic = False
                        warnings.append(f"Target date may be too aggressive for {weight_diff:.1f}kg change")
                        suggestions.append(f"Consider extending timeline to at least {recommended_weeks} weeks")
                    elif weeks_until_target > recommended_weeks * 3:
                        suggestions.append("Timeline is very conservative - you may reach your goal sooner")
        
        elif goal_data.goal_type == "daily_calories":
            if profile.weight_kg and profile.height_cm and profile.age:
                # Calculate BMR using Mifflin-St Jeor equation
                bmr = self._calculate_bmr(profile)
                
                # Apply activity multiplier
                activity_multipliers = {
                    "sedentary": 1.2,
                    "light": 1.375,
                    "moderate": 1.55,
                    "active": 1.725,
                    "very_active": 1.9
                }
                tdee = bmr * activity_multipliers.get(profile.activity_level, 1.2)
                
                target_calories = float(goal_data.target_value)
                
                # Check if target is too low
                if target_calories < bmr * 0.8:
                    is_realistic = False
                    warnings.append("Calorie target is below recommended minimum")
                    suggestions.append(f"Consider targeting at least {int(bmr * 0.8)} calories")
                
                # Check if target aligns with primary goal
                if profile.primary_goal == "weight_loss" and target_calories > tdee:
                    warnings.append("Calorie target exceeds maintenance for weight loss goal")
                    suggestions.append(f"For weight loss, consider {int(tdee - 500)} calories")
                
                elif profile.primary_goal == "weight_gain" and target_calories < tdee:
                    warnings.append("Calorie target is below maintenance for weight gain goal")
                    suggestions.append(f"For weight gain, consider {int(tdee + 500)} calories")
        
        elif goal_data.goal_type == "weekly_exercise":
            target_minutes = float(goal_data.target_value)
            
            # WHO recommends 150-300 minutes of moderate activity per week
            if target_minutes < 150:
                suggestions.append("WHO recommends at least 150 minutes of exercise per week")
            elif target_minutes > 600:
                warnings.append("Very high exercise target - ensure adequate recovery")
                suggestions.append("Consider progressive increase to avoid overtraining")
        
        return GoalValidationResult(
            is_realistic=is_realistic,
            warnings=warnings,
            suggestions=suggestions,
            recommended_timeline=recommended_timeline
        )

    def _calculate_bmr(self, profile: models.UserProfile) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation
        
        Args:
            profile: User profile with weight, height, age
            
        Returns:
            BMR in calories per day
        """
        # Assuming average gender distribution, use average of male/female formulas
        # Male: (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + 5
        # Female: (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) - 161
        
        weight = float(profile.weight_kg)
        height = float(profile.height_cm)
        age = float(profile.age)
        
        bmr_male = (10 * weight) + (6.25 * height) - (5 * age) + 5
        bmr_female = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Return average
        return (bmr_male + bmr_female) / 2

    def calculate_progress_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate progress metrics for all active goals
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dictionary with progress metrics for each goal
        """
        goals = self.get_user_goals(user_id, active_only=True)
        metrics = {}
        
        for goal in goals:
            if goal.target_value > 0:
                progress_percentage = (float(goal.current_value) / float(goal.target_value)) * 100
            else:
                progress_percentage = 0
            
            days_remaining = None
            if goal.target_date:
                days_remaining = (goal.target_date - datetime.utcnow()).days
            
            metrics[str(goal.id)] = {
                "goal_type": goal.goal_type,
                "progress_percentage": min(progress_percentage, 100),
                "current_value": float(goal.current_value),
                "target_value": float(goal.target_value),
                "days_remaining": days_remaining,
                "is_on_track": progress_percentage >= 50 if days_remaining and days_remaining < 30 else True
            }
        
        return metrics
