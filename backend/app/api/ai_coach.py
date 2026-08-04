import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/api/ai", tags=["Secure AI Coach"])


class TodayMetrics(BaseModel):
    calories_eaten: float = 0
    calories_burned: float = 0
    protein_g: float = 0
    hydration_ml: float = 0
    workout_minutes: float = 0
    workouts_logged: int = 0
    meals_logged: int = 0
    recovery_score: Optional[float] = None
    task_completion_pct: Optional[float] = None


class DailyCoachRequest(BaseModel):
    profile: Dict[str, Any] = Field(default_factory=dict)
    today: TodayMetrics = Field(default_factory=TodayMetrics)
    recent_workouts: List[Dict[str, Any]] = Field(default_factory=list)
    recent_meals: List[Dict[str, Any]] = Field(default_factory=list)


class WorkoutPlanRequest(BaseModel):
    goal: str
    level: str
    duration: int
    time_budget_minutes: Optional[int] = None
    target_muscle_groups: List[str] = Field(default_factory=list)


class MealPlanRequest(BaseModel):
    goal: Optional[str] = None
    dailyCalories: Optional[int] = None
    dietaryRestrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)


class BodyAdviceRequest(BaseModel):
    goal: str


class ChatRequest(BaseModel):
    message: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, str]] = Field(default_factory=list)


class MealImageRequest(BaseModel):
    image_base64: str
    user_goal: Optional[str] = None
    daily_calories_remaining: Optional[float] = None


def _fallback_daily_coach(payload: DailyCoachRequest) -> Dict[str, Any]:
    today = payload.today
    goal = (
        payload.profile.get("goal")
        or payload.profile.get("primary_goal")
        or "general fitness"
    )
    if today.workouts_logged == 0:
        action = {
            "title": "Start a focused workout",
            "detail": "A 20-45 minute session will anchor today's progress.",
            "route": "/dashboard/quick",
            "priority": "High",
        }
    elif today.meals_logged < 3:
        action = {
            "title": "Log your next meal",
            "detail": "Prioritize lean protein and a simple carb source.",
            "route": "/dashboard/food-scanner",
            "priority": "High",
        }
    elif today.hydration_ml < 2500:
        action = {
            "title": "Top up hydration",
            "detail": "Drink 500 ml over the next hour.",
            "route": "/dashboard/hydration",
            "priority": "Medium",
        }
    else:
        action = {
            "title": "Review your progress",
            "detail": (
                "Your core habits are covered; check trends and recovery."
            ),
            "route": "/dashboard/progress",
            "priority": "Low",
        }

    return {
        "summary": (
            f"Your current day is aligned with a {goal} goal. "
            "Keep the next action small, measurable, and logged."
        ),
        "next_action": action,
        "focus_area": (
            "Protein consistency"
            if today.protein_g < 100
            else "Recovery quality"
        ),
        "risk": "low" if (today.recovery_score or 85) >= 75 else "moderate",
        "tasks": [
            {
                "id": "hydrate",
                "type": "hydration",
                "label": "Drink 500 ml water",
                "time": "Next hour",
                "priority": "Medium",
                "completed": False,
            },
            {
                "id": "protein",
                "type": "nutrition",
                "label": "Hit your next protein serving",
                "time": "Next meal",
                "priority": "High",
                "completed": False,
            },
            {
                "id": "move",
                "type": "activity",
                "label": "Complete today's movement block",
                "time": "Today",
                "priority": "High",
                "completed": today.workouts_logged > 0,
            },
            {
                "id": "log",
                "type": "nutrition",
                "label": "Log meals before bedtime",
                "time": "Evening",
                "priority": "Medium",
                "completed": today.meals_logged >= 3,
            },
            {
                "id": "recover",
                "type": "recovery",
                "label": "Wind down 30 minutes before sleep",
                "time": "Night",
                "priority": "Low",
                "completed": False,
            },
        ],
    }


