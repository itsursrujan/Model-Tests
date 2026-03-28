import numpy as np
from PIL import Image
from typing import Tuple

# This is our unique signature. It helps us identify if an image was processed by our tool.
# DSAI stands for DeepStegAI.
MAGIC = b"DSAI"

# The header layout is:
# 4 bytes (MAGIC) + 1 byte (Mode ID) + 4 bytes (Payload Length) = 9 bytes total
HEADER_LEN = 4 + 1 + 4 

def bytes_to_bits(b: bytes) -> np.ndarray:
    """
    Converts a byte string into a numpy array of bits (0s and 1s).
    Example: b'A' (65) -> [0 1 0 0 0 0 0 1]
    """
    return np.unpackbits(np.frombuffer(b, dtype=np.uint8))

def bits_to_bytes(bits: np.ndarray, nbytes: int = None) -> bytes:
    """
    Reconstructs bytes from a stream of bits.
    We pad with zeros if the bit count isn't a multiple of 8.
    """
    if bits.size % 8 != 0:
        pad = 8 - (bits.size % 8)
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    out = np.packbits(bits).tobytes()
    return out if nbytes is None else out[:nbytes]

def image_capacity_bits(img: Image.Image) -> int:
    """
    Calculates how much data we can hide in the image.
    Since we hide 1 bit per color channel (R, G, B) of every pixel:
    Capacity = Width * Height * 3 bits.
    """
    w, h = img.size
    return 3 * w * h

def embed_payload_into_image(cover_img: Image.Image, payload_bytes: bytes) -> Image.Image:
    """
    The core logic for hiding data.
    """
    arr = np.array(cover_img.convert("RGB"))
    flat = arr.flatten()
    bits = bytes_to_bits(payload_bytes).astype(np.uint8)
    
    if len(bits) > len(flat):
        raise ValueError(f"Data is too large for this image. Try a larger image or smaller file.")
    
    mask = np.uint8(0xFE)
    flat_head = flat[:len(bits)]
    flat[:len(bits)] = (flat_head & mask) | bits
    out = flat.reshape(arr.shape)
    return Image.fromarray(out)


def extract_payload_from_image(stego_img: Image.Image) -> Tuple[int, bytes, bytes]:
    """
    Recovers the hidden data from an image.
    Returns: (mode_id, payload_bytes, signature_bytes)
    """
    arr = np.array(stego_img.convert("RGB"))
    flat = arr.flatten()
    
    # First, let's extract the header bits
    need_bits = HEADER_LEN * 8
    header_bits = (flat[:need_bits] & 1).astype(np.uint8)
    header_bytes = bits_to_bytes(header_bits)
    
    # Check if our signature is present
    if len(header_bytes) < HEADER_LEN or not header_bytes.startswith(MAGIC):
        raise ValueError("This image doesn't contain a valid DeepStegAI header.")
    
    # Parse the header
    mode_id = header_bytes[4] 
    payload_len = int.from_bytes(header_bytes[5:9], "big")
    
    # Calculate total bits needed including the payload
    total_bits = (HEADER_LEN + payload_len) * 8
    if total_bits > len(flat):
        raise ValueError("Header says payload is larger than the image itself. File might be corrupted.")
    
    # Extract the full payload bits
    payload_bits = (flat[:total_bits] & 1).astype(np.uint8)
    
    # Convert back to bytes
    if payload_bits.size % 8 != 0:
        pad = 8 - (payload_bits.size % 8)
        payload_bits = np.concatenate([payload_bits, np.zeros(pad, dtype=np.uint8)])
    payload_bytes = bits_to_bytes(payload_bits)
    
    # Remove the header
    data_block = payload_bytes[HEADER_LEN:HEADER_LEN+payload_len]
    
    signature = None
    
    # Check for Signed Modes (Bit 1 set)
    # Mode 0: Plain
    # Mode 1: Encrypted
    # Mode 2: Plain + Signed
    # Mode 3: Encrypted + Signed
    
    if mode_id & 2: # logic for signed
        # Structure: [SigLen 4 bytes] [Signature] [Data]
        if len(data_block) < 4:
            raise ValueError("Payload too short for signature header.")
            
        sig_len = int.from_bytes(data_block[:4], 'big')
        if len(data_block) < 4 + sig_len:
             raise ValueError("Payload too short for signature body.")
             
        signature = data_block[4 : 4+sig_len]
        data_block = data_block[4+sig_len :]
        
        # Mask out the signed bit so downstream logic sees 0 or 1
        mode_id = mode_id & 1
        
    return mode_id, data_block, signature
