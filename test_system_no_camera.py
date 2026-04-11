#!/usr/bin/env python3
"""
System Test Without Camera - Verify all components work
"""

import sys
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("  SYSTEM TEST (No Camera Required)")
print("=" * 60)
print()

# Test 1: Model
print("Step 1: Checking YOLO model...")
model_path = Path("model/checkpoints/best.pt")
if not model_path.exists():
    print("❌ Model not found!")
    sys.exit(1)
print(f"✅ Model found: {model_path}")
print()

# Test 2: Core imports
print("Step 2: Testing core imports...")
errors = []

try:
    from ultralytics import YOLO
    print("  ✅ YOLO (ultralytics)")
except Exception as e:
    print(f"  ❌ YOLO: {e}")
    errors.append("YOLO")

try:
    import cv2
    print("  ✅ OpenCV")
except Exception as e:
    print(f"  ❌ OpenCV: {e}")
    errors.append("OpenCV")

try:
    import torch
    print(f"  ✅ PyTorch {torch.__version__}")
    print(f"     CUDA available: {torch.cuda.is_available()}")
except Exception as e:
    print(f"  ❌ PyTorch: {e}")
    errors.append("PyTorch")

try:
    from fastapi import FastAPI
    print("  ✅ FastAPI")
except Exception as e:
    print(f"  ❌ FastAPI: {e}")
    errors.append("FastAPI")

try:
    from sqlalchemy import create_engine
    print("  ✅ SQLAlchemy")
except Exception as e:
    print(f"  ❌ SQLAlchemy: {e}")
    errors.append("SQLAlchemy")

print()

# Test 3: YOLO inference
print("Step 3: Testing YOLO inference...")
try:
    from ultralytics import YOLO
    
    print("  Loading model...")
    model = YOLO(str(model_path))
    print(f"  ✅ Model loaded")
    
    # Create test image
    print("  Creating test image...")
    test_img = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Run inference
    print("  Running inference...")
    results = model(test_img, verbose=False)
    
    print(f"  ✅ Inference successful")
    print(f"     Detections: {len(results[0].boxes)}")
    print(f"     Classes: {model.names}")
    
except Exception as e:
    print(f"  ❌ Inference failed: {e}")
    errors.append("Inference")

print()

# Test 4: Database
print("Step 4: Testing database...")
try:
    from backend.database.connection import init_db, get_db
    from backend.database.models import Violation
    
    print("  Initializing database...")
    init_db()
    print("  ✅ Database initialized")
    
    # Test connection
    db = next(get_db())
    print("  ✅ Database connection working")
    
except Exception as e:
    print(f"  ⚠️  Database: {e}")
    # Database is optional for testing

print()

# Test 5: Configuration
print("Step 5: Testing configuration...")
try:
    from backend.config.settings import get_settings
    
    settings = get_settings()
    print(f"  ✅ Settings loaded")
    print(f"     API Host: {settings.api_host}")
    print(f"     API Port: {settings.api_port}")
    print(f"     Database: {settings.database_url[:30]}...")
    print(f"     Gemini API: {'Configured' if settings.gemini_api_key else 'Not configured (optional)'}")
    
except Exception as e:
    print(f"  ❌ Settings: {e}")
    errors.append("Settings")

print()

# Summary
print("=" * 60)
if len(errors) == 0:
    print("  ✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("System is ready! Next steps:")
    print("  1. Close any apps using the camera")
    print("  2. Test camera: python test_mobile_camera.py --source 0")
    print("  3. Run system: python run_with_mobile.py --source 0")
    print("  4. Or start API: python backend/run_server.py")
else:
    print(f"  ⚠️  {len(errors)} ISSUES FOUND")
    print("=" * 60)
    print()
    print("Issues:", ", ".join(errors))
    print()
    print("Fix with: pip install -r backend_requirements.txt")

print()