def _json_from_text(text: str) -> Any:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def _gemini_json(prompt: str, fallback: Any) -> Any:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return fallback
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=prompt,
        )
        return _json_from_text(response.text or "")
    except Exception:
        return fallback


@router.post("/daily-coach")
async def daily_coach(payload: DailyCoachRequest):
    return _fallback_daily_coach(payload)


@router.post("/daily-tasks")
async def daily_tasks(profile: Dict[str, Any]):
    return _fallback_daily_coach(DailyCoachRequest(profile=profile))["tasks"]


@router.post("/workout-plan")
async def workout_plan(
    payload: WorkoutPlanRequest, db: Session = Depends(get_db)
):
    from ..hybrid_ranker import HybridRanker

    profile = {
        "primary_goal": payload.goal,
        "training_level": payload.level,
    }

    exercises = db.query(models.ExerciseItem).all()
    candidates = []
    for ex in exercises:
        muscle_group = ex.muscle_group or ex.targeted_muscle or ""
        work_sec = ex.avg_set_duration_sec or (
            45 if (ex.movement_pattern or "").lower() in {"push", "pull", "hinge", "squat", "carry"} else 30
        )
        rest_sec = ex.avg_rest_sec or (
            90 if (ex.movement_pattern or "").lower() in {"push", "pull", "hinge", "squat", "carry"} else 45
        )
        candidates.append({
            "id": ex.id,
            "name": ex.name,
            "targeted_muscle": ex.targeted_muscle,
            "muscle_group": muscle_group,
            "difficulty": ex.difficulty,
            "equipment": ex.equipment,
            "calories_per_min": ex.calories_per_min,
            "avg_set_duration_sec": work_sec,
            "avg_rest_sec": rest_sec,
            "default_sets": ex.default_sets or (4 if payload.level.lower() == "advanced" else 3),
            "default_reps": ex.default_reps or ("8-12" if payload.goal.lower() == "muscle_gain" else "10-15"),
            "est_calories_per_set": ex.est_calories_per_set or max(1.5, (ex.calories_per_min or 5.0) * (work_sec / 60.0)),
            "fitness_goal": ex.fitness_goal,
            "description": ex.description
        })

    ranker = HybridRanker(db)
    ranked = ranker.rank_exercises(candidates, profile, limit=30)
    
    budget = payload.time_budget_minutes or payload.duration
    budget_limit = max(15, int(budget * 0.9))
    plan_exercises = []
    total_minutes = 0.0
    total_calories = 0.0
    target_groups = {g.lower() for g in payload.target_muscle_groups if g}
    for ex in ranked:
        if target_groups:
            ex_group = (ex.get("muscle_group") or ex.get("targeted_muscle") or "").lower()
            if not any(group in ex_group for group in target_groups):
                continue
        sets = int(ex.get("default_sets") or (4 if payload.level.lower() == "advanced" else 3))
        work = int(ex.get("avg_set_duration_sec") or 45)
        rest = int(ex.get("avg_rest_sec") or 60)
        est_minutes = (sets * (work + rest)) / 60.0
        if total_minutes + est_minutes > budget_limit and plan_exercises:
            break
        plan_exercises.append({
            "id": ex["id"],
            "name": ex["name"],
            "sets": sets,
            "reps": ex.get("default_reps") or ("8-12" if payload.goal.lower() == "muscle_gain" else "10-15"),
            "description": ex.get("description") or f"Focused training targeting the {ex['targeted_muscle']}.",
            "targeted_muscle": ex["targeted_muscle"],
            "muscle_group": ex.get("muscle_group"),
            "difficulty": ex["difficulty"],
            "equipment": ex["equipment"],
            "avg_set_duration_sec": work,
            "avg_rest_sec": rest,
            "estimated_minutes": round(est_minutes, 1),
            "estimated_calories": round((ex.get("est_calories_per_set") or 0) * sets, 1),
        })
        total_minutes += est_minutes
        total_calories += (ex.get("est_calories_per_set") or 0) * sets
        if total_minutes >= budget_limit:
            break
        
    if not plan_exercises:
        plan_exercises = [
            {
                "id": None,
                "name": "Squat",
                "sets": 4,
                "reps": "8-12",
                "description": "Controlled lower-body compound movement.",
                "targeted_muscle": "Quads and glutes",
                "muscle_group": "Quads",
                "difficulty": payload.level,
                "equipment": "Bodyweight or dumbbells",
                "avg_set_duration_sec": 45,
                "avg_rest_sec": 90,
                "estimated_minutes": 9.0,
                "estimated_calories": 20.0,
            },
            {
                "id": None,
                "name": "Push-up",
                "sets": 3,
                "reps": "8-15",
                "description": "Keep ribs down and press evenly.",
                "targeted_muscle": "Chest and triceps",
                "muscle_group": "Chest",
                "difficulty": payload.level,
                "equipment": "Bodyweight",
                "avg_set_duration_sec": 30,
                "avg_rest_sec": 45,
                "estimated_minutes": 3.8,
                "estimated_calories": 10.0,
            }
        ]

    nutrition_advice = {
        "pre_workout": "Have a light carb and water 45-60 minutes before training.",
        "post_workout": "Eat 25-35g protein within two hours.",
        "recommended_foods": ["Greek yogurt", "Chicken breast", "Rice", "Banana"],
        "hydration_tip": "Sip water steadily during the session."
    }
    
    if payload.goal.lower() == "fat_loss":
        nutrition_advice["recommended_foods"] = ["Egg whites", "Salmon", "Broccoli", "Berries"]
        nutrition_advice["post_workout"] = "Eat 20-30g lean protein with fiber-rich carbs."

    return {
        "title": f"Deterministic {payload.goal.replace('_', ' ').title()} Protocol",
        "duration": f"{payload.duration} mins",
        "intensity": "Medium",
        "exercises": plan_exercises,
        "estimated_total_minutes": round(total_minutes or payload.duration, 1),
        "estimated_total_calories": round(total_calories, 1),
        "nutrition_advice": nutrition_advice
    }


