# AI Steganalysis Model Report

Comprehensive details about the AI model powering the detection system.

## Model Types
### 1. Image Steganalysis
- **SRM + CNN (4-layer architecture)**: The model utilizes Steganalytic Rich Model (SRM) filters to capture noise residuals, followed by a 4-layer Convolutional Neural Network for classification.
- **Explainable AI (Heatmaps)**: Leverages Grad-CAM and Difference heatmaps with statistical noise suppression and thresholding to visually highlight manipulated regions inside images.

### 2. Textual Spam & Phishing Detection
- **Logistic Regression + TF-IDF**: A multi-layer architecture combining term frequency-inverse document frequency encoding for text classification, integrated with heuristic and deterministic domain reputation/URL checks (Phishing detection).

## Input
- **Image Pipeline**: 128x128 patches. Images are processed in 128x128 blocks to efficiently handle any resolution dynamically without downscaling and losing critical stego noise.
- **Text Pipeline**: Raw text content (e.g., up to 33MB of batch parsed data) mapped to unified semantic tokens.

## Training Details
- **Epochs**: 10
- **Batch Size**: 16
- **Optimizer**: Adam
- **Learning Rate**: 0.0003

## Dataset Used
- **stegoimagesdataset**: Provides a large variety of clean and stego images.
- **Mendeley dataset**: Provides specific steganographic techniques like LSB, BPCS, and PVD.

## Training Size
- **Clean**: 8,000 images
- **Stego**: 8,000 images
- **Total**: ~16,000 images

## Accuracy (Realistic Estimate)
- **Training Accuracy**: ~0.80–0.85
- **Practical Accuracy**: ~0.70–0.80 (on real-world, unseen data)

## AI Score Behavior
The model outputs a probability score from 0.0 to 1.0. Typical behaviors observed:
- **Clean**: 0.30–0.50
- **Stego**: 0.65–0.90
- **Moderate Zone**: 0.50–0.75 (requires careful manual review)

## Calibration
To improve decision-making, the raw scores are calibrated using:
`calibrated_score = (raw_score - 0.5) * 1.5 + 0.5`
- This ensures that 0.5 is the neutral point and increases the separation between clean and stego predictions.

## Aggregation
For patch-based inference, the final score for an image is calculated as:
`final_score = 0.7 * mean(patch_scores) + 0.3 * max(patch_scores)`
- This weighting emphasizes local high-confidence detections while maintaining an overview of the global image statistics.
