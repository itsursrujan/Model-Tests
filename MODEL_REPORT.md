# AI Steganalysis Model Report

Comprehensive details about the AI model powering the detection system.

## Model Type
- **SRM + CNN (4-layer architecture)**: The model utilizes Steganalytic Rich Model (SRM) filters to capture noise residuals, followed by a 4-layer Convolutional Neural Network for classification.

## Input
- **128x128 patches**: Images are processed in 128x128 blocks. This patch-based approach allows the model to handle images of any resolution efficiently and avoids resizing artifacts that could obscure steganographic signals.

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
