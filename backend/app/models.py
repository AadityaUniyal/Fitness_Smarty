"""
Database Models for Smarty Reco

SQLAlchemy ORM models for all database tables
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class EnhancedUser(Base):
    """Enhanced user model with Clerk authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    clerk_user_id = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    
    # Profile
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    gender = Column(String, nullable=True)
    activity_level = Column(String, nullable=True)
    primary_goal = Column(String, nullable=True)  # weight_loss, muscle_gain, maintenance
    femmecare_enabled = Column(Boolean, default=False, nullable=True)
    menopause_mode = Column(Boolean, default=False, nullable=True)
    pregnancy_mode = Column(Boolean, default=False, nullable=True)
    local_only = Column(Boolean, default=False, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Versioning for optimistic locking
    version = Column(Integer, default=1, nullable=False)
    __mapper_args__ = {
        "version_id_col": version
    }

    # Relationships
    meal_logs = relationship("MealLog", back_populates="user")
    workout_logs = relationship("WorkoutLog", back_populates="user")


class ExerciseCategory(Base):
    """Exercise categories"""
    __tablename__ = "exercise_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    exercises = relationship("ExerciseItem", back_populates="category")

    @property
    def items(self):
        """Alias for schema compatibility"""
        return self.exercises


class ExerciseItem(Base):
    """Individual exercises"""
    __tablename__ = "exercise_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("exercise_categories.id"))
    name = Column(String, index=True)
    targeted_muscle = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    equipment = Column(String, nullable=True)
    calories_per_min = Column(Float, default=5.0)
    calories_per_rep = Column(Float, default=0.1)  # New: Burn per rep
    description = Column(Text, nullable=True)
    fitness_goal = Column(String, nullable=True)  # fat_loss, muscle_gain, athletic, maintenance
    
    category = relationship("ExerciseCategory", back_populates="exercises")


class FoodCategory(Base):
    """Food categories"""
    __tablename__ = "food_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    foods = relationship("FoodItem", back_populates="category")

    @property
    def items(self):
        """Alias for schema compatibility"""
        return self.foods


class FoodItem(Base):
    """Individual food items"""
    __tablename__ = "food_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    name = Column(String, index=True)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    is_elite = Column(Boolean, default=False)
    target_muscle_group = Column(String, nullable=True)
    recommended_for_goal = Column(String, nullable=True)
    
    category = relationship("FoodCategory", back_populates="foods")

    @property
    def serving_size(self):
        """Default serving size label"""
        return "per 100g"


class MealLog(Base):
    """Meal logging"""
    __tablename__ = "meal_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    meal_name = Column(String, nullable=True)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbs = Column(Float)
    total_fats = Column(Float)
    image_path = Column(String, nullable=True)
    detected_foods = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    is_good_for_user = Column(Boolean, nullable=True)
    user_feedback = Column(Boolean, nullable=True)  # thumbs up/down
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("EnhancedUser", back_populates="meal_logs")


class FoodDetection(Base):
    """YOLOv8 and computer vision detection results"""
    __tablename__ = "food_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String)
    yolo_detections = Column(JSON, nullable=True)  # YOLOv8 results
    gemini_detections = Column(JSON, nullable=True)  # Gemini results
    final_result = Column(JSON, nullable=True)  # Combined/ensemble results
    model_used = Column(String)  # 'yolo', 'gemini', 'hybrid', 'mock'
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkoutLog(Base):
    """Workout logging"""
    __tablename__ = "workout_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workout_name = Column(String, nullable=True)
    duration_minutes = Column(Integer)
    calories_burned = Column(Float)
    exercises_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("EnhancedUser", back_populates="workout_logs")


class BiometricReading(Base):
    """Biometric data"""
    __tablename__ = "biometric_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProgressSnapshot(Base):
    """Progress tracking"""
    __tablename__ = "progress_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    photos = Column(JSON, nullable=True)
    measurements = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


# ============================================================
# ===  GAMIFICATION MODELS (Streaks, Achievements, Badges) ===
# ============================================================


class UserStreak(Base):
    """User activity streaks"""
    __tablename__ = "user_streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    streak_type = Column(String, nullable=False)  # workout, nutrition, hydration, login
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Achievement(Base):
    """Achievement definitions (global templates)"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # workout, nutrition, social, streak, milestone
    achievement_type = Column(String, nullable=False)  # count, streak, goal, special
    icon = Column(String, nullable=True)  # emoji or icon identifier
    rarity = Column(String, default="common")  # common, rare, epic, legendary
    points = Column(Integer, default=10)
    
    # Criteria (JSON with flexible conditions)
    criteria = Column(JSON, nullable=False)
    # Example: {"type": "workout_count", "target": 50}
    # Example: {"type": "streak_days", "streak_type": "workout", "target": 7}
    # Example: {"type": "calories_burned", "target": 10000}
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    """User's earned achievements"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    progress = Column(Float, default=0.0)  # 0-100 percentage
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    achievement = relationship("Achievement", foreign_keys=[achievement_id])


class Badge(Base):
    """Badge definitions (special awards)"""
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=True)
    tier = Column(String, default="bronze")  # bronze, silver, gold, platinum, diamond
    category = Column(String, nullable=False)  # strength, cardio, nutrition, consistency
    points = Column(Integer, default=25)
    
    # Requirements (more specific than achievements)
    requirements = Column(JSON, nullable=False)
    # Example: {"exercise_type": "strength", "total_reps": 1000}
    # Example: {"meal_logs": 100, "protein_avg": 150}
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBadge(Base):
    """User's earned badges"""
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    is_equipped = Column(Boolean, default=False)  # Display on profile
    
    badge = relationship("Badge", foreign_keys=[badge_id])


