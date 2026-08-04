import json
import os
from datetime import datetime, time, timedelta
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
    # Class-level in-memory cache for Gemini coach briefings to minimize API overhead
    _briefing_cache: Dict[str, str] = {}

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

        # 10. Gemini Pass (with Local Cache optimization)
        cache_key = f"{user.id}_{today_start.date().isoformat()}_{calories_eaten}_{protein_eaten}_{hydration_ml}_{recovery_context['score']}"
        if cache_key in self._briefing_cache:
            coach_summary = self._briefing_cache[cache_key]
        else:
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
            self._briefing_cache[cache_key] = coach_summary

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

    def get_explainable_coach(self, user_id: str) -> Dict[str, Any]:
        """Return a deterministic, auditable coach explanation payload."""
        plan = self.get_daily_coach_plan(user_id)
        user = self.db.query(models.EnhancedUser).filter(
            (models.EnhancedUser.clerk_user_id == user_id) | (models.EnhancedUser.id == user_id)
        ).first()
        if not user:
            raise ValueError("User not found")

        profile = self.db.query(models.UserProfile).filter(
            models.UserProfile.user_id == str(user.id)
        ).first()
        daily_progress = self.db.query(models.DailyProgress).filter(
            models.DailyProgress.user_id == user.id
        ).order_by(models.DailyProgress.date.desc()).first()

        workout = plan.get("workout_recommendation", {})
        meal = plan.get("meal_recommendation", {})
        next_action = plan.get("next_action", {})

        calories_remaining = 0.0
        protein_remaining = 0.0
        workout_status = "not_started"
        sets_completed = 0
        sets_planned = 0
        if daily_progress:
            calories_remaining = float(getattr(daily_progress, "calories_remaining", 0) or 0)
            protein_remaining = float(getattr(daily_progress, "protein_remaining", 0) or 0)
            workout_status = getattr(daily_progress, "workout_status", "not_started") or "not_started"
            sets_completed = int(getattr(daily_progress, "sets_completed", 0) or 0)
            sets_planned = int(getattr(daily_progress, "sets_planned", 0) or 0)

        risk_factors: List[str] = []
        if "recovery_low" in plan.get("constraints_applied", []):
            risk_factors.append("Recovery score is low")
        if "protein_deficit" in plan.get("constraints_applied", []):
            risk_factors.append("Protein intake is behind target")
        if "cycle_" in " ".join(plan.get("constraints_applied", [])):
            risk_factors.append("Cycle phase suggests training adjustment")
        if workout_status in {"in_progress", "done"}:
            risk_factors.append("Workout progress is already underway")

        if not risk_factors:
            risk_factors.append("Current data supports a steady training day")

        explanation_lines = []
        if workout.get("type") == "deload":
            explanation_lines.append("A lighter training block is recommended today.")
        elif workout.get("type") == "rest":
            explanation_lines.append("Recovery is the best use of today's energy.")
        else:
            explanation_lines.append("You can proceed with the planned session.")
        if calories_remaining > 0:
            explanation_lines.append(f"About {round(calories_remaining)} kcal remain for the day.")
        if protein_remaining > 0:
            explanation_lines.append(f"You still need roughly {round(protein_remaining)}g protein.")

        confidence = 92
        if workout.get("type") == "deload":
            confidence -= 4
        if "recovery_low" in plan.get("constraints_applied", []):
            confidence -= 8
        if "protein_deficit" in plan.get("constraints_applied", []):
            confidence -= 5
        if daily_progress is None:
            confidence -= 10
        confidence = max(55, min(98, confidence))

        if profile and getattr(profile, "femmecare_enabled", False):
            phase_note = "FemmeCare is enabled, so cycle-aware nudges are active."
        else:
            phase_note = "Standard mode is active."

        return {
            "recommendation": {
                "title": next_action.get("title", "Continue with today's plan"),
                "detail": next_action.get("detail") or workout.get("reasoning") or "Stay consistent.",
                "route": next_action.get("route", "/dashboard"),
                "priority": next_action.get("priority", "Medium"),
            },
            "confidence_score": confidence,
            "explanation": explanation_lines,
            "factors": risk_factors,
            "progress_snapshot": {
                "calories_remaining": calories_remaining,
                "protein_remaining": protein_remaining,
                "workout_status": workout_status,
                "sets_completed": sets_completed,
                "sets_planned": sets_planned,
            },
            "mode_note": phase_note,
            "coach_summary": plan.get("coach_summary"),
            "gender_mode": plan.get("gender_mode"),
            "workout_recommendation": workout,
            "meal_recommendation": meal,
            "next_action": next_action,
        }

    def get_coach_history(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Return a compact coach history timeline for the dashboard."""
        user = self.db.query(models.EnhancedUser).filter(
            (models.EnhancedUser.clerk_user_id == user_id) | (models.EnhancedUser.id == user_id)
        ).first()
        if not user:
            raise ValueError("User not found")

        safe_days = max(3, min(14, int(days or 7)))
        start_date = datetime.utcnow().date() - timedelta(days=safe_days - 1)

        progress_rows = (
            self.db.query(models.DailyProgress)
            .filter(models.DailyProgress.user_id == user.id)
            .order_by(models.DailyProgress.date.desc())
            .limit(safe_days)
            .all()
        )
        feedback_rows = (
            self.db.query(models.CoachFeedback)
            .filter(models.CoachFeedback.user_id == str(user.id))
            .order_by(models.CoachFeedback.created_at.desc())
            .limit(50)
            .all()
        )

        feedback_by_date: Dict[str, List[models.CoachFeedback]] = {}
        for feedback in feedback_rows:
            key = feedback.created_at.date().isoformat()
            feedback_by_date.setdefault(key, []).append(feedback)

        entries: List[Dict[str, Any]] = []
        for row in progress_rows:
            day = row.date.date()
            if day < start_date:
                continue
            progress_pct = 0
            if row.sets_planned:
                progress_pct = int(round((row.sets_completed / max(row.sets_planned, 1)) * 100))

            feedback_for_day = feedback_by_date.get(day.isoformat(), [])
            liked = sum(1 for item in feedback_for_day if int(item.rating or 0) >= 4)
            disliked = sum(1 for item in feedback_for_day if int(item.rating or 0) <= 2)
            dominant_feedback = "balanced"
            if liked > disliked and liked > 0:
                dominant_feedback = "positive"
            elif disliked > liked and disliked > 0:
                dominant_feedback = "needs_adjustment"

            workout_state = row.workout_status or "not_started"
            if workout_state == "done":
                title = "Workout completed"
                detail = f"{row.sets_completed}/{row.sets_planned or 0} sets logged with steady execution."
            elif workout_state == "in_progress":
                title = "Workout in motion"
                detail = f"{row.sets_completed}/{row.sets_planned or 0} sets completed so far."
            elif workout_state == "skipped":
                title = "Workout skipped"
                detail = "The session was intentionally skipped so recovery could take priority."
            else:
                title = "Plan queued"
                detail = "Today’s session was prepared and waiting for action."

            if row.calories_remaining and row.calories_remaining < 0:
                nutrition_note = "You finished above the calorie target."
            elif row.calories_remaining and row.calories_remaining > 0:
                nutrition_note = f"{round(row.calories_remaining)} kcal still available."
            else:
                nutrition_note = "Nutrition stayed near target."

            entries.append({
                "date": day.isoformat(),
                "title": title,
                "detail": f"{detail} {nutrition_note}".strip(),
                "confidence": max(55, min(98, 88 + (5 if workout_state == 'done' else 0) - (4 if disliked else 0))),
                "workout_status": workout_state,
                "progress_percent": progress_pct,
                "sets_completed": int(row.sets_completed or 0),
                "sets_planned": int(row.sets_planned or 0),
                "calories_remaining": float(row.calories_remaining or 0),
                "protein_remaining": float(row.protein_remaining or 0),
                "feedback": dominant_feedback,
                "feedback_count": len(feedback_for_day),
            })

        if not entries:
            entries = [{
                "date": datetime.utcnow().date().isoformat(),
                "title": "No history yet",
                "detail": "Log a meal or workout to start building your coach timeline.",
                "confidence": 60,
                "workout_status": "not_started",
                "progress_percent": 0,
                "sets_completed": 0,
                "sets_planned": 0,
                "calories_remaining": 0,
                "protein_remaining": 0,
                "feedback": "balanced",
                "feedback_count": 0,
            }]

        week_completion = sum(1 for item in entries if item["workout_status"] == "done")
        trend_note = "Consistency is solid this week."
        if week_completion == 0:
            trend_note = "No completed sessions yet, so the coach is keeping the plan lighter."
        elif week_completion >= max(1, len(entries) // 2):
            trend_note = "Training consistency is trending upward."

        return {
            "period_days": safe_days,
            "trend_note": trend_note,
            "entries": entries[:safe_days],
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
