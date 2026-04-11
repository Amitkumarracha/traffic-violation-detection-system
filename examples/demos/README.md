# 🎮 Demo Scripts

Interactive demonstrations of all system components. Perfect for understanding how each part works.

## 📁 Demo Folder Structure

```
examples/demos/
├── demo_main_pipeline.py          Complete 4-thread pipeline
├── demo_camera_stream.py           Video capture & preprocessing
├── demo_ocr_pipeline.py            Plate recognition
├── demo_srgan_pipeline.py          Image upscaling (4x)
├── demo_detector.py                YOLO object detection
├── demo_tracker.py                 DeepSort multi-object tracking
├── demo_augmentation.py            Data augmentation techniques
└── demo_webcam.py                  Real-time webcam demo
```

---

## 🚀 Quick Start

### Run the Main Demo (Recommended for First Time)

```bash
cd examples/demos/

# Run main pipeline demo
python demo_main_pipeline.py

# Expected output:
# ✓ Pipeline initialized
# ✓ Processing frame 1/100
# ✓ Detected 2 vehicles
# ✓ Tracked 2 vehicles
# ✓ Violations: 0
```

### Run All Demos

```bash
# Run each demo in sequence
python demo_detector.py
python demo_tracker.py
python demo_ocr_pipeline.py
python demo_srgan_pipeline.py
python demo_camera_stream.py
python demo_augmentation.py
python demo_webcam.py
python demo_main_pipeline.py
```

---

## 📚 Demo Descriptions

### 1️⃣ Main Pipeline Demo

**File:** `demo_main_pipeline.py`

**What it shows:**
- Complete 4-thread pipeline in action
- All components working together
- Statistics and performance metrics
- End-to-end flow from camera to database

**When to use:**
- First introduction to system
- Showcasing to management/clients
- Validating full system installation

**Run:**
```bash
python demo_main_pipeline.py
```

**What happens:**
1. Initializes all components (detector, tracker, OCR, SRGAN, etc.)
2. Loads sample video or camera stream
3. Processes frames through pipeline
4. Displays detections and tracks
5. Shows violations detected
6. Prints performance stats

**Output example:**
```
🎬 Main Pipeline Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Detector loaded: YOLOv8n
✓ Tracker initialized
✓ OCR ready
✓ SRGAN ready
✓ Processing frames...

Frame 1: 2 vehicles, 2 tracks, 0 violations
Frame 2: 2 vehicles, 2 tracks, 1 violation (speeding)
Frame 3: 3 vehicles, 3 tracks, 1 violation (no helmet)

Stats:
├─ FPS: 25
├─ Avg detection time: 40ms
├─ Memory usage: 1.2GB
└─ Total violations: 4
```

**Key files used:**
- `backend/pipeline/main_pipeline.py`
- `backend/core/detector.py`
- `backend/core/tracker.py`
- `backend/core/ocr.py`
- `backend/core/srgan.py`

---

### 2️⃣ Detector Demo

**File:** `demo_detector.py`

**What it shows:**
- YOLO object detection
- Bounding box visualization
- Confidence scores
- Class labels
- FPS performance

**When to use:**
- Check detector accuracy
- Debug detection failures
- Validate model loading
- Performance testing

**Run:**
```bash
python demo_detector.py --image input.jpg
python demo_detector.py --video traffic.mp4
python demo_detector.py --camera 0  # webcam
```

**What happens:**
1. Loads YOLOv8n model
2. Processes input image/video
3. Detects vehicles and helmets
4. Draws bounding boxes
5. Displays confidence scores
6. Shows performance metrics

**Output example:**
```
🎯 Detector Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Model loaded: yolov8n.pt
✓ Processing frame...

Detections:
├─ Car (0.95) at [100, 50, 200, 150]
├─ Motorcycle (0.87) at [400, 100, 500, 250]
├─ Person (0.92) at [420, 120, 480, 220]
└─ Helmet (0.78) at [435, 130, 465, 160]

Performance:
├─ Detection time: 42ms
└─ FPS: 24
```

**Command-line options:**
```bash
--image PATH          Input image file
--video PATH          Input video file
--camera ID           Webcam ID (default: 0)
--conf THRESHOLD      Confidence threshold (default: 0.5)
--iou THRESHOLD       IOU threshold (default: 0.5)
--device cuda/cpu     Device to use (default: auto)
--visualize           Show visualization
```

**Key files used:**
- `backend/core/detector.py`

---

### 3️⃣ Tracker Demo

**File:** `demo_tracker.py`

**What it shows:**
- DeepSort multi-object tracking
- Track IDs consistency
- Track aging and deletion
- Re-identification
- Performance metrics

