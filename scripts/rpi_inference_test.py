#!/usr/bin/env python3
"""
Raspberry Pi Inference Test Script
Tests model performance on different input sizes
"""

from ultralytics import YOLO
from pathlib import Path
import time
import numpy as np

BASE = Path.home() / "traffic_violation_detection"
MODEL_PATH = BASE / "exports" / "best.pt"

print("="*60)
print("Raspberry Pi Inference Performance Test")
print("="*60)

model = YOLO(str(MODEL_PATH))

# Test different input sizes
test_sizes = [320, 416, 640]

for size in test_sizes:
    print(f"\n[Testing {size}x{size}]")
    
    # Warm up
    dummy = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)
    _ = model(dummy, verbose=False)
    
    # Benchmark
    times = []
    for i in range(10):
        start = time.time()
        results = model(dummy, verbose=False)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = np.mean(times) * 1000  # Convert to ms
    fps = 1000 / avg_time
    
    print(f"  Average inference: {avg_time:.1f} ms")
    print(f"  FPS: {fps:.1f}")
    print(f"  Recommended for RPi: {'✅ YES' if size <= 416 else '⚠️ May be slow'}")

print("\n" + "="*60)
print("Recommendations for Raspberry Pi:")
print("  - Use 320x320 for real-time (15-20 FPS on RPi 4)")
print("  - Use 416x416 for better accuracy (8-12 FPS on RPi 4)")
print("  - Use TFLite INT8 for 3-4x speedup")
print("="*60)
