"""
SRGAN Upscaler Tests
Tests conditional upscaling, performance, and integration
"""

import numpy as np
import cv2
import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# Setup logging
logger = logging.getLogger(__name__)


class TestPlateUpscalerConditional:
    """Test conditional upscaling logic"""
    
    def test_should_upscale_small_area(self):
        """Upscale should trigger for small area"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Create small crop (2000 px² - below 3000 threshold)
        small_crop = np.zeros((25, 80, 3), dtype=np.uint8)  # 80×25 = 2000 px²
        
        assert upscaler.should_upscale(small_crop, threshold_area=3000)
    
    def test_should_not_upscale_large_area(self):
        """Upscale should NOT trigger for large area"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Create large crop (4000 px² - above 3000 threshold)
        large_crop = np.zeros((50, 80, 3), dtype=np.uint8)  # 80×50 = 4000 px²
        
        assert not upscaler.should_upscale(large_crop, threshold_area=3000)
    
    def test_should_upscale_narrow_width(self):
        """Upscale should trigger for narrow width"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Create crop with width < 100px (even if area is large)
        narrow_crop = np.zeros((200, 50, 3), dtype=np.uint8)  # 50×200 = 10000 px², but width=50
        
        assert upscaler.should_upscale(narrow_crop, threshold_area=3000)
    
    def test_should_not_upscale_wide_crop(self):
        """Upscale should NOT trigger for wide crops"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Create wide crop (width ≥ 100px and area ≥ 3000px²)
        wide_crop = np.zeros((40, 150, 3), dtype=np.uint8)  # 150×40 = 6000 px²
        
        assert not upscaler.should_upscale(wide_crop, threshold_area=3000)


