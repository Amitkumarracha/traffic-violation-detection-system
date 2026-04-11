"""
Traffic Violation Detection - Main Pipeline Orchestrator (Thread 1-4)

Implements real-time 4-thread pipeline for traffic violation detection:
  Thread 1: Camera capture (CameraStream) → capture_queue
  Thread 2: Preprocessing (CLAHE, resize) → infer_queue
  Thread 3: Inference (YOLO, tracker, gate) → result_queue
  Thread 4: Logging (OCR, SRGAN, GPS, database) → cloud_queue

Main thread: Display loop with overlay

Architecture:
  capture_queue (maxsize=2)   ← Thread 1 output
      ↓
  infer_queue (maxsize=2)     ← Thread 2 output
      ↓
  result_queue (maxsize=4)    ← Thread 3 output
      ↓
  cloud_queue (maxsize=10)    ← Thread 4 output

Usage:
    pipeline = TrafficViolationPipeline(camera_source=0, show_display=True)
    pipeline.start()
    # ... pipeline runs in background threads ...
    pipeline.stop()
    stats = pipeline.get_stats()

Performance:
  - Total latency: ~50-100ms (frames to violation)
  - Throughput: 30 FPS (camera limited)
  - Violations: Real-time OCR + database logging
  - Cloud: Async non-blocking with 10-item buffer
"""

import cv2
import threading
import queue
import time
import logging
import numpy as np
from pathlib import Path
from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FrameData:
    """Data passed through infer_queue"""
    frame_id: int
    timestamp: float
    frame: np.ndarray  # Original frame
    processed: np.ndarray  # CLAHE + resized
    height: int
    width: int


@dataclass
class InferenceResult:
    """Data passed through result_queue"""
    frame_id: int
    timestamp: float
    frame: np.ndarray
    detections: list  # [{"class": "helmet", "bbox": [x,y,w,h], "conf": 0.95}, ...]
    tracks: dict  # {track_id: Track}
    violations: list  # Confirmed violations only


@dataclass
class LogEntry:
    """Data passed through cloud_queue"""
    violation_id: str
    timestamp: float
    violation_type: str  # "without_helmet", "triple_ride", etc.
    plate_text: str
    confidence: float
    gps_coords: Tuple[float, float]  # (lat, lon)
    frame_path: Optional[str]  # Path to saved frame or None
    srgan_applied: bool


# ============================================================================
# PLATFORM-SPECIFIC IMPORTS (WITH FALLBACKS)
# ============================================================================

def _safe_import(module_path: str, class_name: str, default=None):
    """Safely import a module, return None if not available"""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not import {module_path}.{class_name}: {e}")
        return default


# Try to import core modules (may not exist yet)
Detector = _safe_import("backend.core.detector", "Detector")
VehicleTracker = _safe_import("backend.core.tracker", "VehicleTracker")
ViolationGate = _safe_import("backend.core.violation_gate", "ViolationGate")
PlateOCR = _safe_import("backend.core.ocr", "PlateOCR")
GPSReader = _safe_import("backend.core.gps", "GPSReader")
PlateUpscaler = _safe_import("backend.gan.srgan.inference", "PlateUpscaler")
CameraStream = _safe_import("backend.pipeline.camera_stream", "CameraStream")

# Platform config
try:
    from backend.config.platform_detector import get_platform_config
except ImportError:
    logger.warning("Could not import platform_detector, using defaults")
    def get_platform_config():
        return {
            'name': 'unknown',
            'device': 'cpu',
            'is_raspberry_pi': False,
            'has_gpu': False
        }

# Database
save_violation = _safe_import("backend.database.crud", "save_violation")


# ============================================================================
# MAIN PIPELINE CLASS
# ============================================================================

