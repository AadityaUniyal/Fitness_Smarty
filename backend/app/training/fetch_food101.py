"""Utility script to download and extract the Food‑101 dataset.
The script downloads the official tar.gz, extracts it, and places images
under `app/training/datasets/food-101/images/` for the trainer to use.
"""
import urllib.request
import tarfile
import pathlib
import shutil

DATA_URL = "https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz"
# Resolve to the project's training datasets directory
TARGET_ROOT = pathlib.Path(__file__).resolve().parents[2] / "datasets" / "food-101"

def download_and_extract():
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    tar_path = TARGET_ROOT / "food-101.tar.gz"
    if not tar_path.exists():
        print("[INFO] Downloading Food-101...")
        urllib.request.urlretrieve(DATA_URL, tar_path)
    else:
        print(f"[INFO] Tarball already present: {tar_path}")
    with tarfile.open(tar_path, "r:gz") as tar:
        print("[INFO] Extracting Food‑101…")
        tar.extractall(path=TARGET_ROOT)
    # Flatten images into a single folder expected by the trainer
    img_src = TARGET_ROOT / "food-101" / "images"
    img_dst = TARGET_ROOT / "images"
    img_dst.mkdir(parents=True, exist_ok=True)
    for f in img_src.rglob("*.jpg"):
        shutil.copy2(f, img_dst / f.name)
    print("[OK] Food‑101 ready at", img_dst)

if __name__ == "__main__":
    download_and_extract()
