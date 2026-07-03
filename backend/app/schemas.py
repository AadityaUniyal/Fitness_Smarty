
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AchievementBase(BaseModel):
    title: str
    description: str
    icon: str
    unlocked_at: datetime

class UserResponse(BaseModel):
    id: str
    name: str
    level: int
    xp: int
    weight: float
    height: float
    goal: str
    achievements: List[AchievementBase] = []
    daily_calories: int = 0
    daily_steps: int = 0
    heart_rate: int = 0

class BiometricCreate(BaseModel):
    category: str
    value: float

class FaultCreate(BaseModel):
    part: str
    status: str
    feedback: str

class MealCreate(BaseModel):
    food_name: str
    calories: int

class SocialItem(BaseModel):
    operator_name: str
    activity_type: str
    content: str
    timestamp: datetime

# --- NEW ANALYTICS SCHEMAS ---

class ForecastPoint(BaseModel):
    day: int
    value: float

class ForecastResponse(BaseModel):
    trend: str
    slope: float
    projected_milestone: float
    confidence_score: float
    data_points: List[ForecastPoint]

class SleepProtocolResponse(BaseModel):
    protocol: str
    actions: List[str]
    intensity_cap: str

class PeerBenchmarkResponse(BaseModel):
    global_average_steps: float
    your_average_steps: float
    percentile_rank: float
    rank_title: str
    community_status: str

class AnalyticsReport(BaseModel):
    category: str
    average: float
    trend: str
    data_points: List[Any]

# --- NUTRITION SCHEMAS ---
class FoodItemBase(BaseModel):
    id: int
    name: str
    calories: int
    protein: float
    carbs: float
    fats: float
    serving_size: str
    is_elite: bool
    target_muscle_group: Optional[str] = None
    recommended_for_goal: Optional[str] = None
    
    class Config: from_attributes = True

class FoodCategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    items: List[FoodItemBase] = []
    class Config: from_attributes = True

# --- EXERCISE SCHEMAS ---
class ExerciseItemBase(BaseModel):
    id: int
    name: str
    description: str
    targeted_muscle: str
    difficulty: str
    equipment: str
    calories_per_min: float
    calories_per_rep: float  # New
    class Config: from_attributes = True

class ExerciseCategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    items: List[ExerciseItemBase] = []
    class Config: from_attributes = True

# --- ENHANCED EXERCISE SCHEMAS ---
class ExerciseBase(BaseModel):
    id: str
    name: str
    category: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty_level: str
    instructions: str
    safety_notes: str
    created_at: datetime
    class Config: from_attributes = True

class ExerciseCreate(BaseModel):
    name: str
    category: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty_level: str
    instructions: str
    safety_notes: str

class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    instructions: Optional[str] = None
    safety_notes: Optional[str] = None

class ExerciseSearchRequest(BaseModel):
    name_query: Optional[str] = None
    category: Optional[str] = None
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    limit: int = 100
    offset: int = 0

class ExerciseModificationsResponse(BaseModel):
    base_exercise: ExerciseBase
    easier: List[ExerciseBase]
    harder: List[ExerciseBase]

class ExerciseRecommendationRequest(BaseModel):
    user_experience_level: str
    target_muscle_groups: List[str]
    available_equipment: Optional[List[str]] = None
    limit: int = 10

class ExerciseValidationResponse(BaseModel):
    is_complete: bool
    missing_fields: List[str]


# --- USER PROFILE AND GOAL SCHEMAS ---
class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    age: Optional[int]
    weight_kg: Optional[float]
    height_cm: Optional[int]
    activity_level: str
    primary_goal: str
    dietary_restrictions: List[str]
    allergies: List[str]
    femmecare_enabled: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            # Ensure UUIDs are serialized as strings
            'UUID': lambda v: str(v)
        }
    
    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle UUID conversion"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            # Convert UUID objects to strings
            if 'id' in data and hasattr(data['id'], 'hex'):
                data['id'] = str(data['id'])
            if 'user_id' in data and hasattr(data['user_id'], 'hex'):
                data['user_id'] = str(data['user_id'])
            return cls(**data)
        return super().model_validate(obj)

class UserGoalResponse(BaseModel):
    id: str
    user_id: str
    goal_type: str
    target_value: float
    current_value: float
    target_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            'UUID': lambda v: str(v)
        }
    
    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle UUID conversion"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            if 'id' in data and hasattr(data['id'], 'hex'):
                data['id'] = str(data['id'])
            if 'user_id' in data and hasattr(data['user_id'], 'hex'):
                data['user_id'] = str(data['user_id'])
            return cls(**data)
        return super().model_validate(obj)

