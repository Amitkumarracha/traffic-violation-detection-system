"""
Backend Package
Complete platform detection, configuration, and inference system
"""

__version__ = "1.0.0"
__author__ = "Traffic Violation Detection Team"

from .config import (
    get_platform_config,
    get_settings,
    print_platform_summary,
    print_settings_summary,
    PlatformConfig,
    Settings,
)

from .core import (
    Detector,
    Detection,
    CLASS_NAMES,
    CLASS_COLORS,
    DANGER_CLASSES,
    get_danger_detections,
    print_detections,
)

__all__ = [
    # Config
    "get_platform_config",
    "get_settings",
    "print_platform_summary",
    "print_settings_summary",
    "PlatformConfig",
    "Settings",
    # Core
    "Detector",
    "Detection",
    "CLASS_NAMES",
    "CLASS_COLORS",
    "DANGER_CLASSES",
    "get_danger_detections",
    "print_detections",
]
