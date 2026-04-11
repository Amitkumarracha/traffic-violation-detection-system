#!/usr/bin/env python3
"""
Configuration Testing & Demo Script
Shows how to use the platform detector and settings loader
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from config import (
    get_platform_config,
    print_platform_summary,
    get_inference_config,
    get_settings,
    print_settings_summary,
    validate_settings,
)


def test_platform_detection():
    """Test platform auto-detection"""
    print("\n" + "=" * 60)
    print("TESTING: Platform Detection")
    print("=" * 60 + "\n")
    
    config = get_platform_config()
    print(config)
    
    print("Config as Dictionary:")
    inference_config = get_inference_config()
    for key, value in inference_config.items():
        print(f"  {key}: {value}")


def test_settings_loading():
    """Test settings loading from environment"""
    print("\n" + "=" * 60)
    print("TESTING: Settings Loading")
    print("=" * 60 + "\n")
    
    settings = get_settings()
    print_settings_summary()
    
    print("\nSettings as Dictionary:")
    settings_dict = settings.dict() if hasattr(settings, 'dict') else vars(settings)
    for key, value in settings_dict.items():
        if key.endswith("_key") or key == "notification_email":
            value = "***HIDDEN***" if value else None
        print(f"  {key}: {value}")


def test_settings_validation():
    """Test settings validation"""
    print("\n" + "=" * 60)
    print("TESTING: Settings Validation")
    print("=" * 60 + "\n")
    
    is_valid = validate_settings()
    print(f"\nValidation Result: {'✅ PASS' if is_valid else '⚠️ WARNINGS'}")


def test_singleton_pattern():
    """Test that get_settings returns same instance"""
    print("\n" + "=" * 60)
    print("TESTING: Singleton Pattern")
    print("=" * 60 + "\n")
    
    settings1 = get_settings()
    settings2 = get_settings()
    
    print(f"settings1 id: {id(settings1)}")
    print(f"settings2 id: {id(settings2)}")
    print(f"Same instance: {settings1 is settings2} {'✅' if settings1 is settings2 else '❌'}")


def test_platform_specific_config():
    """Show platform-specific inference settings"""
    print("\n" + "=" * 60)
    print("TESTING: Platform-Specific Configuration")
    print("=" * 60 + "\n")
    
    config = get_platform_config()
    
    print(f"Detected Platform: {config.platform}")
    print(f"Device Name: {config.device_name}\n")
    
    print("Inference Configuration for this platform:")
    print(f"  Image Size:        {config.inference_size}x{config.inference_size}")
    print(f"  Target FPS:        {config.max_fps_target}")
    print(f"  CPU Threads:       {config.num_threads}")
    print(f"  Confidence:        {config.confidence_threshold}")
    print(f"  Coral TPU:         {'Yes' if config.use_coral else 'No'}")
    print(f"  Model Path:        {config.model_path}")
    
    # Show what this means
    print("\n📊 Performance Implications:")
    if config.platform == "raspberry_pi":
        print("  - Optimized for edge deployment")
        print("  - Lower resolution (320x320) for speed")
        print("  - ~10 FPS real-time processing")
        print("  - 4 CPU threads to save resources")
    elif config.platform == "desktop_gpu":
        print("  - GPU acceleration enabled")
        print("  - Full resolution (640x640) for accuracy")
        print("  - ~60 FPS real-time processing")
        print("  - 8 CPU threads for preprocessing")
    else:  # laptop_cpu
        print("  - CPU-only inference")
        print("  - Balanced resolution (416x416)")
        print("  - ~30 FPS target")
        print("  - 4 CPU threads")


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════╗
║  Configuration Module Testing & Demo                 ║
║  Traffic Violation Detection System                  ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        test_platform_detection()
        test_settings_loading()
        test_settings_validation()
        test_singleton_pattern()
        test_platform_specific_config()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")
        
        print("💡 Usage Examples:")
        print("""
# In your application code:

from backend.config import (
    get_platform_config,
    get_settings,
    get_inference_config,
)

# Get platform config
config = get_platform_config()
print(f"Running on: {config.device_name}")
print(f"Using image size: {config.inference_size}x{config.inference_size}")

# Get application settings
settings = get_settings()
print(f"Database: {settings.database_url}")
print(f"API runs on: {settings.api_host}:{settings.api_port}")

# Get inference-ready config
inf_config = get_inference_config()
model_path = inf_config['model_path']
batch_size = 1  # Calculate based on platform
if inf_config['platform'] == 'desktop_gpu':
    batch_size = 32
elif inf_config['platform'] == 'laptop_cpu':
    batch_size = 2
else:  # raspberry_pi
    batch_size = 1
        """)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
