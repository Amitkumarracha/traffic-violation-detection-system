#!/usr/bin/env python3
"""
Environment verification script
Checks Python, PyTorch, CUDA, and YOLOv8 installation
"""

import sys
print(f"Python version: {sys.version}")

try:
    import torch
    print(f"\n✅ PyTorch version: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✅ CUDA version: {torch.version.cuda}")
        print(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        print("⚠️ CUDA not available - training will use CPU (slow)")
except ImportError:
    print("❌ PyTorch not installed")

try:
    from ultralytics import YOLO
    print(f"\n✅ Ultralytics YOLO installed")
    
    # Try loading the correct model for this project
    try:
        model = YOLO('yolo26n.pt')
        print(f"✅ YOLO26n model loaded successfully (NMS-free, edge optimized)")
    except:
        # Fallback to YOLOv8n if YOLO26n not available
        model = YOLO('yolov8n.pt')
        print(f"⚠️ YOLO26n not available, loaded YOLOv8n as fallback")
except ImportError:
    print("❌ Ultralytics not installed")
except Exception as e:
    print(f"⚠️ Error loading YOLO models: {e}")

try:
    import cv2
    print(f"✅ OpenCV version: {cv2.__version__}")
except ImportError:
    print("❌ OpenCV not installed")

try:
    import onnx
    import onnxruntime
    print(f"✅ ONNX version: {onnx.__version__}")
    print(f"✅ ONNXRuntime version: {onnxruntime.__version__}")
except ImportError:
    print("⚠️ ONNX/ONNXRuntime not installed")

print("\n" + "="*50)
print("Environment check complete!")
print("="*50)
