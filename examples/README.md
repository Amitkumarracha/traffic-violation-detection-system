# 📚 Examples & Demonstrations

Quick-start demonstrations for all system components.

## 📁 Folder Structure

```
examples/
├── demos/              Interactive demo scripts
│   ├── demo_main_pipeline.py      Full 4-thread real-time detection
│   ├── demo_camera_stream.py      Camera streaming
│   ├── demo_ocr.py                Plate text recognition
│   ├── demo_srgan.py              Image upscaling
│   ├── demo_tracking.py           Multi-object tracking
│   ├── demo_webcam.py             Webcam capture
│   └── README.md
└── inference/         API and database examples
    ├── example_api_client.py      Query violations via REST API
    ├── example_database.py        Direct database access
    └── README.md
```

## 🚀 Quick Start

### Demo 1: Full Detection Pipeline (BEST START)

```bash
python demos/demo_main_pipeline.py
```

**What it does:**
- Captures video from camera (or default video)
- Detects traffic violations in real-time
- Tracks vehicles across frames
- Extracts and recognizes license plates
- Displays annotated output with statistics
- Press 'q' to quit

**Expected output:**
- Real-time video with bounding boxes (red = violations)
- FPS counter, violation count, queue depths
- Recent violations list

---

### Demo 2: Camera Streaming

```bash
python demos/demo_camera_stream.py
```

**What it does:**
- Captures video from webcam or file
- Demonstrates preprocessing pipeline
- Shows frame enhancement techniques
- Non-blocking queue management

---

### Demo 3: Plate OCR (Text Recognition)

```bash
python demos/demo_ocr.py
```

**What it does:**
- Loads sample plate images
- Recognizes text from plates
- Shows confidence scores
- Displays recognized plate numbers

---

### Demo 4: Image Upscaling (SRGAN)

```bash
python demos/demo_srgan.py
```

**What it does:**
- Takes low-quality plate images
- Upscales 4x using AI super-resolution
- Shows before/after comparison
- Improves OCR accuracy for small plates

---

### Demo 5: Multi-Object Tracking

```bash
python demos/demo_tracking.py
```

**What it does:**
- Shows DeepSort tracker in action
- Tracks vehicles across frames
- Assigns and maintains track IDs
- Demonstrates tracking consistency

---

### Demo 6: Webcam Capture

```bash
python demos/demo_webcam.py
```

**What it does:**
- Simple webcam capture
- Frame preprocessing
- Display options
- Basic image operations

---

## 🔌 API & Database Examples

### Example 1: Query API

```bash
python inference/example_api_client.py
```

**What it demonstrates:**
- List violations (paginated)
- Get violation statistics
- Download violation images
- Check fraud claims
- System health status
- WebSocket connections

**Requirements:**
```bash
# Start API server first
python backend/run_server.py

# In another terminal
python examples/inference/example_api_client.py
```

---

### Example 2: Direct Database Access

```bash
python inference/example_database.py
```

**What it demonstrates:**
- Database connection
- Save violations
- Query violations
- Get statistics
- Fraud check operations
- Direct table access

**No server needed** - connects directly to database.

---

## 📋 Example Categories

### 🎬 Real-Time Processing

| Demo | Purpose | Requirements |
|------|---------|--------------|
| `demo_main_pipeline.py` | Full detection pipeline | Camera/video source |
| `demo_camera_stream.py` | Video capture & preprocessing | Camera/video |
| `demo_tracking.py` | Vehicle tracking | Video with vehicles |

### 🤖 AI/ML Components

| Demo | Purpose | Requirements |
|------|---------|--------------|
| `demo_ocr.py` | Plate text recognition | Plate images |
| `demo_srgan.py` | Image upscaling | Low-res images |
| `demo_detector.py` | YOLO detection | Video/images |

### 💾 Data & API

