from fastapi import APIRouter, Depends, Query, Body, HTTPException, UploadFile, File, Request, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from app.database import get_db
from app import schemas, models
from app.api_validation import APIValidator, ErrorHandler
from app.meal_analysis_service import MealAnalysisService
from app.limiter import limiter

router = APIRouter(prefix="/api/meals", tags=["Meal Analysis"])

@router.post("/analyze", response_model=schemas.MealAnalysisResponse)
@limiter.limit("20/minute")
def analyze_meal_photo(
    request: Request,
    user_id: str = Form(...),
    meal_type: str = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze a meal photo"""
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
        
        if not result.success:
            raise ErrorHandler.bad_request_error(result.error_message or "Meal analysis failed")
        
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
    except Exception as e:
        raise ErrorHandler.internal_error(f"Meal analysis failed: {str(e)}")

@router.get("/{meal_log_id}")
def get_meal_details(
    meal_log_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific meal log"""
    service = MealAnalysisService(db)
    meal_log = service.get_meal_log(meal_log_id)
    if not meal_log:
        raise HTTPException(status_code=404, detail="Meal log not found")
    return meal_log

@router.get("/user/{user_id}/history", response_model=schemas.MealHistoryResponse)
def get_user_meal_history(
    user_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    meal_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get historical meal logs for a user"""
    service = MealAnalysisService(db)
    # Reusing the parsing logic from main.py
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
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

@router.get("/user/{user_id}/daily-summary", response_model=schemas.DailyNutritionSummary)
def get_daily_nutrition_summary(
    user_id: str,
    date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
    ):
    """Get nutrition summary for a specific day"""
    target_date = None
    if date:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    
    service = MealAnalysisService(db)
    summary = service.get_daily_nutrition_summary(user_id=user_id, date=target_date)
    
    total_nutrition = summary.get('total_nutrition', {})
    meals_by_type = summary.get('meals_by_type', {})
    meals_by_type_counts = {k: len(v) for k, v in meals_by_type.items()}
    
    return {
        'date': summary.get('date'),
        'total_calories': total_nutrition.get('calories', 0),
        'total_protein_g': total_nutrition.get('protein_g', 0),
        'total_carbs_g': total_nutrition.get('carbs_g', 0),
        'total_fat_g': total_nutrition.get('fat_g', 0),
        'meal_count': summary.get('meal_count', 0),
        'meals_by_type': meals_by_type_counts
    }
