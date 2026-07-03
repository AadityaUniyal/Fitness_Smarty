from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.concurrency import run_in_threadpool
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


import uuid
from fastapi import BackgroundTasks

# Task status cache/store
scan_tasks = {}

def perform_background_scan(task_id: str, base64_url: str):
    scan_tasks[task_id] = {"status": "processing", "result": None, "error": None}
    try:
        # Runs the model/Gemini scan in this background worker thread
        result = scanner.scan_meal(base64_url)
        result['meal_id'] = task_id
        result['image_path'] = base64_url
        scan_tasks[task_id] = {"status": "completed", "result": result, "error": None}
    except Exception as e:
        scan_tasks[task_id] = {"status": "failed", "result": None, "error": str(e)}


@router.post("/scan")
async def scan_meal_photo(
    file: UploadFile = File(...),
    user_id: str = Form("demo_user"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Scan a meal photo asynchronously using FastAPI BackgroundTasks.
    Returns a task_id to poll status.
    """
    try:
        import base64
        
        # Read the file bytes
        contents = await file.read()
        
        # Validate file size
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be under 10MB")
            
        mime_type = file.content_type or "image/jpeg"
        encoded = base64.b64encode(contents).decode("utf-8")
        base64_url = f"data:{mime_type};base64,{encoded}"
        
        task_id = str(uuid.uuid4())
        scan_tasks[task_id] = {"status": "pending", "result": None, "error": None}
        
        background_tasks.add_task(perform_background_scan, task_id, base64_url)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Meal scanning job started asynchronously. Use /api/meals/tasks/{task_id} to poll progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan job initialization failed: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_scan_task_status(task_id: str):
    """
    Poll status of a meal scanning background job.
    """
    task = scan_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


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
