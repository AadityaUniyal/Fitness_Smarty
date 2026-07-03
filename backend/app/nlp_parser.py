import re
from sqlalchemy.orm import Session
from app.models import FoodItem

# Regex to capture quantity (integer or decimal), unit (g, grams, cups, pieces), and name of food
QUANTITY_PATTERN = re.compile(
    r'(?P<quantity>\d+(?:\.\d+)?)\s*(?P<unit>g|grams|ml|oz|cups|pieces|piece|scoops|scoop|slices|slice)?\s+(?P<food>.+)', 
    re.IGNORECASE
)

# Alternative simple format (e.g. "a banana", "an egg")
ARTICLE_PATTERN = re.compile(
    r'(?P<article>a|an)\s+(?P<food>[a-zA-Z\s]+)', 
    re.IGNORECASE
)

def parse_meal_text(text: str, db: Session) -> list:
    """
    Parse natural text logging statements (e.g., '200g chicken breast and a banana')
    and resolve against database FoodItems to calculate macro targets.
    """
    # Split items by conjunctions/punctuation
    parts = re.split(r'\b(?:and|with|plus|,)\b', text, flags=re.IGNORECASE)
    results = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        quantity = 100.0 # default weight in grams
        food_query = ""

        # Match "200g chicken breast"
        match = QUANTITY_PATTERN.search(part)
        if match:
            q_str = match.group("quantity")
            unit = match.group("unit") or "g"
            food_query = match.group("food").strip()
            
            val = float(q_str)
            if unit.lower() in ["g", "grams"]:
                quantity = val
            elif unit.lower() == "oz":
                quantity = val * 28.35
            elif unit.lower() in ["cups", "cup", "pieces", "piece", "scoops", "scoop", "slices", "slice"]:
                quantity = val * 120.0  # estimate average weight per piece/cup
        else:
            # Match "a banana"
            match_art = ARTICLE_PATTERN.search(part)
            if match_art:
                food_query = match_art.group("food").strip()
                quantity = 120.0 # estimate standard piece weight
            else:
                food_query = part

        if not food_query:
            continue

        # Look up match in database
        food_item = db.query(FoodItem).filter(
            FoodItem.name.ilike(f"%{food_query}%")
        ).first()

        if food_item:
            factor = quantity / 100.0
            results.append({
                "matched": True,
                "food_name": food_item.name,
                "logged_text": part,
                "weight_g": quantity,
                "calories": round(food_item.calories * factor, 1),
                "protein": round(food_item.protein * factor, 1),
                "carbs": round(food_item.carbs * factor, 1),
                "fats": round(food_item.fats * factor, 1)
            })
        else:
            # Fallback for unrecognized items
            results.append({
                "matched": False,
                "food_name": food_query,
                "logged_text": part,
                "weight_g": quantity,
                "calories": round(1.2 * quantity, 1),
                "protein": round(0.08 * quantity, 1),
                "carbs": round(0.15 * quantity, 1),
                "fats": round(0.03 * quantity, 1)
            })

    return results
