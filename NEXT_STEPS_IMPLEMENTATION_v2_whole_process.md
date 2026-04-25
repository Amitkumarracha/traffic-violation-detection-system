# 🚀 Traffic Violation Detection — Next Steps Implementation Guide
## From Trained Model → Full Production System (Cross-Platform: Laptop / PC / RPi)

---

## 📌 PROJECT SUMMARY

| Item | Detail |
|---|---|
| **Model** | YOLOv26n — NMS-free, trained 50 epochs |
| **Accuracy** | mAP50: 85.9% · Precision: 80.5% · Recall: 82.0% |
| **Speed** | 42 FPS (GPU) · 18–25 FPS expected (RPi INT8) |
| **Classes** | 8: with_helmet, without_helmet, number_plate, riding, triple_ride, traffic_violation, motorcycle, vehicle |
| **Exported** | ONNX 9.2MB at exports/tvd_yolo26n_640_20260331.onnx |
| **GAN used** | **SRGAN only** (Real-ESRGAN for plate upscaling) — CycleGAN removed |
| **Augmentation** | albumentations in training config (HSV, mosaic, flip, motion blur) — no GAN |
| **Platforms** | Laptop CPU · Desktop GPU · Raspberry Pi 4B |
| **Database** | SQLite (local/offline) → PostgreSQL (cloud sync) |
| **Verification** | Gemini Flash LLM (only when YOLO conf < 0.90) |
| **Reporting** | PDF evidence report · SHA-256 hash · SendGrid email |

### What is SRGAN doing in this project?
SRGAN (Real-ESRGAN × 4) runs **conditionally** in Thread 4 only when a number plate crop is too small or blurry for PaddleOCR to read reliably (area < 3,000 px² or width < 80px). It upscales the plate 4× before OCR — boosting accuracy from ~60% to ~90% on distant plates. It never runs on every frame.

### What happened to CycleGAN?
**Removed entirely.** Dataset augmentation for adverse conditions (rain, night, fog, motion blur) is handled by `albumentations` transforms already configured in `configs/train_config.yaml`. This is simpler, faster, and produces equally good training data without any GAN training overhead.

### 15-Step Build Plan at a Glance
| Phase | Steps | What gets built |
|---|---|---|
| 1 — Backend Core | 1–5 | Platform config · YOLO detector · DeepSORT tracker · Violation gate · PaddleOCR |
| 2 — GAN | 6 | SRGAN plate upscaler (conditional, Thread 4 only) |
| 3 — Pipeline | 8–9 | 4-thread camera → infer → log orchestrator |
| 4 — Database & API | 10–11 | SQLAlchemy models · FastAPI + WebSocket |
| 5 — Reporting | 12 | Gemini LLM verify · PDF cert · SendGrid email |
| 6 — Launcher | 13 | Universal run.py (auto-detects platform) |
| 7 — Extras | 14–15 | GPS module · INT8 quantisation for RPi |

---

**Current Status:**  
✅ YOLOv26n trained — mAP50: 85.9% | 42 FPS GPU | ONNX exported (9.2MB)  
✅ 8 classes: with_helmet, without_helmet, number_plate, riding, triple_ride, traffic_violation, motorcycle, vehicle  
❌ No SRGAN plate enhancement | No tracking | No real-time pipeline | No backend | No dashboard
> **GAN scope:** SRGAN (Real-ESRGAN) only — for conditional plate super-resolution in Thread 4. No CycleGAN. No offline augmentation. Albumentations handles all dataset augmentation instead.

---

## 📁 TARGET FOLDER STRUCTURE (build this incrementally)

```
traffic_violation_detection/
│
├── exports/                          ← YOUR TRAINED MODEL IS HERE ✅
│   └── tvd_yolo26n_640_20260331.onnx
│
├── backend/                          ← BUILD THIS (entire production system)
│   ├── core/
│   │   ├── detector.py               ← YOLO inference wrapper
│   │   ├── tracker.py                ← DeepSORT multi-frame tracking
│   │   ├── ocr.py                    ← PaddleOCR plate reading
│   │   ├── violation_gate.py         ← 4-stage confirmation logic
│   │   └── gps.py                    ← GPS reader (RPi) / mock (laptop)
│   │
│   ├── gan/
│   │   └── srgan/
│   │       ├── model.py              ← SRGAN/ESRGAN architecture
│   │       ├── inference.py          ← Plate upscaling (4×) — ONLY GAN used
│   │       ├── download_weights.py   ← Auto-download RealESRGAN weights
│   │       └── weights/              ← Pretrained ESRGAN weights (~64MB)
│   │
│   ├── pipeline/
│   │   ├── camera_stream.py          ← Webcam / RPi camera capture thread
│   │   ├── inference_thread.py       ← ONNX inference thread
│   │   ├── postprocess_thread.py     ← OCR + GPS + logging thread
│   │   └── main_pipeline.py          ← 4-thread orchestrator (ENTRY POINT)
│   │
│   ├── api/
│   │   ├── app.py                    ← FastAPI application
│   │   ├── routes/
│   │   │   ├── violations.py         ← GET /violations, POST /report
│   │   │   ├── fraud.py              ← POST /fraud/check
│   │   │   └── health.py             ← GET /health
│   │   └── schemas.py                ← Pydantic request/response models
│   │
│   ├── database/
│   │   ├── models.py                 ← SQLAlchemy DB models
│   │   ├── crud.py                   ← Database operations
│   │   └── connection.py             ← SQLite (local) / PostgreSQL (cloud)
│   │
│   ├── llm/
│   │   └── verifier.py               ← Gemini Flash verification
│   │
│   ├── reporting/
│   │   ├── pdf_generator.py          ← Evidence PDF with SHA-256
│   │   └── email_sender.py           ← SendGrid email dispatch
│   │
│   └── config/
│       ├── settings.py               ← Environment-based config
│       └── platform_detector.py      ← Auto-detect laptop/PC/RPi
│
├── frontend/                         ← React dashboard
│   └── src/
│       ├── components/
│       └── pages/
│
├── docker/
│   ├── Dockerfile.laptop             ← CPU-optimised container
│   ├── Dockerfile.gpu                ← CUDA GPU container
│   └── docker-compose.yml            ← Full stack
│
├── requirements/
│   ├── base.txt                      ← Core dependencies
│   ├── laptop.txt                    ← Laptop/PC extras
│   └── rpi.txt                       ← RPi-specific packages
│
└── run.py                            ← Universal launcher (auto-detects platform)
```

