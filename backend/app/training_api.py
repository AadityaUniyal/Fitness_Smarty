"""
Training API Router

Handles requests to:
1. Ingest new training data (images/labels)
2. Trigger model retraining (Recommendation NN, YOLO, ResNet, User Clustering, LSTM, DQN, Q-Learning)
3. Manage dataset registry
4. Query training status
"""

import json
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.admin import require_admin
from app.database import get_db
from app.models import EnhancedUser, FoodTrainingSample


class RetrainingLockManager:
    """Manages concurrency locks per retraining job type."""

    def __init__(self):
        self._locks = {}
        self._global_lock = threading.Lock()

    def get_lock(self, job_name: str) -> threading.Lock:
        with self._global_lock:
            if job_name not in self._locks:
                self._locks[job_name] = threading.Lock()
            return self._locks[job_name]

    def try_acquire(self, job_name: str) -> bool:
        lock = self.get_lock(job_name)
        return lock.acquire(blocking=False)

    def release(self, job_name: str):
        lock = self.get_lock(job_name)
        if lock.locked():
            try:
                lock.release()
            except RuntimeError:
                pass


_training_locks = RetrainingLockManager()


def _run_with_lock(job_name: str, func, *args, **kwargs):
    """Background task wrapper ensuring lock release upon job completion or failure."""
    try:
        func(*args, **kwargs)
    finally:
        _training_locks.release(job_name)


router = APIRouter(
    prefix="/api/training",
    tags=["training"],
    dependencies=[Depends(require_admin)],
)

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
    db: Session = Depends(get_db),
    admin: EnhancedUser = Depends(require_admin),
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
        calories=0,
    )
    db.add(db_sample)
    db.commit()
    return {
        "status": "success",
        "message": f"Saved sample for {label}",
        "path": str(file_path),
    }


@router.post("/recommendation/train", status_code=status.HTTP_202_ACCEPTED)
async def train_recommendation_model(
    background_tasks: BackgroundTasks,
    epochs: int = 50,
    use_db: bool = False,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train the neural recommendation model asynchronously in background."""
    job_name = "recommendation"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_neural_model import NeuralModelTrainer

        trainer = NeuralModelTrainer()
        trainer.train("app/training/datasets/synthetic_meals.jsonl", use_db, epochs)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": f"Recommendation model training started in background (DB Mode: {use_db})",
        "job": job_name,
    }


@router.post("/vision/train-detector", status_code=status.HTTP_202_ACCEPTED)
async def train_food_detector(
    background_tasks: BackgroundTasks,
    images_src: Optional[str] = None,
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train YOLOv8 food detector asynchronously in background."""
    job_name = "vision_detector"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_food_detector import FoodDetectorTrainer

        trainer = FoodDetectorTrainer()
        trainer.train(images_src=images_src, epochs=epochs, imgsz=imgsz, batch=batch)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "Food detector training started in background",
        "job": job_name,
    }


@router.post("/vision/train-classifier", status_code=status.HTTP_202_ACCEPTED)
async def train_health_classifier(
    background_tasks: BackgroundTasks,
    dataset: Optional[str] = None,
    epochs: int = 30,
    batch: int = 32,
    lr: float = 0.001,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train ResNet50 health classifier asynchronously in background."""
    job_name = "vision_classifier"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_health_classifier import HealthClassifierTrainer

        trainer = HealthClassifierTrainer(dataset_root=dataset)
        trainer.train(epochs=epochs, batch_size=batch, lr=lr)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "Health classifier training started in background",
        "job": job_name,
    }


@router.post("/cluster/users", status_code=status.HTTP_202_ACCEPTED)
async def cluster_users(
    background_tasks: BackgroundTasks,
    n_clusters: Optional[int] = None,
    method: str = "kmeans",
    admin: EnhancedUser = Depends(require_admin),
):
    """Cluster users into archetypes asynchronously in background."""
    job_name = "user_clustering"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.user_clustering import (
            UserClusterEngine,
            generate_sample_profiles,
        )

        profiles = generate_sample_profiles(200)
        engine = UserClusterEngine()
        engine.fit(profiles, n_clusters=n_clusters, method=method)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "User clustering started in background",
        "job": job_name,
    }


@router.post("/forecast/train-lstm", status_code=status.HTTP_202_ACCEPTED)
async def train_lstm(
    background_tasks: BackgroundTasks,
    epochs: int = 100,
    seq_length: int = 14,
    hidden: int = 64,
    layers: int = 2,
    batch: int = 32,
    lr: float = 0.001,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train LSTM weight predictor asynchronously in background."""
    job_name = "forecast_lstm"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_lstm import LSTMTrainer

        trainer = LSTMTrainer()
        trainer.train(
            seq_length=seq_length,
            hidden_size=hidden,
            num_layers=layers,
            epochs=epochs,
            batch_size=batch,
            lr=lr,
        )

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "LSTM forecast model training started in background",
        "job": job_name,
    }


