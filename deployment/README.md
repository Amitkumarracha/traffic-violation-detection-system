# 🚀 Traffic Violation Detection - Deployment

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run inference server:**
   ```bash
   python scripts/run_server.py
   ```

3. **Export models for edge deployment:**
   ```bash
   python scripts/export_onnx.py
   ```

## Folder Structure

```
deployment/
├── models/           # Trained YOLO models (.pt files)
├── configs/          # Dataset and model configs
├── scripts/          # Deployment scripts
├── logs/            # Runtime logs
└── README.md        # This file
```

## Models

- `yolo8_model/weights/best.pt` - YOLOv8 Nano model
- `yolo26_model/weights/best.pt` - YOLO26 Nano model
- `*.onnx` - Edge deployment models (after export)

## API Endpoints

- `GET /api/violations` - List violations
- `POST /api/fraud/check` - Fraud investigation
- `WS /ws/live` - Real-time violation feed
