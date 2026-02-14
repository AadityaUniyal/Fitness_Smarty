
from sqlalchemy.orm import Session
from . import db_models

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

def get_nutritional_summary(items: list):
    """Calculates total macros for a set of items."""
    return {
        "total_calories": sum(item.calories for item in items),
        "total_protein": sum(item.protein for item in items),
        "total_carbs": sum(item.carbs for item in items),
        "total_fats": sum(item.fats for item in items),
    }
