"""
Food Swap Suggestions Service

Provides healthier food alternatives with similar:
- Calorie content
- Macronutrient profile
- Cultural context
- Taste preferences

Helps users make better food choices.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import EnhancedUser as User, FoodItem as Food, UserGoal as UserGoals

class GoalType:
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"


class FoodSwapService:
    """Service for suggesting healthier food alternatives"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def suggest_swap(
        self, 
        user_id: int, 
        food_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest a healthier alternative for a specific food
        
        Args:
            user_id: User ID for personalized recommendations
            food_id: Food to find alternative for
            reason: Optional reason (e.g., 'lower_calorie', 'higher_protein')
        """
        # Get original food
        original_food = self.db.query(Food).filter(Food.id == food_id).first()
        if not original_food:
            return {"error": "Food not found"}
        
        # Get user for personalization
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get user goals
        user_goal = self.db.query(UserGoals).filter(
            UserGoals.user_id == user_id
        ).order_by(UserGoals.created_at.desc()).first()
        
        # Find alternatives
        alternatives = self._find_alternatives(original_food, user_goal, reason)
        
        if not alternatives:
            return {
                "original_food": self._format_food(original_food),
                "alternatives": [],
                "message": "No direct alternatives found, but this food can fit your goals!"
            }
        
        # Rank alternatives
        ranked_alternatives = self._rank_alternatives(
            original_food, 
            alternatives, 
            user_goal
        )
        
        return {
            "original_food": self._format_food(original_food),
            "alternatives": ranked_alternatives[:5],  # Top 5
            "swap_benefits": self._calculate_swap_benefits(
                original_food, 
                ranked_alternatives[0] if ranked_alternatives else None
            )
        }
    
    def get_alternatives_by_category(
        self, 
        user_id: int, 
        category: str
    ) -> Dict[str, Any]:
        """
        Get healthier alternatives for a food category
        
        Categories: protein, carbs, snacks, dairy, etc.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get user goals
        user_goal = self.db.query(UserGoals).filter(
            UserGoals.user_id == user_id
        ).order_by(UserGoals.created_at.desc()).first()
        
        # Category mapping
        category_keywords = {
            "protein": ["chicken", "fish", "beef", "pork", "tofu", "eggs", "protein"],
            "carbs": ["rice", "bread", "pasta", "potato", "grain", "cereal"],
            "snacks": ["chips", "cookie", "candy", "snack", "chocolate"],
            "dairy": ["milk", "cheese", "yogurt", "cream"],
            "vegetables": ["vegetable", "salad", "greens"],
            "fruits": ["fruit", "apple", "banana", "berry"]
        }
        
        keywords = category_keywords.get(category.lower(), [])
        if not keywords:
            return {"error": f"Unknown category: {category}"}
        
        # Find foods in this category
        foods_in_category = []
        for keyword in keywords:
            foods = self.db.query(Food).filter(
                Food.name.ilike(f"%{keyword}%")
            ).all()
            foods_in_category.extend(foods)
        
        # Remove duplicates
        unique_foods = {f.id: f for f in foods_in_category}.values()
        
        # Rank by healthiness for user's goal
        ranked = self._rank_by_healthiness(list(unique_foods), user_goal)
        
        return {
            "category": category,
            "recommended_foods": [self._format_food(f) for f in ranked[:10]],
            "goal": user_goal.goal_type.value if user_goal else "general"
        }
    
    def suggest_meal_swaps(
        self, 
        user_id: int, 
        meal_foods: List[int]
    ) -> Dict[str, Any]:
        """
        Suggest swaps for an entire meal
        
        Args:
            user_id: User ID
            meal_foods: List of food IDs in the meal
        """
        swaps = []
        total_calorie_reduction = 0
        total_protein_increase = 0
        
        for food_id in meal_foods:
            swap_result = self.suggest_swap(user_id, food_id)
            
            if "error" not in swap_result and swap_result["alternatives"]:
                best_alternative = swap_result["alternatives"][0]
                original = swap_result["original_food"]
                
                calorie_diff = original["calories"] - best_alternative["calories"]
                protein_diff = best_alternative["protein_g"] - original["protein_g"]
                
                if calorie_diff > 10 or protein_diff > 2:  # Meaningful improvement
                    swaps.append({
                        "original": original,
                        "suggested": best_alternative,
                        "reason": swap_result["swap_benefits"]["primary_benefit"]
                    })
                    total_calorie_reduction += max(0, calorie_diff)
                    total_protein_increase += max(0, protein_diff)
        
        return {
            "meal_size": len(meal_foods),
            "suggested_swaps": swaps,
            "total_improvements": {
                "calorie_reduction": round(total_calorie_reduction, 1),
                "protein_increase_g": round(total_protein_increase, 1)
            },
            "message": self._generate_swap_message(swaps, total_calorie_reduction, total_protein_increase)
        }
    
    def get_goal_specific_swaps(self, user_id: int, goal: str) -> Dict[str, Any]:
        """
        Get food swaps optimized for a specific goal
        
        Goals: fat_loss, muscle_gain, maintenance
        """
        goal_mapping = {
            "fat_loss": GoalType.FAT_LOSS,
            "muscle_gain": GoalType.MUSCLE_GAIN,
            "maintenance": GoalType.MAINTENANCE
        }
        
        goal_type = goal_mapping.get(goal.lower())
        if not goal_type:
            return {"error": f"Unknown goal: {goal}"}
        
        # Define swap strategies by goal
        if goal_type == GoalType.FAT_LOSS:
            swaps = self._get_fat_loss_swaps()
        elif goal_type == GoalType.MUSCLE_GAIN:
            swaps = self._get_muscle_gain_swaps()
        else:
            swaps = self._get_maintenance_swaps()
        
        return {
            "goal": goal,
            "recommended_swaps": swaps,
            "tips": self._get_goal_tips(goal_type)
        }
    
    def _find_alternatives(
        self, 
        original: Food, 
        user_goal: Optional[UserGoals],
        reason: Optional[str]
    ) -> List[Food]:
        """Find alternative foods"""
        
        # Determine calorie range (±100 calories)
        calorie_min = max(0, original.calories - 100)
        calorie_max = original.calories + 100
        
        # Query similar foods
        query = self.db.query(Food).filter(
            and_(
                Food.id != original.id,
                Food.calories >= calorie_min,
                Food.calories <= calorie_max
            )
        )
        
        # If reason specified, apply filters
        if reason == "lower_calorie":
            query = query.filter(Food.calories < original.calories)
        elif reason == "higher_protein":
            query = query.filter(Food.protein > original.protein)
        
        alternatives = query.all()
        
        # Filter by similar food type (keywords)
        similar_alternatives = self._filter_by_similarity(original, alternatives)
        
        return similar_alternatives
    
    def _filter_by_similarity(self, original: Food, alternatives: List[Food]) -> List[Food]:
        """Filter alternatives by food type similarity"""
        
        # Extract keywords from original food name
        original_keywords = set(original.name.lower().split())
        
        similar = []
        for alt in alternatives:
            alt_keywords = set(alt.name.lower().split())
            
            # Check for common keywords
            common = original_keywords.intersection(alt_keywords)
            if common:
                similar.append(alt)
                continue
            
            # Check for category matches
            if self._same_category(original.name, alt.name):
                similar.append(alt)
        
        return similar if similar else alternatives[:20]  # Fallback to any similar calorie
    
    def _same_category(self, name1: str, name2: str) -> bool:
        """Check if two foods are in the same category"""
        categories = [
            ["chicken", "turkey", "beef", "pork", "meat"],
            ["rice", "bread", "pasta", "grain", "cereal"],
            ["milk", "cheese", "yogurt", "dairy"],
            ["apple", "banana", "orange", "fruit", "berry"],
            ["salad", "vegetable", "greens", "broccoli", "carrot"]
        ]
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        for category in categories:
            in_cat_1 = any(keyword in name1_lower for keyword in category)
            in_cat_2 = any(keyword in name2_lower for keyword in category)
            
            if in_cat_1 and in_cat_2:
                return True
        
        return False
    
    def _rank_alternatives(
        self, 
        original: Food, 
        alternatives: List[Food],
        user_goal: Optional[UserGoals]
    ) -> List[Dict[str, Any]]:
        """Rank alternatives by healthiness"""
        
        scored_alternatives = []
        
        for alt in alternatives:
            score = 0
            reasons = []
            
            # Calorie comparison
            calorie_diff = original.calories - alt.calories
            if calorie_diff > 50:
                score += 3
                reasons.append(f"{int(calorie_diff)} fewer calories")
            elif calorie_diff > 20:
                score += 1
            
            # Protein comparison
            protein_diff = alt.protein - original.protein
            if protein_diff > 5:
                score += 3
                reasons.append(f"+{round(protein_diff, 1)}g protein")
            elif protein_diff > 2:
                score += 1
            
            # Fat comparison (lower is better for most goals)
            if alt.fat < original.fat:
                score += 1
                if original.fat - alt.fat > 5:
                    reasons.append("lower fat")
            
            # Carb comparison (depends on goal)
            if user_goal and user_goal.goal_type == GoalType.MUSCLE_GAIN:
                if alt.carbs > original.carbs:
                    score += 1
            
            # Fiber is always good
            if hasattr(alt, 'fiber') and hasattr(original, 'fiber'):
                if alt.fiber > original.fiber:
                    score += 2
                    reasons.append("higher fiber")
            
            scored_alternatives.append({
                **self._format_food(alt),
                "health_score": score,
                "swap_reasons": reasons if reasons else ["similar nutritional profile"]
            })
        
        # Sort by score (descending)
        scored_alternatives.sort(key=lambda x: x["health_score"], reverse=True)
        
        return scored_alternatives
    
    def _rank_by_healthiness(
        self, 
        foods: List[Food], 
        user_goal: Optional[UserGoals]
    ) -> List[Food]:
        """Rank foods by healthiness for goal"""
        
        def health_score(food: Food) -> float:
            score = 0.0
            
            # Protein density (protein per 100 calories)
            protein_density = (food.protein / max(food.calories, 1)) * 100
            score += protein_density * 2
            
            # Penalize high fat (unless muscle gain)
            if not (user_goal and user_goal.goal_type == GoalType.MUSCLE_GAIN):
                score -= food.fat * 0.5
            
            # Reward moderate carbs
            if 20 <= food.carbs <= 50:
                score += 5
            
            # Fiber bonus
            if hasattr(food, 'fiber') and food.fiber:
                score += food.fiber * 2
            
            return score
        
        return sorted(foods, key=health_score, reverse=True)
    
    def _calculate_swap_benefits(
        self, 
        original: Food, 
        alternative: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate benefits of making the swap"""
        
        if not alternative:
            return {}
        
        calorie_diff = original.calories - alternative["calories"]
        protein_diff = alternative["protein_g"] - original.protein
        fat_diff = original.fat - alternative["fat_g"]
        
        benefits = []
        primary_benefit = ""
        
        if calorie_diff > 50:
            benefits.append(f"Save {int(calorie_diff)} calories")
            primary_benefit = "lower_calorie"
        
        if protein_diff > 5:
            benefits.append(f"Gain {round(protein_diff, 1)}g protein")
            if not primary_benefit:
                primary_benefit = "higher_protein"
        
        if fat_diff > 5:
            benefits.append(f"Reduce fat by {round(fat_diff, 1)}g")
            if not primary_benefit:
                primary_benefit = "lower_fat"
        
        if not primary_benefit:
            primary_benefit = "similar_nutrition"
            benefits.append("Similar nutrition with variety")
        
        return {
            "benefits": benefits,
            "primary_benefit": primary_benefit,
            "calorie_difference": round(calorie_diff, 1),
            "protein_difference": round(protein_diff, 1),
            "fat_difference": round(fat_diff, 1)
        }
    
    def _format_food(self, food: Food) -> Dict[str, Any]:
        """Format food object for response"""
        return {
            "id": food.id,
            "name": food.name,
            "calories": round(food.calories, 1),
            "protein_g": round(food.protein, 1),
            "carbs_g": round(food.carbs, 1),
            "fat_g": round(food.fat, 1)
        }
    
    def _generate_swap_message(
        self, 
        swaps: List[Dict], 
        calorie_reduction: float, 
        protein_increase: float
    ) -> str:
        """Generate message about meal swaps"""
        
        if not swaps:
            return "Your meal looks great! No swaps needed."
        
        msg = f"Making {len(swaps)} swap(s) would "
        
        parts = []
        if calorie_reduction > 50:
            parts.append(f"save {int(calorie_reduction)} calories")
        if protein_increase > 5:
            parts.append(f"add {round(protein_increase, 1)}g protein")
        
        if parts:
            msg += " and ".join(parts) + "!"
        else:
            msg += "improve your meal quality!"
        
        return msg
    
    def _get_fat_loss_swaps(self) -> List[Dict[str, str]]:
        """Common swaps for fat loss"""
        return [
            {"from": "White rice", "to": "Cauliflower rice", "benefit": "Save 150+ calories"},
            {"from": "Regular pasta", "to": "Zucchini noodles", "benefit": "Save 180 calories"},
            {"from": "Beef burger", "to": "Turkey burger", "benefit": "Save 100 calories"},
            {"from": "Fried chicken", "to": "Grilled chicken", "benefit": "Save 200+ calories"},
            {"from": "Soda", "to": "Sparkling water", "benefit": "Save 140 calories"},
            {"from": "Potato chips", "to": "Air-popped popcorn", "benefit": "Save 100 calories"},
            {"from": "Regular yogurt", "to": "Greek yogurt", "benefit": "2x protein, less sugar"}
        ]
    
    def _get_muscle_gain_swaps(self) -> List[Dict[str, str]]:
        """Common swaps for muscle gain"""
        return [
            {"from": "White rice", "to": "Brown rice", "benefit": "More fiber and nutrients"},
            {"from": "Regular milk", "to": "Whole milk", "benefit": "More calories and protein"},
            {"from": "Chicken breast", "to": "Salmon", "benefit": "Healthy fats + protein"},
            {"from": "Regular pasta", "to": "Protein pasta", "benefit": "2x the protein"},
            {"from": "Regular bread", "to": "Whole grain bread", "benefit": "Better carbs"},
            {"from": "Regular oats", "to": "Oats with protein powder", "benefit": "+20g protein"},
            {"from": "Snack bar", "to": "Protein bar", "benefit": "More protein, less sugar"}
        ]
    
    def _get_maintenance_swaps(self) -> List[Dict[str, str]]:
        """Common swaps for maintenance"""
        return [
            {"from": "White bread", "to": "Whole wheat bread", "benefit": "More fiber"},
            {"from": "Regular pasta", "to": "Whole wheat pasta", "benefit": "Better nutrients"},
            {"from": "Butter", "to": "Olive oil", "benefit": "Healthier fats"},
            {"from": "Sugary cereal", "to": "Oatmeal", "benefit": "Sustained energy"},
            {"from": "Soda", "to": "Tea or water", "benefit": "No empty calories"},
            {"from": "Ice cream", "to": "Frozen yogurt", "benefit": "Less fat, similar taste"}
        ]
    
    def _get_goal_tips(self, goal_type: GoalType) -> List[str]:
        """Get tips for specific goal"""
        if goal_type == GoalType.FAT_LOSS:
            return [
                "Focus on volume (more food, fewer calories)",
                "Choose lean proteins",
                "Load up on vegetables",
                "Swap fried for grilled or baked"
            ]
        elif goal_type == GoalType.MUSCLE_GAIN:
            return [
                "Prioritize protein in every meal",
                "Don't fear carbs - you need energy to build muscle",
                "Include healthy fats",
                "Eat frequently throughout the day"
            ]
        else:
            return [
                "Balance is key",
                "Focus on whole foods",
                "Everything in moderation",
                "Listen to your body"
            ]
