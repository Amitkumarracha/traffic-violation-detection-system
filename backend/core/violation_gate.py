"""
Violation Gate - 4-Stage Confirmation System
Prevents false positives through multi-stage validation before reporting violations.

Stages:
1. Confidence check: YOLO confidence > 0.75
2. Temporal consistency: Same violation class in 3 consecutive frames
3. Motion check: Vehicle speed > 3 km/h (not stationary)
4. Cooldown: Same track_id cannot trigger again for 30 seconds
"""

from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from typing import List, Dict, Tuple, Optional
import logging

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class ConfirmedViolation:
    """Represents a violation that passed all 4 confirmation stages"""
    
    track_id: int
    violation_type: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    timestamp: datetime
    frame_number: int
    speed_kmh: Optional[float] = None  # Vehicle speed at violation time
    
    def __str__(self):
        return (
            f"Violation(ID:{self.track_id}, Type:{self.violation_type}, "
            f"Conf:{self.confidence:.2f}, Speed:{self.speed_kmh:.1f}km/h, "
            f"Frame:{self.frame_number})"
        )


class ViolationGate:
    """
    4-stage violation confirmation gate.
    
    Only violations that pass ALL stages are reported:
    - Stage 1: High confidence (> 0.75)
    - Stage 2: Temporal consistency (3 consecutive frames with same violation)
    - Stage 3: Motion (vehicle moving > 3 km/h, not parked)
    - Stage 4: Cooldown (30 second minimum between violations per vehicle)
    """
    
    def __init__(self, 
                 cooldown_seconds: int = 30,
                 consecutive_frames_needed: int = 3,
                 min_speed_kmh: float = 3.0,
                 min_confidence: float = 0.75):
        """
        Initialize violation gate.
        
        Args:
            cooldown_seconds: Minimum seconds between violations for same track_id
            consecutive_frames_needed: Number of consecutive frames for stage 2
            min_speed_kmh: Minimum vehicle speed to pass stage 3 (filters parked vehicles)
            min_confidence: Minimum YOLO detection confidence for stage 1
        """
        
        # Frame history tracking: track_id -> deque of (violation_class, frame_number)
        self.frame_buffer: Dict[int, deque] = {}
        
        # Cooldown tracking: track_id -> timestamp of last confirmed violation
        self.confirmed_violations: Dict[int, datetime] = {}
        
        # Configuration parameters
        self.COOLDOWN_SECONDS = cooldown_seconds
        self.CONSECUTIVE_FRAMES_NEEDED = consecutive_frames_needed
        self.MIN_SPEED_KMH = min_speed_kmh
        self.MIN_CONFIDENCE = min_confidence
        
        # Violation classes that trigger the gate
        self.VIOLATION_CLASSES = [
            'without_helmet',
            'triple_ride',
            'traffic_violation'
        ]
        
        # Statistics tracking
        self.total_violations_confirmed = 0
        self.violations_rejected_stage1 = 0
        self.violations_rejected_stage2 = 0
        self.violations_rejected_stage3 = 0
        self.violations_rejected_stage4 = 0
        self.frame_number = 0
    
    def process(self, tracked_objects: list, tracker) -> List[ConfirmedViolation]:
        """
        Process tracked objects through 4-stage violation gate.
        
        Args:
            tracked_objects: List of TrackedObject from VehicleTracker.update()
            tracker: VehicleTracker instance (for speed estimation)
        
        Returns:
            List of ConfirmedViolation objects that passed all 4 stages
        """
        
        self.frame_number += 1
        confirmed = []
        
        for track in tracked_objects:
            # Skip non-violation classes
            if track.class_name not in self.VIOLATION_CLASSES:
                continue
            
            # ============================================================
            # STAGE 1: CONFIDENCE CHECK
            # ============================================================
            if track.confidence <= self.MIN_CONFIDENCE:
                self.violations_rejected_stage1 += 1
                logger.debug(
                    f"Stage 1 REJECT: track_{track.track_id} "
                    f"confidence {track.confidence:.3f} <= {self.MIN_CONFIDENCE}"
                )
                continue
            
            # ============================================================
            # STAGE 2: TEMPORAL CONSISTENCY
            # ============================================================
            
            # Initialize frame buffer for this track if needed
            if track.track_id not in self.frame_buffer:
                self.frame_buffer[track.track_id] = deque(maxlen=10)
            
            # Add current detection to history
            self.frame_buffer[track.track_id].append(
                (track.class_name, self.frame_number)
            )
            
            # Get recent detections
            recent = list(self.frame_buffer[track.track_id])
            
            # Check if we have enough consecutive frames
            if len(recent) < self.CONSECUTIVE_FRAMES_NEEDED:
                self.violations_rejected_stage2 += 1
                logger.debug(
                    f"Stage 2 REJECT: track_{track.track_id} "
                    f"only {len(recent)}/{self.CONSECUTIVE_FRAMES_NEEDED} frames accumulated"
                )
                continue
            
            # Check if last N frames all have the same violation class
            last_n_classes = [r[0] for r in recent[-self.CONSECUTIVE_FRAMES_NEEDED:]]
            if len(set(last_n_classes)) != 1:
                self.violations_rejected_stage2 += 1
                logger.debug(
                    f"Stage 2 REJECT: track_{track.track_id} "
                    f"inconsistent violation classes in last {self.CONSECUTIVE_FRAMES_NEEDED} frames: {last_n_classes}"
                )
                continue
            
            # ============================================================
            # STAGE 3: MOTION CHECK
            # ============================================================
            
            speed_kmh = tracker.estimate_speed(
                track.track_id,
                fps=30,
                pixels_per_meter=50
            )
            
            # Filter out stationary/parked vehicles
            if speed_kmh is None or speed_kmh <= self.MIN_SPEED_KMH:
                self.violations_rejected_stage3 += 1
                logger.debug(
                    f"Stage 3 REJECT: track_{track.track_id} "
                    f"speed {speed_kmh:.2f} km/h <= {self.MIN_SPEED_KMH} km/h "
                    f"(vehicle stationary or parked)"
                )
                continue
            
            # ============================================================
            # STAGE 4: COOLDOWN CHECK
            # ============================================================
            
            now = datetime.now()
            if track.track_id in self.confirmed_violations:
                last_confirmed = self.confirmed_violations[track.track_id]
                time_since_last = (now - last_confirmed).total_seconds()
                
                if time_since_last < self.COOLDOWN_SECONDS:
                    self.violations_rejected_stage4 += 1
                    logger.debug(
                        f"Stage 4 REJECT: track_{track.track_id} "
                        f"cooldown active - "
                        f"{time_since_last:.1f}s elapsed / {self.COOLDOWN_SECONDS}s required"
                    )
                    continue
            
            # ============================================================
            # ALL STAGES PASSED - CONFIRM VIOLATION
            # ============================================================
            
            violation = ConfirmedViolation(
                track_id=track.track_id,
                violation_type=track.class_name,
                confidence=track.confidence,
                bbox=(track.x1, track.y1, track.x2, track.y2),
                timestamp=now,
                frame_number=self.frame_number,
                speed_kmh=speed_kmh
            )
            
            confirmed.append(violation)
            self.confirmed_violations[track.track_id] = now
            self.total_violations_confirmed += 1
            
            logger.info(
                f"✓ CONFIRMED VIOLATION: {violation}"
            )
        
        return confirmed
    
    def get_stats(self) -> Dict:
        """
        Get gate statistics and false positive reduction metrics.
        
        Returns:
            Dictionary with:
            - total_violations_confirmed: Number of violations that passed all stages
            - violations_rejected_stage1..4: Count of rejections at each stage
            - false_positive_reduction_rate: Percentage of candidates rejected
            - stage1_rejection_rate: % rejected at stage 1
            - stage2_rejection_rate: % rejected at stage 2
            - stage3_rejection_rate: % rejected at stage 3
            - stage4_rejection_rate: % rejected at stage 4
        """
        
        total_rejected = (
            self.violations_rejected_stage1 +
            self.violations_rejected_stage2 +
            self.violations_rejected_stage3 +
            self.violations_rejected_stage4
        )
        
        total_candidates = self.total_violations_confirmed + total_rejected
        
        # Avoid division by zero
        if total_candidates == 0:
            false_positive_reduction_rate = 0.0
        else:
            false_positive_reduction_rate = total_rejected / total_candidates
        
        return {
            'total_violations_confirmed': self.total_violations_confirmed,
            'violations_rejected_stage1': self.violations_rejected_stage1,
            'violations_rejected_stage2': self.violations_rejected_stage2,
            'violations_rejected_stage3': self.violations_rejected_stage3,
            'violations_rejected_stage4': self.violations_rejected_stage4,
            'total_candidates': total_candidates,
            'total_rejected': total_rejected,
            'false_positive_reduction_rate': false_positive_reduction_rate,
            'stage1_rejection_rate': (
                self.violations_rejected_stage1 / total_candidates 
                if total_candidates > 0 else 0.0
            ),
            'stage2_rejection_rate': (
                self.violations_rejected_stage2 / total_candidates 
                if total_candidates > 0 else 0.0
            ),
            'stage3_rejection_rate': (
                self.violations_rejected_stage3 / total_candidates 
                if total_candidates > 0 else 0.0
            ),
            'stage4_rejection_rate': (
                self.violations_rejected_stage4 / total_candidates 
                if total_candidates > 0 else 0.0
            ),
        }
    
    def reset(self):
        """Clear all tracked state. Use for new video or session."""
        self.frame_buffer.clear()
        self.confirmed_violations.clear()
        self.frame_number = 0
        self.total_violations_confirmed = 0
        self.violations_rejected_stage1 = 0
        self.violations_rejected_stage2 = 0
        self.violations_rejected_stage3 = 0
        self.violations_rejected_stage4 = 0
    
    def print_stats(self):
        """Print formatted statistics to console."""
        stats = self.get_stats()
        
        print("\n" + "=" * 70)
        print("VIOLATION GATE STATISTICS")
        print("=" * 70)
        print(f"\n✓ Confirmed Violations: {stats['total_violations_confirmed']}")
        print(f"\n✗ Rejected Candidates: {stats['total_rejected']}")
        print(f"  │")
        print(f"  ├─ Stage 1 (Confidence):        {stats['violations_rejected_stage1']:5d} "
              f"({stats['stage1_rejection_rate']:5.1%})")
        print(f"  ├─ Stage 2 (Temporal):          {stats['violations_rejected_stage2']:5d} "
              f"({stats['stage2_rejection_rate']:5.1%})")
        print(f"  ├─ Stage 3 (Motion):            {stats['violations_rejected_stage3']:5d} "
              f"({stats['stage3_rejection_rate']:5.1%})")
        print(f"  └─ Stage 4 (Cooldown):          {stats['violations_rejected_stage4']:5d} "
              f"({stats['stage4_rejection_rate']:5.1%})")
        
        print(f"\n📊 False Positive Reduction: {stats['false_positive_reduction_rate']:.1%}")
        print(f"   ({stats['total_rejected']} / {stats['total_candidates']} candidates filtered)")
        print("\n" + "=" * 70 + "\n")
