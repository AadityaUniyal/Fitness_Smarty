from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import DailyTask, SmartNextMove, EnhancedUser

router = APIRouter(prefix="/api/tasks", tags=["Daily Checklist"])

@router.get("/{user_id}")
def get_tasks(user_id: int, task_date: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(DailyTask).filter(DailyTask.user_id == user_id)
    if task_date:
        dt = datetime.fromisoformat(task_date)
        q = q.filter(DailyTask.date >= dt.replace(hour=0,minute=0,second=0), DailyTask.date <= dt.replace(hour=23,minute=59,second=59))
    else:
        today = datetime.utcnow().replace(hour=0,minute=0,second=0)
        tomorrow = today.replace(hour=23,minute=59,second=59)
        q = q.filter(DailyTask.date >= today, DailyTask.date <= tomorrow)
    if category:
        q = q.filter(DailyTask.category == category)
    tasks = q.order_by(DailyTask.priority.desc(), DailyTask.sort_order.asc()).all()
    return [{
        "id": t.id, "user_id": t.user_id, "title": t.title, "description": t.description,
        "category": t.category, "is_completed": t.is_completed, "completed_at": t.completed_at,
        "priority": t.priority, "sort_order": t.sort_order, "is_auto": t.is_auto,
        "source": t.source, "is_recurring": t.is_recurring, "recurrence_pattern": t.recurrence_pattern,
        "created_at": t.created_at
    } for t in tasks]

@router.post("/{user_id}")
def create_task(user_id: int, title: str, category: str = "general", description: str = "", priority: int = 0, is_auto: bool = False, source: str = "user", db: Session = Depends(get_db)):
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    task = DailyTask(user_id=user_id, title=title, description=description or None, category=category, priority=priority, is_auto=is_auto, source=source)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "category": task.category}

@router.put("/{task_id}/toggle")
def toggle_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    task.is_completed = not task.is_completed
    task.completed_at = datetime.utcnow() if task.is_completed else None
    db.commit()
    return {"id": task.id, "is_completed": task.is_completed}

@router.put("/{task_id}")
def update_task(task_id: int, title: Optional[str] = None, category: Optional[str] = None, priority: Optional[int] = None, sort_order: Optional[int] = None, db: Session = Depends(get_db)):
    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    if title is not None: task.title = title
    if category is not None: task.category = category
    if priority is not None: task.priority = priority
    if sort_order is not None: task.sort_order = sort_order
    db.commit()
    return {"ok": True}

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}

@router.post("/auto-generate/{user_id}")
def auto_generate_tasks(user_id: int, db: Session = Depends(get_db)):
    """Generate smart daily tasks based on user profile and incomplete routines"""
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    today = datetime.utcnow().replace(hour=0,minute=0,second=0)
    existing = db.query(DailyTask).filter(DailyTask.user_id == user_id, DailyTask.date >= today).count()
    if existing > 3:
        return {"message": "Tasks already exist for today", "count": existing}

    goal = user.primary_goal or "maintenance"
    tasks_data = []

    # Core daily tasks based on goal
    if goal == "fat_loss":
        tasks_data.append({"title": "30 min cardio session", "category": "exercise", "priority": 2, "is_auto": True, "source": "ai_recommendation"})
        tasks_data.append({"title": "Stay under calorie target", "category": "nutrition", "priority": 2, "is_auto": True, "source": "ai_recommendation"})
    elif goal == "muscle_gain":
        tasks_data.append({"title": "Complete today's strength workout", "category": "exercise", "priority": 2, "is_auto": True, "source": "ai_recommendation"})
        tasks_data.append({"title": "Eat protein within 1hr post-workout", "category": "nutrition", "priority": 2, "is_auto": True, "source": "ai_recommendation"})
    else:
        tasks_data.append({"title": "30 min physical activity", "category": "exercise", "priority": 1, "is_auto": True, "source": "ai_recommendation"})

    # Universal tasks
    tasks_data.append({"title": "Drink 8 glasses of water", "category": "hydration", "priority": 1, "is_auto": True, "source": "ai_recommendation"})
    tasks_data.append({"title": "Log your meals", "category": "nutrition", "priority": 1, "is_auto": True, "source": "ai_recommendation"})
    tasks_data.append({"title": "Log your weight", "category": "nutrition", "priority": 0, "is_auto": True, "source": "routine"})
    tasks_data.append({"title": "Stretch for 10 min", "category": "exercise", "priority": 0, "is_auto": True, "source": "routine"})

    # Femme-specific
    if user.gender and user.gender.lower() in ("female", "f"):
        tasks_data.append({"title": "Log cycle symptoms", "category": "femme", "priority": 1, "is_auto": True, "source": "ai_recommendation"})

    for td in tasks_data:
        task = DailyTask(user_id=user_id, date=today, **td)
        db.add(task)
    db.commit()
    return {"message": f"Generated {len(tasks_data)} tasks", "count": len(tasks_data)}
