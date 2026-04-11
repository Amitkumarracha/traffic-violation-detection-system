"""
SRGAN Upscaler Demo
Demonstrates super-resolution upscaling for license plate recognition
"""

import cv2
import numpy as np
import logging
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_conditional_upscaling():
    """Demo: Conditional upscaling based on plate size"""
    
    print("\n" + "=" * 70)
    print("DEMO 1: CONDITIONAL UPSCALING")
    print("=" * 70)
    
    from backend.gan.srgan.inference import create_upscaler
    
    upscaler = create_upscaler(device='cpu')
    
    # Create dummy small and large plates
    small_plate = np.random.randint(0, 255, (20, 45, 3), dtype=np.uint8)  # 900 px²
    large_plate = np.random.randint(0, 255, (40, 150, 3), dtype=np.uint8)  # 6000 px²
    
    print(f"\n🔹 Small plate: {small_plate.shape} = {small_plate.shape[0] * small_plate.shape[1]} px²")
    result_small, upscaled_small = upscaler.upscale_if_needed(small_plate)
    print(f"   Upscaled: {upscaled_small}")
    if upscaled_small:
        print(f"   Result: {result_small.shape} ({result_small.shape[0] * result_small.shape[1]} px²)")
    
    print(f"\n🔹 Large plate: {large_plate.shape} = {large_plate.shape[0] * large_plate.shape[1]} px²")
    result_large, upscaled_large = upscaler.upscale_if_needed(large_plate)
    print(f"   Upscaled: {upscaled_large}")
    print(f"   Result: {result_large.shape} ({result_large.shape[0] * result_large.shape[1]} px²)")
    
    # Stats
    stats = upscaler.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total upscales: {stats['total_upscales']}")
    print(f"   Total skipped: {stats['total_skipped']}")


def demo_size_transformation():
    """Demo: Size transformation during upscaling"""
    
    print("\n" + "=" * 70)
    print("DEMO 2: SIZE TRANSFORMATION")
    print("=" * 70)
    
    from backend.gan.srgan.inference import create_upscaler
    
    upscaler = create_upscaler(device='cpu')
    
    test_sizes = [
        (18, 45),  # Indian license plate typical: 45×18
        (20, 50),  # Slightly larger
        (25, 80),  # Medium plate
    ]
    
    print("\nExpected transformations (4× upscaling):")
    
    for height, width in test_sizes:
        area = height * width
        upscaled_h = height * 4
        upscaled_w = width * 4
        upscaled_area = upscaled_h * upscaled_w
        
        print(f"\n  Input: {width}×{height} = {area} px²")
        print(f"  Output: {upscaled_w}×{upscaled_h} = {upscaled_area} px²")
        print(f"  Scaling factor: {(upscaled_area / area):.0f}×")


def demo_threshold_configuration():
    """Demo: Threshold configuration for conditional upscaling"""
    
    print("\n" + "=" * 70)
    print("DEMO 3: THRESHOLD CONFIGURATION")
    print("=" * 70)
    
    from backend.gan.srgan.inference import PlateUpscaler
    
    upscaler = PlateUpscaler()
    
    print("\n📋 Default thresholds:")
    print(f"   MIN_PLATE_AREA: {upscaler.MIN_PLATE_AREA} px²")
    print(f"   MIN_PLATE_WIDTH: {upscaler.MIN_PLATE_WIDTH} px")
    
    print("\n🔹 Testing area threshold (default 3000 px²):")
    
    test_areas = [
        (20, 80),   # 1600 px² - SMALL
        (30, 100),  # 3000 px² - BOUNDARY
        (40, 150),  # 6000 px² - LARGE
    ]
    
    for h, w in test_areas:
        area = h * w
        should_upscale = upscaler.should_upscale(
            np.zeros((h, w, 3), dtype=np.uint8),
            threshold_area=3000
        )
        status = "✓ UPSCALE" if should_upscale else "✗ SKIP"
        print(f"   {w}×{h} = {area} px² → {status}")
    
    print("\n🔹 Testing width threshold (default 100 px):")
    
    test_widths = [
        (100, 50),   # 50px width - NARROW
        (100, 100),  # 100px width - BOUNDARY
        (100, 150),  # 150px width - WIDE
    ]
    
    for h, w in test_widths:
        area = h * w
        should_upscale = upscaler.should_upscale(
            np.zeros((h, w, 3), dtype=np.uint8),
            threshold_area=3000
        )
        status = "✓ UPSCALE" if should_upscale else "✗ SKIP"
        print(f"   {w}×{h} = {area} px² (width={w}) → {status}")


