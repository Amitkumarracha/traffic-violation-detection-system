#!/usr/bin/env python3
"""
Verify Installation - Check if all dependencies are installed
"""

import sys
import importlib
from pathlib import Path

def check_module(module_name, package_name=None):
    """Check if a module is installed"""
    try:
        importlib.import_module(module_name)
        print(f"  ✅ {package_name or module_name}")
        return True
    except ImportError:
        print(f"  ❌ {package_name or module_name} - NOT INSTALLED")
        return False

def check_file(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"  ✅ {description}")
        return True
    else:
        print(f"  ❌ {description} - NOT FOUND")
        return False

def main():
    print("=" * 60)
    print("  INSTALLATION VERIFICATION")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # Check Python version
    print("🐍 Python Version:")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        all_ok = False
    print()
    
    # Check core dependencies
    print("📦 Core Dependencies:")
    modules = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("torch", "pytorch"),
        ("ultralytics", "ultralytics"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
    ]
    
    for module, package in modules:
        if not check_module(module, package):
            all_ok = False
    print()
    
    # Check optional dependencies
    print("🔧 Optional Dependencies:")
    optional = [
        ("PIL", "pillow"),
        ("reportlab", "reportlab"),
        ("dotenv", "python-dotenv"),
    ]
    
    for module, package in optional:
        check_module(module, package)
    print()
    
    # Check configuration files
    print("⚙️  Configuration Files:")
    check_file(".env", ".env file")
    check_file(".env.example", ".env.example file")
    print()
    
    # Check model
    print("🤖 YOLO Model:")
    model_exists = check_file("model/checkpoints/best.pt", "YOLO model (best.pt)")
    if not model_exists:
        print("     ⚠️  You need to add your trained model")
        print("     Place best.pt in: model/checkpoints/best.pt")
    print()
    
    # Check scripts
    print("📜 Helper Scripts:")
    check_file("test_mobile_camera.py", "Mobile camera test script")
    check_file("run_with_mobile.py", "Mobile camera launcher")
    check_file("deploy_to_rpi.sh", "RPi deployment script")
    print()
    
    # Summary
    print("=" * 60)
    if all_ok:
        print("  ✅ INSTALLATION COMPLETE")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Add YOLO model: model/checkpoints/best.pt")
        print("  2. Test camera: python test_mobile_camera.py")
        print("  3. Run system: python run_with_mobile.py")
        return 0
    else:
        print("  ❌ INSTALLATION INCOMPLETE")
        print("=" * 60)
        print()
        print("Fix missing dependencies:")
        print("  pip install -r backend_requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
