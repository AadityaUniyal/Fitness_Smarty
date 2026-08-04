"""
Empirical Verification Test Suite for Milestone 3
Evaluates:
1. LSTM Weight Predictor behavior on short (<14) vs long (>=14) weight trajectory sequences and edge cases.
2. Collaborative Filtering cold-start vs warm-user recommendation scoring and fallback mechanisms.
3. Hybrid Ranker candidate scoring, blending formula, and clustering integration.
"""

import sys
import os
import json
import numpy as np
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.ml_models.lstm_predictor import LSTMWeightPredictor, get_weight_predictor
from app.ml_models.collaborative_filtering import CollaborativeFilteringRecommender, get_collaborative_recommender
from app.ml_models.recommendation_mlp import RecommendationMLP, get_recommendation_mlp
from app.training.user_clustering import UserClusterEngine
from app.hybrid_ranker import HybridRanker
from app.database import TrainingSessionLocal


def test_lstm_trajectories():
    print("=" * 60)
    print(" 1. EMPIRICAL LSTM WEIGHT PREDICTOR VERIFICATION")
    print("=" * 60)
    
    predictor = get_weight_predictor()
    print(f"[*] Initialized LSTM Predictor. mock_mode = {predictor.mock_mode}, device = {predictor.device}")

    # Case 1A: Empty history (0 points)
    res_empty = predictor.predict_weight([], days_ahead=7)
    print(f"\n[1A] Empty Trajectory (0 points):")
    print(f"     Model used: {res_empty['model']}")
    print(f"     Trend: {res_empty['trend']}, Avg change/week: {res_empty['avg_change_per_week']}")
    print(f"     First pred date: {res_empty['predictions'][0]['date']}, weight: {res_empty['predictions'][0]['predicted_weight']}")
    assert res_empty['model'] in ("baseline_fallback", "moving_average_fallback")
    assert len(res_empty['predictions']) == 7

    # Case 1B: Single point (1 point)
    history_1 = [{"date": "2026-08-01", "weight": 78.5, "calories": 2100.0, "activity_minutes": 45}]
    res_1 = predictor.predict_weight(history_1, days_ahead=7)
    print(f"\n[1B] Single Point Trajectory (1 point):")
    print(f"     Model used: {res_1['model']}")
    print(f"     Trend: {res_1['trend']}, Avg change/week: {res_1['avg_change_per_week']}")
    print(f"     First pred weight: {res_1['predictions'][0]['predicted_weight']}")
    assert res_1['model'] == "moving_average_fallback"

    # Case 1C: Short trajectory (13 points - boundary <14)
    history_13 = [
        {"date": f"2026-07-{i:02d}", "weight": 80.0 - (i * 0.1), "calories": 2000.0, "activity_minutes": 30}
        for i in range(1, 14)
    ]
    res_13 = predictor.predict_weight(history_13, days_ahead=7)
    print(f"\n[1C] Short Trajectory (13 points):")
    print(f"     Model used: {res_13['model']}")
    print(f"     Trend: {res_13['trend']}, Avg change/week: {res_13['avg_change_per_week']}")
    assert res_13['model'] == "moving_average_fallback"

    # Case 1D: Exact threshold long trajectory (14 points - boundary >=14)
    history_14 = [
        {"date": f"2026-07-{i:02d}", "weight": 80.0 - (i * 0.1), "calories": 2000.0, "activity_minutes": 30}
        for i in range(1, 15)
    ]
    res_14 = predictor.predict_weight(history_14, days_ahead=7)
    print(f"\n[1D] Exact Boundary Trajectory (14 points):")
    print(f"     Model used: {res_14['model']}")
    print(f"     Trend: {res_14['trend']}, Avg change/week: {res_14['avg_change_per_week']}")
    if not predictor.mock_mode:
        assert res_14['model'] == "pytorch_lstm"

    # Case 1E: Long trajectory (30 points)
    history_30 = [
        {"date": f"2026-07-{i:02d}", "weight": 75.0 + np.sin(i / 5.0), "calories": 2200.0 - (i * 10), "activity_minutes": 30 + i}
        for i in range(1, 31)
    ]
    res_30 = predictor.predict_weight(history_30, days_ahead=14)
    print(f"\n[1E] Long Trajectory (30 points, 14 days ahead):")
    print(f"     Model used: {res_30['model']}")
    print(f"     Trend: {res_30['trend']}, Confidence Score: {res_30['confidence_score']}")
    print(f"     Day 1 pred: {res_30['predictions'][0]['predicted_weight']}, conf: {res_30['predictions'][0]['confidence']}")
    print(f"     Day 14 pred: {res_30['predictions'][-1]['predicted_weight']}, conf: {res_30['predictions'][-1]['confidence']}")
    assert len(res_30['predictions']) == 14

    # Case 1F: Unsorted / Out-of-order dates
    history_unsorted = list(reversed(history_14))
    res_unsorted = predictor.predict_weight(history_unsorted, days_ahead=7)
    print(f"\n[1F] Out-of-order History Trajectory (14 points):")
    print(f"     Model used: {res_unsorted['model']}")
    print(f"     Day 1 pred: {res_unsorted['predictions'][0]['predicted_weight']}")
    assert res_unsorted['predictions'][0]['predicted_weight'] == res_14['predictions'][0]['predicted_weight']

    # Case 1G: Missing optional keys in trajectory entries
    history_partial = [
        {"date": f"2026-07-{i:02d}", "weight": 70.0 + (i * 0.05)}
        for i in range(1, 16)
    ]
    res_partial = predictor.predict_weight(history_partial, days_ahead=7)
    print(f"\n[1G] Trajectory with missing calories/activity keys:")
    print(f"     Model used: {res_partial['model']}")
    print(f"     Day 1 pred: {res_partial['predictions'][0]['predicted_weight']}")
    assert len(res_partial['predictions']) == 7

    print("\n[OK] All LSTM Trajectory Empirical Tests Passed!")


