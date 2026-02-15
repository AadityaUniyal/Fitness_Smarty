"""
LSTM Weight Predictor

Time-series forecasting for weight prediction using LSTM neural networks
"""

import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not available")


class LSTMWeightPredictor:
    """
    LSTM-based weight prediction model
    
    Predicts future weight based on historical data (weight, calories, activity)
    """
    
    def __init__(self, input_size: int = 3, hidden_size: int = 64, num_layers: int = 2):
        """
        Initialize LSTM predictor
        
        Args:
            input_size: Number of features (weight, calories, activity)
            hidden_size: LSTM hidden dimension
            num_layers: Number of LSTM layers
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.mock_mode = False
        
        if TORCH_AVAILABLE:
            try:
                self.model = LSTMModel(input_size, hidden_size, num_layers).to(self.device)
                self.model.eval()
                print(f"✓ LSTM weight predictor initialized on {self.device}")
            except Exception as e:
                print(f"⚠️  Could not initialize LSTM: {e}")
                self.mock_mode = True
        else:
            print("⚠️  PyTorch not installed. Using mock mode.")
            self.mock_mode = True
    
    def predict_weight(
        self,
        historical_data: List[Dict[str, float]],
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Predict future weight
        
        Args:
            historical_data: List of {date, weight, calories, activity_minutes}
            days_ahead: Number of days to forecast
            
        Returns:
            {
                'predictions': [
                    {'date': '2024-02-20', 'predicted_weight': 75.2, 'confidence': 0.85}
                ],
                'trend': 'decreasing',
                'avg_change_per_week': -0.5,
                'model': 'lstm'
            }
        """
        if self.mock_mode or len(historical_data) < 7:
            return self._mock_predict(historical_data, days_ahead)
        
        try:
            # Prepare data
            sequence = self._prepare_sequence(historical_data)
            
            # Run prediction
            with torch.no_grad():
                predictions = []
                current_seq = sequence[-30:]  # Last 30 days
                
                for day in range(days_ahead):
                    # Predict next day
                    input_tensor = torch.FloatTensor(current_seq).unsqueeze(0).to(self.device)
                    pred = self.model(input_tensor)
                    predicted_weight = float(pred[0, 0])
                    
                    # Add to predictions
                    pred_date = datetime.now() + timedelta(days=day+1)
                    predictions.append({
                        'date': pred_date.strftime('%Y-%m-%d'),
                        'predicted_weight': round(predicted_weight, 1),
                        'confidence': self._calculate_confidence(day)
                    })
                    
                    # Update sequence for next prediction
                    # Assume constant calories/activity (user can override)
                    avg_calories = np.mean([d['calories'] for d in historical_data[-7:]])
                    avg_activity = np.mean([d['activity_minutes'] for d in historical_data[-7:]])
                    
                    new_point = [predicted_weight, avg_calories, avg_activity]
                    current_seq = np.vstack([current_seq[1:], new_point])
            
            # Calculate trend
            weights = [p['predicted_weight'] for p in predictions]
            trend = self._calculate_trend(weights)
            avg_change = (weights[-1] - weights[0]) / (days_ahead / 7)
            
            return {
                'predictions': predictions,
                'trend': trend,
                'avg_change_per_week': round(avg_change, 2),
                'model': 'lstm',
                'confidence_score': predictions[0]['confidence'] if predictions else 0.0
            }
            
        except Exception as e:
            print(f"Error in LSTM prediction: {e}")
            return self._mock_predict(historical_data, days_ahead)
    
    def _prepare_sequence(self, data: List[Dict]) -> np.ndarray:
        """Convert historical data to sequence"""
        sequence = []
        for entry in data:
            sequence.append([
                entry.get('weight', 75),
                entry.get('calories', 2000),
                entry.get('activity_minutes', 30)
            ])
        return np.array(sequence)
    
    def _calculate_confidence(self, day_offset: int) -> float:
        """Calculate prediction confidence (decreases with distance)"""
        return max(0.5, 0.9 - (day_offset * 0.05))
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Determine trend direction"""
        if len(values) < 2:
            return 'stable'
        
        start = np.mean(values[:3])
        end = np.mean(values[-3:])
        change = end - start
        
        if abs(change) < 0.2:
            return 'stable'
        elif change < 0:
            return 'decreasing'
        else:
            return 'increasing'
    
    def _mock_predict(self, historical_data: List[Dict], days_ahead: int) -> Dict[str, Any]:
        """Mock prediction for development"""
        if not historical_data:
            current_weight = 75.0
        else:
            current_weight = historical_data[-1].get('weight', 75.0)
        
        predictions = []
        # Mock: slight decrease over time
        for day in range(days_ahead):
            pred_date = datetime.now() + timedelta(days=day+1)
            pred_weight = current_weight - (day * 0.1)
            
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_weight': round(pred_weight, 1),
                'confidence': max(0.6, 0.85 - (day * 0.03))
            })
        
        return {
            'predictions': predictions,
            'trend': 'decreasing',
            'avg_change_per_week': -0.7,
            'model': 'mock',
            'confidence_score': 0.75
        }


class LSTMModel(nn.Module):
    """PyTorch LSTM model"""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)  # Predict single value (weight)
    
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Get last output
        out = self.fc(out[:, -1, :])
        return out


# Singleton instance
_lstm_instance: Optional[LSTMWeightPredictor] = None

def get_weight_predictor() -> LSTMWeightPredictor:
    """Get singleton LSTM instance"""
    global _lstm_instance
    if _lstm_instance is None:
        _lstm_instance = LSTMWeightPredictor()
    return _lstm_instance