**When to use:**
- Check tracking stability
- Debug ID jumps
- Validate track persistence
- Test re-identification

**Run:**
```bash
python demo_tracker.py --video traffic.mp4
python demo_tracker.py --camera 0
```

**What happens:**
1. Loads DeepSort tracker
2. Processes video with detector
3. Assigns track IDs
4. Follows objects across frames
5. Handles track aging
6. Shows tracking statistics

**Output example:**
```
🔄 Tracker Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Tracker initialized

Frame 1:
├─ Track 1 (Car): confidence 0.95
├─ Track 2 (Motorcycle): confidence 0.87
└─ New tracks created: 2

Frame 2:
├─ Track 1 (Car): confidence 0.96 [SAME]
├─ Track 2 (Motorcycle): confidence 0.88 [SAME]
└─ No re-identifications

Tracking Stats:
├─ Total tracks: 2
├─ Active tracks: 2
├─ Deleted tracks: 0
└─ Re-identifications: 0
```

**Command-line options:**
```bash
--video PATH          Input video file
--camera ID           Webcam ID
--max-age N           Track max age (default: 30)
--min-hits N          Min hits to init track (default: 3)
--visualize           Show visualization
```

**Key files used:**
- `backend/core/tracker.py`
- `backend/core/deep_sort/`

---

### 4️⃣ OCR Pipeline Demo

**File:** `demo_ocr_pipeline.py`

**What it shows:**
- License plate recognition
- Text extraction from plates
- Confidence scores
- Multiple plate handling
- Character-level accuracy

**When to use:**
- Check OCR accuracy
- Debug text recognition
- Test on different plate formats
- Validate character detection

**Run:**
```bash
python demo_ocr_pipeline.py --image plate.jpg
python demo_ocr_pipeline.py --video traffic.mp4
python demo_ocr_pipeline.py --camera 0
```

**What happens:**
1. Loads OCR model
2. Detects license plates (uses detector)
3. Extracts plate regions
4. Recognizes text
5. Filters by confidence
6. Displays results with accuracy

**Output example:**
```
📋 OCR Pipeline Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ OCR model loaded

Detected Plates:
├─ Plate 1: "AB12CD" (confidence: 0.94)
│  ├─ A: 0.98, B: 0.97, 1: 0.96
│  ├─ 2: 0.91, C: 0.92, D: 0.95
│  └─ Bounding box: [240, 180, 320, 210]
├─ Plate 2: "XY34ZW" (confidence: 0.88)
│  ├─ X: 0.94, Y: 0.93, 3: 0.87
│  ├─ 4: 0.89, Z: 0.86, W: 0.88
│  └─ Bounding box: [500, 160, 580, 190]

Stats:
├─ Plates detected: 2
├─ Recognition rate: 100%
└─ Avg confidence: 0.91
```

**Command-line options:**
```bash
--image PATH          Input image file
--video PATH          Input video file
--camera ID           Webcam ID
--conf THRESHOLD      Confidence threshold
--visualize           Show visualization
```

**Key files used:**
- `backend/core/ocr.py`
- `backend/core/detector.py` (for plate detection)

---

### 5️⃣ SRGAN Pipeline Demo

**File:** `demo_srgan_pipeline.py`

**What it shows:**
- Image super-resolution (4x upscaling)
- Before/after comparison
- Quality improvement visualization
- Processing time
- Memory usage

**When to use:**
- Check image enhancement quality
- Benchmark super-resolution performance
- Improve OCR accuracy with upscaling
- Visual quality assessment

**Run:**
```bash
python demo_srgan_pipeline.py --image low_res.jpg
python demo_srgan_pipeline.py --video traffic.mp4
python demo_srgan_pipeline.py --camera 0
```

**What happens:**
1. Loads SRGAN model (4x upscaler)
2. Loads input image/video
3. Upscales each frame 4x
4. Shows before/after
5. Displays quality metrics
6. Saves comparison images

**Output example:**
```
🚀 SRGAN Pipeline Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ SRGAN model loaded

Upscaling...
Original: 640x480 → Upscaled: 2560x1920

Results:
├─ Processing time: 250ms
├─ Memory used: 450MB
├─ PSNR improvement: +8.2dB
├─ SSIM improvement: +0.12
└─ Quality: Excellent ✓

Comparison saved to:
└─ output/comparison.jpg
```

**Command-line options:**
```bash
--image PATH          Input image file
--video PATH          Input video file
--camera ID           Webcam ID
--scale FACTOR        Upscaling factor (default: 4)
--visualize           Show visualization
--save-output         Save upscaled output
```

**Key files used:**
- `backend/core/srgan.py`

---

### 6️⃣ Camera Stream Demo