class TestPlateUpscalerSize:
    """Test output size after upscaling"""
    
    def test_upscale_if_needed_returns_tuple(self):
        """upscale_if_needed should return (image, bool) tuple"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Small crop that should be skipped (lazy load disabled)
        with patch.object(upscaler, '_init_model'):
            small_crop = np.zeros((20, 45, 3), dtype=np.uint8)
            result, was_upscaled = upscaler.upscale_if_needed(
                small_crop,
                threshold_area=3000
            )
            
            assert isinstance(result, np.ndarray)
            assert isinstance(was_upscaled, bool)
    
    def test_upscale_if_needed_skips_large_crops(self):
        """upscale_if_needed should return original if not needed"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Large crop that should not be upscaled
        large_crop = np.zeros((50, 150, 3), dtype=np.uint8)
        result, was_upscaled = upscaler.upscale_if_needed(
            large_crop,
            threshold_area=3000
        )
        
        # Should return original unchanged
        assert np.array_equal(result, large_crop)
        assert not was_upscaled
    
    def test_upscale_increments_counters(self):
        """upscale_if_needed should increment appropriate counters"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Test skip counter
        large_crop = np.zeros((50, 150, 3), dtype=np.uint8)
        initial_skip = upscaler.total_skipped
        upscaler.upscale_if_needed(large_crop, threshold_area=3000)
        assert upscaler.total_skipped == initial_skip + 1


class TestPlateUpscalerBenchmark:
    """Test benchmark functionality"""
    
    def test_benchmark_returns_dict(self):
        """benchmark() should return statistics dictionary"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Mock the model to avoid required weights
        with patch.object(upscaler, 'initialized', True):
            with patch.object(upscaler, 'model'):
                with patch.object(upscaler, 'upscale', return_value=np.zeros((80, 240, 3))):
                    stats = upscaler.benchmark(num_iterations=5)
        
        assert isinstance(stats, dict)
        assert 'iterations' in stats
        assert 'min_ms' in stats
        assert 'max_ms' in stats
        assert 'mean_ms' in stats
        assert 'median_ms' in stats
        assert 'std_ms' in stats
    
    def test_benchmark_iterations(self):
        """benchmark() should run specified iterations"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        with patch.object(upscaler, 'initialized', True):
            with patch.object(upscaler, 'model'):
                with patch.object(upscaler, 'upscale', return_value=np.zeros((80, 240, 3))) as mock_upscale:
                    upscaler.benchmark(num_iterations=10)
        
        # Should call upscale 10 times
        assert mock_upscale.call_count == 10


class TestPlateUpscalerStats:
    """Test statistics collection"""
    
    def test_get_stats_structure(self):
        """get_stats() should return complete stats dict"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        stats = upscaler.get_stats()
        
        required_keys = [
            'initialized',
            'device',
            'scale',
            'total_upscales',
            'total_skipped',
            'avg_upscale_ms',
            'recent_timings',
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"
    
    def test_stats_initial_values(self):
        """Stats should start at zero"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        stats = upscaler.get_stats()
        
        assert stats['total_upscales'] == 0
        assert stats['total_skipped'] == 0
        assert stats['avg_upscale_ms'] == 0.0
        assert len(stats['recent_timings']) == 0


class TestPlateUpscalerInitialization:
    """Test upscaler initialization and lazy loading"""
    
    def test_lazy_initialization(self):
        """PlateUpscaler should not initialize model on construction"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        assert not upscaler.initialized
        assert upscaler.model is None
    
    def test_init_parameters(self):
        """PlateUpscaler should store init parameters"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler(scale=4, device='cpu')
        
        assert upscaler.scale == 4
        assert upscaler.device == 'cpu'
    
    def test_create_upscaler_helper(self):
        """create_upscaler() utility should create PlateUpscaler"""
        from backend.gan.srgan.inference import create_upscaler
        
        upscaler = create_upscaler(device='cpu')
        
        assert upscaler is not None
        assert upscaler.scale == 4
        assert upscaler.device == 'cpu'


class TestPlateUpscalerError:
    """Test error handling"""
    
    def test_upscale_returns_original_on_error(self):
        """upscale() should return original image on error"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        upscaler.initialized = True
        upscaler.model = Mock()
        upscaler.model.enhance.side_effect = RuntimeError("Model error")
        
        test_image = np.zeros((20, 45, 3), dtype=np.uint8)
        result = upscaler.upscale(test_image)
        
        # Should return original on error
        assert np.array_equal(result, test_image)


class TestPlateUpscalerThresholds:
    """Test threshold configuration"""
    
    def test_class_thresholds(self):
        """Verify class-level thresholds"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        assert PlateUpscaler.MIN_PLATE_AREA == 3000
        assert PlateUpscaler.MIN_PLATE_WIDTH == 100
    
    def test_custom_threshold_area(self):
        """Custom threshold_area should override default"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Area 2500 with default threshold (3000) - should upscale
        small_crop = np.zeros((50, 50, 3), dtype=np.uint8)
        assert upscaler.should_upscale(small_crop, threshold_area=3000)
        
        # Same crop with higher threshold (2000) - should NOT upscale
        assert not upscaler.should_upscale(small_crop, threshold_area=2000)


# Integration tests

class TestSRGANIntegration:
    """Integration tests with OCR module"""
    
    def test_upscaler_export(self):
        """PlateUpscaler should be exported from package"""
        from backend.gan.srgan import PlateUpscaler
        
        upscaler = PlateUpscaler()
        assert upscaler is not None
    
    def test_create_upscaler_export(self):
        """create_upscaler should be exported from package"""
        from backend.gan.srgan import create_upscaler
        
        upscaler = create_upscaler(device='cpu')
        assert upscaler is not None
    
    def test_download_weights_export(self):
        """download_weights should be exported from package"""
        from backend.gan.srgan import download_weights, check_weights
        
        assert download_weights is not None
        assert check_weights is not None


# Performance tests

class TestSRGANPerformance:
    """Performance and timing tests"""
    
    def test_timing_buffer_size(self):
        """Timing buffer should be limited to MAX_TIMING_SAMPLES"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        assert upscaler.upscale_times.maxlen == PlateUpscaler.MAX_TIMING_SAMPLES
    
    def test_timing_buffer_limited_to_100(self):
        """Recent timings should not exceed 100 samples"""
        from backend.gan.srgan.inference import PlateUpscaler
        
        upscaler = PlateUpscaler()
        
        # Simulate many upscales
        for _ in range(150):
            upscaler.upscale_times.append(100.0)
        
        # Should be limited to 100
        assert len(upscaler.upscale_times) <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
