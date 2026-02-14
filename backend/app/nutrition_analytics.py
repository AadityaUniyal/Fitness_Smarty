"""
Advanced Nutrition Analytics Engine

Sophisticated math calculations and tracking logic:
1. TDEE/BMR calculations (Mifflin-St Jeor equation)
2. Dynamic macro targets based on goals
3. Meal streak tracking
4. Pattern detection in eating habits
5. Progress analytics
"""

import math
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np


class NutritionAnalytics:
    """Advanced nutrition calculations and analytics"""
    
    def __init__(self):
        pass
    
    def calculate_bmr(self, weight_kg: float, height_cm: float, 
                      age: int, gender: str) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
        
        BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + s
        where s = +5 for males, -161 for females
        
        Returns: BMR in calories/day
        """
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        
        if gender.lower() == 'male':
            bmr += 5
        else:
            bmr -= 161
        
        return round(bmr, 1)
    
    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """
        Calculate Total Daily Energy Expenditure
        
        TDEE = BMR × Activity Multiplier
        
        Activity Levels:
        - sedentary: 1.2 (little to no exercise)
        - light: 1.375 (exercise 1-3 days/week)
        - moderate: 1.55 (exercise 3-5 days/week)
        - active: 1.725 (exercise 6-7 days/week)
        - very_active: 1.9 (physical job + exercise daily)
        
        Returns: TDEE in calories/day
        """
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = multipliers.get(activity_level.lower(), 1.55)
        tdee = bmr * multiplier
        
        return round(tdee, 1)
    
    def calculate_macro_targets(self, tdee: float, goal: str) -> Dict[str, float]:
        """
        Calculate optimal macro targets based on goal
        
        Macro distributions:
        - Weight Loss: 40% protein, 30% carbs, 30% fat (calorie deficit)
        - Muscle Gain: 30% protein, 40% carbs, 30% fat (calorie surplus)
        - Maintenance: 25% protein, 45% carbs, 30% fat
        - Athletic: 30% protein, 50% carbs, 20% fat
        
        Returns: Daily targets in grams & calories
        """
        # Adjust TDEE based on goal
        if goal == 'weight_loss':
            target_calories = tdee * 0.8  # 20% deficit
            protein_pct, carb_pct, fat_pct = 0.40, 0.30, 0.30
        elif goal == 'muscle_gain':
            target_calories = tdee * 1.15  # 15% surplus
            protein_pct, carb_pct, fat_pct = 0.30, 0.40, 0.30
        elif goal == 'athletic_performance':
            target_calories = tdee * 1.05  # Small surplus
            protein_pct, carb_pct, fat_pct = 0.30, 0.50, 0.20
        else:  # maintenance
            target_calories = tdee
            protein_pct, carb_pct, fat_pct = 0.25, 0.45, 0.30
        
        # Calculate grams (protein = 4 cal/g, carbs = 4 cal/g, fat = 9 cal/g)
        protein_g = (target_calories * protein_pct) / 4
        carbs_g = (target_calories * carb_pct) / 4
        fat_g = (target_calories * fat_pct) / 9
        
        return {
            'target_calories': round(target_calories),
            'protein_g': round(protein_g, 1),
            'carbs_g': round(carbs_g, 1),
            'fat_g': round(fat_g, 1),
            'protein_percentage': round(protein_pct * 100, 1),
            'carbs_percentage': round(carb_pct * 100, 1),
            'fat_percentage': round(fat_pct * 100, 1)
        }
    
    def calculate_meal_score(self, meal_nutrition: Dict, targets: Dict) -> Dict:
        """
        Calculate how well a meal fits daily targets
        
        Uses Euclidean distance in normalized macro space
        
        Returns: Score from 0-100 and breakdown
        """
        # Normalize actual macros to percentage
        total_cals = meal_nutrition.get('calories', 0)
        if total_cals == 0:
            return {'score': 0, 'breakdown': {}}
        
        actual_protein = meal_nutrition.get('protein_g', 0) * 4
        actual_carbs = meal_nutrition.get('carbs_g', 0) * 4
        actual_fat = meal_nutrition.get('fat_g', 0) * 9
        total_macro_cals = actual_protein + actual_carbs + actual_fat
        
        if total_macro_cals == 0:
            return {'score': 0, 'breakdown': {}}
        
        actual_pct = np.array([
            actual_protein / total_macro_cals,
            actual_carbs / total_macro_cals,
            actual_fat / total_macro_cals
        ])
        
        # Target percentages
        target_pct = np.array([
            targets['protein_percentage'] / 100,
            targets['carbs_percentage'] / 100,
            targets['fat_percentage'] / 100
        ])
        
        # Euclidean distance (0 = perfect match)
        distance = np.linalg.norm(actual_pct - target_pct)
        
        # Convert to score (max distance is sqrt(2))
        max_distance = math.sqrt(2)
        score = max(0, 100 * (1 - distance / max_distance))
        
        # Calorie fit score (100 = perfect, penalize over/under)
        ideal_meal_cals = targets['target_calories'] / 3  # Assume 3 meals/day
        cal_diff_pct = abs(total_cals - ideal_meal_cals) / ideal_meal_cals
        cal_score = max(0, 100 * (1 - cal_diff_pct))
        
        # Combined score (70% macro fit, 30% calorie fit)
        final_score = (score * 0.7) + (cal_score * 0.3)
        
        return {
            'score': round(final_score, 1),
            'macro_fit': round(score, 1),
            'calorie_fit': round(cal_score, 1),
            'breakdown': {
                'protein_diff': round(actual_pct[0] - target_pct[0], 3),
                'carbs_diff': round(actual_pct[1] - target_pct[1], 3),
                'fat_diff': round(actual_pct[2] - target_pct[2], 3)
            }
        }


class MealTracker:
    """Track meal history and detect patterns"""
    
    def __init__(self):
        self.meal_history = []
    
    def add_meal(self, meal_data: Dict, user_feedback: bool, timestamp: datetime = None):
        """Add a meal to history"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self.meal_history.append({
            'timestamp': timestamp,
            'nutrition': meal_data.get('nutrition', {}),
            'foods': meal_data.get('foods', []),
            'user_liked': user_feedback
        })
    
    def calculate_streak(self) -> Dict:
        """
        Calculate current streak of healthy meals
        
        Returns: Current streak, longest streak
        """
        if not self.meal_history:
            return {'current_streak': 0, 'longest_streak': 0}
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Sort by timestamp
        sorted_meals = sorted(self.meal_history, key=lambda x: x['timestamp'])
        
        for meal in sorted_meals:
            if meal.get('user_liked', False):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Current streak is the last consecutive count
        for meal in reversed(sorted_meals):
            if meal.get('user_liked', False):
                current_streak += 1
            else:
                break
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_meals': len(self.meal_history),
            'success_rate': round(
                sum(1 for m in self.meal_history if m.get('user_liked', False)) / 
                len(self.meal_history) * 100, 1
            ) if self.meal_history else 0
        }
    
    def detect_patterns(self) -> Dict:
        """
        Detect eating patterns using statistical analysis
        
        Returns: Insights about eating habits
        """
        if len(self.meal_history) < 5:
            return {'status': 'insufficient_data'}
        
        # Analyze meal times
        meal_hours = [m['timestamp'].hour for m in self.meal_history]
        avg_meal_time = np.mean(meal_hours)
        std_meal_time = np.std(meal_hours)
        
        # Analyze calorie trends
        calories_history = [
            m['nutrition'].get('calories', 0) 
            for m in self.meal_history
        ]
        avg_calories = np.mean(calories_history)
        std_calories = np.std(calories_history)
        
        # Detect if calories are trending up/down (linear regression)
        x = np.arange(len(calories_history))
        slope, intercept = np.polyfit(x, calories_history, 1)
        
        # Protein trends
        protein_history = [
            m['nutrition'].get('protein_g', 0) 
            for m in self.meal_history
        ]
        avg_protein = np.mean(protein_history)
        
        # Consistency score (lower std = more consistent)
        calorie_consistency = max(0, 100 - (std_calories / avg_calories * 100))
        
        return {
            'status': 'patterns_detected',
            'meal_count': len(self.meal_history),
            'avg_meal_hour': round(avg_meal_time, 1),
            'meal_time_consistency': round(100 - (std_meal_time / 24 * 100), 1),
            'avg_calories_per_meal': round(avg_calories, 1),
            'calorie_std': round(std_calories, 1),
            'calorie_consistency': round(calorie_consistency, 1),
            'calorie_trend': 'increasing' if slope > 5 else 'decreasing' if slope < -5 else 'stable',
            'avg_protein_per_meal': round(avg_protein, 1)
        }
    
    def get_weekly_summary(self) -> Dict:
        """Generate weekly summary statistics"""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        recent_meals = [
            m for m in self.meal_history 
            if m['timestamp'] >= week_ago
        ]
        
        if not recent_meals:
            return {'status': 'no_recent_meals'}
        
        total_calories = sum(m['nutrition'].get('calories', 0) for m in recent_meals)
        total_protein = sum(m['nutrition'].get('protein_g', 0) for m in recent_meals)
        
        # Daily averages
        days_with_meals = len(set(m['timestamp'].date() for m in recent_meals))
        avg_daily_calories = total_calories / max(days_with_meals, 1)
        avg_daily_protein = total_protein / max(days_with_meals, 1)
        
        # Best and worst meals
        sorted_by_calories = sorted(recent_meals, key=lambda x: x['nutrition'].get('calories', 0))
        
        return {
            'period': '7_days',
            'total_meals': len(recent_meals),
            'meals_per_day': round(len(recent_meals) / 7, 1),
            'total_calories': round(total_calories),
            'avg_daily_calories': round(avg_daily_calories, 1),
            'avg_daily_protein': round(avg_daily_protein, 1),
            'highest_calorie_meal': round(sorted_by_calories[-1]['nutrition'].get('calories', 0)) if sorted_by_calories else 0,
            'lowest_calorie_meal': round(sorted_by_calories[0]['nutrition'].get('calories', 0)) if sorted_by_calories else 0,
            'liked_meals': sum(1 for m in recent_meals if m.get('user_liked', False)),
            'success_rate': round(
                sum(1 for m in recent_meals if m.get('user_liked', False)) / 
                len(recent_meals) * 100, 1
            )
        }