class UserPoints(Base):
    """User point tracking and leaderboard"""
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)  # XP within current level
    
    # Point sources breakdown
    workout_points = Column(Integer, default=0)
    nutrition_points = Column(Integer, default=0)
    social_points = Column(Integer, default=0)
    streak_points = Column(Integer, default=0)
    achievement_points = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    """Extended user profile for recommendations"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    gender = Column(String, nullable=True)
    activity_level = Column(String, nullable=True)
    dietary_preferences = Column(JSON, nullable=True)
    allergies = Column(JSON, nullable=True)
    fitness_goal = Column(String, nullable=True)
    daily_calorie_target = Column(Float, nullable=True)
    protein_target_g = Column(Float, nullable=True)
    carbs_target_g = Column(Float, nullable=True)
    fat_target_g = Column(Float, nullable=True)
    femmecare_enabled = Column(Boolean, default=False, nullable=True)
    menopause_mode = Column(Boolean, default=False, nullable=True)
    pregnancy_mode = Column(Boolean, default=False, nullable=True)
    local_only = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def dietary_restrictions(self):
        return self.dietary_preferences

    @dietary_restrictions.setter
    def dietary_restrictions(self, value):
        self.dietary_preferences = value


class UserGoal(Base):
    """User fitness/nutrition goals"""
    __tablename__ = "user_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    goal_type = Column(String)  # weight_loss, muscle_gain, maintenance, etc.
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    target_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SocialActivity(Base):
    """Social feed activity"""
    __tablename__ = "social_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # workout, achievement, milestone
    content = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    likes = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class BiometricRecord(Base):
    """General biometric tracking records"""
    __tablename__ = "biometric_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    category = Column(String)  # steps, heart_rate, sleep, etc.
    value = Column(Float)
    unit = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FoodTrainingSample(Base):
    """
    Dedicated table for the 'Huge Dataset' training branch.
    Stores synthetic and real verfied food data for ML training.
    """
    __tablename__ = "food_training_dataset"
    
    id = Column(Integer, primary_key=True, index=True)
    image_signature = Column(String, nullable=True)  # Vector hash or S3 path
    label = Column(String, index=True)
    calories = Column(Float)
    protein = Column(Float, nullable=True)
    carbs = Column(Float, nullable=True)
    fats = Column(Float, nullable=True)
    source = Column(String)  # 'synthetic', 'user_correction', 'verified_upload'
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FemaleExerciseItem(Base):
    """Specialized exercises for women"""
    __tablename__ = "female_exercise_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("exercise_categories.id"))
    name = Column(String, index=True)
    targeted_muscle = Column(String, nullable=True)
    difficulty = Column(String, nullable=True) # Beginner, Intermediate, Advanced
    equipment = Column(String, nullable=True)
    calories_per_min = Column(Float, default=5.0)
    calories_per_rep = Column(Float, default=0.1)
    suitable_cycle_phase = Column(String, default="all") # Menstrual, Follicular, Ovulatory, Luteal, all
    description = Column(Text, nullable=True)
    
    category = relationship("ExerciseCategory")


class MenstrualCycleLog(Base):
    """Menstrual cycle tracking for female users"""
    __tablename__ = "menstrual_cycle_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # Clerk User ID
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    cycle_length_days = Column(Integer, default=28)
    
    # Store encrypted text format at application level to safeguard health data privacy
    symptoms = Column(JSON, nullable=True) # Or encrypted string representation
    mood = Column(String, nullable=True) # Or encrypted string representation
    flow_intensity = Column(String, nullable=True) # Or encrypted string representation
    notes = Column(Text, nullable=True) # Or encrypted string representation
    
    # Explicit application-layer encrypted fields columns (stores full cipher text)
    encrypted_symptoms = Column(Text, nullable=True)
    encrypted_mood = Column(Text, nullable=True)
    encrypted_flow_intensity = Column(Text, nullable=True)
    encrypted_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)



class UserFeedback(Base):
    """User feedback and satisfaction ratings for Smarty AI."""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)

    # Rating: 1–5 stars
    rating = Column(Integer, nullable=False)

    # Category: bug_report | feature_request | general | ai_quality | ux | performance
    category = Column(String, nullable=False, default="general")

    # The feedback text
    message = Column(Text, nullable=False)

    # Optional: which page/module the feedback is about
    module = Column(String, nullable=True)  # e.g. "workout", "nutrition", "ai_chat"

    # Sentiment: positive | neutral | negative (auto-computed or AI)
    sentiment = Column(String, nullable=True)

    # Status: open | reviewed | resolved
    status = Column(String, default="open")

    # Optional AI-generated acknowledgement
    ai_response = Column(Text, nullable=True)

    # Is it anonymous?
    is_anonymous = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyTask(Base):
    """Daily checklist task for a user"""
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    priority = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_auto = Column(Boolean, default=False)
    source = Column(String(50), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("EnhancedUser", backref="daily_tasks")


class SmartNextMove(Base):
    """AI-generated next-action recommendation based on user state"""
    __tablename__ = "smart_next_moves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    tasks_completed_today = Column(Integer, default=0)
    tasks_pending_today = Column(Integer, default=0)
    calories_consumed = Column(Float, default=0.0)
    calories_burned = Column(Float, default=0.0)
    water_intake_ml = Column(Float, default=0.0)
    current_time_category = Column(String(20), nullable=True)

    next_action_title = Column(String(200), nullable=False)
    next_action_description = Column(Text, nullable=True)
    next_action_category = Column(String(50), nullable=False)
    next_action_route = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=True)
    is_femme_mode = Column(Boolean, default=False)

    generated_at = Column(DateTime, default=datetime.utcnow)
    acted_upon = Column(Boolean, default=False)

    user = relationship("EnhancedUser", backref="smart_next_moves")


class FemaleCycleEntry(Base):
    """Detailed menstrual cycle tracking with symptoms"""
    __tablename__ = "female_cycle_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    phase = Column(String(30), nullable=True)
    symptoms = Column(JSON, nullable=True)
    energy_level = Column(Integer, nullable=True)
    mood = Column(String(30), nullable=True)
    flow_intensity = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("EnhancedUser", backref="cycle_entries")


# ============= SOCIAL FEED =============

class SocialPost(Base):
    """Social feed posts"""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    post_type = Column(String, default="status")  # status, workout, achievement, progress
    workout_data = Column(JSON, nullable=True)
    achievement_data = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("EnhancedUser", backref="social_posts")
    comments = relationship("SocialComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("SocialLike", back_populates="post", cascade="all, delete-orphan")


class SocialComment(Base):
    """Comments on social posts"""
    __tablename__ = "social_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("SocialPost", back_populates="comments")
    user = relationship("EnhancedUser")


class SocialLike(Base):
    """Likes on social posts"""
    __tablename__ = "social_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("SocialPost", back_populates="likes")
    user = relationship("EnhancedUser")


class SocialFollow(Base):
    """User follow relationships"""
    __tablename__ = "social_follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= ACTIVITY TRACKER =============

class ActivitySession(Base):
    """GPS activity tracking sessions"""
    __tablename__ = "activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, default="running")  # running, walking, hiking
    duration_seconds = Column(Integer, default=0)
    distance_km = Column(Float, default=0.0)
    calories = Column(Integer, default=0)
    avg_pace = Column(String, nullable=True)
    avg_speed = Column(Float, default=0.0)
    label = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("EnhancedUser", backref="activity_sessions")
    route_points = relationship("ActivityRoutePoint", back_populates="session", cascade="all, delete-orphan")


class ActivityRoutePoint(Base):
    """GPS route points for activity sessions"""
    __tablename__ = "activity_route_points"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("activity_sessions.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ActivitySession", back_populates="route_points")


# ============= MEAL PLANNER =============

class MealPlan(Base):
    """Weekly meal plans"""
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("EnhancedUser", backref="meal_plans")
    entries = relationship("MealPlanEntry", back_populates="plan", cascade="all, delete-orphan")


class MealPlanEntry(Base):
    """Individual meals within a meal plan"""
    __tablename__ = "meal_plan_entries"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday .. 6=Sunday
    meal_slot = Column(String, nullable=False)  # breakfast, lunch, dinner, snack
    food_name = Column(String, nullable=False)
    serving_size = Column(String, nullable=True)
    calories = Column(Float, default=0)
    protein = Column(Float, default=0)
    carbs = Column(Float, default=0)
    fats = Column(Float, default=0)
    food_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("MealPlan", back_populates="entries")


# ============= FORM COACH =============

class FormCoachSession(Base):
    """Form correction sessions"""
    __tablename__ = "form_coach_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise = Column(String, nullable=False)  # squat, pushup, plank, lunge, curl
    duration_seconds = Column(Integer, default=0)
    rep_count = Column(Integer, default=0)
    feedback_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("EnhancedUser", backref="form_coach_sessions")
    feedback_logs = relationship("FormFeedbackLog", back_populates="session", cascade="all, delete-orphan")


class FormFeedbackLog(Base):
    """Individual form feedback events"""
    __tablename__ = "form_feedback_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("form_coach_sessions.id"), nullable=False)
    message = Column(Text, nullable=False)
    feedback_type = Column(String, default="info")  # good, bad, info
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("FormCoachSession", back_populates="feedback_logs")


# ============= WEARABLE INTEGRATIONS =============

class WearableConnection(Base):
    """Connected wearable device accounts"""
    __tablename__ = "wearable_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False)  # apple_health, garmin, fitbit, whoop, oura
    device_name = Column(String, nullable=False)
    connected = Column(Boolean, default=True)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("EnhancedUser", backref="wearable_connections")
    metrics = relationship("WearableMetric", back_populates="connection", cascade="all, delete-orphan")


class WearableMetric(Base):
    """Synced metrics from wearable devices"""
    __tablename__ = "wearable_metrics"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("wearable_connections.id"), nullable=False)
    metric_type = Column(String, nullable=False)  # steps, heart_rate, sleep, hrv, spo2, calories
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    connection = relationship("WearableConnection", back_populates="metrics")


# ============= REMINDERS & NOTIFICATIONS =============

class Reminder(Base):
    """User reminder settings"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    time = Column(String, nullable=False)  # HH:MM format
    days = Column(JSON, nullable=False)  # [0,1,2,3,4,5,6]
    enabled = Column(Boolean, default=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("EnhancedUser", backref="reminders")


class NotificationLog(Base):
    """Notification history log"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    source = Column(String, nullable=True)  # reminder, system, social
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("EnhancedUser", backref="notification_logs")


class SubscriptionPlan(Base):
    """Subscription plans available in the product"""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    stripe_price_id = Column(String, nullable=True)  # Stripe Price/Price ID
    billing_interval = Column(String, default="month")  # month | year
    price_cents = Column(Integer, default=0)
    currency = Column(String, default="usd")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSubscription(Base):
    """Track a user's subscription status and Stripe subscription id"""
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    stripe_subscription_id = Column(String, nullable=True)
    status = Column(String, default="trialing")  # active, past_due, canceled, unpaid
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("SubscriptionPlan")
    user = relationship("EnhancedUser", backref="subscriptions")


class PaymentTransaction(Base):
    """Record of individual payment transactions"""
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    stripe_payment_intent = Column(String, nullable=True)
    stripe_charge_id = Column(String, nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="usd")
    status = Column(String, nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """Basic invoice record pointing to Stripe invoice objects"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    stripe_invoice_id = Column(String, nullable=True)
    amount_due_cents = Column(Integer, nullable=True)
    paid = Column(Boolean, default=False)
    hosted_invoice_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Gamified Streak & Entitlement Models ---

class ActivityEvent(Base):
    """Event-sourced Daily Logging Activity"""
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False) # "meal_log", "workout_completed", "app_login"
    local_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    timezone_offset_minutes = Column(Integer, default=0, nullable=False)


class StreakState(Base):
    """Streak tracker cache details"""
    __tablename__ = "streak_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    freezes_remaining = Column(Integer, default=3, nullable=False)
    last_computed_at = Column(DateTime, default=datetime.utcnow)


class FreezeLog(Base):
    """Auditable log of when streak freezes are spent"""
    __tablename__ = "freeze_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    date_missed = Column(String, nullable=False) # e.g. "2026-07-02"
    timestamp_spent = Column(DateTime, default=datetime.utcnow)


class Entitlement(Base):
    """User Entitlement & Feature Flag Roles"""
    __tablename__ = "entitlements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    feature_code = Column(String, index=True, nullable=False) # e.g. "RULE_TRACE", "PROGRESSIVE_OVERLOAD"
    granted = Column(Boolean, default=False, nullable=False)


class ProductEvent(Base):
    """Telemetry Events Table for Onboarding & Retention Funnels"""
    __tablename__ = "product_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    event_name = Column(String, index=True, nullable=False) # e.g. "onboarding_start", "onboarding_complete"
    properties_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class CoachFeedback(Base):
    """Feedback for workouts, meals, or general daily plans"""
    __tablename__ = "coach_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    domain = Column(String, nullable=False)  # "exercise" | "meal" | "daily_plan"
    item_id = Column(String, nullable=False)  # exercise_id or meal_log_id or plan_date
    rating = Column(Integer, nullable=False)  # 1-5 or boolean (1/0)
    context_json = Column(JSON, nullable=True)  # profile snapshot at feedback time
    created_at = Column(DateTime, default=datetime.utcnow)




