"""
Advanced Recommendation Engine

Next-level features:
1. Goal Timeline Predictor - "Reach your goal in X weeks"
2. Smart Meal Recommender - Suggests what to eat next
3. Food Swap Engine - "Replace X with Y"
4. Portion Optimizer - Perfect serving sizes
5. Meal Timing Intelligence - When to eat based on activity
"""

from sqlalchemy.orm import Session
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math


class CycleSyncEngine:
    """Algorithm to synchronize training and nutrition with the menstrual cycle."""
    
    PHASES = {
        "Menstrual": (1, 5),   # Days 1-5
        "Follicular": (6, 12),  # Days 6-12
        "Ovulatory": (13, 16), # Days 13-16
        "Luteal": (17, 28)     # Days 17-28
    }

    # Safe pregnancy/postpartum exercise contraindications (ACOG-aligned exclusions)
    PREGNANCY_CONTRAINDICATED_KEYWORDS = [
        "supine", "crunch", "situp", "fall risk", "contact sports", "heavy overhead press", "clean and jerk", "snatch"
    ]

    def get_current_phase(self, last_period_start: datetime, cycle_length: int = 28) -> str:
        """Calculate current cycle phase based on start date."""
        if not last_period_start:
            return "all"
            
        days_since = (datetime.utcnow() - last_period_start).days % cycle_length + 1
        for phase, (start, end) in self.PHASES.items():
            if start <= days_since <= end:
                return phase
        return "Luteal" 

    def get_phase_advice(self, phase: str, symptoms: List[str] = None, user_profile: Dict = None) -> Dict:
        """Return tactical training and nutrition advice for the phase, adapted dynamically by logged symptoms or life stages."""
        symptoms = symptoms or []
        user_profile = user_profile or {}

        # 1. Check for Perimenopause/Menopause Mode
        if user_profile.get("menopause_mode"):
            return {
                "phase": "Menopause Support",
                "training": "Accelerated resistance training focus: Target lifting weights 3-4x per week to preserve muscle mass, support bone density, and improve joint health.",
                "nutrition": "Prioritize bone-health nutrition: High calcium (dairy, fortified milks) and Vitamin D sources, combined with 1.6-2.0g/kg protein intake.",
                "focus": "Strength & Bone Preservation",
                "intensity_limit": "High",
                "bio_context": "Post-reproductive phase. Focus is on long-term joint health, strength maintenance, and metabolic regulation."
            }

        # 2. Check for Pregnancy/Postpartum Mode
        if user_profile.get("pregnancy_mode"):
            return {
                "phase": "Pregnancy Safe Mode",
                "training": "ACOG-aligned activity: Maintain low-impact cardio, pelvic floor exercises (Kegels), and bodyweight strength. Avoid exercises lying flat on your back after the first trimester.",
                "nutrition": "Caloric density support: Emphasize folate, iron, calcium, and adequate hydration. Eat small, frequent meals to aid digestion.",
                "focus": "Safe Conditioning & pelvic strength",
                "intensity_limit": "Moderate",
                "bio_context": "Pregnancy/Postpartum phase. Priority is safe movement, posture, and core/pelvic stability."
            }

        # Base phase advice
        advice = {
            "Menstrual": {
                "training": "Focus on restorative movement: Yoga, walking, and light stretching.",
                "nutrition": "Prioritize iron-rich foods (red meat, spinach, lentils) paired with vitamin C sources (oranges, bell peppers) to boost absorption.",
                "focus": "Recovery & Comfort",
                "intensity_limit": "Low",
                "bio_context": "Estrogen and Progesterone are at their lowest. Focus on replenishment."
            },
            "Follicular": {
                "training": "Energy is rising. Best time for progressive overload and building muscle.",
                "nutrition": "Support rising estrogen with fermented foods and complex carbs for stamina.",
                "focus": "Strength & Growth",
                "intensity_limit": "High",
                "bio_context": "Estrogen is climbing, increasing insulin sensitivity and strength capacity."
            },
            "Ovulatory": {
                "training": "Peak performance window! Max effort HIIT and heavy lifting.",
                "nutrition": "Fiber-rich vegetables and lean proteins to support the hormonal peak.",
                "focus": "Power & Endurance",
                "intensity_limit": "Maximum",
                "bio_context": "Testosterone and Estrogen peak. Energy and confidence are highest."
            },
            "Luteal": {
                "training": "Metabolism is higher but endurance might dip. Steady state cardio is ideal.",
                "nutrition": "Increase healthy fats and protein. Magnesium-rich foods for mood stability.",
                "focus": "Maintenance & Resilience",
                "intensity_limit": "Moderate",
                "bio_context": "Progesterone peaks, increasing body temperature and metabolic rate."
            },
            "all": {
                "training": "Maintain consistent movement patterns across all phases.",
                "nutrition": "Focus on high-quality whole foods and consistent hydration.",
                "focus": "General Wellness",
                "intensity_limit": "Variable",
                "bio_context": "General recommendation for non-tracked or inconsistent cycles."
            }
        }
        
        phase_advice = advice.get(phase, advice["all"]).copy()

        # Dynamic symptom adaptation overrides
        has_fatigue = any(s in symptoms for s in ["Fatigue", "fatigue", "tired", "Low Energy"])
        has_cramps = any(s in symptoms for s in ["Cramps", "cramping", "pain", "Back Pain"])
        
        if has_fatigue or has_cramps:
            phase_advice["training"] = f"Lighter session suggested today because you logged high fatigue or cramping: {phase_advice['training']} (Scaled down by 25-50%)."
            phase_advice["intensity_limit"] = "Low-Moderate"
            phase_advice["focus"] = "Symptom Management"

        return phase_advice

    def get_recommended_exercises(self, db: Session, phase: str, limit: int = 6, user_profile: Dict = None):
        """Fetch specialized exercises for the current phase, applying pregnancy filters if needed."""
        from app.models import FemaleExerciseItem
        user_profile = user_profile or {}
        
        query = db.query(FemaleExerciseItem)
        
        # Apply pregnancy contraindications filter
        if user_profile.get("pregnancy_mode"):
            # Exclude contraindicated exercises
            for kw in self.PREGNANCY_CONTRAINDICATED_KEYWORDS:
                query = query.filter(~FemaleExerciseItem.name.ilike(f"%{kw}%"))
                query = query.filter(~FemaleExerciseItem.description.ilike(f"%{kw}%"))
        
        if phase != 'all' and not user_profile.get("menopause_mode") and not user_profile.get("pregnancy_mode"):
            query = query.filter(
                (FemaleExerciseItem.suitable_cycle_phase == phase) | 
                (FemaleExerciseItem.suitable_cycle_phase == 'all')
            )
            
        return query.order_by(FemaleExerciseItem.calories_per_min.desc()).limit(limit).all()



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
    """Calculate optimal portion sizes based on targets using constrained greedy local search"""
    
    def __init__(self):
        pass
    
    def optimize_portions(self, meal_components: List[Dict], 
                          target_calories: float, target_protein: float) -> Dict:
        """
        Calculate optimal serving sizes using greedy-with-local-search optimization.
        
        Args:
            meal_components: List of foods with nutrition per 100g
            target_calories: Desired total calories
            target_protein: Desired total protein
        
        Returns:
            Optimized portion sizes in grams and resulting nutrition
        """
        if not meal_components:
            return {
                'portions_grams': {},
                'total_nutrition': {'calories': 0.0, 'protein_g': 0.0, 'carbs_g': 0.0, 'fat_g': 0.0},
                'accuracy': {'calories_diff': 0.0, 'protein_diff': 0.0}
            }

        # Setup optimizer boundaries and steps
        min_portion = 30.0   # minimum serving size in grams
        max_portion = 400.0  # maximum serving size in grams
        step_size = 5.0      # adjustment step size
        
        # Initialize portions to 100g
        portions = {c['name']: 100.0 for c in meal_components}
        
        def calculate_nutrition(curr_portions: Dict[str, float]) -> Dict[str, float]:
            totals = {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0}
            for c in meal_components:
                name = c['name']
                nut = c['nutrition_per_100g']
                mult = curr_portions[name] / 100.0
                totals['calories'] += nut.get('calories', 0.0) * mult
                totals['protein'] += nut.get('protein', 0.0) * mult
                totals['carbs'] += nut.get('carbs', 0.0) * mult
                totals['fat'] += nut.get('fat', 0.0) * mult
            return totals

        def calculate_loss(curr_portions: Dict[str, float]) -> float:
            totals = calculate_nutrition(curr_portions)
            # Protein mismatch is weighted heavily (weight=25.0) relative to calories
            cal_diff = totals['calories'] - target_calories
            prot_diff = totals['protein'] - target_protein
            return (cal_diff ** 2) + 25.0 * (prot_diff ** 2)

        # Iterative local search
        improved = True
        max_iterations = 200
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            best_loss = calculate_loss(portions)
            best_adjustment = None
            
            # Try increasing or decreasing each food component
            for c in meal_components:
                name = c['name']
                for direction in [-1.0, 1.0]:
                    new_val = portions[name] + direction * step_size
                    if min_portion <= new_val <= max_portion:
                        # Create test candidate
                        candidate = portions.copy()
                        candidate[name] = new_val
                        loss = calculate_loss(candidate)
                        
                        if loss < best_loss - 0.01:
                            best_loss = loss
                            best_adjustment = (name, new_val)
                            
            if best_adjustment:
                portions[best_adjustment[0]] = best_adjustment[1]
                improved = True

        # Calculate final results
        final_nut = calculate_nutrition(portions)
        
        return {
            'portions_grams': {name: round(g, 1) for name, g in portions.items()},
            'total_nutrition': {
                'calories': round(final_nut['calories'], 1),
                'protein_g': round(final_nut['protein'], 1),
                'carbs_g': round(final_nut['carbs'], 1),
                'fat_g': round(final_nut['fat'], 1)
            },
            'accuracy': {
                'calories_diff': round(abs(final_nut['calories'] - target_calories), 1),
                'protein_diff': round(abs(final_nut['protein'] - target_protein), 1)
            }
        } }


