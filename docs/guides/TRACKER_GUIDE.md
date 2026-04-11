# Vehicle Tracker Guide

Comprehensive guide to the `VehicleTracker` system for multi-object tracking with motion analysis.

## Overview

The `VehicleTracker` wraps the **DeepSort** algorithm for:
- ✅ **Multi-object tracking** - Maintain consistent IDs across frames
- ✅ **Motion analysis** - Speed, direction, velocity estimation
- ✅ **Position prediction** - Forecast future vehicle locations
- ✅ **Temporal consistency** - Handle occlusions and re-identification

## Installation

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Manually install deep-sort
pip install deep-sort-realtime>=1.3.2
```

## Quick Start

### Basic Usage

```python
from backend import Detector, VehicleTracker

# Initialize detector and tracker
detector = Detector("yolov8n.onnx", device="cuda")
tracker = VehicleTracker(max_age=30, n_init=3)

# In your detection loop
for frame in video_frames:
    # Detect objects
    detections = detector.infer(frame)
    
    # Track objects
    tracked_objects = tracker.update(detections, frame)
    
    # Process tracks
    for track in tracked_objects:
        print(f"ID: {track.track_id}, Confidence: {track.confidence:.2f}")
```

### Advanced Usage with Motion Analysis

```python
# Track and analyze motion
tracker = VehicleTracker(max_age=30, n_init=3)

for frame in video_frames:
    detections = detector.infer(frame)
    tracked = tracker.update(detections, frame)
    
    for track in tracked:
        track_id = track.track_id
        
        # Get historical positions
        history = tracker.get_track_history(track_id, last_n_frames=30)
        
        # Estimate speed (km/h)
        speed_kmh = tracker.estimate_speed(
            track_id,
            fps=30,
            pixels_per_meter=50  # Calibrate based on camera
        )
        
        # Get motion direction (0-360°)
        angle = tracker.calculate_motion_angle(track_id)
        
        # Get direction vector (normalized dx, dy)
        direction = tracker.get_direction_vector(track_id)
        
        # Check if moving
        is_moving = tracker.is_moving(track_id, min_velocity=1.0)
        
        # Predict position (N frames ahead)
        future_pos = tracker.predict_position(track_id, frames_ahead=5)
```

## Core Classes & Functions

### VehicleTracker

Main tracking class wrapping DeepSort.

#### Initialization

```python
tracker = VehicleTracker(
    max_age=30,           # Frames to keep unmatched track
    n_init=3,             # Frames needed for confirmation
    embedder="osnet_x0_25_msmt17",  # DeepSort embedding model
    half=False            # Use FP16 (faster, less memory)
)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `update(detections, frame)` | `List[TrackedObject]` | Update tracker with new detections |
| `get_track_history(track_id, last_n_frames=30)` | `List[Tuple[int, int]]` | Get centroid history |
| `estimate_speed(track_id, fps, pixels_per_meter)` | `float` | Speed in km/h |
| `get_direction_vector(track_id)` | `Tuple[float, float]` | Normalized (dx, dy) |
| `get_track_velocity(track_id)` | `Tuple[float, float]` | Velocity in pixels/frame |
| `calculate_motion_angle(track_id)` | `float` | Angle in degrees (0-360°) |
| `is_moving(track_id, min_velocity)` | `bool` | Check if object moving |
| `predict_position(track_id, frames_ahead)` | `Tuple[int, int]` | Future position estimate |
| `reset()` | - | Clear all tracks |
| `print_stats()` | - | Print tracking statistics |
| `get_stats()` | `dict` | Get statistics dictionary |

### TrackedObject

Named tuple containing track data and metadata.

```python
TrackedObject(
    track_id: int,           # Unique track identifier
    class_id: int,          # Detection class
    class_name: str,        # Class name
    confidence: float,      # Detection confidence (0-1)
    x1, y1, x2, y2: int,   # Bounding box (pixels)
    center_x, center_y: int,  # Box center (pixels)
    is_confirmed: bool,      # Track confirmed (age >= n_init)
    age: int                # Frames since track creation
)
```

### Utility Functions

