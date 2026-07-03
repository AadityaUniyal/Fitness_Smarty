
import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def mega_seed():
    db = SessionLocal()
    try:
        # 1. Clear existing data if needed (optional, safer to append or check existence)
        # for now we check if categories exist
        
        # 2. Categories
        ex_categories = [
            {"name": "Chest", "description": "Pectoral muscles training."},
            {"name": "Back", "description": "Lats, rhomboids, and spinal erectors."},
            {"name": "Legs", "description": "Quads, hamstrings, glutes, and calves."},
            {"name": "Shoulders", "description": "Deltoids and traps."},
            {"name": "Arms", "description": "Biceps, triceps, and forearms."},
            {"name": "Core", "description": "Abs, obliques, and lower back stability."},
        ]
        
        for cat in ex_categories:
            if not db.query(models.ExerciseCategory).filter_by(name=cat["name"]).first():
                db.add(models.ExerciseCategory(**cat))
        db.commit()
        
        # Get category IDs
        cat_map = {c.name: c.id for c in db.query(models.ExerciseCategory).all()}
        
        # 3. Exercises Seeding Logic
        # We need ~100 per muscle. I will define base exercises and generate variations.
        
        muscle_bases = {
            "Chest": ["Bench Press", "Flyes", "Push-ups", "Dips", "Pullover", "Squeeze Press"],
            "Back": ["Row", "Pull-up", "Lat Pulldown", "Deadlift", "Shrugs", "Face Pull"],
            "Legs": ["Squat", "Lunge", "Deadlift", "Leg Press", "Leg Curl", "Leg Extension", "Calf Raise", "Step Up"],
            "Shoulders": ["Overhead Press", "Lateral Raise", "Front Raise", "Reverse Fly", "Upright Row", "Arnold Press"],
            "Arms": ["Bicep Curl", "Hammer Curl", "Tricep Extension", "Pushdown", "Skullcrusher", "Kickback", "Preacher Curl"],
            "Core": ["Plank", "Crunch", "Leg Raise", "Russian Twist", "Mountain Climber", "V-up", "Bird Dog", "Dead Bug"]
        }
        
        variations = ["Barbell", "Dumbbell", "Kettlebell", "Machine", "Cable", "Resistance Band", "Bodyweight", "Smith Machine", "Single-Arm", "Deficit", "Incline", "Decline", "Pause", "Tempo"]
        difficulties = ["Beginner", "Intermediate", "Advanced"]
        
        total_exercises = 0
        for muscle, bases in muscle_bases.items():
            count = 0
            for base in bases:
                for var in variations:
                    for diff in difficulties:
                        if count >= 100: break
                        
                        name = f"{var} {base}" if var != "Bodyweight" else f"Bodyweight {base}"
                        # Randomish calorie burn
                        cal_min = 5.0 + (len(name) % 5)
                        cal_rep = 0.1 + (len(name) % 3) * 0.05
                        
                        ex = models.ExerciseItem(
                            category_id=cat_map[muscle],
                            name=name,
                            targeted_muscle=muscle,
                            difficulty=diff,
                            equipment=var,
                            calories_per_min=cal_min,
                            calories_per_rep=cal_rep,
                            description=f"A {diff} level {muscle} exercise using {var}.",
                            fitness_goal="general"
                        )
                        db.add(ex)
                        count += 1
                        total_exercises += 1
                    if count >= 100: break
                if count >= 100: break
        
        db.commit()
        print(f"[OK] Seeded {total_exercises} exercises.")
        
        # 4. Food Seeding
        food_categories = [
            {"name": "Proteins", "description": "High-protein foods."},
            {"name": "Carbohydrates", "description": "Energy sources."},
            {"name": "Fats", "description": "Healthy fats."},
            {"name": "Fruits & Veggies", "description": "Micronutrients."},
            {"name": "Indian Specials", "description": "Traditional Indian cuisine."},
        ]
        
        for cat in food_categories:
            if not db.query(models.FoodCategory).filter_by(name=cat["name"]).first():
                db.add(models.FoodCategory(**cat))
        db.commit()
        
        f_cat_map = {c.name: c.id for c in db.query(models.FoodCategory).all()}
        
        # Generate 100 foods per category
        food_bases = {
            "Proteins": ["Chicken", "Turkey", "Beef", "Fish", "Eggs", "Tofu", "Paneer", "Lentils", "Whey"],
            "Carbohydrates": ["Rice", "Oats", "Bread", "Pasta", "Potato", "Quinoa", "Corn", "Roti"],
            "Fats": ["Avocado", "Olive Oil", "Walnuts", "Almonds", "Peanut Butter", "Chia Seeds"],
            "Fruits & Veggies": ["Broccoli", "Spinach", "Apple", "Banana", "Blueberries", "Kale", "Tomato", "Carrot"],
            "Indian Specials": ["Dal", "Rajma", "Chole", "Paneer Tikka", "Biryani", "Idli", "Dosa", "Poha"]
        }
        
        total_foods = 0
        for cat_name, bases in food_bases.items():
            count = 0
            for base in bases:
                for i in range(15): # Variations
                    if count >= 100: break
                    name = f"{base} Variation {i+1}"
                    
                    # Randomish macros
                    cal = 100 + (i * 10)
                    prot = 5 + (i % 5) * 2
                    carb = 10 + (i % 10) * 3
                    fat = 2 + (i % 3) * 4
                    
                    f = models.FoodItem(
                        category_id=f_cat_map[cat_name],
                        name=name,
                        calories=cal,
                        protein=prot,
                        carbs=carb,
                        fats=fat,
                        is_elite=(i % 5 == 0),
                        recommended_for_goal="general"
                    )
                    db.add(f)
                    count += 1
                    total_foods += 1
        
        db.commit()
        print(f"[OK] Seeded {total_foods} food items.")
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    mega_seed()
