# 🚀 Backend Detector - Quick Start Guide

## Installation

```bash
cd ~/traffic_violation_detection
source tvd_env/bin/activate

# Install detector requirements
pip install -r backend_requirements.txt
```

## Quick Start

### 1. Test Everything Works

```bash
# Test configuration
python test_config.py

# Test detector
python test_detector.py
```

### 2. Live Webcam Detection

```bash
# Real-time webcam (press 'q' to quit)
python demo_webcam.py

# Save video output
python demo_webcam.py --save-video

# With different setup
python demo_webcam.py --size 416 --camera 0
```

### 3. Image Detection

```python
import cv2
from backend import Detector, get_platform_config

# Setup
config = get_platform_config()
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
)

# Detect
frame = cv2.imread('traffic.jpg')
detections = detector.infer(frame)

# Draw
result = detector.draw_detections(frame, detections)
cv2.imwrite('output.jpg', result)

# Print results
for det in detections:
    print(f"{det.class_name}: {det.confidence:.2f}")
```

## Architecture Overview

```
backend/
├── config/
│   ├── platform_detector.py    # Auto-detect platform & hardware
│   └── settings.py              # Environment configuration
│
└── core/
    └── detector.py              # ONNX inference engine
```

## Key Components

### 1. Platform Auto-Detection (`backend.config`)

```python
from backend import get_platform_config

config = get_platform_config()
print(f"Platform: {config.platform}")        # 'raspberry_pi' | 'laptop_cpu' | 'desktop_gpu'
print(f"Inference size: {config.inference_size}x{config.inference_size}")
print(f"Threads: {config.num_threads}")
print(f"FPS target: {config.max_fps_target}")
```

**Auto-Detects:**
- Raspberry Pi (checks `/proc/device-tree/model`)
- GPU availability (checks CUDA)
- Coral TPU (USB detection)

### 2. Settings Management (`backend.config.settings`)

```python
from backend import get_settings

settings = get_settings()
print(f"Database: {settings.database_url}")
print(f"API Host: {settings.api_host}:{settings.api_port}")
print(f"Alert email: {settings.notification_email}")
```

**Loads from `.env` file:**
- API keys (Gemini, SendGrid)
- Database URLs
- Email notifications
- Cloud sync (Supabase)

### 3. Real-time Detection (`backend.core.Detector`)

```python
from backend import Detector, get_platform_config, CLASS_NAMES

# Initialize
config = get_platform_config()
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
    confidence_threshold=0.75,
)

# Run inference
detections = detector.infer(frame)

# Get results
for det in detections:
    print(f"{det.class_name}: {det.confidence:.2f} at ({det.center_x}, {det.center_y})")

# Draw on frame
annotated = detector.draw_detections(frame, detections)

# Benchmark
results = detector.benchmark(n_frames=100)
print(f"FPS: {results['fps_mean']:.1f}")
```

## Detected Classes

| # | Class | Color | Danger? |
|---|-------|-------|---------|
| 0 | with_helmet | 🟢 Green | No |
| 1 | without_helmet | 🔴 Red | ✓ |
| 2 | number_plate | 🟡 Yellow | No |
| 3 | riding | 🔵 Blue | No |
| 4 | triple_ride | 🟠 Orange | ✓ |
| 5 | traffic_violation | 🔴 Red | ✓ |
| 6 | motorcycle | 🔷 Cyan | No |
| 7 | vehicle | 🟣 Purple | No |

Danger classes trigger violations: `without_helmet`, `triple_ride`, `traffic_violation`

## Common Usage Patterns

### Pattern 1: Single Image

```python
from backend import Detector, get_platform_config
import cv2

config = get_platform_config()
detector = Detector(model_path=config.model_path)

image = cv2.imread('test.jpg')
detections = detector.infer(image)
result = detector.draw_detections(image, detections)
cv2.imwrite('output.jpg', result)
```

### Pattern 2: Video Processing

```python
import cv2
from backend import Detector, get_platform_config

config = get_platform_config()
detector = Detector(model_path=config.model_path)

cap = cv2.VideoCapture('video.mp4')
while True:
    ret, frame = cap.read()
    if not ret: break
    
    detections = detector.infer(frame)
    result = detector.draw_detections(frame, detections)
    cv2.imshow('Video', result)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Pattern 3: Real-time Violations Only

```python
from backend import Detector, get_platform_config, get_danger_detections

config = get_platform_config()
detector = Detector(model_path=config.model_path)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    detections = detector.infer(frame)
    violations = get_danger_detections(detections)
    
    if violations:
        print(f"⚠️ {len(violations)} violations!")
        for v in violations:
            print(f"   - {v.class_name}")
        
        # Alert/record/etc
```

### Pattern 4: Performance Monitoring

```python
from backend import Detector, get_platform_config

