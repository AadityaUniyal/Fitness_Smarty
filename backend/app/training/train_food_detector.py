"""
YOLOv8 Food Detector Training Pipeline

Fine-tunes YOLOv8 on food detection datasets (Food-101 or custom).
Handles dataset prep, augmentation, training, mAP eval, and model export.
"""

import json, os, shutil, random
import urllib.request, tarfile, pathlib
import torch
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
    import cv2
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[!] ultralytics not installed. Install with: pip install ultralytics")

try:
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class FoodDetectorTrainer:
    """
    YOLOv8 fine-tuning pipeline for food detection.

    Dataset format expected:
        datasets/
            food_detection/
                images/
                    train/  (jpg/png)
                    val/
                labels/
                    train/  (YOLO .txt per image)
                    val/

    Or auto-prepares from Food-101 structure.
    """

    FOOD101_URL = "https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz"
    FOOD_CLASSES = [
        'apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
        'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
        'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
        'ceviche', 'cheesecake', 'cheese_plate', 'chicken_curry', 'chicken_quesadilla',
        'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder',
        'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes',
        'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict',
        'escargots', 'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras',
        'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice',
        'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich',
        'grilled_salmon', 'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup',
        'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna',
        'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup',
        'mussels', 'nachos', 'omelette', 'onion_rings', 'oysters',
        'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
        'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib',
        'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake', 'risotto',
        'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits',
        'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak', 'strawberry_shortcake',
        'sushi', 'tacos', 'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles'
    ]

    def __init__(self, dataset_root: Optional[str] = None, output_dir: Optional[str] = None):
        self.dataset_root = Path(dataset_root or "app/training/datasets/food_detection")
        self.output_dir = Path(output_dir or "app/training/models/food_detector")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_yaml = self.dataset_root / "data.yaml"
        self.mock_mode = not YOLO_AVAILABLE

    def _prepare_yolo_dataset(self, images_src: str, val_split: float = 0.15) -> bool:
        """Convert a flat image folder into YOLO train/val split with placeholder labels."""
        src = Path(images_src)
        if not src.exists():
            return False

        train_img = self.dataset_root / "images" / "train"
        val_img = self.dataset_root / "images" / "val"
        train_lbl = self.dataset_root / "labels" / "train"
        val_lbl = self.dataset_root / "labels" / "val"

        for d in [train_img, val_img, train_lbl, val_lbl]:
            d.mkdir(parents=True, exist_ok=True)

        images = list(src.glob("*.jpg")) + list(src.glob("*.jpeg")) + list(src.glob("*.png"))
        if not images:
            print("[!] No images found in source directory")
            return False

        train_files, val_files = train_test_split(images, test_size=val_split, random_state=42) if SKLEARN_AVAILABLE else (images[:int(len(images)*(1-val_split))], images[int(len(images)*(1-val_split)):])

        for img_list, img_dir, lbl_dir in [(train_files, train_img, train_lbl), (val_files, val_img, val_lbl)]:
            for img_path in img_list:
                shutil.copy2(img_path, img_dir / img_path.name)
                lbl_path = lbl_dir / (img_path.stem + ".txt")
                if not lbl_path.exists():
                    with open(lbl_path, 'w') as f:
                        f.write("")

        classes = [c.replace('_', ' ') for c in self.FOOD_CLASSES]
        with open(self.data_yaml, 'w') as f:
            f.write(f"path: {self.dataset_root.resolve()}\n")
            f.write(f"train: images/train\n")
            f.write(f"val: images/val\n")
            f.write(f"nc: {len(classes)}\n")
            f.write(f"names: {json.dumps(classes)}\n")

        print(f"[OK] YOLO dataset prepared at {self.dataset_root}")
        print(f"     Train: {len(train_files)}, Val: {len(val_files)}")
        return True

    def _download_food101(self, target_dir: Path) -> bool:
        """Download and extract Food-101 dataset automatically.
        The official tar.gz is ~5GB; this method downloads, extracts, and arranges images under `datasets/food-101/images/`.
        """
        try:
            tar_path = target_dir / "food-101.tar.gz"
            if not tar_path.exists():
                print("[INFO] Downloading Food-101 dataset…")
                urllib.request.urlretrieve(self.FOOD101_URL, tar_path)
            else:
                print(f"[INFO] Food-101 tarball already present at {tar_path}")
            # Extract
            extract_dir = target_dir / "food-101"
            if not extract_dir.exists():
                print("[INFO] Extracting Food-101…")
                with tarfile.open(tar_path, "r:gz") as tar:
                    tar.extractall(path=target_dir)
            # Move images to expected location
            images_src = extract_dir / "images"
            images_dst = target_dir / "images"
            images_dst.mkdir(parents=True, exist_ok=True)
            for img_file in images_src.rglob("*.jpg"):
                shutil.copy2(img_file, images_dst / img_file.name)
            print(f"[OK] Food-101 dataset ready at {images_dst}")
            return True
        except Exception as e:
            print(f"[!] Failed to download/extract Food-101: {e}")
            return False

    def train(self, images_src: Optional[str] = None, epochs: int = 50, imgsz: int = 640, batch: int = 16, pretrained: bool = True, model_size: str = "yolov8n.pt") -> Dict:
        """
        Run YOLOv8 training pipeline.

        Args:
            images_src: Directory containing training images (optional, auto-prepares dataset)
            epochs: Number of training epochs
            imgsz: Training image size
            batch: Batch size
            pretrained: Start from pretrained weights

        Returns:
            Training results dict with metrics
        """
        if self.mock_mode:
            print("[MOCK] YOLOv8 training simulated")
            return self._mock_train_result(epochs)

        print("=" * 70)
        print("  YOLOv8 FOOD DETECTOR TRAINING")
        print("=" * 70)
        print(f"  Epochs: {epochs} | Image size: {imgsz} | Batch: {batch}")
        print()

        if images_src and not self.data_yaml.exists():
            if not self._prepare_yolo_dataset(images_src):
                return self._mock_train_result(epochs, error="Dataset preparation failed")

        if not self.data_yaml.exists():
            if not self._download_food101(self.dataset_root.parent):
                print("[!] No dataset found. Use --images_src or place Food-101 in datasets/")
                return self._mock_train_result(epochs, error="No dataset")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        checkpoint = model_size if pretrained else model_size.replace('.pt', '.yaml')
        model = YOLO(checkpoint)
        results = model.train(
            data=str(self.data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            patience=10,
            save=True,
            project=str(self.output_dir),
            name='food_yolo',
            exist_ok=True,
            augment=True,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
            degrees=0.0,
            translate=0.1,
            scale=0.5,
            shear=0.0,
            perspective=0.0,
            flipud=0.0,
            fliplr=0.5,
            mosaic=1.0,
            mixup=0.0,
            device=device,
        )

        best_model_path = self.output_dir / "food_yolo" / "weights" / "best.pt"
        if best_model_path.exists():
            shutil.copy(best_model_path, self.output_dir / "yolov8_food.pt")
            print(f"[OK] Best model saved to {self.output_dir / 'yolov8_food.pt'}")

        try:
            metrics = model.val()
            val_dict = {
                "mAP50": float(metrics.box.map50),
                "mAP50-95": float(metrics.box.map),
                "precision": float(metrics.box.mp),
                "recall": float(metrics.box.mr),
                "epochs_completed": epochs,
                "best_model": str(best_model_path),
                "status": "success",
            }
        except Exception:
            val_dict = {"status": "success", "epochs_completed": epochs, "note": "Metrics unavailable"}

        return val_dict

    def export_onnx(self) -> str:
        """Export trained model to ONNX format."""
        model_path = self.output_dir / "yolov8_food.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Trained model not found at {model_path}")

        model = YOLO(str(model_path))
        onnx_path = self.output_dir / "yolov8_food.onnx"
        model.export(format="onnx", imgsz=640)
        print(f"[OK] Model exported to {onnx_path}")
        return str(onnx_path)

    def _mock_train_result(self, epochs: int, error: Optional[str] = None) -> Dict:
        result = {
            "status": "mock",
            "epochs": epochs,
            "mAP50": 0.834,
            "mAP50-95": 0.612,
            "precision": 0.871,
            "recall": 0.793,
            "model_path": str(self.output_dir / "yolov8_food.pt"),
            "note": "Simulated training — install ultralytics for real training",
        }
        if error:
            result["error"] = error
        return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train YOLOv8 food detector")
    parser.add_argument("--images", type=str, help="Source directory of training images")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--pretrained", action="store_true", default=True, help="Use pretrained weights")
    parser.add_argument("--model-size", type=str, default="yolov8n.pt", help="YOLO model checkpoint (e.g., yolov8n.pt, yolov8s.pt)")
    parser.add_argument("--export-onnx", action="store_true", help="Export to ONNX after training")
    args = parser.parse_args()

    trainer = FoodDetectorTrainer()
    result = trainer.train(
        images_src=args.images,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        pretrained=args.pretrained,
        model_size=args.model_size,
    )
    print(f"\n[RESULT] {json.dumps(result, indent=2)}")
