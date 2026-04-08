# System Architecture

The AI Steganalysis system is built with a defense-in-depth philosophy, combining multiple detection methods to maximize reliability.

## Multi-Layer Detection System

### 1. Signature Detection
- **Purpose**: Detects known steganographic markers and signatures in binary headers and pixel data.
- **Mechanism**: Scans for specific bit patterns and LSB markers that are common in standard steganography tools.
- **Reliability**: Deterministic and 100% accurate for the specific patterns it is programmed to recognize.

### 2. AI Steganalysis (CNN)
- **Purpose**: Detects statistical anomalies that signature-based systems miss.
- **Mechanism**: Uses a Convolutional Neural Network trained on SRM (Steganalytic Rich Model) noise residuals.
- **Strength**: Identifies "noise" introduced by embedding data even when the specific tool signature is unknown.
- **Explainability**: Heatmap Generation layer runs Grad-CAM sequentially on patches (with statistical noise suppression) to overlay predictive visualization on the original media.

### 3. Spam & Phishing Engine (SecureMessage)
- **Purpose**: Analyzes textual messages and embedded URLs for risk and phishing attempts.
- **Mechanism**: Leverages a TF-IDF vectorizer coupled with a Logistic Regression classifier, supported by an adaptive feedback loop.
- **Output**: Issues a 3-tier risk classification (High, Medium, Low) and writes detailed reason logs to MongoDB.

## Patch-Based Inference
To handle varying image sizes without loss of detail:
1. **Splitting**: The input image is divided into a grid of 128x128 patches.
2. **Analysis**: The model runs inference on each patch individually.
3. **Aggregation**: Patch scores are aggregated using a weighted average (`0.7 * mean + 0.3 * max`) to generate the final image score.

## Document Detection
The system extends beyond images into document analysis:
- **PDF**: Checks for suspicious object structures, embedded scripts, and hidden content between markers.
- **DOCX**: Analyzes the internal XML structure for anomalies or unexpected hidden folders.
- **TXT**: Uses entropy analysis and checks for hidden unicode characters (e.g., zero-width spaces or whitespace steganography).

## Final Verdict Logic
The final verdict for any file is decided by combining all system outputs:
- **Signature Detection triggers** → **STEGO** (Highest Confidence)
- **Aggregated AI Score > 0.75** → **Suspicious** (High Probability of stego)
- **Aggregated AI Score < 0.50** → **Clean** (No anomalies detected)
- **Else (0.50–0.75)** → **Moderate Risk** (Slight anomalies, manual review recommended)
