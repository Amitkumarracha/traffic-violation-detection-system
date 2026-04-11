# Backend Core Module

YOLO26n Detection Engine for Real-time Traffic Violation Detection

## Overview

The `Detector` class provides:
- **ONNX Inference**: Fast, cross-platform model execution
- **Preprocessing**: Letterbox scaling with aspect ratio preservation
- **Coordinate Conversion**: Normalized → pixel coordinates
- **Visualization**: Colored bounding boxes with labels
- **Benchmarking**: Performance profiling

## Features

### 1. **Fast ONNX Inference** ⚡
- CPU-optimized (thread-configurable)
- GPU support via CUDA execution provider
- Coral TPU support
- No NMS post-processing (NMS-free architecture)

### 2. **Letterbox Preprocessing** 📐
- Preserves aspect ratio
- Adds padding to reach inference size
- Handles any input resolution
- Returns scale factors for coordinate conversion

### 3. **Real-time Detection** 🎯
- Returns structured `Detection` namedtuples
- Confidence filtering
- Danger class identification
- Automatic coordinate transformation

### 4. **8 Traffic Violation Classes** 🚦
1. `with_helmet` (Green) ✅
2. `without_helmet` (Red) ⚠️
3. `number_plate` (Yellow)
4. `riding` (Blue)
5. `triple_ride` (Orange) ⚠️
6. `traffic_violation` (Red) ⚠️
7. `motorcycle` (Cyan)
8. `vehicle` (Purple)

**Danger Classes**: without_helmet, triple_ride, traffic_violation

## Installation

```bash
# Install dependencies
pip install onnxruntime opencv-python numpy

# Or use the requirements file
pip install -r backend_requirements.txt
```

## Usage

### Basic Inference

```python
from backend.core import Detector
from backend.config import get_platform_config
import cv2

# Get optimized config for your platform
config = get_platform_config()

# Initialize detector
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
    confidence_threshold=config.confidence_threshold,
)

# Read image
frame = cv2.imread('traffic.jpg')

# Run inference
detections = detector.infer(frame)

# Draw bounding boxes
annotated = detector.draw_detections(frame, detections)

# Display or save
cv2.imshow('Detections', annotated)
cv2.imwrite('output.jpg', annotated)
```

### Filtering Danger Violations

```python
from backend.core import get_danger_detections

# Get detections
detections = detector.infer(frame)

# Filter to only danger classes
danger_only = get_danger_detections(detections)

if danger_only:
    print(f"⚠️ {len(danger_only)} violations detected!")
    for det in danger_only:
        print(f"  - {det.class_name} at ({det.center_x}, {det.center_y})")
```

### Video Processing

```python
import cv2
from backend.core import Detector
from backend.config import get_platform_config

config = get_platform_config()
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
    confidence_threshold=0.75,
)

# Open video
cap = cv2.VideoCapture('traffic_video.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Output video
out = cv2.VideoWriter(
    'output_video.mp4',
    cv2.VideoWriter_fourcc(*'mp4v'),
    fps,
    (width, height),
)

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detect violations
    detections = detector.infer(frame)
    
    # Draw and write
    annotated = detector.draw_detections(frame, detections)
    out.write(annotated)
    
    frame_count += 1
    if frame_count % 30 == 0:
        print(f"Processed {frame_count} frames, {len(detections)} detections")

cap.release()
out.release()
print("✅ Video processing complete!")
```

### Real-time Webcam

```python
import cv2
from backend.core import Detector, print_detections
from backend.config import get_platform_config

config = get_platform_config()
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
    confidence_threshold=0.75,
)

cap = cv2.VideoCapture(0)  # Webcam

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Inference
    detections = detector.infer(frame)
    
    # Display
    annotated = detector.draw_detections(frame, detections)
    cv2.imshow('Traffic Violations', annotated)
    
    frame_count += 1
    if frame_count % 30 == 0:
        print_detections(detections)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Benchmarking

```python
from backend.core import Detector
from backend.config import get_platform_config

config = get_platform_config()
detector = Detector(
    model_path=config.model_path,
    inference_size=config.inference_size,
    num_threads=config.num_threads,
)

# Run benchmark
results = detector.benchmark(n_frames=100)

print(f"Mean inference: {results['mean_ms']:.2f} ms")
print(f"Mean FPS: {results['fps_mean']:.1f}")
```

## API Reference

### Detector Class

#### Constructor

```python
Detector(
    model_path: str,
    inference_size: int = 640,
    num_threads: int = 4,
    confidence_threshold: float = 0.75,
    providers: Optional[List[str]] = None,
)
```

**Parameters:**
- `model_path`: Path to ONNX model
- `inference_size`: Input size (square)
- `num_threads`: CPU threads
- `confidence_threshold`: Detection confidence cutoff
- `providers`: ONNX execution providers (default: CPU)

#### Methods

##### `infer(frame) -> List[Detection]`

Run inference on a single frame.

**Args:**
- `frame`: BGR numpy array (H, W, 3)

**Returns:**
- List of `Detection` namedtuples

**Example:**
```python
detections = detector.infer(frame)
for det in detections:
    print(f"{det.class_name}: {det.confidence:.2f}")
