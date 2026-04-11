"""
Camera Stream Capture - Thread 1
Captures frames from camera/video source and queues them for processing.

NEVER BLOCKS: Frame queue has maxsize=2, old frames are dropped if queue is full.
ALWAYS AVAILABLE: Latest frame is always ready for pickup.

Thread 1 in 4-thread pipeline:
  Thread 1: Camera capture (this module)
  Thread 2: YOLO detection
  Thread 3: Tracking & processing
  Thread 4: Logging & async tasks

Architecture:
  Camera → Frame Queue (maxsize=2) → Detection Thread (reads latest)
"""

import cv2
import threading
import queue
import logging
import time
from pathlib import Path
from typing import Optional, Tuple
import platform

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Non-blocking camera/video frame capture.
    
    Features:
    - Daemon thread that continuously captures frames
    - Fixed-size queue (maxsize=2) - drops old frames if full
    - Platform detection: RPi picamera2 vs laptop OpenCV
    - Automatic reconnection on capture failure
    - FPS tracking
    - Support for webcam, external camera, video files
    
    Usage:
        camera = CameraStream(source=0, width=1280, height=720, fps=30)
        thread = camera.start()
        
        while True:
            frame = camera.read()
            if frame is not None:
                process(frame)
                print(f"FPS: {camera.get_fps():.1f}")
    """
    
    def __init__(
        self,
        source: int | str = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30
    ):
        """
        Initialize camera stream.
        
        Args:
            source: 0 (laptop webcam), 1 (external camera), or file path for testing
            width: Frame width (default: 1280)
            height: Frame height (default: 720)
            fps: Target FPS (default: 30)
        """
        
        self.source = source
        self.width = width
        self.height = height
        self.target_fps = fps
        
        # Frame queue (maxsize=2 ensures we never block)
        # If full, old frame is discarded, new frame is added
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        
        # Control
        self.stop_event = threading.Event()
        self.capture_thread: Optional[threading.Thread] = None
        
        # Capture device
        self.cap = None
        self.is_rpi = False
        self.is_picamera2 = False
        self.is_video_file_flag = False
        
        # FPS tracking
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.measured_fps = 0.0
        
        # Connection attempts
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # Platform detection
        self._detect_platform()
        
        # Initialize capture device
        self._initialize_capture()
        
        logger.info(self._get_startup_message())
    
    # ========== Platform Detection ==========
    
    def _detect_platform(self):
        """Detect platform (Raspberry Pi vs Laptop)"""
        
        system = platform.system()
        machine = platform.machine()
        
        # Check if Raspberry Pi
        self.is_rpi = machine in ['armv7l', 'armv6l', 'aarch64']
        
        if self.is_rpi:
            logger.info("Platform: Raspberry Pi detected")
    
    def _get_platform_name(self) -> str:
        """Get platform name for logging"""
        
        if self.is_rpi:
            return "rpi_camera"
        else:
            return "laptop_cpu"
    
    # ========== Capture Initialization ==========
    
    def _initialize_capture(self):
        """Initialize camera/video capture device"""
        
        # Check if source is a file
        if isinstance(self.source, str):
            self.is_video_file_flag = True
            self._initialize_video_file()
            return
        
        # Try Raspberry Pi camera first (if on RPi)
        if self.is_rpi:
            if self._try_picamera2():
                self.is_picamera2 = True
                return
        
        # Fallback to OpenCV
        self._initialize_cv2_capture()
    
    def _try_picamera2(self) -> bool:
        """Try to initialize picamera2 (RPi camera module)"""
        
        try:
            from picamera2 import Picamera2
            
            logger.info("Initializing PiCamera2...")
            
            self.cap = Picamera2()
            
            # Configure camera
            config = self.cap.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "BGR888"}
            )
            self.cap.configure(config)
            self.cap.start()
            
            logger.info(f"✓ PiCamera2 initialized: {self.width}×{self.height} @ {self.target_fps}fps")
            return True
        
        except ImportError:
            logger.debug("picamera2 not available, falling back to cv2.VideoCapture")
            return False
        
        except Exception as e:
            logger.warning(f"Failed to initialize picamera2: {e}")
            return False
    
    def _initialize_cv2_capture(self):
        """Initialize OpenCV VideoCapture with platform-specific backend"""
        
        backend = cv2.CAP_ANY
        
        # Use platform-specific backend
        if platform.system() == 'Windows':
            backend = cv2.CAP_DSHOW  # DirectShow for better compatibility
        elif platform.system() in ['Linux', 'Darwin']:
            backend = cv2.CAP_V4L2  # Video4Linux for RPi/Linux fallback
        
        logger.info(f"Initializing cv2.VideoCapture (source={self.source}, backend={backend})...")
        
        try:
            self.cap = cv2.VideoCapture(self.source, backend)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera (source={self.source})")
                return
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Set FPS
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Set optimal buffer size (prefer latest frame)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Reduce latency (hardware acceleration if available)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.cap.set(cv2.CAP_PROP_AUTOEXPOSURE, 0.75)
            
            logger.info(f"✓ cv2.VideoCapture initialized: {self.width}×{self.height} @ {self.target_fps}fps")
        
        except Exception as e:
            logger.error(f"Failed to initialize cv2.VideoCapture: {e}")
    
    def _initialize_video_file(self):
        """Initialize video file for testing"""
        
        video_path = Path(self.source)
        
        if not video_path.exists():
            logger.error(f"Video file not found: {self.source}")
            return
        
        logger.info(f"Opening video file: {self.source}")
        
        try:
            self.cap = cv2.VideoCapture(str(video_path))
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video file: {self.source}")
                return
            
            # Get video properties
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"✓ Video file opened: {width}×{height} @ {fps:.1f}fps")
        
        except Exception as e:
            logger.error(f"Failed to open video file: {e}")
    
    # ========== Capture Loop ==========
    
    def _capture_loop(self):
        """Main capture loop (runs in daemon thread)"""
        
        logger.info("Capture loop started")
        
        while not self.stop_event.is_set():
            try:
                if self.cap is None:
                    time.sleep(0.1)
                    continue
                
                # Read frame
                ret, frame = self.cap.read()
                
                if not ret:
                    self.consecutive_failures += 1
                    
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        logger.warning(
                            f"Capture failed {self.consecutive_failures} times - attempting reconnect"
                        )
                        self._reconnect_capture()
                        self.consecutive_failures = 0
                    
                    time.sleep(0.01)
                    continue
                
                # Reset failure counter on successful read
                self.consecutive_failures = 0
                
                # Put frame in queue (drop old frame if queue is full)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Queue is full, remove old frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
                # Update FPS
                self._update_fps()
                
                # Frame rate limiting (avoid overflowing queue)
                time.sleep(1.0 / self.target_fps * 0.9)
            
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                self.consecutive_failures += 1
                time.sleep(0.1)
        
        logger.info("Capture loop stopped")
    
    def _update_fps(self):
        """Update measured FPS"""
        
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        
        if elapsed >= 1.0:  # Update every second
            self.measured_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()
    
    def _reconnect_capture(self):
        """Attempt to reconnect to camera"""
        
        logger.info("Attempting to reconnect to camera...")
        
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            
            time.sleep(0.5)
            
            # Reinitialize
            self._initialize_capture()
            
            if self.cap is not None:
                logger.info("✓ Camera reconnected")
            else:
                logger.error("Failed to reconnect")
        
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
    
    # ========== Public API ==========
    
    def start(self) -> threading.Thread:
        """
        Start capture thread.
        
        Returns:
            Thread object (daemon thread already started)
        """
        
        if self.capture_thread is not None:
            logger.warning("Capture thread already running")
            return self.capture_thread
        
        # Create daemon thread
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="CameraCapture-Thread1"
        )
        
        self.capture_thread.start()
        
        logger.info("✓ Camera capture thread started")
        
        # Give thread time to read first frame
        time.sleep(0.1)
        
        return self.capture_thread
    
    def read(self) -> Optional[cv2.Mat]:
        """
        Read latest frame from queue (non-blocking).
        
        Returns:
            Frame (BGR numpy array) or None if no frame available
        """
        
        try:
            frame = self.frame_queue.get_nowait()
            return frame
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop capture thread and release resources"""
        
        logger.info("Stopping camera stream...")
        
        self.stop_event.set()
        
        # Wait for thread to stop
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=2.0)
        
        # Release resources
        if self.cap is not None:
            try:
                if self.is_picamera2:
                    self.cap.stop()
                else:
                    self.cap.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            
            self.cap = None
        
        logger.info("✓ Camera stream stopped")
    
    # ========== Status ==========
    
    def get_fps(self) -> float:
        """
        Get measured FPS.
        
        Returns:
            Frames per second (measured over 1 second window)
        """
        return self.measured_fps
    
    def is_video_file(self) -> bool:
        """Check if source is a video file (testing mode)"""
        return self.is_video_file_flag
    
    def is_opened(self) -> bool:
        """Check if camera is open"""
        
        if self.cap is None:
            return False
        
        if self.is_picamera2:
            return True  # PiCamera2 has different interface
        
        return self.cap.isOpened()
    
    def _get_startup_message(self) -> str:
        """Get startup message for logging"""
        
        source_name = "unknown"
        if isinstance(self.source, int):
            if self.source == 0:
                source_name = "webcam"
            else:
                source_name = f"camera_{self.source}"
        else:
            source_name = Path(self.source).name
        
        capture_type = "picamera2" if self.is_picamera2 else "cv2"
        platform_name = self._get_platform_name()
        
        return (
            f"Camera: {self.width}×{self.height} @ {self.target_fps}fps | "
            f"Source: {source_name} | "
            f"Type: {capture_type} | "
            f"Platform: {platform_name}"
        )


def create_camera_stream(
    source: int | str = 0,
    width: int = 1280,
    height: int = 720,
    fps: int = 30
) -> CameraStream:
    """
    Factory function to create and start camera stream.
    
    Args:
        source: Camera/file source
        width: Frame width
        height: Frame height
        fps: Target FPS
    
    Returns:
        Started CameraStream object
    """
    
    camera = CameraStream(source, width, height, fps)
    camera.start()
    return camera