---

---

# PHASE 1 — PRODUCTION BACKEND SETUP
## Step 1: Project scaffold + cross-platform config

### 📋 What to do:
Create the folder structure and a smart config system that auto-detects whether it's running on a laptop, GPU PC, or Raspberry Pi — and adjusts model size, threads, and resolution automatically.

### 🤖 COPILOT PROMPT — Copy this exactly into VS Code Copilot Chat:

```
I have a trained YOLOv26n traffic violation detection model exported as ONNX at:
exports/tvd_yolo26n_640_20260331.onnx

The model detects 8 classes: with_helmet, without_helmet, number_plate, riding, 
triple_ride, traffic_violation, motorcycle, vehicle.

Create the file: backend/config/platform_detector.py

This file must:
1. Auto-detect the running platform: 'raspberry_pi', 'laptop_cpu', 'desktop_gpu'
2. Detection logic:
   - Raspberry Pi: check if /proc/device-tree/model exists and contains "Raspberry Pi"
   - Desktop GPU: check if torch.cuda.is_available() returns True
   - Laptop CPU: fallback for everything else
3. Return a PlatformConfig dataclass with these fields:
   - platform: str ('raspberry_pi' | 'laptop_cpu' | 'desktop_gpu')
   - inference_size: int (320 for RPi, 416 for laptop, 640 for GPU)
   - num_threads: int (4 for RPi, 4 for laptop, 8 for GPU)
   - use_coral: bool (True only if Coral USB TPU detected via usb.core)
   - max_fps_target: int (10 for RPi, 30 for laptop, 60 for GPU)
   - confidence_threshold: float (0.75 always)
   - model_path: str (path to ONNX file)
   - device_name: str (human readable)
4. Add a function get_platform_config() that returns the auto-detected config
5. Add a function print_platform_summary() that pretty-prints the detected config
6. Include try/except for all optional imports (torch, usb.core)

Also create backend/config/settings.py with:
- All API keys loaded from .env file using python-dotenv
- GEMINI_API_KEY
- SENDGRID_API_KEY  
- DATABASE_URL (default: sqlite:///./violations.db)
- SUPABASE_URL and SUPABASE_KEY (optional, for cloud sync)
- A Settings class using pydantic BaseSettings
- A get_settings() function with @lru_cache for singleton pattern
```

---

## Step 2: Core ONNX detector wrapper

### 📋 What to do:
Wrap the ONNX model in a clean Python class that handles preprocessing, inference, and postprocessing. This is the heart of the system — everything else calls this.

### 🤖 COPILOT PROMPT:

```
I have a trained YOLO26n model at exports/tvd_yolo26n_640_20260331.onnx
The model is NMS-free (no post-processing NMS needed).
Output shape: (1, N, 6) where each detection is [class_id, x_center, y_center, width, height, confidence]
All coordinates are normalized 0-1 relative to image size.
The 8 classes in order are: with_helmet, without_helmet, number_plate, riding, triple_ride, traffic_violation, motorcycle, vehicle

Create backend/core/detector.py with:

1. A Detector class that:
   - Takes model_path, inference_size, num_threads, confidence_threshold as constructor args
   - Loads the ONNX model using onnxruntime with CPUExecutionProvider
   - Sets SessionOptions: intra_op_num_threads=num_threads, graph_optimization_level=ORT_ENABLE_ALL
   - Warms up the model with a dummy input on init (call once to avoid first-frame lag)

2. A preprocess(frame) method that:
   - Accepts a BGR numpy array (OpenCV frame)
   - Applies letterbox padding to make it square while preserving aspect ratio
   - Resizes to inference_size × inference_size
   - Converts BGR to RGB
   - Normalizes to 0-1 float32
   - Transposes to (1, 3, H, W) shape
   - Returns (tensor, scale_factor, pad_top, pad_left) for bbox rescaling later

3. An infer(frame) method that:
   - Calls preprocess internally
   - Runs session.run()
   - Filters by confidence >= confidence_threshold
   - Converts normalized coords back to pixel coords using scale_factor and padding offsets
   - Returns a list of Detection namedtuples: (class_id, class_name, confidence, x1, y1, x2, y2)

4. A draw_detections(frame, detections) method that:
   - Draws colored bounding boxes on the frame (different color per class)
   - Adds label text: "no_helmet 0.92"
   - Returns annotated frame

5. A benchmark(n_frames=100) method:
   - Runs n_frames inferences on a dummy image
   - Returns average ms per frame and FPS

Use these class colors: with_helmet=green, without_helmet=red, number_plate=yellow, 
riding=blue, triple_ride=orange, traffic_violation=red, motorcycle=cyan, vehicle=purple

Import from backend/config/platform_detector.py for the config.
```