```

##### `draw_detections(frame, detections, line_thickness=2) -> ndarray`

Draw bounding boxes on frame.

**Args:**
- `frame`: BGR numpy array
- `detections`: List of Detection objects
- `line_thickness`: Line thickness in pixels

**Returns:**
- Annotated BGR frame

**Example:**
```python
annotated = detector.draw_detections(frame, detections, line_thickness=3)
cv2.imshow('Result', annotated)
```

##### `preprocess(frame) -> Tuple[ndarray, float, int, int]`

Preprocess frame (internal use mostly).

**Returns:**
- `tensor`: (1, 3, H, W) float32 RGB
- `scale_factor`: Scaling factor
- `pad_top`: Top padding
- `pad_left`: Left padding

##### `benchmark(n_frames=100, image_size=None) -> dict`

Benchmark inference performance.

**Returns:**
- Dict with timing statistics

**Example:**
```python
results = detector.benchmark(n_frames=50)
print(f"FPS: {results['fps_mean']:.1f}")
```

##### `get_stats() -> dict`

Get detector configuration.

##### `print_stats()`

Pretty-print configuration.

### Detection Namedtuple

```python
Detection(
    class_id: int,           # 0-7
    class_name: str,         # "with_helmet", etc.
    confidence: float,       # 0.0-1.0
    x1: int,                 # Pixel coordinates
    y1: int,
    x2: int,
    y2: int,
    center_x: int,          # Image center coordinates
    center_y: int,
    width: int,              # Bounding box dimensions
    height: int,
    is_danger: bool,         # True if violation class
)
```

## Class Details

### Danger Classes

The following classes trigger violations:
- `without_helmet` — Rider without helmet
- `triple_ride` — 3+ people on motorcycle
- `traffic_violation` — Other detected violations

### Color Mapping

```python
CLASS_COLORS = {
    "with_helmet": (0, 255, 0),           # Green (BGR)
    "without_helmet": (0, 0, 255),        # Red
    "number_plate": (0, 255, 255),        # Yellow
    "riding": (255, 0, 0),                # Blue
    "triple_ride": (0, 165, 255),         # Orange
    "traffic_violation": (0, 0, 255),     # Red
    "motorcycle": (255, 255, 0),          # Cyan
    "vehicle": (128, 0, 128),             # Purple
}
```

## Performance Optimization

### For Raspberry Pi
```python
detector = Detector(
    model_path=model_path,
    inference_size=320,        # Smaller for speed
    num_threads=4,
    confidence_threshold=0.75,
)
```

### For GPU
```python
detector = Detector(
    model_path=model_path,
    inference_size=640,        # Full resolution
    num_threads=8,
    confidence_threshold=0.75,
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
)
```

### For Coral TPU
```python
detector = Detector(
    model_path=model_path,
    inference_size=416,        # Balanced
    providers=['TensorrtExecutionProvider', 'CPUExecutionProvider'],
)
```

## Preprocessing Details

The detector uses letterbox preprocessing:

1. **Aspect Ratio Preservation**: Image resized to fit within inference_size while keeping aspect ratio
2. **Padding**: Gray padding added to make square
3. **Normalization**: 0-255 → 0.0-1.0
4. **Color Conversion**: BGR → RGB
5. **Transposition**: (H, W, 3) → (1, 3, H, W)

Example with 800x600 image and 640 inference size:
```
Original: 800x600
Scale: min(640/800, 640/600) = 0.8
Resized: 640x480
Padded: 640x640 (80px top/bottom gray)
```

Coordinates are converted back using:
```
pixel_x = (normalized_x - pad_left) / scale
pixel_y = (normalized_y - pad_top) / scale
```

## Model Output Format

YOLO26n outputs shape `(1, N, 6)` where:
- `1`: Batch size
- `N`: Number of detections
- `6`: [class_id, x_center, y_center, width, height, confidence]

All coordinates are **normalized** (0-1 relative to image size).

The detector automatically converts to pixel coordinates.

## Troubleshooting

### "onnxruntime is not installed"

```bash
pip install onnxruntime
```

### Slow inference on CPU

- Increase `num_threads`
- Decrease `inference_size`
- Use GPU if available

### Model not found

```python
# Verify model path
from pathlib import Path
model_path = "exports/tvd_yolo26n_640_20260331.onnx"
print(f"Model exists: {Path(model_path).exists()}")
print(f"Absolute path: {Path(model_path).resolve()}")
```

### CUDA not detected

```python
# Check CUDA availability
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

## Next Steps

- Integration with database storage
- Alert system for violations
- Multi-frame tracking
- Dashboard visualization
- API endpoints

## License

Part of Traffic Violation Detection System
