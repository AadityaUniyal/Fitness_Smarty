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
    fallback = _fallback_daily_coach(payload)
    prompt = (
        "You are SMARTY AI, a concise fitness coach. Return ONLY valid JSON.\n"
        "\n"
        "User profile:\n"
        f"{json.dumps(payload.profile, ensure_ascii=True)}\n"
        "\n"
        "Today's metrics:\n"
        f"{payload.today.model_dump_json()}\n"
        "\n"
        "Recent workouts:\n"
        f"{json.dumps(payload.recent_workouts[:5], ensure_ascii=True)}\n"
        "\n"
        "Recent meals:\n"
        f"{json.dumps(payload.recent_meals[:5], ensure_ascii=True)}\n"
        "\n"
        "Output schema:\n"
        "{\n"
        '  "summary": "2 concise sentences max",\n'
        '  "next_action": {\n'
        '    "title": "...",\n'
        '    "detail": "...",\n'
        '    "route": "/dashboard/quick|/dashboard/food-scanner|'
        '/dashboard/hydration|/dashboard/progress",\n'
        '    "priority": "High|Medium|Low"\n'
        '  },\n'
        '  "focus_area": "...",\n'
        '  "risk": "low|moderate|high",\n'
        '  "tasks": [\n'
        '    {\n'
        '      "id": "short-id",\n'
        '      "type": "hydration|nutrition|activity|recovery",\n'
        '      "label": "...",\n'
        '      "time": "...",\n'
        '      "priority": "High|Medium|Low",\n'
        '      "completed": false\n'
        '    }\n'
        '  ]\n'
        "}\n"
    )
    return _gemini_json(prompt, fallback)


@router.post("/daily-tasks")
async def daily_tasks(profile: Dict[str, Any]):
    fallback_tasks = _fallback_daily_coach(
        DailyCoachRequest(profile=profile)
    )["tasks"]
    prompt = (
        "Return ONLY valid JSON: a 5 item daily fitness checklist array.\n"
        f"Profile: {json.dumps(profile, ensure_ascii=True)}\n"
        "Each item: id, type(hydration|nutrition|activity|recovery), "
        "label, time, priority(High|Medium|Low), completed.\n"
    )
    return _gemini_json(prompt, fallback_tasks)


@router.post("/workout-plan")
async def workout_plan(
    payload: WorkoutPlanRequest, db: Session = Depends(get_db)
):
    from ..hybrid_ranker import HybridRanker

    profile = {
        "primary_goal": payload.goal,
        "training_level": payload.level,
    }

    exercises = db.query(models.ExerciseItem).limit(100).all()
    candidates = []
    for ex in exercises:
        candidates.append({
            "name": ex.name,
            "targeted_muscle": ex.targeted_muscle,
            "difficulty": ex.difficulty,
            "equipment": ex.equipment,
            "calories_per_min": ex.calories_per_min,
            "fitness_goal": ex.fitness_goal,
        })

    ranker = HybridRanker(db)
    ranked = ranker.rank_exercises(candidates, profile, limit=15)

    fallback = {
        "title": f"{payload.goal} Protocol",
        "duration": f"{payload.duration} mins",
        "intensity": "Medium",
        "exercises": [
            {
                "name": "Squat",
                "sets": 4,
                "reps": "8-12",
                "description": "Controlled lower-body compound movement.",
                "targeted_muscle": "Quads and glutes",
                "difficulty": payload.level,
                "equipment": "Bodyweight or dumbbells",
            },
            {
                "name": "Push-up",
                "sets": 3,
                "reps": "8-15",
                "description": "Keep ribs down and press evenly.",
                "targeted_muscle": "Chest and triceps",
                "difficulty": payload.level,
                "equipment": "Bodyweight",
            },
        ],
        "nutrition_advice": {
            "pre_workout": (
                "Have a light carb and water 45-60 minutes before training."
            ),
            "post_workout": "Eat 25-35g protein within two hours.",
            "recommended_foods": [
                "Greek yogurt", "Chicken breast", "Rice", "Banana"
            ],
            "hydration_tip": "Sip water steadily during the session.",
        },
    }
    prompt = (
        "Generate a structured workout plan as JSON using ONLY these "
        f"exercise candidates:\n{json.dumps(ranked, ensure_ascii=True)}\n\n"
        f"Rules:\n"
        f"- Target duration: {payload.duration} minutes\n"
        f"- Goal: {payload.goal}\n"
        f"- Level: {payload.level}\n"
        f"- Include title, duration, intensity, exercises, "
        f"nutrition_advice.\n"
        f"- For each exercise, provide sets, reps, description, "
        f"targeted_muscle, difficulty, equipment.\n\n"
        f"Return ONLY JSON."
    )
    return _gemini_json(prompt, fallback)