---

## Step 3: DeepSORT vehicle tracking

### 📋 What to do:
Add multi-frame tracking so each vehicle gets a stable ID across frames. This is critical for the 4-stage violation gate — you need to confirm the same vehicle violates across 3+ consecutive frames.

### 🤖 COPILOT PROMPT:

```
Create backend/core/tracker.py for multi-object vehicle tracking.

I need a VehicleTracker class that wraps the deep_sort_realtime library.
Install: pip install deep-sort-realtime

The tracker must:

1. __init__(max_age=30, n_init=3):
   - max_age: how many frames to keep a track without detection
   - n_init: how many frames needed before a track is confirmed
   - Initialize DeepSort tracker

2. update(detections, frame) method:
   - Input: list of Detection namedtuples from detector.py 
     (class_id, class_name, confidence, x1, y1, x2, y2)
   - Convert to deep_sort format: [[x1,y1,w,h], confidence, class_name]
   - Run tracker.update_tracks(detections_ds, frame=frame)
   - Return list of TrackedObject namedtuples:
     (track_id, class_id, class_name, confidence, x1, y1, x2, y2, is_confirmed)
   - Only return tracks where track.is_confirmed() is True

3. get_track_history(track_id, max_frames=10):
   - Return the last N centroid positions for a track_id
   - Used for speed/direction estimation

4. estimate_speed(track_id, fps=30, pixels_per_meter=50):
   - Calculate pixel displacement per frame → convert to km/h
   - Returns speed in km/h (rough estimate)

5. get_direction_vector(track_id):
   - Returns (dx, dy) normalized direction vector from track history
   - Used for wrong-side detection (negative dx = moving against traffic)

Also add a helper function compute_centroid(x1, y1, x2, y2) that returns (cx, cy).
```

---

## Step 4: 4-Stage violation confirmation gate

### 📋 What to do:
This is what makes your system accurate — a violation is only confirmed after passing 4 checks. Without this you get constant false alerts.

### 🤖 COPILOT PROMPT:

```
Create backend/core/violation_gate.py

This implements a 4-stage violation confirmation gate. A violation is only 
confirmed (logged + reported) after ALL 4 stages pass. This prevents false positives.

Stage 1 — Confidence check: YOLO confidence > 0.75
Stage 2 — Temporal consistency: Same violation class detected for tracked vehicle in 
           3 consecutive frames (use track_id from DeepSORT)
Stage 3 — Motion check: Vehicle speed > 3 km/h (not a parked vehicle)  
Stage 4 — Cooldown: Same track_id cannot trigger again for 30 seconds

Create a ViolationGate class:

1. __init__():
   - frame_buffer: dict[track_id → deque(maxlen=10)] storing recent class detections
   - confirmed_violations: dict[track_id → last_confirmed_timestamp]
   - COOLDOWN_SECONDS = 30
   - CONSECUTIVE_FRAMES_NEEDED = 3
   - MIN_SPEED_KMH = 3.0
   - VIOLATION_CLASSES = ['without_helmet', 'triple_ride', 'traffic_violation']

2. process(tracked_objects, tracker) → list[ConfirmedViolation]:
   - For each tracked_object where class_name is in VIOLATION_CLASSES:
     - Stage 1: check confidence > 0.75
     - Stage 2: append to frame_buffer[track_id], check last 3 are same violation
     - Stage 3: get speed from tracker.estimate_speed(track_id) > MIN_SPEED_KMH
     - Stage 4: check cooldown not active for this track_id
   - If all 4 pass: add to confirmed list, update cooldown timestamp
   - Return list of ConfirmedViolation dataclasses

3. ConfirmedViolation dataclass fields:
   - track_id: int
   - violation_type: str
   - confidence: float  
   - bbox: tuple (x1, y1, x2, y2)
   - timestamp: datetime
   - frame_number: int

4. get_stats() → dict:
   - total_violations_confirmed: int
   - violations_rejected_stage1/2/3/4: int (counters for each stage rejection)
   - false_positive_reduction_rate: float (rejections / total candidates)

Print a log line for each rejection: "Stage 2 REJECT: track_5 only 2/3 frames"
```

---

## Step 5: PaddleOCR plate reader

### 📋 What to do:
Read number plate text from the detected plate bounding box. Only triggers after violation is confirmed (to avoid wasting CPU).

### 🤖 COPILOT PROMPT:

