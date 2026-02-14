
from fastapi import FastAPI, Depends, Query, Body, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app import EnhancedUser, MealLog, WorkoutLog, FoodDetection, BiometricReading, ProgressSnapshot, FoodItem, ExerciseItem
from app import recovery_engine, hydration_monitor, challenge_engine
from app import ai_analyzer, sleep_optimization, social_engine
from app.exercise_service import ExerciseService
from app.meal_analysis_service import MealAnalysisService
from app.user_profile_service import UserProfileService, UserProfileCreate as ServiceUserProfileCreate, UserProfileUpdate as ServiceUserProfileUpdate, GoalCreate as ServiceGoalCreate, GoalUpdate as ServiceGoalUpdate
from app.recommendation_engine import RecommendationEngine, RecommendationRequest
from app.api_validation import APIValidator, ErrorHandler, format_success_response
# Updated: Use Clerk authentication
from app.clerk_auth import get_current_user_from_clerk as get_current_user, get_current_user_id_from_clerk as get_current_user_id
from app.auth import AuthService, UserRegister, UserLogin, PasswordChange, Token  # Keep for backwards compatibility if needed
from datetime import datetime
import uuid
import base64
import os




app = FastAPI(title="Smarty AI Neural Infrastructure")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount API Routers
from app.meal_scanning_api import router as meal_router
from app.analytics_api import router as analytics_router
from app.recommendation_api import router as recommendation_router
from app.vision_api import router as vision_router  # Phase 1: Computer Vision
from app.nlp_api import router as nlp_router  # Phase 2: NLP & Language Models
from app.forecast_api import router as forecast_router  # Phase 3: Time-Series
from app.recommendation_api_v2 import router as recommendation_v2_router  # Phase 4: Advanced Recommendations
from app.rl_api import router as rl_router  # Phase 5: Reinforcement Learning
from app.explainability_api import router as explainability_router  # Phase 6: Explainability  
from app.mobile_api import router as mobile_router  # Phase 7: Mobile Deployment
from app.infrastructure_api import router as infrastructure_router  # Phase 8: Infrastructure

app.include_router(meal_router)
app.include_router(analytics_router)
app.include_router(recommendation_router)
app.include_router(vision_router)  # YOLOv8, ResNet, Hybrid Detection
app.include_router(nlp_router)  # BERT, CLIP
app.include_router(forecast_router)  # LSTM, Prophet
app.include_router(recommendation_v2_router)  # Collaborative + Content-Based Filtering
app.include_router(rl_router)  # DQN, Q-Learning
app.include_router(explainability_router)  # SHAP
app.include_router(mobile_router)  # ONNX, TFLite
app.include_router(infrastructure_router)  # Caching, Batch, Health


# Initialize DB and Seed Data Libraries
models.Base.metadata.create_all(bind=database.engine)
database.seed_nutrition_database()
database.seed_exercise_database()

# --- AI & ADVANCED ANALYTICS ---

@app.get("/neural/forecast", tags=["Neural Intelligence"], response_model=schemas.ForecastResponse)
def get_performance_forecast(
    db: Session = Depends(database.get_db), 
    user_id: str = Depends(security.validate_operator_link)
):
    """Predict future performance trends using the AI Analyzer engine."""
    return ai_analyzer.forecast_performance(db, user_id)

@app.get("/neural/plateau-status", tags=["Neural Intelligence"])
def check_for_plateaus(
    db: Session = Depends(database.get_db), 
    user_id: str = Depends(security.validate_operator_link)
):
    """Analyze historical progression for stagnation markers."""
    return ai_analyzer.detect_plateaus(db, user_id)

@app.get("/neural/sleep-protocol", tags=["Metabolic Monitoring"], response_model=schemas.SleepProtocolResponse)
def get_sleep_bio_protocol(
    db: Session = Depends(database.get_db), 
    user_id: str = Depends(security.validate_operator_link)
):
    """Retrieve recovery protocols based on sleep quality and strain."""
    # Mocking strain and quality for now; would normally fetch from DB
    return sleep_optimization.get_recovery_protocol(strain_score=72.5, sleep_quality=58.0)

# --- SOCIAL & COMMUNITY DATA ---

