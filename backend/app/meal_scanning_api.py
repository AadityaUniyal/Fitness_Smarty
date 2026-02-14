"""
Meal Scanning API using Gemini + Personalization
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional
import shutil
from pathlib import Path

from app.database import get_db
from app.gemini_meal_scanner import PersonalizedMealScanner, PreferenceLearner

router = APIRouter(prefix="/api/meals", tags=["Meal Scanning"])

# Initialize scanner
scanner = PersonalizedMealScanner()
learner = PreferenceLearner()


class UserProfile(BaseModel):
    user_id: str
    primary_goal: str  # weight_loss, muscle_gain, maintenance
    age: Optional[int] = 30
    weight_kg: Optional[float] = 70
    activity_level: Optional[str] = "moderate"


class MealFeedback(BaseModel):
    meal_id: str
    user_id: str
    thumbs_up: bool  # True = good for me, False = not good


@router.post("/scan")
async def scan_meal_photo(
    file: UploadFile = File(...),
    user_id: str = "demo_user",
    db: Session = Depends(get_db)
):
    """
    Scan a meal photo using Gemini Vision API
    
    Returns detected foods and nutrition estimate
    """
    try:
        # Save uploaded image temporarily
        upload_dir = Path("meal_images")
        upload_dir.mkdir(exist_ok=True)
        
        image_path = upload_dir / f"{user_id}_{file.filename}"
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Scan with Gemini
        result = scanner.scan_meal(str(image_path))
        
        # Generate meal ID
        import uuid
        meal_id = str(uuid.uuid4())
        
        result['meal_id'] = meal_id
        result['image_path'] = str(image_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/analyze-for-user")
async def analyze_meal_for_user(user_profile: UserProfile, meal_data: Dict):
    """
    Analyze if a meal is good for the user's goals
    
    Uses rule-based logic + learned preferences
    """
    try:
        # Check personalized preferences first
        patterns = learner.analyze_patterns(user_profile.user_id)
        
        # Get recommendation
        result = scanner.is_good_for_user(
            meal_data=meal_data,
            user_profile=user_profile.dict()
        )
        
        # Add personalization insights
        if patterns.get('status') == 'patterns_found':
            result['personalized_insight'] = patterns.get('recommendation')
            result['your_usual_range'] = f"{patterns['preferred_calories']} cal, {patterns['preferred_protein_g']}g protein"
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/feedback")
async def submit_meal_feedback(feedback: MealFeedback, meal_data: Dict, user_profile: Dict):
    """
    User gives thumbs up/down on meal
    
    This data trains personalization
    """
    try:
        success = scanner.save_user_feedback(
            meal_id=feedback.meal_id,
            user_id=feedback.user_id,
            meal_data=meal_data,
            user_profile=user_profile,
            thumbs_up=feedback.thumbs_up
        )
        
        if success:
            feedback_count = scanner.get_feedback_count()
            return {
                'message': 'Thank you! Your feedback helps personalize recommendations.',
                'total_feedback': feedback_count,
                'status': 'learning' if feedback_count >= 10 else 'collecting_data'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """
    Get learned preferences for a user
    
    Returns favorite foods, preferred calorie range, etc.
    """
    patterns = learner.analyze_patterns(user_id)
    return patterns
