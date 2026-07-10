"""
Training API Router

Handles requests to:
1. Ingest new training data (images/labels)
2. Trigger model retraining (Recommendation NN, YOLO, ResNet, Clustering)
3. Manage dataset registry
4. Query training status
"""

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import shutil
from pathlib import Path
import json
from datetime import datetime

from app.database import get_db
from app.models import FoodTrainingSample

router = APIRouter(prefix="/api/training", tags=["training"])

DATASET_DIR = Path("datasets")
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LABELS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/vision/ingest")
async def ingest_vision_sample(
    image: UploadFile = File(...),
    label: str = Form(...),
    confidence: float = Form(0.0),
    corrected: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Ingest a labeled meal image for training dataset."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label.replace(' ', '_')}_{timestamp}.jpg"
    file_path = IMAGES_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    db_sample = FoodTrainingSample(
        label=label,
        image_signature=str(file_path),
        source="n8n_ingest",
        verified=corrected,
        calories=0
    )
    db.add(db_sample)
    db.commit()
    return {"status": "success", "message": f"Saved sample for {label}", "path": str(file_path)}


@router.post("/recommendation/train")
async def train_recommendation_model(
    background_tasks: BackgroundTasks,
    epochs: int = 50,
    use_db: bool = False
):
    """Train the neural recommendation model in background."""
    from app.training.train_neural_model import NeuralModelTrainer
    trainer = NeuralModelTrainer()
    background_tasks.add_task(trainer.train, "app/training/datasets/synthetic_meals.jsonl", use_db, epochs)
    return {"status": "accepted", "message": f"Training started (DB Mode: {use_db})"}


@router.post("/vision/train-detector")
async def train_food_detector(
    background_tasks: BackgroundTasks,
    images_src: Optional[str] = None,
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16
):
    """
    Train YOLOv8 food detector.

    Args:
        images_src: Directory of training images (auto-prepares YOLO dataset)
        epochs: Number of epochs
        imgsz: Training image size
        batch: Batch size
    """
    from app.training.train_food_detector import FoodDetectorTrainer
    trainer = FoodDetectorTrainer()
    result = trainer.train(images_src=images_src, epochs=epochs, imgsz=imgsz, batch=batch)
    return result


@router.post("/vision/train-classifier")
async def train_health_classifier(
    background_tasks: BackgroundTasks,
    dataset: Optional[str] = None,
    epochs: int = 30,
    batch: int = 32,
    lr: float = 0.001
):
    """
    Train ResNet50 health classifier (healthy vs unhealthy food).

    Args:
        dataset: Path to dataset root (train/val with healthy/unhealthy)
        epochs: Number of epochs
        batch: Batch size
        lr: Learning rate
    """
    from app.training.train_health_classifier import HealthClassifierTrainer
    trainer = HealthClassifierTrainer(dataset_root=dataset)
    result = trainer.train(epochs=epochs, batch_size=batch, lr=lr)
    return result


@router.post("/cluster/users")
async def cluster_users(
    background_tasks: BackgroundTasks,
    n_clusters: Optional[int] = None,
    method: str = "kmeans"
):
    """
    Cluster users into archetypes for personalized recommendations.
    Reads user profiles from the database.
    """
    from app.training.user_clustering import UserClusterEngine, generate_sample_profiles
    profiles = generate_sample_profiles(200)
    engine = UserClusterEngine()
    result = engine.fit(profiles, n_clusters=n_clusters, method=method)
    return result


@router.post("/forecast/train-lstm")
async def train_lstm(
    epochs: int = 100,
    seq_length: int = 14,
    hidden: int = 64,
    layers: int = 2,
    batch: int = 32,
    lr: float = 0.001
):
    """Train LSTM weight predictor on synthetic time-series data."""
    from app.training.train_lstm import LSTMTrainer
    trainer = LSTMTrainer()
    result = trainer.train(seq_length=seq_length, hidden_size=hidden, num_layers=layers, epochs=epochs, batch_size=batch, lr=lr)
    return result


@router.post("/rl/train-dqn")
async def train_dqn(
    episodes: int = 500,
    batch: int = 64,
    lr: float = 0.001,
    gamma: float = 0.99
):
    """Train DQN meal sequencer with simulated meal environment."""
    from app.training.train_dqn import DQNTrainer
    trainer = DQNTrainer()
    result = trainer.train(episodes=episodes, batch_size=batch, lr=lr, gamma=gamma)
    return result


@router.post("/rl/train-qlearning")
async def train_qlearning(
    episodes: int = 1000,
    alpha: float = 0.1,
    gamma: float = 0.95
):
    """Train Q-Learning habit former with simulated habit environment."""
    from app.training.train_qlearning import QLearningTrainer
    trainer = QLearningTrainer()
    result = trainer.train(episodes=episodes, alpha=alpha, gamma=gamma)
    return result


@router.post("/cluster/predict")
async def predict_user_cluster(profile: dict):
    """Assign a user profile to the nearest cluster."""
    from app.training.user_clustering import UserClusterEngine
    engine = UserClusterEngine()
    result = engine.predict(profile)
    return result


@router.get("/datasets")
async def list_datasets():
    """List all registered training datasets."""
    from app.training.data_collector import DataCollector
    collector = DataCollector()
    return {"datasets": collector.list_datasets(), "statistics": collector.get_statistics()}


@router.post("/datasets/create")
async def create_dataset(name: str, source_dir: str, val_split: float = 0.15):
    """Create a structured dataset from class folders."""
    from app.training.data_collector import DataCollector
    collector = DataCollector()
    manifest = collector.create_dataset(name, source_dir, val_split=val_split)
    if manifest:
        return {"status": "success", "manifest": manifest}
    raise HTTPException(400, "Failed to create dataset")


@router.get("/status")
async def training_status(db: Session = Depends(get_db)):
    """Get overall training pipeline status."""
    from app.training.data_collector import DataCollector
    collector = DataCollector()
    model_dir = Path("app/training/models")
    models_list = []
    if model_dir.exists():
        for p in list(model_dir.rglob("*.pth")) + list(model_dir.rglob("*.joblib")):
            models_list.append({"name": p.stem, "path": str(p), "size_kb": p.stat().st_size / 1024})
            
    from app.models import CoachFeedback
    feedback_count = db.query(CoachFeedback).count()
    
    return {
        "datasets": collector.get_statistics(),
        "trained_models": models_list,
        "feedback_samples_count": feedback_count,
    }
