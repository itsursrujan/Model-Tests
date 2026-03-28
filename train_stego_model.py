import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np
import os
import random
from steganalysis_model import StegoCNN
import torchvision.transforms as transforms

# ---------------------------------------------------------------------------
# Training Configuration
# ---------------------------------------------------------------------------

EPOCHS = 10
BATCH_SIZE = 16
LR = 0.0003
IMAGE_SIZE = (128, 128)
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')

# Target samples per class (balanced)
TARGET_CLEAN = 8000
TARGET_STEGO = 8000

# ---------------------------------------------------------------------------
# STANDARDIZED NORMALIZATION (MUST be identical in training AND inference)
# ---------------------------------------------------------------------------
NORMALIZE = transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])

# ---------------------------------------------------------------------------
# Dataset Loader
# ---------------------------------------------------------------------------

class StegoDataset(Dataset):
    """
    Standard dataset loader for Steganalysis.
    """
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
            if self.transform:
                img = self.transform(img)
            else:
                img = transforms.Compose([
                    transforms.Resize(IMAGE_SIZE),
                    transforms.ToTensor(),
                    NORMALIZE,
                ])(img)
            return img, label
        except Exception as e:
            # Return zero tensor on error
            return torch.zeros(3, IMAGE_SIZE[0], IMAGE_SIZE[1]), label

def get_train_transforms():
    """
    Augmentation: horizontal flip + 90-degree rotation choices.
    INCLUDES normalization for training/inference parity.
    """
    return transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomChoice([
            transforms.RandomRotation(degrees=(0, 0)),
            transforms.RandomRotation(degrees=(90, 90)),
            transforms.RandomRotation(degrees=(180, 180)),
            transforms.RandomRotation(degrees=(270, 270))
        ]),
        transforms.ToTensor(),
        NORMALIZE,
    ])

def get_val_transforms():
    return transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        NORMALIZE,
    ])

# ---------------------------------------------------------------------------
# INFERENCE TRANSFORM (matches training normalization exactly)
# ---------------------------------------------------------------------------

def get_inference_transform():
    """Single-patch inference transform — identical normalization to training."""
    return transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        NORMALIZE,
    ])

# ---------------------------------------------------------------------------
# Dataset Sampling & Discovery
# ---------------------------------------------------------------------------

def discover_datasets(stegoimages_root, mendeley_root):
    """
    Discovers and balances samples from both datasets.
    Targets TARGET_CLEAN clean and TARGET_STEGO stego samples.
    """
    random.seed(42)

    # 1. Discover from stegoimagesdataset
    all_stegoimages_clean = []
    all_stegoimages_stego = []

    for root, dirs, files in os.walk(stegoimages_root):
        folder_name = os.path.basename(root).lower()
        if 'clean' in folder_name:
            for f in files:
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    all_stegoimages_clean.append(os.path.join(root, f))
        elif ('stego' in folder_name
              and 'stego_b64' not in str(root).lower()
              and 'stego_zip' not in str(root).lower()):
            for f in files:
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    all_stegoimages_stego.append(os.path.join(root, f))

    print(f"  [Discovery] stegoimagesdataset: {len(all_stegoimages_clean)} clean, {len(all_stegoimages_stego)} stego")

    # 2. Discover from Mendeley
    all_mendeley_clean = []
    all_mendeley_stego = []

    for root, dirs, files in os.walk(mendeley_root):
        folder_name = os.path.basename(root).upper()
        if 'CLEAN' in folder_name:
            for f in files:
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    all_mendeley_clean.append(os.path.join(root, f))
        elif any(tech in folder_name for tech in ['BPCS', 'LSB', 'PVD']):
            for f in files:
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    all_mendeley_stego.append(os.path.join(root, f))

    print(f"  [Discovery] Mendeley: {len(all_mendeley_clean)} clean, {len(all_mendeley_stego)} stego")

    # 3. Combine pools
    combined_clean = all_stegoimages_clean + all_mendeley_clean
    combined_stego = all_stegoimages_stego + all_mendeley_stego

    # 4. Sample exactly TARGET_CLEAN / TARGET_STEGO (or max available)
    n_clean = min(TARGET_CLEAN, len(combined_clean))
    n_stego = min(TARGET_STEGO, len(combined_stego))

    # Enforce equal class balance
    n_each = min(n_clean, n_stego)

    final_clean = random.sample(combined_clean, n_each)
    final_stego = random.sample(combined_stego, n_each)

    print(f"  [Balancing] Using {n_each} clean + {n_each} stego = {n_each * 2} total samples")

    samples = [(p, 0) for p in final_clean] + [(p, 1) for p in final_stego]
    random.shuffle(samples)

    return samples

# ---------------------------------------------------------------------------
# Training Main
# ---------------------------------------------------------------------------

