"""
Demo Script: AI Training Pipeline

This script demonstrates the complete ML training workflow:
1. Generate synthetic training data
2. Train health classifier
3. Make predictions
4. Run user clustering
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.training.data_collector import DataCollector
from app.training.train_health_classifier import HealthClassifierTrainer
from app.training.user_clustering import UserClusteringAnalyzer
import numpy as np


def generate_demo_data():
    """Generate synthetic training data for demonstration"""
    print("🎲 Generating synthetic training data...\n")
    
    collector = DataCollector()
    
    # Create diverse user profiles
    user_profiles = [
        {"goals": ["weight_loss"], "age": 28, "weight_kg": 85, "height_cm": 175, "activity_level": "moderate"},
        {"goals": ["muscle_gain"], "age": 24, "weight_kg": 72, "height_cm": 180, "activity_level": "very_active"},
        {"goals": ["maintenance"], "age": 35, "weight_kg": 68, "height_cm": 165, "activity_level": "light"},
        {"goals": ["athletic_performance"], "age": 22, "weight_kg": 75, "height_cm": 178, "activity_level": "very_active"},
    ]
    
    # Create meal examples
    meals_good = [
        {"calories": 450, "protein_g": 35, "carbs_g": 45, "fat_g": 12, "fiber_g": 8, "sugar_g": 5, "detected_foods": ["chicken", "broccoli", "rice"]},
        {"calories": 520, "protein_g": 42, "carbs_g": 50, "fat_g": 15, "fiber_g": 10, "sugar_g": 6, "detected_foods": ["salmon", "quinoa", "asparagus"]},
        {"calories": 380, "protein_g": 30, "carbs_g": 40, "fat_g": 10, "fiber_g": 12, "sugar_g": 4, "detected_foods": ["tofu", "vegetables", "brown_rice"]},
    ]
    
    meals_bad = [
        {"calories": 850, "protein_g": 15, "carbs_g": 120, "fat_g": 35, "fiber_g": 2, "sugar_g": 45, "detected_foods": ["pizza", "soda"]},
        {"calories": 720, "protein_g": 12, "carbs_g": 90, "fat_g": 30, "fiber_g": 1, "sugar_g": 38, "detected_foods": ["burger", "fries", "milkshake"]},
        {"calories": 950, "protein_g": 20, "carbs_g": 110, "fat_g": 42, "fiber_g": 3, "sugar_g": 52, "detected_foods": ["pasta_alfredo", "garlic_bread", "dessert"]},
    ]
    
    # Generate 30 training samples
    for i in range(30):
        profile = user_profiles[i % len(user_profiles)]
        
        if i % 2 == 0:
            # Good meal
            meal = meals_good[i % len(meals_good)]
            feedback = "good_for_me"
        else:
            # Bad meal
            meal = meals_bad[i % len(meals_bad)]
            feedback = "not_good_for_me"
        
        collector.save_health_feedback(
            meal_log_id=f"demo_meal_{i}",
            user_id=f"demo_user_{i % 4}",
            user_profile=profile,
            meal_composition=meal,
            ai_recommendation="",
            user_feedback=feedback,
            reason=None
        )
    
    stats = collector.get_dataset_stats()
    print(f"✅ Generated {stats['health_feedback']} training samples\n")
    return stats


def train_classifier():
    """Train the health classifier"""
    print("🧠 Training health classifier...\n")
    
    trainer = HealthClassifierTrainer()
    success = trainer.train_model(test_size=0.2)
    
    if success:
        print("\n✅ Training complete!\n")
    else:
        print("\n❌ Training failed\n")
    
    return trainer


def demo_predictions(trainer):
    """Demo the trained classifier"""
    print("🔮 Testing predictions...\n")
    
    test_cases = [
        {
            "name": "Healthy Meal (Weight Loss Goal)",
            "profile": {"goals": ["weight_loss"], "age": 30, "weight_kg": 80, "height_cm": 170, "activity_level": "moderate"},
            "meal": {"calories": 420, "protein_g": 38, "carbs_g": 42, "fat_g": 11, "fiber_g": 9, "sugar_g": 5, "detected_foods": ["chicken", "salad"]}
        },
        {
            "name": "High-Calorie Meal (Weight Loss Goal)",
            "profile": {"goals": ["weight_loss"], "age": 30, "weight_kg": 80, "height_cm": 170, "activity_level": "moderate"},
            "meal": {"calories": 1200, "protein_g": 25, "carbs_g": 150, "fat_g": 50, "fiber_g": 3, "sugar_g": 60, "detected_foods": ["burger", "fries", "soda"]}
        },
        {
            "name": "Protein-Rich Meal (Muscle Gain Goal)",
            "profile": {"goals": ["muscle_gain"], "age": 25, "weight_kg": 75, "height_cm": 180, "activity_level": "very_active"},
            "meal": {"calories": 650, "protein_g": 55, "carbs_g": 60, "fat_g": 18, "fiber_g": 8, "sugar_g": 8, "detected_foods": ["steak", "sweet_potato", "broccoli"]}
        }
    ]
    
    for test in test_cases:
        print(f"Test Case: {test['name']}")
        print(f"  Profile: {test['profile']['goals'][0]}, {test['profile']['activity_level']}")
        print(f"  Meal: {test['meal']['calories']} cal, {test['meal']['protein_g']}g protein")
        
        result = trainer.predict(test['profile'], test['meal'])
        
        print(f"  → {result['recommendation']}\n")


def demo_clustering():
    """Demo user clustering"""
    print("👥 Running user clustering analysis...\n")
    
    # Generate synthetic user data
    np.random.seed(42)
    synthetic_users = []
    
    for i in range(50):
        synthetic_users.append({
            'avg_daily_calories': np.random.normal(2000, 400),
            'avg_protein_ratio': np.random.normal(0.3, 0.05),
            'avg_carb_ratio': np.random.normal(0.4, 0.05),
            'avg_fat_ratio': np.random.normal(0.3, 0.05),
            'meals_per_day': np.random.choice([2, 3, 4, 5]),
            'bmi': np.random.normal(24, 4),
            'age_group': np.random.choice([1, 2, 3, 4, 5]),
            'activity_level': np.random.choice([1, 2, 3, 4, 5]),
            'primary_goal': np.random.choice([0, 1, 2, 3, 4])
        })
    
    analyzer = UserClusteringAnalyzer(n_clusters=3)
    analyzer.perform_clustering(synthetic_users)
    
    print("\n✅ Clustering complete!\n")


def main():
    print("="*70)
    print("  AI TRAINING PIPELINE DEMO")
    print("  Fitness Smarty - Market-Leading ML Implementation")
    print("="*70)
    print()
    
    # Step 1: Generate data
    stats = generate_demo_data()
    
    # Step 2: Train classifier
    if stats['health_feedback'] >= 10:
        trainer = train_classifier()
        
        # Step 3: Demo predictions
        demo_predictions(trainer)
    else:
        print("⚠️  Not enough data to train classifier")
    
    # Step 4: Demo clustering
    demo_clustering()
    
    print("="*70)
    print("🎉 Demo Complete!")
    print()
    print("Next steps:")
    print("  1. Integrate these APIs into your frontend")
    print("  2. Collect real user feedback as they use the app")
    print("  3. Retrain models weekly/daily to improve accuracy")
    print("  4. Monitor dataset stats at /api/training/dataset/stats")
    print("="*70)


if __name__ == "__main__":
    main()
