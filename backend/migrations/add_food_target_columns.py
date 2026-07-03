import sqlite3
import os

def migrate_and_seed():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'smarty_neural_core.db')
    print(f"Connecting to database at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Add columns to food_items
    try:
        cursor.execute("ALTER TABLE food_items ADD COLUMN target_muscle_group VARCHAR")
        print("Column 'target_muscle_group' added.")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")

    try:
        cursor.execute("ALTER TABLE food_items ADD COLUMN recommended_for_goal VARCHAR")
        print("Column 'recommended_for_goal' added.")
    except sqlite3.OperationalError as e:
        print(f"Note: {e}")
        
    # 2. Update existing food items
    # We will provide some default values for known foods
    updates = [
        # Muscle gain & specific muscles
        ("chicken", "muscle_gain", "all"),
        ("beef", "muscle_gain", "all"),
        ("salmon", "muscle_gain", "all"),
        ("tuna", "muscle_gain", "all"),
        ("whey", "muscle_gain", "all"),
        ("eggs", "muscle_gain", "all"),
        ("egg_whites", "muscle_gain", "abs"),
        
        # Energy & workout prep
        ("oats", "general", "all"),
        ("banana", "general", "legs"),
        ("sweet_potato", "muscle_gain", "legs"),
        
        # Weight loss
        ("broccoli", "weight_loss", "abs"),
        ("spinach", "weight_loss", "abs"),
        ("asparagus", "weight_loss", "abs"),
        ("cauliflower", "weight_loss", "general"),
        ("quinoa", "weight_loss", "all"),
    ]
    
    for food_term, goal, muscle in updates:
        cursor.execute(
            "UPDATE food_items SET target_muscle_group = ?, recommended_for_goal = ? WHERE name LIKE ?",
            (muscle, goal, f"%{food_term}%")
        )
        print(f"Updated food items matching '{food_term}' -> Goal: {goal}, Muscle: {muscle}")
        
    # Set defaults for any remaining rows
    cursor.execute(
        "UPDATE food_items SET target_muscle_group = 'general', recommended_for_goal = 'general' "
        "WHERE target_muscle_group IS NULL OR recommended_for_goal IS NULL"
    )
    
    conn.commit()
    conn.close()
    print("Migration and seeding complete.")

if __name__ == "__main__":
    migrate_and_seed()