@router.post("/body-advice")
async def body_advice(payload: BodyAdviceRequest):
    advice = {
        "weight_loss": {
            "title": "Fat Loss Plan",
            "description": "Create a sustainable calorie deficit while maintaining muscle mass.",
            "recommendedMacros": {
                "protein": "2.0-2.4 g/kg",
                "carbs": "1.5-2.5 g/kg",
                "fats": "0.6-0.8 g/kg"
            },
            "foodsToFocus": ["Chicken breast", "Eggs", "Spinach", "Salmon", "Oats"],
            "foodsToAvoid": ["Soda", "White bread", "Fried chicken", "Processed snacks"]
        },
        "muscle_gain": {
            "title": "Hypertrophy Program",
            "description": "Provide a clean calorie surplus to fuel muscle growth and strength.",
            "recommendedMacros": {
                "protein": "1.6-2.2 g/kg",
                "carbs": "3.5-5.0 g/kg",
                "fats": "0.8-1.2 g/kg"
            },
            "foodsToFocus": ["Beef", "Rice", "Greek yogurt", "Peanut butter", "Bananas"],
            "foodsToAvoid": ["Sugary cereals", "Excess fast food", "Alcohol"]
        },
        "maintenance": {
            "title": "Healthy Maintenance Profile",
            "description": "Balance energy intake with expenditure to maintain current body weight.",
            "recommendedMacros": {
                "protein": "1.4-1.8 g/kg",
                "carbs": "2.5-3.5 g/kg",
                "fats": "0.7-1.0 g/kg"
            },
            "foodsToFocus": ["Whole grains", "Mixed vegetables", "Eggs", "Avocado", "Trout"],
            "foodsToAvoid": ["Highly refined sugars", "Trans fats", "Sugary drinks"]
        }
    }
    
    goal_key = payload.goal.lower()
    return advice.get(goal_key, advice["maintenance"])


