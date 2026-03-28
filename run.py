import os
import io
import torch
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from werkzeug.utils import secure_filename

# Import existing model and detection logic
from steganalysis_model import StegoCNN
from train_stego_model import predict_image
from detection_engine import scan_image_for_signature
from document_detector import detect_steganography

app = Flask(__name__)
CORS(app)

# --- Initialize CNN Model ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = StegoCNN().to(device)

# Load ONLY stego_model.pth (strict — no best/duplicate)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stego_model.pth")
if os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        print(f"[*] Loaded model weights from {MODEL_PATH}")
    except Exception as e:
        print(f"[!] Error loading model: {e}")
else:
    print(f"[!] Warning: stego_model.pth not found. Running with uninitialized weights.")

model.eval()

# Allowed file extensions
IMAGE_EXT = ('.png', '.jpg', '.jpeg')
DOC_EXT   = ('.pdf', '.docx', '.txt')
ALL_EXT   = IMAGE_EXT + DOC_EXT

def allowed_file(filename: str) -> bool:
    """Check that the extension is in our allowed set."""
    _, ext = os.path.splitext(filename.lower())
    return ext in ALL_EXT


def safe_float(value, default=0.0):
    """Ensure a value is a valid finite float. Never return NaN or Inf."""
    try:
        f = float(value)
        if np.isnan(f) or np.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Get file from request
    file = request.files.get('file') or request.files.get('image')

    if not file or not file.filename:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        _, ext = os.path.splitext(filename.lower())
        return jsonify({"error": f"Unsupported file type: {ext}. Allowed: png, jpg, jpeg, pdf, docx, txt"}), 400

    _, ext = os.path.splitext(filename.lower())

    try:
        # ------------------------------------------------------------------
        # CASE A: IMAGE STEGANALYSIS (CNN + Signature)
        # ------------------------------------------------------------------
        if ext in IMAGE_EXT:
            img_bytes = file.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # 1. Signature Detection (Digital Watermark / LSB marker)
            sig_result = scan_image_for_signature(img)
            signature_detected = sig_result.get("detected", False)

            # 2. AI CNN Analysis (patch-based, calibrated score)
            ai_score = predict_image(model, img)

            # NaN safety — NEVER return NaN
            ai_score = safe_float(ai_score, 0.5)

            # 3. Deterministic Verdict Logic (NO overlapping conditions)
            #    Priority: signature > high score > low score > moderate
            if signature_detected:
                verdict = "STEGO"
                ai_score = 1.0  # Override to full confidence on signature
            elif ai_score > 0.75:
                verdict = "Suspicious"
            elif ai_score < 0.50:
                verdict = "Clean"
            else:
                verdict = "Moderate Risk"

            return jsonify({
                "type": "image",
                "signature_detected": signature_detected,
                "ai_score": ai_score,
                "verdict": verdict,
                "details": sig_result.get("message", "No metadata signature found")
            })

        # ------------------------------------------------------------------
        # CASE B: DOCUMENT / TEXT STEGANALYSIS (Heuristics)
        # ------------------------------------------------------------------
        elif ext in DOC_EXT:
            # Save temporarily for document-reading libraries
            temp_dir = os.environ.get('TEMP', '.') if os.name == 'nt' else '/tmp'
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)

            try:
                result = detect_steganography(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            is_suspicious = result.get("suspicious", False)
            conf_score = safe_float(result.get("confidence_score", 0.0), 0.0)

            # Document verdict (matching image thresholds)
            if is_suspicious and conf_score >= 0.75:
                verdict = "Suspicious"
            elif is_suspicious and conf_score >= 0.50:
                verdict = "Moderate Risk"
            elif is_suspicious:
                 verdict = "Moderate Risk" # Fallback for any suspicious marker
            else:
                verdict = "Clean"

            return jsonify({
                "type": "document",
                "verdict": verdict,
                "ai_score": conf_score,           # Map to ai_score for UI consistency
                "confidence_level": result.get("confidence", "low"),
                "indicators": result.get("detailed_findings", []),
                "reason": result.get("reason", "No issues found"),
                "stats": result.get("stats", {}),
                "file_type": ext.upper()[1:]
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("[*] Starting Dual-Detection Backend on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
