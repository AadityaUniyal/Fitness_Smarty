
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .neon_config import NeonConfig, ConnectionManager, get_connection_manager

# Use enhanced connection management for Neon PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")
TRAINING_DATABASE_URL = os.getenv("TRAINING_DATABASE_URL", DATABASE_URL) # Default to main if not set

if "postgresql" in DATABASE_URL:
    # Use enhanced Neon connection management
    connection_manager = get_connection_manager()
    engine = connection_manager.engine
    SessionLocal = connection_manager.session_factory
    
    # Setup training engine if different
    if TRAINING_DATABASE_URL != DATABASE_URL:
        training_engine = create_engine(TRAINING_DATABASE_URL)
        TrainingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=training_engine)
    else:
        TrainingSessionLocal = SessionLocal

else:
    # Fallback to SQLite for development
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    TrainingSessionLocal = SessionLocal

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

def get_training_db():
    """Get session for the training data branch"""
    db = TrainingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_exercise_database():
    """Injects a comprehensive exercise library tagged by fitness_goal."""
    from . import models
    db = SessionLocal()
    try:
        if db.query(models.ExerciseCategory).first():
            db.close()
            return

        categories = [
            {"name": "Fat Loss Cardio", "description": "High-burn cardio protocols for fat oxidation."},
            {"name": "Muscle Building", "description": "Compound and isolation lifts for hypertrophy."},
            {"name": "Athletic Performance", "description": "Functional and explosive movements for overall athleticism."},
            {"name": "Maintenance & Mobility", "description": "Balanced training for general fitness and recovery."},
        ]
        for cat in categories:
            db.add(models.ExerciseCategory(**cat))
        db.commit()

        fat_cat = db.query(models.ExerciseCategory).filter_by(name="Fat Loss Cardio").first().id
        mus_cat = db.query(models.ExerciseCategory).filter_by(name="Muscle Building").first().id
        ath_cat = db.query(models.ExerciseCategory).filter_by(name="Athletic Performance").first().id
        mob_cat = db.query(models.ExerciseCategory).filter_by(name="Maintenance & Mobility").first().id

        exercises = [
            # ======================== FAT LOSS =========================
            {"category_id": fat_cat, "name": "Burpees", "targeted_muscle": "Full Body", "difficulty": "Intermediate", "equipment": "Bodyweight", "calories_per_min": 14.0, "fitness_goal": "fat_loss", "description": "Explosive full-body movement that spikes heart rate rapidly."},
            {"category_id": fat_cat, "name": "Jump Rope", "targeted_muscle": "Calves/Core", "difficulty": "Beginner", "equipment": "Jump Rope", "calories_per_min": 13.0, "fitness_goal": "fat_loss", "description": "Classic cardio drill for rapid calorie expenditure."},
            {"category_id": fat_cat, "name": "Mountain Climbers", "targeted_muscle": "Core/Shoulders", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 10.0, "fitness_goal": "fat_loss", "description": "Core-intensive cardio interval."},
            {"category_id": fat_cat, "name": "Treadmill Sprint", "targeted_muscle": "Legs/Glutes", "difficulty": "Intermediate", "equipment": "Treadmill", "calories_per_min": 16.0, "fitness_goal": "fat_loss", "description": "High-intensity sprint intervals for fat burning."},
            {"category_id": fat_cat, "name": "Assault Bike Sprint", "targeted_muscle": "Full Body", "difficulty": "Advanced", "equipment": "Fan Bike", "calories_per_min": 25.0, "fitness_goal": "fat_loss", "description": "Max-effort cycling for peak caloric burn."},
            {"category_id": fat_cat, "name": "Battle Ropes", "targeted_muscle": "Shoulders/Core", "difficulty": "Intermediate", "equipment": "Battle Ropes", "calories_per_min": 18.0, "fitness_goal": "fat_loss", "description": "Upper-body cardio with metabolic conditioning."},
            {"category_id": fat_cat, "name": "Jumping Jacks", "targeted_muscle": "Full Body", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 8.0, "fitness_goal": "fat_loss", "description": "Classic warm-up cardio drill."},
            {"category_id": fat_cat, "name": "HIIT Box Jumps", "targeted_muscle": "Quads/Glutes", "difficulty": "Intermediate", "equipment": "Plyo Box", "calories_per_min": 12.0, "fitness_goal": "fat_loss", "description": "Plyometric jumps for power and fat burn."},
            {"category_id": fat_cat, "name": "High Knees", "targeted_muscle": "Core/Hip Flexors", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 9.0, "fitness_goal": "fat_loss", "description": "Running in place with exaggerated knee lift."},
            {"category_id": fat_cat, "name": "Rowing Machine", "targeted_muscle": "Back/Legs", "difficulty": "Intermediate", "equipment": "Rowing Machine", "calories_per_min": 15.0, "fitness_goal": "fat_loss", "description": "Full-body cardio with low joint impact."},
            {"category_id": fat_cat, "name": "Kettlebell Swings", "targeted_muscle": "Posterior Chain", "difficulty": "Intermediate", "equipment": "Kettlebell", "calories_per_min": 13.5, "fitness_goal": "fat_loss", "description": "Hip-hinge movement with high metabolic demand."},
            {"category_id": fat_cat, "name": "Stair Climber", "targeted_muscle": "Glutes/Quads", "difficulty": "Beginner", "equipment": "Stair Machine", "calories_per_min": 11.0, "fitness_goal": "fat_loss", "description": "Low-impact cardio targeting lower body."},

            # ======================== MUSCLE GAIN =======================
            {"category_id": mus_cat, "name": "Barbell Squat", "targeted_muscle": "Quadriceps/Glutes", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 12.0, "fitness_goal": "muscle_gain", "description": "King of all lower body compound lifts."},
            {"category_id": mus_cat, "name": "Deadlift", "targeted_muscle": "Full Posterior Chain", "difficulty": "Advanced", "equipment": "Barbell", "calories_per_min": 15.0, "fitness_goal": "muscle_gain", "description": "Total body strength builder targeting the back, glutes, and hamstrings."},
            {"category_id": mus_cat, "name": "Bench Press", "targeted_muscle": "Pectorals/Triceps", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 8.0, "fitness_goal": "muscle_gain", "description": "Primary upper body horizontal press."},
            {"category_id": mus_cat, "name": "Overhead Press", "targeted_muscle": "Deltoids/Triceps", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 7.5, "fitness_goal": "muscle_gain", "description": "Vertical press for powerful shoulders."},
            {"category_id": mus_cat, "name": "Pull-Ups", "targeted_muscle": "Lats/Biceps", "difficulty": "Intermediate", "equipment": "Bodyweight", "calories_per_min": 9.0, "fitness_goal": "muscle_gain", "description": "Bodyweight vertical pull for back width."},
            {"category_id": mus_cat, "name": "Barbell Row", "targeted_muscle": "Mid Back/Lats", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 8.5, "fitness_goal": "muscle_gain", "description": "Horizontal pull for back thickness."},
            {"category_id": mus_cat, "name": "Incline Dumbbell Press", "targeted_muscle": "Upper Pectorals", "difficulty": "Intermediate", "equipment": "Dumbbells", "calories_per_min": 7.0, "fitness_goal": "muscle_gain", "description": "Targets the upper chest for fuller development."},
            {"category_id": mus_cat, "name": "Romanian Deadlift", "targeted_muscle": "Hamstrings/Glutes", "difficulty": "Intermediate", "equipment": "Barbell", "calories_per_min": 8.0, "fitness_goal": "muscle_gain", "description": "Hip-hinge movement for hamstring isolation."},
            {"category_id": mus_cat, "name": "Leg Press", "targeted_muscle": "Quadriceps", "difficulty": "Beginner", "equipment": "Machine", "calories_per_min": 6.0, "fitness_goal": "muscle_gain", "description": "Machine-based quad development."},
            {"category_id": mus_cat, "name": "Dumbbell Lateral Raise", "targeted_muscle": "Lateral Deltoids", "difficulty": "Beginner", "equipment": "Dumbbells", "calories_per_min": 4.0, "fitness_goal": "muscle_gain", "description": "Isolation work for side delts."},
            {"category_id": mus_cat, "name": "Barbell Bicep Curl", "targeted_muscle": "Biceps", "difficulty": "Beginner", "equipment": "Barbell", "calories_per_min": 3.5, "fitness_goal": "muscle_gain", "description": "Classic bicep builder."},
            {"category_id": mus_cat, "name": "Tricep Rope Pushdown", "targeted_muscle": "Triceps", "difficulty": "Beginner", "equipment": "Cable Machine", "calories_per_min": 3.5, "fitness_goal": "muscle_gain", "description": "Cable isolation for tricep definition."},
            {"category_id": mus_cat, "name": "Cable Chest Fly", "targeted_muscle": "Inner Pectorals", "difficulty": "Intermediate", "equipment": "Cable Machine", "calories_per_min": 5.0, "fitness_goal": "muscle_gain", "description": "Isolation fly for inner chest detail."},
            {"category_id": mus_cat, "name": "Leg Curl Machine", "targeted_muscle": "Hamstrings", "difficulty": "Beginner", "equipment": "Machine", "calories_per_min": 4.0, "fitness_goal": "muscle_gain", "description": "Machine-based hamstring curl."},
            {"category_id": mus_cat, "name": "Calf Raises", "targeted_muscle": "Calves", "difficulty": "Beginner", "equipment": "Machine/Bodyweight", "calories_per_min": 3.0, "fitness_goal": "muscle_gain", "description": "Isolation movement for calf hypertrophy."},
            {"category_id": mus_cat, "name": "Dumbbell Row", "targeted_muscle": "Lats/Rhomboids", "difficulty": "Beginner", "equipment": "Dumbbells", "calories_per_min": 5.5, "fitness_goal": "muscle_gain", "description": "Unilateral back builder."},
            {"category_id": mus_cat, "name": "Face Pulls", "targeted_muscle": "Rear Deltoids/Traps", "difficulty": "Beginner", "equipment": "Cable Machine", "calories_per_min": 4.0, "fitness_goal": "muscle_gain", "description": "Shoulder health and rear delt development."},

            # ======================== ATHLETIC =========================
            {"category_id": ath_cat, "name": "Power Clean", "targeted_muscle": "Full Body", "difficulty": "Advanced", "equipment": "Barbell", "calories_per_min": 16.0, "fitness_goal": "athletic", "description": "Olympic lift for total body explosiveness."},
            {"category_id": ath_cat, "name": "Box Jump", "targeted_muscle": "Quads/Glutes", "difficulty": "Intermediate", "equipment": "Plyo Box", "calories_per_min": 12.0, "fitness_goal": "athletic", "description": "Plyometric movement for lower body power."},
            {"category_id": ath_cat, "name": "Medicine Ball Slam", "targeted_muscle": "Core/Shoulders", "difficulty": "Beginner", "equipment": "Medicine Ball", "calories_per_min": 11.0, "fitness_goal": "athletic", "description": "Explosive core engaged slam pattern."},
            {"category_id": ath_cat, "name": "Farmers Walk", "targeted_muscle": "Traps/Grip/Core", "difficulty": "Beginner", "equipment": "Dumbbells/Kettlebell", "calories_per_min": 8.0, "fitness_goal": "athletic", "description": "Loaded carry for grip and core stability."},
            {"category_id": ath_cat, "name": "Sprint Drills", "targeted_muscle": "Quads/Hamstrings", "difficulty": "Intermediate", "equipment": "Bodyweight", "calories_per_min": 16.0, "fitness_goal": "athletic", "description": "Speed and acceleration training."},
            {"category_id": ath_cat, "name": "Agility Ladder Drills", "targeted_muscle": "Calves/Coordination", "difficulty": "Intermediate", "equipment": "Agility Ladder", "calories_per_min": 10.0, "fitness_goal": "athletic", "description": "Footwork and coordination drills."},
            {"category_id": ath_cat, "name": "Single Leg RDL", "targeted_muscle": "Hamstrings/Glutes/Balance", "difficulty": "Intermediate", "equipment": "Dumbbell", "calories_per_min": 6.0, "fitness_goal": "athletic", "description": "Unilateral hip hinge for balance and posterior chain."},
            {"category_id": ath_cat, "name": "TRX Rows", "targeted_muscle": "Back/Core", "difficulty": "Beginner", "equipment": "TRX", "calories_per_min": 6.5, "fitness_goal": "athletic", "description": "Bodyweight row for functional strength."},
            {"category_id": ath_cat, "name": "Hang Snatch", "targeted_muscle": "Full Body", "difficulty": "Advanced", "equipment": "Barbell", "calories_per_min": 14.0, "fitness_goal": "athletic", "description": "Olympic movement for explosive power."},

            # ======================== MAINTENANCE =====================
            {"category_id": mob_cat, "name": "Walking (Brisk)", "targeted_muscle": "Legs/Core", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 5.0, "fitness_goal": "maintenance", "description": "Low-impact sustained cardio."},
            {"category_id": mob_cat, "name": "Yoga Flow", "targeted_muscle": "Full Kinetic Chain", "difficulty": "Beginner", "equipment": "Yoga Mat", "calories_per_min": 3.0, "fitness_goal": "maintenance", "description": "Flexibility and mindfulness practice."},
            {"category_id": mob_cat, "name": "Swimming Laps", "targeted_muscle": "Full Body", "difficulty": "Intermediate", "equipment": "Pool", "calories_per_min": 11.0, "fitness_goal": "maintenance", "description": "Full body zero-impact cardio."},
            {"category_id": mob_cat, "name": "Bodyweight Squats", "targeted_muscle": "Quads/Glutes", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 5.0, "fitness_goal": "maintenance", "description": "Foundation movement pattern."},
            {"category_id": mob_cat, "name": "Push-Ups", "targeted_muscle": "Chest/Triceps/Core", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 6.0, "fitness_goal": "maintenance", "description": "Classic upper body pushing."},
            {"category_id": mob_cat, "name": "Cat-Cow Stretch", "targeted_muscle": "Spine/Core", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 2.0, "fitness_goal": "maintenance", "description": "Spinal mobility and core activation."},
            {"category_id": mob_cat, "name": "Pigeon Pose", "targeted_muscle": "Glutes/Hips", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 1.5, "fitness_goal": "maintenance", "description": "Deep hip flexor and glute stretch."},
            {"category_id": mob_cat, "name": "Cycling (Moderate)", "targeted_muscle": "Quads/Glutes/Calves", "difficulty": "Beginner", "equipment": "Bicycle", "calories_per_min": 9.0, "fitness_goal": "maintenance", "description": "Sustained aerobic cycling."},
            {"category_id": mob_cat, "name": "Planks", "targeted_muscle": "Core/Shoulders", "difficulty": "Beginner", "equipment": "Bodyweight", "calories_per_min": 4.0, "fitness_goal": "maintenance", "description": "Isometric core stability hold."},
            {"category_id": mob_cat, "name": "Foam Rolling", "targeted_muscle": "Full Body (Recovery)", "difficulty": "Beginner", "equipment": "Foam Roller", "calories_per_min": 2.0, "fitness_goal": "maintenance", "description": "Myofascial release for recovery."},
        ]
        for ex in exercises:
            db.add(models.ExerciseItem(**ex))
        db.commit()
        print(f"✅ Exercise database seeded with {len(exercises)} exercises.")
    except Exception as e:
        print(f"Error seeding exercise database: {e}")
        db.rollback()
    finally:
        db.close()


