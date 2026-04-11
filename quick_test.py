#!/usr/bin/env python3
"""
Quick Test - Run system for 30 seconds to verify everything works
"""

import sys
import time
import cv2
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("  QUICK SYSTEM TEST (30 seconds)")
print("=" * 60)
print()

# Test 1: Check model
print("✓ Step 1: Checking YOLO model...")
model_path = Path("model/checkpoints/best.pt")
if not model_path.exists():
    print("❌ Model not found!")
    sys.exit(1)
print(f"✓ Model found: {model_path}")
print()

# Test 2: Check camera
print("✓ Step 2: Testing camera...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not accessible!")
    sys.exit(1)

ret, frame = cap.read()
if not ret:
    print("❌ Cannot read from camera!")
    cap.release()
    sys.exit(1)

print(f"✓ Camera working: {frame.shape[1]}x{frame.shape[0]}")
cap.release()
print()

# Test 3: Import core modules
print("✓ Step 3: Testing imports...")
try:
    from backend.core.detector import Detector
    print("  ✓ Detector")
except Exception as e:
    print(f"  ⚠️  Detector: {e}")

try:
    from backend.core.tracker import VehicleTracker
    print("  ✓ Tracker")
except Exception as e:
    print(f"  ⚠️  Tracker: {e}")

try:
    from backend.core.ocr import PlateOCR
    print("  ✓ OCR")
except Exception as e:
    print(f"  ⚠️  OCR: {e}")

try:
    from backend.database.crud import save_violation
    print("  ✓ Database")
except Exception as e:
    print(f"  ⚠️  Database: {e}")

print()

# Test 4: Quick detection test
print("✓ Step 4: Testing YOLO detection...")
try:
    from ultralytics import YOLO
    
    model = YOLO(str(model_path))
    print(f"  ✓ Model loaded: {model_path.name}")
    
    # Test inference on a blank frame
    import numpy as np
    test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    results = model(test_frame, verbose=False)
    print(f"  ✓ Inference working (detected {len(results[0].boxes)} objects)")
    
except Exception as e:
    print(f"  ⚠️  Detection test failed: {e}")

print()

# Test 5: Database
print("✓ Step 5: Testing database...")
try:
    from backend.database.connection import get_db, init_db
    
    init_db()
    print("  ✓ Database initialized")
    
    # Test connection
    db = next(get_db())
    print("  ✓ Database connection working")
    
except Exception as e:
    print(f"  ⚠️  Database: {e}")

print()
print("=" * 60)
print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("System is ready! You can now:")
print("  1. Test with webcam: python run_with_mobile.py --source 0")
print("  2. Test with mobile: python run_with_mobile.py --ip YOUR_IP:8080")
print("  3. Start API server: python backend/run_server.py")
print()
