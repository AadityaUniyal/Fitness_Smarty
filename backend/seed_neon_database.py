"""
Comprehensive Database Seeding Script for Neon PostgreSQL

Seeds:
1. Exercise categories and items (by muscle group and difficulty)
2. Food categories and items (with nutrition data)
3. Female-specific exercises

Run: python seed_neon_database.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Exercise data organized by muscle group and difficulty
EXERCISE_DATA = {
    "Chest": {
        "beginner": [
            {"name": "Push-ups", "equipment": "Bodyweight", "calories_per_min": 7.0, "calories_per_rep": 0.5, "goal": "muscle_gain"},
            {"name": "Incline Push-ups", "equipment": "Bench", "calories_per_min": 6.0, "calories_per_rep": 0.4, "goal": "fat_loss"},
            {"name": "Wall Push-ups", "equipment": "Wall", "calories_per_min": 4.0, "calories_per_rep": 0.3, "goal": "maintenance"},
            {"name": "Knee Push-ups", "equipment": "Bodyweight", "calories_per_min": 5.0, "calories_per_rep": 0.35, "goal": "fat_loss"},
        ],
        "intermediate": [
            {"name": "Dumbbell Bench Press", "equipment": "Dumbbells", "calories_per_min": 8.0, "calories_per_rep": 1.0, "goal": "muscle_gain"},
            {"name": "Chest Flyes", "equipment": "Dumbbells", "calories_per_min": 7.0, "calories_per_rep": 0.8, "goal": "muscle_gain"},
            {"name": "Decline Push-ups", "equipment": "Bench", "calories_per_min": 8.0, "calories_per_rep": 0.6, "goal": "athletic"},
            {"name": "Cable Chest Press", "equipment": "Cable Machine", "calories_per_min": 7.5, "calories_per_rep": 0.9, "goal": "muscle_gain"},
        ],
        "advanced": [
            {"name": "Barbell Bench Press", "equipment": "Barbell", "calories_per_min": 9.0, "calories_per_rep": 1.5, "goal": "muscle_gain"},
            {"name": "Incline Barbell Press", "equipment": "Barbell", "calories_per_min": 9.5, "calories_per_rep": 1.6, "goal": "muscle_gain"},
            {"name": "Weighted Dips", "equipment": "Dip Bar + Weight", "calories_per_min": 10.0, "calories_per_rep": 1.8, "goal": "athletic"},
            {"name": "Plyometric Push-ups", "equipment": "Bodyweight", "calories_per_min": 11.0, "calories_per_rep": 1.2, "goal": "athletic"},
        ]
    },
    "Back": {
        "beginner": [
            {"name": "Lat Pulldown (Light)", "equipment": "Cable Machine", "calories_per_min": 6.0, "calories_per_rep": 0.6, "goal": "muscle_gain"},
            {"name": "Seated Cable Row (Light)", "equipment": "Cable Machine", "calories_per_min": 6.0, "calories_per_rep": 0.6, "goal": "muscle_gain"},
            {"name": "Resistance Band Rows", "equipment": "Resistance Band", "calories_per_min": 5.0, "calories_per_rep": 0.4, "goal": "fat_loss"},
            {"name": "Superman Hold", "equipment": "Bodyweight", "calories_per_min": 4.0, "calories_per_rep": 0.3, "goal": "maintenance"},
        ],
        "intermediate": [
            {"name": "Dumbbell Rows", "equipment": "Dumbbells", "calories_per_min": 7.5, "calories_per_rep": 1.0, "goal": "muscle_gain"},
            {"name": "Pull-ups (Assisted)", "equipment": "Pull-up Bar", "calories_per_min": 8.0, "calories_per_rep": 1.2, "goal": "athletic"},
            {"name": "T-Bar Rows", "equipment": "T-Bar", "calories_per_min": 8.0, "calories_per_rep": 1.1, "goal": "muscle_gain"},
            {"name": "Face Pulls", "equipment": "Cable Machine", "calories_per_min": 6.0, "calories_per_rep": 0.5, "goal": "maintenance"},
        ],
        "advanced": [
            {"name": "Barbell Rows", "equipment": "Barbell", "calories_per_min": 9.0, "calories_per_rep": 1.5, "goal": "muscle_gain"},
            {"name": "Deadlifts", "equipment": "Barbell", "calories_per_min": 10.0, "calories_per_rep": 2.0, "goal": "muscle_gain"},
            {"name": "Pull-ups (Unassisted)", "equipment": "Pull-up Bar", "calories_per_min": 9.5, "calories_per_rep": 1.5, "goal": "athletic"},
            {"name": "Weighted Pull-ups", "equipment": "Pull-up Bar + Weight", "calories_per_min": 11.0, "calories_per_rep": 2.2, "goal": "athletic"},
        ]
    },
    "Legs": {
        "beginner": [
            {"name": "Bodyweight Squats", "equipment": "Bodyweight", "calories_per_min": 7.0, "calories_per_rep": 0.5, "goal": "fat_loss"},
            {"name": "Lunges", "equipment": "Bodyweight", "calories_per_min": 7.5, "calories_per_rep": 0.6, "goal": "fat_loss"},
            {"name": "Glute Bridges", "equipment": "Bodyweight", "calories_per_min": 6.0, "calories_per_rep": 0.4, "goal": "muscle_gain"},
            {"name": "Wall Sits", "equipment": "Wall", "calories_per_min": 5.0, "calories_per_rep": 0.3, "goal": "maintenance"},
        ],
        "intermediate": [
            {"name": "Goblet Squats", "equipment": "Dumbbell", "calories_per_min": 8.5, "calories_per_rep": 1.0, "goal": "muscle_gain"},
            {"name": "Bulgarian Split Squats", "equipment": "Dumbbells", "calories_per_min": 8.0, "calories_per_rep": 1.2, "goal": "muscle_gain"},
            {"name": "Leg Press", "equipment": "Leg Press Machine", "calories_per_min": 8.0, "calories_per_rep": 1.0, "goal": "muscle_gain"},
            {"name": "Romanian Deadlifts", "equipment": "Dumbbells", "calories_per_min": 8.5, "calories_per_rep": 1.3, "goal": "muscle_gain"},
        ],
        "advanced": [
            {"name": "Barbell Back Squats", "equipment": "Barbell", "calories_per_min": 10.0, "calories_per_rep": 2.0, "goal": "muscle_gain"},
            {"name": "Barbell Front Squats", "equipment": "Barbell", "calories_per_min": 10.5, "calories_per_rep": 2.1, "goal": "athletic"},
            {"name": "Box Jumps", "equipment": "Plyo Box", "calories_per_min": 12.0, "calories_per_rep": 1.5, "goal": "athletic"},
            {"name": "Pistol Squats", "equipment": "Bodyweight", "calories_per_min": 11.0, "calories_per_rep": 1.8, "goal": "athletic"},
        ]
    },
    "Shoulders": {
        "beginner": [
            {"name": "Shoulder Press (Light DB)", "equipment": "Dumbbells", "calories_per_min": 6.0, "calories_per_rep": 0.5, "goal": "muscle_gain"},
            {"name": "Lateral Raises (Light)", "equipment": "Dumbbells", "calories_per_min": 5.0, "calories_per_rep": 0.4, "goal": "muscle_gain"},
            {"name": "Front Raises", "equipment": "Dumbbells", "calories_per_min": 5.0, "calories_per_rep": 0.4, "goal": "muscle_gain"},
            {"name": "Arm Circles", "equipment": "Bodyweight", "calories_per_min": 3.0, "calories_per_rep": 0.2, "goal": "maintenance"},
        ],
        "intermediate": [
            {"name": "Dumbbell Shoulder Press", "equipment": "Dumbbells", "calories_per_min": 7.5, "calories_per_rep": 0.9, "goal": "muscle_gain"},
            {"name": "Arnold Press", "equipment": "Dumbbells", "calories_per_min": 8.0, "calories_per_rep": 1.0, "goal": "muscle_gain"},
            {"name": "Upright Rows", "equipment": "Barbell", "calories_per_min": 7.0, "calories_per_rep": 0.8, "goal": "muscle_gain"},
            {"name": "Cable Lateral Raises", "equipment": "Cable Machine", "calories_per_min": 6.5, "calories_per_rep": 0.7, "goal": "muscle_gain"},
        ],
        "advanced": [
            {"name": "Barbell Overhead Press", "equipment": "Barbell", "calories_per_min": 9.0, "calories_per_rep": 1.5, "goal": "muscle_gain"},
            {"name": "Pike Push-ups", "equipment": "Bodyweight", "calories_per_min": 8.5, "calories_per_rep": 1.0, "goal": "athletic"},
            {"name": "Handstand Push-ups", "equipment": "Bodyweight", "calories_per_min": 12.0, "calories_per_rep": 2.0, "goal": "athletic"},
            {"name": "Dumbbell Clean & Press", "equipment": "Dumbbells", "calories_per_min": 11.0, "calories_per_rep": 1.8, "goal": "athletic"},
        ]
    },
    "Arms": {
        "beginner": [
            {"name": "Bicep Curls (Light)", "equipment": "Dumbbells", "calories_per_min": 4.0, "calories_per_rep": 0.3, "goal": "muscle_gain"},
            {"name": "Tricep Dips (Bench)", "equipment": "Bench", "calories_per_min": 5.0, "calories_per_rep": 0.4, "goal": "muscle_gain"},
            {"name": "Hammer Curls (Light)", "equipment": "Dumbbells", "calories_per_min": 4.0, "calories_per_rep": 0.3, "goal": "muscle_gain"},
            {"name": "Overhead Tricep Extension", "equipment": "Dumbbell", "calories_per_min": 4.5, "calories_per_rep": 0.35, "goal": "muscle_gain"},
        ],
        "intermediate": [
            {"name": "Barbell Curls", "equipment": "Barbell", "calories_per_min": 5.5, "calories_per_rep": 0.6, "goal": "muscle_gain"},
            {"name": "Skull Crushers", "equipment": "Barbell", "calories_per_min": 6.0, "calories_per_rep": 0.7, "goal": "muscle_gain"},
            {"name": "Concentration Curls", "equipment": "Dumbbell", "calories_per_min": 5.0, "calories_per_rep": 0.5, "goal": "muscle_gain"},
            {"name": "Cable Tricep Pushdowns", "equipment": "Cable Machine", "calories_per_min": 5.5, "calories_per_rep": 0.6, "goal": "muscle_gain"},
        ],
        "advanced": [
            {"name": "Weighted Chin-ups", "equipment": "Pull-up Bar + Weight", "calories_per_min": 9.0, "calories_per_rep": 1.5, "goal": "athletic"},
            {"name": "Close-Grip Bench Press", "equipment": "Barbell", "calories_per_min": 8.0, "calories_per_rep": 1.2, "goal": "muscle_gain"},
            {"name": "21s Bicep Curls", "equipment": "Barbell", "calories_per_min": 7.0, "calories_per_rep": 0.8, "goal": "muscle_gain"},
            {"name": "Diamond Push-ups", "equipment": "Bodyweight", "calories_per_min": 7.5, "calories_per_rep": 0.9, "goal": "athletic"},
        ]
    },
    "Abs": {
        "beginner": [
            {"name": "Crunches", "equipment": "Bodyweight", "calories_per_min": 5.0, "calories_per_rep": 0.3, "goal": "fat_loss"},
            {"name": "Plank", "equipment": "Bodyweight", "calories_per_min": 6.0, "calories_per_rep": 0.4, "goal": "fat_loss"},
            {"name": "Leg Raises", "equipment": "Bodyweight", "calories_per_min": 6.0, "calories_per_rep": 0.5, "goal": "fat_loss"},
            {"name": "Dead Bug", "equipment": "Bodyweight", "calories_per_min": 5.0, "calories_per_rep": 0.3, "goal": "maintenance"},
        ],
        "intermediate": [
            {"name": "Russian Twists", "equipment": "Medicine Ball", "calories_per_min": 7.0, "calories_per_rep": 0.4, "goal": "fat_loss"},
            {"name": "Mountain Climbers", "equipment": "Bodyweight", "calories_per_min": 9.0, "calories_per_rep": 0.6, "goal": "fat_loss"},
            {"name": "Bicycle Crunches", "equipment": "Bodyweight", "calories_per_min": 7.5, "calories_per_rep": 0.5, "goal": "fat_loss"},
            {"name": "Side Plank", "equipment": "Bodyweight", "calories_per_min": 6.5, "calories_per_rep": 0.4, "goal": "maintenance"},
        ],
        "advanced": [
            {"name": "Hanging Leg Raises", "equipment": "Pull-up Bar", "calories_per_min": 8.0, "calories_per_rep": 1.0, "goal": "athletic"},
            {"name": "Ab Wheel Rollouts", "equipment": "Ab Wheel", "calories_per_min": 9.0, "calories_per_rep": 1.2, "goal": "athletic"},
            {"name": "Dragon Flags", "equipment": "Bench", "calories_per_min": 10.0, "calories_per_rep": 1.5, "goal": "athletic"},
            {"name": "L-Sit Hold", "equipment": "Parallel Bars", "calories_per_min": 8.5, "calories_per_rep": 1.0, "goal": "athletic"},
        ]
    },
    "Cardio": {
        "beginner": [
            {"name": "Walking", "equipment": "None", "calories_per_min": 4.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
            {"name": "Light Jogging", "equipment": "None", "calories_per_min": 7.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
            {"name": "Cycling (Leisurely)", "equipment": "Bike", "calories_per_min": 6.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
            {"name": "Swimming (Easy)", "equipment": "Pool", "calories_per_min": 8.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
        ],
        "intermediate": [
            {"name": "Running (Moderate)", "equipment": "None", "calories_per_min": 10.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
            {"name": "Cycling (Moderate)", "equipment": "Bike", "calories_per_min": 9.0, "calories_per_rep": 0.0, "goal": "athletic"},
            {"name": "Rowing", "equipment": "Rowing Machine", "calories_per_min": 11.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
            {"name": "Jump Rope", "equipment": "Jump Rope", "calories_per_min": 12.0, "calories_per_rep": 0.0, "goal": "fat_loss"},
        ],
        "advanced": [
            {"name": "HIIT Sprints", "equipment": "None", "calories_per_min": 15.0, "calories_per_rep": 0.0, "goal": "athletic"},
            {"name": "Running (Fast)", "equipment": "None", "calories_per_min": 13.0, "calories_per_rep": 0.0, "goal": "athletic"},
            {"name": "Burpees", "equipment": "Bodyweight", "calories_per_min": 14.0, "calories_per_rep": 1.5, "goal": "fat_loss"},
            {"name": "Battle Ropes", "equipment": "Battle Ropes", "calories_per_min": 12.0, "calories_per_rep": 0.0, "goal": "athletic"},
        ]
    },
    "Calves": {
        "beginner": [
            {"name": "Standing Calf Raises", "equipment": "Bodyweight", "calories_per_min": 4.0, "calories_per_rep": 0.2, "goal": "muscle_gain"},
            {"name": "Seated Calf Raises", "equipment": "Bodyweight", "calories_per_min": 3.5, "calories_per_rep": 0.2, "goal": "muscle_gain"},
        ],
        "intermediate": [
            {"name": "Weighted Calf Raises", "equipment": "Dumbbells", "calories_per_min": 5.0, "calories_per_rep": 0.4, "goal": "muscle_gain"},
            {"name": "Jump Squats", "equipment": "Bodyweight", "calories_per_min": 8.0, "calories_per_rep": 0.8, "goal": "athletic"},
        ],
        "advanced": [
            {"name": "Single-Leg Calf Raises", "equipment": "Bodyweight", "calories_per_min": 6.0, "calories_per_rep": 0.6, "goal": "athletic"},
            {"name": "Box Jumps (High)", "equipment": "Plyo Box", "calories_per_min": 12.0, "calories_per_rep": 1.5, "goal": "athletic"},
        ]
    }
}

# Female-specific exercises with cycle phase suitability
FEMALE_EXERCISES = [
    {"name": "Pelvic Floor Exercises (Kegels)", "muscle": "Pelvic Floor", "difficulty": "beginner", "phase": "all", "calories_per_rep": 0.1},
    {"name": "Prenatal Yoga Flow", "muscle": "Full Body", "difficulty": "beginner", "phase": "menstrual", "calories_per_min": 4.0},
    {"name": "Menstrual Phase Stretching", "muscle": "Full Body", "difficulty": "beginner", "phase": "menstrual", "calories_per_min": 3.0},
    {"name": "Follicular Phase HIIT", "muscle": "Full Body", "difficulty": "advanced", "phase": "follicular", "calories_per_min": 14.0},
    {"name": "Ovulation Power Training", "muscle": "Full Body", "difficulty": "advanced", "phase": "ovulation", "calories_per_min": 15.0},
    {"name": "Luteal Phase Pilates", "muscle": "Core", "difficulty": "intermediate", "phase": "luteal", "calories_per_min": 6.0},
]

# Food database with per-100g nutrition
FOOD_DATA = {
    "Proteins": [
        {"name": "Chicken Breast", "calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Salmon", "calories": 208, "protein": 20, "carbs": 0, "fats": 13, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Eggs", "calories": 155, "protein": 13, "carbs": 1.1, "fats": 11, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Greek Yogurt", "calories": 59, "protein": 10, "carbs": 3.6, "fats": 0.4, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Lean Beef", "calories": 250, "protein": 26, "carbs": 0, "fats": 15, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Tuna", "calories": 130, "protein": 28, "carbs": 0, "fats": 1, "is_elite": True, "goal": "fat_loss"},
        {"name": "Turkey Breast", "calories": 135, "protein": 30, "carbs": 0, "fats": 1, "is_elite": True, "goal": "fat_loss"},
        {"name": "Cottage Cheese", "calories": 98, "protein": 11, "carbs": 3.4, "fats": 4.3, "is_elite": False, "goal": "muscle_gain"},
        {"name": "Tofu", "calories": 76, "protein": 8, "carbs": 1.9, "fats": 4.8, "is_elite": False, "goal": "maintenance"},
        {"name": "Protein Powder (Whey)", "calories": 400, "protein": 80, "carbs": 8, "fats": 5, "is_elite": True, "goal": "muscle_gain"},
    ],
    "Carbs": [
        {"name": "Brown Rice", "calories": 370, "protein": 7.9, "carbs": 77, "fats": 2.9, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Oats", "calories": 389, "protein": 16.9, "carbs": 66, "fats": 6.9, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Sweet Potato", "calories": 86, "protein": 1.6, "carbs": 20, "fats": 0.1, "is_elite": True, "goal": "fat_loss"},
        {"name": "Quinoa", "calories": 368, "protein": 14, "carbs": 64, "fats": 6, "is_elite": True, "goal": "athletic"},
        {"name": "Whole Wheat Bread", "calories": 247, "protein": 13, "carbs": 41, "fats": 3.4, "is_elite": False, "goal": "maintenance"},
        {"name": "Pasta (Whole Wheat)", "calories": 348, "protein": 14.6, "carbs": 72, "fats": 1.4, "is_elite": False, "goal": "athletic"},
        {"name": "Banana", "calories": 89, "protein": 1.1, "carbs": 23, "fats": 0.3, "is_elite": True, "goal": "athletic"},
        {"name": "Apple", "calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2, "is_elite": False, "goal": "fat_loss"},
    ],
    "Fats": [
        {"name": "Almonds", "calories": 579, "protein": 21, "carbs": 22, "fats": 50, "is_elite": True, "goal": "maintenance"},
        {"name": "Avocado", "calories": 160, "protein": 2, "carbs": 9, "fats": 15, "is_elite": True, "goal": "maintenance"},
        {"name": "Peanut Butter", "calories": 588, "protein": 25, "carbs": 20, "fats": 50, "is_elite": False, "goal": "muscle_gain"},
        {"name": "Olive Oil", "calories": 884, "protein": 0, "carbs": 0, "fats": 100, "is_elite": True, "goal": "maintenance"},
        {"name": "Walnuts", "calories": 654, "protein": 15, "carbs": 14, "fats": 65, "is_elite": True, "goal": "maintenance"},
        {"name": "Chia Seeds", "calories": 486, "protein": 17, "carbs": 42, "fats": 31, "is_elite": True, "goal": "athletic"},
    ],
    "Vegetables": [
        {"name": "Broccoli", "calories": 34, "protein": 2.8, "carbs": 7, "fats": 0.4, "is_elite": True, "goal": "fat_loss"},
        {"name": "Spinach", "calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "is_elite": True, "goal": "fat_loss"},
        {"name": "Kale", "calories": 49, "protein": 4.3, "carbs": 9, "fats": 0.9, "is_elite": True, "goal": "fat_loss"},
        {"name": "Carrots", "calories": 41, "protein": 0.9, "carbs": 10, "fats": 0.2, "is_elite": False, "goal": "maintenance"},
        {"name": "Bell Peppers", "calories": 31, "protein": 1, "carbs": 6, "fats": 0.3, "is_elite": False, "goal": "fat_loss"},
        {"name": "Tomatoes", "calories": 18, "protein": 0.9, "carbs": 3.9, "fats": 0.2, "is_elite": False, "goal": "fat_loss"},
    ],
    "Dairy": [
        {"name": "Milk (Whole)", "calories": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3, "is_elite": False, "goal": "maintenance"},
        {"name": "Milk (Skim)", "calories": 34, "protein": 3.4, "carbs": 5, "fats": 0.1, "is_elite": False, "goal": "fat_loss"},
        {"name": "Cheddar Cheese", "calories": 403, "protein": 25, "carbs": 1.3, "fats": 33, "is_elite": False, "goal": "muscle_gain"},
        {"name": "Mozzarella", "calories": 280, "protein": 28, "carbs": 2.2, "fats": 17, "is_elite": False, "goal": "muscle_gain"},
    ],
    "Indian Foods": [
        {"name": "Paneer", "calories": 296, "protein": 18, "carbs": 1.2, "fats": 25, "is_elite": True, "goal": "muscle_gain"},
        {"name": "Dal (Lentils)", "calories": 116, "protein": 9, "carbs": 20, "fats": 0.4, "is_elite": True, "goal": "fat_loss"},
        {"name": "Roti (Whole Wheat)", "calories": 297, "protein": 11, "carbs": 54, "fats": 3.7, "is_elite": False, "goal": "maintenance"},
        {"name": "Chickpeas", "calories": 364, "protein": 19, "carbs": 61, "fats": 6, "is_elite": True, "goal": "athletic"},
        {"name": "Basmati Rice", "calories": 357, "protein": 7.5, "carbs": 79, "fats": 0.6, "is_elite": False, "goal": "muscle_gain"},
    ],
    "Supplements": [
        {"name": "Creatine Monohydrate", "calories": 0, "protein": 0, "carbs": 0, "fats": 0, "is_elite": True, "goal": "muscle_gain"},
        {"name": "BCAAs", "calories": 0, "protein": 0, "carbs": 0, "fats": 0, "is_elite": True, "goal": "athletic"},
        {"name": "Pre-Workout", "calories": 5, "protein": 0, "carbs": 1, "fats": 0, "is_elite": False, "goal": "athletic"},
    ],
}


def seed_exercises(db: Session):
    """Seed exercise categories and items"""
    logger.info("🏋️  Seeding exercises...")
    
    for muscle_group, difficulty_levels in EXERCISE_DATA.items():
        # Create or get category
        category = db.query(models.ExerciseCategory).filter(
            models.ExerciseCategory.name == muscle_group
        ).first()
        
        if not category:
            category = models.ExerciseCategory(
                name=muscle_group,
                description=f"Exercises targeting {muscle_group.lower()}"
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            logger.info(f"  ✅ Created category: {muscle_group}")
        
        # Add exercises for each difficulty
        for difficulty, exercises in difficulty_levels.items():
            for ex_data in exercises:
                # Check if exercise already exists
                existing = db.query(models.ExerciseItem).filter(
                    models.ExerciseItem.name == ex_data['name'],
                    models.ExerciseItem.category_id == category.id
                ).first()
                
                if not existing:
                    exercise = models.ExerciseItem(
                        category_id=category.id,
                        name=ex_data['name'],
                        targeted_muscle=muscle_group,
                        difficulty=difficulty,
                        equipment=ex_data['equipment'],
                        calories_per_min=ex_data['calories_per_min'],
                        calories_per_rep=ex_data['calories_per_rep'],
                        description=f"{difficulty.capitalize()} {muscle_group.lower()} exercise",
                        fitness_goal=ex_data['goal']
                    )
                    db.add(exercise)
    
    db.commit()
    
    total = db.query(models.ExerciseItem).count()
    logger.info(f"  ✅ Total exercises in database: {total}")


def seed_female_exercises(db: Session):
    """Seed female-specific exercises"""
    logger.info("👩 Seeding female-specific exercises...")
    
    # Create Female-Specific category
    category = db.query(models.ExerciseCategory).filter(
        models.ExerciseCategory.name == "Female-Specific"
    ).first()
    
    if not category:
        category = models.ExerciseCategory(
            name="Female-Specific",
            description="Exercises designed for female health and cycle phases"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
    
    for ex_data in FEMALE_EXERCISES:
        existing = db.query(models.ExerciseItem).filter(
            models.ExerciseItem.name == ex_data['name']
        ).first()
        
        if not existing:
            exercise = models.ExerciseItem(
                category_id=category.id,
                name=ex_data['name'],
                targeted_muscle=ex_data['muscle'],
                difficulty=ex_data['difficulty'],
                equipment="Various",
                calories_per_min=ex_data.get('calories_per_min', 5.0),
                calories_per_rep=ex_data.get('calories_per_rep', 0.3),
                description=f"Suitable for {ex_data['phase']} phase",
                fitness_goal="maintenance"
            )
            db.add(exercise)
    
    db.commit()
    logger.info(f"  ✅ Added {len(FEMALE_EXERCISES)} female-specific exercises")


def seed_foods(db: Session):
    """Seed food categories and items"""
    logger.info("🍎 Seeding foods...")
    
    for food_category, foods in FOOD_DATA.items():
        # Create or get category
        category = db.query(models.FoodCategory).filter(
            models.FoodCategory.name == food_category
        ).first()
        
        if not category:
            category = models.FoodCategory(
                name=food_category,
                description=f"{food_category} for nutrition tracking"
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            logger.info(f"  ✅ Created food category: {food_category}")
        
        # Add foods
        for food_data in foods:
            # Check if food already exists
            existing = db.query(models.FoodItem).filter(
                models.FoodItem.name == food_data['name'],
                models.FoodItem.category_id == category.id
            ).first()
            
            if not existing:
                food = models.FoodItem(
                    category_id=category.id,
                    name=food_data['name'],
                    calories=food_data['calories'],
                    protein=food_data['protein'],
                    carbs=food_data['carbs'],
                    fats=food_data['fats'],
                    is_elite=food_data['is_elite'],
                    recommended_for_goal=food_data['goal']
                )
                db.add(food)
    
    db.commit()
    
    total = db.query(models.FoodItem).count()
    logger.info(f"  ✅ Total foods in database: {total}")


def verify_seeding(db: Session):
    """Verify that data was seeded correctly"""
    logger.info("\n🔍 Verifying seeded data...")
    
    # Count exercises by category
    exercise_cats = db.query(models.ExerciseCategory).all()
    logger.info(f"\n📊 Exercise Categories: {len(exercise_cats)}")
    for cat in exercise_cats:
        count = len(cat.exercises)
        logger.info(f"  • {cat.name}: {count} exercises")
    
    # Count exercises by difficulty
    for difficulty in ['beginner', 'intermediate', 'advanced']:
        count = db.query(models.ExerciseItem).filter(
            models.ExerciseItem.difficulty == difficulty
        ).count()
        logger.info(f"  • {difficulty.capitalize()}: {count} exercises")
    
    # Count foods by category
    food_cats = db.query(models.FoodCategory).all()
    logger.info(f"\n📊 Food Categories: {len(food_cats)}")
    for cat in food_cats:
        count = len(cat.foods)
        logger.info(f"  • {cat.name}: {count} items")
    
    # Count elite foods
    elite_count = db.query(models.FoodItem).filter(
        models.FoodItem.is_elite == True
    ).count()
    logger.info(f"  • Elite Foods: {elite_count}")
    
    logger.info("\n✅ Verification complete!")


def main():
    """Main seeding function"""
    logger.info("\n" + "="*60)
    logger.info("🌱 NEON DATABASE SEEDING SCRIPT")
    logger.info("="*60)
    
    db = SessionLocal()
    
    try:
        # Ensure tables exist
        logger.info("\n📋 Ensuring database tables exist...")
        models.Base.metadata.create_all(bind=db.get_bind())
        logger.info("  ✅ Tables verified")
        
        # Seed exercises
        seed_exercises(db)
        
        # Seed female-specific exercises
        seed_female_exercises(db)
        
        # Seed foods
        seed_foods(db)
        
        # Verify
        verify_seeding(db)
        
        logger.info("\n" + "="*60)
        logger.info("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("\n💡 Next Steps:")
        logger.info("  1. Start backend: uvicorn main:app --reload")
        logger.info("  2. Test API: GET /api/exercises/library")
        logger.info("  3. Test API: GET /api/food/library")
        logger.info("  4. Run calorie tracker tests: python test_calorie_system.py")
        
    except Exception as e:
        logger.error(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