**File:** `demo_camera_stream.py`

**What it shows:**
- Video frame capture
- Preprocessing steps
- Frame rate stability
- Resolution handling
- Stream quality

**When to use:**
- Test camera/video file
- Check stream settings
- Debug frame capture issues
- Verify preprocessing

**Run:**
```bash
python demo_camera_stream.py --camera 0
python demo_camera_stream.py --video traffic.mp4
```

**What happens:**
1. Opens video source
2. Captures frames
3. Applies preprocessing
4. Shows frame info
5. Displays stream stats
6. Real-time statistics

**Output example:**
```
📹 Camera Stream Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Stream initialized

Source: Local Webcam (0)
Resolution: 640x480
FPS: 30
Codec: MJPEG

Frame 1: Size 640x480, dtype uint8
Frame 2: Size 640x480, dtype uint8
...
Frame 100:
├─ FPS: 29.8
├─ Avg frame time: 33.5ms
├─ Dropped frames: 0
└─ Stream health: Excellent ✓
```

**Command-line options:**
```bash
--camera ID           Webcam ID (default: 0)
--video PATH          Input video file path
--fps N               Target FPS (default: 30)
--resolution WxH      Resolution (default: 640x480)
--show-frames N       Show first N frames (default: 100)
```

**Key files used:**
- `backend/core/camera_stream.py`
- `backend/core/preprocessing.py`

---

### 7️⃣ Augmentation Demo

**File:** `demo_augmentation.py`

**What it shows:**
- Data augmentation techniques
- Various transformations
- Augmentation quality
- Effect on model training
- Visual examples

**When to use:**
- Understand data augmentation
- Test augmentation parameters
- Generate training data samples
- Validate preprocessing

**Run:**
```bash
python demo_augmentation.py --image sample.jpg --output ./augmented/
python demo_augmentation.py --dataset path/to/dataset
```

**What happens:**
1. Loads input image(s)
2. Applies various augmentations:
   - Horizontal flip
   - Vertical flip
   - Rotation (±15°)
   - Brightness/contrast adjustment
   - Blur/noise
   - Affine transforms
3. Saves augmented versions
4. Shows comparisons

**Output example:**
```
🎨 Augmentation Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Augmentation pipeline loaded

Original image: sample.jpg (640x480)

Augmentations applied:
├─ Flip horizontal → flipped_h.jpg
├─ Flip vertical → flipped_v.jpg
├─ Rotate +15° → rotated_p15.jpg
├─ Rotate -15° → rotated_m15.jpg
├─ Brightness +0.2 → bright_p0.2.jpg
├─ Contrast +0.3 → contrast_p0.3.jpg
├─ Gaussian blur (σ=1) → blur_1.jpg
├─ Gaussian noise → noise.jpg
└─ Affine transform → affine.jpg

Total: 9 augmented images
Output directory: ./augmented/
```

**Command-line options:**
```bash
--image PATH          Input image file
--dataset PATH        Input dataset directory
--output PATH         Output directory (default: ./augmented/)
--num-aug N           Number of variations (default: 9)
--intensity LEVEL     Augmentation intensity (default: medium)
--visualize           Show side-by-side comparison
```

**Key files used:**
- `backend/core/preprocessing.py`
- `backend/core/augmentation.py`

---

### 8️⃣ Webcam Demo

**File:** `demo_webcam.py`

**What it shows:**
- Real-time webcam detection
- Live tracking while webcam running
- Violations in real-time
- FPS counter
- Interactive controls

**When to use:**
- Live system demonstration
- Real-time testing
- Performance monitoring
- Interactive exploration

**Run:**
```bash
python demo_webcam.py --camera 0
```

**Keyboard Controls:**
```
SPACE   - Pause/resume
P       - Print statistics
S       - Save frame
R       - Reset stats
Q       - Quit
```

**What happens:**
1. Opens webcam
2. Initializes all components
3. Processes frames in real-time
4. Displays detections/tracks
5. Highlights violations
6. Shows live FPS counter

**Output example:**
```
🎥 Live Webcam Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Webcam opened
✓ All components ready

[Webcam window opens with overlays]

Live stats (bottom-right):
├─ FPS: 24
├─ Detections: 2
├─ Tracks: 2
├─ Violations: 1 (🚨 Helmet violation)

Controls:
├─ SPACE to pause
├─ P for stats
├─ S to save
├─ Q to quit
```

**Command-line options:**
```bash
--camera ID           Webcam ID (default: 0)
--conf THRESHOLD      Detection confidence (default: 0.5)
--show-boxes          Show bounding boxes
--show-tracks         Show track lines
--show-violations     Highlight violations
--record-video        Record output video
```

