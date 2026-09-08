import base64
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.ai_multi_provider import ai_engine
from app.database import get_db
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["Secure AI Coach & Multi-Provider Hub"])


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


class VoiceSpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class VoiceTranscribeRequest(BaseModel):
    audio_base64: Optional[str] = None
    content_type: str = "audio/webm"
    mode: str = "general"  # "general", "meal", "workout"


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
            "detail": "Your core habits are covered; check trends and recovery.",
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


# ──────────────────────────────────────────────────────────────────────────
# 1. DAILY COACH & TASKS
# ──────────────────────────────────────────────────────────────────────────
@router.post("/daily-coach")
async def daily_coach(
    payload: DailyCoachRequest,
    current_auth_id: str = Depends(get_current_user_id)
):
    base_plan = _fallback_daily_coach(payload)
    prompt = f"""
Given this user's profile and metrics today:
- Goal: {payload.profile.get('primary_goal') or payload.profile.get('goal') or 'fitness'}
- Calories Eaten: {payload.today.calories_eaten} kcal
- Protein Eaten: {payload.today.protein_g}g
- Hydration: {payload.today.hydration_ml} ml
- Workouts Logged: {payload.today.workouts_logged}
- Recovery Score: {payload.today.recovery_score or 85}%

Write a 2-sentence actionable, encouraging daily coach summary for their dashboard:
"""
    try:
        res = await ai_engine.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are Smarty AI, an elite, scientific fitness coach. Be concise, motivating, and specific.",
            temperature=0.6,
            max_tokens=150,
        )
        if res.get("text"):
            base_plan["summary"] = res["text"]
    except Exception as e:
        logger.warning(f"AI daily coach generation error: {e}")

    return base_plan


@router.post("/daily-tasks")
async def daily_tasks(
    profile: Dict[str, Any],
    current_auth_id: str = Depends(get_current_user_id)
):
    return _fallback_daily_coach(DailyCoachRequest(profile=profile))["tasks"]


