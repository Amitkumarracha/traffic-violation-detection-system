"""
Data Augmentation Tests
Tests for offline augmentation pipeline
"""

import numpy as np
import pytest
import cv2
import tempfile
from pathlib import Path
import shutil
from backend.gan.cyclegan.generate import DataAugmentationGAN


class TestDataAugmentationGAN:
    """Test DataAugmentationGAN augmentation pipeline"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            input_dir = tmppath / 'input' / 'images' / 'train'
            input_dir.mkdir(parents=True)
            
            input_labels = tmppath / 'input' / 'labels' / 'train'
            input_labels.mkdir(parents=True)
            
            output_base = tmppath / 'output'
            
            yield {
                'input_images': input_dir,
                'input_labels': input_labels,
                'output': output_base,
            }
    
    @pytest.fixture
    def synthetic_image(self):
        """Create synthetic test image"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    @pytest.fixture
    def synthetic_label(self):
        """Create synthetic label file content"""
        return "0 0.5 0.5 0.3 0.4\n"  # YOLO format: class x_center y_center width height
    
    # ========== Augmentation Tests ==========
    
    def test_apply_rain(self, synthetic_image):
        """Test rain augmentation"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        result = gen.apply_rain(synthetic_image.copy())
        
        assert result is not None
        assert result.shape == synthetic_image.shape
        assert result.dtype == np.uint8
        # Rain should modify the image
        assert not np.array_equal(result, synthetic_image)
    
    def test_apply_night(self, synthetic_image):
        """Test night augmentation"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        result = gen.apply_night(synthetic_image.copy())
        
        assert result is not None
        assert result.shape == synthetic_image.shape
        assert result.dtype == np.uint8
        # Night should darken image (lower average)
        assert np.mean(result) < np.mean(synthetic_image)
    
    def test_apply_fog(self, synthetic_image):
        """Test fog augmentation"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        result = gen.apply_fog(synthetic_image.copy())
        
        assert result is not None
        assert result.shape == synthetic_image.shape
        assert result.dtype == np.uint8
    
    def test_apply_motion_blur(self, synthetic_image):
        """Test motion blur augmentation"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        result = gen.apply_motion_blur(synthetic_image.copy())
        
        assert result is not None
        assert result.shape == synthetic_image.shape
        assert result.dtype == np.uint8
    
    # ========== Augmentation Function Selection Tests ==========
    
    def test_get_augmentation_func_rain(self):
        """_get_augmentation_func should return rain function"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        func = gen._get_augmentation_func('rain')
        assert func is not None
        assert callable(func)
        assert func == gen.apply_rain
    
    def test_get_augmentation_func_night(self):
        """_get_augmentation_func should return night function"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        func = gen._get_augmentation_func('night')
        assert func is not None
        assert callable(func)
        assert func == gen.apply_night
    
    def test_get_augmentation_func_fog(self):
        """_get_augmentation_func should return fog function"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        func = gen._get_augmentation_func('fog')
        assert func is not None
        assert callable(func)
        assert func == gen.apply_fog
    
    def test_get_augmentation_func_motion_blur(self):
        """_get_augmentation_func should return motion_blur function"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        func = gen._get_augmentation_func('motion_blur')
        assert func is not None
        assert callable(func)
        assert func == gen.apply_motion_blur
    
    def test_get_augmentation_func_invalid(self):
        """_get_augmentation_func should raise for invalid condition"""
        gen = DataAugmentationGAN("dummy", "dummy")
        
        with pytest.raises(ValueError):
            gen._get_augmentation_func('invalid_condition')
    
    # ========== Label File Tests ==========
    
    def test_copy_label_file(self, temp_dirs, synthetic_label):
        """_copy_label_file should copy label correctly"""
        
        # Create label file
        label_path = temp_dirs['input_labels'] / 'img_001.txt'
        label_path.write_text(synthetic_label)
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        result = gen._copy_label_file('img_001.jpg', 'img_001_rain.jpg')
        
        # Should succeed
        assert result is True
        
        # Output label should exist
        output_label = temp_dirs['output'] / 'labels' / 'train' / 'img_001_rain.txt'
        assert output_label.exists()
        
        # Content should match
        assert output_label.read_text() == synthetic_label
    
    def test_copy_label_file_missing(self, temp_dirs):
        """_copy_label_file should handle missing labels gracefully"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        result = gen._copy_label_file('missing.jpg', 'missing_rain.jpg')
        
        # Should return False, not crash
        assert result is False
    
    # ========== Initialization Tests ==========
    
    def test_initialization(self, temp_dirs):
        """Initialization should create output directories"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        assert gen.output_dir.exists()
        assert gen.output_labels_dir.exists()
        assert gen.input_dir == temp_dirs['input_images']
    
    def test_initialization_stats(self, temp_dirs):
        """Initialization should set up stats"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        assert gen.stats['original_images'] == 0
        assert gen.stats['augmented_images'] == 0
        assert gen.stats['label_files_copied'] == 0
    
    # ========== Statistics Tests ==========
    
    def test_get_stats(self, temp_dirs):
        """get_stats should return statistics dictionary"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        stats = gen.get_stats()
        
        assert isinstance(stats, dict)
        assert 'original_images' in stats
        assert 'augmented_images' in stats
        assert 'label_files_copied' in stats
    
    # ========== Integration Tests ==========
    
    def test_full_pipeline_single_image(self, temp_dirs, synthetic_image, synthetic_label):
        """Full pipeline should process single image with all augmentations"""
        
        # Create test image
        img_path = temp_dirs['input_images'] / 'test_img.jpg'
        cv2.imwrite(str(img_path), synthetic_image)
        
        # Create label
        label_path = temp_dirs['input_labels'] / 'test_img.txt'
        label_path.write_text(synthetic_label)
        
        # Run augmentation
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        gen.generate_all(['rain', 'night', 'fog', 'motion_blur'])
        
        # Verify outputs
        output_dir = temp_dirs['output'] / 'images' / 'train'
        
        # Should have: original + original + 4 augmentations = 5 images
        output_images = list(output_dir.glob('*.jpg'))
        assert len(output_images) == 5
        
        # Check expected files
        assert (output_dir / 'test_img_original.jpg').exists()
        assert (output_dir / 'test_img_rain.jpg').exists()
        assert (output_dir / 'test_img_night.jpg').exists()
        assert (output_dir / 'test_img_fog.jpg').exists()
        assert (output_dir / 'test_img_motion_blur.jpg').exists()
    
    def test_statistics_after_generation(self, temp_dirs, synthetic_image, synthetic_label):
        """Statistics should update after generation"""
        
        # Create test image
        img_path = temp_dirs['input_images'] / 'test.jpg'
        cv2.imwrite(str(img_path), synthetic_image)
        
        # Create label
        label_path = temp_dirs['input_labels'] / 'test.txt'
        label_path.write_text(synthetic_label)
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        gen.generate_all(['rain', 'night'])
        
        stats = gen.get_stats()
        
        # 1 original image
        assert stats['original_images'] == 1
        # 1 original + 2 augmented = 3 images
        assert stats['augmented_images'] == 3
        # Should have copied labels
        assert stats['label_files_copied'] > 0
    
    # ========== Condition Tests ==========
    
    def test_selective_conditions(self, temp_dirs, synthetic_image, synthetic_label):
        """Should apply only selected conditions"""
        
        img_path = temp_dirs['input_images'] / 'test.jpg'
        cv2.imwrite(str(img_path), synthetic_image)
        
        label_path = temp_dirs['input_labels'] / 'test.txt'
        label_path.write_text(synthetic_label)
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        # Only rain and night
        gen.generate_all(['rain', 'night'])
        
        output_dir = temp_dirs['output'] / 'images' / 'train'
        output_images = list(output_dir.glob('*.jpg'))
        
        # original + original + rain + night = 4
        assert len(output_images) == 4
        assert (output_dir / 'test_rain.jpg').exists()
        assert (output_dir / 'test_night.jpg').exists()
        assert not (output_dir / 'test_fog.jpg').exists()
    
    # ========== Error Handling Tests ==========
    
    def test_invalid_condition_raises(self, temp_dirs):
        """Invalid condition should raise ValueError"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        with pytest.raises(ValueError):
            gen.generate_all(['invalid_condition'])
    
    def test_empty_directory(self, temp_dirs):
        """Should handle empty input directory gracefully"""
        
        gen = DataAugmentationGAN(
            str(temp_dirs['input_images']),
            str(temp_dirs['output'] / 'images' / 'train')
        )
        
        # Should not crash
        gen.generate_all()
        
        # Output should be empty
        assert len(list(temp_dirs['output'].glob('**/*.jpg'))) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
