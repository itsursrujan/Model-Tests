# Dataset Report

Detailed information about the datasets used for training and testing the AI Steganalysis system.

## Dataset Sources

### 1. stegoimagesdataset (Kaggle)
- **Total size**: ~44,000 images.
- **Usage**: A balanced subset was selected for training to ensure model diversity without overfitting.

### 2. Mendeley Steganography Dataset
- Focused on specific steganographic algorithms.
- **Included categories**:
  - CLEAN (Original images)
  - LSB (Least Significant Bit substitution)
  - BPCS (Bit-Plane Complexity Segmentation)
  - PVD (Pixel Value Differencing)

### 3. Custom Dataset
- **Contents**: 506 files total, split into `clean` and `stego` classes.
- **Stego Folder**: Highly consistent, containing exactly 249 steganographic `.png` images.
- **Clean Folder**: Contains a mixture of 164 images (`.png`, `.jpg`, `.jpeg`) alongside 93 document and code files (`.docx`, `.pdf`, `.txt`, `.py`).
- **Data Quality Note**: Exhibits class imbalance for image classification (249 stego vs 164 clean) and the presence of non-image files in the `clean` class requires filtering before ingestion by image processing pipelines.

## Final Training Dataset Configuration
- **Total**: 16,000 images
- **Clean samples**: 8,000
- **Stego samples**: 8,000
- **Split**: 80% training / 20% validation

## Preprocessing
- **Resize**: Images were resized to 128x128 for uniform input.
- **Normalization**: Pixel values normalized with `mean=0.5` and `std=0.5`.
- **Conversion**: All images were converted to RGB to maintain a consistent 3-channel input for the CNN.

## Augmentation
To improve model robustness, the following augmentations were applied during training:
- **Horizontal Flipping**: Randomly flips images horizontally.
- **90° Rotations**: Randomly rotates images to ensure the model is invariant to orientation.
- **Color Jitter (Optional)**: Subtle brightness/contrast adjustments to simulate varying camera sensors.
