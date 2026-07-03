"""
ML Models Package

Contains all machine learning models for food detection, classification, and recommendations.
Modules are loaded lazily on first use to avoid slow startup.
"""

import importlib
import sys

_LAZY_MODULES = {
    'YOLOFoodDetector': 'yolo_food_detector',
    'RecipeBERT': 'recipe_bert',
    'CLIPSearch': 'clip_search',
    'ResNetFoodClassifier': 'resnet_classifier',
    'MaskRCNNPortionEstimator': 'portion_estimator',
    'LSTMWeightPredictor': 'lstm_predictor',
    'ProphetTrendAnalyzer': 'prophet_analyzer',
    'CollaborativeFilteringRecommender': 'collaborative_filtering',
    'ContentBasedRecommender': 'content_based',
    'DQNMealSequencer': 'reinforcement_learning',
    'QLearningHabitFormer': 'reinforcement_learning',
    'SHAPExplainer': 'shap_explainer',
    'MobileModelExporter': 'mobile_export',
}

_LAZY_FUNCTIONS = {
    'get_yolo_detector': 'yolo_food_detector',
    'get_recipe_bert': 'recipe_bert',
    'get_clip_search': 'clip_search',
    'get_resnet_classifier': 'resnet_classifier',
    'get_portion_estimator': 'portion_estimator',
    'get_weight_predictor': 'lstm_predictor',
    'get_trend_analyzer': 'prophet_analyzer',
    'get_collaborative_recommender': 'collaborative_filtering',
    'get_content_recommender': 'content_based',
    'get_dqn_sequencer': 'reinforcement_learning',
    'get_habit_former': 'reinforcement_learning',
    'get_shap_explainer': 'shap_explainer',
    'get_mobile_exporter': 'mobile_export',
}

class _LazyLoader:
    def __init__(self, original_module):
        self._loaded = {}
        self._original = original_module

    def __getattr__(self, name):
        if name in _LAZY_MODULES:
            module_name = _LAZY_MODULES[name]
            if module_name not in self._loaded:
                self._loaded[module_name] = importlib.import_module(f'.{module_name}', __package__)
            return getattr(self._loaded[module_name], name)
        if name in _LAZY_FUNCTIONS:
            module_name = _LAZY_FUNCTIONS[name]
            if module_name not in self._loaded:
                self._loaded[module_name] = importlib.import_module(f'.{module_name}', __package__)
            return getattr(self._loaded[module_name], name)
        try:
            return getattr(self._original, name)
        except AttributeError:
            raise AttributeError(f"Module 'ml_models' has no attribute '{name}'")

# Replace the module in sys.modules with our lazy loader proxying the original module
original_module = sys.modules[__name__]
sys.modules[__name__] = _LazyLoader(original_module)

