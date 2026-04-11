#!/usr/bin/env python3
"""
Export-only script - Complete model export without retraining
Skips GitHub API calls and network dependencies
"""

import os
import sys
import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime

# Disable telemetry and online features
os.environ['YOLOv8_DISABLED_TELEMETRY'] = '1'
os.environ['YOLO_AUTOINSTALL'] = '0'

import torch
from ultralytics import YOLO

# ==============================================
# PATHS
# ==============================================
BASE = Path.home() / "traffic_violation_detection"
CONFIG_PATH = BASE / "configs" / "train_config.yaml"
RUNS_DIR = BASE / "runs"
EXPORTS_DIR = BASE / "exports"
LOGS_DIR = BASE / "logs"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================
# LOGGING
# ==============================================
log_file = LOGS_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(log_file, 'a') as f:
        f.write(full_msg + '\n')

# ==============================================
# MAIN EXPORT
# ==============================================
def export():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    
    log("=" * 60)
    log("EXPORT ONLY - No Retraining")
    log("=" * 60)
    
    # Find best model - search all possible locations
    log("🔍 Searching for best model...")
    best_model_path = None
    run_dir = None
    
    search_paths = [
        BASE / "runs" / "detect" / "~/traffic_violation_detection/runs/tvd_yolo26n_v1/weights/best.pt",
        BASE / "runs" / "tvd_yolo26n_v1" / "weights" / "best.pt",
        Path(cfg['project']) / cfg['name'] / "weights" / "best.pt",
    ]
    
    for candidate in search_paths:
        if candidate.exists():
            best_model_path = candidate
            run_dir = candidate.parent.parent
            log(f"✅ Found: {best_model_path}")
            break
    
    # If still not found, search recursively
    if not best_model_path:
        log("   Performing deep search...")
        for found in BASE.glob("**/best.pt"):
            best_model_path = found
            run_dir = found.parent.parent
            log(f"✅ Found: {best_model_path}")
            break
    
    if not best_model_path.exists():
        log("❌ ERROR: best.pt not found!")
        log(f"   Expected: {best_model_path}")
        sys.exit(1)
    
    log(f"📂 Model: {best_model_path}")
    log(f"📊 Size: {best_model_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Load model (offline mode)
    log("\n🔄 Loading model (offline mode)...")
    try:
        # Suppress all online features
        import warnings
        warnings.filterwarnings('ignore')
        
        best_model = YOLO(str(best_model_path))
        log("✅ Model loaded successfully")
    except Exception as e:
        log(f"❌ Failed to load model: {e}")
        sys.exit(1)
    
    # ==============================================
    # EXPORT TO MULTIPLE FORMATS
    # ==============================================
    log("\n📦 Starting exports...\n")
    
    export_count = 0
    
    # 1. Export ONNX
    try:
        log("1️⃣ Exporting ONNX (general edge deployment)...")
        best_model.export(
            format='onnx',
            imgsz=cfg['imgsz'],
            optimize=True,
            simplify=True,
            dynamic=False,
            opset=12,
            half=False,
        )
        
        onnx_src = best_model_path.parent / f"{best_model_path.stem}.onnx"
        if not onnx_src.exists():
            onnx_src = best_model_path.with_suffix('.onnx')
        
        if onnx_src.exists():
            onnx_dst = EXPORTS_DIR / f"tvd_yolo26n_640_{datetime.now().strftime('%Y%m%d')}.onnx"
            shutil.copy2(onnx_src, onnx_dst)
            log(f"   ✅ Saved: {onnx_dst.name} ({onnx_dst.stat().st_size / 1024 / 1024:.2f} MB)")
            export_count += 1
        else:
            log(f"   ⚠️ ONNX file not found at {onnx_src}")
    except Exception as e:
        log(f"   ❌ ONNX export failed: {e}")
    
    # 2. Export TFLite FP16
    try:
        log("\n2️⃣ Exporting TFLite FP16 (Raspberry Pi optimized)...")
        best_model.export(
            format='tflite',
            imgsz=cfg['imgsz'],
            int8=False,
            half=True,
        )
        log(f"   ✅ TFLite FP16 exported")
        export_count += 1
    except Exception as e:
        log(f"   ⚠️ TFLite FP16 export failed: {e}")
    
    # 3. Export NCNN
    try:
        log("\n3️⃣ Exporting NCNN (high-performance alternative)...")
        best_model.export(
            format='ncnn',
            imgsz=cfg['imgsz'],
        )
        log(f"   ✅ NCNN exported")
        export_count += 1
    except Exception as e:
        log(f"   ⚠️ NCNN export failed: {e}")
    
    # 4. Copy PT files to exports
    try:
        log("\n4️⃣ Copying PyTorch models...")
        shutil.copy2(best_model_path, EXPORTS_DIR / "best.pt")
        shutil.copy2(best_model_path.parent / "last.pt", EXPORTS_DIR / "last.pt")
        log(f"   ✅ best.pt and last.pt copied")
        export_count += 1
    except Exception as e:
        log(f"   ❌ Failed to copy PT files: {e}")
    
    # ==============================================
    # SUMMARY
    # ==============================================
    log("\n" + "=" * 60)
    log(f"✅ EXPORT COMPLETE ({export_count} steps successful)")
    log("=" * 60)
    log(f"📁 All exports in: {EXPORTS_DIR}")
    log(f"📝 Log: {log_file}")
    log(f"\n📱 Ready for Raspberry Pi deployment:")
    log(f"   - ONNX: Cross-platform deployment with ONNXRuntime")
    log(f"   - TFLite: Optimized for RPi with TensorFlow Lite")
    log(f"   - NCNN: Fastest alternative for RPi")
    log(f"   - .pt: Original PyTorch format")

if __name__ == '__main__':
    export()
