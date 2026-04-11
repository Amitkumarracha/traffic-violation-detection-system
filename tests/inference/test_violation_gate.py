#!/usr/bin/env python3
"""
Violation Gate Testing
Tests the 4-stage violation confirmation system
"""

import sys
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime
from time import sleep

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import (
    Detector,
    VehicleTracker,
    Detection,
    ViolationGate,
    ConfirmedViolation,
)


def test_violation_gate_stages():
    """Test each stage of the violation gate independently"""
    print("\n" + "=" * 70)
    print("TEST 1: Stage-by-Stage Rejection Testing")
    print("=" * 70 + "\n")
    
    gate = ViolationGate(
        cooldown_seconds=30,
        consecutive_frames_needed=3,
        min_speed_kmh=3.0,
        min_confidence=0.75
    )
    
    # Mock tracker for speed estimation
    class MockTracker:
        def estimate_speed(self, track_id, fps=30, pixels_per_meter=50):
            # Simulate different speeds
            if track_id == 1:
                return 0.5  # Too slow, will fail stage 3
            elif track_id == 2:
                return 25.0  # Good speed
            elif track_id == 3:
                return 15.0  # Good speed
            return 10.0
    
    mock_tracker = MockTracker()
    
    # Test Stage 1: Low confidence
    print("Stage 1 - Low Confidence Rejection:")
    print("-" * 70)
    dummy_frame = np.ones((640, 640, 3), dtype=np.uint8) * 100
    
    low_conf_detection = Detection(
        class_id=1, class_name="without_helmet", confidence=0.60,  # Below 0.75
        x1=100, y1=100, x2=200, y2=200,
        center_x=150, center_y=150,
        width=100, height=100, is_danger=True,
    )
    
    # Simulate tracker with track_id=1
    class MockTrackedObj:
        def __init__(self, detection, track_id):
            self.track_id = track_id
            self.class_id = detection.class_id
            self.class_name = detection.class_name
            self.confidence = detection.confidence
            self.x1, self.y1 = detection.x1, detection.y1
            self.x2, self.y2 = detection.x2, detection.y2
            self.center_x, self.center_y = detection.center_x, detection.center_y
            self.is_confirmed = False
            self.age = 1
    
    tracked = [MockTrackedObj(low_conf_detection, track_id=100)]
    violations = gate.process(tracked, mock_tracker)
    
    stats = gate.get_stats()
    print(f"Violations confirmed: {stats['total_violations_confirmed']}")
    print(f"Stage 1 rejections: {stats['violations_rejected_stage1']}")
    print(f"Expected: 1 rejection at stage 1\n")
    
    # Test Stage 2: Insufficient consecutive frames
    print("Stage 2 - Insufficient Consecutive Frames:")
    print("-" * 70)
    gate.reset()
    
    good_conf_detection = Detection(
        class_id=1, class_name="without_helmet", confidence=0.85,  # Good
        x1=100, y1=100, x2=200, y2=200,
        center_x=150, center_y=150,
        width=100, height=100, is_danger=True,
    )
    
    tracked = [MockTrackedObj(good_conf_detection, track_id=200)]
    
    # Process 2 times (need 3)
    for i in range(2):
        violations = gate.process(tracked, mock_tracker)
        print(f"  Frame {i+1}: {len(violations)} violations confirmed")
    
    stats = gate.get_stats()
    print(f"Stage 2 rejections: {stats['violations_rejected_stage2']}")
    print(f"Expected: 1 rejection (only 2 consecutive, need 3)\n")
    
    # Test Stage 3: Vehicle too slow
    print("Stage 3 - Vehicle Too Slow (Stationary):")
    print("-" * 70)
    gate.reset()
    
    # Process 3 times with track_id=1 (speed=0.5 km/h from mock_tracker)
    tracked = [MockTrackedObj(good_conf_detection, track_id=1)]
    for i in range(3):
        violations = gate.process(tracked, mock_tracker)
        print(f"  Frame {i+1}: {len(violations)} violations confirmed")
    
    stats = gate.get_stats()
    print(f"Stage 3 rejections: {stats['violations_rejected_stage3']}")
    print(f"Expected: 1 rejection (speed 0.5 km/h < 3.0 km/h)\n")
    
    # Test Stage 4: Cooldown
    print("Stage 4 - Cooldown Enforcement:")
    print("-" * 70)
    gate.reset()
    
    # Track_id=2 has good speed (25 km/h)
    tracked = [MockTrackedObj(good_conf_detection, track_id=2)]
    
    # First 3 frames - should confirm
    for i in range(3):
        violations = gate.process(tracked, mock_tracker)
        print(f"  Frame {i+1}: {len(violations)} violations confirmed")
    
    # Frame 4 - should be rejected by cooldown
    violations = gate.process(tracked, mock_tracker)
    print(f"  Frame 4: {len(violations)} violations confirmed")
    
    stats = gate.get_stats()
    print(f"Stage 4 rejections: {stats['violations_rejected_stage4']}")
    print(f"Expected: 1 rejection (cooldown active)\n")


