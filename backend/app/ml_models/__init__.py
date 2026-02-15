"""
ML Models Package

Contains all machine learning models for food detection, classification, and recommendations.
"""

from .yolo_food_detector import YOLOFoodDetector, get_yolo_detector
from .recipe_bert import RecipeBERT, get_recipe_bert
from .clip_search import CLIPSearch, get_clip_search
from .resnet_classifier import ResNet50Classifier, get_resnet_classifier
from .portion_estimator import MaskRCNNPortionEstimator, get_portion_estimator
from .lstm_predictor import LSTMWeightPredictor, get_weight_predictor
from .prophet_analyzer import ProphetTrendAnalyzer, get_trend_analyzer
from .collaborative_filtering import CollaborativeFilteringRecommender, get_collaborative_recommender
from .content_based import ContentBasedRecommender, get_content_recommender
from .reinforcement_learning import DQNMealSequencer, QLearningHabitFormer, get_dqn_sequencer, get_habit_former
from .shap_explainer import SHAPExplainer, get_shap_explainer
from .mobile_export import MobileModelExporter, get_mobile_exporter

__all__ = [
    'YOLOFoodDetector',
    'get_yolo_detector',
    'RecipeBERT',
    'get_recipe_bert',
    'CLIPSearch',
    'get_clip_search',
    'ResNet50Classifier',
    'get_resnet_classifier',
    'MaskRCNNPortionEstimator',
    'get_portion_estimator',
    'LSTMWeightPredictor',
    'get_weight_predictor',
    'ProphetTrendAnalyzer',
    'get_trend_analyzer',
    'CollaborativeFilteringRecommender',
    'get_collaborative_recommender',
    'ContentBasedRecommender',
    'get_content_recommender',
    'DQNMealSequencer',
    'QLearningHabitFormer',
    'get_dqn_sequencer',
    'get_habit_former',
    'SHAPExplainer',
    'get_shap_explainer',
    'MobileModelExporter',
    'get_mobile_exporter'
]