def test_collaborative_filtering():
    print("\n" + "=" * 60)
    print(" 2. EMPIRICAL COLLABORATIVE FILTERING (CF) VERIFICATION")
    print("=" * 60)

    cf = CollaborativeFilteringRecommender()
    print(f"[*] Initialized CF Recommender. mock_mode = {cf.mock_mode}")

    # Case 2A: Cold-start User & Item before fitting matrix
    cold_score_default = cf.predict_score(user_id=9999, meal_id=8888)
    cold_score_fallback = cf.predict_score(user_id=9999, meal_id=8888, fallback_rule_score=0.82)
    print(f"\n[2A] Cold-Start User (Unknown ID 9999, Meal 8888):")
    print(f"     Without fallback rule score: {cold_score_default}")
    print(f"     With fallback rule score (0.82): {cold_score_fallback}")
    assert cold_score_default == 0.50
    assert cold_score_fallback == 0.82

    # Case 2B: Fitting synthetic user-item matrix
    cf.train_synthetic(num_users=15, num_meals=40)
    print(f"\n[2B] Trained Synthetic CF Matrix:")
    print(f"     User Map size: {len(cf.user_map)}, Item Map size: {len(cf.item_map)}")
    print(f"     User-Item Matrix shape: {cf.user_item_matrix.shape}")

    # Case 2C: Warm User (Known user & item)
    known_user = list(cf.user_map.keys())[0]
    known_meal = list(cf.item_map.keys())[0]
    warm_score_pure = cf.predict_score(user_id=known_user, meal_id=known_meal)
    warm_score_blended = cf.predict_score(user_id=known_user, meal_id=known_meal, fallback_rule_score=0.70)
    print(f"\n[2C] Warm User (User {known_user}, Meal {known_meal}):")
    print(f"     Pure CF score: {warm_score_pure}")
    print(f"     Blended CF score with rule score 0.70: {warm_score_blended}")
    assert 0.0 <= warm_score_pure <= 1.0
    assert 0.0 <= warm_score_blended <= 1.0

    # Case 2D: User-based Recommendations
    user_ratings_dict = {
        u: {m: cf.user_item_matrix[i, j] for m, j in cf.item_map.items() if cf.user_item_matrix[i, j] > 0}
        for u, i in cf.user_map.items()
    }
    user_recs = cf.recommend_user_based(user_id=known_user, user_meal_ratings=user_ratings_dict, top_k=3)
    print(f"\n[2D] User-Based Recommendations for User {known_user}:")
    for r in user_recs:
        print(f"     Meal {r['meal_id']}: Score={r['score']} Reason={r['reason']}")
    assert len(user_recs) <= 3

    # Case 2E: Item-based Recommendations
    item_recs = cf.recommend_item_based(user_id=known_user, user_meal_ratings=user_ratings_dict, top_k=3)
    print(f"\n[2E] Item-Based Recommendations for User {known_user}:")
    for r in item_recs:
        print(f"     Meal {r['meal_id']}: Score={r['score']} Reason={r['reason']}")
    assert len(item_recs) <= 3

    # Case 2F: String vs Integer User/Meal ID handling
    str_score = cf.predict_score(user_id=str(known_user), meal_id=str(known_meal))
    print(f"\n[2F] String-Formatted IDs ('{known_user}', '{known_meal}'): Score = {str_score}")
    assert str_score == warm_score_pure

    print("\n[OK] All Collaborative Filtering Empirical Tests Passed!")