**Key files used:**
- `backend/pipeline/main_pipeline.py`
- `backend/core/camera_stream.py`
- `backend/core/detector.py`
- `backend/core/tracker.py`

---

## 🎯 Choosing the Right Demo

### "I just started"
**→ Run:** `python demo_main_pipeline.py`

### "I want to understand detection"
**→ Run:** `python demo_detector.py --image sample.jpg`

### "I want to see tracking"
**→ Run:** `python demo_tracker.py --video example.mp4`

### "I need to check OCR"
**→ Run:** `python demo_ocr_pipeline.py --image plate.jpg`

### "Show me live system"
**→ Run:** `python demo_webcam.py --camera 0`

### "I'm doing data augmentation"
**→ Run:** `python demo_augmentation.py --image sample.jpg`

### "I need to validate camera"
**→ Run:** `python demo_camera_stream.py --camera 0`

### "I want to see image upscaling"
**→ Run:** `python demo_srgan_pipeline.py --image low_res.jpg`

---

## 📊 Demo Comparison

| Demo | Components | Input | Output | Time |
|------|-----------|-------|--------|------|
| Main Pipeline | All | Video/Camera | Detections + Violations | 5-10s |
| Detector | YOLO | Image/Video | Detections | 2-5s |
| Tracker | DeepSort | Video | Tracks | 2-5s |
| OCR | OCR | Image/Video | Text | 2-5s |
| SRGAN | Upscaler | Image | Upscaled | 5-15s |
| Camera | Stream | Camera/Video | Frames | 5-10s |
| Augmentation | Transforms | Image/Dataset | Augmented | 5-10s |
| Webcam | All | Live Camera | Real-time | Live |

---

## 🚨 Troubleshooting Demos

### Demo fails to start

**Problem:** Module not found
```bash
ModuleNotFoundError: No module named 'backend'
```

**Solution:**
```bash
cd examples/demos/
cd ../../  # Go to project root
python examples/demos/demo_main_pipeline.py
```

---

### Demo runs but no output

**Problem:** Model files missing
```
FileNotFoundError: yolov8n.pt not found
```

**Solution:**
```bash
# Download models
python scripts/download_models.py

# Or move them manually
cp model_training/models/*.pt .
```

---

### Demo is very slow (< 1 FPS)

**Problem:** Running on CPU instead of GPU

**Solution:**
```bash
# Check GPU
python -c "import torch; print(torch.cuda.is_available())"

# Force GPU usage
python demo_main_pipeline.py --device cuda
```

---

### Webcam demo shows no image

**Problem:** Camera not initialized properly

**Solution:**
```bash
# List available cameras
python -c "import cv2; print(cv2.VideoCapture(0).get(cv2.CAP_PROP_FRAME_WIDTH))"

# Try different camera IDs
python demo_webcam.py --camera 0
python demo_webcam.py --camera 1
python demo_webcam.py --camera 2
```

---

## 📈 Performance Expectations

### On GPU (NVIDIA RTX 3060)

| Demo | Speed | Memory |
|------|-------|--------|
| Detector | ~25 FPS | 1.2 GB |
| Tracker | ~25 FPS | 1.5 GB |
| OCR | ~20 FPS | 1.0 GB |
| SRGAN | ~10 FPS | 2.0 GB |
| Pipeline | ~20 FPS | 2.5 GB |
| Webcam | ~20 FPS | 2.5 GB |

### On CPU (i7-9700K)

| Demo | Speed | Memory |
|------|-------|--------|
| Detector | ~3 FPS | 800 MB |
| Tracker | ~3 FPS | 1.0 GB |
| OCR | ~2 FPS | 600 MB |
| SRGAN | ~0.5 FPS | 1.5 GB |
| Pipeline | ~2 FPS | 1.2 GB |

---

## 🎓 Learning Path

1. **Day 1:** Run `demo_main_pipeline.py`
2. **Day 2:** Run individual component demos
3. **Day 3:** Try with your own data
4. **Day 4:** Customize demo parameters
5. **Day 5:** Explore source code

---

## 📞 Getting Help

- **Slow performance?** Check [docs/guides/CUDA_YOLO_DIAGNOSIS.md](../../docs/guides/CUDA_YOLO_DIAGNOSIS.md)
- **Can't load models?** Check [docs/guides/SETUP_VERIFICATION.md](../../docs/guides/SETUP_VERIFICATION.md)
- **Errors running?** Check [docs/guides/ISSUE_RESOLUTION.md](../../docs/guides/ISSUE_RESOLUTION.md)
- **Want to understand?** Read [docs/guides/](../../docs/guides/)

---

**Happy exploring! 🚀**
