"""
Neural Network Model Trainer

Trains a deep learning model on the synthetic meal dataset
Uses PyTorch for production-grade neural network training
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib


class MealDataset(Dataset):
    """PyTorch Dataset for meal data"""
    
    def __init__(self, features, labels):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class MealRecommendationNN(nn.Module):
    """
    Neural Network for Meal Recommendation
    
    Architecture:
    - Input: 20 features (user + meal data)
    - Hidden layers with dropout for regularization
    - Output: Binary classification (good/bad)
    """
    
    def __init__(self, input_size=20):
        super(MealRecommendationNN, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.network(x)


class NeuralModelTrainer:
    """Trains the neural network model"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.output_dir = Path("app/training/models/neural_model")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_features(self, record: dict) -> np.ndarray:
        """Extract numerical features from a record"""
        profile = record['user_profile']
        meal = record['meal']
        nutrition = meal['nutrition']
        
        # Encode goal
        goal_encoding = {
            'weight_loss': 0,
            'muscle_gain': 1,
            'maintenance': 2,
            'athletic_performance': 3
        }
        
        # Encode activity
        activity_encoding = {
            'sedentary': 1,
            'light': 2,
            'moderate': 3,
            'active': 4,
            'very_active': 5
        }
        
        # User features (7)
        features = [
            profile['age'],
            profile['weight_kg'],
            profile['height_cm'],
            profile['bmi'],
            1 if profile['gender'] == 'male' else 0,
            goal_encoding.get(profile['goal'], 2),
            activity_encoding.get(profile['activity_level'], 3)
        ]
        
        # Meal nutrition features (5)
        features.extend([
            nutrition['calories'],
            nutrition['protein_g'],
            nutrition['carbs_g'],
            nutrition['fat_g'],
            nutrition['fiber_g']
        ])
        
        # Derived features (8)
        total_macros = nutrition['protein_g'] + nutrition['carbs_g'] + nutrition['fat_g']
        if total_macros > 0:
            protein_ratio = nutrition['protein_g'] / total_macros
            carb_ratio = nutrition['carbs_g'] / total_macros
            fat_ratio = nutrition['fat_g'] / total_macros
        else:
            protein_ratio = carb_ratio = fat_ratio = 0.33
        
        # Protein per calorie
        protein_per_cal = nutrition['protein_g'] / nutrition['calories'] if nutrition['calories'] > 0 else 0
        
        # Fiber ratio
        fiber_ratio = nutrition['fiber_g'] / nutrition['calories'] * 100 if nutrition['calories'] > 0 else 0
        
        # Calorie density score
        cal_score = min(nutrition['calories'] / 600, 1.0)  # Normalized to 600 cal
        
        # Number of foods
        num_foods = len(meal['foods'])
        
        # Macro balance (deviation from ideal 30-40-30)
        ideal = [0.3, 0.4, 0.3]
        actual = [protein_ratio, carb_ratio, fat_ratio]
        macro_balance = 1 - np.mean([abs(a - i) for a, i in zip(actual, ideal)])
        
        features.extend([
            protein_ratio,
            carb_ratio,
            fat_ratio,
            protein_per_cal,
            fiber_ratio,
            cal_score,
            num_foods,
            macro_balance
        ])
        
        return np.array(features, dtype=np.float32)
    
    def load_data(self, dataset_file: str):
        """Load and preprocess dataset"""
        print(f"📥 Loading dataset from {dataset_file}...")
        
        dataset_path = Path(dataset_file)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_file}")
        
        # Load records
        records = []
        with open(dataset_path, 'r') as f:
            for line in f:
                records.append(json.loads(line.strip()))
        
        print(f"✓ Loaded {len(records)} records")
        
        # Extract features and labels
        print("🔧 Extracting features...")
        X = np.array([self.extract_features(r) for r in records])
        y = np.array([r['label'] for r in records])
        
        print(f"✓ Feature shape: {X.shape}")
        print(f"✓ Positive samples: {np.sum(y)} ({np.sum(y)/len(y)*100:.1f}%)")
        
        return X, y
    
    def train(self, dataset_file: str, epochs: int = 50, batch_size: int = 32):
        """Train the model"""
        print("="*70)
        print("  NEURAL NETWORK TRAINING")
        print("="*70)
        print()
        
        # Load data
        X, y = self.load_data(dataset_file)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Train: {len(X_train)} | Test: {len(X_test)}")
        
        # Scale features
        print("🔧 Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create datasets
        train_dataset = MealDataset(X_train_scaled, y_train)
        test_dataset = MealDataset(X_test_scaled, y_test)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size)
        
        # Initialize model
        print(f"🧠 Initializing neural network (device: {self.device})...")
        input_size = X_train_scaled.shape[1]
        self.model = MealRecommendationNN(input_size=input_size).to(self.device)
        
        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # Training loop
        print(f"\n🚀 Training for {epochs} epochs...")
        print()
        
        best_accuracy = 0
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            
            for features, labels in train_loader:
                features, labels = features.to(self.device), labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(features).squeeze()
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            
            # Evaluation
            self.model.eval()
            correct = 0
            total = 0
            
            with torch.no_grad():
                for features, labels in test_loader:
                    features, labels = features.to(self.device), labels.to(self.device)
                    outputs = self.model(features).squeeze()
                    predicted = (outputs > 0.5).float()
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            
            accuracy = 100 * correct / total
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
            
            # Print progress
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_train_loss:.4f} - Accuracy: {accuracy:.2f}% - Best: {best_accuracy:.2f}%")
        
        print()
        print(f"✅ Training complete! Best accuracy: {best_accuracy:.2f}%")
        
        # Save model
        self.save_model()
        
        return best_accuracy
    
    def save_model(self):
        """Save trained model and scaler"""
        model_path = self.output_dir / "model.pth"
        scaler_path = self.output_dir / "scaler.joblib"
        
        torch.save(self.model.state_dict(), model_path)
        joblib.dump(self.scaler, scaler_path)
        
        print(f"\n💾 Model saved to: {model_path}")
        print(f"💾 Scaler saved to: {scaler_path}")
    
    def load_model(self, input_size=20):
        """Load trained model"""
        model_path = self.output_dir / "model.pth"
        scaler_path = self.output_dir / "scaler.joblib"
        
        if not model_path.exists():
            raise FileNotFoundError("Model not found. Train the model first.")
        
        self.model = MealRecommendationNN(input_size=input_size).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.scaler = joblib.load(scaler_path)
        self.model.eval()
    
    def predict(self, user_profile: dict, meal: dict) -> dict:
        """Make prediction for a meal"""
        if self.model is None:
            self.load_model()
        
        # Create record
        record = {
            'user_profile': user_profile,
            'meal': meal,
            'label': 0  # Dummy
        }
        
        # Extract features
        features = self.extract_features(record)
        features_scaled = self.scaler.transform([features])
        features_tensor = torch.FloatTensor(features_scaled).to(self.device)
        
        # Predict
        with torch.no_grad():
            output = self.model(features_tensor).item()
        
        is_good = output > 0.5
        confidence = output if is_good else (1 - output)
        
        return {
            'is_good_for_you': bool(is_good),
            'confidence': float(confidence),
            'score': float(output),
            'recommendation': self._generate_recommendation(is_good, confidence, meal)
        }
    
    def _generate_recommendation(self, is_good: bool, confidence: float, meal: dict) -> str:
        """Generate human-readable recommendation"""
        nutrition = meal.get('nutrition', {})
        calories = nutrition.get('calories', 0)
        protein = nutrition.get('protein_g', 0)
        
        if is_good:
            if confidence > 0.85:
                return f"✅ Excellent choice! {calories:.0f} cal, {protein:.0f}g protein - perfect for your goals ({confidence*100:.0f}% confidence)"
            else:
                return f"👍 Good option. {calories:.0f} cal, {protein:.0f}g protein ({confidence*100:.0f}% confidence)"
        else:
            if confidence > 0.85:
                return f"⚠️ Not ideal for your goals. Consider adjusting portions or food choices ({confidence*100:.0f}% confidence)"
            else:
                return f"🤔 Uncertain. {calories:.0f} cal might work depending on your day ({confidence*100:.0f}% confidence)"


if __name__ == "__main__":
    trainer = NeuralModelTrainer()
    
    # Train on synthetic dataset
    accuracy = trainer.train(
        dataset_file="app/training/datasets/synthetic_meals.jsonl",
        epochs=50,
        batch_size=64
    )
    
    print("\n" + "="*70)
    print(f"🎉 Model training complete with {accuracy:.2f}% accuracy!")
    print("="*70)
