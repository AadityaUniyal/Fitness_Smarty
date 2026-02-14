"""
Synthetic Dataset Generator for Meal Analysis

Generates 10,000+ realistic meal records with:
- Food combinations
- Nutritional values
- User profiles
- Success labels (good/bad for user)
"""

import json
import random
from pathlib import Path
from typing import List, Dict
import numpy as np


class MealDatasetGenerator:
    """Generates realistic synthetic meal data for training"""
    
    def __init__(self):
        # Food database with realistic nutrition per 100g
        self.foods = {
            # Proteins
            'chicken_breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
            'salmon': {'calories': 208, 'protein': 20, 'carbs': 0, 'fat': 13, 'fiber': 0},
            'eggs': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0},
            'tofu': {'calories': 76, 'protein': 8, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3},
            'beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 15, 'fiber': 0},
            'turkey': {'calories': 135, 'protein': 30, 'carbs': 0, 'fat': 0.7, 'fiber': 0},
            'tuna': {'calories': 132, 'protein': 28, 'carbs': 0, 'fat': 1.3, 'fiber': 0},
            'greek_yogurt': {'calories': 97, 'protein': 10, 'carbs': 3.6, 'fat': 5, 'fiber': 0},
            
            # Carbs
            'brown_rice': {'calories': 111, 'protein': 2.6, 'carbs': 23, 'fat': 0.9, 'fiber': 1.8},
            'white_rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
            'quinoa': {'calories': 120, 'protein': 4.4, 'carbs': 21, 'fat': 1.9, 'fiber': 2.8},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'fiber': 1.8},
            'sweet_potato': {'calories': 86, 'protein': 1.6, 'carbs': 20, 'fat': 0.1, 'fiber': 3},
            'oats': {'calories': 389, 'protein': 16.9, 'carbs': 66, 'fat': 6.9, 'fiber': 10.6},
            'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2, 'fiber': 2.7},
            
            # Vegetables
            'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6},
            'spinach': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2},
            'carrots': {'calories': 41, 'protein': 0.9, 'carbs': 10, 'fat': 0.2, 'fiber': 2.8},
            'bell_pepper': {'calories': 31, 'protein': 1, 'carbs': 6, 'fat': 0.3, 'fiber': 2.1},
            'asparagus': {'calories': 20, 'protein': 2.2, 'carbs': 3.9, 'fat': 0.1, 'fiber': 2.1},
            'salad_mix': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2, 'fiber': 1.5},
            
            # Fats
            'avocado': {'calories': 160, 'protein': 2, 'carbs': 8.5, 'fat': 14.7, 'fiber': 6.7},
            'olive_oil': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100, 'fiber': 0},
            'nuts': {'calories': 607, 'protein': 20, 'carbs': 21, 'fat': 54, 'fiber': 8},
            'cheese': {'calories': 402, 'protein': 25, 'carbs': 1.3, 'fat': 33, 'fiber': 0},
            
            # Processed/Less Healthy
            'pizza': {'calories': 266, 'protein': 11, 'carbs': 33, 'fat': 10, 'fiber': 2.3},
            'burger': {'calories': 295, 'protein': 17, 'carbs': 24, 'fat': 14, 'fiber': 1.5},
            'fries': {'calories': 312, 'protein': 3.4, 'carbs': 41, 'fat': 15, 'fiber': 3.8},
            'ice_cream': {'calories': 207, 'protein': 3.5, 'carbs': 24, 'fat': 11, 'fiber': 0.7},
            'soda': {'calories': 41, 'protein': 0, 'carbs': 10.6, 'fat': 0, 'fiber': 0},
            'chips': {'calories': 536, 'protein': 6.6, 'carbs': 53, 'fat': 34, 'fiber': 4.4},
        }
        
        # Meal templates
        self.healthy_combos = [
            ['chicken_breast', 'brown_rice', 'broccoli'],
            ['salmon', 'quinoa', 'asparagus'],
            ['turkey', 'sweet_potato', 'spinach'],
            ['tofu', 'brown_rice', 'bell_pepper'],
            ['eggs', 'oats', 'spinach'],
            ['tuna', 'quinoa', 'salad_mix'],
            ['greek_yogurt', 'oats', 'nuts'],
        ]
        
        self.unhealthy_combos = [
            ['burger', 'fries', 'soda'],
            ['pizza', 'soda', 'ice_cream'],
            ['pasta', 'cheese', 'bread'],
            ['fries', 'burger', 'chips'],
        ]
        
        # User goals
        self.goals = ['weight_loss', 'muscle_gain', 'maintenance', 'athletic_performance']
        self.activity_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
    
    def generate_meal(self, healthy: bool = True) -> Dict:
        """Generate a single meal"""
        if healthy:
            foods = random.choice(self.healthy_combos)
        else:
            foods = random.choice(self.unhealthy_combos)
        
        # Random portions (in grams)
        portions = {
            food: random.randint(80, 250) for food in foods
        }
        
        # Calculate total nutrition
        total_nutrition = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'fiber_g': 0
        }
        
        for food, grams in portions.items():
            nutrition = self.foods[food]
            multiplier = grams / 100.0
            total_nutrition['calories'] += nutrition['calories'] * multiplier
            total_nutrition['protein_g'] += nutrition['protein'] * multiplier
            total_nutrition['carbs_g'] += nutrition['carbs'] * multiplier
            total_nutrition['fat_g'] += nutrition['fat'] * multiplier
            total_nutrition['fiber_g'] += nutrition['fiber'] * multiplier
        
        return {
            'foods': list(portions.keys()),
            'portions_g': portions,
            'nutrition': total_nutrition
        }
    
    def generate_user_profile(self) -> Dict:
        """Generate a realistic user profile"""
        age = random.randint(18, 65)
        is_male = random.choice([True, False])
        
        # Realistic height and weight distributions
        if is_male:
            height_cm = int(np.random.normal(175, 7))
            weight_kg = int(np.random.normal(80, 15))
        else:
            height_cm = int(np.random.normal(162, 6))
            weight_kg = int(np.random.normal(65, 12))
        
        # BMI-based goal assignment (more realistic)
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        if bmi < 18.5:
            goal = random.choice(['weight_gain', 'muscle_gain'])
        elif bmi > 25:
            goal = random.choice(['weight_loss', 'athletic_performance'])
        else:
            goal = random.choice(self.goals)
        
        return {
            'age': age,
            'gender': 'male' if is_male else 'female',
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'bmi': round(bmi, 1),
            'goal': goal,
            'activity_level': random.choice(self.activity_levels)
        }
    
    def is_meal_good_for_user(self, meal: Dict, profile: Dict) -> bool:
        """
        Determine if meal aligns with user's goal
        (This creates the training labels)
        """
        nutrition = meal['nutrition']
        calories = nutrition['calories']
        protein = nutrition['protein_g']
        carbs = nutrition['carbs_g']
        fat = nutrition['fat_g']
        
        goal = profile['goal']
        activity = profile['activity_level']
        bmi = profile['bmi']
        
        # Weight loss logic
        if goal == 'weight_loss':
            if calories > 600:
                return False
            if protein < 25:
                return False
            if fat > 20:
                return False
            return True
        
        # Muscle gain logic
        elif goal == 'muscle_gain':
            if protein < 30:
                return False
            if calories < 450:
                return False
            if carbs < 40:
                return False
            return True
        
        # Athletic performance
        elif goal == 'athletic_performance':
            if protein < 25:
                return False
            if carbs < 50:
                return False
            if calories < 500:
                return False
            return True
        
        # Maintenance
        else:
            if 400 < calories < 700 and protein > 20:
                return True
            return False
    
    def generate_dataset(self, n_samples: int = 10000) -> List[Dict]:
        """Generate full dataset"""
        dataset = []
        
        print(f"Generating {n_samples} training samples...")
        
        for i in range(n_samples):
            if i % 1000 == 0:
                print(f"  {i}/{n_samples}...")
            
            # Generate user
            profile = self.generate_user_profile()
            
            # Generate meal (70% healthy, 30% unhealthy)
            is_healthy = random.random() < 0.7
            meal = self.generate_meal(healthy=is_healthy)
            
            # Determine label
            label = self.is_meal_good_for_user(meal, profile)
            
            # Create training record
            record = {
                'user_profile': profile,
                'meal': meal,
                'label': 1 if label else 0
            }
            
            dataset.append(record)
        
        print(f"✓ Generated {n_samples} samples")
        return dataset
    
    def save_dataset(self, dataset: List[Dict], output_file: str):
        """Save dataset to JSONL file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for record in dataset:
                f.write(json.dumps(record) + '\n')
        
        print(f"✓ Dataset saved to: {output_path}")
        
        # Print statistics
        positive = sum(1 for r in dataset if r['label'] == 1)
        negative = len(dataset) - positive
        print(f"\nDataset Statistics:")
        print(f"  Total samples: {len(dataset)}")
        print(f"  Positive (good meals): {positive} ({positive/len(dataset)*100:.1f}%)")
        print(f"  Negative (bad meals): {negative} ({negative/len(dataset)*100:.1f}%)")


if __name__ == "__main__":
    generator = MealDatasetGenerator()
    
    # Generate 10,000 training samples
    dataset = generator.generate_dataset(n_samples=10000)
    
    # Save to file
    generator.save_dataset(dataset, "app/training/datasets/synthetic_meals.jsonl")
    
    print("\n✅ Dataset generation complete!")
    print("Next step: Run train_neural_model.py to train the model")