class NutrientGapAnalyzer:
    """Analyze nutrient deficiencies and excesses"""
    
    def __init__(self):
        # RDA (Recommended Daily Allowance) for adults
        self.rda = {
            'protein_g': 50,
            'fiber_g': 25,
            'vitamin_c_mg': 90,
            'calcium_mg': 1000,
            'iron_mg': 8,
        }
    
    def analyze_gaps(self, daily_nutrition: Dict) -> Dict:
        """
        Identify nutrient gaps using RDA standards
        
        Returns: Deficiencies, excesses, and recommendations
        """
        gaps = {
            'deficiencies': [],
            'adequate': [],
            'excess': []
        }
        
        for nutrient, rda_value in self.rda.items():
            actual = daily_nutrition.get(nutrient, 0)
            percentage = (actual / rda_value) * 100
            
            if percentage < 70:
                gaps['deficiencies'].append({
                    'nutrient': nutrient,
                    'actual': round(actual, 1),
                    'recommended': rda_value,
                    'percentage': round(percentage, 1)
                })
            elif percentage > 150:
                gaps['excess'].append({
                    'nutrient': nutrient,
                    'actual': round(actual, 1),
                    'recommended': rda_value,
                    'percentage': round(percentage, 1)
                })
            else:
                gaps['adequate'].append(nutrient)
        
        return gaps


# Export main classes
__all__ = ['NutritionAnalytics', 'MealTracker', 'NutrientGapAnalyzer']