# Export all recommendation engines
class NutritionalPattern:
    """Represents nutritional pattern analysis"""
    def __init__(self, deficiencies=None, excesses=None, balance_score=0.5):
        self.deficiencies = deficiencies or []
        self.excesses = excesses or []
        self.balance_score = balance_score


class RecommendationRequest:
    """Request object for recommendation engine"""
    def __init__(self, user_id=None, goal_type=None, daily_targets=None, consumed_today=None):
        self.user_id = user_id
        self.goal_type = goal_type
        self.daily_targets = daily_targets or {}
        self.consumed_today = consumed_today or {}


class WorkoutPlanner6Day:
    """Generate 6-day workout splits based on goal and difficulty"""
    
    SPLITS = {
        'ppl': [
            {'day': 1, 'type': 'Push', 'focus': 'Chest, Shoulders, Triceps'},
            {'day': 2, 'type': 'Pull', 'focus': 'Back, Biceps'},
            {'day': 3, 'type': 'Legs', 'focus': 'Quads, Hamstrings, Glutes, Calves'},
            {'day': 4, 'type': 'Push', 'focus': 'Chest, Shoulders, Triceps'},
            {'day': 5, 'type': 'Pull', 'focus': 'Back, Biceps'},
            {'day': 6, 'type': 'Legs', 'focus': 'Quads, Hamstrings, Glutes, Calves'},
            {'day': 7, 'type': 'Rest', 'focus': 'Recovery'}
        ],
        'upper_lower': [
            {'day': 1, 'type': 'Upper', 'focus': 'Chest, Back, Shoulders, Arms'},
            {'day': 2, 'type': 'Lower', 'focus': 'Legs, Core'},
            {'day': 3, 'type': 'Upper', 'focus': 'Chest, Back, Shoulders, Arms'},
            {'day': 4, 'type': 'Lower', 'focus': 'Legs, Core'},
            {'day': 5, 'type': 'Upper', 'focus': 'Chest, Back, Shoulders, Arms'},
            {'day': 6, 'type': 'Lower', 'focus': 'Legs, Core'},
            {'day': 7, 'type': 'Rest', 'focus': 'Recovery'}
        ]
    }