```
Create backend/core/ocr.py for Indian license plate text extraction.

Install: pip install paddleocr paddlepaddle

Create a PlateOCR class:

1. __init__(use_gpu=False):
   - Initialize PaddleOCR with use_angle_cls=False, lang='en', use_gpu=use_gpu, show_log=False
   - Lazy init (don't load on import, load on first call) to save memory

2. preprocess_plate(frame, bbox) → cropped_image:
   - Extract plate region: frame[y1-10:y2+10, x1-10:x2+10] (10px padding)
   - Convert to grayscale
   - Apply Otsu threshold: cv2.threshold(gray, 0, 255, THRESH_BINARY+THRESH_OTSU)
   - If crop width < 100 or height < 25: return None (too small, skip OCR)
   - Return preprocessed crop

3. read_plate(frame, bbox) → PlateResult | None:
   - Call preprocess_plate first
   - If None returned: return None
   - Run PaddleOCR on the crop
   - Extract text and confidence from result[0][0]
   - Clean text: .upper().replace(' ', '').replace('-', '')
   - Apply character corrections: {'O':'0', 'I':'1', 'S':'5', 'B':'8', 'G':'6'}
     BUT only apply corrections in numeric positions (positions 2,3,6,7,8,9)
   - Validate with regex: r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
   - Return PlateResult(text, confidence, is_valid_indian_format)

4. PlateResult dataclass:
   - raw_text: str
   - cleaned_text: str  
   - confidence: float
   - is_valid_indian_format: bool
   - needs_srgan: bool (True if bbox area < 3000 pixels — needs upscaling)

5. should_use_srgan(bbox) → bool:
   - Returns True if plate area (w*h) < 3000 px² OR width < 80px
   - These plates need SRGAN 4× upscale before OCR

Log every OCR attempt: "OCR: MH12AB1234 conf=0.91 valid=True"
Log rejections: "OCR SKIP: plate too small (45x18px)"
```

---

---

# PHASE 2 — GAN INTEGRATION (SRGAN ONLY)
## Step 6: SRGAN for plate super-resolution

### 📋 What to do:
SRGAN upscales small/blurry plate crops 4× before OCR. This is the main GAN component in your live inference pipeline. Only activates when the plate crop is too small for OCR.

### 🤖 COPILOT PROMPT:

```
Create backend/gan/srgan/inference.py for license plate super-resolution.

This uses Real-ESRGAN to upscale small license plate crops 4× before PaddleOCR.
It should only run when the plate crop is smaller than 100×30 pixels.

1. First, create backend/gan/srgan/download_weights.py:
   - Download RealESRGAN_x4plus.pth from GitHub releases if not present
   - URL: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
   - Save to backend/gan/srgan/weights/RealESRGAN_x4plus.pth
   - Show download progress with tqdm
   - Verify file size > 60MB after download

2. Create PlateUpscaler class in backend/gan/srgan/inference.py:

   __init__(scale=4, device='cpu'):
   - Load RealESRGAN model using basicsr library
   - Install: pip install basicsr realesrgan
   - If weights not found: call download_weights.py automatically
   - Set to eval() mode
   - Keep on CPU (RPi has no GPU)
   
   upscale(crop_bgr) → upscaled_bgr:
   - Input: BGR numpy array (small plate crop)
   - Convert BGR → RGB
   - Run through ESRGAN model
   - Convert back RGB → BGR
   - Return 4× larger image
   - Log: "SRGAN: 45x18 → 180x72 in 280ms"

   upscale_if_needed(crop_bgr, threshold_area=3000) → (result_bgr, was_upscaled):
   - Only runs SRGAN if crop area < threshold_area
   - Otherwise returns original unchanged
   - Returns tuple: (image, bool indicating if upscaling was applied)

   benchmark():
   - Run 20 upscaling operations on a 60×20 dummy image
   - Return avg ms per call

3. Create backend/gan/srgan/__init__.py that exports PlateUpscaler

IMPORTANT: SRGAN is CONDITIONAL — only runs when needed, never on every frame.
On Raspberry Pi this takes 200-400ms so it must never block the main pipeline.
Run it in Thread 4 (log thread), never in Thread 3 (inference thread).
```

---

# PHASE 2 — GAN INTEGRATION (SRGAN ONLY)
## Step 6: SRGAN for plate super-resolution

### 📋 What to do:
SRGAN (Real-ESRGAN) upscales small/blurry plate crops 4× before OCR. This is the **only GAN component** in the entire project. It activates conditionally — only when a plate crop is smaller than 100×30 pixels or has area < 3,000 px². All dataset augmentation (rain, night, fog, motion blur) is handled by albumentations, not CycleGAN.

### 🤖 COPILOT PROMPT:

```
Create backend/gan/srgan/inference.py for license plate super-resolution.

This uses Real-ESRGAN to upscale small license plate crops 4× before PaddleOCR.
It should only run when the plate crop is smaller than 100×30 pixels.

NOTE: This is the ONLY GAN used in the entire project. CycleGAN is NOT used.
Dataset augmentation is handled by albumentations (rain, night, fog, motion blur)
in the training pipeline — not by any GAN.

1. First, create backend/gan/srgan/download_weights.py:
   - Download RealESRGAN_x4plus.pth from GitHub releases if not present
   - URL: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
   - Save to backend/gan/srgan/weights/RealESRGAN_x4plus.pth
   - Show download progress with tqdm
   - Verify file size > 60MB after download

2. Create PlateUpscaler class in backend/gan/srgan/inference.py:

   __init__(scale=4, device='cpu'):
   - Load RealESRGAN model using basicsr library
   - Install: pip install basicsr realesrgan
   - If weights not found: call download_weights.py automatically
   - Set to eval() mode
   - Keep on CPU (RPi has no GPU)
   
   upscale(crop_bgr) → upscaled_bgr:
   - Input: BGR numpy array (small plate crop)
   - Convert BGR → RGB
   - Run through ESRGAN model
   - Convert back RGB → BGR
   - Return 4× larger image
   - Log: "SRGAN: 45x18 → 180x72 in 280ms"

   upscale_if_needed(crop_bgr, threshold_area=3000) → (result_bgr, was_upscaled):
   - Only runs SRGAN if crop area < threshold_area
   - Otherwise returns original unchanged
   - Returns tuple: (image, bool indicating if upscaling was applied)

   benchmark():
   - Run 20 upscaling operations on a 60×20 dummy image
   - Return avg ms per call

3. Create backend/gan/srgan/__init__.py that exports PlateUpscaler

IMPORTANT: SRGAN is CONDITIONAL — only runs when needed, never on every frame.
On Raspberry Pi this takes 200-400ms so it must never block the main pipeline.
Run it in Thread 4 (log thread), never in Thread 3 (inference thread).
```