```python
from backend import compute_centroid, compute_iou, print_tracked_objects

# Compute bounding box center
cx, cy = compute_centroid(x1, y1, x2, y2)

# Compute intersection over union
iou = compute_iou((x1, y1, x2, y2), (x1', y1', x2', y2'))

# Pretty print tracked objects
print_tracked_objects(tracked_objects)
```

## Configuration Guide

### Tracker Parameters

#### max_age (default: 30)
- **Meaning**: How many frames to keep a track without detection
- **Range**: 10-100
- **Lower**: Drops tracks quickly (less memory, more ID switches)
- **Higher**: Keeps tracks longer (smoother tracking, more ghost tracks)
- **Use case**: 30 for 30 FPS video = 1 second memory

#### n_init (default: 3)
- **Meaning**: Frames needed before track is "confirmed"
- **Range**: 1-10
- **Lower**: Fast confirmation, more false positives
- **Higher**: Requires more evidence, slower confirmation
- **Use case**: 3 for 30 FPS video = 0.1 second minimum

### Motion Analysis Parameters

#### pixels_per_meter (default: 50)
- **Meaning**: Camera calibration for speed estimation
- **How to calibrate**:
  1. Mark known distance in frame (e.g., 2 meters)
  2. Count pixels in that distance
  3. `pixels_per_meter = pixels_distance / 2`
- **Common values**:
  - Drone camera: 30-50 ppm
  - Traffic camera: 50-150 ppm
  - Highway camera: 20-40 ppm

#### min_velocity (default: 1.0)
- **Meaning**: Minimum velocity threshold (pixels/frame)
- **Use**: In `is_moving()` to filter stationary objects
- **Example**: At 640×480, min_velocity=1.0 = ~0.3 km/h

### Embedder Models

DeepSort uses appearance embeddings for re-identification. Available models:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `osnet_x0_25_msmt17` | Tiny | Fastest | Good |
| `osnet_x0_5_msmt17` | Small | Fast | Better |
| `osnet_x1_0_msmt17` | Medium | Medium | Best |
| `osnet_x1_0_ibn_msmt17` | Large | Slow | Best+ |

## Visualization

### Drawing Tracking Results

```python
import cv2

# Draw bounding boxes and track IDs
for track in tracked:
    # Box
    cv2.rectangle(frame, (track.x1, track.y1), (track.x2, track.y2), (0, 255, 0), 2)
    
    # Track ID
    cv2.putText(frame, f"ID:{track.track_id}", (track.x1, track.y1 - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Centroid
    cv2.circle(frame, (track.center_x, track.center_y), 3, (0, 255, 255), -1)
    
    # Confirmation status
    status = "✓" if track.is_confirmed else "?"
    cv2.putText(frame, status, (track.x1 + 5, track.y2 - 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
```

### Drawing Trajectories

```python
def draw_trajectory(frame, tracker, track_id, color=(0, 255, 0), thickness=2):
    """Draw trajectory of a track"""
    history = tracker.get_track_history(track_id)
    
    if len(history) > 1:
        for i in range(len(history) - 1):
            pt1 = history[i]
            pt2 = history[i + 1]
            cv2.line(frame, pt1, pt2, color, thickness)
    
    return frame

# Usage
for track in tracked:
    frame = draw_trajectory(frame, tracker, track.track_id)
```

## Performance Tuning

### Speed Optimization

```python
# Use smaller embedder for speed
tracker = VehicleTracker(embedder="osnet_x0_25_msmt17")

# Use FP16 for GPU acceleration
tracker = VehicleTracker(half=True)

# Reduce history size in motion analysis
history = tracker.get_track_history(track_id, last_n_frames=10)
```

### Memory Optimization

```python
# Reduce max_age to drop old tracks faster
tracker = VehicleTracker(max_age=15)

# Reset tracker periodically for long videos
if frame_count % 1000 == 0:
    tracker.reset()
```

## Troubleshooting

### Issue: IDs switching constantly
- **Cause**: Objects look similar, DeepSort confused
- **Solution**: 
  - Increase `n_init` to require more confirmation
  - Improve detection quality
  - Reduce `max_age` to prevent false re-associations