# ──────────────────────────────────────────────────────────────────────────
# 2. CONVERSATIONAL AI CHATBOT (Groq / Gemini / OpenRouter)
# ──────────────────────────────────────────────────────────────────────────
@router.post("/chat")
async def chat(
    payload: ChatRequest,
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Real-time interactive AI fitness coach conversation.
    Grounds responses in user biometric data, workout history, and recovery status.
    """
    user_msg = (payload.message or "").strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    p = payload.profile or {}
    goal = p.get("primary_goal") or p.get("goal") or "general fitness"
    gender = p.get("gender") or "unspecified"
    weight = p.get("weight_kg") or p.get("weight") or "unspecified"
    height = p.get("height_cm") or p.get("height") or "unspecified"
    activity_level = p.get("activity_level") or "moderate"
    calorie_goal = p.get("daily_calorie_target") or p.get("calorieGoal") or 2200
    protein_goal = p.get("protein_target_g") or p.get("proteinGoal") or 140

    system_prompt = f"""
You are SMARTY AI, an advanced, highly knowledgeable, and friendly personal AI health, nutrition, and fitness consultant.

User Bio-Profile Context:
- Primary Goal: {goal}
- Gender: {gender}
- Weight: {weight} kg
- Height: {height} cm
- Activity Level: {activity_level}
- Target Daily Calories: {calorie_goal} kcal
- Target Daily Protein: {protein_goal} g
{f"- Today's Coach Briefing: {p.get('today_coach_summary')}" if p.get('today_coach_summary') else ""}
{f"- Today's Workout Focus: {p.get('today_coach_workout')}" if p.get('today_coach_workout') else ""}
{f"- Next Meal Target: {p.get('today_coach_meal')}" if p.get('today_coach_meal') else ""}

Instructions:
1. Provide accurate, scientifically grounded, and concise advice.
2. If asked about workouts, provide specific exercises, sets, reps, and cues.
3. If asked about nutrition, provide exact food examples and macronutrient breakdowns.
4. Keep a modern, encouraging, and razor-sharp tone. Use clean bullet points and markdown bolding where helpful.
5. If the user mentions injury or pain, give safe regression alternatives and suggest consulting a medical professional.
"""

    formatted_history: List[Dict[str, str]] = []
    for item in payload.history[-8:]:
        role = "user" if item.get("role") in ("user", "human") else "assistant"
        content = item.get("text") or item.get("content") or ""
        if content:
            formatted_history.append({"role": role, "content": content})

    formatted_history.append({"role": "user", "content": user_msg})

    try:
        ai_res = await ai_engine.chat_completion(
            messages=formatted_history,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=600,
        )
        return {
            "text": ai_res.get("text", "I am here to help optimize your training and nutrition."),
            "provider": ai_res.get("provider", "multi-provider"),
            "model": ai_res.get("model", "standard"),
        }
    except Exception as exc:
        logger.error(f"Error in chat endpoint: {exc}")
        return {
            "text": "I am currently analyzing your profile. How can I assist with your workout or diet plan today?",
            "provider": "fallback",
            "model": "rule-grounded",
        }


# ──────────────────────────────────────────────────────────────────────────
# 3. VOICE AI (Deepgram STT & TTS)
# ──────────────────────────────────────────────────────────────────────────
@router.post("/voice-transcribe")
async def voice_transcribe(payload: VoiceTranscribeRequest):
    """
    Transcribe audio base64 via Deepgram STT.
    If mode is 'meal', also automatically parses macros and food items.
    """
    if not payload.audio_base64:
        raise HTTPException(status_code=400, detail="Missing audio_base64 data.")

    try:
        raw_b64 = payload.audio_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        audio_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio: {e}")

    result = await ai_engine.transcribe_speech(
        audio_bytes=audio_bytes,
        content_type=payload.content_type,
    )
    transcript = result.get("transcript", "").strip()

    parsed_meal = None
    if transcript and payload.mode == "meal":
        parsed_meal = await ai_engine.parse_voice_meal(transcript)

    return {
        "transcript": transcript,
        "confidence": result.get("confidence", 0.0),
        "provider": result.get("provider", "deepgram"),
        "parsed_meal": parsed_meal,
    }


@router.post("/voice-transcribe-file")
async def voice_transcribe_file(
    file: UploadFile = File(...),
    mode: str = Form("general"),
):
    """Multipart audio upload endpoint for voice transcription."""
    audio_bytes = await file.read()
    result = await ai_engine.transcribe_speech(
        audio_bytes=audio_bytes,
        content_type=file.content_type or "audio/wav",
    )
    transcript = result.get("transcript", "").strip()

    parsed_meal = None
    if transcript and mode == "meal":
        parsed_meal = await ai_engine.parse_voice_meal(transcript)

    return {
        "transcript": transcript,
        "confidence": result.get("confidence", 0.0),
        "provider": result.get("provider", "deepgram"),
        "parsed_meal": parsed_meal,
    }


@router.post("/voice-speak")
async def voice_speak(payload: VoiceSpeakRequest):
    """
    Synthesize high-fidelity voice speech using Deepgram Aura TTS.
    Returns audio/mp3 bytes.
    """
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    audio_bytes = await ai_engine.synthesize_speech(text, voice=payload.voice)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")

    return Response(
        content=audio_bytes,
        media_type="audio/mp3",
        headers={"Content-Disposition": 'inline; filename="coach_voice.mp3"'},
    )


# ──────────────────────────────────────────────────────────────────────────
# 4. VISION MEAL SCANNER (Gemini 3.6/3.5 Flash & Local DB)
# ──────────────────────────────────────────────────────────────────────────
@router.post("/meal-image")
async def meal_image(payload: MealImageRequest, db: Session = Depends(get_db)):
    """Analyze a food image and return exact ingredients and macronutrients."""
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        image_bytes = base64.b64decode(raw_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {exc}")

    result = await ai_engine.scan_meal_image(
        image_bytes=image_bytes,
        user_goal=payload.user_goal or "maintenance",
        daily_calories_remaining=payload.daily_calories_remaining,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────
# 5. WORKOUT & MEAL PLANS
# ──────────────────────────────────────────────────────────────────────────
@router.post("/workout-plan")
async def workout_plan(payload: WorkoutPlanRequest, db: Session = Depends(get_db)):
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
            "description": ex.description,
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
                "name": "Barbell Squat",
                "sets": 4,
                "reps": "8-12",
                "description": "Controlled lower-body compound movement for quad and glute hypertrophy.",
                "targeted_muscle": "Quads and glutes",
                "muscle_group": "Quads",
                "difficulty": payload.level,
                "equipment": "Barbell / Dumbbells",
                "avg_set_duration_sec": 45,
                "avg_rest_sec": 90,
                "estimated_minutes": 9.0,
                "estimated_calories": 25.0,
            },
            {
                "id": None,
                "name": "Push-up / Dumbbell Press",
                "sets": 3,
                "reps": "8-15",
                "description": "Keep core tight and press smoothly through full range of motion.",
                "targeted_muscle": "Chest and triceps",
                "muscle_group": "Chest",
                "difficulty": payload.level,
                "equipment": "Bodyweight / Dumbbells",
                "avg_set_duration_sec": 30,
                "avg_rest_sec": 60,
                "estimated_minutes": 4.5,
                "estimated_calories": 15.0,
            },
        ]

    nutrition_advice = {
        "pre_workout": "Have a light carb and water 45-60 minutes before training.",
        "post_workout": "Eat 25-35g protein within two hours.",
        "recommended_foods": ["Greek yogurt", "Chicken breast", "Rice", "Banana"],
        "hydration_tip": "Sip water steadily during the session.",
    }

    if payload.goal.lower() in ("fat_loss", "weight_loss"):
        nutrition_advice["recommended_foods"] = ["Egg whites", "Salmon", "Broccoli", "Berries"]
        nutrition_advice["post_workout"] = "Eat 20-30g lean protein with fiber-rich carbs."

    return {
        "title": f"Smarty AI {payload.goal.replace('_', ' ').title()} Protocol",
        "duration": f"{payload.duration} mins",
        "intensity": "Medium-High",
        "exercises": plan_exercises,
        "estimated_total_minutes": round(total_minutes or payload.duration, 1),
        "estimated_total_calories": round(total_calories, 1),
        "nutrition_advice": nutrition_advice,
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
                "fats": "0.6-0.8 g/kg",
            },
            "foodsToFocus": ["Chicken breast", "Eggs", "Spinach", "Salmon", "Oats"],
            "foodsToAvoid": ["Soda", "White bread", "Fried chicken", "Processed snacks"],
        },
        "muscle_gain": {
            "title": "Hypertrophy Program",
            "description": "Provide a clean calorie surplus to fuel muscle growth and strength.",
            "recommendedMacros": {
                "protein": "1.6-2.2 g/kg",
                "carbs": "3.5-5.0 g/kg",
                "fats": "0.8-1.2 g/kg",
            },
            "foodsToFocus": ["Beef", "Rice", "Greek yogurt", "Peanut butter", "Bananas"],
            "foodsToAvoid": ["Sugary cereals", "Excess fast food", "Alcohol"],
        },
        "maintenance": {
            "title": "Healthy Maintenance Profile",
            "description": "Balance energy intake with expenditure to maintain current body weight.",
            "recommendedMacros": {
                "protein": "1.4-1.8 g/kg",
                "carbs": "2.5-3.5 g/kg",
                "fats": "0.7-1.0 g/kg",
            },
            "foodsToFocus": ["Whole grains", "Mixed vegetables", "Eggs", "Avocado", "Trout"],
            "foodsToAvoid": ["Highly refined sugars", "Trans fats", "Sugary drinks"],
        },
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
        allergies=",".join(payload.allergies),
    )
    return _mock_meal_plan(prefs)
