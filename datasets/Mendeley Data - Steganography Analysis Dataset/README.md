# Steganography Dataset - Train/Test/Validation Split

## Dataset Information

- **Total Images**: 2835
- **Train Set**: 1984 images (70.0%)
- **Test Set**: 425 images (15.0%)
- **Validation Set**: 426 images (15.0%)

## Methods
- BPCS
- LSB
- PVD

## Directory Structure
```
DATASET_SPLIT/
├── train/
│   ├── BPCS/
│   ├── LSB/
│   └── PVD/
├── test/
│   ├── BPCS/
│   ├── LSB/
│   └── PVD/
└── validation/
    ├── BPCS/
    ├── LSB/
    └── PVD/
```

## Split Details

### Train Set
- BPCS: 672 files
- LSB: 672 files
- PVD: 640 files

### Test Set
- BPCS: 144 files
- LSB: 144 files
- PVD: 137 files

### Validation Set
- BPCS: 144 files
- LSB: 144 files
- PVD: 138 files

## Configuration
- **Train Ratio**: 70%
- **Test Ratio**: 15%
- **Validation Ratio**: 15%
- **Random Seed**: 42
- **Preserve Structure**: True

## Usage

### PyTorch
```python
from torchvision import datasets, transforms

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

train_dataset = datasets.ImageFolder('DATASET_SPLIT/train', transform=transform)
test_dataset = datasets.ImageFolder('DATASET_SPLIT/test', transform=transform)
val_dataset = datasets.ImageFolder('DATASET_SPLIT/validation', transform=transform)
```

### TensorFlow/Keras
```python
from tensorflow.keras.preprocessing.image import ImageDataGenerator

datagen = ImageDataGenerator(rescale=1./255)

train_generator = datagen.flow_from_directory(
    'DATASET_SPLIT/train',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

test_generator = datagen.flow_from_directory(
    'DATASET_SPLIT/test',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

val_generator = datagen.flow_from_directory(
    'DATASET_SPLIT/validation',
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)
```
