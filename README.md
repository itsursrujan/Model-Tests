# AI Steganalysis Model Tests

Hybrid steganography detection system (Signature + AI)

## Features
- **Image steganalysis (CNN + SRM)**: Detects statistical anomalies in images using a Convolutional Neural Network and Steganalytic Rich Model filters.
- **DeepStegAI Heatmap Visualization**: Generates interpretable Grad-CAM and difference heatmaps with statistical noise suppression to highlight manipulated regions.
- **AI Spam & Phishing Detection**: Multi-layer Logistic Regression + TF-IDF engine with lookalike domain checking, explainability reasoning, and 3-tier risk classification.
- **Patch-based inference (resolution independent)**: Splits larger images into 128x128 patches for detection, ensuring consistency across various resolutions.
- **Signature & Document detection**: Deterministic detection of common LSB steganographic markers and heuristic-based analysis for PDF, DOCX, and TXT files.
- **Robust Architecture**: Cluster-ready batch processing with Redis, adaptive feedback loops for the spam model, and stable AI scoring logic.

## How to Run

### Backend
1. Ensure the virtual environment is activated.
2. Install dependencies (if not done): `pip install -r requirements.txt`
3. Start the server:
   ```bash
   python run.py
   ```

### Frontend
1. Navigate to the `frontend` directory.
2. Install dependencies (if not done): `npm install`
3. Start the development server:
   ```bash
   npm run dev
   ```

## Folder Structure Overview
- `run.py`: Main backend entry point.
- `detection_engine.py`: Core logic for Image and Document analysis.
- `steganalysis_model.py`: Model architecture definition (StegoCNN).
- `document_detector.py`: Heuristics for PDF, DOCX, and TXT analysis.
- `frontend/`: React components and UI code.
- `datasets/`: (Excluded from repository) Source training data.

## Model File
The trained model weights are stored in:
`stego_model.pth`