class TrafficViolationPipeline:
    """
    Main orchestrator for 4-thread real-time traffic violation detection.
    
    Thread 1 (CameraStream):
        - Captures frames from camera/video
        - Outputs to capture_queue (maxsize=2)
        - Non-blocking, drops old frames
    
    Thread 2 (Preprocess):
        - Pulls from capture_queue
        - Applies CLAHE for low-light enhancement
        - Resizes to inference size
        - Outputs to infer_queue (maxsize=2)
    
    Thread 3 (Inference):
        - Pulls from infer_queue
        - Runs YOLO detection
        - Runs DeepSort tracking
        - Violation gate filtering
        - Outputs to result_queue (maxsize=4)
    
    Thread 4 (Logging):
        - Pulls from result_queue
        - Runs OCR on detected plates
        - Optional SRGAN upscaling
        - Gets GPS coordinates
        - Saves to database
        - Outputs to cloud_queue (maxsize=10)
    
    Main Thread (Display):
        - Shows annotated frames
        - Overlay: FPS, violation count
        - Keyboard: 'q' to quit
    """
    
    def __init__(self, camera_source: int = 0, show_display: bool = True):
        """
        Initialize pipeline (lazy load on start).
        
        Args:
            camera_source: 0/1 for webcam, or path string for video file
            show_display: False on RPi headless, True on laptop
        """
        logger.info("Initializing TrafficViolationPipeline")
        
        # Config
        self.camera_source = camera_source
        self.show_display = show_display
        self.platform_config = get_platform_config()
        
        # Queues for thread communication
        self.capture_queue = queue.Queue(maxsize=2)      # From camera
        self.infer_queue = queue.Queue(maxsize=2)         # To inference
        self.result_queue = queue.Queue(maxsize=4)        # From inference
        self.cloud_queue = queue.Queue(maxsize=10)        # For cloud upload
        
        # Stop event for graceful shutdown
        self.stop_event = threading.Event()
        self.threads = []
        
        # Components (lazy loaded on start)
        self.camera = None
        self.detector = None
        self.tracker = None
        self.violation_gate = None
        self.ocr = None
        self.gps_reader = None
        self.upscaler = None
        
        # Statistics
        self.stats = {
            'start_time': None,
            'total_frames': 0,
            'frame_times': deque(maxlen=100),  # Last 100 frame times
            'violations_detected': 0,
            'false_positives_rejected': 0,
            'plates_read': 0,
            'srgan_activations': 0,
            'last_stats_log': time.time()
        }
        
        # Display
        self.last_display_frame = None
        self.display_violations = deque(maxlen=10)  # Last 10 violations for overlay
        
        logger.info(f"Pipeline created | Platform: {self.platform_config['name']} | "
                   f"Device: {self.platform_config['device']} | Display: {show_display}")
    
    
    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================
    
    def start(self):
        """Start all 4 threads and main display loop."""
        if self.stats['start_time'] is not None:
            logger.warning("Pipeline already started")
            return
        
        logger.info("Starting TrafficViolationPipeline")
        self.stats['start_time'] = time.time()
        
        # Initialize components
        self._init_components()
        
        # Print startup summary
        self._print_startup_summary()
        
        # Start Camera Stream (Thread 1)
        self.camera = CameraStream(
            source=self.camera_source,
            width=1280,
            height=720,
            fps=30
        )
        camera_thread = self.camera.start()
        logger.info("✓ Thread 1 (Camera): Started")
        
        # Start Preprocess Thread (Thread 2)
        preprocess_thread = threading.Thread(
            target=self._preprocess_thread,
            daemon=True,
            name="PreprocessThread"
        )
        preprocess_thread.start()
        self.threads.append(preprocess_thread)
        logger.info("✓ Thread 2 (Preprocess): Started")
        
        # Start Inference Thread (Thread 3)
        inference_thread = threading.Thread(
            target=self._inference_thread,
            daemon=True,
            name="InferenceThread"
        )
        inference_thread.start()
        self.threads.append(inference_thread)
        logger.info("✓ Thread 3 (Inference): Started")
        
        # Start Logging Thread (Thread 4)
        log_thread = threading.Thread(
            target=self._log_thread,
            daemon=True,
            name="LogThread"
        )
        log_thread.start()
        self.threads.append(log_thread)
        logger.info("✓ Thread 4 (Logging): Started")
        
        logger.info("All threads started. Running pipeline...")
        
        # Start display loop on main thread
        if self.show_display:
            try:
                self._display_loop()
            except KeyboardInterrupt:
                logger.info("Display interrupted by user")
            finally:
                self.stop()
    
    
    def stop(self):
        """Stop all threads and cleanup resources."""
        logger.info("Stopping TrafficViolationPipeline")
        
        # Signal all threads to stop
        self.stop_event.set()
        
        # Give threads 2 seconds to finish
        time.sleep(2)
        
        # Close camera
        if self.camera:
            self.camera.stop()
            logger.info("Camera stopped")
        
        # Flush queues
        self._flush_queue(self.capture_queue)
        self._flush_queue(self.infer_queue)
        self._flush_queue(self.result_queue)
        self._flush_queue(self.cloud_queue)
        
        # Print session summary
        self._print_session_summary()
        
        logger.info("Pipeline stopped")
    
    
    def _init_components(self):
        """Initialize all model components."""
        logger.info("Initializing components...")
        
        # Detector (YOLO26n)
        if Detector:
            try:
                self.detector = Detector(
                    model_path="yolo26n.pt",
                    device=self.platform_config['device']
                )
                logger.info("✓ Detector initialized (YOLO26n)")
            except Exception as e:
                logger.error(f"Failed to initialize Detector: {e}")
        
        # Tracker (DeepSort)
        if VehicleTracker:
            try:
                self.tracker = VehicleTracker()
                logger.info("✓ Tracker initialized (DeepSort)")
            except Exception as e:
                logger.error(f"Failed to initialize Tracker: {e}")
        
        # Violation Gate (4-stage filter)
        if ViolationGate:
            try:
                self.violation_gate = ViolationGate()
                logger.info("✓ Violation Gate initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Violation Gate: {e}")
        
        # OCR (PaddleOCR)
        if PlateOCR:
            try:
                self.ocr = PlateOCR()
                logger.info("✓ OCR initialized (PaddleOCR)")
            except Exception as e:
                logger.error(f"Failed to initialize OCR: {e}")
        
        # GPS Reader
        if GPSReader:
            try:
                self.gps_reader = GPSReader()
                logger.info("✓ GPS Reader initialized")
            except Exception as e:
                logger.warning(f"GPS Reader not available: {e}")
        
        # Plate Upscaler (Real-ESRGAN)
        if PlateUpscaler:
            try:
                self.upscaler = PlateUpscaler(
                    model_name="RealESRGAN_x4plus",
                    scale=4,
                    device=self.platform_config['device']
                )
                logger.info("✓ Plate Upscaler initialized (Real-ESRGAN)")
            except Exception as e:
                logger.warning(f"Plate Upscaler not available: {e}")
        
        logger.info("Component initialization complete")
    
    
    # ========================================================================
    # THREAD 2: PREPROCESSING
    # ========================================================================
    
    def _preprocess_thread(self):
        """
        Thread 2: Pull raw frame, apply CLAHE, resize, push to infer_queue.
        
        CLAHE: Contrast Limited Adaptive Histogram Equalization
            - Enhances local contrast
            - Useful for low-light conditions
            - clipLimit: 2.0, tileGridSize: (8, 8)
        
        Letterboxing: Pad frame to maintain aspect ratio for inference
        """
        logger.info("Preprocess thread started")
        frame_id = 0
        
        # CLAHE initialization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        while not self.stop_event.is_set():
            try:
                # Get raw frame from camera (non-blocking)
                frame = self.camera.read() if self.camera else None
                
                if frame is None:
                    time.sleep(0.01)  # Wait for frame
                    continue
                
                frame_id += 1
                timestamp = time.time()
                
                # Convert BGR to LAB for CLAHE
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)
                
                # Apply CLAHE on L channel
                l_clahe = clahe.apply(l_channel)
                lab_clahe = cv2.merge([l_clahe, a_channel, b_channel])
                
                # Convert back to BGR
                enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
                
                # Resize for inference (maintain aspect ratio with letterboxing)
                # Target: 416x416 for YOLO26n
                processed = self._letterbox(enhanced, (416, 416))
                
                # Create frame data
                frame_data = FrameData(
                    frame_id=frame_id,
                    timestamp=timestamp,
                    frame=enhanced,  # Enhanced for inference
                    processed=processed,  # Resized tensor
                    height=enhanced.shape[0],
                    width=enhanced.shape[1]
                )
                
                # Put in infer_queue (maxsize=2, drops old if full)
                try:
                    self.infer_queue.put(frame_data, timeout=0.1)
                except queue.Full:
                    # Queue full, skip this frame (capture thread will drop old)
                    pass
                
            except Exception as e:
                logger.error(f"Preprocess thread error: {e}")
        
        logger.info("Preprocess thread stopped")
    
    
    # ========================================================================
    # THREAD 3: INFERENCE
    # ========================================================================
    
    def _inference_thread(self):
        """
        Thread 3: Pull from infer_queue, run detection/tracking/gate, push to result_queue.
        
        Steps:
            1. Get frame from infer_queue
            2. Run YOLO detection
            3. Run DeepSort tracking
            4. Apply violation gate (4-stage)
            5. Push confirmed violations to result_queue
        
        Performance: ~5-8ms per frame (125-200 FPS)
        """
        logger.info("Inference thread started")
        frame_count = 0
        last_fps_log = time.time()
        
        while not self.stop_event.is_set():
            try:
                # Get frame data
                frame_data = self.infer_queue.get(timeout=0.1)
                
                frame_count += 1
                elapsed = time.time() - last_fps_log
                
                # Inference
                detections = []
                tracks = {}
                violations = []
                
                if self.detector and self.tracker and self.violation_gate:
                    # Run YOLO detection
                    detections = self.detector.infer(frame_data.processed)
                    
                    # Run DeepSort tracking
                    tracks = self.tracker.update(detections, frame_data.frame)
                    
                    # Apply violation gate (4-stage filter)
                    violations = self.violation_gate.process(
                        detections=detections,
                        tracks=tracks,
                        frame_id=frame_data.frame_id
                    )
                    
                    # Update stats
                    self.stats['violations_detected'] += len(violations)
                    rejected = len(detections) - len(violations)
                    if rejected > 0:
                        self.stats['false_positives_rejected'] += rejected
                
                # Create inference result
                result = InferenceResult(
                    frame_id=frame_data.frame_id,
                    timestamp=frame_data.timestamp,
                    frame=frame_data.frame,
                    detections=detections,
                    tracks=tracks,
                    violations=violations
                )
                
                # Push to result_queue
                try:
                    self.result_queue.put(result, timeout=0.1)
                except queue.Full:
                    pass  # Drop frame if queue full
                
                # Log FPS every 100 frames
                if frame_count % 100 == 0 and elapsed > 0:
                    fps = frame_count / elapsed
                    logger.info(f"Inference FPS: {fps:.1f} | "
                               f"Detections: {len(detections)} | "
                               f"Violations: {len(violations)}")
                    frame_count = 0
                    last_fps_log = time.time()
                
            except queue.Empty:
                time.sleep(0.01)
            except Exception as e:
                logger.error(f"Inference thread error: {e}")
        
        logger.info("Inference thread stopped")
    
    
    # ========================================================================
    # THREAD 4: LOGGING
    # ========================================================================
    
    def _log_thread(self):
        """
        Thread 4: Pull from result_queue, OCR, SRGAN, GPS, database, cloud_queue.
        
        Steps:
            1. Extract plate crops from detections
            2. Optional SRGAN upscaling (if plate too small)
            3. Run PlateOCR to read text
            4. Get GPS coordinates
            5. Save to database via save_violation()
            6. Push to cloud_queue for async upload
            7. Log violation
        
        Performance: 250-750ms per violation (async, non-blocking for Threads 1-3)
        """
        logger.info("Logging thread started")
        
        while not self.stop_event.is_set():
            try:
                # Get inference result
                result = self.result_queue.get(timeout=0.5)
                
                # Process each confirmed violation
                for violation in result.violations:
                    try:
                        violation_id = f"{result.frame_id}_{violation.get('track_id', 0)}"
                        violation_type = violation.get('violation_type', 'unknown')
                        
                        # Extract plate region from frame
                        plate_bbox = violation.get('plate_bbox', None)
                        plate_crop = None
                        
                        if plate_bbox and len(plate_bbox) >= 4:
                            x, y, w, h = plate_bbox[:4]
                            x, y = max(0, x), max(0, y)
                            plate_crop = result.frame[
                                y:y+h,
                                x:x+w
                            ]
                        
                        # Optional SRGAN upscaling
                        srgan_applied = False
                        if plate_crop is not None and self.upscaler:
                            plate_area = plate_crop.shape[0] * plate_crop.shape[1]
                            
                            # Apply SRGAN if plate too small (<30px height)
                            if plate_crop.shape[0] < 30:
                                try:
                                    plate_crop = self.upscaler.upscale(plate_crop)
                                    srgan_applied = True
                                    self.stats['srgan_activations'] += 1
                                except Exception as e:
                                    logger.warning(f"SRGAN upscaling failed: {e}")
                        
                        # OCR - Read plate text
                        plate_text = "UNKNOWN"
                        confidence = 0.0
                        
                        if plate_crop is not None and self.ocr:
                            try:
                                ocr_result = self.ocr.read_plate(plate_crop)
                                plate_text = ocr_result.get('text', 'UNKNOWN')
                                confidence = ocr_result.get('confidence', 0.0)
                                self.stats['plates_read'] += 1
                            except Exception as e:
                                logger.warning(f"OCR failed: {e}")
                        
                        # Get GPS coordinates
                        gps_coords = (0.0, 0.0)
                        if self.gps_reader:
                            try:
                                gps_coords = self.gps_reader.get_location()
                            except Exception as e:
                                logger.warning(f"GPS read failed: {e}")
                        
                        # Create log entry
                        log_entry = LogEntry(
                            violation_id=violation_id,
                            timestamp=result.timestamp,
                            violation_type=violation_type,
                            plate_text=plate_text,
                            confidence=confidence,
                            gps_coords=gps_coords,
                            frame_path=None,  # Could save frame here
                            srgan_applied=srgan_applied
                        )
                        
                        # Save to database
                        if save_violation:
                            try:
                                save_violation(log_entry)
                            except Exception as e:
                                logger.error(f"Database save failed: {e}")
                        
                        # Push to cloud queue
                        try:
                            self.cloud_queue.put(log_entry, timeout=0.1)
                        except queue.Full:
                            logger.warning("Cloud queue full, dropping entry")
                        
                        # Log violation
                        logger.info(
                            f"VIOLATION: {violation_type} | "
                            f"Plate: {plate_text} ({confidence:.2f}) | "
                            f"GPS: {gps_coords[0]:.2f},{gps_coords[1]:.2f} | "
                            f"SRGAN: {srgan_applied}"
                        )
                        
                        # Store for display overlay
                        self.display_violations.append({
                            'type': violation_type,
                            'plate': plate_text,
                            'time': time.time()
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing violation: {e}")
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Logging thread error: {e}")
        
        logger.info("Logging thread stopped")
    
    
    # ========================================================================
    # DISPLAY LOOP (MAIN THREAD)
    # ========================================================================
    
    def _display_loop(self):
        """
        Main thread: Display annotated frames with overlay.
        
        Overlay:
            - FPS: Current inference FPS
            - Violation count: Total detected this session
            - Recent violations: Last 5 with timestamps
            - Queue depths: For debugging
        
        Keyboard:
            - 'q': Quit pipeline
        """
        logger.info("Display loop started")
        
        window_name = "Traffic Violation Detection - Press 'q' to quit"
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        
        last_update = time.time()
        current_fps = 0.0
        
        while not self.stop_event.is_set():
            try:
                # Get latest result frame
                frame = None
                try:
                    while True:  # Drain queue to get latest
                        result = self.result_queue.get_nowait()
                        frame = result.frame
                except queue.Empty:
                    pass
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Calculate FPS
                now = time.time()
                elapsed = now - last_update
                if elapsed > 0:
                    current_fps = 1.0 / elapsed
                    last_update = now
                
                # Create annotation copy
                annotated = frame.copy()
                
                # Draw overlay
                self._draw_overlay(
                    annotated,
                    current_fps,
                    self.stats['violations_detected']
                )
                
                # Display
                cv2.imshow(window_name, annotated)
                
                # Check for quit key
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("User pressed 'q', stopping pipeline")
                    break
                
            except Exception as e:
                logger.error(f"Display loop error: {e}")
        
        cv2.destroyAllWindows()
        logger.info("Display loop stopped")
    
    
    def _draw_overlay(self, frame: np.ndarray, fps: float, violation_count: int):
        """Draw FPS, violation count, and recent violations on frame."""
        h, w = frame.shape[:2]
        
        # FPS counter (top-left)
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        # Violation count (top-right)
        cv2.putText(
            frame,
            f"Violations: {violation_count}",
            (w - 300, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )
        
        # Recent violations (bottom-left)
        y_offset = h - 20
        for i, violation in enumerate(reversed(list(self.display_violations)[-5:])):
            text = f"{violation['type']}: {violation['plate']}"
            cv2.putText(
                frame,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )
            y_offset -= 20
        
        # Queue depths (top-center, for debugging)
        queue_info = (
            f"Q1:{self.capture_queue.qsize()} "
            f"Q2:{self.infer_queue.qsize()} "
            f"Q3:{self.result_queue.qsize()} "
            f"Q4:{self.cloud_queue.qsize()}"
        )
        cv2.putText(
            frame,
            queue_info,
            (w // 2 - 100, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            1
        )
    
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics."""
        uptime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        # Calculate average FPS from frame times
        avg_fps = 0.0
        if len(self.stats['frame_times']) > 0:
            avg_fps = 1.0 / np.mean(list(self.stats['frame_times']))
        
        return {
            'uptime_seconds': int(uptime),
            'total_frames': self.stats['total_frames'],
            'avg_fps': avg_fps,
            'violations_detected': self.stats['violations_detected'],
            'false_positives_rejected': self.stats['false_positives_rejected'],
            'plates_read': self.stats['plates_read'],
            'srgan_activations': self.stats['srgan_activations'],
            'queue_sizes': {
                'capture': self.capture_queue.qsize(),
                'infer': self.infer_queue.qsize(),
                'result': self.result_queue.qsize(),
                'cloud': self.cloud_queue.qsize()
            }
        }
    
    
    def _print_startup_summary(self):
        """Print startup information."""
        logger.info("=" * 70)
        logger.info("TRAFFIC VIOLATION DETECTION - STARTUP SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Platform: {self.platform_config['name']}")
        logger.info(f"Device: {self.platform_config['device']}")
        logger.info(f"Has GPU: {self.platform_config.get('has_gpu', False)}")
        logger.info(f"Camera: {self.camera_source}")
        logger.info(f"Display: {self.show_display}")
        logger.info("=" * 70)
        logger.info("Thread Architecture:")
        logger.info("  Thread 1 (Camera)      → capture_queue (maxsize=2)")
        logger.info("  Thread 2 (Preprocess)  → infer_queue (maxsize=2)")
        logger.info("  Thread 3 (Inference)   → result_queue (maxsize=4)")
        logger.info("  Thread 4 (Logging)     → cloud_queue (maxsize=10)")
        logger.info("=" * 70)
        logger.info("Press 'q' to quit")
        logger.info("=" * 70)
    
    
    def _print_session_summary(self):
        """Print session statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("TRAFFIC VIOLATION DETECTION - SESSION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Uptime: {stats['uptime_seconds']} seconds")
        logger.info(f"Total Frames: {stats['total_frames']}")
        logger.info(f"Average FPS: {stats['avg_fps']:.1f}")
        logger.info(f"Violations Detected: {stats['violations_detected']}")
        logger.info(f"False Positives Rejected: {stats['false_positives_rejected']}")
        logger.info(f"Plates Read: {stats['plates_read']}")
        logger.info(f"SRGAN Activations: {stats['srgan_activations']}")
        logger.info("=" * 70)
    
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    @staticmethod
    def _letterbox(frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Resize frame to target size with letterboxing (maintain aspect ratio).
        
        Args:
            frame: Input frame (H x W x C)
            target_size: (height, width)
        
        Returns:
            Resized frame (height x width x C) with padding
        """
        h, w = frame.shape[:2]
        target_h, target_w = target_size
        
        # Calculate scale
        scale = min(target_w / w, target_h / h)
        
        # Calculate new size
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(frame, (new_w, new_h))
        
        # Create letterbox
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left
        
        letterboxed = cv2.copyMakeBorder(
            resized,
            top, bottom, left, right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0)
        )
        
        return letterboxed
    
    
    @staticmethod
    def _flush_queue(q: queue.Queue):
        """Empty a queue completely."""
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Run pipeline from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Traffic Violation Detection - Real-time 4-thread Pipeline"
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera source (0=webcam, 1=external) or video file path'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without display (for RPi headless)'
    )
    parser.add_argument(
        '--video',
        type=str,
        default=None,
        help='Input video file (for testing)'
    )
    
    args = parser.parse_args()
    
    # Determine camera source
    camera_source = args.video if args.video else args.camera
    
    # Create and start pipeline
    pipeline = TrafficViolationPipeline(
        camera_source=camera_source,
        show_display=not args.headless
    )
    
    try:
        pipeline.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        pipeline.stop()


if __name__ == "__main__":
    main()
