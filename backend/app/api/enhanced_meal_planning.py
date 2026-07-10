"""
Enhanced Meal Planning API
Shopping lists, meal timing optimization, and budget tracking
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app import database, models
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/meal-planning", tags=["Enhanced Meal Planning"])


class ShoppingListRequest(BaseModel):
    user_id: str
    plan_id: int


class MealTimingRequest(BaseModel):
    user_id: str
    workout_time: Optional[str] = None  # HH:MM format


class BudgetItem(BaseModel):
    food_name: str
    quantity: float
    unit: str
    estimated_price: float


class BudgetTrackingRequest(BaseModel):
    user_id: str
    week_start: str  # ISO format date
    items: List[BudgetItem]


@router.post("/shopping-list/generate")
def generate_shopping_list(
    data: ShoppingListRequest,
    db: Session = Depends(database.get_db),
):
    """
    Generate a shopping list from a meal plan.
    Aggregates all ingredients and organizes by category.
    """
    try:
        # Get the meal plan
        plan = db.query(models.MealPlan).filter(
            and_(
                models.MealPlan.id == data.plan_id,
                models.MealPlan.user_id == data.user_id
            )
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        # Get all meal entries for this plan
        entries = db.query(models.MealPlanEntry).filter(
            models.MealPlanEntry.plan_id == data.plan_id
        ).all()
        
        if not entries:
            return {
                "plan_id": data.plan_id,
                "shopping_list": [],
                "total_items": 0
            }
        
        # Aggregate ingredients by food name
        ingredient_map = {}
        for entry in entries:
            food_name = entry.food_name
            if food_name in ingredient_map:
                ingredient_map[food_name]["quantity"] += 1
                ingredient_map[food_name]["total_calories"] += entry.calories
            else:
                # Try to get food details from database
                food = db.query(models.FoodItem).filter(
                    models.FoodItem.id == entry.food_id
                ).first() if entry.food_id else None
                
                category = "Other"
                if food and food.category:
                    category = food.category.name
                
                ingredient_map[food_name] = {
                    "food_name": food_name,
                    "quantity": 1,
                    "serving_size": entry.serving_size or "serving",
                    "category": category,
                    "total_calories": entry.calories,
                    "protein": entry.protein,
                    "carbs": entry.carbs,
                    "fats": entry.fats
                }
        
        # Organize by category
        categorized_list = {}
        for item in ingredient_map.values():
            category = item["category"]
            if category not in categorized_list:
                categorized_list[category] = []
            categorized_list[category].append({
                "food_name": item["food_name"],
                "quantity": item["quantity"],
                "serving_size": item["serving_size"],
                "estimated_amount": f"{item['quantity']} {item['serving_size']}s"
            })
        
        return {
            "plan_id": data.plan_id,
            "user_id": data.user_id,
            "week_range": {
                "start": plan.week_start.isoformat(),
                "end": plan.week_end.isoformat() if plan.week_end else None
            },
            "shopping_list": categorized_list,
            "total_items": len(ingredient_map),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shopping list generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meal-timing/optimize")
def optimize_meal_timing(
    data: MealTimingRequest,
    db: Session = Depends(database.get_db),
):
    """
    Optimize meal timing based on workout schedule and goals.
    Provides pre/post workout meal recommendations.
    """
    try:
        # Get user profile
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == data.user_id
        ).first()
        
        if not profile:
            # Return default recommendations
            goal = "maintenance"
        else:
            goal = profile.fitness_goal or "maintenance"
        
        # Parse workout time if provided
        workout_hour = None
        if data.workout_time:
            try:
                workout_hour = int(data.workout_time.split(":")[0])
            except:
                workout_hour = 17  # Default to 5 PM
        else:
            workout_hour = 17
        
        # Calculate optimal meal times
        recommendations = {
            "workout_time": data.workout_time or "17:00",
            "meal_schedule": []
        }
        
        # Pre-workout meal (2-3 hours before)
        pre_workout_hour = (workout_hour - 2) % 24
        recommendations["meal_schedule"].append({
            "meal_type": "pre_workout",
            "recommended_time": f"{pre_workout_hour:02d}:00",
            "timing": "2-3 hours before workout",
            "focus": "Complex carbs + moderate protein",
            "examples": [
                "Oatmeal with banana and almonds",
                "Whole grain toast with peanut butter",
                "Brown rice with grilled chicken"
            ],
            "avoid": ["Heavy fats", "High fiber right before workout"]
        })
        
        # Pre-workout snack (30-60 min before)
        pre_snack_hour = (workout_hour - 1) % 24
        recommendations["meal_schedule"].append({
            "meal_type": "pre_workout_snack",
            "recommended_time": f"{pre_snack_hour:02d}:30",
            "timing": "30-60 minutes before workout",
            "focus": "Quick carbs + light protein",
            "examples": [
                "Banana with protein shake",
                "Apple with almond butter",
                "Energy bar"
            ],
            "avoid": ["Heavy meals", "Dairy if sensitive"]
        })
        
        # Post-workout meal (30-60 min after)
        post_workout_hour = (workout_hour + 1) % 24
        recommendations["meal_schedule"].append({
            "meal_type": "post_workout",
            "recommended_time": f"{post_workout_hour:02d}:00",
            "timing": "30-60 minutes after workout",
            "focus": "Fast-digesting protein + carbs",
            "examples": [
                "Protein shake with banana",
                "Grilled chicken with sweet potato",
                "Tuna sandwich on whole wheat"
            ],
            "avoid": ["High fat meals (delays absorption)"]
        })
        
        # Additional meal recommendations based on goal
        if goal == "muscle_gain":
            recommendations["meal_schedule"].append({
                "meal_type": "breakfast",
                "recommended_time": "07:00",
                "focus": "High protein + complex carbs",
                "examples": [
                    "Eggs with oatmeal",
                    "Greek yogurt with granola",
                    "Protein pancakes"
                ]
            })
            recommendations["meal_schedule"].append({
                "meal_type": "evening_snack",
                "recommended_time": "21:00",
                "focus": "Slow-digesting protein",
                "examples": [
                    "Cottage cheese",
                    "Casein protein shake",
                    "Greek yogurt with nuts"
                ]
            })
        elif goal == "fat_loss":
            recommendations["meal_schedule"].append({
                "meal_type": "breakfast",
                "recommended_time": "08:00",
                "focus": "Protein + healthy fats",
                "examples": [
                    "Egg whites with avocado",
                    "Protein smoothie",
                    "Greek yogurt with berries"
                ]
            })
        
        # Sort by time
        recommendations["meal_schedule"].sort(
            key=lambda x: x.get("recommended_time", "00:00")
        )
        
        return {
            "user_id": data.user_id,
            "goal": goal,
            "recommendations": recommendations,
            "notes": [
                "Timing recommendations are guidelines. Adjust based on personal response.",
                "Stay hydrated throughout the day.",
                f"For {goal} goals, consistency is key."
            ]
        }
        
    except Exception as e:
        logger.error(f"Meal timing optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/track")
def track_meal_budget(
    data: BudgetTrackingRequest,
    db: Session = Depends(database.get_db),
):
    """
    Track weekly meal budget and expenses.
    Helps users plan cost-effective meals.
    """
    try:
        # Calculate totals
        total_cost = sum(item.estimated_price for item in data.items)
        
        # Categorize by food type
        category_breakdown = {}
        for item in data.items:
            # Try to find the food in database to get category
            food = db.query(models.FoodItem).filter(
                models.FoodItem.name.ilike(f"%{item.food_name}%")
            ).first()
            
            category = "Other"
            if food and food.category:
                category = food.category.name
            
            if category not in category_breakdown:
                category_breakdown[category] = {
                    "items": [],
                    "total_cost": 0
                }
            
            category_breakdown[category]["items"].append({
                "food_name": item.food_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "price": item.estimated_price
            })
            category_breakdown[category]["total_cost"] += item.estimated_price
        
        # Calculate per-meal and per-day costs
        # Assume 21 meals per week (3 per day)
        cost_per_meal = total_cost / 21
        cost_per_day = total_cost / 7
        
        return {
            "user_id": data.user_id,
            "week_start": data.week_start,
            "summary": {
                "total_cost": round(total_cost, 2),
                "total_items": len(data.items),
                "cost_per_day": round(cost_per_day, 2),
                "cost_per_meal": round(cost_per_meal, 2)
            },
            "category_breakdown": {
                cat: {
                    "items": items["items"],
                    "total_cost": round(items["total_cost"], 2),
                    "percentage": round(items["total_cost"] / total_cost * 100, 1) if total_cost > 0 else 0
                }
                for cat, items in category_breakdown.items()
            },
            "savings_tips": [
                "Buy seasonal produce for better prices",
                "Purchase protein in bulk and freeze portions",
                "Prepare meals in advance to reduce waste",
                "Compare prices across different stores",
                "Use frozen vegetables as cost-effective alternatives"
            ]
        }
        
    except Exception as e:
        logger.error(f"Budget tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget/history/{user_id}")
def get_budget_history(
    user_id: str,
    weeks: int = 8,
    db: Session = Depends(database.get_db),
):
    """
    Get historical budget data for trend analysis.
    (Note: This would require a budget tracking table in production)
    """
    # Mock data for now - in production, this would query a budget_logs table
    return {
        "user_id": user_id,
        "weeks_analyzed": weeks,
        "message": "Budget tracking history coming soon. Use /budget/track to start logging expenses.",
        "average_weekly_cost": 0,
        "trend": "stable"
    }


@router.get("/meal-prep/suggestions/{user_id}")
def get_meal_prep_suggestions(
    user_id: str,
    goal: Optional[str] = None,
    db: Session = Depends(database.get_db),
):
    """
    Get meal prep suggestions optimized for batch cooking and storage.
    """
    try:
        # Get user profile if no goal specified
        if not goal:
            profile = db.query(models.UserProfile).filter(
                models.UserProfile.user_id == user_id
            ).first()
            goal = profile.fitness_goal if profile else "maintenance"
        
        # Meal prep suggestions based on goal
        suggestions = {
            "muscle_gain": [
                {
                    "meal": "High-Protein Meal Prep Bowl",
                    "ingredients": ["Grilled chicken breast", "Brown rice", "Broccoli", "Sweet potato"],
                    "prep_time": "60 minutes",
                    "servings": 5,
                    "storage": "Refrigerate up to 4 days",
                    "macros_per_serving": {"protein": 45, "carbs": 50, "fats": 12, "calories": 480}
                },
                {
                    "meal": "Overnight Protein Oats",
                    "ingredients": ["Oats", "Protein powder", "Almond milk", "Banana", "Peanut butter"],
                    "prep_time": "10 minutes",
                    "servings": 4,
                    "storage": "Refrigerate up to 5 days",
                    "macros_per_serving": {"protein": 30, "carbs": 45, "fats": 15, "calories": 420}
                }
            ],
            "fat_loss": [
                {
                    "meal": "Lean Protein & Veggie Bowl",
                    "ingredients": ["Grilled turkey", "Quinoa", "Mixed vegetables", "Olive oil"],
                    "prep_time": "45 minutes",
                    "servings": 5,
                    "storage": "Refrigerate up to 4 days",
                    "macros_per_serving": {"protein": 35, "carbs": 30, "fats": 10, "calories": 340}
                },
                {
                    "meal": "Egg White Muffins",
                    "ingredients": ["Egg whites", "Spinach", "Tomatoes", "Low-fat cheese"],
                    "prep_time": "30 minutes",
                    "servings": 12,
                    "storage": "Refrigerate up to 5 days or freeze",
                    "macros_per_serving": {"protein": 12, "carbs": 3, "fats": 2, "calories": 75}
                }
            ],
            "maintenance": [
                {
                    "meal": "Balanced Buddha Bowl",
                    "ingredients": ["Grilled salmon", "Quinoa", "Avocado", "Roasted vegetables"],
                    "prep_time": "50 minutes",
                    "servings": 4,
                    "storage": "Refrigerate up to 3 days",
                    "macros_per_serving": {"protein": 30, "carbs": 35, "fats": 18, "calories": 420}
                },
                {
                    "meal": "Chicken Stir-Fry Packs",
                    "ingredients": ["Chicken breast", "Mixed vegetables", "Brown rice", "Soy sauce"],
                    "prep_time": "40 minutes",
                    "servings": 5,
                    "storage": "Refrigerate up to 4 days",
                    "macros_per_serving": {"protein": 35, "carbs": 40, "fats": 10, "calories": 390}
                }
            ]
        }
        
        goal_suggestions = suggestions.get(goal, suggestions["maintenance"])
        
        return {
            "user_id": user_id,
            "goal": goal,
            "suggestions": goal_suggestions,
            "tips": [
                "Invest in quality meal prep containers",
                "Cook proteins in bulk and season differently",
                "Prep vegetables in advance for quick assembly",
                "Label containers with date and contents",
                "Freeze extra portions for variety"
            ]
        }
        
    except Exception as e:
        logger.error(f"Meal prep suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
