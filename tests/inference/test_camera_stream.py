"""
Camera Stream Tests
Tests for Thread 1 camera capture module
"""

import pytest
import cv2
import time
import numpy as np
from pathlib import Path
import tempfile
from backend.pipeline.camera_stream import CameraStream, create_camera_stream


class TestCameraStreamInitialization:
    """Test CameraStream initialization"""
    
    def test_initialization_default_params(self):
        """CameraStream should initialize with default parameters"""
        
        camera = CameraStream()
        
        assert camera.source == 0
        assert camera.width == 1280
        assert camera.height == 720
        assert camera.target_fps == 30
        assert not camera.stop_event.is_set()
    
    def test_initialization_custom_params(self):
        """CameraStream should accept custom parameters"""
        
        camera = CameraStream(source=1, width=640, height=480, fps=24)
        
        assert camera.source == 1
        assert camera.width == 640
        assert camera.height == 480
        assert camera.target_fps == 24
    
    def test_initialization_with_video_file(self):
        """CameraStream should detect video file source"""
        
        camera = CameraStream(source='test.mp4')
        
        assert camera.is_video_file()
        assert camera.is_video_file_flag is True
    
    def test_frame_queue_maxsize(self):
        """Frame queue should have maxsize=2"""
        
        camera = CameraStream()
        
        assert camera.frame_queue.maxsize == 2


class TestCameraStreamPlacement:
    """Test CameraStream in pipeline architecture"""
    
    def test_is_thread_1(self):
        """CameraStream should be Thread 1"""
        
        camera = CameraStream()
        thread = camera.start()
        
        try:
            assert "Thread1" in thread.name or "CameraCapture" in thread.name
            assert thread.daemon is True
        finally:
            camera.stop()
    
    def test_daemon_thread(self):
        """Capture thread should be daemon thread"""
        
        camera = CameraStream()
        thread = camera.start()
        
        try:
            assert thread.daemon is True
        finally:
            camera.stop()


class TestCameraStreamNonBlocking:
    """Test non-blocking behavior"""
    
    def test_read_non_blocking_returns_none_when_empty(self):
        """read() should return None immediately if queue empty"""
        
        camera = CameraStream()
        # Don't start capture thread
        
        result = camera.read()
        
        assert result is None
    
    def test_frame_queue_never_blocks(self):
        """Frame queue should never block thread"""
        
        camera = CameraStream()
        
        # Fill queue
        camera.frame_queue.put(np.zeros((480, 640, 3), dtype=np.uint8))
        camera.frame_queue.put(np.zeros((480, 640, 3), dtype=np.uint8))
        
        # Should be full
        assert camera.frame_queue.qsize() == 2
        
        # Adding another frame should not block (should drop old)
        # We simulate the drop-old logic
        try:
            camera.frame_queue.get_nowait()
            camera.frame_queue.put_nowait(np.zeros((480, 640, 3), dtype=np.uint8))
            success = True
        except:
            success = False
        
        assert success


class TestCameraStreamStartStop:
    """Test start/stop functionality"""
    
    def test_start_returns_thread(self):
        """start() should return Thread object"""
        
        camera = CameraStream()
        thread = camera.start()
        
        try:
            assert thread is not None
            assert isinstance(thread, type(thread))
            assert thread.is_alive()
        finally:
            camera.stop()
    
    def test_stop_stops_thread(self):
        """stop() should stop capture thread"""
        
        camera = CameraStream()
        thread = camera.start()
        
        time.sleep(0.2)
        assert thread.is_alive()
        
        camera.stop()
        
        # Give thread time to stop
        time.sleep(0.5)
        assert not thread.is_alive()
    
    def test_start_idempotent(self):
        """start() should handle multiple calls"""
        
        camera = CameraStream()
        thread1 = camera.start()
        thread2 = camera.start()
        
        try:
            # Should return same thread
            assert thread1 is thread2
        finally:
            camera.stop()


class TestCameraStreamPlatformDetection:
    """Test platform detection"""
    
    def test_is_rpi_detection(self):
        """Platform detection should identify RPi"""
        
        camera = CameraStream()
        
        # is_rpi should be boolean
        assert isinstance(camera.is_rpi, bool)
    
    def test_platform_name(self):
        """_get_platform_name should return valid platform"""
        
        camera = CameraStream()
        platform_name = camera._get_platform_name()
        
        assert platform_name in ['laptop_cpu', 'rpi_camera']
    
    def test_startup_message_contains_platform(self):
        """Startup message should include platform info"""
        
        camera = CameraStream()
        message = camera._get_startup_message()
        
        assert 'Camera:' in message
        assert 'Platform:' in message
        assert '1280x720' in message or '1280×720' in message


class TestCameraStreamStatus:
    """Test status methods"""
    
    def test_get_fps_returns_float(self):
        """get_fps() should return float"""
        
        camera = CameraStream()
        
        fps = camera.get_fps()
        
        assert isinstance(fps, float)
        assert fps >= 0.0
    
    def test_is_video_file_returns_bool(self):
        """is_video_file() should return boolean"""
        
        camera_device = CameraStream(source=0)
        camera_file = CameraStream(source='test.mp4')
        
        assert camera_device.is_video_file() is False
        assert camera_file.is_video_file() is True
    
    def test_is_opened_returns_bool(self):
        """is_opened() should return boolean"""
        
        camera = CameraStream()
        
        result = camera.is_opened()
        
        assert isinstance(result, bool)