@router.post("/rl/train-dqn", status_code=status.HTTP_202_ACCEPTED)
async def train_dqn(
    background_tasks: BackgroundTasks,
    episodes: int = 500,
    batch: int = 64,
    lr: float = 0.001,
    gamma: float = 0.99,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train DQN meal sequencer asynchronously in background."""
    job_name = "rl_dqn"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_dqn import DQNTrainer

        trainer = DQNTrainer()
        trainer.train(episodes=episodes, batch_size=batch, lr=lr, gamma=gamma)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "DQN training started in background",
        "job": job_name,
    }


@router.post("/rl/train-qlearning", status_code=status.HTTP_202_ACCEPTED)
async def train_qlearning(
    background_tasks: BackgroundTasks,
    episodes: int = 1000,
    alpha: float = 0.1,
    gamma: float = 0.95,
    admin: EnhancedUser = Depends(require_admin),
):
    """Train Q-Learning habit former asynchronously in background."""
    job_name = "rl_qlearning"
    if not _training_locks.try_acquire(job_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Retraining job for '{job_name}' is already in progress.",
        )

    def _task():
        from app.training.train_qlearning import QLearningTrainer

        trainer = QLearningTrainer()
        trainer.train(episodes=episodes, alpha=alpha, gamma=gamma)

    background_tasks.add_task(_run_with_lock, job_name, _task)
    return {
        "status": "accepted",
        "message": "Q-learning habit former training started in background",
        "job": job_name,
    }


@router.post("/cluster/predict")
async def predict_user_cluster(
    profile: dict,
    admin: EnhancedUser = Depends(require_admin),
):
    """Assign a user profile to the nearest cluster."""
    from app.training.user_clustering import UserClusterEngine

    engine = UserClusterEngine()
    result = engine.predict(profile)
    return result


@router.get("/datasets")
async def list_datasets(
    admin: EnhancedUser = Depends(require_admin),
):
    """List all registered training datasets."""
    from app.training.data_collector import DataCollector

    collector = DataCollector()
    return {
        "datasets": collector.list_datasets(),
        "statistics": collector.get_statistics(),
    }


@router.post("/datasets/create")
async def create_dataset(
    name: str,
    source_dir: str,
    val_split: float = 0.15,
    admin: EnhancedUser = Depends(require_admin),
):
    """Create a structured dataset from class folders."""
    from app.training.data_collector import DataCollector

    collector = DataCollector()
    manifest = collector.create_dataset(name, source_dir, val_split=val_split)
    if manifest:
        return {"status": "success", "manifest": manifest}
    raise HTTPException(400, "Failed to create dataset")


@router.get("/status")
async def training_status(
    db: Session = Depends(get_db),
    admin: EnhancedUser = Depends(require_admin),
):
    """Get overall training pipeline status."""
    from app.training.data_collector import DataCollector

    collector = DataCollector()
    model_dir = Path("app/training/models")
    models_list = []
    if model_dir.exists():
        for p in list(model_dir.rglob("*.pth")) + list(model_dir.rglob("*.joblib")):
            models_list.append(
                {"name": p.stem, "path": str(p), "size_kb": p.stat().st_size / 1024}
            )

    from app.models import CoachFeedback

    feedback_count = db.query(CoachFeedback).count()

    return {
        "datasets": collector.get_statistics(),
        "trained_models": models_list,
        "feedback_samples_count": feedback_count,
    }
