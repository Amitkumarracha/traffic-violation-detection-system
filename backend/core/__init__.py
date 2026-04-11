"""
Core Detection & Inference Module
Real-time YOLO26n inference for traffic violation detection
"""

from .detector import (
    Detector,
    Detection,
    CLASS_NAMES,
    CLASS_COLORS,
    DANGER_CLASSES,
    get_danger_detections,
    print_detections,
)

from .tracker import (
    VehicleTracker,
    TrackedObject,
    compute_centroid,
    compute_iou,
    print_tracked_objects,
)

from .violation_gate import (
    ViolationGate,
    ConfirmedViolation,
)

from .ocr import (
    PlateOCR,
    PlateResult,
    extract_plate_text,
    validate_indian_plate,
)

__all__ = [
    # Detector
    "Detector",
    "Detection",
    "CLASS_NAMES",
    "CLASS_COLORS",
    "DANGER_CLASSES",
    "get_danger_detections",
    "print_detections",
    # Tracker
    "VehicleTracker",
    "TrackedObject",
    "compute_centroid",
    "compute_iou",
    "print_tracked_objects",
    # Violation Gate
    "ViolationGate",
    "ConfirmedViolation",
    # OCR
    "PlateOCR",
    "PlateResult",
    "extract_plate_text",
    "validate_indian_plate",
]
