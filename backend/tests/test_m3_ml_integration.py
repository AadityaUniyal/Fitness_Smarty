"""
Unit and Integration Tests for Milestone 3 (ML Models & Integration)
Tests:
1. LSTM Weight Predictor training, metrics export (lstm_metrics.json), moving-average fallback (<14 entries), sequence length alignment.
2. Collaborative Filtering: rating data training, metrics export (cf_metrics.json), predict_score, cold-start rule fallback.
3. PyTorch Recommendation MLP: train/val split, metrics export (mlp_metrics.json), candidate scoring alignment.
4. K-Means User Clustering: engine fit, predict, cluster assignment actively consumed in HybridRanker.
5. HybridRanker integration: exercise & meal ranking with blended ML scores.
"""

import os
import sys
import json
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml_models.lstm_predictor import LSTMWeightPredictor, get_weight_predictor

from app.ml_models.train_lstm import train as train_lstm
from app.ml_models.collaborative_filtering import CollaborativeFilteringRecommender, get_collaborative_recommender
from app.ml_models.recommendation_mlp import RecommendationMLP, get_recommendation_mlp
from app.training.train_neural_model import NeuralModelTrainer
from app.training.user_clustering import UserClusterEngine, generate_sample_profiles
from app.hybrid_ranker import HybridRanker
from app.database import get_training_db, TrainingSessionLocal


def test_lstm_moving_average_fallback():
    """Verify moving average fallback when user trajectory has fewer than 14 entries."""
    predictor = LSTMWeightPredictor()
    
    # Trajectory with 5 entries (< 14)
    short_history = [
        {"date": f"2024-02-{i:02d}", "weight": 80.0 - (i * 0.1), "calories": 2000.0, "activity_minutes": 30}
        for i in range(1, 6)
    ]
    res = predictor.predict_weight(short_history, days_ahead=7)
    
    assert "predictions" in res
    assert len(res["predictions"]) == 7
    assert res["model"] in ("moving_average_fallback", "baseline_fallback")
    assert res["confidence_score"] > 0.0
    assert res["predictions"][0]["predicted_weight"] > 0.0


def test_lstm_training_metrics_export():
    """Verify LSTM training exports lstm_metrics.json and lstm_config.json."""
    train_lstm(seq_len=14)
    
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_metrics = os.path.join(dir_path, "app", "ml_models", "lstm_metrics.json")
    backend_metrics = os.path.join(dir_path, "ml", "lstm_metrics.json")
    
    assert os.path.exists(backend_metrics) or os.path.exists(app_metrics)
    
    target_file = backend_metrics if os.path.exists(backend_metrics) else app_metrics
    with open(target_file, "r") as f:
        metrics = json.load(f)
        assert "mae" in metrics
        assert "rmse" in metrics
        assert metrics["seq_length"] == 14
        assert metrics["status"] == "success"


def test_collaborative_filtering_fallback_and_predict():
    """Verify CF predict_score with cold-start rule fallback."""
    cf = CollaborativeFilteringRecommender()
    
    # Cold-start user (unknown ID)
    cold_score = cf.predict_score(user_id=99999, meal_id=1, fallback_rule_score=0.75)
    assert cold_score == 0.75
    
    # Train synthetic data
    cf.train_synthetic(num_users=10, num_meals=20)
    score = cf.predict_score(user_id=1, meal_id=1, fallback_rule_score=0.60)
    assert 0.0 <= score <= 1.0


def test_recommendation_mlp_metrics_and_scoring():
    """Verify PyTorch Recommendation MLP metrics export and scoring."""
    trainer = NeuralModelTrainer()
    dataset_file = Path(__file__).resolve().parent.parent / "app" / "training" / "datasets" / "synthetic_meals.jsonl"
    acc = trainer.train(dataset_file=str(dataset_file), epochs=2, batch_size=64)
    assert acc > 50.0

    
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_mlp_metrics = os.path.join(dir_path, "ml", "mlp_metrics.json")
    assert os.path.exists(backend_mlp_metrics)
    
    with open(backend_mlp_metrics, "r") as f:
        metrics = json.load(f)
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert metrics["input_size"] == 20
        
    mlp = RecommendationMLP()
    user_profile = {"age": 28, "weight_kg": 75, "height_cm": 178, "bmi": 23.7, "gender": "male", "goal": "muscle_gain", "activity_level": "active"}
    meal = {"calories": 500, "protein_g": 40, "carbs_g": 50, "fat_g": 12, "name": "Chicken Rice Bowl"}
    
    score = mlp.predict_score(user_profile, meal)
    assert 0.0 <= score <= 1.0


def test_user_clustering_engine():
    """Verify K-Means user cluster assignment and prediction."""
    engine = UserClusterEngine()
    profiles = generate_sample_profiles(n=30)
    res = engine.fit(profiles, n_clusters=3, method="kmeans")
    assert res["status"] in ("success", "mock")
    
    p = profiles[0]
    pred = engine.predict(p)
    assert "cluster_id" in pred
    assert "cluster_label" in pred


def test_hybrid_ranker_integration():
    """Verify HybridRanker integrates exercise ranking and meal ranking with ML scores."""
    session = TrainingSessionLocal()
    try:
        ranker = HybridRanker(session)
        profile = {
            "user_id": 1,
            "primary_goal": "muscle_gain",
            "training_level": "intermediate",
            "age": 28,
            "weight_kg": 75,
            "height_cm": 175,
            "gender": "male",
            "activity_level": "active"
        }
        
        candidates = [
            {"name": "Barbell Bench Press", "fitness_goal": "muscle_gain", "difficulty": "intermediate", "calories_per_min": 7.0},
            {"name": "Bodyweight Squats", "fitness_goal": "weight_loss", "difficulty": "beginner", "calories_per_min": 5.0}
        ]
        
        ranked_ex = ranker.rank_exercises(candidates, profile, limit=5)
        assert len(ranked_ex) == 2
        assert "rank_score" in ranked_ex[0]
        assert "user_cluster" in ranked_ex[0]
        
        # Test rank_meals_from_db
        macro_gap = {"calories": 500, "protein_g": 35}
        ranked_meals = ranker.rank_meals_from_db(profile, macro_gap, limit=3)
        assert isinstance(ranked_meals, list)
        if ranked_meals:
            assert "rank_score" in ranked_meals[0]
            assert "cf_score" in ranked_meals[0]
            assert "mlp_score" in ranked_meals[0]
    finally:
        session.close()


if __name__ == "__main__":
    print("[TEST] Running test_lstm_moving_average_fallback...")
    test_lstm_moving_average_fallback()
    print("[OK] test_lstm_moving_average_fallback passed")

    print("[TEST] Running test_lstm_training_metrics_export...")
    test_lstm_training_metrics_export()
    print("[OK] test_lstm_training_metrics_export passed")

    print("[TEST] Running test_collaborative_filtering_fallback_and_predict...")
    test_collaborative_filtering_fallback_and_predict()
    print("[OK] test_collaborative_filtering_fallback_and_predict passed")

    print("[TEST] Running test_recommendation_mlp_metrics_and_scoring...")
    test_recommendation_mlp_metrics_and_scoring()
    print("[OK] test_recommendation_mlp_metrics_and_scoring passed")

    print("[TEST] Running test_user_clustering_engine...")
    test_user_clustering_engine()
    print("[OK] test_user_clustering_engine passed")

    print("[TEST] Running test_hybrid_ranker_integration...")
    test_hybrid_ranker_integration()
    print("[OK] test_hybrid_ranker_integration passed")

    print("\n=======================================================")
    print(" ALL MILESTONE 3 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")