---

> **⚠️ Step 7 (CycleGAN) has been REMOVED from this project.**  
> Dataset augmentation for rain/night/fog is done with **albumentations** in the training config — faster, simpler, no GAN training required.  
> The existing `configs/train_config.yaml` augmentation settings (HSV, rotation, mosaic, mixup) already cover this. No new code needed.

---

# PHASE 3 — 4-THREAD REAL-TIME PIPELINE
## Step 8: Camera capture thread

### 🤖 COPILOT PROMPT:

```
Create backend/pipeline/camera_stream.py

This is Thread 1 in the 4-thread pipeline. It captures frames from the camera 
and puts them in a queue. It must NEVER block or fall behind.

Create a CameraStream class:

1. __init__(source=0, width=1280, height=720, fps=30):
   - source: 0 for webcam, 1 for external camera, or a video file path for testing
   - Supports both laptop webcam AND Raspberry Pi camera module
   - For RPi camera: try picamera2 first, fallback to cv2.VideoCapture(0)

2. start() → threading.Thread:
   - Start capture loop in daemon thread
   - Returns the thread object

3. Internal _capture_loop():
   - Read frames with cap.read()
   - Put frame in self.frame_queue: Queue(maxsize=2)
   - If queue full: get() the old frame first (always keep latest frame)
   - If cap.read() fails 3 times consecutively: log error, attempt reconnect

4. read() → frame | None:
   - Non-blocking get from queue
   - Returns None if no new frame available

5. stop():
   - Set stop event, release cap

6. get_fps() → float:
   - Returns actual measured FPS (count frames per second)

7. is_video_file() → bool:
   - Returns True if source is a file path (for testing mode)

Add platform detection: if running on RPi and picamera2 available, use it.
If running on laptop, use cv2.VideoCapture with DSHOW backend on Windows or 
V4L2 on Linux.

Log on start: "Camera: 1280x720 @ 30fps | Source: webcam | Platform: laptop_cpu"
```

---

## Step 9: Main 4-thread pipeline orchestrator

### 🤖 COPILOT PROMPT:

```
Create backend/pipeline/main_pipeline.py — this is the MAIN ENTRY POINT for 
real-time traffic violation detection.

It orchestrates 4 threads using Python queue.Queue for communication.

Architecture:
  Thread 1 (CameraStream)    → capture_queue (maxsize=2)
  Thread 2 (PreprocessThread) → infer_queue   (maxsize=2)  
  Thread 3 (InferThread)     → result_queue  (maxsize=4)
  Thread 4 (LogThread)       → cloud_queue   (maxsize=10)

Imports needed:
  from backend.core.detector import Detector
  from backend.core.tracker import VehicleTracker
  from backend.core.violation_gate import ViolationGate
  from backend.core.ocr import PlateOCR
  from backend.core.gps import GPSReader
  from backend.gan.srgan.inference import PlateUpscaler
  from backend.config.platform_detector import get_platform_config
  from backend.database.crud import save_violation

Create TrafficViolationPipeline class:

1. __init__(camera_source=0, show_display=True):
   - Load platform config (auto-detects laptop/RPi/GPU)
   - Initialize all components lazy (load on start())
   - show_display: False on RPi headless, True on laptop

2. start():
   - Initialize: Detector, VehicleTracker, ViolationGate, PlateOCR, GPSReader, PlateUpscaler
   - Print startup summary with platform info
   - Start all 4 threads as daemon threads
   - Start display loop if show_display=True

3. Thread 2 — _preprocess_thread():
   - Pull raw frame from capture_queue
   - Apply CLAHE for low-light enhancement  
   - Resize/letterbox for inference
   - Push (original_frame, processed_tensor, frame_id) to infer_queue

4. Thread 3 — _inference_thread():
   - Pull from infer_queue
   - Run detector.infer()
   - Run tracker.update()
   - Run violation_gate.process()
   - If confirmed violations found: push to result_queue
   - Log FPS every 100 frames

5. Thread 4 — _log_thread():
   - Pull from result_queue
   - For each confirmed violation:
     a. Run PlateOCR.read_plate() on the number_plate detection bbox
     b. If needs_srgan: run PlateUpscaler.upscale_if_needed() FIRST
     c. Get GPS coords from GPSReader
     d. Save to SQLite via save_violation()
     e. Push to cloud_queue for async upload
     f. Log: "VIOLATION: without_helmet | Plate: MH12AB1234 | GPS: 18.52,73.85"

6. _display_loop() (main thread):
   - Get latest annotated frame
   - Show FPS, violation count overlay
   - cv2.imshow() — press 'q' to quit

7. stop():
   - Set stop events on all threads
   - Flush queues
   - Print session summary: total violations, total frames, avg FPS

8. get_stats() → dict:
   - uptime_seconds, total_frames, avg_fps, violations_detected, 
     false_positives_rejected, plates_read, srgan_activations

Log every 10 seconds: performance summary with FPS and queue depths.
```