class ProfileValidationResponse(BaseModel):
    is_complete: bool
    missing_fields: List[str]
    warnings: List[str]
    suggestions: List[str]

class GoalValidationResponse(BaseModel):
    is_realistic: bool
    warnings: List[str]
    suggestions: List[str]
    recommended_timeline: Optional[str]

class ProgressMetricsResponse(BaseModel):
    goal_id: str
    goal_type: str
    progress_percentage: float
    current_value: float
    target_value: float
    days_remaining: Optional[int]
    is_on_track: bool

# --- MEAL ANALYSIS SCHEMAS ---
class MealPhotoUploadRequest(BaseModel):
    user_id: str
    meal_type: str  # breakfast, lunch, dinner, snack
    image_data: str  # base64 encoded image

class DetectedFoodItem(BaseModel):
    food_id: Optional[str]
    name: str
    estimated_quantity_g: float
    confidence_score: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

class MealAnalysisResponse(BaseModel):
    meal_log_id: str
    user_id: str
    meal_type: str
    image_url: str
    analysis_confidence: float
    detected_foods: List[DetectedFoodItem]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    recommendations: List[str]
    logged_at: datetime

class MealHistoryItem(BaseModel):
    meal_log_id: str
    meal_type: str
    logged_at: datetime
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    image_url: Optional[str]
    detected_foods_count: int

class MealHistoryResponse(BaseModel):
    meals: List[MealHistoryItem]
    total_count: int
    page: int
    page_size: int

class DailyNutritionSummary(BaseModel):
    date: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    meal_count: int
    meals_by_type: Dict[str, int]

# --- USER PROFILE SCHEMAS ---
class UserProfileCreate(BaseModel):
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[int] = None
    activity_level: str = "moderate"
    primary_goal: str = "maintenance"
    dietary_restrictions: List[str] = []
    allergies: List[str] = []

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[int] = None
    activity_level: Optional[str] = None
    primary_goal: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    femmecare_enabled: Optional[bool] = None

# --- GOAL SCHEMAS ---
class GoalCreate(BaseModel):
    goal_type: str  # daily_calories, weekly_exercise, weight_target
    target_value: float
    target_date: Optional[str] = None

class GoalUpdate(BaseModel):
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    target_date: Optional[str] = None
    is_active: Optional[bool] = None

class GoalListResponse(BaseModel):
    goals: List[UserGoalResponse]
    total_count: int

# --- RECOMMENDATION SCHEMAS ---
class RecommendationItem(BaseModel):
    id: str
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    is_read: bool
    created_at: datetime
    expires_at: Optional[datetime]

class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationItem]
    total_count: int
    unread_count: int
# --- FEMME CARE SCHEMAS ---

class FemaleExerciseItemBase(BaseModel):
    id: int
    name: str
    targeted_muscle: Optional[str]
    difficulty: str
    equipment: str
    calories_per_min: float
    suitable_cycle_phase: str
    description: Optional[str]
    
    class Config: from_attributes = True

class MenstrualCycleLogBase(BaseModel):
    id: int
    user_id: str
    start_date: datetime
    end_date: Optional[datetime]
    cycle_length_days: int
    symptoms: Optional[List[str]]
    mood: Optional[str]
    flow_intensity: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config: from_attributes = True

class MenstrualCycleLogCreate(BaseModel):
    start_date: datetime
    end_date: Optional[datetime] = None
    symptoms: Optional[List[str]] = []
    mood: Optional[str] = None
    flow_intensity: Optional[str] = None
    notes: Optional[str] = None


# ============= SOCIAL FEED SCHEMAS =============

class SocialPostCreate(BaseModel):
    text: str
    post_type: str = "status"
    workout_data: Optional[Dict[str, Any]] = None
    achievement_data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None

class SocialPostResponse(BaseModel):
    id: int
    user_id: int
    user_name: str = ""
    user_avatar: str = ""
    text: str
    post_type: str
    workout_data: Optional[Dict[str, Any]] = None
    achievement_data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    created_at: datetime

    class Config: from_attributes = True

class SocialCommentCreate(BaseModel):
    text: str

class SocialCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_name: str = ""
    user_avatar: str = ""
    text: str
    created_at: datetime

    class Config: from_attributes = True

class SocialFeedResponse(BaseModel):
    posts: List[SocialPostResponse]
    total_count: int
    page: int
    page_size: int


