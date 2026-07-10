"""
Progress Tracking API Endpoints

Comprehensive progress tracking with weight, measurements, and analytics
"""

from fastapi import APIRouter, Depends, Body, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.progress_tracking_service import ProgressTrackingService


router = APIRouter(prefix="/api/progress", tags=["Progress Tracking"])


class WeightLogRequest(BaseModel):
    """Request model for logging weight"""
    user_id: int
    weight_kg: float
    measured_at: Optional[str] = None  # ISO format datetime


class MeasurementLogRequest(BaseModel):
    """Request model for logging measurements"""
    user_id: int
    measurements: Dict[str, float]  # e.g., {"chest_cm": 100, "waist_cm": 85}
    measured_at: Optional[str] = None


@router.post("/log-weight")
def log_weight(request: WeightLogRequest, db: Session = Depends(get_db)):
    """
    Log weight measurement.
    
    Example:
    {
      "user_id": 1,
      "weight_kg": 75.5,
      "measured_at": "2026-07-09T08:00:00"
    }
    """
    try:
        service = ProgressTrackingService(db)
        
        measured_at = None
        if request.measured_at:
            measured_at = datetime.fromisoformat(request.measured_at.replace('Z', ''))
        
        reading = service.log_weight(
            user_id=request.user_id,
            weight_kg=request.weight_kg,
            measured_at=measured_at
        )
        
        return {
            "success": True,
            "reading_id": reading.id,
            "weight_kg": reading.weight_kg,
            "logged_at": reading.created_at.isoformat(),
            "message": f"Weight logged: {reading.weight_kg} kg"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log weight: {str(e)}")


@router.post("/log-measurements")
def log_measurements(request: MeasurementLogRequest, db: Session = Depends(get_db)):
    """
    Log body measurements.
    
    Example:
    {
      "user_id": 1,
      "measurements": {
        "chest_cm": 100,
        "waist_cm": 85,
        "arms_cm": 35,
        "thighs_cm": 55
      }
    }
    """
    try:
        service = ProgressTrackingService(db)
        
        measured_at = None
        if request.measured_at:
            measured_at = datetime.fromisoformat(request.measured_at.replace('Z', ''))
        
        snapshot = service.log_measurements(
            user_id=request.user_id,
            measurements=request.measurements,
            measured_at=measured_at
        )
        
        return {
            "success": True,
            "snapshot_id": snapshot.id,
            "measurements": snapshot.measurements,
            "logged_at": snapshot.date.isoformat(),
            "message": f"Measurements logged: {len(snapshot.measurements)} metrics"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log measurements: {str(e)}")


@router.get("/weight-history/{user_id}")
def get_weight_history(
    user_id: int,
    days: int = Query(90, description="Number of days to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get weight history for charts/graphs.
    
    Returns data formatted for visualization with trend analysis.
    Perfect for line charts in frontend.
    """
    try:
        service = ProgressTrackingService(db)
        history = service.get_weight_history(user_id, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weight history: {str(e)}")


@router.get("/measurement-history/{user_id}")
def get_measurement_history(
    user_id: int,
    days: int = Query(90, description="Number of days to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get body measurement history.
    
    Returns all measurements organized by type with change calculations.
    """
    try:
        service = ProgressTrackingService(db)
        history = service.get_measurement_history(user_id, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get measurement history: {str(e)}")


@router.get("/comprehensive-report/{user_id}")
def get_comprehensive_progress(
    user_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress report.
    
    Combines:
    - Weight trends
    - Measurements
    - Calorie statistics
    - Workout statistics
    - Consistency metrics
    
    Perfect for monthly/weekly progress reports.
    """
    try:
        service = ProgressTrackingService(db)
        report = service.get_comprehensive_progress(user_id, days)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/goal-progress/{user_id}")
def get_goal_progress(user_id: int, db: Session = Depends(get_db)):
    """
    Get goal progress visualization data.
    
    Returns progress towards all active goals with:
    - Percentage completion
    - Time remaining
    - On-track status
    
    Perfect for progress bars and goal dashboards.
    """
    try:
        service = ProgressTrackingService(db)
        progress = service.get_goal_progress_visualization(user_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goal progress: {str(e)}")


@router.get("/trends/{user_id}")
def get_trends(
    user_id: int,
    metric: str = Query("weight", description="Metric: weight, calories, workout_frequency"),
    days: int = Query(90, description="Number of days"),
    db: Session = Depends(get_db)
):
    """
    Get trend visualization data for charts.
    
    Supported metrics:
    - weight: Weight over time
    - calories: Daily calories consumed vs burned
    - workout_frequency: Workout frequency over time
    
    Returns data formatted for chart libraries (Chart.js, Recharts, etc.)
    """
    try:
        service = ProgressTrackingService(db)
        trends = service.get_trends_visualization(user_id, metric, days)
        return trends
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.get("/dashboard-summary/{user_id}")
def get_dashboard_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get quick progress summary for dashboard widget.
    
    Returns:
    - Latest weight
    - Weight change this week
    - Current streak
    - Goals progress
    """
    try:
        service = ProgressTrackingService(db)
        
        # Get latest weight
        weight_data = service.get_weight_history(user_id, days=7)
        
        # Get goal progress
        goal_data = service.get_goal_progress_visualization(user_id)
        
        # Get weekly report
        weekly_report = service.get_comprehensive_progress(user_id, days=7)
        
        return {
            "user_id": user_id,
            "current_weight": weight_data.get("summary", {}).get("current_weight_kg"),
            "weekly_weight_change": weight_data.get("summary", {}).get("weight_change_kg"),
            "weekly_trend": weight_data.get("summary", {}).get("trend"),
            "consistency_this_week": weekly_report.get("consistency", {}).get("consistency_percentage"),
            "active_goals": goal_data.get("total_goals", 0),
            "goals_on_track": len([g for g in goal_data.get("goals_progress", []) if g.get("on_track")]),
            "workouts_this_week": weekly_report.get("workout_stats", {}).get("total_workouts"),
            "avg_daily_calories": weekly_report.get("nutrition_stats", {}).get("avg_daily_calories")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")