@router.post("/body-advice")
async def body_advice(payload: BodyAdviceRequest):
    fallback = {
        "title": payload.goal,
        "description": (
            "Focus on consistent training, enough protein, "
            "hydration, and recovery."
        ),
        "recommendedMacros": {
            "protein": "1.6-2.2 g/kg",
            "carbs": "match training demand",
            "fats": "20-30% calories",
        },
        "foodsToFocus": [
            "Lean protein", "Whole grains", "Vegetables", "Fruit"
        ],
        "foodsToAvoid": ["Ultra-processed snacks", "Sugary drinks"],
    }
    prompt = (
        f"Return ONLY JSON nutrition/body advice for this goal: "
        f"{payload.goal}. Fields: title, description, recommendedMacros, "
        f"foodsToFocus, foodsToAvoid."
    )
    return _gemini_json(prompt, fallback)


@router.post("/weekly-meal-plan")
async def weekly_meal_plan(payload: MealPlanRequest):
    fallback: List[Dict[str, Any]] = []
    prompt = (
        "\nReturn ONLY valid JSON array with exactly 28 meals.\n"
        f"Profile: {payload.model_dump_json()}\n"
        "Each item: day_of_week 0-6, meal_slot breakfast|lunch|dinner|snack, "
        "food_name, serving_size, calories, protein, carbs, fats.\n"
    )
    return _gemini_json(prompt, fallback)


@router.post("/chat")
async def chat(payload: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {
            "text": (
                "AI chat is running in safe mode. Configure GEMINI_API_KEY "
                "on the backend to enable live coaching."
            )
        }
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        history_text = "\n".join(
            f"{m.get('role', 'user')}: {m.get('text', '')}"
            for m in payload.history[-8:]
        )
        prompt = (
            "You are SMARTY, a concise fitness coach. "
            f"Profile: {json.dumps(payload.profile, ensure_ascii=True)}\n"
            f"History:\n{history_text}\nUser: {payload.message}"
        )
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=prompt,
        )
        return {"text": response.text or ""}
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"AI chat failed: {exc}"
        )


@router.post("/meal-image")
async def meal_image(payload: MealImageRequest):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the backend",
        )
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        cal_rem = (
            payload.daily_calories_remaining
            if payload.daily_calories_remaining is not None
            else "unknown"
        )
        prompt = (
            f"\nAnalyze this meal image for goal "
            f"'{payload.user_goal or 'general fitness'}'.\n"
            f"Calories remaining today: {cal_rem}.\n"
            f"Return ONLY JSON with mealName,totalCalories,totalProtein,"
            f"totalCarbs,totalFats,items,recommendation,goalAlignment,"
            f"mealRating,healthTips,alternatives.\n"
        )
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=[
                types.Part.from_bytes(
                    data=__import__("base64").b64decode(payload.image_base64),
                    mime_type="image/jpeg",
                ),
                prompt,
            ],
        )
        return _json_from_text(response.text or "")
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Meal image analysis failed: {exc}",
        )
