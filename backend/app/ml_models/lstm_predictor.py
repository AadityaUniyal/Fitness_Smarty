"""
LSTM Weight Predictor
Time-series forecasting for weight prediction using LSTM neural networks
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not available")


class LSTMModel(nn.Module):
    """PyTorch LSTM model"""
    
    def __init__(self, input_size: int = 3, hidden_size: int = 64, num_layers: int = 2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)  # Predict single value (weight)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


class LSTMWeightPredictor:
    """
    LSTM-based weight prediction model.
    Loads real trained weights and uses the network to compute forecast timelines.
    """
    
    def __init__(self, input_size: int = 3, hidden_size: int = 64, num_layers: int = 2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.means = [75.0, 2000.0, 30.0]
        self.stds = [10.0, 400.0, 15.0]
        self.mock_mode = True
        
        if TORCH_AVAILABLE:
            try:
                self.model = LSTMModel(input_size, hidden_size, num_layers).to(self.device)
                
                # Try loading saved model configuration
                dir_path = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(dir_path, "lstm_config.json")
                weights_path = os.path.join(dir_path, "lstm_weights.pth")
                
                if os.path.exists(config_path) and os.path.exists(weights_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        self.means = config.get("means", self.means)
                        self.stds = config.get("stds", self.stds)
                    
                    # Load weights
                    self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
                    self.mock_mode = False
                    print("[OK] Real LSTM Weights and Config loaded successfully.")
                else:
                    print("[!] No trained weights found. Running in baseline/mock mode.")
                self.model.eval()
            except Exception as e:
                print(f"[!] Error initializing LSTM: {e}")
                self.mock_mode = True
        else:
            self.mock_mode = True

    def _scale(self, val: float, idx: int) -> float:
        mean = self.means[idx]
        std = self.stds[idx]
        return (val - mean) / std if std > 0 else val

    def _unscale_weight(self, scaled_weight: float) -> float:
        return scaled_weight * self.stds[0] + self.means[0]

    def predict_weight(
        self,
        historical_data: List[Dict[str, float]],
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        if self.mock_mode or len(historical_data) < 7:
            return self._mock_predict(historical_data, days_ahead)
        
        try:
            # Prepare scaled history sequence
            # Sort by date chronologically
            sorted_history = sorted(historical_data, key=lambda x: x.get("date", ""))
            
            sequence = []
            for entry in sorted_history:
                sequence.append([
                    self._scale(entry.get("weight", 75.0), 0),
                    self._scale(entry.get("calories", 2000.0), 1),
                    self._scale(entry.get("activity_minutes", 30.0), 2)
                ])
            
            # Run prediction step-by-step
            predictions = []
            current_seq = np.array(sequence[-30:])  # Take last 30 days
            
            # Fallback if history is less than 30 days
            if len(current_seq) < 30:
                pad_width = 30 - len(current_seq)
                current_seq = np.pad(current_seq, ((pad_width, 0), (0, 0)), mode='edge')

            with torch.no_grad():
                for day in range(days_ahead):
                    input_tensor = torch.FloatTensor(current_seq).unsqueeze(0).to(self.device)
                    pred = self.model(input_tensor)
                    scaled_pred = float(pred[0, 0])
                    
                    predicted_weight = self._unscale_weight(scaled_pred)
                    
                    pred_date = datetime.now() + timedelta(days=day+1)
                    predictions.append({
                        'date': pred_date.strftime('%Y-%m-%d'),
                        'predicted_weight': round(predicted_weight, 2),
                        'confidence': round(self._calculate_confidence(day), 2)
                    })
                    
                    # Update sequence for next step
                    # Assume average calories/activity of last 7 days continues
                    avg_calories = np.mean([d.get('calories', 2000.0) for d in sorted_history[-7:]])
                    avg_activity = np.mean([d.get('activity_minutes', 30.0) for d in sorted_history[-7:]])
                    
                    new_point = [
                        scaled_pred,
                        self._scale(avg_calories, 1),
                        self._scale(avg_activity, 2)
                    ]
                    current_seq = np.vstack([current_seq[1:], new_point])

            weights = [p['predicted_weight'] for p in predictions]
            trend = self._calculate_trend(weights)
            avg_change = (weights[-1] - weights[0]) / (days_ahead / 7.0)
            
            return {
                'predictions': predictions,
                'trend': trend,
                'avg_change_per_week': round(avg_change, 2),
                'model': 'pytorch_lstm',
                'confidence_score': predictions[0]['confidence'] if predictions else 0.0
            }
            
        except Exception as e:
            print(f"[!] PyTorch LSTM prediction failure: {e}")
            return self._mock_predict(historical_data, days_ahead)

    def _calculate_confidence(self, day_offset: int) -> float:
        return max(0.5, 0.9 - (day_offset * 0.05))

    def _calculate_trend(self, values: List[float]) -> str:
        if len(values) < 2:
            return 'stable'
        change = values[-1] - values[0]
        if abs(change) < 0.2:
            return 'stable'
        return 'decreasing' if change < 0 else 'increasing'

    def _mock_predict(self, historical_data: List[Dict], days_ahead: int) -> Dict[str, Any]:
        current_weight = historical_data[-1].get('weight', 75.0) if historical_data else 75.0
        predictions = []
        for day in range(days_ahead):
            pred_date = datetime.now() + timedelta(days=day+1)
            pred_weight = current_weight - (day * 0.08)
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_weight': round(pred_weight, 2),
                'confidence': round(max(0.6, 0.85 - (day * 0.03)), 2)
            })
        return {
            'predictions': predictions,
            'trend': 'decreasing',
            'avg_change_per_week': -0.56,
            'model': 'baseline_fallback',
            'confidence_score': 0.75
        }


# Singleton instance
_lstm_instance: Optional[LSTMWeightPredictor] = None

def get_weight_predictor() -> LSTMWeightPredictor:
    global _lstm_instance
    if _lstm_instance is None:
        _lstm_instance = LSTMWeightPredictor()
    return _lstm_instance
