"""
Advanced Recommendation Engine

Next-level features:
1. Goal Timeline Predictor - "Reach your goal in X weeks"
2. Smart Meal Recommender - Suggests what to eat next
3. Food Swap Engine - "Replace X with Y"
4. Portion Optimizer - Perfect serving sizes
5. Meal Timing Intelligence - When to eat based on activity
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math


class GoalPredictor:
    """Predict when user will reach their goal based on current progress"""
    
    def __init__(self):
        # Safe weight loss/gain rates (kg per week)
        self.safe_rates = {
            'weight_loss': -0.5,  # 0.5kg loss per week
            'weight_gain': 0.25,  # 0.25kg gain per week
            'muscle_gain': 0.15   # 0.15kg muscle per week
        }
    
    def predict_timeline(self, current_weight: float, target_weight: float, 
                         goal: str, avg_daily_deficit: float) -> Dict:
        """
        Predict timeline to reach goal
        
        Uses thermodynamics: 1kg fat ≈ 7700 calories
        
        Args:
            current_weight: Current weight in kg
            target_weight: Target weight in kg
            goal: Goal type (weight_loss, weight_gain, muscle_gain)
            avg_daily_deficit: Average daily calorie deficit/surplus
        
        Returns:
            Timeline prediction with dates and milestones
        """
        weight_diff = target_weight - current_weight
        
        # Calculate weeks needed based on safe rate
        safe_rate = self.safe_rates.get(goal, -0.5)
        weeks_needed_safe = abs(weight_diff / safe_rate) if safe_rate != 0 else 0
        
        # Calculate weeks based on actual deficit
        # 7700 calories deficit = 1kg fat loss
        weekly_deficit = avg_daily_deficit * 7
        kg_per_week_actual = weekly_deficit / 7700 if weekly_deficit != 0 else 0
        weeks_needed_actual = abs(weight_diff / kg_per_week_actual) if kg_per_week_actual != 0 else float('inf')
        
        # Use the safer estimate
        weeks_needed = max(weeks_needed_safe, weeks_needed_actual)
        
        # Calculate milestones (25%, 50%, 75%, 100%)
        milestones = []
        for pct in [0.25, 0.5, 0.75, 1.0]:
            milestone_weeks = weeks_needed * pct
            milestone_date = datetime.utcnow() + timedelta(weeks=milestone_weeks)
            milestone_weight = current_weight + (weight_diff * pct)
            
            milestones.append({
                'percentage': int(pct * 100),
                'weeks_from_now': round(milestone_weeks, 1),
                'date': milestone_date.strftime('%Y-%m-%d'),
                'weight_kg': round(milestone_weight, 1)
            })
        
        # Estimate confidence based on deficit consistency
        confidence = 'high' if abs(avg_daily_deficit) > 200 else 'medium' if abs(avg_daily_deficit) > 100 else 'low'
        
        return {
            'current_weight_kg': round(current_weight, 1),
            'target_weight_kg': round(target_weight, 1),
            'weight_to_lose_gain': round(abs(weight_diff), 1),
            'estimated_weeks': round(weeks_needed, 1),
            'estimated_months': round(weeks_needed / 4.33, 1),
            'target_date': (datetime.utcnow() + timedelta(weeks=weeks_needed)).strftime('%Y-%m-%d'),
            'weekly_rate_kg': round(safe_rate, 2),
            'daily_deficit_needed': round(safe_rate * 7700 / 7, 0),
            'current_daily_deficit': round(avg_daily_deficit, 0),
            'on_track': abs(avg_daily_deficit) >= abs(safe_rate * 1100),  # 1100 = 7700/7
            'confidence': confidence,
            'milestones': milestones
        }


class MealRecommender:
    """Suggest optimal meals based on remaining daily macros"""
    
    def __init__(self):
        # Meal templates with macro profiles
        self.meal_templates = {
            'high_protein_low_carb': {
                'name': 'Grilled Chicken Salad',
                'foods': ['chicken_breast', 'mixed_greens', 'avocado', 'olive_oil'],
                'macros': {'protein_g': 45, 'carbs_g': 15, 'fat_g': 20, 'calories': 420}
            },
            'high_protein_high_carb': {
                'name': 'Chicken & Rice Bowl',
                'foods': ['chicken_breast', 'brown_rice', 'vegetables'],
                'macros': {'protein_g': 40, 'carbs_g': 55, 'fat_g': 12, 'calories': 480}
            },
            'balanced': {
                'name': 'Salmon with Quinoa',
                'foods': ['salmon', 'quinoa', 'asparagus', 'lemon'],
                'macros': {'protein_g': 35, 'carbs_g': 45, 'fat_g': 18, 'calories': 480}
            },
            'low_calorie': {
                'name': 'Egg White Omelette',
                'foods': ['egg_whites', 'spinach', 'tomatoes', 'mushrooms'],
                'macros': {'protein_g': 25, 'carbs_g': 12, 'fat_g': 5, 'calories': 180}
            },
            'post_workout': {
                'name': 'Protein Smoothie Bowl',
                'foods': ['protein_powder', 'banana', 'oats', 'berries', 'greek_yogurt'],
                'macros': {'protein_g': 38, 'carbs_g': 60, 'fat_g': 8, 'calories': 450}
            }
        }
    
    def recommend_next_meal(self, daily_targets: Dict, consumed_so_far: Dict, 
                           time_of_day: str = 'lunch') -> Dict:
        """
        Recommend next meal based on remaining macros
        
        Uses optimization to find best-fit meal
        
        Args:
            daily_targets: Target macros for the day
            consumed_so_far: What user has eaten today
            time_of_day: breakfast, lunch, dinner, snack
        
        Returns:
            Recommended meal with reasoning
        """
        # Calculate remaining macros
        remaining = {
            'protein_g': daily_targets['protein_g'] - consumed_so_far.get('protein_g', 0),
            'carbs_g': daily_targets['carbs_g'] - consumed_so_far.get('carbs_g', 0),
            'fat_g': daily_targets['fat_g'] - consumed_so_far.get('fat_g', 0),
            'calories': daily_targets['target_calories'] - consumed_so_far.get('calories', 0)
        }
        
        # Score each meal template
        best_meal = None
        best_score = float('-inf')
        
        for meal_type, meal_data in self.meal_templates.items():
            macros = meal_data['macros']
            
            # Calculate fit score (minimize difference from remaining)
            protein_diff = abs(macros['protein_g'] - remaining['protein_g'])
            carbs_diff = abs(macros['carbs_g'] - remaining['carbs_g'])
            fat_diff = abs(macros['fat_g'] - remaining['fat_g'])
            cal_diff = abs(macros['calories'] - remaining['calories'])
            
            # Weighted scoring
            score = -(protein_diff * 2 + carbs_diff * 1.5 + fat_diff * 1.5 + cal_diff * 0.5)
            
            if score > best_score:
                best_score = score
                best_meal = {
                    'type': meal_type,
                    **meal_data,
                    'fit_score': round(100 + score / 10, 1)  # Normalize to 0-100
                }
        
        return {
            'recommended_meal': best_meal,
            'remaining_macros': {k: round(v, 1) for k, v in remaining.items()},
            'reason': self._generate_reason(remaining, best_meal['macros']),
            'alternative_options': self._get_alternatives(remaining)
        }
    
    def _generate_reason(self, remaining: Dict, meal_macros: Dict) -> str:
        """Generate human-readable reason for recommendation"""
        if remaining['protein_g'] > 30:
            return f"High protein need ({remaining['protein_g']:.0f}g remaining). This meal provides {meal_macros['protein_g']}g."
        elif remaining['calories'] < 300:
            return f"Low calorie budget remaining ({remaining['calories']:.0f} cal). Light meal recommended."
        elif remaining['carbs_g'] > 50:
            return f"Carbs needed for energy ({remaining['carbs_g']:.0f}g remaining)."
        else:
            return "Balanced meal to complete daily targets."
    
    def _get_alternatives(self, remaining: Dict) -> List[str]:
        """Suggest alternative meal ideas"""
        alternatives = []
        
        if remaining['protein_g'] > 40:
            alternatives.append("Grilled steak with vegetables")
        if remaining['carbs_g'] > 60:
            alternatives.append("Pasta with lean protein")
        if remaining['calories'] < 350:
            alternatives.append("Greek yogurt with berries")
        
        return alternatives[:2]


class FoodSwapEngine:
    """Suggest healthier alternatives to foods"""
    
    def __init__(self):
        # Food swap database
        self.swaps = {
            'white_rice': {
                'alternatives': [
                    {'food': 'quinoa', 'benefit': '+4g protein, +3g fiber per serving'},
                    {'food': 'cauliflower_rice', 'benefit': '-70% calories, +vegetables'},
                    {'food': 'brown_rice', 'benefit': '+2g fiber, more nutrients'}
                ],
                'reason': 'More nutrients and fiber'
            },
            'pasta': {
                'alternatives': [
                    {'food': 'whole_wheat_pasta', 'benefit': '+5g fiber per serving'},
                    {'food': 'chickpea_pasta', 'benefit': '+10g protein, +8g fiber'},
                    {'food': 'zucchini_noodles', 'benefit': '-75% calories, +vegetables'}
                ],
                'reason': 'Higher protein and fiber'
            },
            'soda': {
                'alternatives': [
                    {'food': 'sparkling_water', 'benefit': '-140 calories, no sugar'},
                    {'food': 'green_tea', 'benefit': '-140 calories, antioxidants'},
                    {'food': 'water_with_lemon', 'benefit': '-140 calories, vitamin C'}
                ],
                'reason': 'Eliminate empty calories'
            },
            'chips': {
                'alternatives': [
                    {'food': 'air_popped_popcorn', 'benefit': '-60% calories, +fiber'},
                    {'food': 'roasted_chickpeas', 'benefit': '+protein, +fiber'},
                    {'food': 'veggie_sticks_with_hummus', 'benefit': '+protein, +nutrients'}
                ],
                'reason': 'More filling and nutritious'
            },
            'ice_cream': {
                'alternatives': [
                    {'food': 'greek_yogurt_with_berries', 'benefit': '+protein, -sugar'},
                    {'food': 'frozen_banana_nice_cream', 'benefit': '-50% calories, +potassium'},
                    {'food': 'protein_ice_cream', 'benefit': '+20g protein, -calories'}
                ],
                'reason': 'Satisfy sweet tooth healthily'
            }
        }
    
    def suggest_swaps(self, detected_foods: List[str]) -> List[Dict]:
        """
        Suggest healthier swaps for detected foods
        
        Returns list of swap suggestions
        """
        suggestions = []
        
        for food in detected_foods:
            # Normalize food name
            food_lower = food.lower().replace(' ', '_')
            
            if food_lower in self.swaps:
                suggestions.append({
                    'original_food': food,
                    'swaps': self.swaps[food_lower]['alternatives'],
                    'reason': self.swaps[food_lower]['reason']
                })
        
        return suggestions


class PortionOptimizer:
    """Calculate optimal portion sizes based on targets"""
    
    def __init__(self):
        pass
    
    def optimize_portions(self, meal_components: List[Dict], 
                         target_calories: float, target_protein: float) -> Dict:
        """
        Calculate optimal serving sizes using linear optimization
        
        Args:
            meal_components: List of foods with nutrition per 100g
            target_calories: Desired total calories
            target_protein: Desired total protein
        
        Returns:
            Optimized portion sizes in grams
        """
        # Simplified optimization (in production, use scipy.optimize)
        # Goal: minimize |actual - target| for calories and protein
        
        optimized_portions = {}
        
        # Simple heuristic: distribute evenly, then adjust
        base_portion = 150  # grams
        
        for component in meal_components:
            food_name = component['name']
            nutrition = component['nutrition_per_100g']
            
            # Calculate multiplier based on protein density
            protein_density = nutrition['protein'] / nutrition['calories'] if nutrition['calories'] > 0 else 0
            
            # Higher protein foods get slightly larger portions
            multiplier = 1.0 + (protein_density * 0.5)
            optimized_portions[food_name] = round(base_portion * multiplier, 0)
        
        # Scale to meet calorie target
        total_cal_estimate = sum(
            (optimized_portions[c['name']] / 100) * c['nutrition_per_100g']['calories']
            for c in meal_components
        )
        
        scale_factor = target_calories / total_cal_estimate if total_cal_estimate > 0 else 1.0
        
        for food in optimized_portions:
            optimized_portions[food] = round(optimized_portions[food] * scale_factor, 0)
        
        # Calculate final nutrition
        final_nutrition = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0
        }
        
        for component in meal_components:
            portion = optimized_portions[component['name']]
            nutrition = component['nutrition_per_100g']
            multiplier = portion / 100
            
            final_nutrition['calories'] += nutrition['calories'] * multiplier
            final_nutrition['protein_g'] += nutrition['protein'] * multiplier
            final_nutrition['carbs_g'] += nutrition['carbs'] * multiplier
            final_nutrition['fat_g'] += nutrition['fat'] * multiplier
        
        return {
            'portions_grams': optimized_portions,
            'total_nutrition': {k: round(v, 1) for k, v in final_nutrition.items()},
            'accuracy': {
                'calories_diff': round(abs(final_nutrition['calories'] - target_calories), 1),
                'protein_diff': round(abs(final_nutrition['protein_g'] - target_protein), 1)
            }
        }


# Export all recommendation engines
__all__ = ['GoalPredictor', 'MealRecommender', 'FoodSwapEngine', 'PortionOptimizer']