---

---

# PHASE 4 — DATABASE + API
## Step 10: Database models and CRUD

### 🤖 COPILOT PROMPT:

```
Create backend/database/models.py and backend/database/crud.py

Using SQLAlchemy with SQLite for local storage and PostgreSQL for cloud.
Install: pip install sqlalchemy alembic

In models.py, create these SQLAlchemy models:

1. Violation model:
   - id: Integer primary key auto-increment
   - timestamp: DateTime (UTC, default=now)
   - violation_type: String (without_helmet/triple_ride/traffic_violation)
   - plate_number: String nullable (OCR result)
   - plate_confidence: Float nullable
   - confidence: Float (YOLO confidence)
   - latitude: Float nullable
   - longitude: Float nullable
   - image_path: String (path to saved evidence image)
   - sha256_hash: String (hash of the evidence image file)
   - llm_verified: Boolean default False
   - llm_confidence: Float nullable
   - srgan_used: Boolean default False (was SRGAN applied to plate)
   - platform: String (raspberry_pi/laptop_cpu/desktop_gpu)
   - synced_to_cloud: Boolean default False

2. FraudCheck model:
   - id: Integer primary key
   - claim_timestamp: DateTime
   - claim_location_lat: Float
   - claim_location_lng: Float  
   - search_radius_meters: Integer default 200
   - footage_found: Boolean
   - ai_fault_analysis: Text (JSON string from LLM)
   - fraud_score: Float (0-1, higher = more suspicious)
   - created_at: DateTime

In crud.py create:
   - save_violation(db, violation_data: dict) → Violation
   - get_violations(db, skip=0, limit=100) → list[Violation]
   - get_violations_by_type(db, violation_type) → list[Violation]
   - get_unsynced_violations(db) → list[Violation]
   - mark_synced(db, violation_id) → None
   - save_fraud_check(db, fraud_data) → FraudCheck
   - get_violations_near_location(db, lat, lng, radius_km=0.2) → list[Violation]

In connection.py:
   - get_db() generator for dependency injection
   - Create tables on startup
   - Auto-detect: use SQLite if DATABASE_URL not set, PostgreSQL if set
```

---

## Step 11: FastAPI backend

### 🤖 COPILOT PROMPT:

```
Create backend/api/app.py — FastAPI application

Install: pip install fastapi uvicorn python-multipart

The API serves both the React dashboard and external integrations (insurance company).

In app.py:

1. Create FastAPI app with:
   - Title: "Traffic Violation Detection API"
   - CORS enabled for localhost:3000 (React dev) and *
   - Startup event: initialize DB tables, load platform config
   - Include all routers

2. Create backend/api/routes/violations.py:
   
   GET /api/violations:
   - Returns paginated list of violations
   - Query params: skip, limit, violation_type, date_from, date_to
   - Returns list of ViolationResponse schemas
   
   GET /api/violations/{id}:
   - Returns single violation with image URL
   
   GET /api/violations/stats:
   - Returns: total_count, by_type breakdown, hourly_distribution (last 24h),
     top_locations (lat/lng clusters), avg_confidence
   
   GET /api/violations/{id}/image:
   - Serves the evidence image file
   
   POST /api/violations/{id}/verify:
   - Triggers Gemini LLM verification for a specific violation
   - Returns updated violation with llm_confidence

3. Create backend/api/routes/fraud.py:
   
   POST /api/fraud/check:
   - Body: {timestamp, latitude, longitude, plate_number, claim_description}
   - Query DB for violations within 200m radius, ±15 minute window
   - If footage found: run LLM analysis
   - Return: {footage_found, footage_count, ai_analysis, fraud_score, recommendation}

4. Create backend/api/routes/health.py:
   
   GET /api/health:
   - Returns: {status, platform, model_loaded, gpu_available, uptime_seconds,
               db_connection, violations_today, pipeline_fps}

5. Create backend/api/schemas.py with Pydantic models for all request/response types.

Add automatic API documentation at /docs (Swagger UI — built into FastAPI).
Add WebSocket endpoint at /ws/live that streams live violation events to frontend.
```

---

---

# PHASE 5 — REPORTING + LLM VERIFICATION
## Step 12: LLM verifier + PDF report

### 🤖 COPILOT PROMPT:

```
Create backend/llm/verifier.py and backend/reporting/pdf_generator.py

--- verifier.py ---

Create GeminiVerifier class:
Install: pip install google-generativeai

1. __init__():
   - Load GEMINI_API_KEY from settings
   - Initialize genai.GenerativeModel('gemini-1.5-flash')

2. verify_violation(image_path, violation_type, plate_number) → VerificationResult:
   - Load image as bytes
   - Build prompt:
     "You are a traffic enforcement AI. Analyze this image and determine if there 
      is a traffic violation of type: {violation_type}.
      Detected plate: {plate_number}
      Respond ONLY with JSON: 
      {verified: bool, confidence: 0-100, violation_description: str, reasoning: str}"
   - Call model with image + text prompt
   - Parse JSON response
   - Return VerificationResult dataclass
   - If API call fails: return VerificationResult(verified=False, confidence=0, error=str(e))

3. Only call this API when violation confidence < 0.90 (high confidence = skip LLM)
   Log: "LLM verify: SKIP (conf=0.95 > threshold)" or "LLM verify: CALL (conf=0.82)"

--- pdf_generator.py ---

Create EvidenceReport class:
Install: pip install reportlab pillow

1. generate(violation: Violation) → str (returns PDF file path):
   - Creates a professional A4 PDF evidence report
   
   Page layout:
   - Header: "TRAFFIC VIOLATION EVIDENCE REPORT" with logo placeholder
   - Reference: "Report ID: TVD-{violation_id}-{date}"
   
   Section 1 — Violation Details:
   - Type, timestamp, plate number, GPS coordinates, confidence score
   
   Section 2 — Evidence Image:
   - Embed the evidence image (annotated with bounding boxes)
   - Caption: "Original evidence image — unmodified"
   
   Section 3 — Technical Verification:
   - AI model: YOLOv26n | mAP50: 85.9%
   - SRGAN applied: Yes/No
   - LLM verification: Gemini Flash | Confidence: X%
   - SHA-256 hash: {hash_value}
   - Hash verified: This report was generated from unmodified evidence
   
   Section 4 — Legal Notice:
   - "Generated under IT Act 2000, Section 65B, Indian Evidence Act"
   - "SHA-256 hash guarantees evidence integrity"
   - Timestamp footer
   
   Save to: reports/{date}/{report_id}.pdf
   Return the file path

2. Also create backend/reporting/email_sender.py:
   - send_violation_report(violation, pdf_path, recipient_email)
   - Uses SendGrid API
   - Attaches PDF report
   - Subject: "Traffic Violation Report — {plate_number} — {timestamp}"
```

---

---

# PHASE 6 — UNIVERSAL LAUNCHER
## Step 13: Cross-platform run.py launcher

### 🤖 COPILOT PROMPT:

```
Create run.py in the project root — this is the SINGLE ENTRY POINT for running 
the system on ANY platform (laptop, PC, Raspberry Pi).

It must auto-detect the platform and start the appropriate components.

Create a main() function that:

1. Parse command line arguments:
   --mode: 'pipeline' (default) | 'api' | 'full' | 'test'
   --source: camera source (default: 0 for webcam, or video file path)
   --no-display: headless mode flag (auto-set on RPi)
   --port: API port (default: 8000)
   NOTE: 'augment' mode is removed — CycleGAN is not used in this project.

2. Always run first:
   - from backend.config.platform_detector import get_platform_config, print_platform_summary
   - config = get_platform_config()
   - print_platform_summary()

3. Mode: 'pipeline' (real-time detection):
   - from backend.pipeline.main_pipeline import TrafficViolationPipeline
   - pipeline = TrafficViolationPipeline(source=args.source, show_display=not args.no_display)
   - pipeline.start()

4. Mode: 'api' (API server only, no camera):
   - uvicorn.run('backend.api.app:app', host='0.0.0.0', port=args.port, reload=False)

5. Mode: 'full' (pipeline + API simultaneously):
   - Start pipeline in background thread
   - Start FastAPI in main thread
   - Both run concurrently

6. Mode: 'test' (test with video file):
   - Run pipeline with source='test_video.mp4'
   - Auto-stop when video ends
   - Print performance summary

7. Mode: 'test' (test with video file):
   - Run pipeline with source='test_video.mp4'
   - Auto-stop when video ends
   - Print performance summary

8. Print on start:
   ╔══════════════════════════════════════════╗
   ║  Traffic Violation Detection System      ║
   ║  Platform: laptop_cpu                    ║
   ║  Model: YOLOv26n (85.9% mAP50)          ║
   ║  Mode: full                              ║
   ╚══════════════════════════════════════════╝

Also create requirements/base.txt with ALL needed packages with pinned versions:
onnxruntime==1.17.0
opencv-python==4.9.0.80
paddleocr==2.7.3
paddlepaddle==2.6.1
deep-sort-realtime==1.3.2
fastapi==0.110.0
uvicorn==0.27.1
sqlalchemy==2.0.28
pydantic==2.6.3
python-dotenv==1.0.1
google-generativeai==0.4.0
reportlab==4.1.0
tqdm==4.66.2
basicsr==1.4.2
realesrgan==0.3.0
sendgrid==6.11.0
# NOTE: albumentations is used in YOLOv26n training config only (not in backend)
# NOTE: CycleGAN / cyclegan are NOT used — removed from project scope
```

---

---

# PHASE 7 — REMAINING MISSING COMPONENTS (from your checklist)
## Step 14: GPS module (RPi + laptop mock)

### 🤖 COPILOT PROMPT:

```
Create backend/core/gps.py

The system runs on both Raspberry Pi (real GPS) and laptop (mock GPS).
It must work on BOTH with the same interface.

Create GPSReader class:

1. __init__():
   - Auto-detect if gpsd is available (RPi with NEO-6M module)
   - If not available: use MockGPS that returns Pune coordinates 
     (18.5204, 73.8567) with small random jitter to simulate movement

2. start() → threading.Thread:
   - Real GPS: connect to gpsd daemon, start reading in daemon thread
   - Mock GPS: start mock thread that updates coords every second

3. get_location() → GPSLocation | None:
   - Thread-safe read of latest GPS fix
   - Returns GPSLocation(lat, lng, accuracy, timestamp, is_mock)
   - Returns None if no fix available yet (first 30-90 seconds on real GPS)

4. GPSLocation dataclass:
   - latitude: float
   - longitude: float
   - accuracy_meters: float (2.5 for real GPS, 0.0 for mock)
   - timestamp: datetime
   - is_mock: bool (always True on laptop — important for legal use)

5. get_google_maps_url(lat, lng) → str:
   - Returns https://maps.google.com/maps?q={lat},{lng}

6. Real GPS setup instructions in docstring:
   - Hardware: NEO-6M GPS module connected to RPi GPIO 14(TX) / 15(RX)
   - sudo apt install gpsd gpsd-clients
   - sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock
   - pip install gpsd-py3

Log: "GPS: Real fix acquired — 18.5204°N 73.8567°E ±2.5m"
Log: "GPS: Using mock coordinates (laptop mode) — mark evidence as SIMULATION"
```

---

## Step 15: Model quantization for RPi

### 🤖 COPILOT PROMPT:

```
Create scripts/quantize_for_rpi.py

This script quantizes our trained ONNX model to INT8 for faster RPi inference.
Input: exports/tvd_yolo26n_640_20260331.onnx (9.2MB, FP32)
Output: exports/tvd_yolo26n_416_int8.onnx (~2.3MB, INT8) 
        + exports/tvd_yolo26n_320_int8.onnx (~1.4MB, INT8)

Steps to implement:

1. Load calibration images (200 representative images from dataset/images/val/)

2. Create a CalibrationDataReader class implementing onnxruntime.quantization.CalibrationDataReader:
   - Load 200 diverse images from val set
   - Preprocess each: letterbox → 416×416 → BGR→RGB → /255 → float32 → (1,3,416,416)
   - Use a mix of: clear/rain/day/night images for good calibration

3. Run static INT8 quantization:
   from onnxruntime.quantization import quantize_static, CalibrationDataReader, QuantFormat
   quantize_static(
       model_input='exports/tvd_yolo26n_640_20260331.onnx',
       model_output='exports/tvd_yolo26n_416_int8.onnx', 
       calibration_data_reader=reader,
       quant_format=QuantFormat.QOperator,
       per_channel=False,
       reduce_range=True  # Better for ARM
   )

4. Validate quantized model:
   - Run 100 inference passes on test images
   - Compare mAP50 between FP32 and INT8 models
   - PASS if mAP50 drop < 1.5% (acceptable quality loss for 2× speed gain)
   - Print comparison table

5. Benchmark both models:
   - Run 200 frames on dummy input
   - Print: FP32: Xms/frame | INT8: Yms/frame | Speedup: Z×

6. Also export a 320×320 INT8 version for ultra-low-power RPi mode:
   - Re-export from PyTorch at 320px first, then quantize

Print final report:
   ┌─────────────────────────────────────────────┐
   │ Quantization Results                        │
   ├──────────────────┬──────────┬───────────────┤
   │ Model            │ Size     │ RPi FPS (est) │
   ├──────────────────┼──────────┼───────────────┤
   │ FP32 640px       │ 9.2 MB   │ 3-5 FPS       │
   │ FP32 416px       │ 9.2 MB   │ 8-12 FPS      │
   │ INT8 416px ✅    │ 2.3 MB   │ 18-25 FPS     │
   │ INT8 320px       │ 1.4 MB   │ 25-35 FPS     │
   └──────────────────┴──────────┴───────────────┘
```

---

---

# QUICK REFERENCE — EXECUTION ORDER

```
Day 1 (Backend Foundation):
  python run.py --mode test         ← after Steps 1-5 + 8-9

Day 2 (SRGAN + OCR + Pipeline):
  python run.py --mode pipeline     ← after Step 6 (SRGAN) is complete

Day 2 (API):
  python run.py --mode full         ← after Steps 10-11

Day 3 (Production):
  python run.py --mode full --no-display   ← RPi headless deployment
  python scripts/quantize_for_rpi.py       ← optimize ONNX for RPi
```

---

# DEPENDENCIES INSTALL SEQUENCE

```bash
# Step 1: Base inference (all platforms)
pip install onnxruntime opencv-python fastapi uvicorn sqlalchemy \
            pydantic python-dotenv tqdm

# Step 2: OCR  
pip install paddlepaddle paddleocr

# Step 3: Tracking
pip install deep-sort-realtime

# Step 4: SRGAN (the ONLY GAN — for plate super-resolution)
pip install basicsr realesrgan

# Step 5: LLM + Reporting
pip install google-generativeai reportlab sendgrid

# RPi only (run on Pi):
pip install gpsd-py3 picamera2

# NOTE: albumentations is already in your training environment (configs/train_config.yaml)
# It is NOT needed in the backend. CycleGAN is NOT used anywhere in this project.
```

---

*Generated for: traffic_violation_detection project | YOLOv26n mAP50: 85.9% | ONNX: 9.2MB | GAN: SRGAN only (no CycleGAN)*
