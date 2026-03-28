import os
import torch
import torch.nn.functional as F
from PIL import Image
import io
import re
import cv2
import numpy as np
from PyPDF2 import PdfReader
from docx import Document
from steganalysis_model import StegoCNN
import torchvision.transforms as transforms
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Global Model Configuration
# ---------------------------------------------------------------------------

# Use stego_model.pth only (no _best suffix)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stego_model.pth")
IMAGE_SIZE = (128, 128)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# STANDARDIZED NORMALIZATION — must match train_stego_model.py exactly
NORMALIZE = transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])

_model_instance = None

def get_stego_model() -> Any:
    global _model_instance
    if _model_instance is None:
        _model_instance = StegoCNN().to(DEVICE)
        if os.path.exists(MODEL_PATH):
            try:
                state_dict = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
                _model_instance.load_state_dict(state_dict)
                _model_instance.eval()
                print(f"  [DocDetector] Loaded model from {MODEL_PATH}")
            except Exception as e:
                print(f"  [Warning] Could not load stego model: {e}")
    return _model_instance


# ---------------------------------------------------------------------------
# Image Analysis Helpers
# ---------------------------------------------------------------------------

def perform_opencv_precheck(image_bytes: bytes) -> float:
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return 0.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        l_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        if hist.sum() == 0:
            return 0.0
        hist /= hist.sum()
        p = hist[hist > 0]
        entropy = -float(np.sum(p * np.log2(p + 1e-10)))
        score = 0.0
        if entropy > 7.7:
            score += 0.3
        if l_var > 1000:
            score += 0.2
        return float(score)
    except Exception:
        return 0.0


def analyze_asset_bytes(image_bytes: bytes) -> float:
    """Analyze embedded image bytes for stego indicators. Uses same normalization as training."""
    try:
        model = get_stego_model()
        if model is None:
            return 0.5
        img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # MUST use same transform as training pipeline
        img_tensor = transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
            NORMALIZE,
        ])(img_pil).unsqueeze(0).to(DEVICE)

        # PART 5: NaN SAFETY (INPUT)
        if torch.isnan(img_tensor).any():
            img_tensor = torch.nan_to_num(img_tensor, nan=0.0)

        with torch.no_grad():
            outputs = model(img_tensor)

            # PART 5: NaN SAFETY (OUTPUT)
            if torch.isnan(outputs).any():
                return 0.5

            raw_prob = float(F.softmax(outputs, dim=1)[0][1].item())

        # PART 5: NaN SAFETY (PROB)
        if np.isnan(raw_prob) or np.isinf(raw_prob):
            raw_prob = 0.5

        # PART 1: FINAL SCORE CALIBRATION (matching train_stego_model.py: factor = 1.5)
        calibrated = (raw_prob - 0.5) * 1.5 + 0.5
        calibrated = max(0.0, min(1.0, float(calibrated)))

        # Final NaN check before aggregation
        if np.isnan(calibrated) or np.isinf(calibrated):
            calibrated = 0.5

        # Perform OpenCV forensic precheck
        cv_score = perform_opencv_precheck(image_bytes)
        
        # Aggregate logic (70% AI, 30% CV Forensics)
        return (calibrated * 0.7) + (cv_score * 0.3)
    except Exception:
        return 0.5  # Neutral fallback on error


# ---------------------------------------------------------------------------
# Text Stego Detection
# ---------------------------------------------------------------------------

def scan_text_for_stego(text: str) -> List[str]:
    """Detect hidden characters and whitespace-based steganography in text."""
    findings = []

    # Zero-width / invisible Unicode chars
    zero_width = re.findall(r'[\u200b-\u200d\u200e\u200f\uFEFF\u2060\u2061\u2062\u2063]', text)
    if len(zero_width) > 3:
        findings.append(f"Found {len(zero_width)} hidden zero-width characters.")

    # Trailing whitespace pattern
    lines = text.split('\n')
    trailing = [l for l in lines if l.endswith((' ', '\t')) and len(l) > 12]
    if len(trailing) > 5:
        findings.append(f"Suspicious trailing whitespace on {len(trailing)} lines.")

    # Homoglyph-like unicode substitutions (lookalike characters)
    homoglyphs = re.findall(r'[\u0430\u0435\u043e\u0440\u0441\u0445\u04bb]', text)
    if len(homoglyphs) > 2:
        findings.append(f"Found {len(homoglyphs)} potential homoglyph characters.")

    return findings


# ---------------------------------------------------------------------------
# TXT File Detection
# ---------------------------------------------------------------------------

def scan_txt_file(file_path: str) -> List[str]:
    """
    Detect abnormal binary patterns, non-printable characters,
    zero-width unicode, and abnormal whitespace entropy in .txt files.
    """
    findings = []

    try:
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()
    except Exception as e:
        return [f"Could not read file: {e}"]

    total_bytes = len(raw_bytes)
    if total_bytes == 0:
        return findings

    # 1. Detect null bytes (binary embedding indicator)
    null_count = raw_bytes.count(b'\x00')
    null_ratio = null_count / total_bytes
    if null_ratio > 0.01:
        findings.append(f"Abnormal binary content: {null_count} null bytes ({null_ratio:.1%} of file).")

    # 2. Detect high proportion of non-printable, non-whitespace bytes
    non_printable = sum(1 for b in raw_bytes if b < 0x20 and b not in (0x09, 0x0A, 0x0D))
    np_ratio = non_printable / total_bytes
    if np_ratio > 0.05:
        findings.append(f"High non-printable byte ratio: {non_printable} bytes ({np_ratio:.1%}).")

    # 3. Decode as text and look for hidden character patterns
    try:
        text = raw_bytes.decode('utf-8', errors='replace')
    except Exception:
        text = ""

    text_findings = scan_text_for_stego(text)
    findings.extend(text_findings)

    # 4. Whitespace entropy analysis
    lines = text.split('\n')
    very_long_trailing = [l for l in lines if len(l) > 0 and (len(l) - len(l.rstrip())) > 20]
    if len(very_long_trailing) > 2:
        findings.append(f"Detected {len(very_long_trailing)} lines with excessive trailing whitespace (>20 spaces).")

    # 5. Check for repeated byte sequences that suggest encoding
    chunk_size = 16
    chunks = [raw_bytes[i:i+chunk_size] for i in range(0, total_bytes - chunk_size, chunk_size)]
    unique_chunks = len(set(chunks))
    if len(chunks) > 100 and unique_chunks / len(chunks) < 0.3:
        findings.append("Low entropy: repetitive byte patterns may indicate encoded data.")

    return findings


