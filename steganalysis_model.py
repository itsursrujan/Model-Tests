import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class SRMConv2d(nn.Module):
    """
    A specialized Convolutional Layer that uses fixed SRM (Spatial Rich Models) kernels.
    This layer acts as a High-Pass Filter to suppress image content and reveal 
    steganographic noise residuals.
    """
    def __init__(self):
        super(SRMConv2d, self).__init__()
        self.channels = 3  # RGB
        
        # Define 3 basic high-pass filters (SRM kernels)
        # 1. KV Kernel (Residuals)
        k1 = np.array([[0, 0, 0, 0, 0],
                       [0, -1, 2, -1, 0],
                       [0, 2, -4, 2, 0],
                       [0, -1, 2, -1, 0],
                       [0, 0, 0, 0, 0]], dtype=np.float32)
        
        # 2. Edge Kernel
        k2 = np.array([[-1, 2, -2, 2, -1],
                       [2, -6, 8, -6, 2],
                       [-2, 8, -12, 8, -2],
                       [2, -6, 8, -6, 2],
                       [-1, 2, -2, 2, -1]], dtype=np.float32)
                       
        # 3. Square Kernel
        k3 = np.array([[0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0],
                       [0, 1, -2, 1, 0],
                       [0, -2, 4, -2, 0],
                       [0, 1, -2, 1, 0]], dtype=np.float32)

        # Normalize kernels
        k1 = k1 / 4.0
        k2 = k2 / 12.0
        k3 = k3 / 4.0
        
        # Stack them: (Out_Channels, In_Channels/Groups, H, W)
        # We want to apply each of the 3 filters to each of the 3 RGB channels independently.
        # So we'll have 9 output channels total (3 filters * 3 colors).
        
        filters = []
        for k in [k1, k2, k3]:
            # Replicate for RGB
            filters.append(k) 
            
        filters = np.array(filters) # Shape (3, 5, 5)
        
        # In PyTorch Conv2d: (out_channels, in_channels, kH, kW)
        # We want 3 output channels (one per filter type) per input channel.
        # Actually, simpler approach: Apply 1 filter to R, G, B separately.
        # Let's make 3 filters. We will apply them using group convolution.
        
        # Shape: (3, 1, 5, 5) -> 3 filters, each acts on 1 channel
        weight = torch.from_numpy(filters).unsqueeze(1).type(torch.FloatTensor)
        
        # We repeat this for RGB. 
        # Total weights: (9, 1, 5, 5). 
        # Groups = 3. Input = 3. Output = 9.
        # First 3 outputs = R filtered by k1, k2, k3
        # Next 3 outputs = G filtered by k1, k2, k3...
        
        self.weight = nn.Parameter(weight.repeat(3, 1, 1, 1), requires_grad=False)
        
    def forward(self, x):
        # x shape: (Batch, 3, H, W)
        # Output shape: (Batch, 9, H, W)
        # Groups=3 means:
        # Input Channel 0 (R) goes to Output Channels 0-2 (Filters k1,k2,k3)
        # Input Channel 1 (G) goes to Output Channels 3-5
        # Input Channel 2 (B) goes to Output Channels 6-8
        return F.conv2d(x, self.weight, padding=2, groups=3)

class StegoCNN(nn.Module):
    """
    A lightweight Deep Learning model for Steganalysis.
    Architecture:
    1. SRM High-Pass Filter (Fixed) -> Extracts noise
    2. Conv Block 1
    3. Conv Block 2
    4. Global Average Pooling
    5. Dense Classifier
    """
    def __init__(self):
        super(StegoCNN, self).__init__()
        
        # 1. Pre-processing: SRM Filter
        self.srm = SRMConv2d()
        
        # 2. Feature Extraction
        # Input: 9 channels (residuals). Output: 16 channels.
        self.conv1 = nn.Sequential(
            nn.Conv2d(9, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2) # Downsample
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.conv4 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)) # Global Average Pooling -> (Batch, 128, 1, 1)
        )
        
        # 3. Classification
        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, 2) # Output: [Clean_Score, Stego_Score]
        )
        
    def forward(self, x):
        # x: (Batch, 3, H, W)
        
        # 1. Extract Residuals (The "Secret Sauce")
        x = self.srm(x) # -> (Batch, 9, H, W)
        
        # 2. CNN Layers
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        
        # 3. Flatten
        x = x.view(x.size(0), -1) # -> (Batch, 128)
        
        # 4. Classify
        x = self.fc(x)
        
        return x

def get_model():
    return StegoCNN()
