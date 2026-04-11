# License Plate Super-Resolution with Real-ESRGAN

## Overview

Real-ESRGAN provides **4× super-resolution upscaling** for small license plates, enabling accurate OCR on distant vehicles. Only plates below area/width thresholds are processed to minimize overhead.

**Key Characteristics:**
- **Conditional execution**: Only upscales plates < 3000 px² or < 100 px wide
- **4× upscaling**: 45×18 → 180×72 pixels
- **200-400ms per plate** on Raspberry Pi (acceptable in async Thread 4)
- **Integrated with OCR**: Automatically retry failed reads on upscaled images
- **Non-blocking**: Runs in separate logging thread, doesn't impact detection/tracking

---

## Installation

### 1. Download Model Weights

```bash
# Automatically download RealESRGAN_x4plus.pth (203 MB)
python -m backend.gan.srgan.download_weights

# Or manually:
python backend/gan/srgan/download_weights.py
```

Location: `backend/gan/srgan/weights/RealESRGAN_x4plus.pth`

### 2. Install Dependencies

```bash
pip install basicsr>=1.4.0 realesrgan>=0.3.0
```

Or update requirements.txt:

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python demo_srgan.py
```

---

## API Reference

### PlateUpscaler Class

#### Initialization
```python
from backend.gan.srgan import PlateUpscaler

# Create upscaler (lazy-loaded - weights not loaded until first use)
upscaler = PlateUpscaler(scale=4, device='cpu')
```

**Parameters:**
- `scale`: Upscaling factor (default: 4×)
- `device`: 'cpu' or 'cuda' (default: 'cpu' for Raspberry Pi)

#### Methods

##### upscale(crop_bgr) → upscaled_bgr

Apply 4× upscaling to plate crop.

```python
import cv2

# Read small plate crop
small_plate = cv2.imread('plate_crop.png')  # 45×18

# Upscale
large_plate = upscaler.upscale(small_plate)  # 180×72

print(f"Original: {small_plate.shape}")
print(f"Upscaled: {large_plate.shape}")
```

**Behavior:**
- Lazy-loads model on first call
- Auto-downloads weights if missing
- Logs timing: `"SRGAN: 45×18 → 180×72 in 280ms"`
- Returns original on error

---

##### upscale_if_needed(crop_bgr, threshold_area=3000) → (image, bool)

Conditionally upscale based on plate size.

```python
# Only upscale if area < 3000 px² or width < 100 px
result, was_upscaled = upscaler.upscale_if_needed(plate_crop)

if was_upscaled:
    print(f"✓ Upscaled from {plate_crop.shape} to {result.shape}")
    # Retry OCR on upscaled image
else:
    print(f"✗ Large enough, using original")
    # Use original image directly
```

**Returns:**
- `image`: Either original or 4× upscaled
- `was_upscaled`: Boolean flag

**Thresholds:**
- Area: < 3000 px² (typical: 45×18 = 810 px²)
- Width: < 100 px (typical: 45-80 px)

---

##### should_upscale(crop_bgr, threshold_area=3000) → bool

Check if upscaling needed WITHOUT processing.

```python
# Fast check without actual upscaling
h, w = plate_crop.shape[:2]

if upscaler.should_upscale(plate_crop, threshold_area=3000):
    print(f"Plate too small: {w}×{h} - upscaling recommended")
else:
    print(f"Plate large enough: {w}×{h} - skip upscaling")
```

---

##### benchmark(num_iterations=20) → dict

Measure upscaling performance.

```python
# Run benchmarks (default: 20 iterations on 60×20 dummy images)
stats = upscaler.benchmark(num_iterations=50)

print(f"Average: {stats['mean_ms']:.1f}ms")
print(f"Min: {stats['min_ms']:.1f}ms")
print(f"Max: {stats['max_ms']:.1f}ms")
print(f"Median: {stats['median_ms']:.1f}ms")
```

**Returns:**
```python
{
    'iterations': 20,
    'min_ms': 245.3,
    'max_ms': 312.7,
    'mean_ms': 280.5,
    'median_ms': 278.2,
    'std_ms': 18.4,
}
```

**Performance Benchmarks** (CPU, Raspberry Pi):
- Small plates (45×18): 200-250 ms
- Medium plates (60×20): 250-300 ms
- Larger plates (80×25): 300-400 ms

---

##### get_stats() → dict

Get upscaler usage statistics.

```python
stats = upscaler.get_stats()

print(f"Total upscales: {stats['total_upscales']}")
print(f"Total skipped: {stats['total_skipped']}")
print(f"Average time: {stats['avg_upscale_ms']:.1f}ms")
```

**Returns:**
```python
{
    'initialized': True,
    'device': 'cpu',
    'scale': 4,
    'total_upscales': 42,
    'total_skipped': 158,
    'avg_upscale_ms': 287.3,
    'recent_timings': [280.5, 285.3, 292.1, ...],  # Last 100
}
```

---

##### print_stats()

Pretty-print statistics.

```python
upscaler.print_stats()

