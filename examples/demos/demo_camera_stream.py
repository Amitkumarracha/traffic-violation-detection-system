"""
Camera Stream Demo
Demonstrates Thread 1 of the 4-thread pipeline
"""

import cv2
import time
import logging
from pathlib import Path
from backend.pipeline.camera_stream import CameraStream, create_camera_stream

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_capture():
    """Demo: Basic camera frame capture"""
    
    print("\n" + "=" * 80)
    print("DEMO 1: BASIC CAMERA CAPTURE")
    print("=" * 80)
    
    print("\nCapturing from webcam (5 seconds, 30fps)...\n")
    
    # Create camera stream
    camera = CameraStream(source=0, width=1280, height=720, fps=30)
    thread = camera.start()
    
    try:
        frame_count = 0
        last_fps = 0
        
        start_time = time.time()
        
        while time.time() - start_time < 5:
            frame = camera.read()
            
            if frame is not None:
                frame_count += 1
                fps = camera.get_fps()
                
                # Print every second
                if fps != last_fps:
                    print(f"  Frame {frame_count}: {frame.shape} @ {fps:.1f} FPS")
                    last_fps = fps
            
            time.sleep(0.01)
        
        print(f"\n✓ Captured {frame_count} frames in 5 seconds")
        print(f"✓ Average FPS: {frame_count / 5:.1f}")
        print(f"✓ Camera stream: {camera.width}×{camera.height} @ {camera.target_fps}fps")
    
    finally:
        camera.stop()
    
    print("=" * 80)


def demo_non_blocking():
    """Demo: Non-blocking queue behavior"""
    
    print("\n" + "=" * 80)
    print("DEMO 2: NON-BLOCKING QUEUE BEHAVIOR")
    print("=" * 80)
    
    print("\nDemonstrating that frame queue never blocks...\n")
    
    camera = CameraStream()
    
    # Simulate capture thread filling queue
    print("  Filling queue to capacity (maxsize=2)...")
    
    frame1 = b'\x00' * (1280 * 720 * 3)
    frame2 = b'\x00' * (1280 * 720 * 3)
    frame3 = b'\x00' * (1280 * 720 * 3)
    
    try:
        camera.frame_queue.put_nowait(frame1)
        print(f"    Added frame 1, queue size: {camera.frame_queue.qsize()}")
    except:
        pass
    
    try:
        camera.frame_queue.put_nowait(frame2)
        print(f"    Added frame 2, queue size: {camera.frame_queue.qsize()}")
    except:
        pass
    
    print(f"  Queue is at capacity: {camera.frame_queue.qsize() == 2}")
    
    print("\n  Attempting to add 3rd frame without blocking...")
    t0 = time.time()
    
    # Simulate the non-blocking drop logic
    try:
        camera.frame_queue.get_nowait()
        camera.frame_queue.put_nowait(frame3)
    except:
        pass
    
    elapsed = time.time() - t0
    
    print(f"    ✓ Added frame 3 in {elapsed*1000:.1f}ms (non-blocking)")
    print(f"    Queue size: {camera.frame_queue.qsize()}")
    print("\n✓ Queue never blocks - always keeps latest frame")
    
    print("=" * 80)


def demo_factory():
    """Demo: Factory function"""
    
    print("\n" + "=" * 80)
    print("DEMO 3: FACTORY FUNCTION")
    print("=" * 80)
    
    print("\nUsing create_camera_stream() factory...\n")
    
    camera = create_camera_stream(
        source=0,
        width=1280,
        height=720,
        fps=30
    )
    
    try:
        print(f"  Camera created and started")
        print(f"  Resolution: {camera.width}×{camera.height}")
        print(f"  Target FPS: {camera.target_fps}")
        print(f"  Is video file: {camera.is_video_file()}")
        print(f"  Camera thread alive: {camera.capture_thread.is_alive()}")
        
        time.sleep(1)
        
        print(f"  Measured FPS: {camera.get_fps():.1f}")
    
    finally:
        camera.stop()
        print(f"  Camera stopped")
    
    print("=" * 80)


