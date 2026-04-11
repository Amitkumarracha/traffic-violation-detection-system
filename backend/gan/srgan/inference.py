"""
RealESRGAN License Plate Super-Resolution
Upscales small license plate crops 4× before OCR
"""

from pathlib import Path
from typing import Tuple
import cv2
import numpy as np
import logging
from time import time
from collections import deque

logger = logging.getLogger(__name__)


class PlateUpscaler:
    """
    License plate super-resolution using RealESRGAN.
    
    Conditionally upscales small plate crops (< threshold_area) 4× before OCR.
    Only runs when needed - never blocks main inference pipeline.
    Designed for threading (runs in separate thread, not inference thread).
    """
    
    # Size thresholds
    MIN_PLATE_AREA = 3000      # pixels² - upscale below this
    MIN_PLATE_WIDTH = 100      # pixels - upscale if narrower
    
    # Performance tracking
    MAX_TIMING_SAMPLES = 100
    
    def __init__(self, scale: int = 4, device: str = 'cpu'):
        """
        Initialize PlateUpscaler with RealESRGAN model.
        
        Args:
            scale: Upscaling factor (default: 4×)
            device: 'cpu' or 'cuda' (default: 'cpu' for Raspberry Pi)
        
        Note: Automatically downloads weights if not present.
        """
        self.scale = scale
        self.device = device
        self.model = None
        self.initialized = False
        
        # Performance tracking
        self.upscale_times = deque(maxlen=self.MAX_TIMING_SAMPLES)
        self.total_upscales = 0
        self.total_skipped = 0
        
        logger.info(f"PlateUpscaler initialized (scale={scale}×, device={device}, lazy-loaded)")
    
    def _init_model(self):
        """Lazy initialization of RealESRGAN model"""
        if self.initialized:
            return
        
        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
        except ImportError as e:
            logger.error(
                f"Failed to import ESRGAN modules: {e}\n"
                f"Install with: pip install basicsr realesrgan"
            )
            raise
        
        # Check and download weights if needed
        weights_path = self._get_weights_path()
        
        if not self._weights_exist(weights_path):
            logger.info("downloading model weights...")
            self._download_weights()
        
        try:
            logger.info(f"Loading RealESRGAN model from {weights_path}...")
            
            # Initialize model architecture
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=self.scale
            )
            
            # Load upscaler
            self.model = RealESRGANer(
                scale=self.scale,
                model_path=str(weights_path),
                upsampler=model,
                tile=400,  # Tile size for memory management
                tile_pad=10,
                pre_pad=0,
                half=False  # Use FP32 for CPU stability
            )
            
            self.model.device = self.device
            logger.info("✓ RealESRGAN model loaded successfully")
            self.initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize RealESRGAN: {e}")
            raise
    
    def _get_weights_path(self) -> Path:
        """Get path to model weights"""
        module_dir = Path(__file__).parent
        return module_dir / "weights" / "RealESRGAN_x4plus.pth"
    
    def _weights_exist(self, weights_path: Path) -> bool:
        """Check if weights file exists and is valid"""
        if not weights_path.exists():
            return False
        
        file_size_mb = weights_path.stat().st_size / (1024 * 1024)
        return file_size_mb >= 60.0
    
    def _download_weights(self):
        """Automatically download model weights"""
        try:
            from .download_weights import download_weights
            
            output_path = self._get_weights_path()
            if not download_weights(output_path=str(output_path)):
                raise RuntimeError("Weight download failed")
        
        except Exception as e:
            logger.error(f"Failed to download weights: {e}")
            raise
    
    def upscale(self, crop_bgr: np.ndarray) -> np.ndarray:
        """
        Upscale license plate crop 4×.
        
        Args:
            crop_bgr: BGR numpy array (small plate crop)
        
        Returns:
            Upscaled BGR image (4× larger)
        """
        
        # Lazy init on first call
        if not self.initialized:
            self._init_model()
        
        start_time = time()
        original_shape = crop_bgr.shape[:2]  # (height, width)
        
        try:
            # Convert BGR → RGB for ESRGAN
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            
            # Run upscaling
            output_rgb, _ = self.model.enhance(crop_rgb, outscale=self.scale)
            
            # Convert back RGB → BGR
            output_bgr = cv2.cvtColor(output_rgb, cv2.COLOR_RGB2BGR)
            
            # Track timing
            elapsed_ms = (time() - start_time) * 1000
            self.upscale_times.append(elapsed_ms)
            self.total_upscales += 1
            
            # Log result
            upscaled_shape = output_bgr.shape[:2]
            logger.debug(
                f"SRGAN: {original_shape[1]}x{original_shape[0]} → "
                f"{upscaled_shape[1]}x{upscaled_shape[0]} in {elapsed_ms:.0f}ms"
            )
            
            return output_bgr
        
        except Exception as e:
            logger.error(f"SRGAN upscaling failed: {e}")
            # Return original on error
            return crop_bgr
    
    def should_upscale(
        self,
        crop_bgr: np.ndarray,
        threshold_area: int = None
    ) -> bool:
        """
        Determine if crop needs upscaling.
        
        Args:
            crop_bgr: Input image
            threshold_area: Minimum area (default: 3000 px²)
        
        Returns:
            True if upscaling recommended
        """
        
        if threshold_area is None:
            threshold_area = self.MIN_PLATE_AREA
        
        height, width = crop_bgr.shape[:2]
        area = height * width
        
        # Upscale if area too small OR width too narrow
        return area < threshold_area or width < self.MIN_PLATE_WIDTH
    
    def upscale_if_needed(
        self,
        crop_bgr: np.ndarray,
        threshold_area: int = None
    ) -> Tuple[np.ndarray, bool]:
        """
        Conditionally upscale plate crop.
        
        Only runs SRGAN if crop is below threshold_area.
        Otherwise returns original unchanged.
        
        Args:
            crop_bgr: Input BGR image
            threshold_area: Min area before upscaling (default: 3000 px²)
        
        Returns:
            Tuple of (upscaled_image, was_upscaled)
            - upscaled_image: Either original or 4× upscaled
            - was_upscaled: Boolean indicating if upscaling was applied
        """
        
        if threshold_area is None:
            threshold_area = self.MIN_PLATE_AREA
        
        # Check if upscaling needed
        if not self.should_upscale(crop_bgr, threshold_area):
            self.total_skipped += 1
            return crop_bgr, False
        
        # Perform upscaling
        upscaled = self.upscale(crop_bgr)
        self.total_upscales += 1
        
        logger.debug(f"Applied SRGAN upscaling (area threshold: {threshold_area}px²)")
        
        return upscaled, True
    
    def benchmark(self, num_iterations: int = 20) -> dict:
        """
        Benchmark upscaling performance.
        
        Args:
            num_iterations: Number of upscaling runs (default: 20)
        
        Returns:
            Dictionary with timing statistics
        """
        
        logger.info(f"Running SRGAN benchmark ({num_iterations} iterations)...")
        
        # Create dummy small plate image (60×20)
        dummy_crop = np.random.randint(0, 255, (20, 60, 3), dtype=np.uint8)
        
        # Clear timing buffer
        self.upscale_times.clear()
        
        # Run benchmark
        for i in range(num_iterations):
            _ = self.upscale(dummy_crop)
            if (i + 1) % 5 == 0:
                logger.debug(f"  {i+1}/{num_iterations} completed")
        
        # Calculate statistics
        times = list(self.upscale_times)
        times_np = np.array(times)
        
        stats = {
            'iterations': num_iterations,
            'min_ms': float(times_np.min()),
            'max_ms': float(times_np.max()),
            'mean_ms': float(times_np.mean()),
            'median_ms': float(np.median(times_np)),
            'std_ms': float(times_np.std()),
        }
        
        logger.info(f"Benchmark results:")
        logger.info(f"  Min: {stats['min_ms']:.1f}ms")
        logger.info(f"  Max: {stats['max_ms']:.1f}ms")
        logger.info(f"  Mean: {stats['mean_ms']:.1f}ms")
        logger.info(f"  Median: {stats['median_ms']:.1f}ms")
        logger.info(f"  Std Dev: {stats['std_ms']:.1f}ms")
        
        return stats
    
    def get_stats(self) -> dict:
        """
        Get upscaler statistics.
        
        Returns:
            Dictionary with usage and performance stats
        """
        
        avg_time_ms = np.mean(list(self.upscale_times)) if self.upscale_times else 0.0
        
        return {
            'initialized': self.initialized,
            'device': self.device,
            'scale': self.scale,
            'total_upscales': self.total_upscales,
            'total_skipped': self.total_skipped,
            'avg_upscale_ms': avg_time_ms,
            'recent_timings': list(self.upscale_times),
        }
    
    def print_stats(self):
        """Print upscaler statistics"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("PLATE UPSCALER STATISTICS")
        print("=" * 60)
        print(f"\nDevice: {stats['device']}")
        print(f"Scale: {stats['scale']}×")
        print(f"Initialized: {stats['initialized']}")
        print(f"\nUsage:")
        print(f"  Total upscales: {stats['total_upscales']}")
        print(f"  Total skipped: {stats['total_skipped']}")
        if stats['total_upscales'] + stats['total_skipped'] > 0:
            upscale_rate = stats['total_upscales'] / (stats['total_upscales'] + stats['total_skipped'])
            print(f"  Upscale rate: {upscale_rate:.1%}")
        
        print(f"\nPerformance:")
        print(f"  Avg time: {stats['avg_upscale_ms']:.1f}ms")
        print("\n" + "=" * 60 + "\n")


# Utility functions

def create_upscaler(device: str = 'cpu') -> PlateUpscaler:
    """
    Create a PlateUpscaler instance.
    
    Args:
        device: 'cpu' or 'cuda'
    
    Returns:
        PlateUpscaler instance
    """
    return PlateUpscaler(scale=4, device=device)