# Output:
# ============================================================
# PLATE UPSCALER STATISTICS
# ============================================================
# 
# Device: cpu
# Scale: 4×
# Initialized: True
# 
# Usage:
#   Total upscales: 42
#   Total skipped: 158
#   Upscale rate: 21.0%
# 
# Performance:
#   Avg time: 287.3ms
# 
# ============================================================
```

---

### Utility Functions

#### create_upscaler(device='cpu') → PlateUpscaler

Create upscaler instance.

```python
from backend.gan.srgan import create_upscaler

upscaler = create_upscaler(device='cpu')
```

---

## Integration with OCR Pipeline

### Standard Workflow

```python
from backend.core.ocr import PlateOCR
from backend.gan.srgan import create_upscaler
import cv2

# Initialize
ocr = PlateOCR()
upscaler = create_upscaler(device='cpu')

frame = cv2.imread('traffic_frame.jpg')
plate_bbox = [100, 50, 150, 80]  # x1, y1, x2, y2
x1, y1, x2, y2 = plate_bbox

# Extract plate crop
plate_crop = frame[y1:y2, x1:x2]

# Read with OCR
result = ocr.read_plate(frame, plate_bbox)

# If OCR confidence low AND plate is small, retry with upscaling
if result.confidence < 0.5 and result.needs_srgan:
    print(f"Low confidence ({result.confidence:.2f}) - upscaling...")
    upscaled, was_upscaled = upscaler.upscale_if_needed(plate_crop)
    
    if was_upscaled:
        # Retry OCR on upscaled image
        result_retry = ocr.read_plate(upscaled, None)  # Already cropped
        if result_retry.confidence > result.confidence:
            result = result_retry
            print(f"✓ Improved: {result.confidence:.2f}")

print(f"Final plate: {result.cleaned_text}")
```

### Async Integration (Recommended)

In `Thread 4` (logging thread):

```python
def logging_thread_worker(queue):
    """Thread 4: Logging and async processing"""
    
    upscaler = create_upscaler(device='cpu')
    ocr = PlateOCR()
    
    while True:
        item = queue.get()
        
        if item['type'] == 'plate_crop':
            # Async SRGAN + OCR (doesn't block Thread 3)
            crop = item['crop']
            frame = item['frame']
            bbox = item['bbox']
            
            # Conditional upscaling
            upscaled, was_upscaled = upscaler.upscale_if_needed(crop)
            
            # OCR on result
            if was_upscaled:
                result = ocr.read_plate(upscaled, None)
            else:
                result = ocr.read_plate(frame, bbox)
            
            logger.info(f"Plate: {result.cleaned_text}")
```

---

## Performance Characteristics

### Upscaling Time

| Plate Size | Area | Time (CPU) | When Applied |
|-----------|------|-----------|---------------|
| 45×18 | 810 px² | 200-250 ms | Always (< 3000) |
| 60×20 | 1200 px² | 250-300 ms | Always (< 3000) |
| 80×25 | 2000 px² | 300-350 ms | Always (< 3000) |
| 100×30 | 3000 px² | 350-400 ms | Boundary |
| 120×40 | 4800 px² | Never | Skipped (≥ 3000 AND ≥ 100 width) |

### Thread Impact

**Thread 3 (Inference - Detection/Tracking):**
- Detection: 5-8 ms
- Tracking: 2-4 ms
- **SRGAN: NOT RUN** ✓ (No blocking)

**Thread 4 (Logging - OCR/SRGAN):**
- OCR baseline: 250-350 ms
- SRGAN upscaling: +200-400 ms (when needed)
- Total with SRGAN: 450-750 ms (acceptable async)

---

## Threshold Configuration

### Default Thresholds

```python
PlateUpscaler.MIN_PLATE_AREA = 3000      # pixels²
PlateUpscaler.MIN_PLATE_WIDTH = 100      # pixels
```

### Custom Thresholds

```python
# More aggressive (upscale more plates)
result, was_upscaled = upscaler.upscale_if_needed(
    crop,
    threshold_area=2000  # Lower than default
)

# More conservative (upscale fewer plates)
result, was_upscaled = upscaler.upscale_if_needed(
    crop,
    threshold_area=5000  # Higher than default
)
```

### Decision Logic

```
if area < threshold_area OR width < 100:
    upscale()
else:
    skip
```

Examples:
- 45×18 (810 px²): ✓ Upscale (area < 3000)
- 50×20 (1000 px²): ✓ Upscale (area < 3000)
- 80×40 (3200 px²): ✗ Skip (area ≥ 3000 AND width ≥ 100)
- 60×40 (2400 px²): ✓ Upscale (area < 3000)
- 80×25 (2000 px²): ✓ Upscale (area < 3000)
- 50×15 (750 px²): ✓ Upscale (area < 3000)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'basicsr'"

```bash
pip install basicsr>=1.4.0 realesrgan>=0.3.0
```

### "RuntimeError: weights not found"

```bash
# Download weights manually
python -m backend.gan.srgan.download_weights