def seed_nutrition_database():
    """Injects a comprehensive food library with per-100g macros and goal/muscle tags."""
    from . import models
    db = SessionLocal()
    try:
        if db.query(models.FoodCategory).first():
            db.close()
            return

        categories = [
            {"name": "Proteins", "description": "High-protein foods for muscle building and recovery."},
            {"name": "Carbohydrates", "description": "Complex carbs for sustained energy."},
            {"name": "Healthy Fats", "description": "Essential fats for hormones and brain health."},
            {"name": "Vegetables", "description": "Micronutrient-dense low-cal foods."},
            {"name": "Dairy & Eggs", "description": "High-bioavailability proteins and fats."},
            {"name": "Indian Foods", "description": "Common South Asian foods with accurate macros."},
            {"name": "Supplements & Shakes", "description": "Post-workout and protein supplements."},
            {"name": "Treats", "description": "High-calorie indulgent foods (use in moderation)."},
        ]
        for cat in categories:
            db.add(models.FoodCategory(**cat))
        db.commit()

        prot_id = db.query(models.FoodCategory).filter_by(name="Proteins").first().id
        carb_id = db.query(models.FoodCategory).filter_by(name="Carbohydrates").first().id
        fat_id  = db.query(models.FoodCategory).filter_by(name="Healthy Fats").first().id
        veg_id  = db.query(models.FoodCategory).filter_by(name="Vegetables").first().id
        dai_id  = db.query(models.FoodCategory).filter_by(name="Dairy & Eggs").first().id
        ind_id  = db.query(models.FoodCategory).filter_by(name="Indian Foods").first().id
        shk_id  = db.query(models.FoodCategory).filter_by(name="Supplements & Shakes").first().id
        tre_id  = db.query(models.FoodCategory).filter_by(name="Treats").first().id

        # All values are per 100g unless noted
        foods = [
            # ============ PROTEINS ============
            {"category_id": prot_id, "name": "Chicken Breast", "calories": 165, "protein": 31.0, "carbs": 0.0, "fats": 3.6, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Turkey Breast", "calories": 135, "protein": 30.0, "carbs": 0.0, "fats": 1.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Salmon (Wild)", "calories": 208, "protein": 22.0, "carbs": 0.0, "fats": 13.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tuna (canned in water)", "calories": 116, "protein": 26.0, "carbs": 0.0, "fats": 1.0, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Cod Fillet", "calories": 82, "protein": 18.0, "carbs": 0.0, "fats": 0.7, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Shrimp", "calories": 99, "protein": 24.0, "carbs": 0.0, "fats": 0.3, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Lean Ground Beef (95%)", "calories": 137, "protein": 21.4, "carbs": 0.0, "fats": 5.0, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Bison Steak", "calories": 143, "protein": 28.0, "carbs": 0.0, "fats": 2.4, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tofu (Firm)", "calories": 83, "protein": 10.0, "carbs": 1.0, "fats": 5.0, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tempeh", "calories": 192, "protein": 19.0, "carbs": 9.0, "fats": 11.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Lentils (cooked)", "calories": 116, "protein": 9.0, "carbs": 20.0, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Black Beans (cooked)", "calories": 132, "protein": 8.9, "carbs": 24.0, "fats": 0.5, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Cottage Cheese", "calories": 98, "protein": 11.0, "carbs": 3.4, "fats": 4.3, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Pork Tenderloin", "calories": 143, "protein": 26.0, "carbs": 0.0, "fats": 3.5, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Sardines (in water)", "calories": 208, "protein": 25.0, "carbs": 0.0, "fats": 11.5, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},

            # ============ CARBOHYDRATES ============
            {"category_id": carb_id, "name": "White Rice (cooked)", "calories": 130, "protein": 2.7, "carbs": 28.0, "fats": 0.3, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Brown Rice (cooked)", "calories": 112, "protein": 2.3, "carbs": 24.0, "fats": 0.8, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Sweet Potato (baked)", "calories": 86, "protein": 1.6, "carbs": 20.0, "fats": 0.1, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "White Potato (boiled)", "calories": 77, "protein": 2.0, "carbs": 17.0, "fats": 0.1, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Quinoa (cooked)", "calories": 120, "protein": 4.4, "carbs": 21.0, "fats": 1.9, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Oats (dry)", "calories": 389, "protein": 17.0, "carbs": 66.0, "fats": 7.0, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Oatmeal (cooked)", "calories": 68, "protein": 2.4, "carbs": 12.0, "fats": 1.4, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Banana", "calories": 89, "protein": 1.1, "carbs": 23.0, "fats": 0.3, "is_elite": True, "recommended_for_goal": "athletic", "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Apple", "calories": 52, "protein": 0.3, "carbs": 14.0, "fats": 0.2, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": carb_id, "name": "Blueberries", "calories": 57, "protein": 0.7, "carbs": 14.0, "fats": 0.3, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": carb_id, "name": "Whole Wheat Bread (1 slice)", "calories": 80, "protein": 4.0, "carbs": 13.0, "fats": 1.1, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Chickpeas (cooked)", "calories": 164, "protein": 8.9, "carbs": 27.0, "fats": 2.6, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Corn (cooked)", "calories": 96, "protein": 3.4, "carbs": 21.0, "fats": 1.5, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "legs"},

            # ============ HEALTHY FATS ============
            {"category_id": fat_id, "name": "Avocado", "calories": 160, "protein": 2.0, "carbs": 8.5, "fats": 14.7, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Extra Virgin Olive Oil", "calories": 884, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Walnuts", "calories": 654, "protein": 15.2, "carbs": 13.7, "fats": 65.2, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Almonds", "calories": 579, "protein": 21.0, "carbs": 22.0, "fats": 50.0, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Chia Seeds", "calories": 486, "protein": 16.5, "carbs": 42.1, "fats": 30.7, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": fat_id, "name": "Flax Seeds", "calories": 534, "protein": 18.3, "carbs": 28.9, "fats": 42.2, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Peanut Butter", "calories": 588, "protein": 25.0, "carbs": 20.0, "fats": 50.0, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "MCT Oil", "calories": 900, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "is_elite": True, "recommended_for_goal": "athletic", "target_muscle_group": "all"},
            {"category_id": fat_id, "name": "Coconut Oil", "calories": 892, "protein": 0.0, "carbs": 0.0, "fats": 100.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},

            # ============ VEGETABLES ============
            {"category_id": veg_id, "name": "Broccoli", "calories": 34, "protein": 2.8, "carbs": 6.6, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": veg_id, "name": "Spinach", "calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": veg_id, "name": "Kale", "calories": 49, "protein": 4.3, "carbs": 8.8, "fats": 0.9, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": veg_id, "name": "Asparagus", "calories": 20, "protein": 2.2, "carbs": 3.7, "fats": 0.1, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": veg_id, "name": "Bell Pepper", "calories": 31, "protein": 1.0, "carbs": 6.0, "fats": 0.3, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": veg_id, "name": "Zucchini", "calories": 17, "protein": 1.2, "carbs": 3.1, "fats": 0.3, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": veg_id, "name": "Cucumber", "calories": 15, "protein": 0.7, "carbs": 3.6, "fats": 0.1, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": veg_id, "name": "Cauliflower", "calories": 25, "protein": 1.9, "carbs": 5.0, "fats": 0.3, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": veg_id, "name": "Mushrooms", "calories": 22, "protein": 3.1, "carbs": 3.3, "fats": 0.3, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": veg_id, "name": "Tomato", "calories": 18, "protein": 0.9, "carbs": 3.9, "fats": 0.2, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": veg_id, "name": "Garlic", "calories": 149, "protein": 6.4, "carbs": 33.1, "fats": 0.5, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},

            # ============ DAIRY & EGGS ============
            {"category_id": dai_id, "name": "Whole Egg", "calories": 155, "protein": 13.0, "carbs": 1.1, "fats": 11.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": dai_id, "name": "Egg Whites", "calories": 52, "protein": 11.0, "carbs": 1.0, "fats": 0.2, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": dai_id, "name": "Greek Yogurt (0% fat)", "calories": 59, "protein": 10.0, "carbs": 3.6, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": dai_id, "name": "Whole Milk", "calories": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": dai_id, "name": "Skim Milk", "calories": 34, "protein": 3.4, "carbs": 4.9, "fats": 0.1, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": dai_id, "name": "Cheddar Cheese", "calories": 403, "protein": 25.0, "carbs": 1.3, "fats": 33.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": dai_id, "name": "Mozzarella (low fat)", "calories": 254, "protein": 24.0, "carbs": 3.0, "fats": 16.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},

            # ============ INDIAN FOODS ============
            {"category_id": ind_id, "name": "Dal (cooked)", "calories": 116, "protein": 9.0, "carbs": 20.0, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Roti (whole wheat)", "calories": 265, "protein": 9.0, "carbs": 52.0, "fats": 3.7, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Paneer", "calories": 265, "protein": 18.0, "carbs": 3.6, "fats": 20.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Rajma (cooked)", "calories": 127, "protein": 8.7, "carbs": 22.8, "fats": 0.5, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Moong Dal (cooked)", "calories": 105, "protein": 7.0, "carbs": 19.0, "fats": 0.4, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": ind_id, "name": "Idli (1 piece ~30g)", "calories": 39, "protein": 2.0, "carbs": 8.0, "fats": 0.2, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},
            {"category_id": ind_id, "name": "Poha (cooked)", "calories": 110, "protein": 2.2, "carbs": 23.0, "fats": 0.9, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Curd/Yogurt (full fat)", "calories": 98, "protein": 3.1, "carbs": 4.7, "fats": 4.3, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "all"},
            {"category_id": ind_id, "name": "Sprouts (mixed)", "calories": 65, "protein": 5.0, "carbs": 9.0, "fats": 0.7, "is_elite": True, "recommended_for_goal": "weight_loss", "target_muscle_group": "abs"},
            {"category_id": ind_id, "name": "Sambar (per serving ~200g)", "calories": 80, "protein": 4.0, "carbs": 12.0, "fats": 2.0, "is_elite": False, "recommended_for_goal": "weight_loss", "target_muscle_group": "general"},

            # ============ SUPPLEMENTS & SHAKES ============
            {"category_id": shk_id, "name": "Whey Protein Powder", "calories": 400, "protein": 80.0, "carbs": 8.0, "fats": 5.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": shk_id, "name": "Casein Protein Powder", "calories": 380, "protein": 77.0, "carbs": 6.0, "fats": 3.0, "is_elite": True, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": shk_id, "name": "Plant Protein Powder", "calories": 360, "protein": 70.0, "carbs": 15.0, "fats": 6.0, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},
            {"category_id": shk_id, "name": "Creatine Monohydrate", "calories": 0, "protein": 0.0, "carbs": 0.0, "fats": 0.0, "is_elite": True, "recommended_for_goal": "athletic", "target_muscle_group": "all"},
            {"category_id": shk_id, "name": "Mass Gainer (per 100g powder)", "calories": 380, "protein": 25.0, "carbs": 60.0, "fats": 5.0, "is_elite": False, "recommended_for_goal": "muscle_gain", "target_muscle_group": "all"},

            # ============ TREATS ============
            {"category_id": tre_id, "name": "Dark Chocolate (85%)", "calories": 598, "protein": 7.8, "carbs": 45.9, "fats": 42.6, "is_elite": True, "recommended_for_goal": "general", "target_muscle_group": "general"},
            {"category_id": tre_id, "name": "Donut (glazed)", "calories": 452, "protein": 4.3, "carbs": 58.0, "fats": 22.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "general"},
            {"category_id": tre_id, "name": "Pizza Slice (pepperoni)", "calories": 285, "protein": 12.0, "carbs": 36.0, "fats": 10.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "general"},
            {"category_id": tre_id, "name": "French Fries (100g)", "calories": 312, "protein": 3.4, "carbs": 41.0, "fats": 15.0, "is_elite": False, "recommended_for_goal": "general", "target_muscle_group": "general"},
        ]
        for f in foods:
            db.add(models.FoodItem(**f))
        db.commit()
        print(f"✅ Food database seeded with {len(foods)} items.")
    except Exception as e:
        print(f"Error seeding food database: {e}")
        db.rollback()
    finally:
        db.close()

