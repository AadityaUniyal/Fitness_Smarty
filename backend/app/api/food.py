from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/food", tags=["Food Database"])

@router.get("/library")
def get_food_library(db: Session = Depends(get_db)):
    cats = db.query(models.FoodCategory).all()
    result = []
    for cat in cats:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description or "",
            "items": [{
                "id": f.id,
                "name": f.name,
                "category_id": f.category_id,
                "serving_size": "per 100g",
                "calories": f.calories or 0,
                "protein": f.protein or 0,
                "carbs": f.carbs or 0,
                "fats": f.fats or 0,
                "is_elite": f.is_elite or False
            } for f in cat.foods]
        })
    return result

@router.get("/search")
def search_food(
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.FoodItem)
    if q:
        query = query.filter(models.FoodItem.name.ilike(f"%{q}%"))
    if category_id is not None:
        query = query.filter(models.FoodItem.category_id == category_id)
    foods = query.limit(50).all()
    
    # Fallback to Open Food Facts if search has few results and query is active
    if len(foods) < 3 and q and len(q) > 1:
        try:
            from app.openfoodfacts_service import OpenFoodFactsService
            from app.cache import local_cache
            
            cache_key = f"off_search_{q.strip().lower()}"
            off_results = local_cache.get(cache_key)
            
            if off_results is None:
                service = OpenFoodFactsService()
                off_results = service.search_products(q)
                local_cache.set(cache_key, off_results, ttl_seconds=3600)
                
            if off_results:
                # Find or create Open Food Facts category
                off_cat = db.query(models.FoodCategory).filter(models.FoodCategory.name == "Open Food Facts").first()
                if not off_cat:
                    off_cat = models.FoodCategory(name="Open Food Facts", description="External food products fetched from Open Food Facts")
                    db.add(off_cat)
                    db.commit()
                    db.refresh(off_cat)
                
                # Import new items
                imported_any = False
                for item in off_results:
                    existing = db.query(models.FoodItem).filter(models.FoodItem.name.ilike(item["name"])).first()
                    if not existing:
                        new_food = models.FoodItem(
                            category_id=off_cat.id,
                            name=item["name"],
                            calories=item["calories"],
                            protein=item["protein"],
                            carbs=item["carbs"],
                            fats=item["fats"],
                            is_elite=False,
                            recommended_for_goal="general"
                        )
                        db.add(new_food)
                        imported_any = True
                
                if imported_any:
                    db.commit()
                    # Re-query foods
                    query = db.query(models.FoodItem)
                    if q:
                        query = query.filter(models.FoodItem.name.ilike(f"%{q}%"))
                    if category_id is not None:
                        query = query.filter(models.FoodItem.category_id == category_id)
                    foods = query.limit(50).all()
        except Exception as e:
            # Log and skip fallback on connection errors
            import logging
            logging.getLogger(__name__).warning(f"Failed to fetch Open Food Facts: {e}")
            
    return [{
        "id": f.id,
        "name": f.name,
        "category_id": f.category_id,
        "serving_size": "per 100g",
        "calories": f.calories or 0,
        "protein": f.protein or 0,
        "carbs": f.carbs or 0,
        "fats": f.fats or 0,
        "is_elite": f.is_elite or False
    } for f in foods]

@router.get("/goal/{goal}")
def get_foods_by_goal(goal: str, limit: int = Query(12), db: Session = Depends(get_db)):
    foods = db.query(models.FoodItem).filter(
        models.FoodItem.recommended_for_goal == goal
    ).limit(limit).all()
    return {"foods": [{
        "id": f.id,
        "name": f.name,
        "category": f.category.name if f.category else None,
        "calories": f.calories or 0,
        "protein_g": f.protein or 0,
        "carbs_g": f.carbs or 0,
        "fats_g": f.fats or 0,
        "is_elite": f.is_elite or False
    } for f in foods]}

@router.post("/calculate-portion")
def calculate_portion(
    food_name: str = Body(...),
    quantity_grams: float = Body(100.0),
    db: Session = Depends(get_db)
):
    food = db.query(models.FoodItem).filter(
        models.FoodItem.name.ilike(f"%{food_name}%")
    ).first()
    if not food:
        raise HTTPException(status_code=404, detail=f"Food '{food_name}' not found in database")
    ratio = quantity_grams / 100.0
    return {
        "food_name": food.name,
        "quantity_grams": quantity_grams,
        "calories": round((food.calories or 0) * ratio, 1),
        "protein_g": round((food.protein or 0) * ratio, 1),
        "carbs_g": round((food.carbs or 0) * ratio, 1),
        "fat_g": round((food.fats or 0) * ratio, 1)
    }
