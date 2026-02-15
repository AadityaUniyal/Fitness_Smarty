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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    description = Column(Text, nullable=True)
    
    category = relationship("ExerciseCategory", back_populates="exercises")


class FoodCategory(Base):
    """Food categories"""
    __tablename__ = "food_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    foods = relationship("FoodItem", back_populates="category")


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
    
    category = relationship("FoodCategory", back_populates="foods")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class Achievement(Base):
    """User achievements/badges"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    badge_type = Column(String, nullable=True)
    earned_at = Column(DateTime, default=datetime.utcnow)


class BiometricRecord(Base):
    """General biometric tracking records"""
    __tablename__ = "biometric_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    category = Column(String)  # steps, heart_rate, sleep, etc.
    value = Column(Float)
    unit = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
