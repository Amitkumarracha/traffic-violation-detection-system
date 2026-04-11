#!/usr/bin/env python3
"""
Simplified SRGAN Integration for Inference Enhancement
Only applies SRGAN after frame detection for license plate upscaling
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from backend.gan.srgan.inference import PlateUpscaler

logger = logging.getLogger(__name__)


class InferenceSRGAN:
    """
    Simplified SRGAN integration for inference-time enhancement only.

    Usage:
        enhancer = InferenceSRGAN()
        if enhancer.needs_upscaling(plate_bbox):
            enhanced_plate = enhancer.upscale(plate_crop)
    """

    def __init__(self, device: str = 'auto'):
        """
        Initialize SRGAN for inference enhancement.

        Args:
            device: 'auto' (GPU if available, else CPU), 'cpu', or 'cuda'
        """
        # Auto-detect device
        if device == 'auto':
            try:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            except:
                device = 'cpu'

        self.upscaler = PlateUpscaler(scale=4, device=device)
        self.upscale_count = 0

        logger.info(f"SRGAN initialized for inference enhancement (device: {device})")

    def needs_upscaling(self, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Check if license plate needs SRGAN upscaling.

        Args:
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            True if plate is too small for reliable OCR
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height

        # Use same thresholds as PlateUpscaler
        needs_srgan = area < 3000 or width < 100

        return needs_srgan

    def upscale_plate(self, plate_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Upscale license plate crop using SRGAN.

        Args:
            plate_crop: License plate image crop

        Returns:
            Upscaled image (4x resolution) or None if failed
        """
        try:
            # Upscale using SRGAN
            upscaled = self.upscaler.upscale(plate_crop)

            if upscaled is not None:
                self.upscale_count += 1
                logger.debug(f"SRGAN applied (count: {self.upscale_count})")
                return upscaled
            else:
                logger.warning("SRGAN upscaling failed")
                return None

        except Exception as e:
            logger.error(f"SRGAN upscaling error: {e}")
            return None

    def get_stats(self) -> dict:
        """Get SRGAN usage statistics"""
        return {
            'srgan_activations': self.upscale_count,
            'device': self.upscaler.device
        }


# Global instance for easy import
_srgan_instance = None

def get_srgan_enhancer(device: str = 'auto') -> InferenceSRGAN:
    """Get or create global SRGAN enhancer instance"""
    global _srgan_instance
    if _srgan_instance is None:
        _srgan_instance = InferenceSRGAN(device=device)
    return _srgan_instance


# Example usage in inference pipeline
def enhance_plate_for_ocr(plate_crop: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Enhance license plate for OCR if needed.

    Args:
        plate_crop: Original plate crop
        bbox: Bounding box for size check

    Returns:
        Enhanced plate crop (original or upscaled)
    """
    enhancer = get_srgan_enhancer()

    if enhancer.needs_upscaling(bbox):
        enhanced = enhancer.upscale_plate(plate_crop)
        if enhanced is not None:
            return enhanced

    # Return original if upscaling not needed or failed
    return plate_crop


if __name__ == "__main__":
    # Test SRGAN integration
    print("Testing SRGAN inference enhancement...")

    # Create test plate crop (small image)
    test_plate = np.random.randint(0, 255, (50, 150, 3), dtype=np.uint8)

    # Test bounding box that needs upscaling
    test_bbox = (100, 100, 250, 150)  # Small area

    enhancer = InferenceSRGAN()

    if enhancer.needs_upscaling(test_bbox):
        print("✅ Plate needs SRGAN upscaling")
        enhanced = enhancer.upscale_plate(test_plate)
        if enhanced is not None:
            print(f"✅ Upscaling successful: {test_plate.shape} → {enhanced.shape}")
        else:
            print("❌ Upscaling failed")
    else:
        print("ℹ️  Plate doesn't need upscaling")

    print(f"Stats: {enhancer.get_stats()}")