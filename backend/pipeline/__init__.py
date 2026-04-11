"""
Traffic Violation Detection Pipeline - 4-Thread Architecture

Thread 1: Camera Capture (camera_stream.py)
  - Captures frames from camera/video (30 FPS)
  - Non-blocking queue management
  - Platform detection (RPi picamera2 vs laptop cv2)
  - Output: capture_queue (maxsize=2)

Thread 2: Preprocessing (_preprocess_thread in main_pipeline.py)
  - CLAHE enhancement for low-light
  - Letterboxing for inference
  - Output: infer_queue (maxsize=2)
  
Thread 3: Inference (_inference_thread in main_pipeline.py)
  - YOLO26n detection (5-8ms, 125-200 FPS)
  - DeepSort tracking (2-4ms, 250-500 FPS)
  - Violation gate filtering (1-2ms)
  - Output: result_queue (maxsize=4)

Thread 4: Logging (_log_thread in main_pipeline.py)
  - PlateOCR extraction (250-350ms)
  - SRGAN upscaling if needed (200-400ms)
  - GPS coordinate reading (50-100ms)
  - Database saving + cloud upload
  - Output: cloud_queue (maxsize=10)

Main Thread: Display Loop
  - Live frame display with overlays
  - FPS counter, violation count
  - Queue depth visualization
  - Keyboard 'q' to quit

Module Entry Point: TrafficViolationPipeline
"""

from .camera_stream import CameraStream
from .main_pipeline import TrafficViolationPipeline

__all__ = [
    'CameraStream',
    'TrafficViolationPipeline',
]

__version__ = '2.0.0'