@app.get("/social/benchmarks", tags=["Social Synchronization"], response_model=schemas.PeerBenchmarkResponse)
def get_community_standing(
    db: Session = Depends(database.get_db), 
    user_id: str = Depends(security.validate_operator_link)
):
    """Compare performance against global anonymous neural network data."""
    return social_engine.get_peer_benchmarks(db, user_id)

# --- EXISTING ENDPOINTS ---

@app.get("/neural/recovery", tags=["Neural Diagnostics"])
def get_recovery_diagnostics(db: Session = Depends(database.get_db), user_id: str = Depends(security.validate_operator_link)):
    """Fetch AI-computed recovery score and readiness diagnostics."""
    return recovery_engine.calculate_recovery_score(db, user_id)

@app.get("/neural/hydration", tags=["Metabolic Monitoring"])
def get_hydration_protocol(db: Session = Depends(database.get_db), user_id: str = Depends(security.validate_operator_link)):
    """Calculate personalized fluid requirements based on current load."""
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    return hydration_monitor.get_hydration_requirement(user, activity_minutes=84)

@app.get("/social/challenges", tags=["Social Synchronization"])
def get_neural_challenges():
    """Retrieve active community challenges from the global network."""
    return challenge_engine.get_active_challenges()

@app.get("/nutrition/library", response_model=List[schemas.FoodCategoryResponse])
def get_nutrition_library(db: Session = Depends(database.get_db)):
    """Fetch all food categories and their associated elite items."""
    return db.query(models.FoodCategory).all()

@app.get("/nutrition/search", response_model=List[schemas.FoodItemBase])
def search_nutrition(
    q: Optional[str] = None, 
    category_id: Optional[int] = None, 
    db: Session = Depends(database.get_db)
):
    """Search for specific biofuel nodes based on query and category."""
    return nutrition_engine.search_biofuels(db, q, category_id)

@app.get("/exercise/library", response_model=List[schemas.ExerciseCategoryResponse])
def get_exercise_library(db: Session = Depends(database.get_db)):
    """Fetch all exercise categories and movements from the Neural Vault."""
    return db.query(models.ExerciseCategory).all()

# --- ENHANCED EXERCISE ENDPOINTS ---

@app.post("/exercises", response_model=schemas.ExerciseBase, tags=["Enhanced Exercises"])
def create_exercise(
    exercise_data: schemas.ExerciseCreate,
    db: Session = Depends(database.get_db)
):
    """Create a new exercise with comprehensive information"""
    try:
        exercise = ExerciseService.create_exercise(
            db=db,
            name=exercise_data.name,
            category=exercise_data.category,
            muscle_groups=exercise_data.muscle_groups,
            equipment=exercise_data.equipment,
            difficulty_level=exercise_data.difficulty_level,
            instructions=exercise_data.instructions,
            safety_notes=exercise_data.safety_notes
        )
        return exercise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/exercises/{exercise_id}", response_model=schemas.ExerciseBase, tags=["Enhanced Exercises"])
def get_exercise(
    exercise_id: str,
    db: Session = Depends(database.get_db)
):
    """Get a specific exercise by ID"""
    try:
        exercise_uuid = uuid.UUID(exercise_id)
        exercise = ExerciseService.get_exercise_by_id(db, exercise_uuid)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

@app.post("/exercises/search", response_model=List[schemas.ExerciseBase], tags=["Enhanced Exercises"])
def search_exercises(
    search_params: schemas.ExerciseSearchRequest,
    db: Session = Depends(database.get_db)
):
    """
    Advanced exercise search with multiple filters
    
    Supports filtering by:
    - Name (partial match)
    - Category (strength, cardio, flexibility, sports)
    - Muscle groups (exercises targeting at least one specified group)
    - Equipment (exercises using at least one specified equipment)
    - Difficulty level (beginner, intermediate, advanced)
    """
    exercises = ExerciseService.search_exercises(
        db=db,
        name_query=search_params.name_query,
        category=search_params.category,
        muscle_groups=search_params.muscle_groups,
        equipment=search_params.equipment,
        difficulty_level=search_params.difficulty_level,
        limit=search_params.limit,
        offset=search_params.offset
    )
    return exercises