config = get_platform_config()
detector = Detector(model_path=config.model_path)

# Benchmark
results = detector.benchmark(n_frames=100)
print(f"Device: {config.device_name}")
print(f"Avg: {results['mean_ms']:.1f}ms ({results['fps_mean']:.1f} FPS)")
print(f"Best: {results['min_ms']:.1f}ms ({results['fps_max']:.1f} FPS)")
print(f"Worst: {results['max_ms']:.1f}ms ({results['fps_min']:.1f} FPS)")
```

## Environment Setup

### Create `.env` file

```bash
cp .env.example .env
nano .env
```

Add your configuration:
```bash
# API Keys (optional)
GEMINI_API_KEY=your_key_here
SENDGRID_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./violations.db

# Notifications
NOTIFICATION_EMAIL=your_email@example.com
ALERT_ON_VIOLATION=true
```

## Detection Output Format

Each detection returns:

```python
Detection(
    class_id=0,                 # Class ID (0-7)
    class_name="with_helmet",   # Class name
    confidence=0.95,            # 0-1 confidence score
    x1=100, y1=50,              # Top-left corner (pixels)
    x2=300, y2=250,             # Bottom-right corner (pixels)
    center_x=200, center_y=150, # Center coordinates
    width=200, height=200,      # Bounding box size
    is_danger=False,            # Safety violation?
)
```

## Performance Tips

### For Raspberry Pi
```python
detector = Detector(
    model_path=model_path,
    inference_size=320,    # Smaller = faster
    num_threads=4,         # Limited threads on RPi
    confidence_threshold=0.8,
)
results = detector.benchmark()  # Expect ~10 FPS
```

### For Laptop CPU
```python
detector = Detector(
    model_path=model_path,
    inference_size=416,    # Balanced
    num_threads=4,
    confidence_threshold=0.75,
)
results = detector.benchmark()  # Expect ~30 FPS
```

### For Desktop GPU
```python
detector = Detector(
    model_path=model_path,
    inference_size=640,    # Full resolution
    num_threads=8,
    confidence_threshold=0.75,
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
)
results = detector.benchmark()  # Expect ~60+ FPS
```

## Testing Scripts

### `test_config.py` - Configuration Testing
Tests platform detection and environment settings

```bash
python test_config.py
```

### `test_detector.py` - Detector Testing
Tests inference, preprocessing, visualization

```bash
python test_detector.py
```

### `demo_webcam.py` - Live Detection Demo
Real-time webcam with visualization

```bash
python demo_webcam.py          # Basic
python demo_webcam.py --save-video  # Save output
python demo_webcam.py --max-frames 300  # Limit frames
```

## Troubleshooting

### ❌ "onnxruntime not installed"
```bash
pip install onnxruntime
```

### ❌ "Model not found"
Check model path:
```python
from pathlib import Path
p = Path("exports/tvd_yolo26n_640_20260331.onnx")
print(f"Exists: {p.exists()}")
print(f"Full path: {p.resolve()}")
```

### ❌ Slow inference
- Increase `num_threads`
- Decrease `inference_size`
- Use GPU if available

### ❌ GPU not detected
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## Integration Examples

### FastAPI Server

```python
from fastapi import FastAPI, UploadFile
from backend import Detector, get_platform_config
import cv2
import numpy as np

app = FastAPI()
config = get_platform_config()
detector = Detector(model_path=config.model_path)

@app.post("/detect")
async def detect(file: UploadFile):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    detections = detector.infer(image)
    return {
        "detections": len(detections),
        "violations": sum(1 for d in detections if d.is_danger),
    }
```

### Database Storage

```python
from backend import Detector, get_platform_config, get_settings
from sqlalchemy import create_engine
import datetime

config = get_platform_config()
settings = get_settings()
detector = Detector(model_path=config.model_path)

engine = create_engine(settings.database_url)

detections = detector.infer(frame)
for det in detections:
    if det.is_danger:
        # Store violation
        violation = {
            "class": det.class_name,
            "confidence": det.confidence,
            "timestamp": datetime.datetime.now(),
        }
        # Save to database
```

## Next Steps

1. **Database Integration** — Store violations
2. **REST API** — FastAPI/Flask server
3. **Dashboard** — Visualize violations
4. **Alerts** — Email/SMS notifications
5. **Deployment** — Docker/RPi deployment

## Reference

- YOLO Paper: https://arxiv.org/abs/2405.16243
- ONNX Runtime: https://onnxruntime.ai/
- YOLO26n: Latest end-to-end YOLO variant
- NMS-Free: No post-processing needed

## Support

Check these files for more info:
- `backend/config/README.md` — Configuration details
- `backend/core/README.md` — Detector API reference
- Test scripts: `test_*.py` for usage examples