### Issue: Tracks disappear and reappear
- **Cause**: `max_age` too low, or detection misses
- **Solution**:
  - Increase `max_age`
  - Improve detection robustness
  - Reduce confidence threshold

### Issue: Motion analysis inaccurate
- **Cause**: Calibration error or shaking camera
- **Solution**:
  - Recalibrate `pixels_per_meter`
  - Use longer history window (increase last_n_frames)
  - Add camera stabilization

### Issue: Memory usage growing
- **Cause**: Tracks not being cleaned up
- **Solution**:
  - Reduce `max_age`
  - Call `tracker.reset()` periodically
  - Use FP16 mode

## Advanced Examples

### Example 1: Speed Limit Violation Detection

```python
def check_speed_violation(tracker, track_id, speed_limit_kmh=50):
    """Check if vehicle exceeds speed limit"""
    speed = tracker.estimate_speed(track_id, fps=30, pixels_per_meter=50)
    
    if speed is not None and speed > speed_limit_kmh:
        return True, speed
    return False, speed

# Usage
for track in tracked:
    violation, speed = check_speed_violation(tracker, track.track_id, speed_limit_kmh=50)
    
    if violation:
        print(f"Speed violation: ID {track.track_id} at {speed:.1f} km/h")
```

### Example 2: Lane Detection & Wrong Way

```python
def check_wrong_way(tracker, track_id, allowed_direction_min=350, allowed_direction_max=10):
    """Check if vehicle going wrong way"""
    angle = tracker.calculate_motion_angle(track_id)
    
    # Check if angle in allowed range (e.g., 350-360° and 0-10° = right direction)
    if allowed_direction_max < allowed_direction_min:  # Wraps around 0°
        in_range = angle >= allowed_direction_min or angle <= allowed_direction_max
    else:
        in_range = allowed_direction_min <= angle <= allowed_direction_max
    
    return not in_range, angle

# Usage
for track in tracked:
    violation, angle = check_wrong_way(tracker, track.track_id)
    
    if violation:
        print(f"Wrong way: ID {track.track_id} at {angle:.1f}°")
```

### Example 3: Collision Prediction

```python
def predict_collision(tracker, track_id1, track_id2, time_to_impact=2.0, fps=30):
    """Predict if two tracks will collide"""
    
    # Get future positions
    future_frames = int(time_to_impact * fps)
    pos1 = tracker.predict_position(track_id1, frames_ahead=future_frames)
    pos2 = tracker.predict_position(track_id2, frames_ahead=future_frames)
    
    if pos1 is None or pos2 is None:
        return False, None
    
    # Check distance
    distance = ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
    collision_distance = 100  # pixels
    
    return distance < collision_distance, distance

# Usage
tracks_list = [t.track_id for t in tracked]
for i in range(len(tracks_list)):
    for j in range(i + 1, len(tracks_list)):
        collision, dist = predict_collision(tracker, tracks_list[i], tracks_list[j])
        if collision:
            print(f"Collision alert: ID {tracks_list[i]} <-> ID {tracks_list[j]}, distance: {dist:.0f}px")
```

## Testing

Run the comprehensive test suite:

```bash
# Test individual tracker functions
python test_tracker.py

# Test integrated detector + tracker
python test_integrated.py --camera 0

# Benchmark performance
python test_integrated.py --benchmark 100

# Limit frames for testing
python test_integrated.py --max-frames 300
```

## Performance Benchmarks

Typical performance on RTX A4000:

| Operation | Time | FPS |
|-----------|------|-----|
| Detection (YOLO26n) | 5-8ms | 125-200 |
| Tracking (DeepSort) | 2-4ms | 250-500 |
| Total (640×640) | 8-12ms | 80-125 |

Memory usage: ~2-3 GB GPU, < 500 MB CPU

## References

- **DeepSort Paper**: https://arxiv.org/abs/1703.07402
- **OSNet**: https://arxiv.org/abs/1905.00953
- **Deep-Sort-Realtime**: https://github.com/mikel-brostrom/yolov8_tracking

## Next Steps

- Implement database storage for violations
- Add REST API server for remote access
- Deploy on Raspberry Pi with optimized settings
- Integrate with alert system (email/SMS)
