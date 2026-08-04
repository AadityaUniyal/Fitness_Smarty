"""
Train Neural Model Module (backend/ml/train_neural_model.py)
Re-exports NeuralModelTrainer from app.training.train_neural_model.
"""

from app.training.train_neural_model import (
    NeuralModelTrainer,
    MealDataset,
    MealRecommendationNN,
)

__all__ = ["NeuralModelTrainer", "MealDataset", "MealRecommendationNN"]
