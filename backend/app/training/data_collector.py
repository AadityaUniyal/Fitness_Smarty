"""
Data Collection Pipeline

Automates collection, validation, and registration of training data.
Supports downloading from URLs, local file imports, and dataset registry management.
"""

import json, os, hashlib, csv, io
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

import numpy as np
from PIL import Image

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class DatasetManifest:
    """Metadata for a collected dataset."""
    name: str
    version: str
    description: str
    source: str
    license: str = "unknown"
    num_samples: int = 0
    num_classes: int = 0
    classes: List[str] = field(default_factory=list)
    created_at: str = ""
    split_sizes: Dict[str, int] = field(default_factory=dict)
    image_formats: List[str] = field(default_factory=list)
    file_hash: str = ""


class DataCollector:
    """
    Data collection and registry management.

    Features:
    - Download images from URLs
    - Import local files
    - Validate image integrity
    - Create dataset manifests
    - Register datasets in JSON registry
    - Split into train/val/test
    """

    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

    def __init__(self, registry_path: Optional[str] = None, storage_root: Optional[str] = None):
        self.registry_path = Path(registry_path or "app/training/datasets/registry.json")
        self.storage_root = Path(storage_root or "app/training/datasets")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.registry: Dict = {}
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    self.registry = json.load(f)
            except (json.JSONDecodeError, Exception):
                self.registry = {}

    def _hash_file(self, filepath: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha.update(chunk)
        return sha.hexdigest()

    def _validate_image(self, filepath: Path) -> bool:
        """Verify file is a valid image."""
        try:
            img = Image.open(filepath)
            img.verify()
            return True
        except Exception:
            return False

    def download_from_url(self, url: str, output_name: Optional[str] = None, category: Optional[str] = None) -> Optional[Path]:
        """Download a single image from URL."""
        if not REQUESTS_AVAILABLE:
            print("[!] requests not installed. Install with: pip install requests")
            return None

        try:
            resp = requests.get(url, timeout=30, stream=True)
            resp.raise_for_status()
            content_type = resp.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"[!] URL does not point to an image: {content_type}")
                return None

            ext = '.jpg'
            for e in self.SUPPORTED_FORMATS:
                if e in content_type:
                    ext = e
                    break

            dest_dir = self.storage_root / "downloads"
            if category:
                dest_dir = dest_dir / category
            dest_dir.mkdir(parents=True, exist_ok=True)

            filename = output_name or url.split('/')[-1].split('?')[0]
            if not any(filename.lower().endswith(e) for e in self.SUPPORTED_FORMATS):
                filename += ext

            filepath = dest_dir / filename
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            if self._validate_image(filepath):
                print(f"[OK] Downloaded {url} -> {filepath} ({filepath.stat().st_size / 1024:.1f} KB)")
                return filepath
            else:
                filepath.unlink(missing_ok=True)
                print(f"[!] Downloaded file is not a valid image: {url}")
                return None

        except Exception as e:
            print(f"[!] Failed to download {url}: {e}")
            return None

    def download_batch(self, urls: List[str], category: Optional[str] = None) -> List[Path]:
        """Download multiple images."""
        results = []
        for url in urls:
            path = self.download_from_url(url, category=category)
            if path:
                results.append(path)
        print(f"[OK] Downloaded {len(results)}/{len(urls)} images")
        return results

    def import_local(self, source_dir: str, category: Optional[str] = None, recursive: bool = True) -> List[Path]:
        """Import images from a local directory."""
        src = Path(source_dir)
        if not src.exists():
            print(f"[!] Source directory not found: {source_dir}")
            return []

        pattern = "**/*" if recursive else "*"
        imported = []
        for f in src.glob(pattern):
            if f.suffix.lower() in self.SUPPORTED_FORMATS:
                if not self._validate_image(f):
                    print(f"[!] Invalid image, skipping: {f}")
                    continue

                dest_dir = self.storage_root / "imported"
                if category:
                    dest_dir = dest_dir / category
                dest_dir.mkdir(parents=True, exist_ok=True)

                dest = dest_dir / f.name
                import shutil
                shutil.copy2(f, dest)
                imported.append(dest)

        print(f"[OK] Imported {len(imported)} images from {source_dir}")
        return imported

    def create_dataset(self, name: str, source_dir: str, val_split: float = 0.15, test_split: float = 0.05) -> Optional[DatasetManifest]:
        """
        Create a structured dataset from images organized in class folders.

        Expects: source_dir/class_name/*.jpg
        """
        src = Path(source_dir)
        if not src.exists():
            print(f"[!] Source not found: {source_dir}")
            return None

        # Find class directories
        class_dirs = [d for d in src.iterdir() if d.is_dir()]
        if not class_dirs:
            print(f"[!] No class subdirectories found in {source_dir}")
            return None

        all_images = []
        for cls_dir in class_dirs:
            class_name = cls_dir.name
            for img_path in cls_dir.glob("*"):
                if img_path.suffix.lower() in self.SUPPORTED_FORMATS and self._validate_image(img_path):
                    all_images.append((img_path, class_name))

        if not all_images:
            print("[!] No valid images found in class directories")
            return None

        np.random.shuffle(all_images)

        n = len(all_images)
        n_test = int(n * test_split)
        n_val = int(n * val_split)

        test_set = all_images[:n_test]
        val_set = all_images[n_test:n_test + n_val]
        train_set = all_images[n_test + n_val:]

        dataset_dir = self.storage_root / name
        for split_name, split_data in [("train", train_set), ("val", val_set), ("test", test_set)]:
            for img_path, class_name in split_data:
                dest = dataset_dir / split_name / class_name / img_path.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(img_path, dest)

        classes = sorted(set(cls for _, cls in all_images))
        manifest = DatasetManifest(
            name=name,
            version="1.0.0",
            description=f"Dataset with {n} images across {len(classes)} classes",
            source=str(src),
            num_samples=n,
            num_classes=len(classes),
            classes=classes,
            created_at=datetime.utcnow().isoformat(),
            split_sizes={"train": len(train_set), "val": len(val_set), "test": len(test_set)},
            image_formats=list(set(img_path.suffix.lower() for img_path, _ in all_images)),
        )

        self._register_dataset(manifest)
        print(f"[OK] Dataset '{name}' created at {dataset_dir}")
        print(f"     {len(train_set)} train, {len(val_set)} val, {len(test_set)} test, {len(classes)} classes")
        return manifest

    def _register_dataset(self, manifest: DatasetManifest):
        """Register dataset in the JSON registry."""
        entry = asdict(manifest)
        entry["updated_at"] = datetime.utcnow().isoformat()
        self.registry[manifest.name] = entry
        self._save_registry()

    def _save_registry(self):
        """Persist registry to disk."""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def list_datasets(self) -> List[str]:
        """List all registered datasets."""
        return list(self.registry.keys())

    def get_dataset_info(self, name: str) -> Optional[Dict]:
        """Get metadata for a registered dataset."""
        return self.registry.get(name)

    def remove_dataset(self, name: str) -> bool:
        """Remove dataset from registry (does not delete files)."""
        if name in self.registry:
            del self.registry[name]
            self._save_registry()
            print(f"[OK] Dataset '{name}' removed from registry")
            return True
        return False

    def export_registry_csv(self, output_path: str):
        """Export registry summary to CSV."""
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Version", "Samples", "Classes", "Source", "Created"])
            for entry in self.registry.values():
                writer.writerow([entry["name"], entry["version"], entry["num_samples"], entry["num_classes"], entry["source"], entry["created_at"]])
        print(f"[OK] Registry exported to {output_path}")

    def get_statistics(self) -> Dict:
        """Get aggregate statistics across all datasets."""
        total_samples = sum(e.get("num_samples", 0) for e in self.registry.values())
        total_datasets = len(self.registry)
        return {
            "total_datasets": total_datasets,
            "total_samples": total_samples,
            "datasets": self.list_datasets(),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Data Collection Pipeline")
    sub = parser.add_subparsers(dest="command")

    dl = sub.add_parser("download", help="Download image from URL")
    dl.add_argument("url", type=str, help="Image URL")
    dl.add_argument("--category", type=str, help="Category folder")

    imp = sub.add_parser("import", help="Import images from local directory")
    imp.add_argument("source", type=str, help="Source directory")
    imp.add_argument("--category", type=str, help="Category folder")

    create = sub.add_parser("create", help="Create structured dataset from class folders")
    create.add_argument("name", type=str, help="Dataset name")
    create.add_argument("source", type=str, help="Source directory with class subfolders")
    create.add_argument("--val", type=float, default=0.15)

    info = sub.add_parser("list", help="List registered datasets")
    info_p = sub.add_parser("info", help="Get dataset info")
    info_p.add_argument("name", type=str, help="Dataset name")

    args = parser.parse_args()
    collector = DataCollector()

    if args.command == "download":
        collector.download_from_url(args.url, category=args.category)
    elif args.command == "import":
        collector.import_local(args.source, category=args.category)
    elif args.command == "create":
        collector.create_dataset(args.name, args.source, val_split=args.val)
    elif args.command == "list":
        for name in collector.list_datasets():
            info = collector.get_dataset_info(name)
            print(f"  {name}: {info['num_samples']} samples, {info['num_classes']} classes" if info else f"  {name}")
    elif args.command == "info":
        info = collector.get_dataset_info(args.name)
        if info:
            print(json.dumps(info, indent=2))
        else:
            print(f"[!] Dataset '{args.name}' not found")
    else:
        parser.print_help()
