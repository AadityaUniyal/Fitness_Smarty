import pytest
pytest.importorskip("numpy")
from app.database import SessionLocal
from app.recommendation_engine import RecommendationEngine

def test_foods_by_aim():
    db = SessionLocal()
    engine = RecommendationEngine(db)
    
    print("Testing 'muscle_gain' and 'all' muscles:")
    foods = engine.recommend_foods_by_goal_and_muscle("muscle_gain", "all", 5)
    for f in foods:
        print(f" - {f.name} (Protein: {f.protein}g, Cals: {f.calories}) [Target: {f.target_muscle_group}, Goal: {f.recommended_for_goal}]")
        
    print("\nTesting 'weight_loss' and 'abs':")
    foods = engine.recommend_foods_by_goal_and_muscle("weight_loss", "abs", 5)
    for f in foods:
        print(f" - {f.name} (Protein: {f.protein}g, Cals: {f.calories}) [Target: {f.target_muscle_group}, Goal: {f.recommended_for_goal}]")
        
    db.close()

if __name__ == "__main__":
    test_foods_by_aim()
