# performance_metrics.py
import numpy as np
import math
from PIL import Image

def calculate_mse_psnr(cover_path, stego_path):
    """Calculate MSE and PSNR between cover and stego images."""
    try:
        # Load images
        cover_image = Image.open(cover_path).convert('RGB')
        stego_image = Image.open(stego_path).convert('RGB')
        
        # Convert to numpy arrays
        cover_array = np.array(cover_image)
        stego_array = np.array(stego_image)
        
        # Ensure images have same dimensions
        if cover_array.shape != stego_array.shape:
            raise ValueError("Images have different dimensions")
        
        # Calculate MSE for each channel
        mse_r = np.mean((cover_array[:,:,0] - stego_array[:,:,0]) ** 2)
        mse_g = np.mean((cover_array[:,:,1] - stego_array[:,:,1]) ** 2)
        mse_b = np.mean((cover_array[:,:,2] - stego_array[:,:,2]) ** 2)
        
        # Average MSE across channels
        mse = (mse_r + mse_g + mse_b) / 3
        
        # Calculate PSNR
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        
        return mse, psnr

    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None