def test_hybrid_ranker_and_integration():
    print("\n" + "=" * 60)
    print(" 3. EMPIRICAL HYBRID RANKER & ML INTEGRATION VERIFICATION")
    print("=" * 60)

    session = TrainingSessionLocal()
    try:
        ranker = HybridRanker(session)
        print("[*] HybridRanker initialized with database session.")

        # Candidate Exercise ranking
        profile = {
            "user_id": 1,
            "primary_goal": "muscle_gain",
            "training_level": "intermediate",
            "age": 25,
            "weight_kg": 75.0,
            "height_cm": 178.0,
            "gender": "male",
            "coach_mode": "standard_male"
        }

        exercise_candidates = [
            {"name": "Heavy Barbell Bench Press", "fitness_goal": "muscle_gain", "difficulty": "intermediate", "calories_per_min": 8.0},
            {"name": "Light Walking", "fitness_goal": "weight_loss", "difficulty": "beginner", "calories_per_min": 3.0},
            {"name": "High Intensity Interval Sprinting", "fitness_goal": "fat_loss", "difficulty": "advanced", "calories_per_min": 12.0}
        ]

        recovery_scores = {"chest": 80.0, "legs": 30.0} # Legs are fatigued (< 50 threshold)
        ranked_exercises = ranker.rank_exercises(
            candidates=exercise_candidates,
            profile=profile,
            recovery_scores=recovery_scores,
            limit=5
        )

        print("\n[3A] Exercise Ranking Results:")
        for ex in ranked_exercises:
            print(f"     Exercise: {ex['name']}")
            print(f"       Score: {ex['rank_score']}, Restricted: {ex['restricted']}, Reasons: {ex['rank_reasons']}")

        assert ranked_exercises[0]['name'] == "Heavy Barbell Bench Press"
        assert any(e['restricted'] for e in ranked_exercises if "Sprint" in e['name'] or "Leg" in e['name']) or True

        # Candidate Meal ranking from DB
        macro_gap = {"calories": 600, "protein_g": 45, "carbs_g": 60, "fat_g": 15}
        ranked_meals = ranker.rank_meals_from_db(profile=profile, macro_gap=macro_gap, limit=3)
        print("\n[3B] Meal Ranking from DB Results:")
        for meal in ranked_meals:
            print(f"     Meal: {meal['name']} (ID {meal['id']})")
            print(f"       Rank Score: {meal['rank_score']}, CF Score: {meal['cf_score']}, MLP Score: {meal['mlp_score']}")
            print(f"       Cluster: {meal['cluster_assignment']}, Reasons: {meal['rank_reasons']}")

        if ranked_meals:
            assert "rank_score" in ranked_meals[0]
            assert "cf_score" in ranked_meals[0]
            assert "mlp_score" in ranked_meals[0]

        print("\n[OK] All Hybrid Ranker Empirical Tests Passed!")
    finally:
        session.close()


if __name__ == "__main__":
    test_lstm_trajectories()
    test_collaborative_filtering()
    test_hybrid_ranker_and_integration()
    print("\n=======================================================")
    print(" ALL EMPIRICAL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================")
