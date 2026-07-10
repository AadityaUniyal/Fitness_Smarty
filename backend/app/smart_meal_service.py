"""
Smart Meal Recommendation Service

Provides intelligent meal suggestions based on:
- Remaining calories for the day
- Time of day
- User's fitness goal
- Macro balance
- Food preferences
"""

from typing import Dict, List, Optional
from datetime import datetime, time
from sqlalchemy.orm import Session
from app import models
from app.calorie_tracker_service import CalorieTrackerService
from app.gender_specific_service import GenderSpecificService
import logging

logger = logging.getLogger(__name__)


class SmartMealService:
    """Service for intelligent meal recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calorie_tracker = CalorieTrackerService(db)
        self.gender_service = GenderSpecificService(db)
    
    def get_meal_recommendation(
        self,
        user_id: int,
        meal_type: Optional[str] = None
    ) -> Dict:
        """
        Get smart meal recommendation based on current daily status.
        
        Args:
            user_id: User ID
            meal_type: Optional meal type (breakfast, lunch, dinner, snack)
        
        Returns:
            Dictionary with meal suggestions and reasoning
        """
        # Get daily summary
        summary = self.calorie_tracker.get_daily_calorie_summary(user_id)
        
        # Get user profile for preferences
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Determine meal type if not provided
        if not meal_type:
            meal_type = self._determine_meal_type()
        
        # Get user's goal and macro targets
        goal = user.primary_goal or "maintenance"
        macro_targets = self.gender_service.get_gender_specific_macro_targets(
            user_id=user_id,
            goal=goal
        )
        
        # Calculate remaining macros
        remaining_calories = summary['calories_remaining']
        remaining_protein = macro_targets['macros']['protein_g'] - summary['nutrition_consumed']['protein_g']
        remaining_carbs = macro_targets['macros']['carbs_g'] - summary['nutrition_consumed']['carbs_g']
        remaining_fats = macro_targets['macros']['fat_g'] - summary['nutrition_consumed']['fat_g']
        
        # Get meal suggestions based on remaining macros
        suggestions = self._generate_meal_suggestions(
            meal_type=meal_type,
            remaining_calories=remaining_calories,
            remaining_protein=remaining_protein,
            remaining_carbs=remaining_carbs,
            remaining_fats=remaining_fats,
            goal=goal
        )
        
        # Get reasoning
        reasoning = self._generate_reasoning(
            meal_type=meal_type,
            remaining_calories=remaining_calories,
            summary=summary,
            goal=goal
        )
        
        return {
            "user_id": user_id,
            "meal_type": meal_type,
            "current_status": {
                "calories_consumed": summary['calories_consumed'],
                "calories_burned": summary['calories_burned'],
                "net_calories": summary['net_calories'],
                "calories_remaining": remaining_calories,
                "on_track": summary['on_track']
            },
            "remaining_macros": {
                "protein_g": round(remaining_protein, 1),
                "carbs_g": round(remaining_carbs, 1),
                "fat_g": round(remaining_fats, 1)
            },
            "meal_suggestions": suggestions,
            "reasoning": reasoning,
            "recommended_foods": self._get_recommended_foods(
                remaining_calories=remaining_calories,
                goal=goal
            )
        }
    
    def _determine_meal_type(self) -> str:
        """Determine meal type based on current time"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 11:
            return "breakfast"
        elif 11 <= current_hour < 15:
            return "lunch"
        elif 15 <= current_hour < 18:
            return "snack"
        elif 18 <= current_hour < 23:
            return "dinner"
        else:
            return "late_snack"
    
    def _generate_meal_suggestions(
        self,
        meal_type: str,
        remaining_calories: float,
        remaining_protein: float,
        remaining_carbs: float,
        remaining_fats: float,
        goal: str
    ) -> List[Dict]:
        """Generate meal suggestions based on remaining macros"""
        
        suggestions = []
        
        # Calculate target for this meal (portion of remaining)
        meal_portions = {
            "breakfast": 0.30,
            "lunch": 0.35,
            "dinner": 0.30,
            "snack": 0.15,
            "late_snack": 0.10
        }
        
        portion = meal_portions.get(meal_type, 0.25)
        target_calories = remaining_calories * portion
        target_protein = remaining_protein * portion
        
        # Goal-specific meal templates
        meal_templates = self._get_meal_templates(goal, meal_type)
        
        # Find meals that fit remaining calories
        for template in meal_templates:
            if template['calories'] <= remaining_calories:
                suggestions.append(template)
        
        # Sort by how well they match targets
        suggestions.sort(
            key=lambda x: abs(x['calories'] - target_calories) + 
                         abs(x['protein_g'] - target_protein)
        )
        
        return suggestions[:5]  # Top 5 suggestions
    
    def _get_meal_templates(self, goal: str, meal_type: str) -> List[Dict]:
        """Get meal templates based on goal and meal type"""
        
        templates = {
            "fat_loss": {
                "breakfast": [
                    {
                        "name": "High Protein Oatmeal",
                        "description": "Oats with protein powder, berries, and almonds",
                        "calories": 350,
                        "protein_g": 30,
                        "carbs_g": 45,
                        "fat_g": 8,
                        "foods": ["Oats (50g)", "Protein Powder (30g)", "Berries (100g)", "Almonds (10g)"]
                    },
                    {
                        "name": "Egg White Scramble",
                        "description": "Egg whites with vegetables and whole wheat toast",
                        "calories": 300,
                        "protein_g": 28,
                        "carbs_g": 35,
                        "fat_g": 5,
                        "foods": ["Egg Whites (150g)", "Vegetables (100g)", "Whole Wheat Bread (40g)"]
                    }
                ],
                "lunch": [
                    {
                        "name": "Grilled Chicken Salad",
                        "description": "Chicken breast with mixed greens and vinaigrette",
                        "calories": 400,
                        "protein_g": 40,
                        "carbs_g": 25,
                        "fat_g": 15,
                        "foods": ["Chicken Breast (150g)", "Mixed Greens (100g)", "Olive Oil (10ml)"]
                    },
                    {
                        "name": "Tuna Bowl",
                        "description": "Tuna with quinoa and vegetables",
                        "calories": 420,
                        "protein_g": 38,
                        "carbs_g": 40,
                        "fat_g": 10,
                        "foods": ["Tuna (120g)", "Quinoa (60g)", "Vegetables (150g)"]
                    }
                ],
                "dinner": [
                    {
                        "name": "Baked Salmon & Veggies",
                        "description": "Salmon with roasted vegetables",
                        "calories": 450,
                        "protein_g": 38,
                        "carbs_g": 30,
                        "fat_g": 20,
                        "foods": ["Salmon (150g)", "Broccoli (150g)", "Sweet Potato (100g)"]
                    }
                ],
                "snack": [
                    {
                        "name": "Greek Yogurt & Berries",
                        "description": "High protein Greek yogurt with fresh berries",
                        "calories": 180,
                        "protein_g": 20,
                        "carbs_g": 22,
                        "fat_g": 2,
                        "foods": ["Greek Yogurt (200g)", "Berries (100g)"]
                    }
                ]
            },
            "muscle_gain": {
                "breakfast": [
                    {
                        "name": "Power Breakfast Bowl",
                        "description": "Eggs, oats, peanut butter, and banana",
                        "calories": 650,
                        "protein_g": 35,
                        "carbs_g": 70,
                        "fat_g": 25,
                        "foods": ["Eggs (100g)", "Oats (80g)", "Peanut Butter (20g)", "Banana (100g)"]
                    }
                ],
                "lunch": [
                    {
                        "name": "Chicken & Rice Bowl",
                        "description": "Grilled chicken with brown rice and vegetables",
                        "calories": 700,
                        "protein_g": 50,
                        "carbs_g": 80,
                        "fat_g": 15,
                        "foods": ["Chicken Breast (200g)", "Brown Rice (100g)", "Vegetables (100g)"]
                    }
                ],
                "dinner": [
                    {
                        "name": "Steak & Sweet Potato",
                        "description": "Lean beef with sweet potato and avocado",
                        "calories": 750,
                        "protein_g": 55,
                        "carbs_g": 60,
                        "fat_g": 28,
                        "foods": ["Lean Beef (200g)", "Sweet Potato (200g)", "Avocado (50g)"]
                    }
                ],
                "snack": [
                    {
                        "name": "Protein Shake & Nuts",
                        "description": "Whey protein with milk and almonds",
                        "calories": 400,
                        "protein_g": 35,
                        "carbs_g": 30,
                        "fat_g": 15,
                        "foods": ["Protein Powder (40g)", "Milk (250ml)", "Almonds (20g)"]
                    }
                ]
            },
            "maintenance": {
                "breakfast": [
                    {
                        "name": "Balanced Breakfast",
                        "description": "Eggs, toast, and fruit",
                        "calories": 450,
                        "protein_g": 25,
                        "carbs_g": 50,
                        "fat_g": 15,
                        "foods": ["Eggs (100g)", "Whole Wheat Bread (60g)", "Fruit (100g)"]
                    }
                ],
                "lunch": [
                    {
                        "name": "Mediterranean Bowl",
                        "description": "Chicken, quinoa, and Greek salad",
                        "calories": 550,
                        "protein_g": 40,
                        "carbs_g": 55,
                        "fat_g": 18,
                        "foods": ["Chicken (150g)", "Quinoa (70g)", "Greek Salad (150g)"]
                    }
                ],
                "dinner": [
                    {
                        "name": "Balanced Dinner",
                        "description": "Fish, rice, and vegetables",
                        "calories": 500,
                        "protein_g": 35,
                        "carbs_g": 50,
                        "fat_g": 15,
                        "foods": ["Fish (150g)", "Rice (80g)", "Vegetables (150g)"]
                    }
                ],
                "snack": [
                    {
                        "name": "Fruit & Nuts",
                        "description": "Apple with almond butter",
                        "calories": 250,
                        "protein_g": 8,
                        "carbs_g": 30,
                        "fat_g": 12,
                        "foods": ["Apple (150g)", "Almond Butter (15g)"]
                    }
                ]
            }
        }
        
        goal_templates = templates.get(goal, templates["maintenance"])
        return goal_templates.get(meal_type, goal_templates.get("lunch", []))
    
    def _generate_reasoning(
        self,
        meal_type: str,
        remaining_calories: float,
        summary: Dict,
        goal: str
    ) -> str:
        """Generate reasoning for meal recommendation"""
        
        if remaining_calories < 0:
            return f"⚠️ You've exceeded your daily calorie target by {abs(remaining_calories):.0f} calories. Consider a light meal or skip this meal."
        
        if remaining_calories < 200:
            return f"✅ You're close to your target! A small snack (under 200 calories) would be perfect."
        
        if remaining_calories < 500:
            return f"You have {remaining_calories:.0f} calories left. A moderate meal focusing on protein would be ideal for {goal}."
        
        if remaining_calories < 800:
            return f"You have {remaining_calories:.0f} calories remaining. A balanced meal with good protein and carbs is recommended."
        
        return f"You have {remaining_calories:.0f} calories left today. You can afford a full meal. Focus on hitting your protein target!"
    
    def _get_recommended_foods(
        self,
        remaining_calories: float,
        goal: str
    ) -> List[Dict]:
        """Get recommended foods from database based on remaining calories and goal"""
        
        # Query foods from database matching goal
        foods = self.db.query(models.FoodItem).filter(
            models.FoodItem.recommended_for_goal == goal
        ).limit(10).all()
        
        recommended = []
        for food in foods:
            # Calculate appropriate portion
            if remaining_calories > 0:
                max_grams = min(300, (remaining_calories / food.calories) * 100)
                
                recommended.append({
                    "food_id": food.id,
                    "name": food.name,
                    "category": food.category.name if food.category else None,
                    "suggested_portion_g": round(max_grams, 0),
                    "calories_per_100g": food.calories,
                    "protein_per_100g": food.protein,
                    "is_elite": food.is_elite
                })
        
        return recommended[:8]  # Top 8 recommendations
    
    def get_post_workout_meal(
        self,
        user_id: int,
        calories_burned: float
    ) -> Dict:
        """
        Get post-workout meal recommendation.
        
        Args:
            user_id: User ID
            calories_burned: Calories burned in workout
        
        Returns:
            Post-workout meal recommendation
        """
        user = self.db.query(models.EnhancedUser).filter(
            models.EnhancedUser.id == user_id
        ).first()
        
        goal = user.primary_goal or "maintenance"
        
        # Post-workout meals should be protein + carb focused
        recommendations = {
            "fat_loss": {
                "target_calories": calories_burned * 0.5,  # Eat back 50% of burned
                "protein_ratio": 0.40,
                "carb_ratio": 0.40,
                "fat_ratio": 0.20
            },
            "muscle_gain": {
                "target_calories": calories_burned * 0.8,  # Eat back 80% of burned
                "protein_ratio": 0.35,
                "carb_ratio": 0.45,
                "fat_ratio": 0.20
            },
            "maintenance": {
                "target_calories": calories_burned * 0.6,
                "protein_ratio": 0.35,
                "carb_ratio": 0.45,
                "fat_ratio": 0.20
            }
        }
        
        rec = recommendations.get(goal, recommendations["maintenance"])
        target_cals = rec["target_calories"]
        
        suggestions = [
            {
                "name": "Protein Shake + Banana",
                "description": "Fast-absorbing protein with simple carbs",
                "calories": target_cals * 0.5,
                "protein_g": (target_cals * rec["protein_ratio"]) / 4,
                "timing": "Within 30 minutes post-workout"
            },
            {
                "name": "Chicken & Rice",
                "description": "Lean protein with complex carbs for recovery",
                "calories": target_cals,
                "protein_g": (target_cals * rec["protein_ratio"]) / 4,
                "timing": "Within 2 hours post-workout"
            }
        ]
        
        return {
            "user_id": user_id,
            "workout_calories_burned": calories_burned,
            "recommended_refuel_calories": round(target_cals, 0),
            "macro_split": {
                "protein": f"{rec['protein_ratio']*100:.0f}%",
                "carbs": f"{rec['carb_ratio']*100:.0f}%",
                "fats": f"{rec['fat_ratio']*100:.0f}%"
            },
            "suggestions": suggestions,
            "tip": "Focus on protein and carbs for optimal recovery. Keep fats moderate."
        }
