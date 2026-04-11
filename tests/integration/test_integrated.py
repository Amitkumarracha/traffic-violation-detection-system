#!/usr/bin/env python3
"""
Integrated Detector + Tracker Testing System
Tests complete pipeline: detection -> tracking -> motion analysis
"""

import sys
from pathlib import Path
import numpy as np
import cv2
import argparse
from time import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    Detector,
    VehicleTracker,
    Detection,
    print_tracked_objects,
)


class IntegratedTestSystem:
    """Combined detector + tracker test system"""
    
    def __init__(self, model_path="./yolov8n.pt", device="auto", model_size=640):
        """Initialize detector and tracker"""
        print("Initializing Integrated Test System...")
        
        # Initialize detector
        try:
            # Try ONNX first
            onnx_path = model_path.replace(".pt", ".onnx")
            if Path(onnx_path).exists():
                print(f"Loading ONNX model: {onnx_path}")
                self.detector = Detector(onnx_path, device=device, model_size=model_size)
                print("✅ Detector loaded (ONNX)")
            else:
                print(f"ONNX not found, will use PyTorch: {model_path}")
                self.detector = Detector(model_path, device=device, model_size=model_size)
                print("✅ Detector loaded (PyTorch)")
        except Exception as e:
            print(f"❌ Failed to load detector: {e}")
            raise
        
        # Initialize tracker
        try:
            self.tracker = VehicleTracker(max_age=30, n_init=3)
            print("✅ Tracker initialized")
        except Exception as e:
            print(f"❌ Failed to initialize tracker: {e}")
            raise
        
        self.frame_count = 0
        self.total_time = 0.0
    
    def process_frame(self, frame):
        """Process single frame with detection and tracking"""
        start_time = time()
        
        # Detect
        detections = self.detector.infer(frame)
        
        # Track
        tracked = self.tracker.update(detections, frame)
        
        # Timing
        process_time = (time() - start_time) * 1000  # ms
        self.total_time += process_time
        self.frame_count += 1
        fps = 1000.0 / process_time if process_time > 0 else 0
        
        return tracked, detections, process_time, fps
    
    def draw_results(self, frame, tracked, detections, process_time, fps):
        """Draw detection and tracking results"""
        # Draw detections
        if detections:
            frame = self.detector.draw_detections(frame, detections)
        
        # Draw tracking information
        frame = self._draw_tracking_info(frame, tracked)
        
        # Draw stats
        frame = self._draw_stats(frame, len(detections), len(tracked), process_time, fps)
        
        return frame
    
    def _draw_tracking_info(self, frame, tracked):
        """Draw tracking information on frame"""
        for track in tracked:
            # Draw bounding box (blue for tracked)
            cv2.rectangle(frame, (track.x1, track.y1), (track.x2, track.y2), (255, 0, 0), 2)
            
            # Draw track ID
            cv2.putText(frame, f"ID:{track.track_id}", (track.x1, track.y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            # Draw centroid
            cv2.circle(frame, (track.center_x, track.center_y), 3, (0, 255, 255), -1)
            
            # Draw confimation status
            status = "✓" if track.is_confirmed else "?"
            cv2.putText(frame, status, (track.x1 + 5, track.y2 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        return frame
    
    def _draw_stats(self, frame, n_detections, n_tracked, process_time, fps):
        """Draw statistics on frame"""
        h, w = frame.shape[:2]
        
        # Background for text
        cv2.rectangle(frame, (5, 5), (350, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (5, 5), (350, 100), (200, 200, 200), 1)
        
        # Text
        stats_text = [
            f"Frame: {self.frame_count}",
            f"Detections: {n_detections}",
            f"Tracked: {n_tracked}",
            f"Process: {process_time:.1f}ms",
            f"FPS: {fps:.1f}",
        ]
        
        y = 25
        for text in stats_text:
            cv2.putText(frame, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            y += 15
        
        return frame
    
    def benchmark(self, n_frames=100):
        """Run benchmark test"""
        print("\n" + "=" * 60)
        print(f"BENCHMARK: Processing {n_frames} frames")
        print("=" * 60 + "\n")
        
        # Create dummy frame
        dummy_frame = np.ones((640, 640, 3), dtype=np.uint8) * 100
        
        times = []
        
        for i in range(n_frames):
            start = time()
            
            # Create mock detections
            detections = [
                Detection(
                    class_id=6, class_name="motorcycle", confidence=0.9,
                    x1=50 + (i % 5) * 20, y1=50, x2=150 + (i % 5) * 20, y2=150,
                    center_x=100 + (i % 5) * 20, center_y=100,
                    width=100, height=100, is_danger=False,
                ),
            ]
            
            tracked, detections, pt, fps = self.process_frame(dummy_frame)
            times.append(pt)
            
            if (i + 1) % 25 == 0:
                print(f"  Frame {i+1}/{n_frames}: {pt:.2f}ms, {fps:.1f} FPS")
        
        times = np.array(times)
        print(f"\nAverage: {times.mean():.2f}ms ({1000.0/times.mean():.1f} FPS)")
        print(f"Min: {times.min():.2f}ms, Max: {times.max():.2f}ms")
        print(f"Std Dev: {times.std():.2f}ms")
    
    def interactive_test(self, camera_id=0, max_frames=None):
        """Interactive live camera test"""
        print("\n" + "=" * 60)
        print("INTERACTIVE TEST: Camera Feed")
        print("=" * 60)
        print("Controls:")
        print("  Q - Quit")
        print("  P - Pause/Resume")
        print("  S - Save frame")
        print("  B - Show/hide bounding boxes")
        print("=" * 60 + "\n")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Failed to open camera {camera_id}")
            return
        
        paused = False
        show_boxes = True
        frame_count = 0
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        print("End of stream or error")
                        break
                    
                    # Process frame
                    tracked, detections, process_time, fps = self.process_frame(frame)
                    
                    # Draw results
                    if show_boxes:
                        frame = self.draw_results(frame, tracked, detections, process_time, fps)
                    
                    frame_count += 1
                    
                    # Check frame limit
                    if max_frames and frame_count >= max_frames:
                        print(f"Reached max frames: {max_frames}")
                        break
                
                # Display
                cv2.imshow("Traffic Violation Detection - Integrated Test", frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    paused = not paused
                    print(f"{'Paused' if paused else 'Resumed'}")
                elif key == ord('s'):
                    filename = f"frame_{frame_count:04d}.png"
                    cv2.imwrite(filename, frame)
                    print(f"Saved: {filename}")
                elif key == ord('b'):
                    show_boxes = not show_boxes
                    print(f"Boxes {'enabled' if show_boxes else 'disabled'}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
            print(f"\nProcessed {frame_count} frames")
            if frame_count > 0:
                avg_time = sum([self.total_time]) / frame_count if self.frame_count > 0 else 0
                print(f"Average processing time: {avg_time:.2f}ms")
    
    def print_stats(self):
        """Print system statistics"""
        if self.frame_count > 0:
            avg_time = self.total_time / self.frame_count
            print(f"\nSystem Statistics:")
            print(f"  Frames processed: {self.frame_count}")
            print(f"  Total time: {self.total_time:.1f}ms")
            print(f"  Average per frame: {avg_time:.2f}ms")
            print(f"  Average FPS: {1000.0/avg_time:.1f}")


def main():
    parser = argparse.ArgumentParser(description="Integrated Detector + Tracker Test")
    parser.add_argument("--model", default="yolov8n.pt", help="Model path")
    parser.add_argument("--size", type=int, default=640, help="Model input size")
    parser.add_argument("--device", default="auto", help="Device (cpu/cuda/auto)")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument("--benchmark", type=int, default=0, help="Run benchmark (n frames)")
    parser.add_argument("--max-frames", type=int, default=None, help="Max frames to process")
    parser.add_argument("--test", choices=["centroid", "iou", "tracker", "motion", "all"], 
                       default="all", help="Test type")
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════╗
║  Integrated Test System                              ║
║  Detection + Tracking + Motion Analysis              ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        # Initialize system
        system = IntegratedTestSystem(
            model_path=args.model,
            device=args.device,
            model_size=args.size
        )
        
        print("\n✅ System initialized successfully!\n")
        
        # Run tests
        if args.benchmark > 0:
            system.benchmark(n_frames=args.benchmark)
        else:
            try:
                system.interactive_test(camera_id=args.camera, max_frames=args.max_frames)
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
        
        system.print_stats()
        
        print("\n✅ Test completed")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
