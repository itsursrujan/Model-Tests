# Known Limitations

We maintain full transparency regarding the system's capabilities and current constraints to ensure informed usage.

## AI Score Limitations
- **Uncertainty**: Scores hovering near 0.50 are inherently uncertain and may indicate a file that the model cannot confidently classify.
- **False Positives**: High-ISO photos (very noisy "clean" images) can occasionally trip the "Moderate Risk" threshold because the system perceives the natural sensor noise as potentially artificial steganographic noise.

## Dataset Limitations
- **Algorithm Bias**: The model is extensively trained on LSB-based steganography (LSB, BPCS, PVD).
- **Advanced Methods**: It has limited exposure to highly advanced steganographic methods like **S-UNIWARD** or **HILL**, which are designed to minimize statistical noise and may bypass the current CNN filters.

## Document Detection
- **Heuristic-based**: Unlike the image system, document detection uses rule-based heuristics rather than a deep learning model.
- **Conservative Results**: If a document is large and complex, the heuristics may produce a 50% "Moderate Risk" fallback value if no overt signatures or anomalies are found, reflecting uncertainty rather than a clean bill of health.

## Model Constraints
- **Lightweight Architecture**: The model is optimized for low-mid GPU systems (4-layer CNN). While very fast, it is not as computationally deep as research-grade models like **SRNet**.
- **Memory**: Extremely high-resolution images (8K+) may consume significant RAM during patch-based processing if batching is not handled properly.

## Spam Engine Limitations
- **Semantic Obfuscation**: The TF-IDF + Logistic Regression model is robust against standard textual spam and phishing links, but may struggle against highly personalized spear-phishing or AI-generated semantic obfuscation compared to deep LLM approaches.

## Future Improvements
To move toward production-grade forensics:
- **Expand SRM kernels**: Adding more high-order filter banks to capture subtler statistical footprints.
- **ALASKA2 Dataset**: Retraining on the competition-grade ALASKA2 dataset for better generalization against high-end stego masking.
- **Document AI**: Developing a dedicated NLP-transformer or structure-aware model for document steganography instead of relying solely on heuristics.
