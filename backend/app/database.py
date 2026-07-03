
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")
TRAINING_DATABASE_URL = os.getenv("TRAINING_DATABASE_URL", DATABASE_URL)


def _sqlite_engine(database_url: str):
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        if db_path and db_path != ":memory:":
            Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            # Run self-contained sqlite database migration
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # User columns
                for col in ["menopause_mode", "pregnancy_mode", "local_only"]:
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col} BOOLEAN DEFAULT 0")
                    except sqlite3.OperationalError:
                        pass
                    try:
                        cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} BOOLEAN DEFAULT 0")
                    except sqlite3.OperationalError:
                        pass
                # Menstrual columns
                for col in ["encrypted_symptoms", "encrypted_mood", "encrypted_flow_intensity", "encrypted_notes"]:
                    try:
                        cursor.execute(f"ALTER TABLE menstrual_cycle_logs ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError:
                        pass
                conn.commit()
                conn.close()
            except Exception as migration_err:
                print(f"[Migration] Auto schema migration warning: {migration_err}")
    return create_engine(database_url, connect_args={"check_same_thread": False})


try:
    if DATABASE_URL.startswith("postgresql"):
        from .neon_config import get_connection_manager
        connection_manager = get_connection_manager()
        engine = connection_manager.engine
        SessionLocal = connection_manager.session_factory
        if TRAINING_DATABASE_URL != DATABASE_URL:
            training_engine = create_engine(TRAINING_DATABASE_URL)
            TrainingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=training_engine)
        else:
            TrainingSessionLocal = SessionLocal
    else:
        engine = _sqlite_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        if TRAINING_DATABASE_URL != DATABASE_URL:
            training_engine = _sqlite_engine(TRAINING_DATABASE_URL)
            TrainingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=training_engine)
        else:
            TrainingSessionLocal = SessionLocal
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}), falling back to SQLite")
    fallback_url = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./smarty_neural_core.db")
    engine = _sqlite_engine(fallback_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    TrainingSessionLocal = SessionLocal

Base = declarative_base()

def get_db():
    """Get database session with proper cleanup"""
    if DATABASE_URL.startswith("postgresql"):
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

def get_training_db():
    """Get session for the training data branch"""
    db = TrainingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_nutrition_database():
    """Seed food categories and items (supporting custom foods.json seed if present)"""
    import json
    from . import models
    db = SessionLocal()
    try:
        if db.query(models.FoodCategory).first():
            db.close()
            return

        categories = [
            {"name": "Fruits", "description": "Fresh and dried fruits"},
            {"name": "Vegetables", "description": "Fresh vegetables and greens"},
            {"name": "Proteins", "description": "Meat, fish, eggs, and plant proteins"},
            {"name": "Dairy", "description": "Milk, cheese, yogurt, and alternatives"},
            {"name": "Grains", "description": "Rice, pasta, bread, and cereals"},
            {"name": "Nuts & Seeds", "description": "Tree nuts, seeds, and butters"},
            {"name": "Beverages", "description": "Drinks, smoothies, and shakes"},
            {"name": "Snacks", "description": "Healthy snacks and treats"},
        ]
        for cat in categories:
            db.add(models.FoodCategory(**cat))
        db.commit()

        # Load category mappings
        cat_map = {c.name: c.id for c in db.query(models.FoodCategory).all()}

        # Check for custom foods.json seed file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        foods_json_path = os.path.join(base_dir, "seed_data", "foods.json")
        
        foods = []
        if os.path.exists(foods_json_path) and os.path.getsize(foods_json_path) > 100:
            with open(foods_json_path, "r", encoding="utf-8") as f:
                custom_foods = json.load(f)
                for item in custom_foods:
                    cat_id = cat_map.get(item.get("category_name"))
                    if cat_id:
                        foods.append({
                            "category_id": cat_id,
                            "name": item["name"],
                            "calories": item["calories"],
                            "protein": item["protein"],
                            "carbs": item["carbs"],
                            "fats": item["fats"],
                            "recommended_for_goal": item["recommended_for_goal"]
                        })
        
        if not foods:
            # Fallback to default lists
            fruit_cat = cat_map.get("Fruits")
            veg_cat = cat_map.get("Vegetables")
            protein_cat = cat_map.get("Proteins")
            dairy_cat = cat_map.get("Dairy")
            grain_cat = cat_map.get("Grains")
            nut_cat = cat_map.get("Nuts & Seeds")
            bev_cat = cat_map.get("Beverages")
            snack_cat = cat_map.get("Snacks")
            
            foods = [
                {"category_id": fruit_cat, "name": "Apple", "calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2, "recommended_for_goal": "maintenance"},
                {"category_id": fruit_cat, "name": "Banana", "calories": 89, "protein": 1.1, "carbs": 23, "fats": 0.3, "recommended_for_goal": "muscle_gain"},
                {"category_id": fruit_cat, "name": "Blueberries", "calories": 57, "protein": 0.7, "carbs": 14, "fats": 0.3, "recommended_for_goal": "fat_loss"},
                {"category_id": fruit_cat, "name": "Orange", "calories": 47, "protein": 0.9, "carbs": 12, "fats": 0.1, "recommended_for_goal": "maintenance"},
                {"category_id": veg_cat, "name": "Broccoli", "calories": 34, "protein": 2.8, "carbs": 7, "fats": 0.4, "recommended_for_goal": "fat_loss"},
                {"category_id": veg_cat, "name": "Spinach", "calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "recommended_for_goal": "fat_loss"},
                {"category_id": veg_cat, "name": "Sweet Potato", "calories": 86, "protein": 1.6, "carbs": 20, "fats": 0.1, "recommended_for_goal": "muscle_gain"},
                {"category_id": veg_cat, "name": "Kale", "calories": 49, "protein": 4.3, "carbs": 9, "fats": 0.9, "recommended_for_goal": "fat_loss"},
                {"category_id": protein_cat, "name": "Chicken Breast", "calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "recommended_for_goal": "muscle_gain"},
                {"category_id": protein_cat, "name": "Salmon", "calories": 208, "protein": 20, "carbs": 0, "fats": 13, "recommended_for_goal": "muscle_gain"},
                {"category_id": protein_cat, "name": "Eggs", "calories": 155, "protein": 13, "carbs": 1.1, "fats": 11, "recommended_for_goal": "muscle_gain"},
                {"category_id": protein_cat, "name": "Tofu", "calories": 76, "protein": 8, "carbs": 1.9, "fats": 4.8, "recommended_for_goal": "fat_loss"},
                {"category_id": protein_cat, "name": "Lean Ground Beef", "calories": 250, "protein": 26, "carbs": 0, "fats": 15, "recommended_for_goal": "muscle_gain"},
                {"category_id": dairy_cat, "name": "Greek Yogurt", "calories": 59, "protein": 10, "carbs": 3.6, "fats": 0.7, "recommended_for_goal": "muscle_gain"},
                {"category_id": dairy_cat, "name": "Whole Milk", "calories": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3, "recommended_for_goal": "muscle_gain"},
                {"category_id": dairy_cat, "name": "Cottage Cheese", "calories": 98, "protein": 11, "carbs": 3.4, "fats": 4.3, "recommended_for_goal": "fat_loss"},
                {"category_id": grain_cat, "name": "Brown Rice", "calories": 111, "protein": 2.6, "carbs": 23, "fats": 0.9, "recommended_for_goal": "muscle_gain"},
                {"category_id": grain_cat, "name": "Oats", "calories": 389, "protein": 16.9, "carbs": 66, "fats": 6.9, "recommended_for_goal": "muscle_gain"},
                {"category_id": grain_cat, "name": "Quinoa", "calories": 120, "protein": 4.4, "carbs": 21, "fats": 1.9, "recommended_for_goal": "fat_loss"},
                {"category_id": nut_cat, "name": "Almonds", "calories": 579, "protein": 21, "carbs": 22, "fats": 50, "recommended_for_goal": "muscle_gain"},
                {"category_id": nut_cat, "name": "Peanut Butter", "calories": 588, "protein": 25, "carbs": 20, "fats": 50, "recommended_for_goal": "muscle_gain"},
                {"category_id": nut_cat, "name": "Chia Seeds", "calories": 486, "protein": 17, "carbs": 42, "fats": 31, "recommended_for_goal": "fat_loss"},
                {"category_id": bev_cat, "name": "Whey Protein Shake", "calories": 120, "protein": 24, "carbs": 3, "fats": 1.5, "recommended_for_goal": "muscle_gain"},
                {"category_id": bev_cat, "name": "Black Coffee", "calories": 2, "protein": 0.3, "carbs": 0, "fats": 0, "recommended_for_goal": "fat_loss"},
                {"category_id": snack_cat, "name": "Dark Chocolate", "calories": 546, "protein": 4.9, "carbs": 61, "fats": 31, "recommended_for_goal": "maintenance"},
                {"category_id": snack_cat, "name": "Rice Cakes", "calories": 35, "protein": 0.8, "carbs": 7.3, "fats": 0.3, "recommended_for_goal": "fat_loss"},
            ]
            
        for food in foods:
            db.add(models.FoodItem(**food))
        db.commit()
        print(f"[OK] Nutrition database seeded with {len(foods)} food items.")
    except Exception as e:
        print(f"Error seeding nutrition database: {e}")
        db.rollback()
    finally:
        db.close()


def seed_exercise_database():
    """Injects a comprehensive exercise library tagged by fitness_goal from JSON seed data.

    Uses wger-sourced data (8 real categories) when available, otherwise falls
    back to a minimal hardcoded set.  If the DB was previously seeded with the
    old 4-category schema but wger data now exists, the exercises are re-seeded
    automatically.
    """
    import json
    from . import models
    from .generate_seed_data import generate_exercises_json

    db = SessionLocal()
    try:
        # wger categories (matches real wger data)
        wger_categories = [
            {"name": "Abs", "description": "Core and abdominal exercises."},
            {"name": "Arms", "description": "Bicep, tricep, and forearm exercises."},
            {"name": "Back", "description": "Lat, trap, and posterior chain exercises."},
            {"name": "Calves", "description": "Calf raise and lower-leg exercises."},
            {"name": "Cardio", "description": "Cardiovascular and conditioning exercises."},
            {"name": "Chest", "description": "Pectoral press and fly exercises."},
            {"name": "Legs", "description": "Quadricep, hamstring, and glute exercises."},
            {"name": "Shoulders", "description": "Deltoid press and raise exercises."},
        ]

        # Detect if we need to re-seed (old synthetic categories → new wger categories)
        existing_count = db.query(models.ExerciseItem).count()
        has_wger_cats = db.query(models.ExerciseCategory).filter_by(name="Abs").first() is not None
        json_path = generate_exercises_json()
        is_wger_source = "wger" in json_path

        if existing_count > 0 and has_wger_cats and not is_wger_source:
            # Already seeded with wger categories, skip
            db.close()
            return
        elif existing_count > 0 and not has_wger_cats and is_wger_source:
            # Old schema but new wger data available — re-seed
            logger.info("Detected category schema change. Re-seeding exercises with wger data …")
            db.query(models.ExerciseItem).delete()
            db.query(models.ExerciseCategory).delete()
            db.commit()
        elif existing_count > 0:
            # Already seeded, no schema change needed
            db.close()
            return

        # Ensure categories exist
        for cat in wger_categories:
            if not db.query(models.ExerciseCategory).filter_by(name=cat["name"]).first():
                db.add(models.ExerciseCategory(**cat))
        db.commit()

        # Load category mappings
        cat_map = {c.name: c.id for c in db.query(models.ExerciseCategory).all()}

        # Load exercise JSON
        with open(json_path, "r", encoding="utf-8") as f:
            exercises_data = json.load(f)

        exercise_objects = []
        for ex in exercises_data:
            cat_id = cat_map.get(ex["category_name"])
            if cat_id:
                exercise_objects.append(models.ExerciseItem(
                    category_id=cat_id,
                    name=ex["name"],
                    targeted_muscle=ex["targeted_muscle"],
                    difficulty=ex["difficulty"],
                    equipment=ex["equipment"],
                    calories_per_min=ex["calories_per_min"],
                    fitness_goal=ex["fitness_goal"],
                    description=ex.get("description", "")
                ))

        db.bulk_save_objects(exercise_objects)
        db.commit()
        source_label = "wger API" if is_wger_source else "fallback"
        print(f"[OK] Exercise database seeded with {len(exercise_objects)} exercises ({source_label}).")

        # Seed Specialized Female Exercises
        existing_female_count = db.query(models.FemaleExerciseItem).count()
        if existing_female_count == 0:
            print("Seeding specialized cycle-synced female exercises...")
            female_exercises = [
                # Menstrual Phase (Low intensity, recovery, gentle)
                {
                    "category_name": "Cardio",
                    "name": "Restorative Yoga Flow",
                    "targeted_muscle": "Full Body",
                    "difficulty": "Beginner",
                    "equipment": "Mat",
                    "calories_per_min": 3.2,
                    "suitable_cycle_phase": "Menstrual",
                    "description": "Gentle, restorative yoga postures designed to relieve menstrual cramping, open the hips, and calm the nervous system."
                },
                {
                    "category_name": "Cardio",
                    "name": "Slow Pelvic Floor Stretches",
                    "targeted_muscle": "Pelvic Floor",
                    "difficulty": "Beginner",
                    "equipment": "Mat",
                    "calories_per_min": 2.5,
                    "suitable_cycle_phase": "Menstrual",
                    "description": "Slow, ACOG-aligned breathing and deep stretching targeting pelvic stability, relieving lower back aches."
                },
                
                # Follicular Phase (Energy rising, progressive overload, building strength)
                {
                    "category_name": "Legs",
                    "name": "Progressive Kettlebell Deadlifts",
                    "targeted_muscle": "Glutes & Hamstrings",
                    "difficulty": "Intermediate",
                    "equipment": "Kettlebell",
                    "calories_per_min": 7.5,
                    "suitable_cycle_phase": "Follicular",
                    "description": "Focusing on strength development and glute activation during the follicular peak when estrogen supports hypertrophic growth."
                },
                {
                    "category_name": "Abs",
                    "name": "Pilates Core Alignment",
                    "targeted_muscle": "Abs",
                    "difficulty": "Intermediate",
                    "equipment": "Mat",
                    "calories_per_min": 5.0,
                    "suitable_cycle_phase": "Follicular",
                    "description": "Core-strengthening Pilates flow, building abdominal strength and pelvic alignment."
                },
                
                # Ovulatory Phase (High testosterone/estrogen, peak output)
                {
                    "category_name": "Cardio",
                    "name": "High-Intensity Interval Training (HIIT)",
                    "targeted_muscle": "Full Body",
                    "difficulty": "Advanced",
                    "equipment": "None",
                    "calories_per_min": 12.5,
                    "suitable_cycle_phase": "Ovulatory",
                    "description": "Explosive intervals leveraging peak energy, maximum strength capacity, and optimal insulin sensitivity."
                },
                {
                    "category_name": "Legs",
                    "name": "Barbell Squats (Peak Load)",
                    "targeted_muscle": "Quadriceps",
                    "difficulty": "Advanced",
                    "equipment": "Barbell",
                    "calories_per_min": 10.0,
                    "suitable_cycle_phase": "Ovulatory",
                    "description": "Heavy squats capitalizing on your peak strength levels during ovulation. Go for progressive overload."
                },
                
                # Luteal Phase (Endurance, steady-state movement)
                {
                    "category_name": "Cardio",
                    "name": "Steady-State Aerobic Jogging",
                    "targeted_muscle": "Legs",
                    "difficulty": "Intermediate",
                    "equipment": "None",
                    "calories_per_min": 8.0,
                    "suitable_cycle_phase": "Luteal",
                    "description": "Low-to-moderate steady jogging. Fits perfectly with high luteal body temperatures and fat oxidation rates."
                },
                {
                    "category_name": "Arms",
                    "name": "Moderate Resistance Arm Sculpting",
                    "targeted_muscle": "Arms",
                    "difficulty": "Beginner",
                    "equipment": "Dumbbells",
                    "calories_per_min": 4.5,
                    "suitable_cycle_phase": "Luteal",
                    "description": "Moderate dumbbell circuits for arm preservation and endurance, avoiding high central nervous system fatigue."
                }
            ]
            
            female_objects = []
            for item in female_exercises:
                cat_id = cat_map.get(item["category_name"])
                if cat_id:
                    female_objects.append(models.FemaleExerciseItem(
                        category_id=cat_id,
                        name=item["name"],
                        targeted_muscle=item["targeted_muscle"],
                        difficulty=item["difficulty"],
                        equipment=item["equipment"],
                        calories_per_min=item["calories_per_min"],
                        suitable_cycle_phase=item["suitable_cycle_phase"],
                        description=item["description"]
                    ))
            db.bulk_save_objects(female_objects)
            db.commit()
            print(f"[OK] Seeded {len(female_objects)} cycle-synced female exercises successfully.")
            
    except Exception as e:
        print(f"Error seeding exercise database: {e}")
        db.rollback()
    finally:
        db.close()