def demo_statistics():
    """Demo: Statistics tracking"""
    
    print("\n" + "=" * 70)
    print("DEMO 4: STATISTICS TRACKING")
    print("=" * 70)
    
    from backend.gan.srgan.inference import create_upscaler
    
    upscaler = create_upscaler(device='cpu')
    
    # Simulate mixture of upscaling and skipping
    small_plate = np.zeros((20, 45, 3), dtype=np.uint8)
    large_plate = np.zeros((40, 150, 3), dtype=np.uint8)
    
    print("\nSimulating 10 plate processing events:")
    
    for i in range(10):
        if i % 3 == 0:
            upscaler.upscale_if_needed(small_plate)
            print(f"  Event {i+1}: Small plate (upscaled)")
        else:
            upscaler.upscale_if_needed(large_plate)
            print(f"  Event {i+1}: Large plate (skipped)")
    
    # Print statistics
    upscaler.print_stats()


def demo_integration_workflow():
    """Demo: Integration with OCR workflow"""
    
    print("\n" + "=" * 70)
    print("DEMO 5: OCR INTEGRATION WORKFLOW")
    print("=" * 70)
    
    from backend.gan.srgan.inference import create_upscaler
    
    print("\nSimulated workflow:")
    print("  1. Detector finds license plate crop")
    print("  2. Check if upscaling needed")
    print("  3. If small: Apply 4× SRGAN upscaling")
    print("  4. Pass to PaddleOCR for text extraction")
    
    upscaler = create_upscaler(device='cpu')
    
    # Simulated detections
    detections = [
        ("frame_001", np.zeros((18, 45, 3), dtype=np.uint8), "SMALL - distant vehicle"),
        ("frame_002", np.zeros((35, 120, 3), dtype=np.uint8), "LARGE - close vehicle"),
        ("frame_003", np.zeros((22, 60, 3), dtype=np.uint8), "MEDIUM - medium distance"),
    ]
    
    print("\n📷 Processing detections:")
    
    for frame_id, crop, description in detections:
        h, w = crop.shape[:2]
        area = h * w
        
        upscaled, was_upscaled = upscaler.upscale_if_needed(crop)
        upscaled_h, upscaled_w = upscaled.shape[:2]
        
        print(f"\n  {frame_id} ({description})")
        print(f"    Input:  {w}×{h} = {area} px²")
        
        if was_upscaled:
            print(f"    Output: {upscaled_w}×{upscaled_h} = {upscaled_h * upscaled_w} px² (upscaled)")
            print(f"    → Pass to OCR for retry")
        else:
            print(f"    → Sufficient size, process directly")


def demo_api_reference():
    """Demo: Complete API reference"""
    
    print("\n" + "=" * 70)
    print("API REFERENCE: PlateUpscaler")
    print("=" * 70)
    
    print("""
PlateUpscaler(scale=4, device='cpu')
    Initialize upscaler
    Args:
        scale: Upscaling factor (default: 4×)
        device: 'cpu' or 'cuda' (default: 'cpu')

.upscale(crop_bgr) -> upscaled_bgr
    Apply 4× upscaling to plate crop
    Args:
        crop_bgr: BGR numpy array
    Returns:
        Upscaled BGR image (4× larger)
    
.upscale_if_needed(crop_bgr, threshold_area=3000) -> (image, bool)
    Conditionally upscale based on size
    Args:
        crop_bgr: BGR numpy array
        threshold_area: Min area before upscaling (default: 3000 px²)
    Returns:
        Tuple of (image, was_upscaled)

.should_upscale(crop_bgr, threshold_area=3000) -> bool
    Check if upscaling needed WITHOUT processing
    Args:
        crop_bgr: BGR numpy array
        threshold_area: Min area threshold (default: 3000 px²)
    Returns:
        True if upscaling recommended

.benchmark(num_iterations=20) -> dict
    Measure upscaling performance
    Args:
        num_iterations: Number of test runs (default: 20)
    Returns:
        Dict with min/max/mean/median/std timing in ms

.get_stats() -> dict
    Get upscaler usage statistics
    Returns:
        Dict with counters and performance metrics

.print_stats()
    Pretty-print statistics

create_upscaler(device='cpu') -> PlateUpscaler
    Utility function to create upscaler instance
    Args:
        device: 'cpu' or 'cuda'
    Returns:
        PlateUpscaler instance
    """)


def main():
    """Run all demos"""
    
    print("\n" + "=" * 70)
    print("LICENSE PLATE SUPER-RESOLUTION DEMO")
    print("Real-ESRGAN 4× Upscaling for Small Plates")
    print("=" * 70)
    
    # Note: Demos 1-4 work without actual model weights (using dummy images)
    # For actual upscaling support, weights need to be downloaded first
    
    try:
        demo_conditional_upscaling()
        demo_size_transformation()
        demo_threshold_configuration()
        demo_statistics()
        demo_integration_workflow()
        demo_api_reference()
        
        print("\n" + "=" * 70)
        print("✓ All demos completed successfully!")
        print("=" * 70)
        print("\n📝 Next steps:")
        print("  1. Download model weights: python -m backend.gan.srgan.download_weights")
        print("  2. Run tests: pytest test_srgan.py -v")
        print("  3. Integrate with OCR: See SRGAN_GUIDE.md")
        print()
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure backend modules are in PYTHONPATH")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