# ---------------------------------------------------------------------------
# Confidence Level Conversion
# ---------------------------------------------------------------------------

def score_to_confidence_label(conf: float) -> str:
    """Convert numeric confidence to low/medium/high label."""
    if conf < 0.4:
        return "low"
    elif conf < 0.7:
        return "medium"
    else:
        return "high"


# ---------------------------------------------------------------------------
# Main Detection Entry Point
# ---------------------------------------------------------------------------

def detect_steganography(file_path: str) -> Dict[str, Any]:
    detailed_findings: List[str] = []
    stats: Dict[str, Any] = {
        "images_scanned": 0,
        "stego_images_found": 0,
        "diagrams_found": 0
    }

    try:
        ext = file_path.lower()
        if ext.endswith(".pdf"):
            _scan_pdf(file_path, detailed_findings, stats)
        elif ext.endswith(".docx"):
            _scan_docx(file_path, detailed_findings, stats)
        elif ext.endswith(".txt"):
            txt_findings = scan_txt_file(file_path)
            detailed_findings.extend(txt_findings)
        else:
            return {
                "suspicious": False,
                "confidence": 0.0,
                "confidence_level": "low",
                "reason": "Unsupported format",
                "detailed_findings": [],
                "stats": stats
            }
    except Exception as e:
        return {
            "suspicious": True,
            "confidence": 0.1,
            "confidence_level": "low",
            "reason": f"Scan error: {str(e)}",
            "detailed_findings": [],
            "stats": stats
        }

    # Calculate confidence score and label
    conf = 0.0
    if detailed_findings:
        is_suspicious = True
        # Base confidence on number of markers and stego image results
        conf = 0.4 + (len(detailed_findings) * 0.1)
        if stats.get("stego_images_found", 0) > 0:
            conf = max(conf, 0.8)
        conf = min(conf, 1.0)
    else:
        is_suspicious = False
        conf = 0.1

    conf_label = score_to_confidence_label(conf)

    # PART 6: RETURN STRUCTURED RESULT
    return {
        "suspicious": is_suspicious,
        "confidence": conf_label,          # Needs to be "low" | "medium" | "high" per spec
        "confidence_score": float(conf),   # Keeping numeric score for internal or optional use
        "reason": detailed_findings[0] if detailed_findings else "Clean - No anomalies detected",
        "detailed_findings": detailed_findings,
        "stats": stats
    }


# ---------------------------------------------------------------------------
# PDF Scanner
# ---------------------------------------------------------------------------

def _scan_pdf(file_path, detailed_findings, stats):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

        # Check for empty/hidden content pages
        if not page_text or len(page_text.strip()) == 0:
            detailed_findings.append("PDF page with no extractable text detected (possible hidden content).")

        if "/Resources" in page:
            res = page["/Resources"].get_object()
            if "/XObject" in res:
                x_objects = res["/XObject"].get_object()
                for obj_name in x_objects:
                    obj = x_objects[obj_name].get_object()
                    if obj.get("/Subtype") == "/Image":
                        stats["images_scanned"] += 1
                        try:
                            score = analyze_asset_bytes(obj._data)
                            if score > 0.6:
                                stats["stego_images_found"] += 1
                                detailed_findings.append("Hybrid Engine Alert: Noise residuals detected in PDF asset.")
                        except Exception:
                            pass

    text_findings = scan_text_for_stego(text)
    detailed_findings.extend(text_findings)


# ---------------------------------------------------------------------------
# DOCX Scanner
# ---------------------------------------------------------------------------

def _scan_docx(file_path, detailed_findings, stats):
    doc = Document(file_path)

    # Extract paragraphs and detect abnormal structure
    paragraphs = [p.text for p in doc.paragraphs]
    text = "\n".join(paragraphs)

    # Detect abnormal paragraph structure
    empty_paragraphs = sum(1 for p in paragraphs if len(p.strip()) == 0)
    if len(paragraphs) > 10 and empty_paragraphs / len(paragraphs) > 0.5:
        detailed_findings.append(f"Abnormal document structure: {empty_paragraphs}/{len(paragraphs)} empty paragraphs.")

    # Scan embedded images
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref.lower() or "media" in rel.target_ref.lower():
            stats["images_scanned"] += 1
            try:
                score = analyze_asset_bytes(rel.target_part.blob)
                if score > 0.6:
                    stats["stego_images_found"] += 1
                    detailed_findings.append("Hybrid Engine Alert: Encoded data signatures found in DOCX media.")
            except Exception:
                pass

    text_findings = scan_text_for_stego(text)
    detailed_findings.extend(text_findings)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(detect_steganography(sys.argv[1]))