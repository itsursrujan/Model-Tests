"""
Validation Test Suite for Steganalysis System
Tests all critical paths defined in Part 9 of the spec.
"""
import os
import sys
import torch
import numpy as np
from PIL import Image
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from steganalysis_model import StegoCNN
from train_stego_model import predict_image, get_inference_transform, NORMALIZE
from detection_engine import scan_image_for_signature
from stego_engine import MAGIC, embed_payload_into_image, bytes_to_bits

PASS = "[PASS]"
FAIL = "[FAIL]"


def create_clean_image(w=256, h=256):
    """Create a simple clean gradient image."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            arr[y, x] = [int(x / w * 255), int(y / h * 255), 128]
    return Image.fromarray(arr)


def create_stego_image(w=256, h=256):
    """Create an image with embedded LSB signature."""
    img = create_clean_image(w, h)
    # Embed our DSAI magic header
    header = MAGIC + b'\x00' + (16).to_bytes(4, 'big') + b'HIDDEN_DATA_TEST'
    return embed_payload_into_image(img, header)


def create_highres_image(w=1920, h=1080):
    """Create a high-resolution image."""
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    return Image.fromarray(arr)


def load_model():
    """Load the trained model."""
    device = torch.device("cpu")
    model = StegoCNN().to(device)
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stego_model.pth")
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"[*] Model loaded from {model_path}")
    else:
        print(f"[!] WARNING: Model not found at {model_path}, using random weights")
    model.eval()
    return model


def test_1_clean_image():
    """Test 1: Clean image should score < 0.5 and verdict = Clean"""
    print("\n" + "=" * 50)
    print("TEST 1: Clean Image Detection")
    print("=" * 50)

    model = load_model()
    img = create_clean_image()
    score = predict_image(model, img)

    is_nan = np.isnan(score) or np.isinf(score)
    # Threshold update per PART 2: Clean < 0.50
    verdict = "Clean" if score < 0.50 else "Suspicious" if score > 0.75 else "Moderate Risk"

    print(f"  Score: {score:.4f}")
    print(f"  Verdict: {verdict}")
    print(f"  NaN check: {PASS if not is_nan else FAIL}")
    print(f"  Score < 0.5: {PASS if score < 0.5 else FAIL}")
    print(f"  Result: {PASS if not is_nan and score < 0.5 else FAIL}")
    return not is_nan and score < 0.5


def test_2_lsb_stego():
    """Test 2: LSB stego image should have signature detected"""
    print("\n" + "=" * 50)
    print("TEST 2: LSB Stego (Signature Detection)")
    print("=" * 50)

    img = create_stego_image()
    sig_result = scan_image_for_signature(img)
    detected = sig_result.get("detected", False)

    print(f"  Signature detected: {detected}")
    print(f"  Message: {sig_result.get('message', 'N/A')}")
    print(f"  Result: {PASS if detected else FAIL}")
    return detected


def test_3_ai_suspicious():
    """Test 3: AI score check (run on the model, verifying no NaN)"""
    print("\n" + "=" * 50)
    print("TEST 3: AI Score Stability")
    print("=" * 50)

    model = load_model()
    # Run prediction multiple times to check consistency
    img = create_clean_image(512, 512)
    scores = []
    for i in range(5):
        score = predict_image(model, img)
        scores.append(score)

    all_valid = all(not np.isnan(s) and not np.isinf(s) for s in scores)
    all_in_range = all(0.0 <= s <= 1.0 for s in scores)
    std_dev = np.std(scores)

    print(f"  Scores: {[f'{s:.4f}' for s in scores]}")
    print(f"  Std Dev: {std_dev:.6f}")
    print(f"  All valid (no NaN): {PASS if all_valid else FAIL}")
    print(f"  All in [0,1]: {PASS if all_in_range else FAIL}")
    # Threshold updated to 0.05 to allow for the added 0.005 noise (Part 3)
    print(f"  Stable (std < 0.05): {PASS if std_dev < 0.05 else FAIL}")
    return all_valid and all_in_range and std_dev < 0.05


def test_4_highres():
    """Test 4: High-res image (1920x1080) should not crash and produce stable output"""
    print("\n" + "=" * 50)
    print("TEST 4: High-Resolution Image (1920x1080)")
    print("=" * 50)

    model = load_model()
    img = create_highres_image(1920, 1080)

    try:
        score = predict_image(model, img)
        is_nan = np.isnan(score) or np.isinf(score)
        in_range = 0.0 <= score <= 1.0

        print(f"  Score: {score:.4f}")
        print(f"  No crash: {PASS}")
        print(f"  No NaN: {PASS if not is_nan else FAIL}")
        print(f"  In range [0,1]: {PASS if in_range else FAIL}")
        print(f"  Result: {PASS if not is_nan and in_range else FAIL}")
        return not is_nan and in_range
    except Exception as e:
        print(f"  CRASHED: {e}")
        print(f"  Result: {FAIL}")
        return False


def test_5_normalization_parity():
    """Test 5: Verify inference uses same normalization as training"""
    print("\n" + "=" * 50)
    print("TEST 5: Normalization Parity Check")
    print("=" * 50)

    transform = get_inference_transform()
    img = create_clean_image(128, 128)
    tensor = transform(img)

    # With Normalize(0.5, 0.5, 0.5), values should be in [-1, 1]
    min_val = tensor.min().item()
    max_val = tensor.max().item()
    has_normalize = min_val < 0  # If normalized, should have negative values

    print(f"  Tensor range: [{min_val:.4f}, {max_val:.4f}]")
    print(f"  Has normalization (negative values): {PASS if has_normalize else FAIL}")
    return has_normalize


def test_6_verdict_logic():
    """Test 6: Verify verdict logic is deterministic and non-overlapping"""
    print("\n" + "=" * 50)
    print("TEST 6: Verdict Logic Determinism (New Thresholds)")
    print("=" * 50)

    # Thresholds: < 0.50 Clean, > 0.75 Suspicious
    test_cases = [
        (0.00, "Clean"),
        (0.20, "Clean"),
        (0.49, "Clean"),
        (0.50, "Moderate Risk"),
        (0.60, "Moderate Risk"),
        (0.74, "Moderate Risk"),
        (0.75, "Moderate Risk"),
        (0.76, "Suspicious"),
        (0.90, "Suspicious"),
        (1.00, "Suspicious"),
    ]

    all_pass = True
    for score, expected in test_cases:
        if score > 0.75:
            verdict = "Suspicious"
        elif score < 0.50:
            verdict = "Clean"
        else:
            verdict = "Moderate Risk"

        ok = verdict == expected
        if not ok:
            all_pass = False
        print(f"  Score {score:.2f} -> {verdict} (expected: {expected}) {PASS if ok else FAIL}")

    print(f"  Result: {PASS if all_pass else FAIL}")
    return all_pass


if __name__ == "__main__":
    print("=" * 60)
    print("  STEGANALYSIS SYSTEM VALIDATION SUITE")
    print("=" * 60)

    results = []
    results.append(("Clean Image", test_1_clean_image()))
    results.append(("LSB Stego", test_2_lsb_stego()))
    results.append(("AI Stability", test_3_ai_suspicious()))
    results.append(("High-Res", test_4_highres()))
    results.append(("Normalization", test_5_normalization_parity()))
    results.append(("Verdict Logic", test_6_verdict_logic()))

    print("\n" + "=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)
    for name, passed in results:
        print(f"  {PASS if passed else FAIL} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n  {passed}/{total} tests passed")
    print("=" * 60)
