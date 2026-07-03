
from sqlalchemy.orm import Session
from . import models

def search_biofuels(db: Session, query: str = None, category_id: int = None):
    """
    Search and filter the food library based on name and category.
    """
    db_query = db.query(models.FoodItem)
    
    if category_id:
        db_query = db_query.filter(models.FoodItem.category_id == category_id)
        
    if query:
        # Simple case-insensitive search
        db_query = db_query.filter(models.FoodItem.name.ilike(f"%{query}%"))
        
    return db_query.all()

def calculate_item_macros(item, grams: float):
    """Calculates macros for a specific amount of food in grams."""
    # Assuming the DB values are per 100g as per seeding script
    factor = grams / 100.0
    return {
        "name": item.name,
        "grams": grams,
        "calories": round(item.calories * factor, 1),
        "protein": round(item.protein * factor, 1),
        "carbs": round(item.carbs * factor, 1),
        "fats": round(item.fats * factor, 1),
    }

def get_nutritional_summary(items_with_grams: list):
    """
    Calculates total macros for a set of items with their respective gram amounts.
    items_with_grams: List of tuples (FoodItem, grams)
    """
    total = {
        "total_calories": 0.0,
        "total_protein": 0.0,
        "total_carbs": 0.0,
        "total_fats": 0.0,
    }
    
    for item, grams in items_with_grams:
        macros = calculate_item_macros(item, grams)
        total["total_calories"] += macros["calories"]
        total["total_protein"] += macros["protein"]
        total["total_carbs"] += macros["carbs"]
        total["total_fats"] += macros["fats"]
        
    return {k: round(v, 1) for k, v in total.items()}
def get_meal_feedback(meal_macros: dict, goal: str):
    """
    Grades a meal (A-E) based on its macro distribution and the user's goal.
    meal_macros: {'calories': float, 'protein': float, 'carbs': float, 'fats': float}
    goal: 'fat_loss', 'muscle_gain', 'athletic', 'maintenance'
    """
    if meal_macros['calories'] <= 0:
        return {"grade": "N/A", "message": "No nutritional data found."}

    # Calculate actual distribution
    p_cal = meal_macros['protein'] * 4
    c_cal = meal_macros['carbs'] * 4
    f_cal = meal_macros['fats'] * 9
    total = p_cal + c_cal + f_cal or 1
    
    p_pct = p_cal / total
    c_pct = c_cal / total
    f_pct = f_cal / total

    # Grade based on goal
    grade = "B"
    message = "Balanced meal choice."

    if goal == 'fat_loss':
        if p_pct >= 0.35 and c_pct <= 0.35:
            grade, message = "A", "Excellent high-protein, low-carb choice for fat loss."
        elif c_pct > 0.55:
            grade, message = "C", "A bit high in carbs for fat loss. Try adding more protein."
        elif f_pct > 0.45:
            grade, message = "D", "High fat content. Watch your oil/butter intake."
            
    elif goal == 'muscle_gain':
        if p_pct >= 0.25 and c_pct >= 0.45:
            grade, message = "A", "Perfect fuel/protein mix for hypertrophy."
        elif p_pct < 0.15:
            grade, message = "C", "Low protein detected. Muscles need more building blocks!"
            
    elif goal == 'athletic':
        if 0.4 <= c_pct <= 0.6 and p_pct >= 0.2:
            grade, message = "A", "Ideal balanced energy for performance."
            
    return {
        "grade": grade,
        "message": message,
        "distribution": {"protein": round(p_pct*100, 1), "carbs": round(c_pct*100, 1), "fats": round(f_pct*100, 1)}
    }

def get_daily_strategy(consumed: dict, targets: dict, time_of_day: str):
    """
    Calculates remaining targets and suggests a strategy for the next meal.
    consumed: {'calories': f, 'protein': f, 'carbs': f, 'fats': f}
    targets: {'calories': f, 'protein': f, 'carbs': f, 'fats': f}
    """
    remaining = {k: max(0, targets.get(k, 0) - consumed.get(k, 0)) for k in ['calories', 'protein', 'carbs', 'fats']}
    
    # Analyze deficits
    p_deficit = remaining['protein'] > (targets['protein'] * 0.4) # Still need 40% of protein
    c_surplus = consumed['carbs'] > (targets['carbs'] * 0.7) # Already ate 70% of carbs
    
    strategy = "Keep following your plan."
    advice = []

    if p_deficit:
        advice.append("Focus primarily on lean protein (chicken, fish, tofu).")
    if c_surplus:
        advice.append("Limit further carb intake. Opt for fibrous vegetables instead.")
    if remaining['calories'] < 300:
        advice.append("Calories low. Focus on volume-eating (greens) to stay full.")
        
    if advice:
        strategy = " ".join(advice)

    return {
        "remaining": remaining,
        "strategy": strategy,
        "is_budget_critical": remaining['calories'] < (targets['calories'] * 0.2)
    }
