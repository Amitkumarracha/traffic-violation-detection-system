#!/usr/bin/env python3
"""
AI Traffic Violation Detection - YOLO26n Training Script
Optimized for Raspberry Pi Edge Deployment (NMS-free architecture)
Features:
  - Auto-resume from last checkpoint
  - Comprehensive logging
  - ONNX export after training (optimized for RPi)
  - TFLite export for edge devices
  - All metrics saved
  - YOLO26 NMS-free inference for faster edge deployment
"""

import os, sys, yaml, json, time, signal, shutil
from pathlib import Path
from datetime import datetime
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
CHECKPOINT_TRACKER = LOGS_DIR / "last_checkpoint.json"

for d in [RUNS_DIR, EXPORTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==============================================
# LOGGING
# ==============================================
log_file = LOGS_DIR / f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(log_file, 'a') as f:
        f.write(full_msg + '\n')

# ==============================================
# FIND LAST CHECKPOINT
# ==============================================
def find_last_checkpoint(project, name):
    """Find the last saved checkpoint to resume from"""
    run_dir = Path(project) / name
    
    # Check best.pt and last.pt
    last_pt = run_dir / "weights" / "last.pt"
    best_pt = run_dir / "weights" / "best.pt"
    
    if last_pt.exists():
        log(f"📂 Found checkpoint: {last_pt}")
        return str(last_pt)
    
    # Search across all run folders with same name pattern
    for run in sorted(Path(project).glob(f"{name}*"), reverse=True):
        last = run / "weights" / "last.pt"
        if last.exists():
            log(f"📂 Found checkpoint in: {last}")
            return str(last)
    
    log("🆕 No checkpoint found — starting fresh training")
    return None

# ==============================================
# SAVE CHECKPOINT TRACKER
# ==============================================
def save_tracker(info):
    with open(CHECKPOINT_TRACKER, 'w') as f:
        json.dump(info, f, indent=2)

# ==============================================
# GRACEFUL SHUTDOWN HANDLER
# ==============================================
def handle_interrupt(sig, frame):
    log("\n⚠️ Training interrupted! Checkpoint auto-saved by YOLO.")
    log(f"▶️ To resume: python scripts/train.py --resume")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_interrupt)
signal.signal(signal.SIGTERM, handle_interrupt)

