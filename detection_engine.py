import numpy as np
from PIL import Image
from stego_engine import bits_to_bytes, MAGIC

def scan_image_for_signature(img: Image.Image) -> dict:
    """
    Analyzes an image to see if it contains our specific digital signature.
    
    How it works:
    1. We look at the very first 32 pixels (roughly).
    2. We extract the Least Significant Bit from each.
    3. We combine these bits to form 4 bytes.
    4. We check if these 4 bytes match our magic signature "DSAI".
    
    This is extremely fast because we don't need to process the whole image,
    just the header at the beginning.
    """
    try:
        # Convert to RGB to ensure consistent channel count
        arr = np.array(img.convert("RGB"))
        flat = arr.flatten()
        
        # Safety check: is the image big enough to even have a header?
        if len(flat) < 32:
            return {"detected": False, "error": "Image is too small to contain data."}
            
        # Extract the first 32 bits (4 bytes * 8 bits)
        header_bits = (flat[:32] & 1).astype(np.uint8)
        header_bytes = bits_to_bytes(header_bits)
        
        # Compare with our known signatures
        if header_bytes.startswith(MAGIC):
            return {
                "detected": True,
                "confidence": "100%",
                "message": "DeepStegAI Signature Found (Standard LSB)",
                "magic_bytes": header_bytes.hex()
            }
        elif header_bytes.startswith(b"ADPT") or header_bytes.startswith(b"ADPS"):
            return {
                "detected": True,
                "confidence": "100%",
                "message": "DeepStegAI Signature Found (Adaptive Edge)",
                "magic_bytes": header_bytes.hex()
            }
        else:
            return {
                "detected": False,
                "confidence": "0%",
                "message": "No Signature Found",
                "magic_bytes": header_bytes.hex()
            }
            
    except Exception as e:
        return {"detected": False, "error": str(e)}