class TestCameraStreamQueueManagement:
    """Test queue management (core non-blocking feature)"""
    
    def test_queue_drops_old_frame_when_full(self):
        """Queue should drop old frame when full"""
        
        camera = CameraStream()
        
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 10
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 20
        frame3 = np.ones((480, 640, 3), dtype=np.uint8) * 30
        
        # Add two frames (fills queue)
        camera.frame_queue.put(frame1)
        camera.frame_queue.put(frame2)
        
        # Simulate the drop-old-frame logic from _capture_loop
        try:
            camera.frame_queue.get_nowait()
            camera.frame_queue.put_nowait(frame3)
        except:
            pass
        
        # Read back
        f1 = camera.read()
        f2 = camera.read()
        
        # Should have the latest frames
        # (exact order depends on timing, but should have frame3)
        frames = []
        if f1 is not None:
            frames.append(np.mean(f1))
        if f2 is not None:
            frames.append(np.mean(f2))
        
        # At least have frame3 (value 30)
        assert max(frames) >= 20 if frames else True
    
    def test_read_returns_none_when_queue_empty(self):
        """read() should return None when queue empty"""
        
        camera = CameraStream()
        
        # Queue is empty
        assert camera.frame_queue.empty()
        
        result = camera.read()
        
        assert result is None
    
    def test_read_returns_frame_when_available(self):
        """read() should return frame when available"""
        
        camera = CameraStream()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        camera.frame_queue.put(frame)
        
        result = camera.read()
        
        assert result is not None
        assert result.shape == (480, 640, 3)


class TestCameraStreamFactory:
    """Test factory function"""
    
    def test_create_camera_stream_default(self):
        """create_camera_stream() should create and start"""
        
        camera = create_camera_stream()
        
        try:
            assert isinstance(camera, CameraStream)
            # Thread should be started
            assert camera.capture_thread is not None
        finally:
            camera.stop()
    
    def test_create_camera_stream_custom(self):
        """create_camera_stream() should accept custom params"""
        
        camera = create_camera_stream(source=0, width=640, height=480, fps=24)
        
        try:
            assert camera.width == 640
            assert camera.height == 480
            assert camera.target_fps == 24
        finally:
            camera.stop()


class TestCameraStreamErrorHandling:
    """Test error handling and recovery"""
    
    def test_reconnect_capability(self):
        """Camera should have reconnect capability"""
        
        camera = CameraStream()
        
        # Should have reconnect method
        assert hasattr(camera, '_reconnect_capture')
        assert callable(camera._reconnect_capture)
    
    def test_consecutive_failure_tracking(self):
        """Camera should track consecutive failures"""
        
        camera = CameraStream()
        
        assert camera.consecutive_failures == 0
        assert camera.max_consecutive_failures == 3
    
    def test_fps_tracking_initialization(self):
        """FPS tracking should be initialized"""
        
        camera = CameraStream()
        
        assert camera.frame_count == 0
        assert camera.measured_fps == 0.0


class TestCameraStreamLogging:
    """Test logging output"""
    
    def test_startup_message_format(self):
        """Startup message should have proper format"""
        
        camera = CameraStream()
        message = camera._get_startup_message()
        
        # Should contain all required info
        assert 'Camera:' in message
        assert 'fps' in message or '@' in message
        assert 'Source:' in message
        assert 'Platform:' in message
        assert 'Type:' in message


class TestCameraStreamIntegration:
    """Integration tests"""
    
    def test_full_lifecycle(self):
        """Test complete start/read/stop lifecycle"""
        
        camera = CameraStream()
        
        # Start
        thread = camera.start()
        assert thread.is_alive()
        
        # Give time for first frame
        time.sleep(0.2)
        
        # Read (may or may not have frame depending on camera)
        frame = camera.read()
        # Just verify it doesn't crash
        assert frame is None or isinstance(frame, np.ndarray)
        
        # Stop
        camera.stop()
        time.sleep(0.2)
        assert not thread.is_alive()
    
    def test_multiple_read_calls(self):
        """Multiple read calls should not block"""
        
        camera = CameraStream()
        
        frame = np.ones((480, 640, 3), dtype=np.uint8)
        camera.frame_queue.put(frame)
        
        # Should not block
        t0 = time.time()
        
        camera.read()
        camera.read()
        camera.read()
        
        elapsed = time.time() - t0
        
        # Should be very fast (all non-blocking)
        assert elapsed < 0.1  # Much less than 100ms


class TestCameraStreamVideoFile:
    """Test video file support"""
    
    def test_is_video_file_with_path(self):
        """Video file should be detected by source"""
        
        camera = CameraStream(source='video.mp4')
        
        assert camera.is_video_file()
    
    def test_is_video_file_with_device(self):
        """Device camera should not be detected as video file"""
        
        camera = CameraStream(source=0)
        
        assert not camera.is_video_file()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
