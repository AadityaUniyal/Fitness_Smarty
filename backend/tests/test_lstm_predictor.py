import pytest
pytest.importorskip("numpy")
pytest.importorskip("torch")
import os
import json
from app.ml_models.train_lstm import train, generate_synthetic_user_data, create_sequences
from app.ml_models.lstm_predictor import LSTMWeightPredictor


def test_synthetic_data_generation():
    data = generate_synthetic_user_data(num_users=3, days=35)
    assert len(data) == 3
    assert len(data[0]) == 35
    assert "weight" in data[0][0]
    assert "calories" in data[0][0]


def test_train_pipeline():
    # Make sure we can execute train pipeline
    train()
    
    dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weights_path = os.path.join(dir_path, "app", "ml_models", "lstm_weights.pth")
    config_path = os.path.join(dir_path, "app", "ml_models", "lstm_config.json")
    
    assert os.path.exists(weights_path)
    assert os.path.exists(config_path)
    
    with open(config_path, "r") as f:
        config = json.load(f)
        assert "mae" in config
        assert config["mae"] > 0


def test_lstm_predictor_inference():
    predictor = LSTMWeightPredictor()
    # If trained models exist, it runs in PyTorch mode (mock_mode=False)
    
    history = [
        {"date": f"2024-02-{i:02d}", "weight": 80.0 - (i * 0.05), "calories": 1900.0, "activity_minutes": 35}
        for i in range(1, 35)
    ]
    
    res = predictor.predict_weight(history, days_ahead=7)
    assert "predictions" in res
    assert len(res["predictions"]) == 7
    assert res["predictions"][0]["predicted_weight"] > 0.0
