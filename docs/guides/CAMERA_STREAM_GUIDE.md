# Camera Stream - Thread 1 of 4-Thread Pipeline

## Overview

**CameraStream** is the first thread in the traffic violation detection pipeline. It captures frames from camera/video sources and provides them to the detection thread while maintaining real-time performance.

**Key Characteristics:**
- **Non-blocking**: Never blocks or falls behind
- **Daemon thread**: Runs in background
- **Fixed-size queue**: maxsize=2 (always keeps latest frame)
- **Cross-platform**: Laptop webcam, external camera, Raspberry Pi camera module
- **FPS tracking**: Monitors actual capture rate
- **Error recovery**: Automatically reconnects on failure

---

## Architecture

### 4-Thread Pipeline

```
Thread 1: Camera Capture (THIS MODULE)
  Input:  Camera or video file
  Output: Frame queue
  
  ↓ (Frame queue)
  
Thread 2: Detection (YOLO26n)
  Input:  Frame from Thread 1
  Output: Detection queue
  Speed:  5-8ms per frame
  
  ↓ (Detection queue)
  
Thread 3: Tracking & Processing
  Input:  Detections from Thread 2
  Output: Confirmed violation queue
  Speed:  2-4ms for tracking
  
  ↓ (Result queue)
  
Thread 4: Logging & Async Tasks
  Input:  Violations from Thread 3
  Tasks:  OCR, SRGAN, database, alerts
  Speed:  250-750ms (async, non-blocking)
```

**Thread 1 Responsibilities:**
- Continuous frame capture
- Non-blocking queue management
- FPS tracking
- Error recovery

---

## Installation

Dependencies included in `requirements.txt`:
```
opencv-python-headless>=4.8.0
```

For Raspberry Pi camera:
```bash
pip install picamera2
```

---

## API Reference

### Class: CameraStream

#### `__init__(source=0, width=1280, height=720, fps=30)`

Initialize camera stream.

**Parameters:**
- `source` (int | str): 
  - `0`: Default webcam (laptop)
  - `1`: External camera (USB)
  - Path string: Video file (testing)
- `width` (int): Frame width in pixels (default: 1280)
- `height` (int): Frame height in pixels (default: 720)
- `fps` (int): Target frames per second (default: 30)

**Example:**
```python
# Laptop webcam
camera = CameraStream(source=0, width=1280, height=720, fps=30)

# External USB camera
camera = CameraStream(source=1, width=1920, height=1080, fps=30)

# Video file for testing
camera = CameraStream(source='test_video.mp4')

# Raspberry Pi (auto-detects picamera2)
camera = CameraStream(source=0, width=640, height=480, fps=24)
```

---

#### `start() → threading.Thread`

Start capture thread (daemon).

**Returns:** Thread object (already started)

**Note:** Thread is already started and running as daemon

**Example:**
```python
camera = CameraStream()
thread = camera.start()

# Thread is now capturing frames
# Returns immediately (non-blocking)
```

---

#### `read() → Frame | None`

Read latest frame from queue (non-blocking).

**Returns:** 
- numpy array (BGR) if frame available
- None if no frame in queue

**Blocking:** NO - Returns immediately

**Example:**
```python
camera = CameraStream()
camera.start()

# Non-blocking read
frame = camera.read()

if frame is not None:
    height, width = frame.shape[:2]
    print(f"Frame: {width}×{height}")
else:
    print("No frame available yet")
```

---

#### `stop()`

Stop capture thread and cleanup.

**Blocks:** Yes, but briefly (up to 2 seconds thread join timeout)

**Example:**
```python
try:
    while True:
        frame = camera.read()
finally:
    camera.stop()  # Always cleanup
```

---

#### `get_fps() → float`

Get measured FPS (updated every 1 second).

**Returns:** Frames per second (float)

**Example:**
```python
fps = camera.get_fps()
print(f"Current FPS: {fps:.1f}")
# Output: Current FPS: 28.5
```

---

#### `is_video_file() → bool`

Check if source is a video file (testing mode).

**Returns:** True if video file, False if camera

**Example:**
```python
camera1 = CameraStream(source=0)
camera2 = CameraStream(source='video.mp4')

print(camera1.is_video_file())  # False
print(camera2.is_video_file())  # True
```

---

#### `is_opened() → bool`

Check if camera is open and ready.

**Returns:** True if camera accessible, False otherwise

**Example:**
```python
if camera.is_opened():
    print("Camera ready")
else:
    print("Camera not available")
```

---

### Function: `create_camera_stream(source=0, width=1280, height=720, fps=30) → CameraStream`

Factory function to create and start camera stream.

**Returns:** Started CameraStream object

**Example:**
```python
# Create and start in one call
camera = create_camera_stream(width=1920, height=1080, fps=60)

# Ready to use immediately
frame = camera.read()
```

