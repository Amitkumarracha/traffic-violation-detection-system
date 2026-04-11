# 🚀 QUICK START - COPY & PASTE READY

## START HERE - Copy-paste this entire block:

```bash
# Navigate to project
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection'

# Verify everything is ready
echo "✓ Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo "✓ Checking dataset..."
find model_training/training_dataset_final/images -type f | wc -l

echo "✓ Checking code fixes..."
grep "batch_size = 32" model_training/train_both_models.py
```

---

## START TRAINING - Choose ONE:

### Option 1: Direct (see all output)
```bash
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection/model_training'
python3 train_both_models.py
```

### Option 2: Background (RECOMMENDED - keep terminal free)
```bash
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection/model_training'
nohup python3 train_both_models.py > training_output.log 2>&1 &
```

### Option 3: Using script
```bash
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection'
bash START_TRAINING.sh
```

---

## MONITOR TRAINING - Open NEW terminal & copy ONE of these:

### Monitor GPU (BEST - Updates every 1 second)
```bash
watch -n 1 nvidia-smi
```

### Monitor output (if running in background)
```bash
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection/model_training'
tail -f training_output.log
```

### Monitor metrics (updates as training progresses)
```bash
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection/model_training'
while true; do clear; date; tail -2 trained_models_tvd/yolo8_model*/results.csv 2>/dev/null || echo "Waiting..."; sleep 10; done
```

---

## AFTER TRAINING COMPLETES:

```bash
# Check results
cat model_training/training_log_final.json | python3 -m json.tool

# View final metrics
tail -5 model_training/trained_models_tvd/yolo8_model*/results.csv

# Export to ONNX (for edge)
cd model_training && python3 scripts/export_onnx.py

# Start API server
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection'
python3 backend/run_server.py
```

---

## EMERGENCY - If training fails:

```bash
# Stop training
pkill -f train_both_models

# Clear GPU
python3 -c "import torch; torch.cuda.empty_cache(); print('✓ GPU cleared')"

# Check GPU
nvidia-smi

# Start again
cd '/home/CL502-25/Downloads/gAn_CV/~/traffic_violation_detection/model_training'
python3 train_both_models.py
```

---

## FILES YOU'LL NEED:

- ✅ Code fixed: `model_training/train_both_models.py` (batch=32, img=640)
- ✅ Dataset ready: `model_training/training_dataset_final/` (12,376 images)
- ✅ Models ready: `model_training/models/` (yolov8n.pt, yolo26n.pt)
- ✅ Script ready: `START_TRAINING.sh`, `MONITOR_TRAINING.sh`

---

## EXPECTED RESULTS:

| Item | Value |
|------|-------|
| Training Time | 3-4 hours |
| GPU Memory | 14-15 GB used |
| GPU Temp | 40-60°C |
| Batch Size | 32 |
| Epochs/Model | 200 |
| Expected mAP50 | 85-90% |
| Output Folder | `trained_models_tvd/` |

---

**Ready? Start with Option 2 (background mode) and monitor with GPU watch command!**