<<<<<<< HEAD
    def generate_6day_plan(self, goal: str, difficulty: str, db: Session, user_id: Optional[str] = None) -> Dict:
        """Generate a 6-day plan with specific exercises from DB, factoring in muscle recovery gating and FemmeCare resistance priority."""
        from app.models import ExerciseItem, EnhancedUser
        from app.recovery_engine import calculate_recovery_score, is_exercise_gated
        
        # Correct gender/module bias: ensure strength splits are preferred for FemmeCare/Menopause mode
        femmecare_enabled = False
        menopause_mode = False
        pregnancy_mode = False
        
        if db and user_id:
            user = db.query(EnhancedUser).filter(
                (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
            ).first()
            if user:
                femmecare_enabled = user.femmecare_enabled or False
                menopause_mode = user.menopause_mode or False
                pregnancy_mode = user.pregnancy_mode or False

        # If user is in menopause or FemmeCare is enabled, prioritize strength-based PPL split
        if menopause_mode or femmecare_enabled:
            split_type = 'ppl'
        else:
            split_type = 'ppl' if 'muscle' in goal.lower() else 'upper_lower'
            
        split = self.SPLITS[split_type]

        
        # Calculate muscle recovery scores if user_id is provided
        recovery_scores = {}
        if user_id:
            try:
                rec_data = calculate_recovery_score(db, user_id)
                recovery_scores = rec_data.get("muscle_group_recovery", {})
            except Exception as e:
                print(f"[!] Error loading recovery score for gating: {e}")

=======
    def generate_6day_plan(self, goal: str, difficulty: str, db: Session) -> Dict:
        """Generate a 6-day plan with specific exercises from DB"""
        from app.models import ExerciseItem
        
        split_type = 'ppl' if 'muscle' in goal.lower() else 'upper_lower'
        split = self.SPLITS[split_type]
        
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
        plan = []
        for day in split:
            if day['type'] == 'Rest':
                plan.append({**day, 'exercises': []})
                continue
                
            # Filter exercises for the focus muscle groups
            muscles = [m.strip() for m in day['focus'].split(',')]
            
            day_exercises = []
            for muscle in muscles:
                # Get exercises for this muscle and difficulty
                query = db.query(ExerciseItem).filter(
                    ExerciseItem.targeted_muscle.ilike(f"%{muscle}%"),
                    ExerciseItem.difficulty.ilike(f"%{difficulty}%")
                ).limit(3).all() # 3 per primary muscle in the group
                
                for ex in query:
<<<<<<< HEAD
                    # Check if gated due to muscle recovery status
                    gated, reason = is_exercise_gated(ex.name, recovery_scores, threshold=50.0)
                    
=======
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
                    day_exercises.append({
                        "id": ex.id,
                        "name": ex.name,
                        "muscle": ex.targeted_muscle,
                        "reps": "10-12" if difficulty == "Beginner" else "8-10",
                        "sets": 3 if difficulty == "Beginner" else 4,
<<<<<<< HEAD
                        "cal_per_rep": ex.calories_per_rep or 0.1,
                        "restricted": gated,
                        "restriction_reason": reason if gated else ""
=======
                        "cal_per_rep": ex.calories_per_rep or 0.1
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
                    })
            
            plan.append({**day, 'exercises': day_exercises})
            
        return {
            "split_type": split_type,
            "goal": goal,
            "difficulty": difficulty,
<<<<<<< HEAD
            "weekly_plan": plan,
            "muscle_recovery_context": {m: round(v, 1) for m, v in recovery_scores.items()} if recovery_scores else None
        }


class UserRecommendation:
    """Helper class matching RecommendationItem schema"""
    def __init__(self, id_val: str, rec_type: str, title: str, description: str, confidence_score: float, is_read: bool, created_at: datetime, expires_at: Optional[datetime] = None):
        self.id = id_val
        self.recommendation_type = rec_type
        self.title = title
        self.description = description
        self.confidence_score = confidence_score
        self.is_read = is_read
        self.created_at = created_at
        self.expires_at = expires_at or (created_at + timedelta(days=1))


=======
            "weekly_plan": plan
        }


