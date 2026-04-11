#!/usr/bin/env python3
"""
License Plate OCR Demo
Real-time plate detection, tracking, and text extraction
"""

import sys
from pathlib import Path
import cv2
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    Detector,
    VehicleTracker,
    PlateOCR,
)


class PlateReaderSystem:
    """Integrated plate detection, tracking, and OCR system"""
    
    def __init__(self, model_path="yolov8n.onnx", use_gpu=True, camera_id=0):
        """Initialize system components"""
        print("Initializing Plate Reader System...")
        
        # Initialize detector
        try:
            print("  Loading detector...")
            self.detector = Detector(model_path, device="cuda" if use_gpu else "cpu")
            print("  ✓ Detector loaded")
        except Exception as e:
            print(f"  ✗ Failed to load detector: {e}")
            raise
        
        # Initialize tracker
        try:
            print("  Loading tracker...")
            self.tracker = VehicleTracker(max_age=30, n_init=3)
            print("  ✓ Tracker loaded")
        except Exception as e:
            print(f"  ✗ Failed to load tracker: {e}")
            raise
        
        # Initialize OCR (lazy loaded)
        try:
            print("  Initializing OCR (lazy)...")
            self.ocr = PlateOCR(use_gpu=use_gpu)
            print("  ✓ OCR ready (lazy-loaded)")
        except Exception as e:
            print(f"  ✗ Failed to initialize OCR: {e}")
            raise
        
        self.camera_id = camera_id
        self.frame_count = 0
        self.plate_detections = {}  # track_id → PlateResult
    
    def process_frame(self, frame):
        """Process single frame"""
        self.frame_count += 1
        
        # Detect objects
        detections = self.detector.infer(frame)
        
        # Track objects
        tracked = self.tracker.update(detections, frame)
        
        # Extract plate numbers for motorcycles/vehicles
        for track in tracked:
            if track.class_name in ['motorcycle', 'vehicle']:
                # Try to extract plate
                bbox = (track.x1, track.y1, track.x2, track.y2)
                plate_result = self.ocr.read_plate(frame, bbox)
                
                if plate_result is not None:
                    self.plate_detections[track.track_id] = plate_result
        
        return frame, detections, tracked
    
    def draw_results(self, frame, detections, tracked):
        """Draw detection, tracking, and plate info"""
        
        # Draw detections
        if detections:
            frame = self.detector.draw_detections(frame, detections)
        
        # Draw tracked objects and plate info
        for track in tracked:
            if track.class_name not in ['motorcycle', 'vehicle']:
                continue
            
            # Draw bounding box
            cv2.rectangle(frame, (track.x1, track.y1), (track.x2, track.y2),
                         (0, 255, 0), 2)
            
            # Draw track ID
            cv2.putText(frame, f"ID:{track.track_id}", (track.x1, track.y1 - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw plate info if available
            if track.track_id in self.plate_detections:
                plate = self.plate_detections[track.track_id]
                
                # Color based on validity
                color = (0, 255, 0) if plate.is_valid_indian_format else (0, 0, 255)
                
                # Draw plate text
                text = f"Plate: {plate.cleaned_text}"
                cv2.putText(frame, text, (track.x1, track.y2 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Draw confidence
                conf_text = f"Conf: {plate.confidence:.2f}"
                cv2.putText(frame, conf_text, (track.x1, track.y2 + 45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                # Draw SRGAN flag
                if plate.needs_srgan:
                    cv2.putText(frame, "SRGAN", (track.x1, track.y2 + 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
        
        # Draw stats
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (5, 5), (300, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (5, 5), (300, 100), (200, 200, 200), 1)
        
        stats_text = [
            f"Frame: {self.frame_count}",
            f"Tracked: {len(tracked)}",
            f"Plates: {len(self.plate_detections)}",
        ]
        
        y = 25
        for text in stats_text:
            cv2.putText(frame, text, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                       (0, 255, 0), 1)
            y += 15
        
        return frame
    
    def run_camera(self, max_frames=None):
        """Run on camera feed"""
        print(f"\nStarting camera feed (camera {self.camera_id})...")
        print("Controls: Q=quit, S=screenshot, P=pause\n")
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            return
        
        paused = False
        frame_count = 0
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame, detections, tracked = self.process_frame(frame)
                    frame = self.draw_results(frame, detections, tracked)
                    
                    frame_count += 1
                    
                    if max_frames and frame_count >= max_frames:
                        break
                
                cv2.imshow("License Plate Reader", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    paused = not paused
                    print(f"{'Paused' if paused else 'Resumed'}")
                elif key == ord('s'):
                    filename = f"plate_frame_{self.frame_count:04d}.png"
                    cv2.imwrite(filename, frame)
                    print(f"Saved: {filename}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def run_video(self, video_path, max_frames=None):
        """Run on video file"""
        print(f"\nProcessing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Failed to open video: {video_path}")
            return
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame, detections, tracked = self.process_frame(frame)
                frame = self.draw_results(frame, detections, tracked)
                
                cv2.imshow("License Plate Reader", frame)
                
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"  Frame {frame_count}: {len(tracked)} objects tracked")
                
                if max_frames and frame_count >= max_frames:
                    break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        print(f"Processed {frame_count} frames")
        print(f"Plates detected: {len(self.plate_detections)}")


def main():
    parser = argparse.ArgumentParser(description="License Plate OCR Demo")
    parser.add_argument("--model", default="yolov8n.onnx", help="Model path")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument("--video", help="Video file path")
    parser.add_argument("--cpu", action="store_true", help="Use CPU only")
    parser.add_argument("--max-frames", type=int, help="Max frames to process")
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════╗
║  License Plate Reader - OCR Demo                     ║
║  Real-time Vehicle & Plate Detection                 ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        system = PlateReaderSystem(
            model_path=args.model,
            use_gpu=not args.cpu,
            camera_id=args.camera
        )
        
        if args.video:
            system.run_video(args.video, max_frames=args.max_frames)
        else:
            system.run_camera(max_frames=args.max_frames)
        
        print("\n✅ Demo completed")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
