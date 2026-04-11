#!/usr/bin/env python3
"""
Tracker Testing & Demo Script
Shows VehicleTracker functionality
"""

import sys
from pathlib import Path
import numpy as np
import cv2

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    Detector,
    VehicleTracker,
    Detection,
    compute_centroid,
    compute_iou,
    print_tracked_objects,
)


def test_compute_centroid():
    """Test centroid computation"""
    print("\n" + "=" * 60)
    print("TEST 1: Compute Centroid")
    print("=" * 60 + "\n")
    
    # Test case
    x1, y1, x2, y2 = 100, 50, 300, 250
    cx, cy = compute_centroid(x1, y1, x2, y2)
    
    print(f"Bounding box: ({x1}, {y1}) - ({x2}, {y2})")
    print(f"Centroid: ({cx}, {cy})")
    
    expected_cx = (100 + 300) // 2
    expected_cy = (50 + 250) // 2
    
    assert cx == expected_cx and cy == expected_cy, "Centroid calculation failed"
    print("✅ Centroid calculation correct!")


def test_compute_iou():
    """Test IoU computation"""
    print("\n" + "=" * 60)
    print("TEST 2: Compute IoU")
    print("=" * 60 + "\n")
    
    # Identical boxes
    box1 = (0, 0, 100, 100)
    box2 = (0, 0, 100, 100)
    iou = compute_iou(box1, box2)
    print(f"Identical boxes IoU: {iou}")
    assert abs(iou - 1.0) < 0.001, "IoU should be 1.0 for identical boxes"
    
    # No overlap
    box1 = (0, 0, 100, 100)
    box2 = (200, 200, 300, 300)
    iou = compute_iou(box1, box2)
    print(f"No overlap IoU: {iou}")
    assert iou == 0.0, "IoU should be 0.0 for non-overlapping boxes"
    
    # Partial overlap
    box1 = (0, 0, 100, 100)
    box2 = (50, 50, 150, 150)
    iou = compute_iou(box1, box2)
    print(f"Partial overlap IoU: {iou}")
    assert 0 < iou < 1, "IoU should be between 0 and 1 for partial overlap"
    
    print("✅ IoU calculations correct!")


def test_tracker_initialization():
    """Test tracker initialization"""
    print("\n" + "=" * 60)
    print("TEST 3: Tracker Initialization")
    print("=" * 60 + "\n")
    
    try:
        tracker = VehicleTracker(max_age=30, n_init=3)
        tracker.print_stats()
        print("✅ Tracker initialized successfully!")
        return tracker
    except Exception as e:
        print(f"❌ Failed to initialize tracker: {e}")
        return None


def test_tracker_update(tracker):
    """Test tracker update"""
    print("\n" + "=" * 60)
    print("TEST 4: Tracker Update")
    print("=" * 60 + "\n")
    
    if not tracker:
        print("⚠️ Skipping (tracker not available)")
        return
    
    # Create dummy frame
    dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    
    # Create mock detection
    mock_detection = Detection(
        class_id=6,
        class_name="motorcycle",
        confidence=0.95,
        x1=100,
        y1=100,
        x2=200,
        y2=250,
        center_x=150,
        center_y=175,
        width=100,
        height=150,
        is_danger=False,
    )
    
    # Update tracker
    tracked = tracker.update([mock_detection], dummy_frame)
    
    print(f"Tracked objects: {len(tracked)}")
    print_tracked_objects(tracked)
    
    if tracked:
        print("✅ Tracker update successful!")
    else:
        print("⚠️ No confirmed tracks (need more frames)")


