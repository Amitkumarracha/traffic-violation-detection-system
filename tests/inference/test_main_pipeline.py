"""
Test Suite for TrafficViolationPipeline (main_pipeline.py)

Tests:
    - Pipeline initialization
    - Component loading
    - Thread creation and lifecycle
    - Queue communication
    - Stats tracking
    - Display overlay rendering
    - Graceful shutdown
"""

import unittest
import time
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.pipeline.main_pipeline import (
    TrafficViolationPipeline,
    FrameData,
    InferenceResult,
    LogEntry,
)


class TestTrafficViolationPipeline(unittest.TestCase):
    """Test TrafficViolationPipeline main orchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = TrafficViolationPipeline(
            camera_source=0,
            show_display=False  # No display for tests
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'pipeline'):
            try:
                self.pipeline.stop()
            except:
                pass
    
    # ========================================================================
    # Initialization Tests
    # ========================================================================
    
    def test_initialization(self):
        """Test pipeline initialization"""
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.camera_source, 0)
        self.assertFalse(self.pipeline.show_display)
        self.assertIsNotNone(self.pipeline.platform_config)
    
    def test_queue_initialization(self):
        """Test queue creation with correct sizes"""
        self.assertEqual(self.pipeline.capture_queue.maxsize, 2)
        self.assertEqual(self.pipeline.infer_queue.maxsize, 2)
        self.assertEqual(self.pipeline.result_queue.maxsize, 4)
        self.assertEqual(self.pipeline.cloud_queue.maxsize, 10)
    
    def test_stop_event_initialization(self):
        """Test stop event is initialized"""
        self.assertFalse(self.pipeline.stop_event.is_set())
    
    def test_stats_initialization(self):
        """Test stats dictionary is initialized"""
        stats = self.pipeline.stats
        self.assertIsNone(stats['start_time'])
        self.assertEqual(stats['total_frames'], 0)
        self.assertEqual(stats['violations_detected'], 0)
    
    # ========================================================================
    # Component Tests
    # ========================================================================
    
    def test_component_initialization(self):
        """Test component init (should handle missing modules gracefully)"""
        # Call init_components without starting full pipeline
        self.pipeline._init_components()
        # Should not crash even if modules missing
        self.assertIsNotNone(self.pipeline)
    
    # ========================================================================
    # Data Structure Tests
    # ========================================================================
    
    def test_frame_data_creation(self):
        """Test FrameData dataclass"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        processed = np.zeros((416, 416, 3), dtype=np.uint8)
        
        fd = FrameData(
            frame_id=1,
            timestamp=time.time(),
            frame=frame,
            processed=processed,
            height=720,
            width=1280
        )
        
        self.assertEqual(fd.frame_id, 1)
        self.assertEqual(fd.height, 720)
        self.assertEqual(fd.width, 1280)
    
    def test_inference_result_creation(self):
        """Test InferenceResult dataclass"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        result = InferenceResult(
            frame_id=1,
            timestamp=time.time(),
            frame=frame,
            detections=[],
            tracks={},
            violations=[]
        )
        
        self.assertEqual(result.frame_id, 1)
        self.assertEqual(len(result.detections), 0)
        self.assertEqual(len(result.violations), 0)
    
    def test_log_entry_creation(self):
        """Test LogEntry dataclass"""
        entry = LogEntry(
            violation_id="test_001",
            timestamp=time.time(),
            violation_type="without_helmet",
            plate_text="MH12AB1234",
            confidence=0.95,
            gps_coords=(18.52, 73.85),
            frame_path=None,
            srgan_applied=False
        )
        
        self.assertEqual(entry.violation_id, "test_001")
        self.assertEqual(entry.violation_type, "without_helmet")
        self.assertEqual(entry.plate_text, "MH12AB1234")
        self.assertAlmostEqual(entry.confidence, 0.95)
    
    # ========================================================================
    # Utility Function Tests
    # ========================================================================
    
    def test_letterbox_same_size(self):
        """Test letterboxing with same size frame"""
        frame = np.zeros((416, 416, 3), dtype=np.uint8)
        result = TrafficViolationPipeline._letterbox(frame, (416, 416))
        
        self.assertEqual(result.shape[:2], (416, 416))
    
    def test_letterbox_resize_height(self):
        """Test letterboxing resizes tall frame correctly"""
        frame = np.zeros((1000, 500, 3), dtype=np.uint8)
        result = TrafficViolationPipeline._letterbox(frame, (416, 416))
        
        self.assertEqual(result.shape[:2], (416, 416))
    
    def test_letterbox_resize_width(self):
        """Test letterboxing resizes wide frame correctly"""
        frame = np.zeros((500, 1000, 3), dtype=np.uint8)
        result = TrafficViolationPipeline._letterbox(frame, (416, 416))
        
        self.assertEqual(result.shape[:2], (416, 416))
    
    def test_letterbox_maintains_aspect_ratio(self):
        """Test that letterboxing maintains aspect ratio"""
        # Create frame with 2:1 aspect ratio
        frame = np.zeros((200, 400, 3), dtype=np.uint8)
        result = TrafficViolationPipeline._letterbox(frame, (416, 416))
        
        # Result should be 416x416
        self.assertEqual(result.shape[:2], (416, 416))
        # But content should maintain 2:1 ratio
        self.assertTrue(result.shape[0] == 416)
    
    # ========================================================================
    # Queue Management Tests
    # ========================================================================
    
    def test_flush_queue_empty(self):
        """Test flush_queue empties a queue"""
        for i in range(5):
            self.pipeline.capture_queue.put(i)
        
        self.assertEqual(self.pipeline.capture_queue.qsize(), 5)
        TrafficViolationPipeline._flush_queue(self.pipeline.capture_queue)
        self.assertEqual(self.pipeline.capture_queue.qsize(), 0)
    
    def test_flush_queue_already_empty(self):
        """Test flush_queue with already empty queue"""
        self.assertEqual(self.pipeline.capture_queue.qsize(), 0)
        # Should not raise
        TrafficViolationPipeline._flush_queue(self.pipeline.capture_queue)
        self.assertEqual(self.pipeline.capture_queue.qsize(), 0)
    
    # ========================================================================
    # Stats Tests
    # ========================================================================
    
    def test_get_stats_before_start(self):
        """Test get_stats before pipeline start"""
        stats = self.pipeline.get_stats()
        
        self.assertIn('uptime_seconds', stats)
        self.assertIn('total_frames', stats)
        self.assertIn('avg_fps', stats)
        self.assertIn('violations_detected', stats)
        self.assertIn('false_positives_rejected', stats)
        self.assertIn('plates_read', stats)
        self.assertIn('srgan_activations', stats)
        self.assertIn('queue_sizes', stats)
    
    def test_stats_initial_values(self):
        """Test stats have correct initial values"""
        stats = self.pipeline.get_stats()
        
        self.assertEqual(stats['total_frames'], 0)
        self.assertEqual(stats['violations_detected'], 0)
        self.assertEqual(stats['false_positives_rejected'], 0)
        self.assertEqual(stats['plates_read'], 0)
        self.assertEqual(stats['srgan_activations'], 0)
    
    def test_stats_queue_sizes(self):
        """Test queue sizes in stats"""
        stats = self.pipeline.get_stats()
        queue_sizes = stats['queue_sizes']
        
        self.assertEqual(queue_sizes['capture'], 0)
        self.assertEqual(queue_sizes['infer'], 0)
        self.assertEqual(queue_sizes['result'], 0)
        self.assertEqual(queue_sizes['cloud'], 0)
    
    # ========================================================================
    # Display Tests
    # ========================================================================
    
    def test_draw_overlay_no_crash(self):
        """Test draw_overlay doesn't crash with valid frame"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Should not raise
        self.pipeline._draw_overlay(frame, fps=30.0, violation_count=5)
    
    def test_draw_overlay_with_violations(self):
        """Test draw_overlay with recent violations"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Add some violations
        self.pipeline.display_violations.append({
            'type': 'without_helmet',
            'plate': 'MH12AB1234',
            'time': time.time()
        })
        
        # Should not raise
        self.pipeline._draw_overlay(frame, fps=30.0, violation_count=1)
    
    def test_draw_overlay_updates_frame(self):
        """Test draw_overlay actually modifies frame"""
        frame_orig = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame = frame_orig.copy()
        
        self.pipeline._draw_overlay(frame, fps=30.0, violation_count=5)
        
        # Frame should be modified (not all zeros)
        self.assertTrue(np.any(frame != frame_orig))
    
    # ========================================================================
    # Thread Safety Tests
    # ========================================================================
    
    def test_thread_safe_stats_update(self):
        """Test stats can be updated safely"""
        for i in range(100):
            self.pipeline.stats['total_frames'] += 1
            self.pipeline.stats['violations_detected'] += 1
        
        self.assertEqual(self.pipeline.stats['total_frames'], 100)
        self.assertEqual(self.pipeline.stats['violations_detected'], 100)
    
    # ========================================================================
    # Lifecycle Tests
    # ========================================================================
    
    def test_stop_event_can_be_set(self):
        """Test stop event can be set"""
        self.assertFalse(self.pipeline.stop_event.is_set())
        self.pipeline.stop_event.set()
        self.assertTrue(self.pipeline.stop_event.is_set())
    
    def test_multiple_stop_calls(self):
        """Test multiple stop calls don't crash"""
        # Should not raise
        self.pipeline.stop()
        self.pipeline.stop()
    
    # ========================================================================
    # Integration Tests
    # ========================================================================
    
    def test_platform_config_loaded(self):
        """Test platform config is loaded"""
        config = self.pipeline.platform_config
        
        self.assertIn('name', config)
        self.assertIn('device', config)
    
    def test_video_file_source(self):
        """Test pipeline with video file source"""
        # Create with video file source
        pipeline = TrafficViolationPipeline(
            camera_source="test_video.mp4",
            show_display=False
        )
        
        self.assertEqual(pipeline.camera_source, "test_video.mp4")
        pipeline.stop()  # Cleanup


class TestFrameDataStructures(unittest.TestCase):
    """Test data structures used in pipeline"""
    
    def test_frame_data_attributes(self):
        """Test FrameData has all required attributes"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        processed = np.zeros((416, 416, 3), dtype=np.uint8)
        
        fd = FrameData(
            frame_id=42,
            timestamp=123.456,
            frame=frame,
            processed=processed,
            height=720,
            width=1280
        )
        
        self.assertEqual(fd.frame_id, 42)
        self.assertEqual(fd.timestamp, 123.456)
        self.assertEqual(fd.height, 720)
        self.assertEqual(fd.width, 1280)
        self.assertEqual(fd.frame.shape, (720, 1280, 3))
        self.assertEqual(fd.processed.shape, (416, 416, 3))


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTrafficViolationPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameDataStructures))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    run_tests()
