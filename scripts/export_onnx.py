#!/usr/bin/env python3
"""
Multi-format Export Script for Raspberry Pi Deployment
YOLO26n - NMS-free architecture for faster edge inference
Exports: ONNX, TFLite, NCNN
"""

from ultralytics import YOLO
from pathlib import Path
import onnx, onnxruntime as ort
import numpy as np
import json
from datetime import datetime

BASE = Path.home() / "traffic_violation_detection"
EXPORTS = BASE / "exports"
EXPORTS.mkdir(exist_ok=True)

# Find best model
best_pt = BASE / "runs" / "tvd_yolo26n_v1" / "weights" / "best.pt"
print(f"Loading: {best_pt}")

model = YOLO(str(best_pt))

# Export ONNX (640x640 for accuracy)
print("\n[1/4] Exporting ONNX 640x640 (NMS-free)...")
model.export(
    format='onnx',
    imgsz=640,
    optimize=True,
    simplify=True,
    dynamic=False,
    opset=12,
    half=False,
)

onnx_path = best_pt.parent / "best.onnx"
dst_640 = EXPORTS / f"tvd_yolo26n_640_{datetime.now().strftime('%Y%m%d')}.onnx"

import shutil
shutil.copy2(onnx_path, dst_640)
print(f"✅ ONNX 640x640 saved to: {dst_640}")

# Validate ONNX model
print("\nValidating ONNX model...")
onnx_model = onnx.load(str(dst_640))
onnx.checker.check_model(onnx_model)
print("✅ ONNX model is valid")

# Test inference with ONNXRuntime
print("\nTesting ONNX inference...")
sess = ort.InferenceSession(str(dst_640), providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
input_name = sess.get_inputs()[0].name
dummy = np.random.rand(1, 3, 640, 640).astype(np.float32)
outputs = sess.run(None, {input_name: dummy})
print(f"✅ ONNX inference OK. Output shape: {outputs[0].shape}")

# Export TFLite FP16 (best for Raspberry Pi)
print("\n[2/4] Exporting TFLite FP16 (optimized for Raspberry Pi)...")
try:
    model.export(
        format='tflite',
        imgsz=640,
        int8=False,
        half=True,  # FP16 for better accuracy on RPi
    )
    print("✅ TFLite FP16 exported")
except Exception as e:
    print(f"⚠️ TFLite export: {e}")

# Export TFLite INT8 (fastest on Raspberry Pi)
print("\n[3/4] Exporting TFLite INT8 (fastest on Raspberry Pi)...")
try:
    model.export(
        format='tflite',
        imgsz=640,
        int8=True,  # INT8 quantization for speed
    )
    print("✅ TFLite INT8 exported")
except Exception as e:
    print(f"⚠️ TFLite INT8 export: {e}")

# Export NCNN (alternative for Raspberry Pi)
print("\n[4/4] Exporting NCNN (alternative framework)...")
try:
    model.export(
        format='ncnn',
        imgsz=640,
    )
    print("✅ NCNN exported")
except Exception as e:
    print(f"⚠️ NCNN export: {e}")

# Save export info
info = {
    "onnx_path": str(dst_640),
    "input_shape": [1, 3, 640, 640],
    "output_shape": list(outputs[0].shape),
    "providers": sess.get_providers(),
    "exported_at": datetime.now().isoformat(),
    "raspberry_pi_notes": {
        "recommended": "TFLite FP16 for best balance",
        "fastest": "TFLite INT8 for maximum speed",
        "flexible": "ONNX with ONNXRuntime",
        "inference_size": "Use 320x320 or 416x416 on RPi for real-time"
    }
}
with open(EXPORTS / "export_info.json", 'w') as f:
    json.dump(info, f, indent=2)

print(f"\n{'='*60}")
print("✅ YOLO26n Export Complete!")
print(f"{'='*60}")
print(f"ONNX 640x640: {dst_640}")
print(f"File size: {dst_640.stat().st_size / 1e6:.1f} MB")
print(f"\n📱 Raspberry Pi Deployment (YOLO26 NMS-free):")
print(f"   - TFLite FP16: Best accuracy/speed balance")
print(f"   - TFLite INT8: Maximum speed (3-4x faster)")
print(f"   - ONNX: Most flexible, use with ONNXRuntime")
print(f"   - NMS-free: Faster inference, no post-processing")
print(f"   - Recommended inference: 320x320 or 416x416")
print(f"{'='*60}")

import shutil
shutil.copy2(onnx_path, dst)
print(f"ONNX saved to: {dst}")

# Validate ONNX model
print("\nValidating ONNX model...")
onnx_model = onnx.load(str(dst))
onnx.checker.check_model(onnx_model)
print("✅ ONNX model is valid")

# Test inference with ONNXRuntime
print("\nTesting ONNX inference...")
sess = ort.InferenceSession(str(dst), providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
input_name = sess.get_inputs()[0].name
dummy = np.random.rand(1, 3, 640, 640).astype(np.float32)
outputs = sess.run(None, {input_name: dummy})
print(f"✅ ONNX inference OK. Output shape: {outputs[0].shape}")

# Save export info
info = {
    "onnx_path": str(dst),
    "input_shape": [1, 3, 640, 640],
    "output_shape": list(outputs[0].shape),
    "providers": sess.get_providers(),
    "exported_at": datetime.now().isoformat()
}
with open(EXPORTS / "export_info.json", 'w') as f:
    json.dump(info, f, indent=2)
print(f"\n✅ Export complete: {dst}")
print(f"File size: {dst.stat().st_size / 1e6:.1f} MB")
