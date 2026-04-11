#!/usr/bin/env python3
"""
Detector Testing & Demo Script
Shows how to use the Detector class
"""

import sys
from pathlib import Path
import numpy as np
import cv2

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.core import Detector, print_detections, get_danger_detections
from backend.config import get_platform_config, print_platform_summary


def test_detector_initialization():
    """Test detector initialization"""
    print("\n" + "=" * 60)
    print("TEST 1: Detector Initialization")
    print("=" * 60 + "\n")
    
    config = get_platform_config()
    
    try:
        detector = Detector(
            model_path=config.model_path,
            inference_size=config.inference_size,
            num_threads=config.num_threads,
            confidence_threshold=config.confidence_threshold,
        )
        
        detector.print_stats()
        print("✅ Detector initialized successfully!")
        return detector
        
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_inference(detector):
    """Test inference on dummy frame"""
    print("\n" + "=" * 60)
    print("TEST 2: Inference on Dummy Frame")
    print("=" * 60 + "\n")
    
    try:
        # Create dummy frame
        dummy_frame = np.random.randint(
            0, 256, (480, 640, 3), dtype=np.uint8
        )
        
        print(f"Test frame shape: {dummy_frame.shape}")
        print(f"Test frame dtype: {dummy_frame.dtype}")
        
        # Run inference
        print("\n🎯 Running inference...")
        detections = detector.infer(dummy_frame)
        
        print(f"✅ Inference complete!")
        print(f"   Detections found: {len(detections)}")
        
        if detections:
            print_detections(detections)
            
            # Check dangerous detections
            danger = get_danger_detections(detections)
            if danger:
                print(f"\n⚠️ Danger detections: {len(danger)}")
        
        return detections
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_preprocessing(detector):
    """Test preprocessing pipeline"""
    print("\n" + "=" * 60)
    print("TEST 3: Preprocessing Pipeline")
    print("=" * 60 + "\n")
    
    try:
        # Create test frame of various sizes
        test_sizes = [(480, 640), (720, 1280), (360, 640)]
        
        for h, w in test_sizes:
            frame = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
            
            print(f"\nTest frame: {h}x{w}")
            tensor, scale, pad_top, pad_left = detector.preprocess(frame)
            
            print(f"  Tensor shape: {tensor.shape}")
            print(f"  Tensor range: [{tensor.min():.3f}, {tensor.max():.3f}]")
            print(f"  Scale factor: {scale:.3f}")
            print(f"  Padding: ({pad_top}, {pad_left})")
        
        print("\n✅ Preprocessing tests passed!")
        
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
        import traceback
        traceback.print_exc()


def test_visualization(detector):
    """Test visualization"""
    print("\n" + "=" * 60)
    print("TEST 4: Visualization")
    print("=" * 60 + "\n")
    
    try:
        # Create a frame with some content
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
        
        # Add some shapes to make it more interesting
        cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), 2)
        cv2.circle(frame, (500, 350), 50, (0, 0, 255), 2)
        
        # Mock detections
        from backend.core import Detection
        
        mock_detections = [
            Detection(
                class_id=0,
                class_name="with_helmet",
                confidence=0.95,
                x1=50, y1=50, x2=200, y2=200,
                center_x=125, center_y=125,
                width=150, height=150,
                is_danger=False,
            ),
            Detection(
                class_id=1,
                class_name="without_helmet",
                confidence=0.87,
                x1=300, y1=150, x2=500, y2=350,
                center_x=400, center_y=250,
                width=200, height=200,
                is_danger=True,
            ),
        ]
        
        print(f"Mock detections: {len(mock_detections)}")
        
        # Draw
        annotated = detector.draw_detections(frame, mock_detections)
        
        print(f"Annotated shape: {annotated.shape}")
        print("✅ Visualization test passed!")
        
        # Save test image
        output_path = "test_visualization.jpg"
        cv2.imwrite(output_path, annotated)
        print(f"   Saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Visualization failed: {e}")
        import traceback
        traceback.print_exc()


def test_benchmark(detector):
    """Test benchmarking"""
    print("\n" + "=" * 60)
    print("TEST 5: Performance Benchmark")
    print("=" * 60 + "\n")
    
    try:
        results = detector.benchmark(n_frames=20)
        
        print("\n✅ Benchmark complete!")
        print("\nDetailed Results:")
        for key, value in results.items():
            print(f"  {key:20} {value}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════╗
║  Detector Module Testing & Demo                      ║
║  Traffic Violation Detection System                  ║
╚══════════════════════════════════════════════════════╝
    """)
    
    # Print platform info
    print("Platform Configuration:")
    print_platform_summary()
    
    # Initialize detector
    detector = test_detector_initialization()
    if not detector:
        print("\nCannot proceed without detector")
        return 1
    
    # Run tests
    test_inference(detector)
    test_preprocessing(detector)
    test_visualization(detector)
    test_benchmark(detector)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60 + "\n")
    
    print("💡 Usage Examples:")
    print("""
# Basic inference:
detector = Detector(model_path, inference_size=416, num_threads=4)
detections = detector.infer(frame)

# Draw results:
annotated = detector.draw_detections(frame, detections)

# Get danger violations:
danger = [d for d in detections if d.is_danger]

# Benchmark:
results = detector.benchmark(n_frames=100)
print(f"FPS: {results['fps_mean']:.1f}")
    """)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