>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
class RecommendationEngine:
    """Unified recommendation engine facade"""
    
    def __init__(self, db=None):
        self.db = db
        self.goal_predictor = GoalPredictor()
        self.meal_recommender = MealRecommender()
        self.food_swap_engine = FoodSwapEngine()
        self.portion_optimizer = PortionOptimizer()
        self.workout_planner = WorkoutPlanner6Day()
<<<<<<< HEAD
        self.cycle_sync_engine = CycleSyncEngine()
        
        # Lazy load cluster engine
        self._cluster_engine = None

    def _get_cluster_engine(self):
        if self._cluster_engine is None:
            try:
                from app.training.user_clustering import UserClusterEngine
                self._cluster_engine = UserClusterEngine()
                self._cluster_engine._load_model()
            except Exception as e:
                print(f"[!] Could not initialize UserClusterEngine: {e}")
        return self._cluster_engine

    def get_user_recommendations(self, user_id: str, include_read: bool = False, limit: int = 10) -> List[UserRecommendation]:
        """
        Retrieve and generate personalized recommendations using real ML user clustering.
        """
        from app import models
        import uuid
        
        # Try to resolve user
        user = None
        if self.db:
            # Check by Clerk ID first
            user = self.db.query(models.EnhancedUser).filter(models.EnhancedUser.clerk_user_id == user_id).first()
            if not user:
                # Fallback to auto-incremented integer ID
                try:
                    user_int_id = int(user_id)
                    user = self.db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_int_id).first()
                except ValueError:
                    pass

        # If user not found, generate generic fallback recommendations
        if not user:
            return [
                UserRecommendation(
                    id_val="gen_1",
                    rec_type="nutrition",
                    title="Focus on Protein Intake",
                    description="Aim to consume high-quality protein (chicken, tofu, eggs) with every meal.",
                    confidence_score=0.9,
                    is_read=False,
                    created_at=datetime.utcnow()
                ),
                UserRecommendation(
                    id_val="gen_2",
                    rec_type="exercise",
                    title="Stay Active Regularly",
                    description="Incorporate 30 minutes of moderate activity into your daily routine.",
                    confidence_score=0.85,
                    is_read=False,
                    created_at=datetime.utcnow()
                )
            ][:limit]

        # Use cluster engine if available to fetch archetype details
        cluster_label = "General Wellness"
        cluster_desc = "Standard baseline health optimization"
        cluster_confidence = 0.5
        cluster_matched = False
        
        engine = self._get_cluster_engine()
        if engine and engine.kmeans:
            try:
                # Construct profile dictionary matching training format
                profile_dict = {
                    "age": user.age or 30,
                    "weight_kg": user.weight_kg or 70.0,
                    "height_cm": user.height_cm or 170.0,
                    "gender": user.gender or "male",
                    "goal": user.primary_goal or "maintenance",
                    "activity_level": user.activity_level or "moderate",
                }
                
                # Derive BMI, BMR, TDEE for profile dict
                from app.nutrition_analytics import NutritionAnalytics
                analytics = NutritionAnalytics()
                bmr = analytics.calculate_bmr(profile_dict["weight_kg"], profile_dict["height_cm"], profile_dict["age"], profile_dict["gender"])
                tdee = analytics.calculate_tdee(bmr, profile_dict["activity_level"])
                profile_dict["bmi"] = profile_dict["weight_kg"] / ((profile_dict["height_cm"] / 100.0) ** 2)
                profile_dict["bmr"] = bmr
                profile_dict["tdee"] = tdee
                
                # Run the trained KMeans model
                assignment = engine.assign_cluster(profile_dict)
                cluster_label = assignment.get("cluster_label", cluster_label)
                cluster_desc = assignment.get("cluster_description", cluster_desc)
                cluster_confidence = assignment.get("confidence", cluster_confidence)
                cluster_matched = True
            except Exception as e:
                print(f"[!] Clustering assignment failed: {e}")

        # Construct specific advice based on cluster matching
        recs = []
        now = datetime.utcnow()
        
        if user.primary_goal and "muscle" in user.primary_goal.lower():
            recs.append(UserRecommendation(
                id_val=f"rec_muscle_{user.id}_1",
                rec_type="nutrition",
                title="Prioritize Protein & Calorie Surplus",
                description=f"Your cluster ({cluster_label}) indicates a high requirement for energy. Target a surplus to build muscle.",
                confidence_score=round(float(cluster_confidence), 2),
                is_read=False,
                created_at=now
            ))
            recs.append(UserRecommendation(
                id_val=f"rec_muscle_{user.id}_2",
                rec_type="exercise",
                title="Progressive Overload Session",
                description=f"Cluster Profile: {cluster_desc}. Perform compound lifts (squats, deadlifts) with 8-10 reps per set.",
                confidence_score=0.9,
                is_read=False,
                created_at=now
            ))
        elif user.primary_goal and "loss" in user.primary_goal.lower():
            recs.append(UserRecommendation(
                id_val=f"rec_loss_{user.id}_1",
                rec_type="nutrition",
                title="Calorie Deficit Strategy",
                description=f"Archetype Segment: {cluster_label}. Aim for a daily 500-calorie deficit to trigger safe fat loss.",
                confidence_score=round(float(cluster_confidence), 2),
                is_read=False,
                created_at=now
            ))
            recs.append(UserRecommendation(
                id_val=f"rec_loss_{user.id}_2",
                rec_type="exercise",
                title="Steady-State Cardio & High Neat",
                description=f"Cluster Profile: {cluster_desc}. Prioritize daily steps and add 30 mins of zone 2 cardio.",
                confidence_score=0.88,
                is_read=False,
                created_at=now
            ))
        else:
            # General / Maintenance
            recs.append(UserRecommendation(
                id_val=f"rec_maint_{user.id}_1",
                rec_type="nutrition",
                title="Balanced Macronutrient Focus",
                description=f"Cluster Segment: {cluster_label}. Aim for 40% carbs, 30% protein, and 30% fats to maintain body composition.",
                confidence_score=round(float(cluster_confidence), 2),
                is_read=False,
                created_at=now
            ))
            recs.append(UserRecommendation(
                id_val=f"rec_maint_{user.id}_2",
                rec_type="exercise",
                title="Mixed Cardiovascular & Resistance Training",
                description=f"Archetype details: {cluster_desc}. Focus on metabolic health and endurance maintenance.",
                confidence_score=0.8,
                is_read=False,
                created_at=now
            ))
            
        # Add a default reminder for water or sleep
        recs.append(UserRecommendation(
            id_val=f"rec_recovery_{user.id}",
            rec_type="recovery",
            title="Optimize Recovery Protocols",
            description=f"Cluster advice: {cluster_desc}. Aim for 7-8 hours of sleep to match your active segment requirement.",
            confidence_score=0.75,
            is_read=False,
            created_at=now
        ))

        return recs[:limit]

    def get_cycle_sync_advice(self, last_period_start: datetime, cycle_length: int = 28, user_id: str = None, symptoms: List[str] = None):
        """Get advice and exercises for the current cycle phase, adapted dynamically to user states and logged history."""
        from app.models import EnhancedUser, MenstrualCycleLog
        from app.security_encryption import decrypt_value
        
        user_profile = {"menopause_mode": False, "pregnancy_mode": False}
        learned_cycle_length = cycle_length
        anomaly_warning = ""
        cycle_history_stats = None

        if self.db and user_id:
            user = self.db.query(EnhancedUser).filter(
                (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
            ).first()
            if user:
                user_profile["menopause_mode"] = user.menopause_mode or False
                user_profile["pregnancy_mode"] = user.pregnancy_mode or False
                user_profile["local_only"] = user.local_only or False

            # Retrieve previous cycle logs to calculate adaptive rolling average and variance
            logs = self.db.query(MenstrualCycleLog).filter(
                MenstrualCycleLog.user_id == user_id
            ).order_by(MenstrualCycleLog.start_date.desc()).all()

            if logs:
                # Decrypt symptoms and notes if needed
                for log in logs:
                    if log.encrypted_symptoms:
                        try:
                            dec = decrypt_value(log.encrypted_symptoms)
                            log.symptoms = dec.split(",") if dec else []
                        except Exception:
                            pass

                # If we have multiple logs, compute intervals between them to find real cycle lengths
                if len(logs) >= 2:
                    lengths = []
                    # Compute dates differences
                    for i in range(len(logs) - 1):
                        diff = (logs[i].start_date - logs[i+1].start_date).days
                        # Filter out unrealistic values (e.g. less than 15 days or more than 90 days)
                        if 15 <= diff <= 90:
                            lengths.append(diff)
                    
                    if lengths:
                        avg_len = sum(lengths) / len(lengths)
                        learned_cycle_length = int(round(avg_len))
                        
                        # Calculate variance/standard deviation
                        variance = sum((x - avg_len) ** 2 for x in lengths) / len(lengths)
                        std_dev = math.sqrt(variance)

                        cycle_history_stats = {
                            "average_cycle_length": round(avg_len, 1),
                            "std_dev_days": round(std_dev, 1),
                            "logged_cycles_count": len(logs)
                        }

                        # Outlier detection (rolling z-score / standard dev limit)
                        # Flag cycle anomalies gently: if last cycle diff deviates by > 6 days from rolling average
                        if len(lengths) >= 2 and abs(lengths[0] - avg_len) > 6:
                            anomaly_warning = (
                                f"Your last cycle length ({lengths[0]} days) was a meaningful outlier from your usual "
                                f"pattern of {round(avg_len, 1)} days. We recommend mentioning this variation to your "
                                "doctor or gynecologist if this variation persists."
                            )

        # Get phase advice & exercises
        phase = self.cycle_sync_engine.get_current_phase(last_period_start, learned_cycle_length)
        advice = self.cycle_sync_engine.get_phase_advice(phase, symptoms=symptoms, user_profile=user_profile)
        
        # Pull exercises
        exercises = []
        if self.db:
            exercises = self.cycle_sync_engine.get_recommended_exercises(self.db, phase, user_profile=user_profile)
            
        return {
            "phase": phase,
            "advice": advice,
            "learned_cycle_length": learned_cycle_length,
            "anomaly_warning": anomaly_warning,
            "cycle_history_stats": cycle_history_stats,
            "user_profile": user_profile,
            "recommended_exercises": [
                {
                    "id": ex.id,
                    "name": ex.name,
                    "muscle": ex.targeted_muscle,
                    "difficulty": ex.difficulty,
                    "equipment": ex.equipment,
                    "calories_per_min": ex.calories_per_min,
                    "description": ex.description
                } for ex in exercises
            ]
        }

=======
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
    
    def generate_workout_plan(self, goal: str, difficulty: str):
        if not self.db: return {}
        return self.workout_planner.generate_6day_plan(goal, difficulty, self.db)
    
    def predict_goal_timeline(self, current_weight, target_weight, goal, avg_daily_deficit):
        return self.goal_predictor.predict_timeline(current_weight, target_weight, goal, avg_daily_deficit)
    
    def recommend_next_meal(self, daily_targets, consumed_so_far, time_of_day='lunch'):
        return self.meal_recommender.recommend_next_meal(daily_targets, consumed_so_far, time_of_day)
    
    def suggest_food_swaps(self, detected_foods):
        return self.food_swap_engine.suggest_swaps(detected_foods)
    
    def optimize_portions(self, meal_components, target_calories, target_protein):
        return self.portion_optimizer.optimize_portions(meal_components, target_calories, target_protein)
    
    def analyze_nutritional_patterns(self, user_id):
        """Analyze nutritional patterns - returns NutritionalPattern"""
        return NutritionalPattern()
    
<<<<<<< HEAD
    def recommend_foods_by_goal_and_muscle(self, goal: str, target_muscle: str, limit: int = 10, user_id: str = None):
        """Recommend foods tailored to a specific aim and muscle group, adjusted for menstrual iron/vitamin C sync or menopause bone-health."""
        if not self.db:
            return []
            
        from app.models import FoodItem, EnhancedUser, MenstrualCycleLog
        from sqlalchemy import or_
        
        # Check user modes
        is_menstrual = False
        is_menopause = False
        if user_id:
            user = self.db.query(EnhancedUser).filter(
                (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
            ).first()
            if user and user.femmecare_enabled:
                if user.menopause_mode:
                    is_menopause = True
                elif not user.pregnancy_mode:
                    # Check cycle phase
                    log = self.db.query(MenstrualCycleLog).filter(
                        MenstrualCycleLog.user_id == user_id
                    ).order_by(MenstrualCycleLog.start_date.desc()).first()
                    if log:
                        phase = self.cycle_sync_engine.get_current_phase(log.start_date, log.cycle_length_days)
                        if phase == "Menstrual":
                            is_menstrual = True

=======
    def recommend_foods_by_goal_and_muscle(self, goal: str, target_muscle: str, limit: int = 10):
        """Recommend foods tailored to a specific aim and muscle group"""
        if not self.db:
            return []
            
        from app.models import FoodItem
        from sqlalchemy import or_
        
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
        query = self.db.query(FoodItem)
        
        if goal:
            goal_lower = goal.lower().replace(" ", "_")
            query = query.filter(or_(
                FoodItem.recommended_for_goal.ilike(f"%{goal_lower}%"),
                FoodItem.recommended_for_goal.ilike("%general%")
            ))
            
        if target_muscle:
            muscle_lower = target_muscle.lower()
            query = query.filter(or_(
                FoodItem.target_muscle_group.ilike(f"%{muscle_lower}%"),
                FoodItem.target_muscle_group.ilike("%all%"),
                FoodItem.target_muscle_group.ilike("%full_body%")
            ))
            
<<<<<<< HEAD
        # Extract matches
        foods = query.all()

        # Custom sort logic based on FemmeCare requirements:
        # Menstrual -> weight iron/vitamin C foods higher
        # Menopause -> weight calcium/vitamin D/protein foods higher
        def scoring_function(food):
            score = 0.0
            name_lower = food.name.lower()
            
            # Base macro factors
            if goal and 'muscle' in goal.lower():
                score += food.protein * 0.5
            elif goal and 'loss' in goal.lower():
                score -= food.calories * 0.02
                
            if food.is_elite:
                score += 15.0
                
            # FemmeCare adjustments
            if is_menstrual:
                # Target iron-rich and vitamin C foods
                iron_rich = ["spinach", "beef", "lentil", "dark chocolate", "chia", "egg", "salmon", "kale"]
                vit_c = ["orange", "bell pepper", "broccoli", "strawberries", "lemon"]
                if any(x in name_lower for x in iron_rich):
                    score += 20.0
                if any(x in name_lower for x in vit_c):
                    score += 15.0
                    
            if is_menopause:
                # Target bone health: calcium, vitamin D, protein
                bone_health = ["yogurt", "milk", "cottage cheese", "chia", "almond", "salmon", "tofu", "broccoli"]
                if any(x in name_lower for x in bone_health):
                    score += 20.0
                if food.protein > 10.0:
                    score += 10.0

            return score

        # Sort descending by score
        foods.sort(key=scoring_function, reverse=True)
        return foods[:limit]

=======
        # Prioritize elite foods and order by appropriate macro based on goal
        if goal and 'muscle' in goal.lower():
            query = query.order_by(FoodItem.is_elite.desc(), FoodItem.protein.desc())
        elif goal and 'loss' in goal.lower():
            query = query.order_by(FoodItem.is_elite.desc(), FoodItem.calories.asc())
        else:
            query = query.order_by(FoodItem.is_elite.desc())
            
        return query.limit(limit).all()
>>>>>>> 0353e412dc8715e7f787c8e95e1aca44f058882a
    
    def calculate_workout_burn(self, exercises_performed: List[Dict]) -> Dict:
        """
        Calculate total calories burned based on reps, sets, and cal_per_rep.
        exercises_performed: List of {'exercise_id': int, 'reps': int, 'sets': int}
        """
        if not self.db: return {"total_burn": 0, "breakdown": []}
        
        from app.models import ExerciseItem
        total_burn = 0.0
        breakdown = []
        
        for entry in exercises_performed:
            ex = self.db.query(ExerciseItem).filter_by(id=entry['exercise_id']).first()
            if ex:
                burn = entry['reps'] * entry['sets'] * (ex.calories_per_rep or 0.1)
                total_burn += burn
                breakdown.append({
                    "name": ex.name,
                    "reps": entry['reps'],
                    "sets": entry['sets'],
                    "calories": round(burn, 1)
                })
        
        return {
            "total_burn": round(total_burn, 1),
            "breakdown": breakdown
        }

    def get_recommendations(self, request: RecommendationRequest):
        """Get general recommendations based on request"""
        return {
            "recommendations": [],
            "total": 0,
            "user_id": request.user_id
        }


__all__ = [
    'GoalPredictor', 'MealRecommender', 'FoodSwapEngine', 'PortionOptimizer',
    'RecommendationEngine', 'RecommendationRequest', 'NutritionalPattern',
    'CycleSyncEngine'
]