def train_model():
    print("=" * 60)
    print("  StegoCNN Training — Balanced & Calibrated")
    print("=" * 60)

    # Dataset roots
    datasets_root = r'C:\Users\Srujan Aravalli\Desktop\Model Tests\datasets'
    stegoimages_root = os.path.join(datasets_root, 'stegoimagesdataset -marcozuppelli')
    mendeley_root = os.path.join(datasets_root, 'Mendeley Data - Steganography Analysis Dataset')

    # 1. Prepare Samples
    all_samples = discover_datasets(stegoimages_root, mendeley_root)

    # 2. Train / Validation Split (80 / 20)
    random.shuffle(all_samples)
    num_train = int(0.8 * len(all_samples))
    train_samples = all_samples[:num_train]
    val_samples = all_samples[num_train:]

    train_ds = StegoDataset(train_samples, transform=get_train_transforms())
    val_ds = StegoDataset(val_samples, transform=get_val_transforms())

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=True if torch.cuda.is_available() else False
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    print(f"  [Setup] Train: {len(train_samples)}, Val: {len(val_samples)}")

    # 3. Model & Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  [Setup] Training on: {device}")

    model = StegoCNN().to(device)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    # Early stopping — patience = 2
    best_val_acc = 0.0
    patience_counter = 0
    MAX_PATIENCE = 2

    # Strict save path — ONLY stego_model.pth
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stego_model.pth")

    # 4. Training Loop
    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_correct = 0
        train_total = 0
        running_loss = 0.0

        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            # NaN guard on input
            if torch.isnan(inputs).any():
                inputs = torch.nan_to_num(inputs, nan=0.0)

            optimizer.zero_grad()
            outputs = model(inputs)

            # NaN guard on output
            if torch.isnan(outputs).any():
                print(f"  [Warning] NaN in model output at batch {i}, skipping")
                continue

            loss = criterion(outputs, labels)

            if torch.isnan(loss):
                print(f"  [Warning] NaN loss at batch {i}, skipping")
                continue

            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            train_correct += (preds == labels).type(torch.int).sum().item()
            train_total += labels.size(0)

            if (i + 1) % 50 == 0:
                print(f"    Epoch {epoch:02d} | Batch {i+1}/{len(train_loader)} | Acc: {train_correct/train_total:.4f}")

        train_acc = (train_correct / train_total) if train_total > 0 else 0
        avg_loss = running_loss / max(len(train_loader), 1)

        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                if torch.isnan(inputs).any():
                    inputs = torch.nan_to_num(inputs, nan=0.0)
                outputs = model(inputs)
                if torch.isnan(outputs).any():
                    outputs = torch.nan_to_num(outputs, nan=0.0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).type(torch.int).sum().item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) if val_total > 0 else 0

        print(f"Epoch {epoch:02d}/{EPOCHS} | Loss: {avg_loss:.4f} | Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f}")

        # Save best model (overwrite stego_model.pth only)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), save_path)
            print(f"  [Best] Model saved -> stego_model.pth (Val Acc: {best_val_acc:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= MAX_PATIENCE:
                print(f"  [Early Stopping] No improvement for {MAX_PATIENCE} epochs. Stopping.")
                break

    print("=" * 60)
    print(f"Training Complete. Best Val Accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {save_path}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# PATCH-BASED INFERENCE (Resolution-Independent)
# ---------------------------------------------------------------------------

def predict_image(model, img_input):
    """
    Predict stego probability for an image using PATCH-BASED inference.
    
    Steps:
    1. Load image in RGB
    2. Split into 128x128 patches
    3. Resize edge patches minimally
    4. Run model per patch
    5. Aggregate: final_score = mean(patch_scores)
    6. Apply calibration
    7. NaN guard + clamp to [0, 1]
    
    Returns calibrated score between 0 and 1.
    """
    device = next(model.parameters()).device
    model.eval()

    # 1. Load image
    if isinstance(img_input, str):
        img = Image.open(img_input).convert("RGB")
    else:
        img = img_input.convert("RGB")

    w, h = img.size
    patch_size = 128

    # 2. Collect patches
    patches = []
    for y in range(0, h, patch_size):
        for x in range(0, w, patch_size):
            # Crop the patch
            right = min(x + patch_size, w)
            bottom = min(y + patch_size, h)
            patch = img.crop((x, y, right, bottom))

            pw, ph = patch.size

            # 3. Skip very small edge patches (< 32px in either dimension)
            if pw < 32 or ph < 32:
                continue

            # Resize edge patches to 128x128 if they're undersized
            if pw != patch_size or ph != patch_size:
                patch = patch.resize((patch_size, patch_size), Image.BILINEAR)

            patches.append(patch)

    # Fallback: if image is smaller than 128x128, resize the whole thing
    if len(patches) == 0:
        patches.append(img.resize((patch_size, patch_size), Image.BILINEAR))

    # 4. Run model per patch — use SAME transform as training
    transform = get_inference_transform()
    patch_scores = []

    with torch.no_grad():
        for patch in patches:
            img_tensor = transform(patch).unsqueeze(0).to(device)

            # NaN guard on input tensor
            if torch.isnan(img_tensor).any():
                img_tensor = torch.nan_to_num(img_tensor, nan=0.0)

            outputs = model(img_tensor)

            # NaN guard before softmax
            if torch.isnan(outputs).any():
                patch_scores.append(0.5)
                continue

            probs = F.softmax(outputs, dim=1)
            score = probs[0][1].item()

            # NaN guard after softmax
            if np.isnan(score) or np.isinf(score):
                score = 0.5

            # Clamp individual patch score
            score = max(0.0, min(1.0, score))
            patch_scores.append(score)

    # 5. Aggregate: weighted mean + max (Part 4)
    if len(patch_scores) == 0:
        final_score = 0.5
    else:
        avg_score = sum(patch_scores) / len(patch_scores)
        max_score = max(patch_scores)
        final_score = 0.7 * avg_score + 0.3 * max_score

    # 6. Score Stability: add minimal random noise for realism (Part 3)
    noise = np.random.normal(0, 0.005)
    final_score = final_score + noise

    # 7. Calibration: score = (score - 0.5) * 1.5 + 0.5 (Part 1)
    calibrated = (final_score - 0.5) * 1.5 + 0.5

    # 8. Final clamp and NaN safety (Part 5)
    calibrated = max(0.0, min(1.0, float(calibrated)))
    if np.isnan(calibrated) or np.isinf(calibrated):
        calibrated = 0.5

    return calibrated


if __name__ == "__main__":
    train_model()