def test_violation_gate_full_scenario():
    """Test complete violation detection scenario"""
    print("\n" + "=" * 70)
    print("TEST 2: Full Violation Detection Scenario")
    print("=" * 70 + "\n")
    
    gate = ViolationGate(
        cooldown_seconds=30,
        consecutive_frames_needed=3,
        min_speed_kmh=3.0,
        min_confidence=0.75
    )
    
    class MockTracker:
        def estimate_speed(self, track_id, fps=30, pixels_per_meter=50):
            # Different speeds for different vehicles
            speeds = {
                1: 45.0,   # High speed violation
                2: 55.0,   # High speed violation
                3: 2.0,    # Parked
            }
            return speeds.get(track_id, 10.0)
    
    mock_tracker = MockTracker()
    
    class MockTrackedObj:
        def __init__(self, track_id, class_name, confidence):
            self.track_id = track_id
            self.class_id = 1
            self.class_name = class_name
            self.confidence = confidence
            self.x1, self.y1 = 100, 100
            self.x2, self.y2 = 200, 200
            self.center_x, self.center_y = 150, 150
            self.is_confirmed = True
            self.age = 5
    
    # Simulate 10 frames of detection
    print("Processing 10 frames of detection...\n")
    
    for frame_num in range(1, 11):
        print(f"Frame {frame_num}:")
        
        tracked = [
            MockTrackedObj(1, "without_helmet", 0.92),
            MockTrackedObj(2, "triple_ride", 0.88),
            MockTrackedObj(3, "without_helmet", 0.80),  # Parked vehicle
        ]
        
        violations = gate.process(tracked, mock_tracker)
        
        for v in violations:
            print(f"  ✓ CONFIRMED: {v}")
        
        if not violations:
            print(f"  (No violations confirmed this frame)")
        
        print()
    
    # Print final statistics
    gate.print_stats()


def test_confirmed_violation_dataclass():
    """Test ConfirmedViolation dataclass"""
    print("\n" + "=" * 70)
    print("TEST 3: ConfirmedViolation Dataclass")
    print("=" * 70 + "\n")
    
    violation = ConfirmedViolation(
        track_id=42,
        violation_type="without_helmet",
        confidence=0.95,
        bbox=(100, 100, 200, 200),
        timestamp=datetime.now(),
        frame_number=512,
        speed_kmh=62.5
    )
    
    print(f"Violation Object: {violation}")
    print(f"\nDetails:")
    print(f"  Track ID: {violation.track_id}")
    print(f"  Type: {violation.violation_type}")
    print(f"  Confidence: {violation.confidence:.3f}")
    print(f"  Bounding Box: {violation.bbox}")
    print(f"  Speed: {violation.speed_kmh:.1f} km/h")
    print(f"  Frame: {violation.frame_number}")
    print(f"  Timestamp: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")


def test_gate_statistics():
    """Test gate statistics calculation"""
    print("\n" + "=" * 70)
    print("TEST 4: Gate Statistics")
    print("=" * 70 + "\n")
    
    gate = ViolationGate()
    
    # Manually set statistics to test reporting
    gate.total_violations_confirmed = 157
    gate.violations_rejected_stage1 = 342
    gate.violations_rejected_stage2 = 185
    gate.violations_rejected_stage3 = 1204
    gate.violations_rejected_stage4 = 89
    
    print("Simulated Results from 2000-frame video:\n")
    
    stats = gate.get_stats()
    
    print(f"Total Candidates: {stats['total_candidates']}")
    print(f"Confirmed Violations: {stats['total_violations_confirmed']}")
    print(f"Total Rejected: {stats['total_rejected']}")
    print(f"\nStage-wise Rejections:")
    print(f"  Stage 1: {stats['violations_rejected_stage1']} ({stats['stage1_rejection_rate']:.1%})")
    print(f"  Stage 2: {stats['violations_rejected_stage2']} ({stats['stage2_rejection_rate']:.1%})")
    print(f"  Stage 3: {stats['violations_rejected_stage3']} ({stats['stage3_rejection_rate']:.1%})")
    print(f"  Stage 4: {stats['violations_rejected_stage4']} ({stats['stage4_rejection_rate']:.1%})")
    print(f"\nFalse Positive Reduction Rate: {stats['false_positive_reduction_rate']:.1%}")
    
    gate.print_stats()


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════╗
║  Violation Gate Testing                              ║
║  4-Stage False Positive Prevention System             ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        test_violation_gate_stages()
        test_violation_gate_full_scenario()
        test_confirmed_violation_dataclass()
        test_gate_statistics()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