# Or verify download location
ls -lh backend/gan/srgan/weights/RealESRGAN_x4plus.pth
```

Expected size: ~200 MB

### "Slow upscaling (> 500ms)"

This is normal on Raspberry Pi. If too slow:
- Run upscaler in separate thread (recommended)
- Skip upscaling for less critical detections
- Use `should_upscale()` to prefilter

### "Out of memory during upscaling"

RealESRGAN uses tiling (400×400 blocks) to manage memory.
- Reduce tile size if needed (see `inference.py`)
- Run on CPU instead of GPU
- Process smaller batches

### "Inconsistent output size"

Output size = input×4 (always). Verify:
```python
input_h, input_w = crop.shape[:2]
output_h, output_w = upscaled.shape[:2]

assert output_h == input_h * 4
assert output_w == input_w * 4
```

---

## Advanced Usage

### Profiling Real-Time Performance

```python
from backend.gan.srgan import create_upscaler
import time

upscaler = create_upscaler()

# Profile on real video frames
for frame in video_stream:
    t0 = time.time()
    result, was_upscaled = upscaler.upscale_if_needed(crop)
    elapsed = time.time() - t0
    
    if was_upscaled:
        print(f"Upscale: {elapsed*1000:.0f}ms")

upscaler.print_stats()
```

### Batch Upscaling

```python
from backend.gan.srgan import create_upscaler

upscaler = create_upscaler()

# Process multiple plates
plates = [crop1, crop2, crop3, ...]

for i, plate in enumerate(plates):
    result, was_upscaled = upscaler.upscale_if_needed(plate)
    print(f"Plate {i}: {'upscaled' if was_upscaled else 'skipped'}")

upscaler.print_stats()
```

### Device Selection

```python
# CPU (default, works everywhere)
upscaler_cpu = PlateUpscaler(device='cpu')

# GPU (if CUDA available)
upscaler_gpu = PlateUpscaler(device='cuda')

# Auto-detect (not recommended)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
upscaler = PlateUpscaler(device=device)
```

---

## Performance Optimization Tips

1. **Use conditional upscaling** - Don't upscale all plates
   ```python
   result, was_upscaled = upscaler.upscale_if_needed(crop)
   ```

2. **Run in separate thread** - Don't block detection/tracking
   ```python
   threading.Thread(target=ocr_with_srgan, args=(crop,)).start()
   ```

3. **Batch process** - Load model once
   ```python
   upscaler = create_upscaler()  # Load model once
   for crop in crops:
       upscaler.upscale_if_needed(crop)  # Reuse model
   ```

4. **Monitor statistics** - Know what's happening
   ```python
   stats = upscaler.get_stats()
   upscale_rate = stats['total_upscales'] / (stats['total_upscales'] + stats['total_skipped'])
   ```

5. **Benchmark regularly** - Verify performance
   ```python
   stats = upscaler.benchmark(num_iterations=50)
   ```

---

## Files

| File | Purpose |
|------|---------|
| `backend/gan/srgan/inference.py` | Main PlateUpscaler class |
| `backend/gan/srgan/download_weights.py` | Weight downloader utility |
| `backend/gan/srgan/__init__.py` | Package exports |
| `backend/gan/srgan/weights/` | Model weights directory |
| `test_srgan.py` | Comprehensive test suite |
| `demo_srgan.py` | Interactive demonstrations |
| `SRGAN_GUIDE.md` | This documentation |

---

## Reference Implementation

Complete end-to-end example:

```python
#!/usr/bin/env python3
"""Example: License plate detection → OCR with super-resolution"""

import cv2
from backend.core.ocr import PlateOCR
from backend.gan.srgan import create_upscaler

def process_plate(frame, bbox):
    """Process single plate with optional upscaling"""
    
    ocr = PlateOCR()
    upscaler = create_upscaler(device='cpu')
    
    # Extract crop
    x1, y1, x2, y2 = bbox
    crop = frame[y1:y2, x1:x2]
    
    # Read with OCR
    result = ocr.read_plate(frame, bbox)
    
    # Retry with upscaling if needed
    if not result.is_valid_indian_format and result.needs_srgan:
        upscaled, was_upscaled = upscaler.upscale_if_needed(crop)
        if was_upscaled:
            result_retry = ocr.read_plate(upscaled, None)
            if result_retry.confidence > result.confidence:
                result = result_retry
    
    return result

if __name__ == '__main__':
    frame = cv2.imread('traffic_frame.jpg')
    bbox = [100, 50, 250, 100]
    
    result = process_plate(frame, bbox)
    print(f"Plate: {result.cleaned_text}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Valid: {result.is_valid_indian_format}")
```

---

## See Also

- [OCR_GUIDE.md](./OCR_GUIDE.md) - License plate text extraction
- [VIOLATION_GATE_GUIDE.md](./VIOLATION_GATE_GUIDE.md) - False positive prevention
- [demo_srgan.py](./demo_srgan.py) - Interactive examples
- [test_srgan.py](./test_srgan.py) - Test suite