@router.post("/weekly-meal-plan")
async def weekly_meal_plan(payload: MealPlanRequest):
    from app.api.meal_planner import _mock_meal_plan
    from app.schemas import MealPlanGenerateRequest
    prefs = MealPlanGenerateRequest(
        goal=payload.goal,
        daily_calories=payload.dailyCalories,
        dietary_preferences=",".join(payload.dietaryRestrictions),
        allergies=",".join(payload.allergies)
    )
    return _mock_meal_plan(prefs)


@router.post("/chat")
async def chat(payload: ChatRequest):
    raise HTTPException(
        status_code=400,
        detail="Chatbot has been disabled as per safety and precision guidelines."
    )


@router.post("/meal-image")
async def meal_image(payload: MealImageRequest, db: Session = Depends(get_db)):
    import base64
    from app.food_detection_model import FoodDetectionModel
    from app.food_service import FoodDatabaseService

    try:
        image_bytes = base64.b64decode(payload.image_base64)
        detector = FoodDetectionModel()
        detect_result = detector.detect_foods(image_bytes)
        
        items = []
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fats = 0.0
        
        detected_food_names = []
        
        for food in detect_result.detected_foods:
            detected_food_names.append(food.food_name)
            db_food = db.query(models.FoodItem).filter(models.FoodItem.name.ilike(f"%{food.food_name}%")).first()
            grams = food.estimated_quantity_g or 150.0
            factor = grams / 100.0
            
            if db_food:
                name = db_food.name
                cal = db_food.calories * factor
                prot = db_food.protein * factor
                carb = db_food.carbs * factor
                fat = db_food.fats * factor
            else:
                name = food.food_name.title()
                cal = 150.0 * factor
                prot = 10.0 * factor
                carb = 15.0 * factor
                fat = 5.0 * factor
                
            items.append({
                "name": name,
                "portion": f"{int(grams)}g",
                "calories": round(cal, 1),
                "protein": round(prot, 1),
                "carbs": round(carb, 1),
                "fats": round(fat, 1),
                "isHealthy": (cal / (prot + 0.1) < 20)
            })
            
            total_calories += cal
            total_protein += prot
            total_carbs += carb
            total_fats += fat
            
        if not items:
            items = [{
                "name": "Balanced Meal Plate",
                "portion": "350g",
                "calories": 420.0,
                "protein": 30.0,
                "carbs": 45.0,
                "fats": 12.0,
                "isHealthy": True
            }]
            total_calories = 420.0
            total_protein = 30.0
            total_carbs = 45.0
            total_fats = 12.0
            detected_food_names = ["Balanced Meal Plate"]
            
        meal_name = " & ".join([n.title() for n in detected_food_names[:3]])
        
        goal = payload.user_goal or "maintenance"
        goal_alignment = "Perfectly aligned with your goal."
        if goal == "weight_loss":
            goal_alignment = "Ideal low calorie, nutrient dense alignment."
        elif goal == "muscle_gain":
            goal_alignment = "Great amino-acid profile for muscle rebuild."
            
        return {
            "mealName": meal_name,
            "totalCalories": round(total_calories, 1),
            "totalProtein": round(total_protein, 1),
            "totalCarbs": round(total_carbs, 1),
            "totalFats": round(total_fats, 1),
            "items": items,
            "recommendation": f"This meal contains {round(total_protein, 1)}g of protein and total of {round(total_calories, 1)} kcal.",
            "goalAlignment": goal_alignment,
            "mealRating": 5,
            "healthTips": [
                "Drink 300ml of water before eating.",
                "Chew slowly to aid enzyme digestion."
            ],
            "alternatives": [
                "Boiled eggs with spinach",
                "Grilled tofu with mixed salad"
            ]
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Local meal image processing failed: {exc}"
        )