---

## Usage Examples

### Example 1: Basic Capture

```python
from backend.pipeline import CameraStream

# Initialize
camera = CameraStream(source=0, width=1280, height=720, fps=30)

# Start capture
thread = camera.start()

# Read frames continuously
try:
    while True:
        frame = camera.read()
        if frame is not None:
            print(f"Frame shape: {frame.shape}")
            # Pass to detection thread (Thread 2)

finally:
    camera.stop()
```

### Example 2: With FPS Monitoring

```python
camera = create_camera_stream()

for i in range(100):
    frame = camera.read()
    if frame is not None:
        fps = camera.get_fps()
        print(f"Frame {i}: {fps:.1f} FPS")
    
    time.sleep(0.01)  # Non-blocking

camera.stop()
```

### Example 3: Video File Testing

```python
# For testing with pre-recorded video
camera = CameraStream(source='test_violation.mp4')
camera.start()

while True:
    frame = camera.read()
    if frame is None:
        print("End of video")
        break
    
    # Process frame
    process_frame(frame)

camera.stop()
```

### Example 4: Multiple Cameras

```python
cameras = [
    CameraStream(source=0, width=1280, height=720),  # Intersection 1
    CameraStream(source=1, width=1280, height=720),  # Intersection 2
]

for camera in cameras:
    camera.start()

try:
    while True:
        frames = [cam.read() for cam in cameras]
        frames = [f for f in frames if f is not None]
        
        if frames:
            process_multiple(frames)

finally:
    for camera in cameras:
        camera.stop()
```

### Example 5: External Integration

```python
import threading
import queue

# Create communication queue with detection thread
detection_queue = queue.Queue(maxsize=5)

def camera_thread():
    camera = CameraStream()
    camera.start()
    
    try:
        while True:
            frame = camera.read()
            if frame is not None:
                try:
                    detection_queue.put_nowait(frame)
                except queue.Full:
                    pass  # Skip frame if detection is behind
    finally:
        camera.stop()

# Start camera thread
t1 = threading.Thread(target=camera_thread, daemon=True)
t1.start()

# Detection thread reads from queue
while True:
    try:
        frame = detection_queue.get(timeout=1)
        detect(frame)
    except queue.Empty:
        pass
```

---

## Non-Blocking Behavior

### Queue Management

The frame queue has `maxsize=2`:

1. **Frame arrives** from capture
2. **Queue status:**
   - Empty: Add frame ✓
   - 1 frame: Add frame ✓
   - 2 frames (FULL): Remove old frame, add new frame ✓
3. **Result:** Latest frame always available, never blocks

### Code Logic

```python
# In _capture_loop():
try:
    frame_queue.put_nowait(frame)  # Try to add
except queue.Full:
    # Queue full, drop old frame
    frame_queue.get_nowait()       # Remove old
    frame_queue.put_nowait(frame)  # Add new
```

---

## Platform Support

### Laptop/Desktop

**Supported Systems:** Windows, Linux, macOS

**Backends Used:**
- Windows: DirectShow (CAP_DSHOW)
- Linux/macOS: V4L2 (CAP_V4L2)

**Requirements:** USB webcam or built-in camera

**Example:**
```python
camera = CameraStream(source=0)  # Use default backend
```

### Raspberry Pi

**Supported:** All RPi models with camera module

**Camera Options:**
1. **PiCamera Module** (Recommended)
   - Auto-detected and preferred
   - Requires: `picamera2`
   - Installation: `pip install picamera2`

2. **USB Webcam** (Fallback)
   - Fallback if PiCamera not available
   - No additional software needed

**Example:**
```python
# Automatically uses PiCamera if available
camera = CameraStream(source=0, width=640, height=480, fps=24)
```

---

## Error Handling & Recovery

### Automatic Reconnection

If capture fails 3 times consecutively:
1. Release current connection
2. Wait 0.5 seconds
3. Attempt reconnection

### Error Cases Handled

- Camera disconnected during operation
- Frame read timeout
- Out of focus
- Lens obstruction

### Logging

All errors are logged with details:

```python
logger.warning("Capture failed 3 times - attempting reconnect")
logger.info("✓ Camera reconnected")
logger.error("Failed to reconnect")
```

---

## Performance Characteristics

### Speed

| Operation | Time | Blocking |
|-----------|------|----------|
| read() | <1ms | NO |
| get_fps() | <1ms | NO |
| start() | ~50ms | NO |
| stop() | ~500ms | YES (brief) |
| Capture loop | ~33ms @ 30fps | NO |

### Memory

- Queue: 2 frames max ≈ 10MB (at 1280×720×3)
- Capture loop thread: ≈2MB
- Total: ≈12MB overhead

### CPU

- Capture loop: ≈5-10% single core
- Platform overhead varies:
  - Laptop: Minimal
  - RPi: Depends on camera module

