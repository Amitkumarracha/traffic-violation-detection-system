#!/usr/bin/env python3
"""
Standalone evaluation script for trained YOLO26n model
"""

from ultralytics import YOLO
from pathlib import Path
import json, yaml
from datetime import datetime

BASE = Path.home() / "traffic_violation_detection"
RUNS = BASE / "runs" / "tvd_yolo26n_v1"

# Find best model
best_pt = RUNS / "weights" / "best.pt"
if not best_pt.exists():
    for run in sorted(BASE.glob("runs/tvd_yolo26n_v1*/"), reverse=True):
        bp = run / "weights" / "best.pt"
        if bp.exists():
            best_pt = bp
            break

print(f"Evaluating: {best_pt}")
model = YOLO(str(best_pt))

with open(BASE / "configs" / "train_config.yaml") as f:
    cfg = yaml.safe_load(f)

# Full validation
results = model.val(
    data=cfg['data'],
    imgsz=640,
    batch=16,
    device=0,
    save_json=True,
    plots=True,
    verbose=True,
)

metrics = {
    "mAP@0.5": round(float(results.box.map50), 4),
    "mAP@0.5:0.95": round(float(results.box.map), 4),
    "Precision": round(float(results.box.mp), 4),
    "Recall": round(float(results.box.mr), 4),
    "Per-class AP": {
        f"class_{i}": round(float(ap), 4)
        for i, ap in enumerate(results.box.ap50)
    },
    "evaluated_at": datetime.now().isoformat()
}

out = BASE / "logs" / "evaluation_results.json"
with open(out, 'w') as f:
    json.dump(metrics, f, indent=2)

print("\n" + "="*50)
print("EVALUATION RESULTS")
print("="*50)
for k, v in metrics.items():
    if not isinstance(v, dict):
        print(f"{k:20}: {v}")
print(f"\nSaved to: {out}")