@app.get("/exercises/difficulty/{difficulty_level}", response_model=List[schemas.ExerciseBase], tags=["Enhanced Exercises"])
def get_exercises_by_difficulty(
    difficulty_level: str,
    db: Session = Depends(database.get_db)
):
    """Get all exercises for a specific difficulty level"""
    try:
        exercises = ExerciseService.get_exercises_by_difficulty(db, difficulty_level)
        return exercises
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/exercises/muscle-group/{muscle_group}", response_model=List[schemas.ExerciseBase], tags=["Enhanced Exercises"])
def get_exercises_by_muscle_group(
    muscle_group: str,
    db: Session = Depends(database.get_db)
):
    """Get all exercises targeting a specific muscle group"""
    exercises = ExerciseService.get_exercises_by_muscle_group(db, muscle_group)
    return exercises

@app.put("/exercises/{exercise_id}", response_model=schemas.ExerciseBase, tags=["Enhanced Exercises"])
def update_exercise(
    exercise_id: str,
    exercise_data: schemas.ExerciseUpdate,
    db: Session = Depends(database.get_db)
):
    """Update an existing exercise"""
    try:
        exercise_uuid = uuid.UUID(exercise_id)
        # Filter out None values
        update_data = {k: v for k, v in exercise_data.dict().items() if v is not None}
        exercise = ExerciseService.update_exercise(db, exercise_uuid, **update_data)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/exercises/{exercise_id}", tags=["Enhanced Exercises"])
