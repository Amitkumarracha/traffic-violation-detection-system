"""
Configuration Package
Auto-detects platform and loads environment settings
"""

from .platform_detector import (
    PlatformConfig,
    get_platform_config,
    print_platform_summary,
    get_inference_config,
)
from .settings import (
    Settings,
    get_settings,
    print_settings_summary,
    validate_settings,
)

__all__ = [
    "PlatformConfig",
    "get_platform_config",
    "print_platform_summary",
    "get_inference_config",
    "Settings",
    "get_settings",
    "print_settings_summary",
    "validate_settings",
]
