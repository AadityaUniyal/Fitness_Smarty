import json
import os
from datetime import datetime, time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app import models
from app.recommendation_engine import RecommendationEngine, WorkoutPlanner6Day, CycleSyncEngine, MealRecommender
from app.recovery_engine import calculate_recovery_score, is_exercise_gated
from .hybrid_ranker import HybridRanker


class UnifiedCoachService:
    """
    Unified Coach Service orchestrates the user's daily fitness and nutrition targets.
    It combines rules/local ML algorithms with Gemini narration.
    """

    def __init__(self, db: Session):
        self.db = db
        self.rec_engine = RecommendationEngine(db=db)
        self.workout_planner = WorkoutPlanner6Day()
        self.cycle_sync = CycleSyncEngine()
        self.meal_recommender = MealRecommender()
        self.ranker = HybridRanker(db=db)

    def get_daily_coach_plan(self, user_id: str) -> Dict[str, Any]:
        # 1. Resolve user
        user = self.db.query(models.EnhancedUser).filter(
            (models.EnhancedUser.clerk_user_id == user_id) | (models.EnhancedUser.id == user_id)
        ).first()
        if not user:
            raise ValueError("User not found")

        # Get or create UserProfile for extra details
        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == str(user.id)
        ).first()
        if not profile:
            profile = self.db.query(models.UserProfile).filter(
                models.UserProfile.user_id == user_id
            ).first()

        # Determine gender mode and coach mode
        gender = (profile.gender if profile else user.gender) or "male"
        gender_lower = gender.lower()
        femmecare_on = (profile.femmecare_enabled if profile else user.femmecare_enabled) or False
        menopause_mode = (profile.menopause_mode if profile else user.menopause_mode) or False
        pregnancy_mode = (profile.pregnancy_mode if profile else user.pregnancy_mode) or False

        gender_mode = "male"
        coach_mode = "standard_male"
        if gender_lower in ("female", "f"):
            if femmecare_on:
                gender_mode = "femmecare"
                if pregnancy_mode:
                    coach_mode = "pregnancy"
                elif menopause_mode:
                    coach_mode = "menopause"
                else:
                    coach_mode = "femmecare"
            else:
                gender_mode = "female"
                coach_mode = "standard_female"

        # Determine constraints applied list
        constraints_applied = []

        # 2. Get female cycle context if applicable
        cycle_phase = "all"
        cycle_advice = None
        if gender_mode == "femmecare" and not pregnancy_mode and not menopause_mode:
            latest_cycle = self.db.query(models.MenstrualCycleLog).filter(
                models.MenstrualCycleLog.user_id == str(user.id)
            ).order_by(models.MenstrualCycleLog.start_date.desc()).first()
            
            last_start = latest_cycle.start_date if latest_cycle else datetime.utcnow()
            cycle_len = latest_cycle.cycle_length_days if latest_cycle else 28
            cycle_phase = self.cycle_sync.get_current_phase(last_start, cycle_len)
            constraints_applied.append(f"cycle_{cycle_phase.lower()}")
            cycle_advice = self.cycle_sync.get_phase_advice(cycle_phase, user_profile={
                "femmecare_enabled": femmecare_on,
                "menopause_mode": menopause_mode,
                "pregnancy_mode": pregnancy_mode
            })
        elif pregnancy_mode:
            constraints_applied.append("pregnancy_mode")
            cycle_advice = self.cycle_sync.get_phase_advice("Pregnancy Safe Mode", user_profile={"pregnancy_mode": True})
        elif menopause_mode:
            constraints_applied.append("menopause_mode")
            cycle_advice = self.cycle_sync.get_phase_advice("Menopause Support", user_profile={"menopause_mode": True})

        # 3. Get Recovery Details
        recovery_context = {"score": 85, "muscle_group_recovery": {}}
        try:
            recovery_data = calculate_recovery_score(self.db, user.id)
            recovery_context = {
                "score": recovery_data.get("score", 85),
                "muscle_group_recovery": recovery_data.get("muscle_group_recovery", {})
            }
        except Exception:
            pass

        if recovery_context["score"] < 60:
            constraints_applied.append("recovery_low")
        elif recovery_context["score"] < 40:
            constraints_applied.append("recovery_critical")

        # 4. Today's logs & stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)

        meals_today = self.db.query(models.MealLog).filter(
            models.MealLog.user_id == user.id,
            models.MealLog.created_at >= today_start,
            models.MealLog.created_at <= today_end
        ).all()

        workouts_today = self.db.query(models.WorkoutLog).filter(
            models.WorkoutLog.user_id == user.id,
            models.WorkoutLog.created_at >= today_start,
            models.WorkoutLog.created_at <= today_end
        ).all()

        # Hydration
        water_logs = self.db.query(models.BiometricRecord).filter(
            models.BiometricRecord.user_id == str(user.id),
            models.BiometricRecord.category.in_(["hydration", "water"]),
            models.BiometricRecord.timestamp >= today_start,
            models.BiometricRecord.timestamp <= today_end
        ).all()
        hydration_ml = sum(float(w.value) for w in water_logs)

        calories_eaten = sum(float(m.total_calories or 0) for m in meals_today)
        protein_eaten = sum(float(m.total_protein or 0) for m in meals_today)
        carbs_eaten = sum(float(m.total_carbs or 0) for m in meals_today)
        fats_eaten = sum(float(m.total_fats or 0) for m in meals_today)

        # 5. Nutrition Targets & Macro Gap
        calorie_target = (profile.daily_calorie_target if profile else None) or 2200.0
        protein_target = (profile.protein_target_g if profile else None) or 150.0
        carbs_target = (profile.carbs_target_g if profile else None) or 220.0
        fat_target = (profile.fat_target_g if profile else None) or 70.0

        macro_gap = {
            "calories": max(0.0, float(calorie_target - calories_eaten)),
            "protein_g": max(0.0, float(protein_target - protein_eaten)),
            "carbs_g": max(0.0, float(carbs_target - carbs_eaten)),
            "fat_g": max(0.0, float(fat_target - fats_eaten))
        }

        if macro_gap["protein_g"] > 50.0:
            constraints_applied.append("protein_deficit")

        # 6. Workout recommendations from WorkoutPlanner6Day & HybridRanker
        goal = (profile.fitness_goal if profile else user.primary_goal) or "maintenance"
        difficulty = (profile.activity_level if profile else user.activity_level) or "Intermediate"
        diff_str = "Intermediate"
        if "light" in str(difficulty).lower() or "beg" in str(difficulty).lower():
            diff_str = "Beginner"
        elif "heavy" in str(difficulty).lower() or "adv" in str(difficulty).lower():
            diff_str = "Advanced"

        weekly_plan = self.workout_planner.generate_6day_plan(
            goal=goal,
            difficulty=diff_str,
            db=self.db,
            user_id=user.id
        )

        day_of_week = datetime.utcnow().isoweekday()
        today_session = next(
            (day for day in weekly_plan.get("weekly_plan", []) if day.get("day") == day_of_week),
            None
        )

        workout_rec = {"type": "rest", "exercises": [], "reasoning": "Rest day recommended for recovery."}
        if today_session and today_session.get("type") != "Rest":
            candidates = today_session.get("exercises", [])
            profile_dict = {
                "goal": goal,
                "training_level": diff_str,
                "coach_mode": coach_mode
            }
            ranked_exs = self.ranker.rank_exercises(
                candidates=candidates,
                profile=profile_dict,
                recovery_scores=recovery_context["muscle_group_recovery"],
                cycle_phase=cycle_phase
            )
            
            is_deload = recovery_context["score"] < 50
            rec_type = "deload" if is_deload else "single"
            
            reasoning = "Normal progression block."
            if is_deload:
                reasoning = f"Lighter intensity suggested due to recovery score of {recovery_context['score']}%."
            if cycle_advice:
                reasoning += f" Cycle sync advice: {cycle_advice.get('training')}"

            workout_rec = {
                "type": rec_type,
                "exercises": ranked_exs,
                "reasoning": reasoning
            }

        # 7. Meal recommendation
        profile_dict_meal = {
            "dietary_restrictions": profile.dietary_preferences if profile else [],
            "allergies": profile.allergies if profile else [],
            "goal": goal,
            "coach_mode": coach_mode
        }
        
        recommended_foods = self.ranker.rank_meals_from_db(
            profile=profile_dict_meal,
            macro_gap=macro_gap,
            limit=5
        )

        best_template = self.meal_recommender.recommend_next_meal(
            daily_targets={
                "protein_g": protein_target,
                "carbs_g": carbs_target,
                "fat_g": fat_target,
                "target_calories": calorie_target
            },
            consumed_so_far={
                "protein_g": protein_eaten,
                "carbs_g": carbs_eaten,
                "fat_g": fats_eaten,
                "calories": calories_eaten
            }
        )

        meal_rec = {
            "next_meal": best_template.get("name", "High Protein Salad") if best_template else "Balanced Meal",
            "foods": recommended_foods,
            "macro_gap": macro_gap
        }

        # 8. Daily Tasks
        daily_tasks = []
        db_tasks = self.db.query(models.DailyTask).filter(
            models.DailyTask.user_id == user.id,
            models.DailyTask.date >= today_start,
            models.DailyTask.date <= today_end
        ).all()

        if db_tasks:
            for t in db_tasks:
                daily_tasks.append({
                    "id": str(t.id),
                    "type": t.category,
                    "label": t.title,
                    "completed": t.is_completed,
                    "priority": "High" if t.priority >= 2 else "Medium"
                })
        else:
            default_tasks = [
                {"id": "hydrate", "type": "hydration", "label": "Drink 2.5L of water", "completed": hydration_ml >= 2500, "priority": "Medium"},
                {"id": "protein", "type": "nutrition", "label": f"Hit daily protein target ({protein_target}g)", "completed": protein_eaten >= protein_target, "priority": "High"},
                {"id": "move", "type": "activity", "label": "Complete today's training block", "completed": len(workouts_today) > 0, "priority": "High"},
                {"id": "log", "type": "nutrition", "label": "Log all meals", "completed": len(meals_today) >= 3, "priority": "Medium"}
            ]
            
            if gender_mode == "femmecare" and cycle_phase == "Menstrual":
                default_tasks.append({"id": "femmecare_rest", "type": "recovery", "label": "Perform restorative stretching", "completed": False, "priority": "High"})
            elif recovery_context["score"] < 50:
                default_tasks.append({"id": "recovery_sleep", "type": "recovery", "label": "Sleep priority: Wind down early", "completed": False, "priority": "High"})

            for dt in default_tasks:
                daily_tasks.append(dt)

        # 9. Next Action Logic
        pending_tasks = [t for t in daily_tasks if not t["completed"]]
        
        next_action = {
            "title": "Start with your first task",
            "route": "/dashboard",
            "priority": "High",
            "detail": "Pick the highest priority task and get going!"
        }

        if len(pending_tasks) == 0:
            next_action = {
                "title": "All tasks complete! Review your day",
                "route": "/progress",
                "priority": "Low",
                "detail": "Great progress. Check your stats and plan tomorrow."
            }
        else:
            urgent = [t for t in pending_tasks if t["priority"] == "High"]
            pick = urgent[0] if urgent else pending_tasks[0]
            route = "/nutrition" if pick["type"] in ("nutrition", "hydration") else "/workout" if pick["type"] == "activity" else "/dashboard"
            
            next_action = {
                "title": f"Next up: {pick['label']}",
                "route": route,
                "priority": pick["priority"],
                "detail": "Keep the momentum going."
            }

        # 10. Gemini Pass
        coach_summary = self._generate_gemini_narration(
            user_profile={
                "gender": gender,
                "goal": goal,
                "recovery_score": recovery_context["score"],
                "cycle_phase": cycle_phase if gender_mode == "femmecare" else None,
                "menopause": menopause_mode,
                "pregnancy": pregnancy_mode
            },
            today_metrics={
                "calories_eaten": calories_eaten,
                "protein_eaten": protein_eaten,
                "hydration_ml": hydration_ml
            },
            workout_rec=workout_rec,
            meal_rec=meal_rec,
            next_action=next_action
        )

        return {
            "coach_summary": coach_summary,
            "gender_mode": gender_mode,
            "today_focus": {
                "training": workout_rec.get("reasoning", "Active recovery day."),
                "nutrition": f"Aim for {calorie_target} kcal, prioritizing protein."
            },
            "workout_recommendation": workout_rec,
            "meal_recommendation": meal_rec,
            "daily_tasks": daily_tasks,
            "next_action": next_action,
            "constraints_applied": constraints_applied
        }

    def _generate_gemini_narration(self, user_profile: Dict, today_metrics: Dict, workout_rec: Dict, meal_rec: Dict, next_action: Dict) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "")
        fallback = f"Ready for today's focus? Today's workout focuses on {workout_rec.get('reasoning')}. Your next meal should target remaining macros."
        if not api_key:
            return fallback

        prompt = f"""
You are SMARTY AI, an expert, concise personal coach.
Given the structured plan made by local algorithms below, output a short (exactly 2 sentences) natural language daily coach briefing for the user's dashboard.
DO NOT invent or add any new workout routines, macro counts, or target numbers. Stick strictly to narrating the structured decisions provided.

Profile Context:
- Goal: {user_profile.get("goal")}
- Gender: {user_profile.get("gender")}
- Recovery: {user_profile.get("recovery_score")}%
- Cycle Phase: {user_profile.get("cycle_phase")}
- Pregnancy Mode: {user_profile.get("pregnancy")}
- Menopause Mode: {user_profile.get("menopause")}

Today's Progress:
- Calories Consumed: {today_metrics.get("calories_eaten")}
- Protein Consumed: {today_metrics.get("protein_eaten")}g
- Hydration: {today_metrics.get("hydration_ml")}ml

Plan Decisions:
- Recommended Workout type: {workout_rec.get("type")} ({workout_rec.get("reasoning")})
- Recommended next meal target: {meal_rec.get("next_meal")}
- Priority Action: {next_action.get("title")}

Concise daily summary:
"""
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
            )
            txt = response.text or ""
            return txt.strip()
        except Exception:
            return fallback