# ============= ACTIVITY TRACKER SCHEMAS =============

class RoutePointCreate(BaseModel):
    lat: float
    lng: float
    timestamp: Optional[datetime] = None

class ActivitySessionCreate(BaseModel):
    activity_type: str = "running"
    duration_seconds: int = 0
    distance_km: float = 0.0
    calories: int = 0
    avg_pace: Optional[str] = None
    avg_speed: float = 0.0
    label: Optional[str] = None
    route_points: List[RoutePointCreate] = []

class RoutePointResponse(BaseModel):
    id: int
    lat: float
    lng: float
    timestamp: datetime

    class Config: from_attributes = True

class ActivitySessionResponse(BaseModel):
    id: int
    activity_type: str
    duration_seconds: int
    distance_km: float
    calories: int
    avg_pace: Optional[str]
    avg_speed: float
    label: Optional[str]
    started_at: datetime
    created_at: datetime
    route_points: List[RoutePointResponse] = []

    class Config: from_attributes = True

class ActivityListResponse(BaseModel):
    sessions: List[ActivitySessionResponse]
    total_count: int
    page: int
    page_size: int


# ============= MEAL PLAN SCHEMAS =============

class MealPlanEntryCreate(BaseModel):
    day_of_week: int
    meal_slot: str
    food_name: str
    serving_size: Optional[str] = None
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fats: float = 0
    food_id: Optional[int] = None

class MealPlanCreate(BaseModel):
    week_start: str  # ISO date
    entries: List[MealPlanEntryCreate] = []

class MealPlanEntryResponse(BaseModel):
    id: int
    day_of_week: int
    meal_slot: str
    food_name: str
    serving_size: Optional[str]
    calories: float
    protein: float
    carbs: float
    fats: float
    food_id: Optional[int]

    class Config: from_attributes = True

class MealPlanResponse(BaseModel):
    id: int
    week_start: datetime
    week_end: Optional[datetime]
    entries: List[MealPlanEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config: from_attributes = True

class MealPlanGenerateRequest(BaseModel):
    week_start: str  # ISO date
    daily_calories: Optional[int] = None
    goal: Optional[str] = None
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    exclude_foods: List[str] = []


# ============= FORM COACH SCHEMAS =============

class FormFeedbackLogCreate(BaseModel):
    message: str
    feedback_type: str = "info"

class FormCoachSessionCreate(BaseModel):
    exercise: str
    duration_seconds: int = 0
    rep_count: int = 0
    feedback_summary: Optional[str] = None
    feedback_logs: List[FormFeedbackLogCreate] = []

class FormFeedbackLogResponse(BaseModel):
    id: int
    message: str
    feedback_type: str
    timestamp: datetime

    class Config: from_attributes = True

class FormCoachSessionResponse(BaseModel):
    id: int
    exercise: str
    duration_seconds: int
    rep_count: int
    feedback_summary: Optional[str]
    feedback_logs: List[FormFeedbackLogResponse] = []
    created_at: datetime

    class Config: from_attributes = True


# ============= WEARABLE INTEGRATION SCHEMAS =============

class WearableConnectRequest(BaseModel):
    device_id: str
    device_name: str
    access_token: Optional[str] = None

class WearableMetricCreate(BaseModel):
    metric_type: str
    value: float
    unit: Optional[str] = None
    recorded_at: Optional[datetime] = None

class WearableMetricResponse(BaseModel):
    id: int
    metric_type: str
    value: float
    unit: Optional[str]
    recorded_at: datetime

    class Config: from_attributes = True

class WearableConnectionResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    connected: bool
    last_sync: Optional[datetime]
    created_at: datetime
    metrics: List[WearableMetricResponse] = []

    class Config: from_attributes = True


# ============= REMINDER SCHEMAS =============

class ReminderCreate(BaseModel):
    label: str
    description: Optional[str] = None
    time: str
    days: List[int] = [0,1,2,3,4,5,6]
    enabled: bool = True
    icon: Optional[str] = None

class ReminderUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    time: Optional[str] = None
    days: Optional[List[int]] = None
    enabled: Optional[bool] = None
    icon: Optional[str] = None

class ReminderResponse(BaseModel):
    id: int
    label: str
    description: Optional[str]
    time: str
    days: List[int]
    enabled: bool
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config: from_attributes = True

class NotificationLogResponse(BaseModel):
    id: int
    title: str
    body: Optional[str]
    icon: Optional[str]
    source: Optional[str]
    read: bool
    created_at: datetime

    class Config: from_attributes = True
