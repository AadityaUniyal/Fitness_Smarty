"""
Hydration Tracking API Endpoints

Track water intake, view hydration goals, and get reminders.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date

from ..database import get_db
from ..hydration_service import HydrationService

router = APIRouter(prefix="/api/hydration", tags=["hydration"])


class WaterLogRequest(BaseModel):
    """Request model for logging water intake"""
    user_id: int
    amount_ml: Optional[float] = None
    glasses: Optional[float] = None


@router.post("/log-water")
async def log_water_intake(
    request: WaterLogRequest,
    db: Session = Depends(get_db)
):
    """
    Log water intake
    
    Provide either:
    - amount_ml: Water in milliliters
    - glasses: Number of glasses (250ml each)
    
    Returns updated daily summary with progress toward goal.
    """
    service = HydrationService(db)
    result = service.log_water(
        user_id=request.user_id,
        amount_ml=request.amount_ml,
        glasses=request.glasses
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/daily-summary/{user_id}")
async def get_daily_summary(
    user_id: int,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get hydration summary for today or a specific date
    
    Shows:
    - Current water intake
    - Daily goal
    - Progress percentage
    - Remaining amount to drink
    """
    service = HydrationService(db)
    
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = service.get_daily_summary(user_id, target_date=parsed_date)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/goal/{user_id}")
async def get_hydration_goal(
    user_id: int,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Calculate daily hydration goal
    
    Based on:
    - Body weight (35ml per kg)
    - Workout activity (adds 500ml)
    - Gender
    
    Returns goal in both milliliters and glasses.
    """
    service = HydrationService(db)
    
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = service.calculate_daily_goal(user_id, target_date=parsed_date)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/trends/{user_id}")
async def get_hydration_trends(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get 7-day hydration trends
    
    Shows:
    - Daily water intake
    - Goals achieved
    - Average intake
    - Consistency score
    - Trend analysis (improving/declining/stable)
    """
    service = HydrationService(db)
    result = service.get_weekly_trends(user_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/reminders/{user_id}")
async def get_hydration_reminders(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get personalized hydration reminders
    
    Returns time-based reminders:
    - Morning: Start your day right
    - Afternoon: Stay hydrated
    - Evening: Don't forget
    - Night: One more before bed
    
    Includes motivational messages based on progress.
    """
    service = HydrationService(db)
    result = service.get_hydration_reminders(user_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/quick-log/{user_id}")
async def quick_log_glass(
    user_id: int,
    glasses: float = Query(default=1, description="Number of glasses to log"),
    db: Session = Depends(get_db)
):
    """
    Quick log for mobile/simple interfaces
    
    Just tap to log 1 glass (or specify amount).
    Perfect for quick tracking throughout the day.
    """
    service = HydrationService(db)
    result = service.log_water(user_id=user_id, glasses=glasses)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "message": f"Logged {glasses} glass(es)! 💧",
        "total_today": result["daily_summary"]["current_glasses"],
        "progress": result["daily_summary"]["progress_percentage"]
    }