def test_tracker_motion_analysis(tracker):
    """Test motion analysis"""
    print("\n" + "=" * 60)
    print("TEST 5: Motion Analysis")
    print("=" * 60 + "\n")
    
    if not tracker:
        print("⚠️ Skipping (tracker not available)")
        return
    
    dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    
    # Simulate motion over frames
    print("Simulating vehicle motion over 15 frames...\n")
    
    for frame_idx in range(15):
        # Vehicle moving diagonally
        x_offset = frame_idx * 3
        y_offset = frame_idx * 2
        
        detection = Detection(
            class_id=7,
            class_name="vehicle",
            confidence=0.92,
            x1=100 + x_offset,
            y1=100 + y_offset,
            x2=200 + x_offset,
            y2=250 + y_offset,
            center_x=150 + x_offset,
            center_y=175 + y_offset,
            width=100,
            height=150,
            is_danger=False,
        )
        
        tracked = tracker.update([detection], dummy_frame)
    
    if tracked:
        track_id = tracked[0].track_id
        
        print(f"Track ID: {track_id}")
        print(f"Confirmed: {tracked[0].is_confirmed}")
        
        # Get history
        history = tracker.get_track_history(track_id)
        print(f"\nTrack history length: {len(history)}")
        if history:
            print(f"  First position: {history[0]}")
            print(f"  Last position: {history[-1]}")
        
        # Estimate speed
        speed = tracker.estimate_speed(track_id, fps=30, pixels_per_meter=50)
        if speed is not None:
            print(f"\nEstimated speed: {speed:.2f} km/h")
        
        # Get direction
        direction = tracker.get_direction_vector(track_id)
        if direction is not None:
            dx, dy = direction
            print(f"Direction vector: ({dx:.2f}, {dy:.2f})")
            angle = tracker.calculate_motion_angle(track_id)
            print(f"Motion angle: {angle:.1f}°")
        
        # Check if moving
        is_moving = tracker.is_moving(track_id, min_velocity=1.0)
        print(f"Is moving: {is_moving}")
        
        # Predict position
        pred_pos = tracker.predict_position(track_id, frames_ahead=5)
        if pred_pos:
            print(f"Predicted position (5 frames ahead): {pred_pos}")
        
        print("\n✅ Motion analysis complete!")
    else:
        print("⚠️ No tracked object available")


def test_multiple_tracks(tracker):
    """Test tracking multiple objects"""
    print("\n" + "=" * 60)
    print("TEST 6: Multiple Object Tracking")
    print("=" * 60 + "\n")
    
    if not tracker:
        print("⚠️ Skipping (tracker not available)")
        return
    
    dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    
    print("Simulating 3 vehicles over 10 frames...\n")
    
    for frame_idx in range(10):
        detections = [
            # Vehicle 1 - moving right
            Detection(
                class_id=7, class_name="vehicle", confidence=0.9,
                x1=50 + frame_idx * 5, y1=50,
                x2=150 + frame_idx * 5, y2=150,
                center_x=100 + frame_idx * 5, center_y=100,
                width=100, height=100, is_danger=False,
            ),
            # Vehicle 2 - moving down
            Detection(
                class_id=7, class_name="vehicle", confidence=0.88,
                x1=300, y1=100 + frame_idx * 4,
                x2=400, y2=200 + frame_idx * 4,
                center_x=350, center_y=150 + frame_idx * 4,
                width=100, height=100, is_danger=False,
            ),
            # Motorcycle - stationary
            Detection(
                class_id=6, class_name="motorcycle", confidence=0.93,
                x1=450, y1=300,
                x2=550, y2=400,
                center_x=500, center_y=350,
                width=100, height=100, is_danger=False,
            ),
        ]
        
        tracked = tracker.update(detections, dummy_frame)
    
    # Print final state
    print(f"Final tracked objects: {len(tracked)}")
    print_tracked_objects(tracked)
    
    # Analyze each track
    stats = tracker.get_stats()
    print(f"\nActive tracks: {stats['active_tracks']}")
    
    print("✅ Multiple object tracking complete!")


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════╗
║  Vehicle Tracker Testing                             ║
║  Traffic Violation Detection System                  ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        test_compute_centroid()
        test_compute_iou()
        
        tracker = test_tracker_initialization()
        if tracker:
            test_tracker_update(tracker)
            test_tracker_motion_analysis(tracker)
            test_multiple_tracks(tracker)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
