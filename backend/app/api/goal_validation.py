"""
Goal Validation & Adjustment API
SMART goal wizard, validation, and automatic progress-based adjustments
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app import database, models
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/goals", tags=["Goal Management"])


class GoalCreationRequest(BaseModel):
    user_id: str
    goal_type: str  # weight_loss, muscle_gain, strength, endurance, body_fat
    target_value: float
    target_date: str  # ISO format
    notes: Optional[str] = None


class GoalValidationResponse(BaseModel):
    is_realistic: bool
    is_smart: bool
    warnings: list
    suggestions: list
    adjusted_target: Optional[float] = None
    adjusted_timeline: Optional[str] = None


@router.post("/create-smart")
def create_smart_goal(
    request: GoalCreationRequest,
    db: Session = Depends(database.get_db),
):
    """
    Create a SMART goal with automatic validation.
    SMART = Specific, Measurable, Achievable, Relevant, Time-bound
    """
    try:
        # Get user profile for context
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == request.user_id
        ).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Validate the goal
        validation = validate_goal(
            user_id=request.user_id,
            goal_type=request.goal_type,
            target_value=request.target_value,
            target_date=request.target_date,
            current_weight=profile.weight_kg,
            db=db
        )
        
        # Get current value based on goal type
        current_value = get_current_value(request.user_id, request.goal_type, profile, db)
        
        # Create the goal
        goal = models.UserGoal(
            user_id=request.user_id,
            goal_type=request.goal_type,
            target_value=validation.get("adjusted_target", request.target_value),
            current_value=current_value,
            target_date=datetime.fromisoformat(validation.get("adjusted_timeline", request.target_date)),
            is_active=True,
            notes=request.notes
        )
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return {
            "goal_id": goal.id,
            "created": True,
            "validation": validation,
            "goal": {
                "type": goal.goal_type,
                "current": goal.current_value,
                "target": goal.target_value,
                "target_date": goal.target_date.isoformat(),
                "progress_percentage": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def validate_goal(
    user_id: str,
    goal_type: str,
    target_value: float,
    target_date: str,
    current_weight: Optional[float],
    db: Session
) -> dict:
    """
    Validate if a goal is realistic and SMART.
    Returns validation result with warnings and suggestions.
    """
    warnings = []
    suggestions = []
    is_realistic = True
    is_smart = True
    adjusted_target = None
    adjusted_timeline = None
    
    # Parse target date
    try:
        target_dt = datetime.fromisoformat(target_date)
        days_to_target = (target_dt - datetime.utcnow()).days
        weeks_to_target = days_to_target / 7
    except:
        is_smart = False
        warnings.append("Invalid target date format")
        return {
            "is_realistic": False,
            "is_smart": False,
            "warnings": warnings,
            "suggestions": ["Use ISO format for date (YYYY-MM-DD)"]
        }
    
    # Check if timeline is reasonable (at least 1 week)
    if days_to_target < 7:
        is_realistic = False
        warnings.append("Timeline too short for sustainable progress")
        adjusted_timeline = (datetime.utcnow() + timedelta(weeks=4)).isoformat()
        suggestions.append("Recommend at least 4 weeks for any fitness goal")
    
    # Goal-specific validation
    if goal_type == "weight_loss":
        if not current_weight:
            warnings.append("Current weight not set in profile")
            suggestions.append("Update your profile with current weight")
        else:
            weight_to_lose = current_weight - target_value
            
            # Healthy weight loss: 0.5-1kg per week
            max_healthy_loss = weeks_to_target * 1.0  # kg
            min_recommended = weeks_to_target * 0.5  # kg
            
            if weight_to_lose > max_healthy_loss:
                is_realistic = False
                warnings.append(f"Weight loss goal too aggressive: {weight_to_lose:.1f}kg in {weeks_to_target:.0f} weeks")
                warnings.append("Healthy rate: 0.5-1kg per week")
                
                # Adjust target or timeline
                adjusted_target = current_weight - max_healthy_loss
                suggestions.append(f"Suggested target: {adjusted_target:.1f}kg")
                suggestions.append(f"Or extend timeline to {int(weight_to_lose / 0.75)} weeks")
            
            elif weight_to_lose < 0:
                is_realistic = False
                warnings.append("Target weight is higher than current weight")
                suggestions.append("For weight gain, use 'muscle_gain' goal type")
            
            elif weight_to_lose < 1:
                warnings.append("Very small weight change - consider body composition goals instead")
                suggestions.append("Focus on body fat percentage or muscle gain")
            
            if weight_to_lose > 0:
                # Calculate required calorie deficit
                total_deficit = weight_to_lose * 7700  # 1kg fat = 7700 kcal
                daily_deficit = total_deficit / days_to_target
                
                if daily_deficit > 1000:
                    warnings.append(f"Requires {daily_deficit:.0f} kcal daily deficit - very challenging")
                    suggestions.append("Combine diet (500 kcal) and exercise (300-500 kcal) for sustainable results")
                else:
                    suggestions.append(f"Target daily deficit: {daily_deficit:.0f} kcal (diet + exercise)")
    
    elif goal_type == "muscle_gain":
        if not current_weight:
            warnings.append("Current weight not set in profile")
        else:
            muscle_to_gain = target_value - current_weight
            
            # Realistic muscle gain: 0.25-0.5kg per week (beginners), 0.1-0.25kg (intermediate)
            max_gain = weeks_to_target * 0.5  # kg (optimistic)
            
            if muscle_to_gain > max_gain:
                is_realistic = False
                warnings.append(f"Muscle gain goal too aggressive: {muscle_to_gain:.1f}kg in {weeks_to_target:.0f} weeks")
                warnings.append("Natural muscle gain: 0.1-0.5kg per week depending on experience")
                
                adjusted_target = current_weight + max_gain
                suggestions.append(f"Suggested target: {adjusted_target:.1f}kg")
            
            elif muscle_to_gain < 0:
                is_realistic = False
                warnings.append("Target is lower than current weight")
                suggestions.append("For weight loss, use 'weight_loss' goal type")
            
            if muscle_to_gain > 0:
                # Calculate required calorie surplus
                daily_surplus = 300  # Typical surplus for lean gains
                suggestions.append(f"Aim for {daily_surplus} kcal daily surplus with high protein")
                suggestions.append("Progressive overload in training is essential")
                suggestions.append("Track protein: 1.6-2.2g per kg body weight")
    
    elif goal_type == "body_fat":
        if target_value < 5 or target_value > 35:
            is_realistic = False
            warnings.append(f"Body fat target {target_value}% may be unhealthy")
            
            if target_value < 5:
                warnings.append("Below 5% body fat is dangerous for most people")
                adjusted_target = 10
            else:
                suggestions.append("Consider consulting a health professional")
        
        # Get current body fat if available
        recent_reading = db.query(models.BiometricReading).filter(
            models.BiometricReading.user_id == user_id
        ).order_by(desc(models.BiometricReading.created_at)).first()
        
        if recent_reading and recent_reading.body_fat_pct:
            current_bf = recent_reading.body_fat_pct
            bf_change = abs(current_bf - target_value)
            
            # Realistic: 0.5-1% per month
            max_change = (weeks_to_target / 4) * 1.0
            
            if bf_change > max_change:
                is_realistic = False
                warnings.append(f"Body fat change of {bf_change:.1f}% in {weeks_to_target:.0f} weeks is very aggressive")
                suggestions.append("Realistic rate: 0.5-1% per month")
    
    elif goal_type == "strength":
        # Strength goals are more variable
        suggestions.append("Track your lifts weekly to monitor progress")
        suggestions.append("Progressive overload: increase weight by 2.5-5% when you hit target reps")
        suggestions.append("Beginners can expect faster strength gains")
    
    elif goal_type == "endurance":
        suggestions.append("Increase running/cardio volume by no more than 10% per week")
        suggestions.append("Include rest days to prevent overtraining")
        suggestions.append("Track heart rate and perceived exertion")
    
    # Generic SMART criteria check
    if not target_value or target_value <= 0:
        is_smart = False
        warnings.append("Target value must be positive and specific")
    
    # Add general suggestions
    if not suggestions:
        suggestions.append("Track progress weekly for accountability")
        suggestions.append("Adjust goal if circumstances change")
    
    return {
        "is_realistic": is_realistic,
        "is_smart": is_smart and days_to_target >= 7,
        "warnings": warnings,
        "suggestions": suggestions,
        "adjusted_target": adjusted_target,
        "adjusted_timeline": adjusted_timeline
    }


def get_current_value(user_id: str, goal_type: str, profile, db: Session) -> float:
    """Get current value for a specific goal type."""
    if goal_type in ["weight_loss", "muscle_gain"]:
        return float(profile.weight_kg) if profile.weight_kg else 0.0
    
    elif goal_type == "body_fat":
        recent_reading = db.query(models.BiometricReading).filter(
            models.BiometricReading.user_id == user_id
        ).order_by(desc(models.BiometricReading.created_at)).first()
        return float(recent_reading.body_fat_pct) if recent_reading and recent_reading.body_fat_pct else 0.0
    
    else:
        return 0.0


@router.get("/progress/{goal_id}")
def get_goal_progress(
    goal_id: int,
    db: Session = Depends(database.get_db),
):
    """
    Get detailed progress for a specific goal with auto-adjustment recommendations.
    """
    try:
        goal = db.query(models.UserGoal).filter(models.UserGoal.id == goal_id).first()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Get profile for updated current value
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == goal.user_id
        ).first()
        
        # Update current value
        current_value = get_current_value(goal.user_id, goal.goal_type, profile, db)
        goal.current_value = current_value
        db.commit()
        
        # Calculate progress
        if goal.goal_type in ["weight_loss"]:
            # For weight loss, progress is from starting point toward lower target
            initial_value = goal.target_value + abs(goal.target_value - current_value)
            total_change_needed = initial_value - goal.target_value
            change_achieved = initial_value - current_value
        else:
            # For gains, progress is from starting point toward higher target
            total_change_needed = goal.target_value - (goal.current_value or 0)
            change_achieved = current_value - (goal.current_value or 0)
        
        progress_pct = (change_achieved / total_change_needed * 100) if total_change_needed != 0 else 0
        progress_pct = max(0, min(100, progress_pct))  # Clamp between 0-100
        
        # Calculate expected progress based on time elapsed
        days_elapsed = (datetime.utcnow() - goal.start_date).days
        days_total = (goal.target_date - goal.start_date).days if goal.target_date else 90
        expected_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
        
        # Determine if on track
        on_track = progress_pct >= (expected_progress - 10)  # Allow 10% tolerance
        
        # Auto-adjustment recommendations
        recommendations = []
        should_adjust = False
        
        if progress_pct < expected_progress - 20:
            should_adjust = True
            recommendations.append({
                "type": "behind_schedule",
                "message": "You're behind schedule. Consider adjusting your target or extending timeline.",
                "suggested_action": "Review your diet and exercise consistency"
            })
        
        elif progress_pct > expected_progress + 20:
            recommendations.append({
                "type": "ahead_schedule",
                "message": "Great progress! You're ahead of schedule.",
                "suggested_action": "You might reach your goal early. Consider setting a new target."
            })
        
        # Check if goal is too easy or too hard
        if days_elapsed > 14:  # After 2 weeks
            weekly_rate = change_achieved / (days_elapsed / 7)
            
            if goal.goal_type == "weight_loss" and weekly_rate < 0.2:
                should_adjust = True
                recommendations.append({
                    "type": "slow_progress",
                    "message": f"Weight loss rate very slow ({weekly_rate:.2f}kg/week)",
                    "suggested_action": "Increase calorie deficit by 200-300 kcal or add cardio"
                })
            
            elif goal.goal_type == "weight_loss" and weekly_rate > 1.2:
                should_adjust = True
                recommendations.append({
                    "type": "fast_progress",
                    "message": f"Weight loss rate too fast ({weekly_rate:.2f}kg/week)",
                    "suggested_action": "Reduce deficit to preserve muscle mass"
                })
        
        return {
            "goal_id": goal.id,
            "goal_type": goal.goal_type,
            "status": "active" if goal.is_active else "inactive",
            "current_value": current_value,
            "target_value": goal.target_value,
            "start_date": goal.start_date.isoformat(),
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "progress": {
                "percentage": round(progress_pct, 1),
                "change_achieved": round(change_achieved, 2),
                "change_needed": round(total_change_needed, 2),
                "expected_progress": round(expected_progress, 1),
                "on_track": on_track
            },
            "timeline": {
                "days_elapsed": days_elapsed,
                "days_remaining": (goal.target_date - datetime.utcnow()).days if goal.target_date else None,
                "days_total": days_total
            },
            "should_adjust": should_adjust,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal progress error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjust/{goal_id}")
def adjust_goal(
    goal_id: int,
    adjustment: dict = Body(...),
    db: Session = Depends(database.get_db),
):
    """
    Adjust a goal based on progress and feedback.
    """
    try:
        goal = db.query(models.UserGoal).filter(models.UserGoal.id == goal_id).first()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Update goal parameters
        if "target_value" in adjustment:
            goal.target_value = adjustment["target_value"]
        
        if "target_date" in adjustment:
            goal.target_date = datetime.fromisoformat(adjustment["target_date"])
        
        if "notes" in adjustment:
            existing_notes = goal.notes or ""
            goal.notes = f"{existing_notes}\n[{datetime.utcnow().date()}] Adjusted: {adjustment['notes']}"
        
        goal.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "goal_id": goal.id,
            "adjusted": True,
            "new_target": goal.target_value,
            "new_deadline": goal.target_date.isoformat() if goal.target_date else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Goal adjustment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-wizard")
def goal_validation_wizard(
    user_id: str,
    goal_type: str,
    target_value: float,
    weeks: int,
    db: Session = Depends(database.get_db),
):
    """
    Interactive goal validation wizard.
    Provides real-time feedback as user inputs goal parameters.
    """
    try:
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == user_id
        ).first()
        
        target_date = (datetime.utcnow() + timedelta(weeks=weeks)).isoformat()
        
        validation = validate_goal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target_value,
            target_date=target_date,
            current_weight=profile.weight_kg if profile else None,
            db=db
        )
        
        return {
            "user_id": user_id,
            "input": {
                "goal_type": goal_type,
                "target_value": target_value,
                "weeks": weeks
            },
            "validation": validation,
            "ready_to_create": validation["is_realistic"] and validation["is_smart"]
        }
        
    except Exception as e:
        logger.error(f"Validation wizard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/{user_id}")
def get_active_goals(
    user_id: str,
    db: Session = Depends(database.get_db),
):
    """
    Get all active goals for a user with progress summaries.
    """
    try:
        goals = db.query(models.UserGoal).filter(
            and_(
                models.UserGoal.user_id == user_id,
                models.UserGoal.is_active == True
            )
        ).order_by(desc(models.UserGoal.created_at)).all()
        
        goal_summaries = []
        for goal in goals:
            # Quick progress calculation
            if goal.target_value and goal.current_value:
                change_needed = goal.target_value - goal.current_value
                progress = 0 if change_needed == 0 else 100
            else:
                progress = 0
            
            goal_summaries.append({
                "id": goal.id,
                "type": goal.goal_type,
                "target": goal.target_value,
                "current": goal.current_value,
                "progress_pct": progress,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "days_remaining": (goal.target_date - datetime.utcnow()).days if goal.target_date else None
            })
        
        return {
            "user_id": user_id,
            "active_goals": goal_summaries,
            "count": len(goal_summaries)
        }
        
    except Exception as e:
        logger.error(f"Active goals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