def delete_exercise(
    exercise_id: str,
    db: Session = Depends(database.get_db)
):
    """Delete an exercise"""
    try:
        exercise_uuid = uuid.UUID(exercise_id)
        success = ExerciseService.delete_exercise(db, exercise_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return {"message": "Exercise deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

@app.get("/exercises/{exercise_id}/modifications", response_model=schemas.ExerciseModificationsResponse, tags=["Enhanced Exercises"])
def get_exercise_modifications(
    exercise_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get exercise modifications and alternatives
    
    Returns easier and harder variations of the exercise
    based on difficulty level and muscle groups
    """
    try:
        exercise_uuid = uuid.UUID(exercise_id)
        base_exercise = ExerciseService.get_exercise_by_id(db, exercise_uuid)
        if not base_exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        modifications = ExerciseService.get_exercise_modifications(db, exercise_uuid)
        return {
            "base_exercise": base_exercise,
            "easier": modifications['easier'],
            "harder": modifications['harder']
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

@app.post("/exercises/recommend", response_model=List[schemas.ExerciseBase], tags=["Enhanced Exercises"])
def recommend_exercises(
    recommendation_params: schemas.ExerciseRecommendationRequest,
    db: Session = Depends(database.get_db)
):
    """
    Get personalized exercise recommendations
    
    Based on user experience level, target muscle groups, and available equipment
    """
    try:
        exercises = ExerciseService.recommend_exercises(
            db=db,
            user_experience_level=recommendation_params.user_experience_level,
            target_muscle_groups=recommendation_params.target_muscle_groups,
            available_equipment=recommendation_params.available_equipment,
            limit=recommendation_params.limit
        )
        return exercises
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/exercises/{exercise_id}/validate", response_model=schemas.ExerciseValidationResponse, tags=["Enhanced Exercises"])
def validate_exercise_completeness(
    exercise_id: str,
    db: Session = Depends(database.get_db)
):
    """Validate that an exercise has all required information"""
    try:
        exercise_uuid = uuid.UUID(exercise_id)
        exercise = ExerciseService.get_exercise_by_id(db, exercise_uuid)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        validation_result = ExerciseService.validate_exercise_completeness(exercise)
        return validation_result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid exercise ID format")

@app.get("/users/me", response_model=schemas.UserResponse)
def get_current_operator(
    db: Session = Depends(database.get_db), 
    user_id: str = Depends(security.validate_operator_link)
):
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    if not user:
        user = EnhancedUser(id=user_id, username="operator_alex", email="alex@smarty.com", weight_kg=80.0, height_cm=180.0, primary_goal="Athletic")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {**user.__dict__, "achievements": user.achievements, "daily_calories": 2450, "daily_steps": 12402, "heart_rate": 72}

@app.get("/social/feed", response_model=List[schemas.SocialItem])
def get_global_feed(db: Session = Depends(database.get_db)):
    feed = db.query(models.SocialActivity).order_by(models.SocialActivity.timestamp.desc()).limit(10).all()
    if not feed:
        return [
            {"operator_name": "Unit_7", "activity_type": "WORKOUT", "content": "Completed Leg Protocol", "timestamp": datetime.utcnow()},
            {"operator_name": "Zero_One", "activity_type": "LEVEL_UP", "content": "Reached Neural Tier 5!", "timestamp": datetime.utcnow()}
        ]
    return feed

# --- AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/register", response_model=Token, tags=["Authentication"])
def register(
    user_data: UserRegister,
    db: Session = Depends(database.get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **name**: User's name
    
    Returns JWT access and refresh tokens
    """
    auth_service = AuthService(db)
    
    try:
        # Register user
        user = auth_service.register_user(user_data)
        
        # Automatically log in and return tokens
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        tokens = auth_service.login(login_data)
        
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Registration failed: {str(e)}")


@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
def login(
    login_data: UserLogin,
    db: Session = Depends(database.get_db)
):
    """
    Login with email and password
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT access and refresh tokens
    """
    auth_service = AuthService(db)
    
    try:
        tokens = auth_service.login(login_data)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Login failed: {str(e)}")


@app.post("/api/auth/refresh", response_model=Token, tags=["Authentication"])
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(database.get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new JWT access and refresh tokens
    """
    auth_service = AuthService(db)
    
    try:
        tokens = auth_service.refresh_access_token(refresh_token)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Token refresh failed: {str(e)}")


@app.post("/api/auth/change-password", tags=["Authentication"])
def change_password(
    password_data: PasswordChange,
    current_user: models.EnhancedUser = Depends(require_auth),
    db: Session = Depends(database.get_db)
):
    """
    Change user password (requires authentication)
    
    - **current_password**: Current password
    - **new_password**: New strong password
    
    Returns success message
    """
    auth_service = AuthService(db)
    
    try:
        success = auth_service.change_password(str(current_user.id), password_data)
        if success:
            return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise ErrorHandler.internal_error(f"Password change failed: {str(e)}")


@app.get("/api/auth/me", tags=["Authentication"])
def get_current_user_info(
    current_user: models.EnhancedUser = Depends(require_auth)
):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


@app.post("/api/auth/logout", tags=["Authentication"])
def logout(current_user: models.EnhancedUser = Depends(require_auth)):
    """
    Logout user (client should discard tokens)
    
    Requires valid JWT token in Authorization header
    """
    return {"message": "Logged out successfully"}

# --- MEAL PHOTO UPLOAD AND ANALYSIS ENDPOINTS ---

@app.post("/api/meals/analyze", response_model=schemas.MealAnalysisResponse, tags=["Meal Analysis"])
def analyze_meal_photo(
    user_id: str = Body(...),
    meal_type: str = Body(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    """
    Upload and analyze a meal photo
    
    - **user_id**: User identifier
    - **meal_type**: Type of meal (breakfast, lunch, dinner, snack)
    - **image_file**: Image file to analyze
    
    Returns detailed nutritional analysis with detected foods and recommendations
    """
    # Validate user_id
    user_validation = APIValidator.validate_user_id(user_id)
    if not user_validation.is_valid:
        raise ErrorHandler.validation_error(user_validation.errors)
    
    # Validate meal_type
    meal_type_validation = APIValidator.validate_meal_type(meal_type)
    if not meal_type_validation.is_valid:
        raise ErrorHandler.validation_error(meal_type_validation.errors)
    
    # Read image data
    try:
        image_data = image_file.file.read()
    except Exception as e:
        raise ErrorHandler.bad_request_error(f"Failed to read image file: {str(e)}")
    
    # Validate image file
    image_validation = APIValidator.validate_image_file(image_data)
    if not image_validation.is_valid:
        raise ErrorHandler.validation_error(image_validation.errors)
    
    # Analyze meal
    service = MealAnalysisService(db)
    try:
        result = service.analyze_meal_photo(
            image_bytes=image_data,
            user_id=user_id,
            meal_type=meal_type
        )
        
        # Check if analysis was successful
        if not result.success:
            raise ErrorHandler.bad_request_error(result.error_message or "Meal analysis failed")
        
        # Format response - flatten detected foods nutrition data
        formatted_detected_foods = []
        for food in result.detected_foods:
            nutrition = food.get('nutrition', {})
            formatted_food = {
                "food_id": food.get('food_id'),
                "name": food.get('food_name', ''),
                "estimated_quantity_g": food.get('estimated_quantity_g', 0),
                "confidence_score": food.get('confidence_score', 0),
                "calories": nutrition.get('calories', 0),
                "protein_g": nutrition.get('protein_g', 0),
                "carbs_g": nutrition.get('carbs_g', 0),
                "fat_g": nutrition.get('fat_g', 0)
            }
            formatted_detected_foods.append(formatted_food)
        
        return {
            "meal_log_id": result.meal_log_id,
            "user_id": user_id,
            "meal_type": meal_type,
            "image_url": result.image_url,
            "analysis_confidence": result.analysis_confidence,
            "detected_foods": formatted_detected_foods,
            "total_calories": result.total_nutrition.get('calories', 0),
            "total_protein_g": result.total_nutrition.get('protein_g', 0),
            "total_carbs_g": result.total_nutrition.get('carbs_g', 0),
            "total_fat_g": result.total_nutrition.get('fat_g', 0),
            "recommendations": result.recommendations,
            "logged_at": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise ErrorHandler.bad_request_error(str(e))
    except Exception as e:
        raise ErrorHandler.internal_error(f"Meal analysis failed: {str(e)}")

@app.get("/api/meals/{meal_log_id}", tags=["Meal Analysis"])
def get_meal_details(
    meal_log_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get detailed information about a specific meal log
    """
    service = MealAnalysisService(db)
    meal_log = service.get_meal_log(meal_log_id)
    
    if not meal_log:
        raise HTTPException(status_code=404, detail="Meal log not found")
    
    return meal_log

@app.get("/api/meals/user/{user_id}/history", response_model=schemas.MealHistoryResponse, tags=["Meal Analysis"])
def get_user_meal_history(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(database.get_db)
):
    """
    Get historical meal logs for a user with filtering and pagination
    """
    # Validate user_id
    user_validation = APIValidator.validate_user_id(user_id)
    if not user_validation.is_valid:
        raise ErrorHandler.validation_error(user_validation.errors)
    
    # Validate pagination
    pagination_validation = APIValidator.validate_pagination(limit, offset)
    if not pagination_validation.is_valid:
        raise ErrorHandler.validation_error(pagination_validation.errors)
    
    # Validate meal_type if provided
    if meal_type:
        meal_type_validation = APIValidator.validate_meal_type(meal_type)
        if not meal_type_validation.is_valid:
            raise ErrorHandler.validation_error(meal_type_validation.errors)
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    
    if start_date:
        date_validation = APIValidator.validate_date_format(start_date, "start_date")
        if not date_validation.is_valid:
            raise ErrorHandler.validation_error(date_validation.errors)
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise ErrorHandler.bad_request_error("Invalid start_date format. Use ISO format.")
    
    if end_date:
        date_validation = APIValidator.validate_date_format(end_date, "end_date")
        if not date_validation.is_valid:
            raise ErrorHandler.validation_error(date_validation.errors)
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise ErrorHandler.bad_request_error("Invalid end_date format. Use ISO format.")
    
    service = MealAnalysisService(db)
    try:
        history = service.get_user_meal_history(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            meal_type=meal_type,
            limit=limit,
            offset=offset
        )
        
        return {
            "meals": history['meals'],
            "total_count": history['total_count'],
            "page": offset // limit + 1,
            "page_size": limit
        }
    except Exception as e:
        raise ErrorHandler.internal_error(f"Failed to retrieve meal history: {str(e)}")

@app.get("/api/meals/user/{user_id}/daily-summary", response_model=schemas.DailyNutritionSummary, tags=["Meal Analysis"])
def get_daily_nutrition_summary(
    user_id: str,
    date: Optional[str] = Query(None, description="Date (ISO format, defaults to today)"),
    db: Session = Depends(database.get_db)
):
    """
    Get nutrition summary for a specific day
    """
    # Parse date if provided
    target_date = None
    if date:
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    service = MealAnalysisService(db)
    summary = service.get_daily_nutrition_summary(user_id=user_id, date=target_date)
    
    # Flatten the response to match schema
    total_nutrition = summary.get('total_nutrition', {})
    meals_by_type = summary.get('meals_by_type', {})
    
    # Convert meals_by_type from lists to counts
    meals_by_type_counts = {
        meal_type: len(meals)
        for meal_type, meals in meals_by_type.items()
    }
    
    return {
        'date': summary.get('date'),
        'total_calories': total_nutrition.get('calories', 0),
        'total_protein_g': total_nutrition.get('protein_g', 0),
        'total_carbs_g': total_nutrition.get('carbs_g', 0),
        'total_fat_g': total_nutrition.get('fat_g', 0),
        'meal_count': summary.get('meal_count', 0),
        'meals_by_type': meals_by_type_counts
    }

# --- USER PROFILE ENDPOINTS ---

@app.post("/api/users/{user_id}/profile", response_model=schemas.UserProfileResponse, tags=["User Profile"])
def create_user_profile(
    user_id: str,
    profile_data: schemas.UserProfileCreate,
    db: Session = Depends(database.get_db)
):
    """
    Create a user profile with personal information and preferences
    
    - **age**: User's age
    - **weight_kg**: Weight in kilograms
    - **height_cm**: Height in centimeters
    - **activity_level**: Activity level (sedentary, light, moderate, active, very_active)
    - **primary_goal**: Primary fitness goal (weight_loss, weight_gain, muscle_gain, maintenance, athletic_performance)
    - **dietary_restrictions**: List of dietary restrictions
    - **allergies**: List of food allergies
    """
    # Validate user_id
    user_validation = APIValidator.validate_user_id(user_id)
    if not user_validation.is_valid:
        raise ErrorHandler.validation_error(user_validation.errors)
    
    # Validate activity_level
    activity_validation = APIValidator.validate_activity_level(profile_data.activity_level)
    if not activity_validation.is_valid:
        raise ErrorHandler.validation_error(activity_validation.errors)
    
    # Validate primary_goal
    goal_validation = APIValidator.validate_primary_goal(profile_data.primary_goal)
    if not goal_validation.is_valid:
        raise ErrorHandler.validation_error(goal_validation.errors)
    
    # Validate numeric ranges
    if profile_data.age is not None:
        age_validation = APIValidator.validate_numeric_range(profile_data.age, "age", 1, 150)
        if not age_validation.is_valid:
            raise ErrorHandler.validation_error(age_validation.errors)
    
    if profile_data.weight_kg is not None:
        weight_validation = APIValidator.validate_numeric_range(profile_data.weight_kg, "weight_kg", 20, 500)
        if not weight_validation.is_valid:
            raise ErrorHandler.validation_error(weight_validation.errors)
    
    if profile_data.height_cm is not None:
        height_validation = APIValidator.validate_numeric_range(profile_data.height_cm, "height_cm", 50, 300)
        if not height_validation.is_valid:
            raise ErrorHandler.validation_error(height_validation.errors)
    
    service = UserProfileService(db)
    
    # Check if profile already exists
    existing_profile = service.get_user_profile(user_id)
    if existing_profile:
        raise ErrorHandler.conflict_error("User profile already exists. Use PUT to update.")
    
    try:
        # Convert schema to service model
        service_profile_data = ServiceUserProfileCreate(
            age=profile_data.age,
            weight_kg=profile_data.weight_kg,
            height_cm=profile_data.height_cm,
            activity_level=profile_data.activity_level,
            primary_goal=profile_data.primary_goal,
            dietary_restrictions=profile_data.dietary_restrictions,
            allergies=profile_data.allergies
        )
        
        profile = service.create_user_profile(user_id, service_profile_data)
        # Convert UUID fields to strings for response
        return schemas.UserProfileResponse.model_validate(profile)
    except ValueError as e:
        raise ErrorHandler.bad_request_error(str(e))

@app.get("/api/users/{user_id}/profile", response_model=schemas.UserProfileResponse, tags=["User Profile"])
def get_user_profile(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get user profile information
    """
    service = UserProfileService(db)
    profile = service.get_user_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Convert UUID fields to strings for response
    return schemas.UserProfileResponse.model_validate(profile)

@app.put("/api/users/{user_id}/profile", response_model=schemas.UserProfileResponse, tags=["User Profile"])
def update_user_profile(
    user_id: str,
    profile_data: schemas.UserProfileUpdate,
    db: Session = Depends(database.get_db)
):
    """
    Update user profile information
    """
    service = UserProfileService(db)
    
    try:
        # Convert schema to service model, preserving only set fields
        update_dict = profile_data.model_dump(exclude_unset=True)
        service_profile_data = ServiceUserProfileUpdate(**update_dict)
        
        profile = service.update_user_profile(user_id, service_profile_data)
        # Convert UUID fields to strings for response
        return schemas.UserProfileResponse.model_validate(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/{user_id}/profile/validate", response_model=schemas.ProfileValidationResponse, tags=["User Profile"])
def validate_user_profile(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Validate user profile completeness and provide suggestions
    """
    service = UserProfileService(db)
    
    try:
        validation_result = service.validate_profile(user_id)
        return {
            "is_complete": validation_result.is_complete,
            "missing_fields": validation_result.missing_fields,
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- GOAL SETTING AND TRACKING ENDPOINTS ---

@app.post("/api/users/{user_id}/goals", response_model=schemas.UserGoalResponse, tags=["Goals"])
def create_user_goal(
    user_id: str,
    goal_data: schemas.GoalCreate,
    db: Session = Depends(database.get_db)
):
    """
    Create a new fitness goal for the user
    
    - **goal_type**: Type of goal (daily_calories, weekly_exercise, weight_target)
    - **target_value**: Target value to achieve
    - **target_date**: Optional target date (ISO format)
    """
    # Validate user_id
    user_validation = APIValidator.validate_user_id(user_id)
    if not user_validation.is_valid:
        raise ErrorHandler.validation_error(user_validation.errors)
    
    # Validate goal_type
    goal_type_validation = APIValidator.validate_goal_type(goal_data.goal_type)
    if not goal_type_validation.is_valid:
        raise ErrorHandler.validation_error(goal_type_validation.errors)
    
    # Validate target_value
    target_validation = APIValidator.validate_numeric_range(
        goal_data.target_value, 
        "target_value", 
        0.1, 
        1000000
    )
    if not target_validation.is_valid:
        raise ErrorHandler.validation_error(target_validation.errors)
    
    # Validate target_date if provided
    if goal_data.target_date:
        date_validation = APIValidator.validate_date_format(goal_data.target_date, "target_date")
        if not date_validation.is_valid:
            raise ErrorHandler.validation_error(date_validation.errors)
    
    service = UserProfileService(db)
    
    try:
        # Convert schema to service model
        service_goal_data = ServiceGoalCreate(
            goal_type=goal_data.goal_type,
            target_value=goal_data.target_value,
            target_date=goal_data.target_date
        )
        
        goal = service.create_goal(user_id, service_goal_data)
        # Convert UUID fields to strings for response
        return schemas.UserGoalResponse.model_validate(goal)
    except ValueError as e:
        raise ErrorHandler.bad_request_error(str(e))

@app.get("/api/users/{user_id}/goals", response_model=schemas.GoalListResponse, tags=["Goals"])
def get_user_goals(
    user_id: str,
    active_only: bool = Query(True, description="Return only active goals"),
    db: Session = Depends(database.get_db)
):
    """
    Get all goals for a user
    """
    service = UserProfileService(db)
    goals = service.get_user_goals(user_id, active_only=active_only)
    
    # Convert UUID fields to strings for response
    goals_response = [schemas.UserGoalResponse.model_validate(goal) for goal in goals]
    
    return {
        "goals": goals_response,
        "total_count": len(goals_response)
    }

@app.put("/api/goals/{goal_id}", response_model=schemas.UserGoalResponse, tags=["Goals"])
def update_goal(
    goal_id: str,
    goal_data: schemas.GoalUpdate,
    db: Session = Depends(database.get_db)
):
    """
    Update an existing goal
    """
    service = UserProfileService(db)
    
    try:
        # Convert schema to service model
        service_goal_data = ServiceGoalUpdate(
            target_value=goal_data.target_value,
            current_value=goal_data.current_value,
            target_date=goal_data.target_date,
            is_active=goal_data.is_active
        )
        
        goal = service.update_goal(goal_id, service_goal_data)
        return goal
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/goals/{goal_id}/validate", response_model=schemas.GoalValidationResponse, tags=["Goals"])
def validate_goal(
    goal_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Validate if a goal is realistic and get recommendations
    """
    service = UserProfileService(db)
    
    # Get the goal
    goal = db.query(UserGoal).filter(UserGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Create goal data for validation
    goal_data = ServiceGoalCreate(
        goal_type=goal.goal_type,
        target_value=goal.target_value,
        target_date=goal.target_date.isoformat() if goal.target_date else None
    )
    
    try:
        validation_result = service.validate_goal(goal.user_id, goal_data)
        return {
            "is_realistic": validation_result.is_realistic,
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions,
            "recommended_timeline": validation_result.recommended_timeline
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/{user_id}/progress", response_model=schemas.ProgressMetricsResponse, tags=["Goals"])
def get_progress_metrics(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Get progress metrics for all active user goals
    """
    service = UserProfileService(db)
    
    try:
        metrics = service.calculate_progress_metrics(user_id)
        
        # Return first goal's metrics (or extend to return all goals)
        if metrics['goals']:
            first_goal = metrics['goals'][0]
            return {
                "goal_id": first_goal['goal_id'],
                "goal_type": first_goal['goal_type'],
                "progress_percentage": first_goal['progress_percentage'],
                "current_value": first_goal['current_value'],
                "target_value": first_goal['target_value'],
                "days_remaining": first_goal.get('days_remaining'),
                "is_on_track": first_goal['is_on_track']
            }
        else:
            raise HTTPException(status_code=404, detail="No active goals found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RECOMMENDATION ENDPOINTS ---

@app.get("/api/users/{user_id}/recommendations", response_model=schemas.RecommendationListResponse, tags=["Recommendations"])
def get_user_recommendations(
    user_id: str,
    recommendation_type: Optional[str] = Query(None, description="Filter by type (meal, exercise, goal_adjustment)"),
    include_read: bool = Query(False, description="Include already read recommendations"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db)
):
    """
    Get personalized recommendations for the user
    """
    engine = RecommendationEngine(db)
    
    # Get recommendations using only supported parameters
    recommendations = engine.get_user_recommendations(
        user_id=user_id,
        include_read=include_read,
        limit=limit
    )
    
    # Filter by recommendation_type if provided
    if recommendation_type:
        recommendations = [r for r in recommendations if r.recommendation_type == recommendation_type]
    
    # Apply offset manually
    recommendations = recommendations[offset:]
    
    # Format response
    formatted_recs = []
    for rec in recommendations:
        formatted_recs.append({
            "id": str(rec.id),
            "recommendation_type": rec.recommendation_type,
            "title": rec.title,
            "description": rec.description,
            "confidence_score": rec.confidence_score,
            "is_read": rec.is_read,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "expires_at": rec.expires_at.isoformat() if rec.expires_at else None
        })
    
    return {
        "recommendations": formatted_recs,
        "total_count": len(formatted_recs),
        "unread_count": sum(1 for rec in recommendations if not rec.is_read)
    }

@app.post("/api/users/{user_id}/recommendations/generate", tags=["Recommendations"])
def generate_recommendations(
    user_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Generate new personalized recommendations based on user data
    """
    engine = RecommendationEngine(db)
    
    try:
        request = RecommendationRequest(user_id=user_id)
        result = engine.generate_recommendations(request)
        
        return {
            "message": "Recommendations generated successfully",
            "meal_recommendations_count": len(result.meal_recommendations),
            "exercise_recommendations_count": len(result.exercise_recommendations),
            "goal_recommendations_count": len(result.goal_recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@app.put("/api/recommendations/{recommendation_id}/read", tags=["Recommendations"])
def mark_recommendation_read(
    recommendation_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Mark a recommendation as read
    """
    engine = RecommendationEngine(db)
    
    success = engine.mark_recommendation_read(recommendation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {"message": "Recommendation marked as read"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
