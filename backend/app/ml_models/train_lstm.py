"""
Training pipeline for LSTM Weight Predictor.
Generates synthetic weight history and trains the PyTorch LSTM model.
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import random
import os
import json
from datetime import datetime, timedelta

# Import models
from lstm_predictor import LSTMModel, LSTMWeightPredictor

class SyntheticDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


def generate_synthetic_user_data(num_users=60, days=90) -> list:
    """
    Generates plausible daily logs for users: weight, calories consumed, activity minutes.
    """
    data = []
    for uid in range(num_users):
        # Baseline user features
        base_weight = random.uniform(60.0, 100.0)
        tdee = base_weight * 22.0 + 300.0 # BMR approx
        
        current_weight = base_weight
        start_date = datetime.now() - timedelta(days=days)
        
        user_logs = []
        for d in range(days):
            # 1. Calorie intake
            calories = max(1000.0, random.normalvariate(2000.0, 300.0))
            # 2. Activity
            activity = max(0, int(random.normalvariate(40.0, 15.0)))
            
            # Calorie burn adjustments
            activity_burn = activity * 6.0
            daily_tdee = tdee + activity_burn
            
            # Weight change thermodynamics: 7700 calories = 1kg
            deficit = calories - daily_tdee
            weight_change = deficit / 7700.0
            
            # Plausible water weight noise
            water_noise = random.normalvariate(0.0, 0.2)
            
            current_weight += weight_change
            displayed_weight = current_weight + water_noise
            
            log_date = start_date + timedelta(days=d)
            user_logs.append({
                "date": log_date.strftime("%Y-%m-%d"),
                "weight": round(displayed_weight, 2),
                "calories": round(calories, 1),
                "activity_minutes": activity
            })
        data.append(user_logs)
    return data


def create_sequences(user_data, seq_length=30):
    sequences = []
    targets = []
    
    # We will compute basic scaling params
    all_points = []
    for user_logs in user_data:
        for entry in user_logs:
            all_points.append([entry["weight"], entry["calories"], entry["activity_minutes"]])
            
    all_points = np.array(all_points)
    means = all_points.mean(axis=0)
    stds = all_points.std(axis=0)
    
    # Normalize helper
    def scale(val, mean, std):
        return (val - mean) / std if std > 0 else val
        
    for user_logs in user_data:
        for i in range(len(user_logs) - seq_length):
            seq = []
            for j in range(seq_length):
                entry = user_logs[i + j]
                seq.append([
                    scale(entry["weight"], means[0], stds[0]),
                    scale(entry["calories"], means[1], stds[1]),
                    scale(entry["activity_minutes"], means[2], stds[2])
                ])
            target = scale(user_logs[i + seq_length]["weight"], means[0], stds[0])
            sequences.append(seq)
            targets.append([target])
            
    return np.array(sequences), np.array(targets), means, stds


def train():
    print("[*] Generating synthetic training logs...")
    raw_data = generate_synthetic_user_data(num_users=60, days=90)
    
    seq_len = 30
    sequences, targets, means, stds = create_sequences(raw_data, seq_length=seq_len)
    
    # Split
    split_idx = int(len(sequences) * 0.8)
    train_seqs, test_seqs = sequences[:split_idx], sequences[split_idx:]
    train_targ, test_targ = targets[:split_idx], targets[split_idx:]
    
    train_dataset = SyntheticDataset(train_seqs, train_targ)
    test_dataset = SyntheticDataset(test_seqs, test_targ)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Init Model
    model = LSTMModel(input_size=3, hidden_size=64, num_layers=2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    print("[*] Training PyTorch LSTM weight predictor...")
    model.train()
    for epoch in range(10):
        total_loss = 0.0
        for x_batch, y_batch in train_loader:
            optimizer.zero_grad()
            pred = model(x_batch)
            loss = criterion(pred, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
    # Evaluation
    model.eval()
    test_mae = 0.0
    with torch.no_grad():
        for i in range(len(test_seqs)):
            x_val = torch.FloatTensor(test_seqs[i]).unsqueeze(0)
            pred = model(x_val)
            # Unscale prediction and target back to kg
            pred_kg = float(pred[0, 0]) * stds[0] + means[0]
            targ_kg = float(test_targ[i][0]) * stds[0] + means[0]
            test_mae += abs(pred_kg - targ_kg)
            
    mae = test_mae / len(test_seqs)
    print(f"[OK] Training complete. Held-out Split MAE: {mae:.4f} kg")
    
    # Save Model Weights and scaler configs
    dir_path = os.path.dirname(os.path.abspath(__file__))
    weights_path = os.path.join(dir_path, "lstm_weights.pth")
    config_path = os.path.join(dir_path, "lstm_config.json")
    
    torch.save(model.state_dict(), weights_path)
    
    config = {
        "means": list(means),
        "stds": list(stds),
        "seq_length": seq_len,
        "mae": round(mae, 4)
    }
    with open(config_path, "w") as f:
        json.dump(config, f)
        
    print(f"[OK] Saved model weights to: {weights_path}")
    print(f"[OK] Saved scaler config to: {config_path}")


if __name__ == "__main__":
    train()
