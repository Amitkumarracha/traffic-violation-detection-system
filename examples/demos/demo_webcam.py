#!/usr/bin/env python3
"""
Real-time Webcam Detection Demo
Shows live traffic violation detection from webcam
"""

import sys
import time
import argparse
from pathlib import Path

import cv2
import numpy as np

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core import Detector, print_detections, get_danger_detections
from backend.config import get_platform_config, print_platform_summary


class WebcamDetector:
    """Real-time webcam detection"""
    
    def __init__(
        self,
        model_path: str = None,
        camera_id: int = 0,
        inference_size: int = None,
        show_fps: bool = True,
        save_video: bool = False,
    ):
        self.camera_id = camera_id
        self.show_fps = show_fps
        self.save_video = save_video
        
        # Load config
        config = get_platform_config(model_path)
        print_platform_summary()
        
        # Initialize detector
        self.detector = Detector(
            model_path=config.model_path,
            inference_size=inference_size or config.inference_size,
            num_threads=config.num_threads,
            confidence_threshold=config.confidence_threshold,
        )
        
        self.detector.print_stats()
        
        # Video properties
        self.frame_count = 0
        self.violation_count = 0
        self.times = []
    
    def run(self, max_frames: int = None):
        """Run real-time detection"""
        
        # Open camera
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"❌ Cannot open camera {self.camera_id}")
            return
        
        # Get properties
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"\n🎥 Camera opened: {width}x{height} @ {fps_in:.1f} FPS")
        
        # Video writer (optional)
        writer = None
        if self.save_video:
            output_path = f"detections_{int(time.time())}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(
                output_path,
                fourcc,
                fps_in,
                (width, height),
            )
            print(f"💾 Saving to: {output_path}")
        
        print("\n🚀 Starting real-time detection...")
        print("   Press 'q' to quit, 's' to screenshot\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("End of stream")
                    break
                
                self.frame_count += 1
                
                # Inference
                start = time.time()
                detections = self.detector.infer(frame)
                infer_time = (time.time() - start) * 1000
                self.times.append(infer_time)
                
                # Draw
                annotated = self.detector.draw_detections(frame, detections)
                
                # Get danger detections
                danger = get_danger_detections(detections)
                self.violation_count += len(danger)
                
                # Add info overlay
                info_lines = [
                    f"Frame: {self.frame_count}",
                    f"Detections: {len(detections)}",
                    f"Violations: {len(danger)}",
                    f"Infer: {infer_time:.1f}ms",
                ]
                
                if self.show_fps and len(self.times) > 0:
                    avg_fps = 1000.0 / np.mean(self.times[-30:])
                    info_lines.insert(0, f"FPS: {avg_fps:.1f}")
                
                # Draw info
                y_pos = 30
                for line in info_lines:
                    color = (0, 255, 0)
                    if "Violations" in line and len(danger) > 0:
                        color = (0, 0, 255)  # Red if violations
                    
                    cv2.putText(
                        annotated,
                        line,
                        (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                    )
                    y_pos += 30
                
                # Display
                cv2.imshow("Traffic Violation Detection", annotated)
                
                # Save frame
                if writer:
                    writer.write(annotated)
                
                # Print detections periodically
                if self.frame_count % 30 == 0:
                    print(f"\n[Frame {self.frame_count}] {len(detections)} detections")
                    if danger:
                        print(f"⚠️ {len(danger)} violations:")
                        for det in danger:
                            print(f"   - {det.class_name} ({det.confidence:.2f})")
                
                # Check for max frames
                if max_frames and self.frame_count >= max_frames:
                    print(f"\nReached max frames ({max_frames})")
                    break
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord('s'):
                    shot_path = f"screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(shot_path, annotated)
                    print(f"📸 Screenshot saved: {shot_path}")
        
        finally:
            # Cleanup
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            
            # Summary
            self._print_summary()
    
    def _print_summary(self):
        """Print session summary"""
        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Frames processed: {self.frame_count}")
        print(f"Total violations: {self.violation_count}")
        if self.times:
            print(f"Avg inference: {np.mean(self.times):.2f} ms")
            print(f"Min inference: {np.min(self.times):.2f} ms")
            print(f"Max inference: {np.max(self.times):.2f} ms")
            print(f"Avg FPS: {1000.0 / np.mean(self.times):.1f}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time Traffic Violation Detection"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera ID (default: 0)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to ONNX model (default: from config)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Inference size (default: from config)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Max frames to process",
    )
    parser.add_argument(
        "--save-video",
        action="store_true",
        help="Save output video",
    )
    parser.add_argument(
        "--no-fps",
        action="store_true",
        help="Don't show FPS",
    )
    
    args = parser.parse_args()
    
    detector = WebcamDetector(
        model_path=args.model,
        camera_id=args.camera,
        inference_size=args.size,
        show_fps=not args.no_fps,
        save_video=args.save_video,
    )
    
    detector.run(max_frames=args.max_frames)


if __name__ == "__main__":
    main()
