from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import SmartNextMove, DailyTask, EnhancedUser
import math

from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id

router = APIRouter(prefix="/api/nextmove", tags=["Smart Next Move"])

@router.get("/{user_id}")
def get_next_move(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    if str(user_id) != str(current_auth_id):
        raise HTTPException(403, "Operation forbidden. You cannot access recommendations for another user.")
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    today = datetime.utcnow().replace(hour=0,minute=0,second=0)
    tomorrow = today.replace(hour=23,minute=59,second=59)

    tasks = db.query(DailyTask).filter(
        DailyTask.user_id == user_id,
        DailyTask.date >= today,
        DailyTask.date <= tomorrow
    ).all()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed)
    pending = [t for t in tasks if not t.is_completed]

    # Time-based context
    hour = datetime.utcnow().hour
    if hour < 12: time_cat = "morning"
    elif hour < 17: time_cat = "afternoon"
    elif hour < 22: time_cat = "evening"
    else: time_cat = "night"

    # Determine next best action
    next_action = _compute_next_action(pending, total, completed, time_cat, user)

    return {
        "user_id": user_id,
        "time_category": time_cat,
        "tasks_total": total,
        "tasks_completed": completed,
        "tasks_pending": len(pending),
        "next_action": next_action,
    }


def _compute_next_action(pending, total, completed, time_cat, user):
    """Smart logic to determine the best next action."""
    is_femme = user.gender and user.gender.lower() in ("female", "f")

    # If all done, suggest review and recovery
    if completed >= total > 0:
        return {
            "title": "All tasks complete! Time to review your day",
            "description": "Great progress. Check your stats and plan tomorrow.",
            "category": "review",
            "route": "/progress",
            "reasoning": "You've completed everything. Recovery & planning mode.",
            "is_femme_mode": is_femme,
        }

    # If nothing done yet
    if completed == 0:
        # Morning priority
        if time_cat == "morning":
            return {
                "title": "Start your day right — log your morning weight",
                "description": "Morning weigh-in sets the baseline for today's tracking.",
                "category": "nutrition",
                "route": "/progress",
                "reasoning": "First task of the day: establish your baseline.",
                "is_femme_mode": is_femme,
            }
        return {
            "title": "Start with your first task of the day",
            "description": "Pick the highest priority task and get going!",
            "category": "general",
            "route": "/dashboard",
            "reasoning": "You haven't started today's tasks yet.",
            "is_femme_mode": is_femme,
        }

    # Pick highest priority pending task
    urgent = [t for t in pending if t.priority >= 2]
    high = [t for t in pending if t.priority == 1]

    if urgent:
        t = urgent[0]
        route = _category_route(t.category)
        return {
            "title": f"Urgent: {t.title}",
            "description": t.description or "High priority task waiting for you.",
            "category": t.category,
            "route": route,
            "reasoning": f"Highest priority ({t.category}) task is still open.",
            "is_femme_mode": is_femme,
        }

    if high:
        t = high[0]
        route = _category_route(t.category)
        return {
            "title": f"Next up: {t.title}",
            "description": t.description or "Keep the momentum going.",
            "category": t.category,
            "route": route,
            "reasoning": f"High priority ({t.category}) task recommended next.",
            "is_femme_mode": is_femme,
        }

    if pending:
        t = pending[0]
        route = _category_route(t.category)
        return {
            "title": f"Try: {t.title}",
            "description": t.description or "A pending task awaits.",
            "category": t.category,
            "route": route,
            "reasoning": f"Oldest pending {t.category} task.",
            "is_femme_mode": is_femme,
        }

    # Fallback
    return {
        "title": "Log a meal or do a quick workout",
        "description": "Keep your streak alive!",
        "category": "general",
        "route": "/dashboard",
        "reasoning": "No pending tasks found.",
        "is_femme_mode": is_femme,
    }


def _category_route(cat: str) -> str:
    routes = {
        "nutrition": "/nutrition",
        "exercise": "/workout",
        "hydration": "/nutrition",
        "femme": "/female",
        "sleep": "/progress",
        "mindful": "/progress",
        "review": "/progress",
    }
    return routes.get(cat, "/dashboard")
