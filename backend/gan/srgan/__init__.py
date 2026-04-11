"""
RealESRGAN License Plate Super-Resolution Module

Provides 4× upscaling for small license plate crops before OCR.
Only processes plates below area/width thresholds.
"""

from .inference import PlateUpscaler, create_upscaler
from .download_weights import download_weights, check_weights

__all__ = [
    'PlateUpscaler',
    'create_upscaler',
    'download_weights',
    'check_weights',
]

__version__ = '1.0.0'
