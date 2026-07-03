"""
Neon PostgreSQL Full Migration
==============================
- Adds missing columns to exercise_items and food_items
- Clears and re-seeds exercise categories + items (50+, goal-tagged)
- Clears and re-seeds food categories + items (65+, per-100g macros)
- PRESERVES all users, user_profiles, meal_logs, etc.

Run from backend directory:
    $env:DATABASE_URL="postgresql://..."
    python migrations/neon_full_migration.py
"""
import os, sys

NEON_URL = "postgresql://neondb_owner:npg_u8mPOinQJwt0@ep-spring-forest-ae89a0gy-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ["DATABASE_URL"] = NEON_URL

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import SessionLocal
from app import models

engine = create_engine(NEON_URL, pool_pre_ping=True)

# ─────────────────────────────────────────────────────────────────────────────
def run_migration():
    print("=" * 60)
    print("  NEON DB MIGRATION SCRIPT")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. Add fitness_goal to exercise_items
        print("\n[1/4] Adding missing columns to exercise_items...")
        conn.execute(text("""
            ALTER TABLE exercise_items
            ADD COLUMN IF NOT EXISTS fitness_goal VARCHAR;
        """))
        conn.commit()
        print("      -> fitness_goal column OK")

        # 2. Add goal/muscle columns to food_items
        print("\n[2/4] Adding missing columns to food_items...")
        conn.execute(text("""
            ALTER TABLE food_items
            ADD COLUMN IF NOT EXISTS recommended_for_goal VARCHAR;
        """))
        conn.execute(text("""
            ALTER TABLE food_items
            ADD COLUMN IF NOT EXISTS target_muscle_group VARCHAR;
        """))
        conn.commit()
        print("      -> recommended_for_goal, target_muscle_group columns OK")

        # 3. Clear old seed data for exercises + foods (NOT users)
        print("\n[3/4] Clearing old exercise and food seed data...")
        conn.execute(text("DELETE FROM exercise_items"))
        conn.execute(text("DELETE FROM exercise_categories"))
        conn.execute(text("DELETE FROM food_items"))
        conn.execute(text("DELETE FROM food_categories"))
        # Reset sequences
        conn.execute(text("ALTER SEQUENCE exercise_items_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE exercise_categories_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE food_items_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE food_categories_id_seq RESTART WITH 1"))
        conn.commit()
        print("      -> Cleared + sequences reset")

    # 4. Re-seed with expanded data
    print("\n[4/4] Seeding exercise and food databases...")

    _seed_exercises()
    _seed_foods()

    # Final counts
    with engine.connect() as conn:
        ex_count   = conn.execute(text("SELECT COUNT(*) FROM exercise_items")).scalar()
        food_count = conn.execute(text("SELECT COUNT(*) FROM food_items")).scalar()
        cat_ex     = conn.execute(text("SELECT COUNT(*) FROM exercise_categories")).scalar()
        cat_food   = conn.execute(text("SELECT COUNT(*) FROM food_categories")).scalar()

    print("\n" + "=" * 60)
    print("  MIGRATION COMPLETE")
    print(f"  Exercise categories : {cat_ex}")
    print(f"  Exercise items      : {ex_count}")
    print(f"  Food categories     : {cat_food}")
    print(f"  Food items          : {food_count}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
def _seed_exercises():
    db = SessionLocal()
    try:
        cats = [
            {"name": "Fat Loss Cardio",       "description": "High-intensity exercises for maximum calorie burn."},
            {"name": "Muscle Building",        "description": "Resistance and strength exercises for hypertrophy."},
            {"name": "Athletic Performance",   "description": "Power, speed, agility training."},
            {"name": "Maintenance & Mobility", "description": "Low-impact, flexibility and endurance work."},
        ]
        for c in cats:
            db.add(models.ExerciseCategory(**c))
        db.commit()

        fl = db.query(models.ExerciseCategory).filter_by(name="Fat Loss Cardio").first().id
        mb = db.query(models.ExerciseCategory).filter_by(name="Muscle Building").first().id
        ap = db.query(models.ExerciseCategory).filter_by(name="Athletic Performance").first().id
        mo = db.query(models.ExerciseCategory).filter_by(name="Maintenance & Mobility").first().id

        exercises = [
            # ─── FAT LOSS CARDIO (goal: fat_loss) ───────────────────────
            {"category_id": fl, "name": "Burpees",              "targeted_muscle": "Full Body",   "difficulty": "Intermediate", "equipment": "None",     "calories_per_min": 12.0, "fitness_goal": "fat_loss",    "description": "High-intensity full body exercise combining squat, plank, and jump."},
            {"category_id": fl, "name": "Jump Rope",            "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Jump Rope","calories_per_min": 13.0, "fitness_goal": "fat_loss",    "description": "Continuous jumping rope for sustained cardio burn."},
            {"category_id": fl, "name": "High Knees",           "targeted_muscle": "Legs, Core",  "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 10.0, "fitness_goal": "fat_loss",    "description": "Running in place with knees raised high for cardio."},
            {"category_id": fl, "name": "Mountain Climbers",    "targeted_muscle": "Core, Shoulders","difficulty": "Intermediate","equipment": "None",    "calories_per_min": 10.5, "fitness_goal": "fat_loss",    "description": "Dynamic plank movement targeting core and cardiovascular system."},
            {"category_id": fl, "name": "Battle Ropes",         "targeted_muscle": "Arms, Core",  "difficulty": "Intermediate", "equipment": "Battle Ropes","calories_per_min": 14.0,"fitness_goal": "fat_loss", "description": "Alternating wave patterns for intense upper body cardio."},
            {"category_id": fl, "name": "Treadmill Sprint",     "targeted_muscle": "Legs, Glutes","difficulty": "Advanced",     "equipment": "Treadmill","calories_per_min": 14.5, "fitness_goal": "fat_loss",    "description": "Max-effort treadmill sprints with rest intervals."},
            {"category_id": fl, "name": "Cycling (Spin)",       "targeted_muscle": "Legs, Glutes","difficulty": "Beginner",     "equipment": "Spin Bike","calories_per_min": 11.0, "fitness_goal": "fat_loss",    "description": "Stationary cycling at variable resistance."},
            {"category_id": fl, "name": "Rowing Machine",       "targeted_muscle": "Full Body",   "difficulty": "Intermediate", "equipment": "Rower",   "calories_per_min": 12.5, "fitness_goal": "fat_loss",    "description": "Full-body rowing for cardio and light resistance."},
            {"category_id": fl, "name": "Jumping Jacks",        "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 8.0,  "fitness_goal": "fat_loss",    "description": "Classic calisthenics movement for warm-up and cardio."},
            {"category_id": fl, "name": "HIIT Box Jumps",       "targeted_muscle": "Legs, Glutes","difficulty": "Advanced",     "equipment": "Plyo Box", "calories_per_min": 13.5, "fitness_goal": "fat_loss",    "description": "Explosive plyometric box jumps in HIIT format."},
            {"category_id": fl, "name": "Kickboxing Combos",    "targeted_muscle": "Full Body",   "difficulty": "Intermediate", "equipment": "None",     "calories_per_min": 11.5, "fitness_goal": "fat_loss",    "description": "Shadow kickboxing combining punches and kicks."},
            {"category_id": fl, "name": "Stair Climber",        "targeted_muscle": "Legs, Glutes","difficulty": "Beginner",     "equipment": "Stair Machine","calories_per_min": 9.0,"fitness_goal": "fat_loss",  "description": "Continuous step climbing for lower body cardio."},
            {"category_id": fl, "name": "Elliptical Trainer",   "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Elliptical","calories_per_min": 9.5, "fitness_goal": "fat_loss",    "description": "Low-impact full body cardio on elliptical machine."},
            # ─── MUSCLE BUILDING (goal: muscle_gain) ────────────────────
            {"category_id": mb, "name": "Barbell Back Squat",   "targeted_muscle": "Legs, Glutes","difficulty": "Advanced",     "equipment": "Barbell",  "calories_per_min": 8.0,  "fitness_goal": "muscle_gain", "description": "Primary compound lower body strength exercise."},
            {"category_id": mb, "name": "Conventional Deadlift","targeted_muscle": "Back, Legs",  "difficulty": "Advanced",     "equipment": "Barbell",  "calories_per_min": 8.5,  "fitness_goal": "muscle_gain", "description": "King of compound movements; builds posterior chain."},
            {"category_id": mb, "name": "Bench Press",          "targeted_muscle": "Chest, Triceps","difficulty": "Intermediate","equipment": "Barbell,Bench","calories_per_min": 6.5,"fitness_goal": "muscle_gain","description": "Flat barbell press for chest development."},
            {"category_id": mb, "name": "Overhead Press",       "targeted_muscle": "Shoulders",   "difficulty": "Intermediate", "equipment": "Barbell",  "calories_per_min": 6.0,  "fitness_goal": "muscle_gain", "description": "Standing military press for shoulder strength."},
            {"category_id": mb, "name": "Pull-Ups",             "targeted_muscle": "Back, Biceps","difficulty": "Intermediate", "equipment": "Pull-up Bar","calories_per_min": 7.0, "fitness_goal": "muscle_gain", "description": "Bodyweight vertical pull for back width and bicep."},
            {"category_id": mb, "name": "Barbell Row",          "targeted_muscle": "Back, Biceps","difficulty": "Intermediate", "equipment": "Barbell",  "calories_per_min": 6.0,  "fitness_goal": "muscle_gain", "description": "Horizontal pulling for middle back thickness."},
            {"category_id": mb, "name": "Dumbbell Curl",        "targeted_muscle": "Biceps",      "difficulty": "Beginner",     "equipment": "Dumbbells","calories_per_min": 4.0,  "fitness_goal": "muscle_gain", "description": "Isolation curl for bicep peak development."},
            {"category_id": mb, "name": "Tricep Pushdown",      "targeted_muscle": "Triceps",     "difficulty": "Beginner",     "equipment": "Cable Machine","calories_per_min": 4.5,"fitness_goal": "muscle_gain","description": "Cable isolation for tricep size and definition."},
            {"category_id": mb, "name": "Leg Press",            "targeted_muscle": "Legs, Glutes","difficulty": "Beginner",     "equipment": "Leg Press Machine","calories_per_min": 5.5,"fitness_goal": "muscle_gain","description": "Machine compound for quad and glute development."},
            {"category_id": mb, "name": "Incline Dumbbell Press","targeted_muscle": "Upper Chest","difficulty": "Intermediate", "equipment": "Dumbbells,Bench","calories_per_min": 6.0,"fitness_goal": "muscle_gain","description": "Upper chest emphasis with incline angle."},
            {"category_id": mb, "name": "Romanian Deadlift",    "targeted_muscle": "Hamstrings",  "difficulty": "Intermediate", "equipment": "Barbell",  "calories_per_min": 6.5,  "fitness_goal": "muscle_gain", "description": "Hip hinge targeting hamstring and glute stretch."},
            {"category_id": mb, "name": "Cable Lateral Raise",  "targeted_muscle": "Shoulders",   "difficulty": "Beginner",     "equipment": "Cable Machine","calories_per_min": 3.5,"fitness_goal": "muscle_gain","description": "Side delt isolation for shoulder width."},
            {"category_id": mb, "name": "Chest Dips",           "targeted_muscle": "Chest, Triceps","difficulty": "Intermediate","equipment": "Dip Bars", "calories_per_min": 7.0,  "fitness_goal": "muscle_gain", "description": "Bodyweight dip with chest lean for lower chest."},
            {"category_id": mb, "name": "Seated Calf Raise",    "targeted_muscle": "Calves",      "difficulty": "Beginner",     "equipment": "Calf Machine","calories_per_min": 3.5,"fitness_goal": "muscle_gain","description": "Soleus isolation for calf development."},
            {"category_id": mb, "name": "Face Pulls",           "targeted_muscle": "Rear Delts, Traps","difficulty": "Beginner","equipment": "Cable Machine","calories_per_min": 3.5,"fitness_goal": "muscle_gain","description": "Cable rear delt exercise for shoulder health."},
            {"category_id": mb, "name": "Hack Squat",           "targeted_muscle": "Quads, Glutes","difficulty": "Intermediate","equipment": "Hack Squat Machine","calories_per_min": 6.0,"fitness_goal": "muscle_gain","description": "Machine squat variant for quad dominance."},
            # ─── ATHLETIC PERFORMANCE (goal: athletic) ───────────────────
            {"category_id": ap, "name": "Power Clean",          "targeted_muscle": "Full Body",   "difficulty": "Advanced",     "equipment": "Barbell",  "calories_per_min": 10.0, "fitness_goal": "athletic",    "description": "Olympic lift developing explosive power."},
            {"category_id": ap, "name": "Box Jump",             "targeted_muscle": "Legs, Glutes","difficulty": "Intermediate", "equipment": "Plyo Box", "calories_per_min": 11.0, "fitness_goal": "athletic",    "description": "Explosive lower body plyometric for power development."},
            {"category_id": ap, "name": "Sprint Intervals (400m)","targeted_muscle": "Legs",     "difficulty": "Advanced",     "equipment": "Track",    "calories_per_min": 15.0, "fitness_goal": "athletic",    "description": "Short sprints with recovery for speed and VO2 max."},
            {"category_id": ap, "name": "Agility Ladder Drills","targeted_muscle": "Legs, Core", "difficulty": "Intermediate", "equipment": "Agility Ladder","calories_per_min": 9.5,"fitness_goal": "athletic","description": "Foot-speed and coordination drills with ladder."},
            {"category_id": ap, "name": "Kettlebell Swing",     "targeted_muscle": "Glutes, Core","difficulty": "Intermediate", "equipment": "Kettlebell","calories_per_min": 12.0,"fitness_goal": "athletic",    "description": "Hip hinge swing for power and cardio."},
            {"category_id": ap, "name": "Hang Snatch",          "targeted_muscle": "Full Body",   "difficulty": "Advanced",     "equipment": "Barbell",  "calories_per_min": 9.5,  "fitness_goal": "athletic",    "description": "Olympic lift variation for power and mobility."},
            {"category_id": ap, "name": "Med Ball Slam",        "targeted_muscle": "Core, Shoulders","difficulty": "Intermediate","equipment": "Med Ball","calories_per_min": 11.0, "fitness_goal": "athletic",    "description": "Explosive overhead slam for power and conditioning."},
            {"category_id": ap, "name": "Depth Jumps",          "targeted_muscle": "Legs",        "difficulty": "Advanced",     "equipment": "Plyo Box", "calories_per_min": 12.5, "fitness_goal": "athletic",    "description": "Drop-and-rebound plyometric for reactive power."},
            {"category_id": ap, "name": "Broad Jumps",          "targeted_muscle": "Legs, Glutes","difficulty": "Intermediate", "equipment": "None",     "calories_per_min": 11.5, "fitness_goal": "athletic",    "description": "Horizontal power jumps for explosive leg drive."},
            # ─── MAINTENANCE & MOBILITY (goal: maintenance) ──────────────
            {"category_id": mo, "name": "Brisk Walking (30min)","targeted_muscle": "Legs, Core",  "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 5.0,  "fitness_goal": "maintenance", "description": "Steady-pace walking for cardiovascular health."},
            {"category_id": mo, "name": "Yoga Flow (Vinyasa)",  "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Yoga Mat", "calories_per_min": 4.0,  "fitness_goal": "maintenance", "description": "Flowing yoga sequence for flexibility and stress relief."},
            {"category_id": mo, "name": "Swimming Laps",        "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Pool",     "calories_per_min": 8.0,  "fitness_goal": "maintenance", "description": "Low-impact full body swim for fitness and recovery."},
            {"category_id": mo, "name": "Plank Hold",           "targeted_muscle": "Core",        "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 3.5,  "fitness_goal": "maintenance", "description": "Isometric core hold for spine stability."},
            {"category_id": mo, "name": "Foam Rolling",         "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Foam Roller","calories_per_min": 2.5,"fitness_goal": "maintenance", "description": "Self-myofascial release for muscle recovery."},
            {"category_id": mo, "name": "Light Cycling",        "targeted_muscle": "Legs",        "difficulty": "Beginner",     "equipment": "Bicycle",  "calories_per_min": 6.0,  "fitness_goal": "maintenance", "description": "Easy outdoor or stationary cycling for active recovery."},
            {"category_id": mo, "name": "Stretching Routine",   "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 2.0,  "fitness_goal": "maintenance", "description": "Full body static stretching for flexibility."},
            {"category_id": mo, "name": "Tai Chi",              "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 3.0,  "fitness_goal": "maintenance", "description": "Slow flowing movements for balance and stress relief."},
            {"category_id": mo, "name": "Light Jogging",        "targeted_muscle": "Legs, Core",  "difficulty": "Beginner",     "equipment": "None",     "calories_per_min": 7.0,  "fitness_goal": "maintenance", "description": "Easy conversational pace jogging for cardio base."},
            {"category_id": mo, "name": "Resistance Band Work", "targeted_muscle": "Full Body",   "difficulty": "Beginner",     "equipment": "Resistance Bands","calories_per_min": 4.0,"fitness_goal": "maintenance","description": "Light band exercises to maintain muscle tone."},
        ]
        for ex in exercises:
            db.add(models.ExerciseItem(**ex))
        db.commit()
        print(f"   -> Seeded {len(exercises)} exercises.")
    except Exception as e:
        db.rollback()
        print(f"   ERROR seeding exercises: {e}")
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
def _seed_foods():
    db = SessionLocal()
    try:
        cats = [
            {"name": "Proteins",             "description": "High-protein foods for muscle building and recovery."},
            {"name": "Carbohydrates",         "description": "Complex carbs for sustained energy."},
            {"name": "Healthy Fats",          "description": "Essential fats for hormones and brain health."},
            {"name": "Vegetables",            "description": "Micronutrient-dense low-cal foods."},
            {"name": "Dairy & Eggs",          "description": "High-bioavailability proteins and fats."},
            {"name": "Indian Foods",          "description": "Common South Asian foods with accurate per-100g macros."},
            {"name": "Supplements & Shakes",  "description": "Post-workout and protein supplements."},
            {"name": "Treats",                "description": "High-calorie indulgent foods (use in moderation)."},
        ]
        for c in cats:
            db.add(models.FoodCategory(**c))
        db.commit()

        prot_id = db.query(models.FoodCategory).filter_by(name="Proteins").first().id
        carb_id = db.query(models.FoodCategory).filter_by(name="Carbohydrates").first().id
        fat_id  = db.query(models.FoodCategory).filter_by(name="Healthy Fats").first().id
        veg_id  = db.query(models.FoodCategory).filter_by(name="Vegetables").first().id
        dai_id  = db.query(models.FoodCategory).filter_by(name="Dairy & Eggs").first().id
        ind_id  = db.query(models.FoodCategory).filter_by(name="Indian Foods").first().id
        shk_id  = db.query(models.FoodCategory).filter_by(name="Supplements & Shakes").first().id
        tre_id  = db.query(models.FoodCategory).filter_by(name="Treats").first().id

        foods = [
            # ── PROTEINS (per 100g) ──────────────────────────────────────
            {"category_id": prot_id, "name": "Chicken Breast",        "calories": 165, "protein": 31.0, "carbs": 0.0,  "fats": 3.6,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Turkey Breast",         "calories": 135, "protein": 30.0, "carbs": 0.0,  "fats": 1.0,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Salmon (Wild)",         "calories": 208, "protein": 22.0, "carbs": 0.0,  "fats": 13.0, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tuna (canned in water)","calories": 116, "protein": 26.0, "carbs": 0.0,  "fats": 1.0,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Cod Fillet",            "calories": 82,  "protein": 18.0, "carbs": 0.0,  "fats": 0.7,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Shrimp",                "calories": 99,  "protein": 24.0, "carbs": 0.0,  "fats": 0.3,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": prot_id, "name": "Lean Ground Beef (95%)","calories": 137, "protein": 21.4, "carbs": 0.0,  "fats": 5.0,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Bison Steak",           "calories": 143, "protein": 28.0, "carbs": 0.0,  "fats": 2.4,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tofu (Firm)",           "calories": 83,  "protein": 10.0, "carbs": 1.0,  "fats": 5.0,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Tempeh",                "calories": 192, "protein": 19.0, "carbs": 9.0,  "fats": 11.0, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Lentils (cooked)",      "calories": 116, "protein": 9.0,  "carbs": 20.0, "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Black Beans (cooked)",  "calories": 132, "protein": 8.9,  "carbs": 24.0, "fats": 0.5,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Cottage Cheese",        "calories": 98,  "protein": 11.0, "carbs": 3.4,  "fats": 4.3,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Pork Tenderloin",       "calories": 143, "protein": 26.0, "carbs": 0.0,  "fats": 3.5,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": prot_id, "name": "Sardines (in water)",   "calories": 208, "protein": 25.0, "carbs": 0.0,  "fats": 11.5, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            # ── CARBOHYDRATES (per 100g) ─────────────────────────────────
            {"category_id": carb_id, "name": "White Rice (cooked)",   "calories": 130, "protein": 2.7,  "carbs": 28.0, "fats": 0.3,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Brown Rice (cooked)",   "calories": 112, "protein": 2.3,  "carbs": 24.0, "fats": 0.8,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Sweet Potato (baked)",  "calories": 86,  "protein": 1.6,  "carbs": 20.0, "fats": 0.1,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "White Potato (boiled)", "calories": 77,  "protein": 2.0,  "carbs": 17.0, "fats": 0.1,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Quinoa (cooked)",       "calories": 120, "protein": 4.4,  "carbs": 21.0, "fats": 1.9,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Oats (dry)",            "calories": 389, "protein": 17.0, "carbs": 66.0, "fats": 7.0,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Oatmeal (cooked)",      "calories": 68,  "protein": 2.4,  "carbs": 12.0, "fats": 1.4,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Banana",                "calories": 89,  "protein": 1.1,  "carbs": 23.0, "fats": 0.3,  "is_elite": True,  "recommended_for_goal": "athletic",     "target_muscle_group": "legs"},
            {"category_id": carb_id, "name": "Apple",                 "calories": 52,  "protein": 0.3,  "carbs": 14.0, "fats": 0.2,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": carb_id, "name": "Blueberries",           "calories": 57,  "protein": 0.7,  "carbs": 14.0, "fats": 0.3,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": carb_id, "name": "Whole Wheat Bread",     "calories": 80,  "protein": 4.0,  "carbs": 13.0, "fats": 1.1,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Chickpeas (cooked)",    "calories": 164, "protein": 8.9,  "carbs": 27.0, "fats": 2.6,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": carb_id, "name": "Corn (cooked)",         "calories": 96,  "protein": 3.4,  "carbs": 21.0, "fats": 1.5,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "legs"},
            # ── HEALTHY FATS (per 100g) ──────────────────────────────────
            {"category_id": fat_id,  "name": "Avocado",               "calories": 160, "protein": 2.0,  "carbs": 8.5,  "fats": 14.7, "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Extra Virgin Olive Oil","calories": 884, "protein": 0.0,  "carbs": 0.0,  "fats": 100.0,"is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Walnuts",               "calories": 654, "protein": 15.2, "carbs": 13.7, "fats": 65.2, "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Almonds",               "calories": 579, "protein": 21.0, "carbs": 22.0, "fats": 50.0, "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Chia Seeds",            "calories": 486, "protein": 16.5, "carbs": 42.1, "fats": 30.7, "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": fat_id,  "name": "Flax Seeds",            "calories": 534, "protein": 18.3, "carbs": 28.9, "fats": 42.2, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Peanut Butter",         "calories": 588, "protein": 25.0, "carbs": 20.0, "fats": 50.0, "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "MCT Oil",               "calories": 900, "protein": 0.0,  "carbs": 0.0,  "fats": 100.0,"is_elite": True,  "recommended_for_goal": "athletic",     "target_muscle_group": "all"},
            {"category_id": fat_id,  "name": "Coconut Oil",           "calories": 892, "protein": 0.0,  "carbs": 0.0,  "fats": 100.0,"is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            # ── VEGETABLES (per 100g) ────────────────────────────────────
            {"category_id": veg_id,  "name": "Broccoli",              "calories": 34,  "protein": 2.8,  "carbs": 6.6,  "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": veg_id,  "name": "Spinach",               "calories": 23,  "protein": 2.9,  "carbs": 3.6,  "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": veg_id,  "name": "Kale",                  "calories": 49,  "protein": 4.3,  "carbs": 8.8,  "fats": 0.9,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": veg_id,  "name": "Asparagus",             "calories": 20,  "protein": 2.2,  "carbs": 3.7,  "fats": 0.1,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": veg_id,  "name": "Bell Pepper",           "calories": 31,  "protein": 1.0,  "carbs": 6.0,  "fats": 0.3,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": veg_id,  "name": "Zucchini",              "calories": 17,  "protein": 1.2,  "carbs": 3.1,  "fats": 0.3,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": veg_id,  "name": "Cucumber",              "calories": 15,  "protein": 0.7,  "carbs": 3.6,  "fats": 0.1,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": veg_id,  "name": "Cauliflower",           "calories": 25,  "protein": 1.9,  "carbs": 5.0,  "fats": 0.3,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": veg_id,  "name": "Mushrooms",             "calories": 22,  "protein": 3.1,  "carbs": 3.3,  "fats": 0.3,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": veg_id,  "name": "Tomato",                "calories": 18,  "protein": 0.9,  "carbs": 3.9,  "fats": 0.2,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": veg_id,  "name": "Garlic",                "calories": 149, "protein": 6.4,  "carbs": 33.1, "fats": 0.5,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            # ── DAIRY & EGGS (per 100g) ──────────────────────────────────
            {"category_id": dai_id,  "name": "Whole Egg",             "calories": 155, "protein": 13.0, "carbs": 1.1,  "fats": 11.0, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": dai_id,  "name": "Egg Whites",            "calories": 52,  "protein": 11.0, "carbs": 1.0,  "fats": 0.2,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": dai_id,  "name": "Greek Yogurt (0% fat)", "calories": 59,  "protein": 10.0, "carbs": 3.6,  "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": dai_id,  "name": "Whole Milk",            "calories": 61,  "protein": 3.2,  "carbs": 4.8,  "fats": 3.3,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": dai_id,  "name": "Skim Milk",             "calories": 34,  "protein": 3.4,  "carbs": 4.9,  "fats": 0.1,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": dai_id,  "name": "Cheddar Cheese",        "calories": 403, "protein": 25.0, "carbs": 1.3,  "fats": 33.0, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": dai_id,  "name": "Mozzarella (low fat)",  "calories": 254, "protein": 24.0, "carbs": 3.0,  "fats": 16.0, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            # ── INDIAN FOODS (per 100g) ──────────────────────────────────
            {"category_id": ind_id,  "name": "Dal (cooked)",          "calories": 116, "protein": 9.0,  "carbs": 20.0, "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Roti (whole wheat)",    "calories": 265, "protein": 9.0,  "carbs": 52.0, "fats": 3.7,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Paneer",                "calories": 265, "protein": 18.0, "carbs": 3.6,  "fats": 20.0, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Rajma (cooked)",        "calories": 127, "protein": 8.7,  "carbs": 22.8, "fats": 0.5,  "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Moong Dal (cooked)",    "calories": 105, "protein": 7.0,  "carbs": 19.0, "fats": 0.4,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": ind_id,  "name": "Idli (per piece ~30g)", "calories": 39,  "protein": 2.0,  "carbs": 8.0,  "fats": 0.2,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": ind_id,  "name": "Poha (cooked)",         "calories": 110, "protein": 2.2,  "carbs": 23.0, "fats": 0.9,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Curd / Dahi (full fat)","calories": 98,  "protein": 3.1,  "carbs": 4.7,  "fats": 4.3,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Sprouts (mixed)",       "calories": 65,  "protein": 5.0,  "carbs": 9.0,  "fats": 0.7,  "is_elite": True,  "recommended_for_goal": "fat_loss",     "target_muscle_group": "abs"},
            {"category_id": ind_id,  "name": "Sambar (~200g serving)","calories": 80,  "protein": 4.0,  "carbs": 12.0, "fats": 2.0,  "is_elite": False, "recommended_for_goal": "fat_loss",     "target_muscle_group": "general"},
            {"category_id": ind_id,  "name": "Chana Masala (cooked)", "calories": 164, "protein": 8.9,  "carbs": 27.4, "fats": 2.8,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Palak Paneer",          "calories": 178, "protein": 9.5,  "carbs": 6.0,  "fats": 13.5, "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": ind_id,  "name": "Dosa (plain)",          "calories": 120, "protein": 3.2,  "carbs": 24.0, "fats": 1.5,  "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "all"},
            # ── SUPPLEMENTS & SHAKES (per 100g powder) ───────────────────
            {"category_id": shk_id,  "name": "Whey Protein Powder",   "calories": 400, "protein": 80.0, "carbs": 8.0,  "fats": 5.0,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": shk_id,  "name": "Casein Protein Powder", "calories": 380, "protein": 77.0, "carbs": 6.0,  "fats": 3.0,  "is_elite": True,  "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": shk_id,  "name": "Plant Protein Powder",  "calories": 360, "protein": 70.0, "carbs": 15.0, "fats": 6.0,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": shk_id,  "name": "Mass Gainer (100g)",    "calories": 380, "protein": 25.0, "carbs": 60.0, "fats": 5.0,  "is_elite": False, "recommended_for_goal": "muscle_gain",  "target_muscle_group": "all"},
            {"category_id": shk_id,  "name": "Creatine Monohydrate",  "calories": 0,   "protein": 0.0,  "carbs": 0.0,  "fats": 0.0,  "is_elite": True,  "recommended_for_goal": "athletic",     "target_muscle_group": "all"},
            # ── TREATS ───────────────────────────────────────────────────
            {"category_id": tre_id,  "name": "Dark Chocolate (85%)",  "calories": 598, "protein": 7.8,  "carbs": 45.9, "fats": 42.6, "is_elite": True,  "recommended_for_goal": "general",      "target_muscle_group": "general"},
            {"category_id": tre_id,  "name": "Donut (glazed)",        "calories": 452, "protein": 4.3,  "carbs": 58.0, "fats": 22.0, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "general"},
            {"category_id": tre_id,  "name": "Pizza (pepperoni slice)","calories": 285, "protein": 12.0, "carbs": 36.0, "fats": 10.0, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "general"},
            {"category_id": tre_id,  "name": "French Fries (100g)",   "calories": 312, "protein": 3.4,  "carbs": 41.0, "fats": 15.0, "is_elite": False, "recommended_for_goal": "general",      "target_muscle_group": "general"},
        ]
        for f in foods:
            db.add(models.FoodItem(**f))
        db.commit()
        print(f"   -> Seeded {len(foods)} food items.")
    except Exception as e:
        db.rollback()
        print(f"   ERROR seeding foods: {e}")
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_migration()