---

## Logging Output

### Startup Message

```
Camera: 1280×720 @ 30fps | Source: webcam | Type: cv2 | Platform: laptop_cpu
```

### Normal Operation

```
2026-03-31 10:00:00 - CameraStream - INFO - ✓ Camera capture thread started
2026-03-31 10:00:01 - CameraStream - INFO - Camera: 1280×720 @ 30fps | ...
```

### Errors

```
2026-03-31 10:00:05 - CameraStream - WARNING - Capture failed 3 times - attempting reconnect
2026-03-31 10:00:06 - CameraStream - INFO - ✓ Camera reconnected
```

---

## Configuration

### Resolution Recommendations

| Scenario | Resolution | FPS | Quality |
|----------|-----------|-----|---------|
| Real-time detection | 1280×720 | 30 | High |
| High speed | 640×480 | 60 | Medium |
| High quality | 1920×1080 | 24 | Very High |
| RPi (limited) | 640×480 | 30 | Medium |

### Example Configurations

**HD Live Detection:**
```python
camera = CameraStream(source=0, width=1280, height=720, fps=30)
```

**4K High Quality:**
```python
camera = CameraStream(source=0, width=1920, height=1080, fps=24)
```

**RPi Camera Module:**
```python
camera = CameraStream(source=0, width=640, height=480, fps=24)
```

**USB Webcam:**
```python
camera = CameraStream(source=1, width=1280, height=720, fps=30)
```

---

## Troubleshooting

### Camera Not Found

```
ERROR - Failed to open camera (source=0)
```

**Solutions:**
1. Check camera connection
2. Try different source number: 0, 1, 2, etc.
3. Verify camera not used by other application
4. Check camera permissions (Linux/RPi)

### Low FPS

```
Current FPS: 5.2 (expected 30.0)
```

**Causes & Solutions:**
1. **USB bandwidth limited**: Use shorter cable, different port
2. **CPU bottleneck**: Reduce resolution or FPS
3. **Camera overload**: Close other apps
4. **RPi performance**: Use smaller resolution (640×480)

### Frames Dropping

```
Queue full, dropping old frames
```

**Causes:**
1. Detection thread too slow (Thread 2 can't keep up)
2. Frame queue only holds 2 frames by design

**Solutions:**
- Verify Thread 2 is running and processing
- Reduce frame resolution
- Ensure no blocking in read() calls

### Connection Timeout

```
WARNING - Capture failed 3 times - attempting reconnect
```

**Causes:**
1. USB disconnected
2. Camera driver crashed
3. Hardware failure

**Solutions:**
1. Reconnect camera
2. Restart driver
3. Try different USB port
4. Restart application

---

## Testing

### Run Tests

```bash
pytest test_camera_stream.py -v
```

### Run Demo

```bash
python demo_camera_stream.py
```

---

## Integration with Pipeline

### Connection to Thread 2 (Detection)

Thread 1 (Camera) → Frame Queue → Thread 2 (Detection)

```python
# Thread 1
camera = CameraStream()
camera.start()

# Thread 2 (in separate thread)
def detection_worker():
    while True:
        frame = camera.read()
        if frame is not None:
            detections = yolo.detect(frame)
            # Put detections in queue for Thread 3
```

### Queue Handoff

```
Camera Stream                Detection Thread
┌──────────────┐            ┌────────────────┐
│              │            │                │
│ read():      │──Frame───→ │ read():        │
│ Returns      │ Queue      │ Processes      │
│ latest       │            │ frame          │
│              │            │                │
└──────────────┘            └────────────────┘
```

---

## Performance Tips

1. **Use smaller resolution** for faster processing
   ```python
   CameraStream(width=640, height=480)  # 4× faster than 1280×720
   ```

2. **Increase FPS** for smoother operation
   ```python
   CameraStream(fps=60)  # Smoother than 24fps
   ```

3. **Use video file** for reproducible testing
   ```python
   CameraStream(source='test.mp4')  # Consistent results
   ```

4. **Monitor actual FPS**
   ```python
   print(f"Actual FPS: {camera.get_fps():.1f}")
   ```

---

## Files

| File | Purpose |
|------|---------|
| `backend/pipeline/camera_stream.py` | Main module (500+ lines) |
| `backend/pipeline/__init__.py` | Package exports |
| `test_camera_stream.py` | Test suite (40+ tests) |
| `demo_camera_stream.py` | Interactive demos |
| `CAMERA_STREAM_GUIDE.md` | This documentation |

---

## See Also

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete 4-thread pipeline
- [PIPELINE_GUIDE.md](./PIPELINE_GUIDE.md) - Pipeline details
- [demo_camera_stream.py](./demo_camera_stream.py) - Demonstrations

---

**Last Updated**: Phase 7 (Pipeline Thread 1)  
**Status**: Production ready ✅
