"""
Hybrid Ranker — local ML + rule-based scoring for exercise and meal candidates.

Gemini narrates; this module ranks candidates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ExerciseItem, FemaleExerciseItem, FoodItem


class HybridRanker:
    """Score and rank exercise and meal candidates for a user profile."""

    EXERCISE_WEIGHTS = {
        "goal_match": 3.0,
        "difficulty_match": 2.0,
        "recovery_clear": 2.5,
        "cycle_match": 2.0,
        "calorie_efficiency": 0.5,
    }

    def __init__(self, db: Session):
        self.db = db

    def rank_exercises(
        self,
        candidates: List[Dict[str, Any]],
        profile: Dict[str, Any],
        recovery_scores: Optional[Dict[str, float]] = None,
        cycle_phase: Optional[str] = None,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        from app.recovery_engine import is_exercise_gated

        recovery_scores = recovery_scores or {}
        goal = (profile.get("primary_goal") or profile.get("goal") or "maintenance").lower()
        difficulty = (profile.get("training_level") or "intermediate").lower()
        coach_mode = profile.get("coach_mode", "standard_male")
        use_female_pool = coach_mode in ("femmecare", "standard_female", "pregnancy", "menopause")

        # Actively consume K-Means user cluster assignment
        cluster_info = None
        try:
            from app.training.user_clustering import UserClusterEngine
            cluster_engine = UserClusterEngine()
            cluster_info = cluster_engine.predict(profile)
        except Exception:
            cluster_info = None

        scored: List[Dict[str, Any]] = []
        for ex in candidates:
            name = ex.get("name", "")
            ex_goal = (ex.get("fitness_goal") or ex.get("goal") or "maintenance").lower()
            ex_diff = (ex.get("difficulty") or "beginner").lower()

            score = 0.0
            reasons: List[str] = []

            if goal in ex_goal or ex_goal in goal or self._goal_compatible(goal, ex_goal):
                score += self.EXERCISE_WEIGHTS["goal_match"]
                reasons.append("goal_match")

            if difficulty in ex_diff or ex_diff in difficulty:
                score += self.EXERCISE_WEIGHTS["difficulty_match"]
                reasons.append("difficulty_match")

            gated, gate_reason = is_exercise_gated(name, recovery_scores, threshold=50.0)
            if not gated:
                score += self.EXERCISE_WEIGHTS["recovery_clear"]
                reasons.append("recovery_ok")
            else:
                score -= 1.5
                reasons.append(f"recovery_gated:{gate_reason}")

            if use_female_pool and cycle_phase and cycle_phase != "all":
                phase = ex.get("suitable_cycle_phase") or ex.get("cycle_phase") or "all"
                if phase == "all" or phase.lower() == cycle_phase.lower():
                    score += self.EXERCISE_WEIGHTS["cycle_match"]
                    reasons.append("cycle_match")

            cal = float(ex.get("calories_per_min") or ex.get("cal_per_rep") or 5.0)
            score += min(cal / 10.0, 1.0) * self.EXERCISE_WEIGHTS["calorie_efficiency"]

            # Apply cluster preference boost if cluster info present
            if cluster_info and "cluster_label" in cluster_info:
                c_label = str(cluster_info["cluster_label"]).lower()
                if ("muscle" in c_label or "athletic" in c_label) and any(k in ex_goal or k in name.lower() for k in ("strength", "hypertrophy", "barbell", "dumbbell")):
                    score += 0.5
                    reasons.append("cluster_strength_boost")
                elif "weight loss" in c_label and any(k in ex_goal or k in name.lower() for k in ("cardio", "hiit", "jump", "run")):
                    score += 0.5
                    reasons.append("cluster_cardio_boost")

            scored.append({
                **ex,
                "rank_score": round(score, 2),
                "rank_reasons": reasons,
                "user_cluster": cluster_info.get("cluster_label", "") if cluster_info else "",
                "restricted": gated,
                "restriction_reason": gate_reason if gated else "",
            })

        scored.sort(key=lambda x: x["rank_score"], reverse=True)
        return scored[:limit]

    def rank_meals_from_db(
        self,
        profile: Dict[str, Any],
        macro_gap: Dict[str, float],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Rank food items from DB against remaining macro budget blending CF, MLP & K-Means cluster scores."""
        restrictions = {r.lower() for r in (profile.get("dietary_restrictions") or [])}
        allergies = {a.lower() for a in (profile.get("allergies") or [])}
        goal = (profile.get("primary_goal") or profile.get("goal") or "maintenance").lower()
        user_id = profile.get("user_id", 1)

        # Load ML components dynamically
        try:
            from app.ml_models.collaborative_filtering import get_collaborative_recommender
            cf_recommender = get_collaborative_recommender()
        except Exception:
            cf_recommender = None

        try:
            from app.ml_models.recommendation_mlp import get_recommendation_mlp
            mlp_recommender = get_recommendation_mlp()
        except Exception:
            mlp_recommender = None

        try:
            from app.training.user_clustering import UserClusterEngine
            cluster_engine = UserClusterEngine()
            cluster_info = cluster_engine.predict(profile)
        except Exception:
            cluster_info = None

        foods = self.db.query(FoodItem).limit(200).all()
        scored: List[Dict[str, Any]] = []

        for food in foods:
            name_lower = food.name.lower()
            if any(r in name_lower for r in allergies):
                continue
            if "vegan" in restrictions and any(x in name_lower for x in ("chicken", "beef", "egg", "fish", "salmon", "yogurt")):
                continue
            if "vegetarian" in restrictions and any(x in name_lower for x in ("chicken", "beef", "fish", "salmon")):
                continue

            # 1. Rule-based macro fit score
            protein_fit = 1.0 - min(abs((food.protein or 0) - macro_gap.get("protein_g", 30)) / 40.0, 1.0)
            cal_fit = 1.0 - min(abs((food.calories or 0) - macro_gap.get("calories", 400)) / 500.0, 1.0)
            goal_boost = 0.2 if food.recommended_for_goal and goal in (food.recommended_for_goal or "").lower() else 0.0
            rule_score = protein_fit * 2.0 + cal_fit * 1.5 + goal_boost + (0.3 if food.is_elite else 0.0)

            # Normalized rule score (range 0..1)
            norm_rule_score = min(1.0, max(0.0, rule_score / 4.0))

            # 2. Collaborative Filtering score with rule fallback
            cf_score = cf_recommender.predict_score(user_id, food.id, fallback_rule_score=norm_rule_score) if cf_recommender else norm_rule_score

            # 3. PyTorch Recommendation MLP score
            food_dict = {
                "id": food.id,
                "name": food.name,
                "calories": food.calories,
                "protein": food.protein,
                "carbs": food.carbs,
                "fats": food.fats
            }
            mlp_score = mlp_recommender.predict_score(profile, food_dict) if mlp_recommender else norm_rule_score

            # 4. K-Means User Cluster Archetype preference boost
            cluster_boost = 0.0
            if cluster_info and "cluster_label" in cluster_info:
                label = str(cluster_info["cluster_label"]).lower()
                if "muscle" in label and (food.protein or 0) >= 25:
                    cluster_boost += 0.3
                elif "weight loss" in label and (food.calories or 0) <= 450:
                    cluster_boost += 0.3
                elif "athletic" in label and (food.protein or 0) >= 20 and (food.calories or 0) >= 350:
                    cluster_boost += 0.3

            # Final blended rank score
            final_score = rule_score * 0.50 + cf_score * 1.2 + mlp_score * 1.0 + cluster_boost * 0.5

            reasons = ["macro_fit"]
            if cf_score > 0.55:
                reasons.append("cf_personalized")
            if mlp_score > 0.55:
                reasons.append("neural_mlp_fit")
            if cluster_boost > 0:
                reasons.append("cluster_archetype_boost")

            scored.append({
                "id": food.id,
                "name": food.name,
                "calories": food.calories,
                "protein": food.protein,
                "carbs": food.carbs,
                "fats": food.fats,
                "rank_score": round(final_score, 2),
                "cf_score": round(cf_score, 2),
                "mlp_score": round(mlp_score, 2),
                "cluster_assignment": cluster_info.get("cluster_label", "") if cluster_info else "",
                "rank_reasons": reasons
            })

        scored.sort(key=lambda x: x["rank_score"], reverse=True)
        return scored[:limit]

    def score_meal_template(
        self,
        meal_data: Dict[str, Any],
        macro_gap: Dict[str, float],
    ) -> float:
        """Score a meal template against remaining macros."""
        macros = meal_data.get("macros") or meal_data
        protein_diff = abs(float(macros.get("protein_g", 0)) - macro_gap.get("protein_g", 0))
        cal_diff = abs(float(macros.get("calories", 0)) - macro_gap.get("calories", 0))
        return -(protein_diff * 2 + cal_diff * 0.5)

    @staticmethod
    def _goal_compatible(user_goal: str, ex_goal: str) -> bool:
        pairs = {
            "muscle_gain": {"muscle_gain", "athletic", "maintenance"},
            "weight_loss": {"fat_loss", "weight_loss", "athletic", "maintenance"},
            "athletic": {"athletic", "maintenance", "muscle_gain"},
            "maintenance": {"maintenance", "athletic"},
        }
        return ex_goal in pairs.get(user_goal, {user_goal})

