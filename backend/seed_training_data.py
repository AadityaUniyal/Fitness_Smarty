"""
Huge Dataset Seeder

Generates a large synthetic dataset of food items with nutritional variations
to simulate a 'verified' training branch in the database.
"""

import sys
import os
from pathlib import Path
import random
from sqlalchemy.orm import Session
from app.database import get_training_db, Base, engine
from app.models import FoodTrainingSample

# Ensure tables exist (will be done in seed_training_data via bound engine)

# Expanded Food Templates for "Huge Data" diversity
FOOD_TEMPLATES = {
    # Proteins
    "Grilled Chicken Breast": {"cal": (120, 180), "pro": (25, 35), "carb": (0, 2), "fat": (2, 5)},
    "Fried Chicken": {"cal": (250, 400), "pro": (15, 25), "carb": (10, 20), "fat": (15, 25)},
    "Steak": {"cal": (200, 350), "pro": (20, 30), "carb": (0, 2), "fat": (10, 20)},
    "Salmon": {"cal": (180, 250), "pro": (20, 25), "carb": (0, 1), "fat": (10, 15)},
    "Tofu": {"cal": (80, 120), "pro": (8, 12), "carb": (2, 5), "fat": (4, 8)},
    "Egg (Boiled)": {"cal": (70, 80), "pro": (6, 7), "carb": (0, 1), "fat": (5, 6)},
    "Egg (Fried)": {"cal": (90, 110), "pro": (6, 7), "carb": (0, 1), "fat": (7, 9)},
    
    # Carbs
    "White Rice (1 cup)": {"cal": (180, 220), "pro": (3, 5), "carb": (40, 50), "fat": (0, 1)},
    "Brown Rice (1 cup)": {"cal": (200, 240), "pro": (4, 6), "carb": (40, 50), "fat": (1, 2)},
    "Pasta": {"cal": (200, 250), "pro": (7, 9), "carb": (40, 60), "fat": (1, 2)},
    "Oatmeal": {"cal": (140, 180), "pro": (5, 7), "carb": (25, 35), "fat": (2, 4)},
    "Potato (Baked)": {"cal": (120, 180), "pro": (3, 5), "carb": (30, 40), "fat": (0, 1)},
    "Sweet Potato": {"cal": (100, 150), "pro": (2, 4), "carb": (25, 35), "fat": (0, 1)},
    "Quinoa": {"cal": (200, 240), "pro": (6, 10), "carb": (35, 45), "fat": (3, 5)},
    
    # Fast Food / Meals
    "Pizza Slice": {"cal": (250, 400), "pro": (10, 15), "carb": (30, 40), "fat": (10, 20)},
    "Cheeseburger": {"cal": (300, 600), "pro": (15, 30), "carb": (30, 50), "fat": (15, 30)},
    "Fries (Medium)": {"cal": (300, 450), "pro": (3, 5), "carb": (40, 60), "fat": (15, 25)},
    "Burrito": {"cal": (500, 900), "pro": (20, 40), "carb": (60, 100), "fat": (20, 40)},
    "Caesar Salad": {"cal": (300, 500), "pro": (5, 10), "carb": (10, 20), "fat": (25, 40)},
    
    # Fruits & Veg
    "Apple": {"cal": (50, 100), "pro": (0, 1), "carb": (15, 25), "fat": (0, 1)},
    "Banana": {"cal": (90, 120), "pro": (1, 2), "carb": (20, 30), "fat": (0, 1)},
    "Avocado": {"cal": (200, 300), "pro": (2, 4), "carb": (10, 15), "fat": (20, 30)},
    "Broccoli": {"cal": (30, 50), "pro": (2, 4), "carb": (5, 10), "fat": (0, 1)},
    
    # Snacks
    "Almonds (Handful)": {"cal": (150, 180), "pro": (5, 7), "carb": (3, 6), "fat": (12, 16)},
    "Greek Yogurt": {"cal": (100, 150), "pro": (10, 20), "carb": (4, 8), "fat": (0, 5)},
    "Protein Bar": {"cal": (180, 250), "pro": (15, 25), "carb": (20, 30), "fat": (5, 10)},
}

def generate_samples(start_id, count=10000):
    samples = []
    print(f"Generating {count} synthetic training samples...")
    
    flavors = ["Spicy", "Sweet", "Grilled", "Baked", "Fried", "Homemade", "Restaurant", "Organic"]
    
    for i in range(count):
        base_name = random.choice(list(FOOD_TEMPLATES.keys()))
        template = FOOD_TEMPLATES[base_name]
        
        # Add random variation to nutritional values
        cal_var = random.uniform(0.8, 1.2)
        
        cal = random.uniform(*template["cal"]) * cal_var
        pro = random.uniform(*template["pro"]) * cal_var
        carb = random.uniform(*template["carb"]) * cal_var
        fat = random.uniform(*template["fat"]) * cal_var
        
        # Sometimes add a modifier to the name
        if random.random() > 0.7:
            name = f"{random.choice(flavors)} {base_name}"
        else:
            name = base_name
            
        samples.append(FoodTrainingSample(
            label=name,
            calories=round(cal, 1),
            protein=round(pro, 1),
            carbs=round(carb, 1),
            fats=round(fat, 1),
            source="synthetic_huge_data",
            verified=True,
            image_signature=f"synthetic_{start_id + i}"
        ))
        
    return samples

def seed_training_data():
    # Use training DB session
    db = next(get_training_db())
    
    # Ensure tables exist in the TRAINING database
    # This fixes the issue where tables were only created in Main DB
    Base.metadata.create_all(bind=db.get_bind())
    
    try:
        # Check existing count
        count = db.query(FoodTrainingSample).count()
        print(f"Current training set size: {count}")
        
        target = 10000
        if count < target:
            to_add = target - count
            print(f"Adding {to_add} records to reach {target}...")
            
            # Batch insert to avoid memory issues
            batch_size = 1000
            for i in range(0, to_add, batch_size):
                batch_count = min(batch_size, to_add - i)
                new_samples = generate_samples(count + i, batch_count)
                db.bulk_save_objects(new_samples)
                db.commit()
                print(f"  Mapped {i + batch_count}/{to_add}")
                
            print(f"✅ Successfully populated training DB with huge data.")
        else:
            print("Training set is already huge (>= 10000).")
            
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_training_data()