# ==============================================
# MAIN TRAINING
# ==============================================
def train():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    
    log("=" * 60)
    log("AI TRAFFIC VIOLATION DETECTION - YOLOv8n TRAINING")
    log("=" * 60)
    log(f"PyTorch: {torch.__version__}")
    log(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log(f"GPU: {torch.cuda.get_device_name(0)}")
        log(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Check for resume
    resume_path = find_last_checkpoint(cfg['project'], cfg['name'])
    resume = '--resume' in sys.argv or '-r' in sys.argv
    
    if resume and resume_path:
        log(f"🔄 RESUMING from: {resume_path}")
        model = YOLO(resume_path)
        results = model.train(resume=True)
    else:
        if resume_path and not resume:
            log(f"⚠️ Checkpoint found but --resume not passed.")
            log(f"   Starting fresh. Use --resume to continue from: {resume_path}")
        
        log(f"🚀 Starting fresh training with: {cfg['model']}")
        model = YOLO(cfg['model'])
        
        results = model.train(
            data=cfg['data'],
            epochs=cfg['epochs'],
            patience=cfg['patience'],
            batch=cfg['batch'],
            imgsz=cfg['imgsz'],
            workers=cfg['workers'],
            optimizer=cfg['optimizer'],
            lr0=cfg['lr0'],
            lrf=cfg['lrf'],
            momentum=cfg['momentum'],
            weight_decay=cfg['weight_decay'],
            warmup_epochs=cfg['warmup_epochs'],
            warmup_momentum=cfg['warmup_momentum'],
            warmup_bias_lr=cfg['warmup_bias_lr'],
            hsv_h=cfg['hsv_h'],
            hsv_s=cfg['hsv_s'],
            hsv_v=cfg['hsv_v'],
            degrees=cfg['degrees'],
            translate=cfg['translate'],
            scale=cfg['scale'],
            shear=cfg['shear'],
            perspective=cfg['perspective'],
            flipud=cfg['flipud'],
            fliplr=cfg['fliplr'],
            mosaic=cfg['mosaic'],
            mixup=cfg['mixup'],
            copy_paste=cfg['copy_paste'],
            save=True,
            save_period=cfg['save_period'],
            cache=cfg['cache'],
            device=cfg['device'],
            exist_ok=cfg['exist_ok'],
            pretrained=cfg['pretrained'],
            verbose=cfg['verbose'],
            seed=cfg['seed'],
            deterministic=cfg['deterministic'],
            cos_lr=cfg['cos_lr'],
            close_mosaic=cfg['close_mosaic'],
            amp=cfg['amp'],
            project=cfg['project'],
            name=cfg['name'],
        )
    
    # ==============================================
    # POST TRAINING — EVALUATE & EXPORT
    # ==============================================
    log("\n" + "="*60)
    log("✅ TRAINING COMPLETE — Running Evaluation & Export")
    log("="*60)
    
    run_dir = Path(cfg['project']) / cfg['name']
    best_model_path = run_dir / "weights" / "best.pt"
    
    if not best_model_path.exists():
        # Try finding in numbered runs
        for run in sorted(Path(cfg['project']).glob(f"{cfg['name']}*"), reverse=True):
            bp = run / "weights" / "best.pt"
            if bp.exists():
                best_model_path = bp
                run_dir = run
                break
    
    log(f"Best model: {best_model_path}")
    
    # Load best model for evaluation
    best_model = YOLO(str(best_model_path))
    
    # Run validation
    log("\n📊 Running final validation...")
    val_results = best_model.val(
        data=cfg['data'],
        imgsz=cfg['imgsz'],
        batch=cfg['batch'],
        device=cfg['device'],
        save_json=True,
        save_hybrid=True,
    )
    
    # Save metrics
    metrics = {
        "mAP50": float(val_results.box.map50),
        "mAP50-95": float(val_results.box.map),
        "precision": float(val_results.box.mp),
        "recall": float(val_results.box.mr),
        "timestamp": datetime.now().isoformat(),
        "model": str(best_model_path),
        "epochs_trained": cfg['epochs'],
    }
    
    metrics_file = run_dir / "final_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    log(f"\n📈 Final Metrics:")
    for k, v in metrics.items():
        if isinstance(v, float):
            log(f"   {k}: {v:.4f}")
    
    log(f"\n💾 Metrics saved to: {metrics_file}")
    
    # ==============================================
    # EXPORT TO MULTIPLE FORMATS FOR RASPBERRY PI
    # ==============================================
    log("\n📦 Exporting models for Raspberry Pi deployment...")
    
    # Export ONNX (for general edge deployment)
    try:
        log("Exporting ONNX...")
        best_model.export(
            format='onnx',
            imgsz=cfg['imgsz'],
            optimize=True,
            simplify=True,
            dynamic=False,
            opset=12,
            half=False,             # FP32 for RPi compatibility
        )
        
        onnx_src = best_model_path.parent / f"{best_model_path.stem}.onnx"
        if not onnx_src.exists():
            onnx_src = best_model_path.with_suffix('.onnx')
        
        onnx_dst = EXPORTS_DIR / f"tvd_yolo11n_640_{datetime.now().strftime('%Y%m%d')}.onnx"
        
        if onnx_src.exists():
            shutil.copy2(onnx_src, onnx_dst)
            log(f"✅ ONNX model saved to: {onnx_dst}")
    except Exception as e:
        log(f"❌ ONNX export failed: {e}")
    
    # Export TFLite (optimized for Raspberry Pi)
    try:
        log("\nExporting TFLite (optimized for Raspberry Pi)...")
        best_model.export(
            format='tflite',
            imgsz=cfg['imgsz'],
            int8=False,             # FP16 for better accuracy
            half=True,
        )
        
        tflite_src = best_model_path.parent / f"{best_model_path.stem}_saved_model" / f"{best_model_path.stem}_float16.tflite"
        if not tflite_src.exists():
            tflite_src = best_model_path.with_suffix('_float16.tflite')
        
        tflite_dst = EXPORTS_DIR / f"tvd_yolo11n_640_fp16_{datetime.now().strftime('%Y%m%d')}.tflite"
        
        if tflite_src.exists():
            shutil.copy2(tflite_src, tflite_dst)
            log(f"✅ TFLite FP16 model saved to: {tflite_dst}")
    except Exception as e:
        log(f"⚠️ TFLite export failed: {e}")
    
    # Export NCNN (for Raspberry Pi with NCNN framework)
    try:
        log("\nExporting NCNN (alternative for Raspberry Pi)...")
        best_model.export(
            format='ncnn',
            imgsz=cfg['imgsz'],
        )
        log(f"✅ NCNN model exported")
    except Exception as e:
        log(f"⚠️ NCNN export failed: {e}")
    
    # Copy best.pt to exports
    shutil.copy2(best_model_path, EXPORTS_DIR / "best.pt")
    shutil.copy2(best_model_path.parent / "last.pt", EXPORTS_DIR / "last.pt")
    
    log(f"\n🎉 ALL DONE! Exports saved to: {EXPORTS_DIR}")
    log(f"   Logs: {log_file}")
    log(f"   Run dir: {run_dir}")
    log(f"\n📱 Raspberry Pi Deployment (YOLO26 NMS-free):")
    log(f"   - Use TFLite FP16 for best balance of speed/accuracy")
    log(f"   - Use ONNX with ONNXRuntime for flexibility")
    log(f"   - Use NCNN for maximum performance")
    log(f"   - NMS-free architecture = faster inference!")
    log(f"   - Recommended inference size: 320x320 or 416x416 on RPi")

if __name__ == '__main__':
    train()
