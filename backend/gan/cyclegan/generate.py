"""
Data Augmentation Pipeline for Traffic Violation Detection Dataset

Offline tool to generate synthetic weather conditions for dataset expansion.
Expands dataset from 1,470 to ~6,000 images (4× augmentation).

NOT USED IN LIVE INFERENCE - Runs once offline for training.

Augmentations:
  - Rain: Simulates precipitation with line patterns
  - Night: Dark scenes with blue tint and sensor noise
  - Fog: Atmospheric haze/visibility reduction
  - Motion Blur: Fast-moving vehicle effects

Usage:
    python generate.py
    
    Or programmatically:
    gen = DataAugmentationGAN('dataset/images/train', 'dataset_augmented/images/train')
    gen.generate_all(['rain', 'night', 'fog', 'motion_blur'])
"""

import os
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
import logging
import albumentations as A
from typing import List, Tuple
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataAugmentationGAN:
    """
    Offline data augmentation for weather/condition variation.
    
    Generates synthetic variations (rain, night, fog, motion blur) of training images
    to expand dataset for improved model robustness.
    
    Workflow:
        1. Load each image from input_dir
        2. Apply augmentation (rain/night/fog/motion_blur)
        3. Save augmented image with condition suffix
        4. Copy corresponding label file unchanged
        5. Report summary statistics
    """
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize data augmentation pipeline.
        
        Args:
            input_dir: Path to input images (e.g., dataset/images/train/)
            output_dir: Path to save augmented images (e.g., dataset_augmented/images/train/)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Labels directory (same structure)
        self.input_labels_dir = self.input_dir.parent.parent / 'labels' / 'train'
        self.output_labels_dir = self.output_dir.parent.parent / 'labels' / 'train'
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'original_images': 0,
            'augmented_images': 0,
            'label_files_copied': 0,
        }
        
        logger.info(f"Input images: {self.input_dir}")
        logger.info(f"Output images: {self.output_dir}")
        logger.info(f"Input labels: {self.input_labels_dir}")
    
    # ========== Augmentation Methods ==========
    
    def apply_rain(self, image: np.ndarray) -> np.ndarray:
        """
        Apply rainfall augmentation.
        
        Simulates rain streaks/drops on the image.
        
        Args:
            image: Input BGR image
        
        Returns:
            Augmented image with rain effect
        """
        transform = A.Compose([
            A.RandomRain(
                slant_lower=-10,
                slant_upper=10,
                drop_length=25,
                drop_width=2,
                p=1.0
            )
        ], bbox_params=A.BboxParams(format='pascal_voc'))
        
        # Apply without bboxes (image-only)
        augmented = transform(image=image)['image']
        
        logger.debug(f"Applied rain augmentation")
        return augmented
    
    def apply_night(self, image: np.ndarray) -> np.ndarray:
        """
        Apply nighttime augmentation.
        
        Simulates low-light conditions with:
        - Brightness reduction (20-40% of original)
        - Blue tint (night sky effect)
        - Gaussian noise (sensor noise simulation)
        
        Args:
            image: Input BGR image
        
        Returns:
            Dark, tinted image with noise
        """
        # Step 1: Reduce brightness
        transform_brightness = A.Compose([
            A.RandomBrightnessContrast(
                brightness_limit=(-0.6, -0.4),  # 40-60% darker
                contrast_limit=0.0,
                p=1.0
            )
        ])
        
        augmented = transform_brightness(image=image)['image']
        
        # Step 2: Add blue tint (night sky effect)
        # Increase blue channel, slightly decrease red channel
        augmented = augmented.astype(np.float32)
        augmented[:, :, 0] = np.clip(augmented[:, :, 0] * 1.2, 0, 255)  # Blue
        augmented[:, :, 2] = np.clip(augmented[:, :, 2] * 0.7, 0, 255)  # Red
        augmented = augmented.astype(np.uint8)
        
        # Step 3: Add Gaussian noise (sensor noise)
        noise = np.random.normal(0, 15, augmented.shape)
        augmented = np.clip(augmented.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        
        logger.debug(f"Applied night augmentation (brightness reduction + blue tint + noise)")
        return augmented
    
    def apply_fog(self, image: np.ndarray) -> np.ndarray:
        """
        Apply fog/haze augmentation.
        
        Simulates atmospheric haze/reduced visibility.
        
        Args:
            image: Input BGR image
        
        Returns:
            Fogged/hazy image
        """
        transform = A.Compose([
            A.RandomFog(
                fog_coef_lower=0.3,
                fog_coef_upper=0.6,
                p=1.0
            )
        ])
        
        augmented = transform(image=image)['image']
        
        logger.debug(f"Applied fog augmentation")
        return augmented
    
    def apply_motion_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply motion blur augmentation.
        
        Simulates fast-moving vehicles or camera motion.
        
        Args:
            image: Input BGR image
        
        Returns:
            Motion-blurred image
        """
        transform = A.Compose([
            A.MotionBlur(
                blur_limit=(7, 15),  # Variable blur strength
                p=1.0
            )
        ])
        
        augmented = transform(image=image)['image']
        
        logger.debug(f"Applied motion blur augmentation")
        return augmented
    
    # ========== Utility Methods ==========
    
    def _copy_label_file(self, image_name: str, augmented_name: str) -> bool:
        """
        Copy label file for augmented image (unchanged coordinates).
        
        Args:
            image_name: Original image filename (e.g., 'img_001.jpg')
            augmented_name: Augmented image name (e.g., 'img_001_rain.jpg')
        
        Returns:
            True if successful, False otherwise
        """
        # Get label filenames
        image_base = Path(image_name).stem  # Remove .jpg
        augmented_base = Path(augmented_name).stem
        
        input_label = self.input_labels_dir / f"{image_base}.txt"
        output_label = self.output_labels_dir / f"{augmented_base}.txt"
        
        # Copy label file if it exists
        if input_label.exists():
            shutil.copy2(input_label, output_label)
            return True
        else:
            logger.warning(f"Label file not found: {input_label}")
            return False
    
    def _get_augmentation_func(self, condition: str):
        """
        Get augmentation function for given condition.
        
        Args:
            condition: One of 'rain', 'night', 'fog', 'motion_blur'
        
        Returns:
            Augmentation function
        """
        augmentation_map = {
            'rain': self.apply_rain,
            'night': self.apply_night,
            'fog': self.apply_fog,
            'motion_blur': self.apply_motion_blur,
        }
        
        if condition not in augmentation_map:
            raise ValueError(f"Unknown condition: {condition}")
        
        return augmentation_map[condition]
    
    # ========== Main Processing ==========
    
    def generate_all(self, conditions: List[str] = None):
        """
        Generate augmented images for all conditions.
        
        Processes all input images and creates augmented versions for each condition.
        
        Args:
            conditions: List of augmentations to apply
                       (default: ['rain', 'night', 'fog', 'motion_blur'])
        
        Example:
            gen.generate_all(['rain', 'night', 'fog'])
        """
        
        if conditions is None:
            conditions = ['rain', 'night', 'fog', 'motion_blur']
        
        # Validate conditions
        valid_conditions = {'rain', 'night', 'fog', 'motion_blur'}
        for cond in conditions:
            if cond not in valid_conditions:
                raise ValueError(f"Invalid condition: {cond}. Must be one of {valid_conditions}")
        
        logger.info(f"Starting augmentation with conditions: {conditions}")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        
        # Get image list
        image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
        image_files = sorted([
            f for f in self.input_dir.iterdir()
            if f.suffix in image_extensions
        ])
        
        if not image_files:
            logger.error(f"No images found in {self.input_dir}")
            return
        
        self.stats['original_images'] = len(image_files)
        
        logger.info(f"Found {len(image_files)} images to augment")
        logger.info(f"Total output: {len(image_files)} × {len(conditions) + 1} augmentations")
        
        # Process each image
        for image_path in tqdm(image_files, desc="Processing images"):
            try:
                # Load image
                image = cv2.imread(str(image_path))
                if image is None:
                    logger.warning(f"Failed to read image: {image_path}")
                    continue
                
                image_name = image_path.name
                
                # Copy original image
                output_original = self.output_dir / f"{image_path.stem}_original{image_path.suffix}"
                shutil.copy2(image_path, output_original)
                
                # Copy original label
                if self._copy_label_file(image_name, f"{image_path.stem}_original{image_path.suffix}"):
                    self.stats['label_files_copied'] += 1
                
                # Apply each augmentation
                for condition in conditions:
                    try:
                        # Get augmentation function
                        aug_func = self._get_augmentation_func(condition)
                        
                        # Apply augmentation
                        augmented_image = aug_func(image)
                        
                        # Save augmented image
                        output_name = f"{image_path.stem}_{condition}{image_path.suffix}"
                        output_path = self.output_dir / output_name
                        
                        success = cv2.imwrite(str(output_path), augmented_image)
                        if not success:
                            logger.warning(f"Failed to write: {output_path}")
                            continue
                        
                        # Copy label file (same coordinates)
                        if self._copy_label_file(image_name, output_name):
                            self.stats['label_files_copied'] += 1
                        
                        self.stats['augmented_images'] += 1
                    
                    except Exception as e:
                        logger.error(f"Error applying {condition} to {image_name}: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
                continue
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print augmentation summary statistics"""
        
        print("\n" + "=" * 80)
        print("DATA AUGMENTATION SUMMARY")
        print("=" * 80)
        
        total_output = self.stats['augmented_images'] + self.stats['original_images']
        
        print(f"\n📊 Statistics:")
        print(f"   Original images: {self.stats['original_images']}")
        print(f"   Augmented images: {self.stats['augmented_images']}")
        print(f"   Total images: {total_output}")
        print(f"   Label files copied: {self.stats['label_files_copied']}")
        
        if self.stats['original_images'] > 0:
            expansion_factor = total_output / self.stats['original_images']
            print(f"\n📈 Dataset Expansion:")
            print(f"   Expansion factor: {expansion_factor:.1f}×")
            print(f"   {self.stats['original_images']} → {total_output} images")
        
        print(f"\n📁 Output Directory: {self.output_dir}")
        print(f"📁 Output Labels: {self.output_labels_dir}")
        
        print("\n✅ Augmentation complete!")
        print("=" * 80 + "\n")
    
    def get_stats(self) -> dict:
        """
        Get augmentation statistics.
        
        Returns:
            Dictionary with augmentation statistics
        """
        return self.stats.copy()


def main():
    """Main entry point for offline data augmentation"""
    
    # Configuration
    input_dir = 'dataset/images/train'
    output_dir = 'dataset_augmented/images/train'
    
    # Check if input directory exists
    if not Path(input_dir).exists():
        logger.error(f"Input directory not found: {input_dir}")
        logger.info("Expected structure:")
        logger.info("  dataset/")
        logger.info("  ├── images/")
        logger.info("  │   └── train/  ← input images here")
        logger.info("  └── labels/")
        logger.info("      └── train/  ← .txt label files here")
        return
    
    try:
        # Create augmentation pipeline
        print("\n" + "=" * 80)
        print("TRAFFIC VIOLATION DETECTION - DATA AUGMENTATION")
        print("Weather/Condition Variation Generation")
        print("=" * 80 + "\n")
        
        gen = DataAugmentationGAN(input_dir, output_dir)
        
        # Apply all augmentations
        gen.generate_all(
            conditions=['rain', 'night', 'fog', 'motion_blur']
        )
        
        logger.info("✓ Data augmentation pipeline completed successfully!")
    
    except Exception as e:
        logger.error(f"Fatal error during augmentation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
