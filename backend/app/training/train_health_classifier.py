"""
ResNet50 Food Health Classifier Training

Fine-tunes ResNet50 to classify food images as healthy or unhealthy.
Uses transfer learning from ImageNet weights.
"""

import json, os
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np
from PIL import Image

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    import torchvision.transforms as transforms
    import torchvision.models as models
    from torchvision.datasets import ImageFolder
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not available. Install with: pip install torch torchvision")

try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False


class HealthClassifierTrainer:
    """
    ResNet50 fine-tuning for binary food health classification.

    Dataset format:
        datasets/
            food_health/
                train/
                    healthy/
                    unhealthy/
                val/
                    healthy/
                    unhealthy/
                test/
                    healthy/
                    unhealthy/
    """

    def __init__(self, dataset_root: Optional[str] = None, output_dir: Optional[str] = None):
        self.dataset_root = Path(dataset_root or "app/training/datasets/food_health")
        self.output_dir = Path(output_dir or "app/training/models/health_classifier")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
        self.mock_mode = not TORCH_AVAILABLE

    def _get_transforms(self, img_size: int = 224) -> Tuple:
        """Get train/val image transforms with augmentation."""
        train_transform = transforms.Compose([
            transforms.Resize(int(img_size * 1.15)),
            transforms.RandomResizedCrop(img_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        val_transform = transforms.Compose([
            transforms.Resize(int(img_size * 1.15)),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        return train_transform, val_transform

    def _load_data(self, batch_size: int = 32, num_workers: int = 2) -> Optional[Tuple]:
        """Load datasets using ImageFolder structure."""
        train_path = self.dataset_root / "train"
        val_path = self.dataset_root / "val"

        if not train_path.exists() or not val_path.exists():
            print(f"[!] Dataset not found at {self.dataset_root}")
            print("    Expected: train/{healthy,unhealthy}/  val/{healthy,unhealthy}/")
            return None

        train_tf, val_tf = self._get_transforms()
        train_dataset = ImageFolder(str(train_path), transform=train_tf)
        val_dataset = ImageFolder(str(val_path), transform=val_tf)

        class_names = train_dataset.classes
        print(f"[OK] Classes: {class_names} ({len(train_dataset)} train, {len(val_dataset)} val)")

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

        return train_loader, val_loader, class_names

    def _build_model(self, num_classes: int = 2, freeze_backbone: bool = True) -> nn.Module:
        """Build ResNet50 with custom classifier head."""
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

        if freeze_backbone:
            for param in model.parameters():
                param.requires_grad = False

        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

        return model.to(self.device)

    def _plot_training(self, save_path: Path):
        """Plot training curves."""
        if not PLOT_AVAILABLE:
            return
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        for ax, metric, title in [
            (axes[0], 'loss', 'Loss'),
            (axes[1], 'acc', 'Accuracy')
        ]:
            ax.plot(self.history[f'train_{metric}'], label=f'Train {title}')
            ax.plot(self.history[f'val_{metric}'], label=f'Val {title}')
            ax.set_xlabel('Epoch')
            ax.set_ylabel(title)
            ax.legend()
            ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(str(save_path), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] Training plot saved to {save_path}")

    def _plot_confusion_matrix(self, y_true: List[int], y_pred: List[int], class_names: List[str], save_path: Path):
        """Plot confusion matrix."""
        if not PLOT_AVAILABLE:
            return
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig(str(save_path), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] Confusion matrix saved to {save_path}")

    def train(self, epochs: int = 30, batch_size: int = 32, lr: float = 0.001, freeze_backbone: bool = True) -> Dict:
        """
        Run ResNet50 fine-tuning.

        Args:
            epochs: Number of training epochs
            batch_size: Batch size
            lr: Learning rate
            freeze_backbone: Freeze pretrained backbone (only train classifier head)

        Returns:
            Training results dict with metrics
        """
        if self.mock_mode:
            print("[MOCK] Health classifier training simulated")
            return self._mock_train_result(epochs)

        print("=" * 70)
        print("  ResNet50 FOOD HEALTH CLASSIFIER TRAINING")
        print("=" * 70)
        print(f"  Epochs: {epochs} | Batch: {batch_size} | LR: {lr} | Device: {self.device}")
        print()

        data = self._load_data(batch_size=batch_size)
        if data is None:
            return self._mock_train_result(epochs, error="Dataset not found")
        train_loader, val_loader, class_names = data

        self.model = self._build_model(num_classes=len(class_names), freeze_backbone=freeze_backbone)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(self.model.fc.parameters() if freeze_backbone else self.model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_val_acc = 0.0
        best_model_state = None

        for epoch in range(epochs):
            train_loss, train_correct, train_total = 0.0, 0, 0
            self.model.train()
            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()

            val_loss, val_correct, val_total = 0.0, 0, 0
            self.model.eval()
            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(self.device), labels.to(self.device)
                    outputs = self.model(images)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

            scheduler.step()

            train_acc = train_correct / train_total
            val_acc = val_correct / val_total
            self.history["train_loss"].append(train_loss / len(train_loader))
            self.history["val_loss"].append(val_loss / len(val_loader))
            self.history["train_acc"].append(train_acc)
            self.history["val_acc"].append(val_acc)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_state = self.model.state_dict()

            if (epoch + 1) % 5 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1}/{epochs}] Train Loss: {train_loss/len(train_loader):.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss/len(val_loader):.4f} Acc: {val_acc:.4f}")

        if best_model_state:
            self.model.load_state_dict(best_model_state)
            model_path = self.output_dir / "resnet50_food_health.pth"
            torch.save(self.model.state_dict(), model_path)
            print(f"[OK] Best model saved to {model_path}")

        self._plot_training(self.output_dir / "training_curves.png")

        all_preds, all_labels = [], []
        self.model.eval()
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(self.device)
                outputs = self.model(images)
                _, predicted = torch.max(outputs, 1)
                all_preds.extend(predicted.cpu().tolist())
                all_labels.extend(labels.cpu().tolist())

        self._plot_confusion_matrix(all_labels, all_preds, class_names, self.output_dir / "confusion_matrix.png")

        metrics = {
            "accuracy": float(accuracy_score(all_labels, all_preds)) if SKLEARN_AVAILABLE else float(best_val_acc),
            "epochs_completed": epochs,
            "best_val_accuracy": float(best_val_acc),
            "model_path": str(self.output_dir / "resnet50_food_health.pth"),
            "num_train_samples": len(train_loader.dataset),
            "num_val_samples": len(val_loader.dataset),
            "class_names": class_names,
            "status": "success",
        }

        if SKLEARN_AVAILABLE:
            metrics["precision"] = float(precision_score(all_labels, all_preds, average='weighted', zero_division=0))
            metrics["recall"] = float(recall_score(all_labels, all_preds, average='weighted', zero_division=0))
            metrics["f1_score"] = float(f1_score(all_labels, all_preds, average='weighted', zero_division=0))
            report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True, zero_division=0)
            metrics["classification_report"] = report

        return metrics

    def predict(self, image: Image.Image) -> Dict:
        """Run inference on a single image."""
        if self.model is None:
            model_path = self.output_dir / "resnet50_food_health.pth"
            if not model_path.exists():
                return {"error": "Model not trained yet"}
            self.model = self._build_model(num_classes=2)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()

        _, val_tf = self._get_transforms()
        tensor = val_tf(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)

        classes = self._get_class_names()
        return {
            "predicted": classes[predicted.item()],
            "confidence": float(probs[0][predicted.item()]),
            "probabilities": {classes[i]: float(probs[0][i]) for i in range(len(classes))},
        }

    def _get_class_names(self) -> List[str]:
        train_path = self.dataset_root / "train"
        if train_path.exists():
            return sorted([d.name for d in train_path.iterdir() if d.is_dir()])
        return ["healthy", "unhealthy"]

    def _mock_train_result(self, epochs: int, error: Optional[str] = None) -> Dict:
        result = {
            "status": "mock",
            "epochs": epochs,
            "accuracy": 0.892,
            "precision": 0.887,
            "recall": 0.892,
            "f1_score": 0.889,
            "model_path": str(self.output_dir / "resnet50_food_health.pth"),
            "note": "Simulated training — install torch & torchvision for real training",
        }
        if error:
            result["error"] = error
        return result


def generate_placeholder_dataset(output_dir: str, n_per_class: int = 50):
    """Generate small synthetic dataset for testing the pipeline."""
    out = Path(output_dir)
    for split in ["train", "val", "test"]:
        for cls_name in ["healthy", "unhealthy"]:
            cls_dir = out / split / cls_name
            cls_dir.mkdir(parents=True, exist_ok=True)
            for i in range(n_per_class):
                img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
                img.save(str(cls_dir / f"{cls_name}_{i:04d}.jpg"))
    print(f"[OK] Placeholder dataset generated at {out}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train ResNet50 health classifier")
    parser.add_argument("--dataset", type=str, help="Path to dataset root (train/val/test with healthy/unhealthy)")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--batch", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--generate-test-data", action="store_true", help="Generate placeholder dataset for testing")
    args = parser.parse_args()

    if args.generate_test_data:
        generate_placeholder_dataset(args.dataset or "app/training/datasets/food_health")
    else:
        trainer = HealthClassifierTrainer(dataset_root=args.dataset)
        result = trainer.train(epochs=args.epochs, batch_size=args.batch, lr=args.lr)
        print(f"\n[RESULT] {json.dumps(result, indent=2)}")
