import json, os, logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/meal-plans", tags=["Meal Planner"])


def _gemini_generate_meal_plan(prefs: schemas.MealPlanGenerateRequest) -> List[dict]:
    """Call Gemini API to generate a 7-day meal plan. Falls back to mock data."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key:
        try:
            try:
                import google.genai as genai
            except ImportError:
                import google.generativeai as genai
            genai.configure(api_key=api_key)
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            slots = ["breakfast", "lunch", "dinner", "snack"]
            prompt = f"""Generate a 7-day meal plan as JSON. Return ONLY valid JSON with no markdown formatting.

Rules:
- Daily calorie target: {prefs.daily_calories or 2000}
- Goal: {prefs.goal or 'general'}
- Dietary preferences: {prefs.dietary_preferences or 'none'}
- Allergies: {prefs.allergies or 'none'}
- Exclude: {prefs.exclude_foods or 'none'}
- 4 meals per day: breakfast, lunch, dinner, snack
- Include realistic calorie, protein(g), carbs(g), fats(g) for each meal

Output format (array of objects):
[
  {{"day_of_week": 0, "meal_slot": "breakfast", "food_name": "...", "serving_size": "...", "calories": 0, "protein": 0, "carbs": 0, "fats": 0}},
  ...
]

day_of_week: 0=Monday .. 6=Sunday.
Generate all 28 meals (7 days x 4 slots)."""
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            text = resp.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            entries = json.loads(text)
            if isinstance(entries, list) and len(entries) == 28:
                return entries
        except Exception as e:
            logger.warning(f"Gemini meal plan generation failed: {e}")
    return _mock_meal_plan(prefs)


def _mock_meal_plan(prefs: schemas.MealPlanGenerateRequest) -> List[dict]:
    """Generate a mock 7-day meal plan when Gemini is unavailable."""
    meals_by_slot = {
        "breakfast": [
            ("Oatmeal with Berries", "1 bowl", 350, 12, 58, 6),
            ("Scrambled Eggs & Toast", "2 eggs + 2 slices", 420, 28, 30, 18),
            ("Greek Yogurt Parfait", "250g", 320, 20, 42, 8),
            ("Smoothie Bowl", "400ml", 380, 15, 60, 10),
            ("Protein Pancakes", "3 pancakes", 400, 30, 45, 12),
            ("Avocado Toast", "2 slices", 360, 12, 35, 20),
            ("Granola with Milk", "1 cup", 340, 14, 55, 9),
        ],
        "lunch": [
            ("Grilled Chicken Salad", "400g", 450, 40, 15, 22),
            ("Turkey Wrap", "1 wrap", 480, 35, 40, 18),
            ("Quinoa Buddha Bowl", "500g", 420, 18, 55, 14),
            ("Tuna Sandwich", "1 sandwich", 440, 32, 45, 15),
            ("Lentil Soup", "500ml", 380, 22, 52, 10),
            ("Caesar Salad with Chicken", "450g", 460, 38, 18, 26),
            ("Beef Stir-fry", "400g", 490, 42, 35, 20),
        ],
        "dinner": [
            ("Salmon with Rice", "200g + 1 cup", 520, 42, 50, 16),
            ("Chicken Pasta", "400g", 550, 38, 55, 18),
            ("Vegetable Curry", "500g", 420, 16, 60, 14),
            ("Beef Tacos", "3 tacos", 510, 36, 45, 22),
            ("Baked Cod & Potatoes", "300g + 200g", 470, 40, 40, 14),
            ("Stir-fry Tofu & Rice", "450g", 410, 22, 55, 12),
            ("Lean Steak & Veggies", "200g + 300g", 500, 48, 25, 22),
        ],
        "snack": [
            ("Protein Shake", "1 scoop + milk", 180, 25, 12, 3),
            ("Apple with Almond Butter", "1 apple + 2 tbsp", 220, 6, 28, 10),
            ("Mixed Nuts", "1 handful", 170, 5, 6, 15),
            ("Cottage Cheese & Pineapple", "200g", 160, 22, 12, 4),
            ("Rice Cakes with Hummus", "3 cakes + 3 tbsp", 190, 7, 25, 8),
            ("Greek Yogurt", "200g", 140, 18, 8, 4),
            ("Protein Bar", "1 bar", 200, 20, 22, 6),
        ],
    }
    entries = []
    for day in range(7):
        for slot in ["breakfast", "lunch", "dinner", "snack"]:
            pool = meals_by_slot[slot]
            name, serving, cal, prot, carbs, fats = pool[day % len(pool)]
            entries.append({
                "day_of_week": day,
                "meal_slot": slot,
                "food_name": name,
                "serving_size": serving,
                "calories": cal,
                "protein": prot,
                "carbs": carbs,
                "fats": fats,
            })
    return entries


@router.get("/plans", response_model=List[schemas.MealPlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    plans = db.query(models.MealPlan).filter(
        models.MealPlan.user_id == current_user.id
    ).order_by(desc(models.MealPlan.week_start)).all()
    result = []
    for p in plans:
        result.append(schemas.MealPlanResponse(
            id=p.id, week_start=p.week_start, week_end=p.week_end,
            entries=[schemas.MealPlanEntryResponse(
                id=e.id, day_of_week=e.day_of_week, meal_slot=e.meal_slot,
                food_name=e.food_name, serving_size=e.serving_size,
                calories=e.calories, protein=e.protein, carbs=e.carbs, fats=e.fats,
                food_id=e.food_id,
            ) for e in p.entries],
            created_at=p.created_at, updated_at=p.updated_at,
        ))
    return result


@router.post("/plans", response_model=schemas.MealPlanResponse, status_code=201)
def create_plan(
    data: schemas.MealPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    try:
        ws = datetime.fromisoformat(data.week_start)
    except ValueError:
        raise HTTPException(400, "Invalid week_start format (use ISO date)")
    plan = models.MealPlan(
        user_id=current_user.id, week_start=ws,
        week_end=datetime(ws.year, ws.month, ws.day, 23, 59, 59) if ws else None,
    )
    db.add(plan)
    db.flush()
    for e in data.entries:
        db.add(models.MealPlanEntry(
            plan_id=plan.id, day_of_week=e.day_of_week, meal_slot=e.meal_slot,
            food_name=e.food_name, serving_size=e.serving_size,
            calories=e.calories, protein=e.protein, carbs=e.carbs, fats=e.fats,
            food_id=e.food_id,
        ))
    db.commit()
    db.refresh(plan)
    return schemas.MealPlanResponse(
        id=plan.id, week_start=plan.week_start, week_end=plan.week_end,
        entries=[schemas.MealPlanEntryResponse(
            id=e.id, day_of_week=e.day_of_week, meal_slot=e.meal_slot,
            food_name=e.food_name, serving_size=e.serving_size,
            calories=e.calories, protein=e.protein, carbs=e.carbs, fats=e.fats,
            food_id=e.food_id,
        ) for e in plan.entries],
        created_at=plan.created_at, updated_at=plan.updated_at,
    )


@router.get("/plans/{plan_id}", response_model=schemas.MealPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    return schemas.MealPlanResponse(
        id=plan.id, week_start=plan.week_start, week_end=plan.week_end,
        entries=[schemas.MealPlanEntryResponse(
            id=e.id, day_of_week=e.day_of_week, meal_slot=e.meal_slot,
            food_name=e.food_name, serving_size=e.serving_size,
            calories=e.calories, protein=e.protein, carbs=e.carbs, fats=e.fats,
            food_id=e.food_id,
        ) for e in plan.entries],
        created_at=plan.created_at, updated_at=plan.updated_at,
    )


@router.delete("/plans/{plan_id}", status_code=204)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    plan = db.query(models.MealPlan).filter(
        models.MealPlan.id == plan_id,
        models.MealPlan.user_id == current_user.id,
    ).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    db.delete(plan)
    db.commit()


@router.post("/generate", response_model=schemas.MealPlanResponse, status_code=201)
def generate_plan(
    prefs: schemas.MealPlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    try:
        ws = datetime.fromisoformat(prefs.week_start)
    except ValueError:
        raise HTTPException(400, "Invalid week_start format (use ISO date)")
    entries_data = _gemini_generate_meal_plan(prefs)
    plan = models.MealPlan(
        user_id=current_user.id, week_start=ws,
        week_end=datetime(ws.year, ws.month, ws.day, 23, 59, 59) + timedelta(days=6),
    )
    db.add(plan)
    db.flush()
    for e in entries_data:
        db.add(models.MealPlanEntry(
            plan_id=plan.id, day_of_week=e["day_of_week"], meal_slot=e["meal_slot"],
            food_name=e["food_name"], serving_size=e.get("serving_size"),
            calories=e.get("calories", 0), protein=e.get("protein", 0),
            carbs=e.get("carbs", 0), fats=e.get("fats", 0),
        ))
    db.commit()
    db.refresh(plan)
    return schemas.MealPlanResponse(
        id=plan.id, week_start=plan.week_start, week_end=plan.week_end,
        entries=[schemas.MealPlanEntryResponse(
            id=e.id, day_of_week=e.day_of_week, meal_slot=e.meal_slot,
            food_name=e.food_name, serving_size=e.serving_size,
            calories=e.calories, protein=e.protein, carbs=e.carbs, fats=e.fats,
            food_id=e.food_id,
        ) for e in plan.entries],
        created_at=plan.created_at, updated_at=plan.updated_at,
    )
