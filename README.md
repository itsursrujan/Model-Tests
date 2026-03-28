# AI Steganalysis Model Tests

Hybrid steganography detection system (Signature + AI)

## Features
- **Image steganalysis (CNN + SRM)**: Detects statistical anomalies in images using a Convolutional Neural Network and Steganalytic Rich Model filters.
- **Patch-based inference (resolution independent)**: Splits larger images into 128x128 patches for detection, ensuring consistency across various resolutions.
- **Signature detection (LSB markers)**: Deterministic detection of common LSB steganographic markers.
- **Document detection (PDF, DOCX, TXT)**: Heuristic-based analysis to find hidden content in document formats.
- **Stable AI scoring (no NaN)**: Hardened scoring logic to prevent numerical instability and ensure reliable outputs.

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
