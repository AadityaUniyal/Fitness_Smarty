
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .neon_config import NeonConfig, ConnectionManager, get_connection_manager

# Use enhanced connection management for Neon PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")

if "postgresql" in DATABASE_URL:
    # Use enhanced Neon connection management
    connection_manager = get_connection_manager()
    engine = connection_manager.engine
    SessionLocal = connection_manager.session_factory
else:
    # Fallback to SQLite for development
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Get database session with proper cleanup"""
    if "postgresql" in DATABASE_URL:
        # Use enhanced connection manager
        from .neon_config import get_database_session
        yield from get_database_session()
    else:
        # SQLite fallback
        db = SessionLocal()
        try: 
            yield db
        finally: 
            db.close()

def seed_exercise_database():
    """Injects a massive library of Kinetic Nodes (Exercises)."""
    from . import db_models as models
    db = SessionLocal()
    if db.query(models.ExerciseCategory).first():
        db.close()
        return

    categories = [
        {"name": "Power & Strength", "description": "High-intensity output for myofibrillar hypertrophy."},
        {"name": "Hypertrophy Nodes", "description": "Volume-based training for sarcoplasmic expansion."},
        {"name": "Metabolic Engine", "description": "Cardiovascular protocols for maximized thermal burn."},
        {"name": "Neural Mobility", "description": "Kinetic stretching and joint synchronization."}
    ]
    for cat in categories:
        db.add(models.ExerciseCategory(**cat))
    db.commit()

    str_cat = db.query(models.ExerciseCategory).filter_by(name="Power & Strength").first().id
    hyp_cat = db.query(models.ExerciseCategory).filter_by(name="Hypertrophy Nodes").first().id
    met_cat = db.query(models.ExerciseCategory).filter_by(name="Metabolic Engine").first().id
    mob_cat = db.query(models.ExerciseCategory).filter_by(name="Neural Mobility").first().id

    exercises = [
        # Strength
        {"category_id": str_cat, "name": "Barbell Squat", "targeted_muscle": "Quadriceps/Glutes", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 12.0},
        {"category_id": str_cat, "name": "Deadlift", "targeted_muscle": "Postural Chain", "difficulty": "Advanced", "equipment": "Barbell", "calories_per_min": 15.0},
        {"category_id": str_cat, "name": "Bench Press", "targeted_muscle": "Pectorals", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 8.0},
        {"category_id": str_cat, "name": "Overhead Press", "targeted_muscle": "Deltoids", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 7.5},
        
        # Hypertrophy
        {"category_id": hyp_cat, "name": "Dumbbell Lateral Raise", "targeted_muscle": "Lateral Deltoids", "difficulty": "Beginner", "equipment": "Dumbbells", "calories_per_min": 4.0},
        {"category_id": hyp_cat, "name": "Cable Chest Fly", "targeted_muscle": "Inner Pectorals", "difficulty": "Intermediate", "equipment": "Cables", "calories_per_min": 5.0},
        {"category_id": hyp_cat, "name": "Leg Extension", "targeted_muscle": "Quadriceps", "difficulty": "Beginner", "equipment": "Machine", "calories_per_min": 4.5},
        {"category_id": hyp_cat, "name": "Bicep Preacher Curl", "targeted_muscle": "Biceps", "difficulty": "Beginner", "equipment": "EZ Bar", "calories_per_min": 3.5},
        {"category_id": hyp_cat, "name": "Hammer Curls", "targeted_muscle": "Brachialis", "difficulty": "Beginner", "equipment": "Dumbbells", "calories_per_min": 3.5},

        # Metabolic
        {"category_id": met_cat, "name": "Battle Ropes", "targeted_muscle": "Full Body", "difficulty": "Intermediate", "equipment": "Ropes", "calories_per_min": 18.0},
        {"category_id": met_cat, "name": "Assault Bike Sprint", "targeted_muscle": "Full Body", "difficulty": "Advanced", "equipment": "Fan Bike", "calories_per_min": 25.0},
        {"category_id": met_cat, "name": "Burpees", "targeted_muscle": "Full Body", "difficulty": "Intermediate", "equipment": "Bodyweight", "calories_per_min": 14.0},
        {"category_id": met_cat, "name": "Mountain Climbers", "targeted_muscle": "Core/Shoulders", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 10.0},

        # Mobility
        {"category_id": mob_cat, "name": "Worlds Greatest Stretch", "targeted_muscle": "Full Kinetic Chain", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 3.0},
        {"category_id": mob_cat, "name": "Cat-Cow Protocol", "targeted_muscle": "Spine/Core", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 2.0},
        {"category_id": mob_cat, "name": "Pigeon Stretch", "targeted_muscle": "Glutes/Hips", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 1.5}
    ]
    for ex in exercises:
        db.add(models.ExerciseItem(**ex, description="Standard neural-calibrated movement."))
    db.commit()
    db.close()

def seed_nutrition_database():
    """Injects a Comprehensive Biofuel Library (Food) for AI analysis."""
    from . import db_models as models
    db = SessionLocal()
    if db.query(models.FoodCategory).first():
        db.close()
        return

    categories = [
        {"name": "Neural Proteins", "description": "High-bioavailability amino acids for recovery."},
        {"name": "Kinetic Carbs", "description": "Complex glycogen nodes for energy performance."},
        {"name": "Essential Lipids", "description": "Hormonal optimization and brain health fats."},
        {"name": "Micro-Nodes", "description": "High density vitamins and essential minerals."},
        {"name": "Recovery Shakes", "description": "Rapid-absorption post-session synchronization fluids."},
        {"name": "Cheat Loops", "description": "Metabolic stressors (use in controlled windows)."}
    ]
    for cat in categories:
        db.add(models.FoodCategory(**cat))
    db.commit()

    prot_id = db.query(models.FoodCategory).filter_by(name="Neural Proteins").first().id
    carb_id = db.query(models.FoodCategory).filter_by(name="Kinetic Carbs").first().id
    fat_id = db.query(models.FoodCategory).filter_by(name="Essential Lipids").first().id
    micr_id = db.query(models.FoodCategory).filter_by(name="Micro-Nodes").first().id
    shak_id = db.query(models.FoodCategory).filter_by(name="Recovery Shakes").first().id
    chea_id = db.query(models.FoodCategory).filter_by(name="Cheat Loops").first().id

    foods = [
        # Neural Proteins (Approx per 100g)
        {"category_id": prot_id, "name": "Bison Steak", "calories": 143, "protein": 28.0, "carbs": 0.0, "fats": 2.4, "is_elite": True},
        {"category_id": prot_id, "name": "Chicken Breast", "calories": 165, "protein": 31.0, "carbs": 0.0, "fats": 3.6, "is_elite": True},
        {"category_id": prot_id, "name": "Egg Whites (Liquid)", "calories": 52, "protein": 11.0, "carbs": 1.0, "fats": 0.2, "is_elite": True},
        {"category_id": prot_id, "name": "Cod Fillet", "calories": 82, "protein": 18.0, "carbs": 0.0, "fats": 0.7, "is_elite": True},
        {"category_id": prot_id, "name": "Salmon (Wild)", "calories": 208, "protein": 22.0, "carbs": 0.0, "fats": 13.0, "is_elite": True},
        {"category_id": prot_id, "name": "Greek Yogurt (0%)", "calories": 59, "protein": 10.0, "carbs": 3.6, "fats": 0.4, "is_elite": True},
        {"category_id": prot_id, "name": "Turkey Breast", "calories": 135, "protein": 30.0, "carbs": 0.0, "fats": 1.0, "is_elite": False},
        {"category_id": prot_id, "name": "Lean Ground Beef (95%)", "calories": 137, "protein": 21.4, "carbs": 0.0, "fats": 5.0, "is_elite": False},
        {"category_id": prot_id, "name": "Tofu (Firm)", "calories": 83, "protein": 10.0, "carbs": 1.0, "fats": 5.0, "is_elite": True},
        {"category_id": prot_id, "name": "Tempeh", "calories": 192, "protein": 19.0, "carbs": 9.0, "fats": 11.0, "is_elite": True},
        {"category_id": prot_id, "name": "Seitan", "calories": 104, "protein": 21.0, "carbs": 4.0, "fats": 0.6, "is_elite": False},
        {"category_id": prot_id, "name": "Cottage Cheese", "calories": 98, "protein": 11.0, "carbs": 3.4, "fats": 4.3, "is_elite": False},
        {"category_id": prot_id, "name": "Lentils", "calories": 116, "protein": 9.0, "carbs": 20.0, "fats": 0.4, "is_elite": True},

        # Kinetic Carbs (Approx per 100g cooked)
        {"category_id": carb_id, "name": "Jasmin Rice", "calories": 130, "protein": 2.7, "carbs": 28.0, "fats": 0.3, "is_elite": True},
        {"category_id": carb_id, "name": "Sweet Potato", "calories": 86, "protein": 1.6, "carbs": 20.0, "fats": 0.1, "is_elite": True},
        {"category_id": carb_id, "name": "Quinoa", "calories": 120, "protein": 4.4, "carbs": 21.0, "fats": 1.9, "is_elite": True},
        {"category_id": carb_id, "name": "Oatmeal", "calories": 68, "protein": 2.4, "carbs": 12.0, "fats": 1.4, "is_elite": True},
        {"category_id": carb_id, "name": "Brown Rice", "calories": 112, "protein": 2.3, "carbs": 24.0, "fats": 0.8, "is_elite": False},
        {"category_id": carb_id, "name": "Blueberries", "calories": 57, "protein": 0.7, "carbs": 14.0, "fats": 0.3, "is_elite": True},
        {"category_id": carb_id, "name": "Banana Node", "calories": 89, "protein": 1.1, "carbs": 23.0, "fats": 0.3, "is_elite": True},
        {"category_id": carb_id, "name": "White Potato", "calories": 77, "protein": 2.0, "carbs": 17.0, "fats": 0.1, "is_elite": False},
        {"category_id": carb_id, "name": "Whole Wheat Pasta", "calories": 124, "protein": 5.3, "carbs": 27.0, "fats": 0.5, "is_elite": False},
        {"category_id": carb_id, "name": "Buckwheat", "calories": 92, "protein": 3.4, "carbs": 20.0, "fats": 0.6, "is_elite": True},
        {"category_id": carb_id, "name": "Chickpeas", "calories": 164, "protein": 8.9, "carbs": 27.0, "fats": 2.6, "is_elite": False},
        {"category_id": carb_id, "name": "Rice Cakes", "calories": 387, "protein": 8.2, "carbs": 82.0, "fats": 2.8, "is_elite": False},

        # Essential Lipids (Approx per 100g)
        {"category_id": fat_id, "name": "MCT Oil", "calories": 900, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "is_elite": True},
        {"category_id": fat_id, "name": "Extra Virgin Olive Oil", "calories": 884, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "is_elite": True},
        {"category_id": fat_id, "name": "Avocado", "calories": 160, "protein": 2.0, "carbs": 8.5, "fats": 14.7, "is_elite": True},
        {"category_id": fat_id, "name": "Brazil Nuts", "calories": 656, "protein": 14.0, "carbs": 12.0, "fats": 66.0, "is_elite": True},
        {"category_id": fat_id, "name": "Almond Butter", "calories": 614, "protein": 21.0, "carbs": 19.0, "fats": 55.0, "is_elite": False},
        {"category_id": fat_id, "name": "Walnuts", "calories": 654, "protein": 15.2, "carbs": 13.7, "fats": 65.2, "is_elite": True},
        {"category_id": fat_id, "name": "Chia Seeds", "calories": 486, "protein": 16.5, "carbs": 42.1, "fats": 30.7, "is_elite": True},
        {"category_id": fat_id, "name": "Flax Seeds", "calories": 534, "protein": 18.3, "carbs": 28.9, "fats": 42.2, "is_elite": False},
        {"category_id": fat_id, "name": "Macadamia Nuts", "calories": 718, "protein": 7.9, "carbs": 13.8, "fats": 75.8, "is_elite": False},
        {"category_id": fat_id, "name": "Egg Yolk", "calories": 322, "protein": 15.9, "carbs": 3.6, "fats": 26.5, "is_elite": True},

        # Micro-Nodes (Approx per 100g)
        {"category_id": micr_id, "name": "Asparagus Spears", "calories": 20, "protein": 2.2, "carbs": 3.7, "fats": 0.1, "is_elite": True},
        {"category_id": micr_id, "name": "Brussels Sprouts", "calories": 43, "protein": 3.4, "carbs": 9.0, "fats": 0.3, "is_elite": True},
        {"category_id": micr_id, "name": "Bell Pepper Array", "calories": 31, "protein": 1.0, "carbs": 6.0, "fats": 0.3, "is_elite": True},
        {"category_id": micr_id, "name": "Spinach", "calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "is_elite": True},
        {"category_id": micr_id, "name": "Broccoli", "calories": 34, "protein": 2.8, "carbs": 6.6, "fats": 0.4, "is_elite": True},
        {"category_id": micr_id, "name": "Kale", "calories": 49, "protein": 4.3, "carbs": 8.8, "fats": 0.9, "is_elite": True},
        {"category_id": micr_id, "name": "Zucchini", "calories": 17, "protein": 1.2, "carbs": 3.1, "fats": 0.3, "is_elite": False},
        {"category_id": micr_id, "name": "Garlic Node", "calories": 149, "protein": 6.4, "carbs": 33.1, "fats": 0.5, "is_elite": True},
        {"category_id": micr_id, "name": "Ginger Root", "calories": 80, "protein": 1.8, "carbs": 17.8, "fats": 0.8, "is_elite": True},

        # Recovery Shakes (Approx per serving)
        {"category_id": shak_id, "name": "Post-Alpha Whey", "calories": 120, "protein": 24.0, "carbs": 3.0, "fats": 1.5, "is_elite": True},
        {"category_id": shak_id, "name": "Casein Night-Node", "calories": 110, "protein": 25.0, "carbs": 2.0, "fats": 0.5, "is_elite": True},
        {"category_id": shak_id, "name": "Hemp Protein", "calories": 130, "protein": 15.0, "carbs": 11.0, "fats": 3.5, "is_elite": False},
        {"category_id": shak_id, "name": "Electrolyte Matrix", "calories": 10, "protein": 0.0, "carbs": 2.0, "fats": 0.0, "is_elite": True},
        {"category_id": shak_id, "name": "Collagen Peptide", "calories": 70, "protein": 18.0, "carbs": 0.0, "fats": 0.0, "is_elite": False},

        # Cheat Loops (Approx per serving)
        {"category_id": chea_id, "name": "Glycerol Glazed Donut", "calories": 450, "protein": 4.0, "carbs": 60.0, "fats": 22.0, "is_elite": False},
        {"category_id": chea_id, "name": "Double Neural Burger", "calories": 890, "protein": 45.0, "carbs": 50.0, "fats": 55.0, "is_elite": False},
        {"category_id": chea_id, "name": "Pepperoni Pizza Slice", "calories": 285, "protein": 12.0, "carbs": 36.0, "fats": 10.0, "is_elite": False},
        {"category_id": chea_id, "name": "French Fries (Large)", "calories": 510, "protein": 6.0, "carbs": 66.0, "fats": 24.0, "is_elite": False},
        {"category_id": chea_id, "name": "Dark Chocolate (85%)", "calories": 598, "protein": 7.8, "carbs": 45.9, "fats": 42.6, "is_elite": True}
    ]
    for f in foods:
        db.add(models.FoodItem(**f))
    db.commit()
    db.close()
    print("BIOFUEL ASSET LIBRARIES SYNCHRONIZED.")
