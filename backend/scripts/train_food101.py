"""
train_food101.py — Fine-tune ResNet18 on the Food-101 dataset.

Downloads Food-101 via torchvision, freezes the backbone except layer4,
replaces the FC head with a 101-class linear layer, and trains for
~10-15 epochs.  Saves the best model (by validation top-1 accuracy) to
    backend/weights/resnet18_food101.pth

Run locally or in Google Colab:
    python backend/scripts/train_food101.py

Expected results (ResNet18, frozen layers 1-3, ~10 epochs):
    Top-1 accuracy ≥ 70-75%   |   Top-5 accuracy ≥ 92-95%

Training time:
    GPU (T4/RTX 3060): ~1-2 hours
    CPU: ~12-24 hours (functional but slow)
"""

import os
import sys
import time
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from torchvision.models import ResNet18_Weights

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
WEIGHTS_DIR = BACKEND_DIR / "weights"
BEST_MODEL_PATH = WEIGHTS_DIR / "resnet18_food101.pth"

# Food-101 class names (sorted alphabetically, matching torchvision ordering)
FOOD101_CLASSES = sorted([
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
    'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak',
    'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki', 'tiramisu',
    'tuna_tartare', 'waffles',
])

NUM_CLASSES = 101


# ── Data transforms ───────────────────────────────────────────────────────────

def get_transforms():
    """ImageNet-normalised transforms with training augmentation."""
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(imagenet_mean, imagenet_std),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(imagenet_mean, imagenet_std),
    ])

    return train_transform, val_transform


# ── Model ─────────────────────────────────────────────────────────────────────

def build_model(unfreeze_layer4: bool = True) -> nn.Module:
    """Load pretrained ResNet18 and replace the FC head."""
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)

    # Freeze everything
    for param in model.parameters():
        param.requires_grad = False

    # Unfreeze layer4 for better feature adaptation
    if unfreeze_layer4:
        for param in model.layer4.parameters():
            param.requires_grad = True

    # Replace the classification head
    num_features = model.fc.in_features  # 512 for ResNet18
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(num_features, NUM_CLASSES),
    )

    return model


# ── Training loop ─────────────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer, device, epoch, total_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if (batch_idx + 1) % 50 == 0:
            print(f"  Epoch [{epoch}/{total_epochs}] Batch [{batch_idx+1}/{len(loader)}] "
                  f"Loss: {loss.item():.4f} Acc: {100.*correct/total:.1f}%")

    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct_top1 = 0
    correct_top5 = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        total += labels.size(0)

        # Top-1
        _, pred = outputs.max(1)
        correct_top1 += pred.eq(labels).sum().item()

        # Top-5
        _, pred5 = outputs.topk(5, dim=1)
        correct_top5 += pred5.eq(labels.unsqueeze(1)).any(1).sum().item()

    val_loss = running_loss / total
    top1_acc = 100. * correct_top1 / total
    top5_acc = 100. * correct_top5 / total
    return val_loss, top1_acc, top5_acc


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fine-tune ResNet18 on Food-101")
    parser.add_argument("--epochs", type=int, default=12, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr-head", type=float, default=1e-3, help="Learning rate for FC head")
    parser.add_argument("--lr-backbone", type=float, default=1e-4, help="Learning rate for layer4")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader workers")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU training")
    args = parser.parse_args()

    # Device
    if args.no_gpu or not torch.cuda.is_available():
        device = torch.device("cpu")
        if not args.no_gpu:
            print("[!] No GPU detected. Training on CPU (this will be slow).")
    else:
        device = torch.device("cuda")
        print(f"[OK] Using GPU: {torch.cuda.get_device_name(0)}")

    # Data
    print(f"Loading Food-101 dataset to {DATA_DIR} …")
    train_transform, val_transform = get_transforms()

    train_dataset = datasets.Food101(
        root=str(DATA_DIR), split="train", download=True, transform=train_transform
    )
    val_dataset = datasets.Food101(
        root=str(DATA_DIR), split="test", download=True, transform=val_transform
    )

    print(f"  Train: {len(train_dataset)} images  |  Val: {len(val_dataset)} images")

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=args.workers, pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=(device.type == "cuda"),
    )

    # Model
    model = build_model(unfreeze_layer4=True).to(device)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Model params: {total_params:,} total, {trainable:,} trainable "
          f"({100*trainable/total_params:.1f}%)")

    # Optimizer — different LR for head vs backbone
    head_params = list(model.fc.parameters())
    backbone_params = list(model.layer4.parameters())
    optimizer = optim.Adam([
        {"params": head_params, "lr": args.lr_head},
        {"params": backbone_params, "lr": args.lr_backbone},
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()

    # Training
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    best_top1 = 0.0
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f" Training ResNet18 on Food-101 — {args.epochs} epochs")
    print(f"{'='*60}\n")

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch, args.epochs
        )
        val_loss, top1_acc, top5_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        epoch_time = time.time() - epoch_start

        # Save best model
        improved = ""
        if top1_acc > best_top1:
            best_top1 = top1_acc
            torch.save(model.state_dict(), str(BEST_MODEL_PATH))
            improved = " ★ BEST"

        print(f"Epoch {epoch:2d}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% | "
              f"Val Loss: {val_loss:.4f} Top-1: {top1_acc:.1f}% Top-5: {top5_acc:.1f}% | "
              f"{epoch_time:.0f}s{improved}")

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f" Training complete in {total_time/60:.1f} minutes")
    print(f" Best Top-1 Accuracy: {best_top1:.1f}%")
    print(f" Model saved to: {BEST_MODEL_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
