import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from app.food_service import FoodSearchEngine
from app.models import FoodItem as Food

Base = declarative_base()


def test_food_search_engine():
    engine = create_engine("sqlite:///:memory:")
    # We will temporarily use the TempFood model structure compatible with models.FoodItem
    # Create tables
    models_metadata = Food.__table__.metadata
    models_metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Seed food items
    f1 = Food(id=1, name="Grilled Chicken Breast", calories=165.0, protein=31.0, carbs=0.0, fats=3.6)
    f2 = Food(id=2, name="White Long Grain Rice", calories=130.0, protein=2.7, carbs=28.0, fats=0.3)
    f3 = Food(id=3, name="Apple Red Delicious", calories=52.0, protein=0.3, carbs=14.0, fats=0.2)
    
    db.add_all([f1, f2, f3])
    db.commit()
    
    search_engine = FoodSearchEngine(db)
    
    # 1. Exact/LIKE search test
    exact_res = search_engine.exact_search("Chicken")
    assert len(exact_res) == 1
    assert exact_res[0].name == "Grilled Chicken Breast"
    
    # 2. Fuzzy search test
    fuzzy_res = search_engine.fuzzy_search("Chiken") # Typo in Chicken
    assert len(fuzzy_res) > 0
    assert fuzzy_res[0][0].name == "Grilled Chicken Breast"
    assert fuzzy_res[0][1] > 60
