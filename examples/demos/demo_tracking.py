#!/usr/bin/env python3
"""
Multi-Object Tracking Demo
Shows real-time vehicle tracking with motion analysis
"""

import sys
import time
import argparse
from pathlib import Path

import cv2
import numpy as np

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    Detector,
    VehicleTracker,
    get_platform_config,
    print_platform_summary,
    print_tracked_objects,
)


class TrackedVisionSystem:
    """Real-time detection + tracking system"""
    
    def __init__(
        self,
        model_path: str = None,
        camera_id: int = 0,
        inference_size: int = None,
        max_age: int = 30,
        n_init: int = 3,
    ):
        """Initialize detection + tracking"""
        
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
        
        # Initialize tracker
        self.tracker = VehicleTracker(max_age=max_age, n_init=n_init)
        
        self.camera_id = camera_id
        self.frame_count = 0
        self.times = []
        
        print(f"\n✅ System initialized with detection + tracking")
    
    def draw_tracked_objects(
        self,
        frame: np.ndarray,
        tracked_objects: list,
        show_trajectory: bool = True,
    ) -> np.ndarray:
        """Draw tracked objects with info"""
        
        annotated = frame.copy()
        
        for obj in tracked_objects:
            # Get color (class-based)
            from backend.core import CLASS_COLORS
            color = CLASS_COLORS.get(obj.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(
                annotated,
                (obj.x1, obj.y1),
                (obj.x2, obj.y2),
                color,
                2,
            )
            
            # Draw track ID and info
            label = f"ID:{obj.track_id} {obj.class_name}"
            
            # Get motion info
            speed = self.tracker.estimate_speed(obj.track_id)
            direction = self.tracker.get_direction_vector(obj.track_id)
            
            if speed is not None:
                label += f" {speed:.1f}km/h"
            
            if direction is not None:
                dx, dy = direction
                angle = self.tracker.calculate_motion_angle(obj.track_id)
                if angle is not None:
                    label += f" @{angle:.0f}°"
            
            # Draw label
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
            )
            
            cv2.rectangle(
                annotated,
                (obj.x1, obj.y1 - label_size[1] - baseline),
                (obj.x1 + label_size[0], obj.y1),
                color,
                -1,
            )
            
            cv2.putText(
                annotated,
                label,
                (obj.x1, obj.y1 - baseline),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )
            
            # Draw trajectory
            if show_trajectory:
                history = self.tracker.get_track_history(obj.track_id, max_frames=15)
                if len(history) > 1:
                    for i in range(len(history) - 1):
                        pt1 = history[i]
                        pt2 = history[i + 1]
                        cv2.line(annotated, pt1, pt2, color, 1)
            
            # Draw center point
            cv2.circle(annotated, (obj.center_x, obj.center_y), 3, color, -1)
        
        return annotated
    
    def run(self, max_frames: int = None, save_video: bool = False):
        """Run real-time detection + tracking"""
        
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
        
        # Video writer
        writer = None
        if save_video:
            output_path = f"tracking_{int(time.time())}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps_in, (width, height))
            print(f"💾 Saving to: {output_path}")
        
        print("\n🚀 Starting detection + tracking...")
        print("   Press 'q' to quit, 's' for screenshot, 't' to toggle trajectory\n")
        
        show_trajectory = True
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                self.frame_count += 1
                
                # Detect
                start = time.time()
                detections = self.detector.infer(frame)
                detect_time = (time.time() - start) * 1000
                
                # Track
                start_track = time.time()
                tracked = self.tracker.update(detections, frame)
                track_time = (time.time() - start_track) * 1000
                total_time = detect_time + track_time
                
                self.times.append(total_time)
                
                # Draw
                annotated = self.draw_tracked_objects(
                    frame, tracked, show_trajectory=show_trajectory
                )
                
                # Info overlay
                info_lines = [
                    f"Frame: {self.frame_count}",
                    f"Detections: {len(detections)}",
                    f"Tracked: {len(tracked)}",
                    f"Detect: {detect_time:.1f}ms",
                    f"Track: {track_time:.1f}ms",
                ]
                
                if len(self.times) > 0:
                    avg_fps = 1000.0 / np.mean(self.times[-30:])
                    info_lines.insert(0, f"FPS: {avg_fps:.1f}")
                
                y_pos = 30
                for line in info_lines:
                    cv2.putText(
                        annotated,
                        line,
                        (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        1,
                    )
                    y_pos += 25
                
                # Display
                cv2.imshow("Detection + Tracking", annotated)
                
                if writer:
                    writer.write(annotated)
                
                # Print periodically
                if self.frame_count % 30 == 0:
                    print(f"\n[Frame {self.frame_count}]")
                    print(f"  Detections: {len(detections)}")
                    print(f"  Tracked: {len(tracked)}")
                    if tracked:
                        print("  Active tracks:")
                        for obj in tracked[:3]:
                            speed = self.tracker.estimate_speed(obj.track_id)
                            speed_str = f" ({speed:.1f}km/h)" if speed else ""
                            print(f"    - ID {obj.track_id}: {obj.class_name}{speed_str}")
                
                if max_frames and self.frame_count >= max_frames:
                    break
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    shot_path = f"tracking_shot_{int(time.time())}.jpg"
                    cv2.imwrite(shot_path, annotated)
                    print(f"📸 Saved: {shot_path}")
                elif key == ord('t'):
                    show_trajectory = not show_trajectory
                    print(f"Trajectory: {'ON' if show_trajectory else 'OFF'}")
        
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            
            self._print_summary()
    
    def _print_summary(self):
        """Print session summary"""
        print("\n" + "=" * 60)
        print("DETECTION + TRACKING SESSION SUMMARY")
        print("=" * 60)
        print(f"Total frames: {self.frame_count}")
        if self.times:
            print(f"Avg total time: {np.mean(self.times):.2f} ms")
            print(f"Avg FPS: {1000.0 / np.mean(self.times):.1f}")
        print(f"Max active tracks: {self.tracker.get_stats()['active_tracks']}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time Detection + Tracking"
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument("--model", type=str, default=None, help="Model path")
    parser.add_argument("--size", type=int, default=None, help="Inference size")
    parser.add_argument("--max-frames", type=int, default=None, help="Max frames")
    parser.add_argument("--save-video", action="store_true", help="Save output")
    parser.add_argument("--max-age", type=int, default=30, help="Max track age")
    parser.add_argument("--n-init", type=int, default=3, help="N init frames")
    
    args = parser.parse_args()
    
    system = TrackedVisionSystem(
        model_path=args.model,
        camera_id=args.camera,
        inference_size=args.size,
        max_age=args.max_age,
        n_init=args.n_init,
    )
    
    system.run(max_frames=args.max_frames, save_video=args.save_video)


if __name__ == "__main__":
    main()