| Example | Purpose | Requirements |
|---------|---------|--------------|
| `example_api_client.py` | REST API queries | Running API server |
| `example_database.py` | Database operations | SQLite/PostgreSQL |

---

## 🎯 Use Cases

### Use Case 1: I want to see real-time detection

```bash
# Run full pipeline demo
python demos/demo_main_pipeline.py
```

This gives you the complete experience with all components working together.

---

### Use Case 2: I want to test a specific component

```bash
# Test just OCR
python demos/demo_ocr.py

# Test just tracking
python demos/demo_tracking.py

# Test just upscaling
python demos/demo_srgan.py
```

---

### Use Case 3: I want to query violations

```bash
# Start the API
python backend/run_server.py &

# Query violations
python examples/inference/example_api_client.py
```

---

### Use Case 4: I want to work with the database directly

```bash
python examples/inference/example_database.py
```

No API needed - direct database access.

---

## 🔧 Customization

### Change Input Source

In any demo:
```python
# Edit the script
camera_source = 0           # 0 = default camera
camera_source = "video.mp4" # file-based video
camera_source = "rtsp://..." # IP camera stream
```

### Change Output

```python
# Show display
show_display = True

# Hide display
show_display = False

# Save output video
save_video = True
```

### Adjust Parameters

Edit configuration in demo files:
```python
CONF_THRESHOLD = 0.5
NMS_THRESHOLD = 0.4
TRACK_MAX_AGE = 30
```

---

## 🚀 Advanced Usage

### Running Multiple Demos

Terminal 1:
```bash
python demos/demo_main_pipeline.py
```

Terminal 2:
```bash
python examples/inference/example_api_client.py
```

Both run simultaneously - pipeline detects violations, API queries them in real-time.

---

### Custom Demo

Create `my_demo.py`:
```python
from backend.pipeline import TrafficViolationPipeline
from backend.database import get_db_context, get_violations

# Create pipeline
pipeline = TrafficViolationPipeline()

# Start detection
pipeline.start()

# While running in another terminal
# with get_db_context() as db:
#     violations = get_violations(db, limit=10)
#     for v in violations:
#         print(f"Detected: {v.violation_type}")
```

---

## 📊 Performance Notes

### Performance by Demo

| Demo | CPU | Memory | GPU | FPS |
|------|-----|--------|-----|-----|
| demo_main_pipeline | High | 1-2GB | Optional | 15-30 |
| demo_camera_stream | Low | 200MB | No | ~30 |
| demo_ocr | Medium | 500MB | No | ~2 |
| demo_srgan | High | 1GB | Yes | ~5 |
| demo_tracking | Medium | 600MB | Optional | ~20 |

---

## 🐛 Troubleshooting

### Camera not found

```bash
# Check available cameras
python -c "import cv2; cap = cv2.VideoCapture(1); print(cap.isOpened())"

# Use different camera index
# Edit: camera_source = 1  (instead of 0)
```

### Out of memory

```bash
# Reduce frame size
# Edit: frame_width = 640 (instead of 1280)

# Or disable display
# show_display = False
```

### API connection refused

```bash
# Start API server first
python backend/run_server.py

# Wait 2s for startup
# Then run: python examples/inference/example_api_client.py
```

### Database locked

```bash
# Close other connections
# Or use PostgreSQL instead of SQLite
# Set DATABASE_URL environment variable
```

---

## 📚 Next Steps

1. **Run a demo**
   ```bash
   python demos/demo_main_pipeline.py
   ```

2. **Modify it**
   - Change input source
   - Adjust parameters
   - Add custom logic

3. **Integrate it**
   - Import into your code
   - Extend functionality
   - Add your own components

## ✨ Key Demos

✅ `demo_main_pipeline.py` - Best for understanding full system
✅ `example_api_client.py` - Best for API integration
✅ `example_database.py` - Best for data engineering

---

**Ready to explore? Start with `demo_main_pipeline.py`! 🎬**