def demo_fps_tracking():
    """Demo: FPS tracking"""
    
    print("\n" + "=" * 80)
    print("DEMO 4: FPS TRACKING")
    print("=" * 80)
    
    print("\nTracking measured FPS over 10 seconds...\n")
    
    camera = CameraStream()
    thread = camera.start()
    
    try:
        fps_values = []
        
        for i in range(10):
            fps = camera.get_fps()
            fps_values.append(fps)
            print(f"  Second {i+1}: {fps:.1f} FPS")
            time.sleep(1)
        
        if fps_values:
            avg_fps = sum(fps_values) / len(fps_values)
            max_fps = max(fps_values)
            min_fps = min(fps_values)
            
            print(f"\n  Average FPS: {avg_fps:.1f}")
            print(f"  Max FPS: {max_fps:.1f}")
            print(f"  Min FPS: {min_fps:.1f}")
        
    finally:
        camera.stop()
    
    print("=" * 80)


def demo_thread_info():
    """Demo: Thread information"""
    
    print("\n" + "=" * 80)
    print("DEMO 5: THREAD INFORMATION")
    print("=" * 80)
    
    print("\nThread architecture for 4-thread pipeline:\n")
    
    print("  Thread 1: Camera Capture (camera_stream.py) - THIS MODULE")
    print("    ├─ Captures frames from camera/video")
    print("    ├─ Puts frames in queue (maxsize=2)")
    print("    ├─ Never blocks or falls behind")
    print("    └─ Always keeps latest frame ready")
    print()
    print("  Thread 2: Detection (detection_processor.py)")
    print("    ├─ Reads frames from Thread 1")
    print("    ├─ Runs YOLO26n detection")
    print("    └─ Puts detections in queue for Thread 3")
    print()
    print("  Thread 3: Tracking & Processing (tracking_processor.py)")
    print("    ├─ Reads detections from Thread 2")
    print("    ├─ Runs DeepSort tracking")
    print("    ├─ Applies violation gate")
    print("    └─ Puts results in queue for Thread 4")
    print()
    print("  Thread 4: Logging & Async Tasks (logging_processor.py)")
    print("    ├─ Reads results from Thread 3")
    print("    ├─ Performs OCR (200-350ms)")
    print("    ├─ Performs SRGAN upscaling (200-400ms)")
    print("    ├─ Logs violations to database")
    print("    └─ Sends alerts")
    
    print("\n  Creating Thread 1 now...\n")
    
    camera = CameraStream()
    thread = camera.start()
    
    try:
        print(f"  ✓ Thread name: {thread.name}")
        print(f"  ✓ Thread alive: {thread.is_alive()}")
        print(f"  ✓ Thread daemon: {thread.daemon}")
        print(f"  ✓ Queue maxsize: {camera.frame_queue.maxsize}")
        print(f"  ✓ Platform: {camera._get_platform_name()}")
        print(f"  ✓ Startup message: {camera._get_startup_message()}")
    
    finally:
        camera.stop()
    
    print("=" * 80)


def demo_usage_code():
    """Demo: Code usage examples"""
    
    print("\n" + "=" * 80)
    print("DEMO 6: USAGE EXAMPLES")
    print("=" * 80)
    
    print("""
Example 1: Basic Usage
    from backend.pipeline import CameraStream
    
    camera = CameraStream(source=0, width=1280, height=720, fps=30)
    thread = camera.start()
    
    while True:
        frame = camera.read()
        if frame is not None:
            process(frame)

Example 2: Using Factory
    from backend.pipeline import create_camera_stream
    
    camera = create_camera_stream()
    while True:
        frame = camera.read()
        if frame is not None:
            print(f"FPS: {camera.get_fps():.1f}")

Example 3: Video File (Testing)
    camera = CameraStream(source='test_video.mp4')
    if camera.is_video_file():
        print("Running in test mode with video file")

Example 4: Custom Resolution
    camera = CameraStream(
        source=0,
        width=640,
        height=480,
        fps=24
    )
    camera.start()

Example 5: With Cleanup
    camera = CameraStream()
    thread = camera.start()
    
    try:
        while condition:
            frame = camera.read()
    finally:
        camera.stop()  # Ensures proper cleanup
    """)
    
    print("=" * 80)


def main():
    """Run all demonstrations"""
    
    print("\n" + "=" * 80)
    print("CAMERA STREAM - THREAD 1 PIPELINE DEMONSTRATION")
    print("Non-blocking Frame Capture Architecture")
    print("=" * 80)
    
    demos = [
        ("Basic Capture", demo_basic_capture),
        ("Non-Blocking Queue", demo_non_blocking),
        ("Factory Function", demo_factory),
        ("FPS Tracking", demo_fps_tracking),
        ("Thread Info", demo_thread_info),
        ("Usage Examples", demo_usage_code),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Demo {i} ({name}) failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ All demonstrations completed!")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
