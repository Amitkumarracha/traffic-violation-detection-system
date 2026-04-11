#!/usr/bin/env python3
"""
INT8 Quantization Script for Raspberry Pi

Quantizes ONNX model to INT8 for faster inference on Raspberry Pi.
Reduces model size by ~4x and increases FPS by 2-3x.
"""

import sys
import logging
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def find_onnx_model() -> Path:
    """Find ONNX model to quantize"""
    search_paths = [
        Path("exports/tvd_yolo26n_640_20260331.onnx"),
        Path("exports").glob("tvd_yolo26n_*.onnx"),
        Path("exports/best.onnx"),
    ]
    
    for path in search_paths:
        if isinstance(path, Path) and path.exists():
            logger.info(f"Found ONNX model: {path}")
            return path
        elif hasattr(path, '__iter__'):
            # It's a glob result
            for p in path:
                logger.info(f"Found ONNX model: {p}")
                return p
    
    logger.error("No ONNX model found in exports/")
    logger.info("Run export first: python scripts/export_model.py")
    return None


class CalibrationDataReader:
    """
    Calibration data reader for INT8 quantization.
    Provides sample images for calibration.
    """
    
    def __init__(self, calibration_images: list, input_name: str, input_shape: tuple):
        """
        Initialize calibration data reader.
        
        Args:
            calibration_images: List of preprocessed image arrays
            input_name: ONNX model input name
            input_shape: Input tensor shape (e.g., (1, 3, 416, 416))
        """
        self.images = calibration_images
        self.input_name = input_name
        self.input_shape = input_shape
        self.current_index = 0
    
    def get_next(self):
        """Get next calibration sample"""
        if self.current_index >= len(self.images):
            return None
        
        image = self.images[self.current_index]
        self.current_index += 1
        
        return {self.input_name: image}
    
    def rewind(self):
        """Reset to beginning"""
        self.current_index = 0


def load_calibration_images(num_images: int = 200, img_size: int = 416) -> list:
    """
    Load calibration images for quantization.
    
    Args:
        num_images: Number of calibration images
        img_size: Image size (default: 416 for RPi)
    
    Returns:
        List of preprocessed image arrays
    """
    import cv2
    
    # Search for calibration images
    image_dirs = [
        Path("dataset/images/val"),
        Path("tests/test_images"),
        Path("examples/test_images"),
    ]
    
    images = []
    for img_dir in image_dirs:
        if img_dir.exists():
            image_files = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
            logger.info(f"Found {len(image_files)} images in {img_dir}")
            
            for img_file in image_files[:num_images]:
                try:
                    # Load and preprocess
                    img = cv2.imread(str(img_file))
                    if img is None:
                        continue
                    
                    # Letterbox resize
                    h, w = img.shape[:2]
                    scale = min(img_size / h, img_size / w)
                    new_h, new_w = int(h * scale), int(w * scale)
                    
                    resized = cv2.resize(img, (new_w, new_h))
                    
                    # Pad to square
                    pad_h = (img_size - new_h) // 2
                    pad_w = (img_size - new_w) // 2
                    
                    padded = np.full((img_size, img_size, 3), 114, dtype=np.uint8)
                    padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
                    
                    # Convert to RGB and normalize
                    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
                    normalized = rgb.astype(np.float32) / 255.0
                    
                    # Transpose to (1, 3, H, W)
                    transposed = np.transpose(normalized, (2, 0, 1))
                    batched = np.expand_dims(transposed, axis=0)
                    
                    images.append(batched)
                    
                    if len(images) >= num_images:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to load {img_file}: {e}")
                    continue
            
            if len(images) >= num_images:
                break
    
    if len(images) == 0:
        logger.warning("No calibration images found - generating synthetic data")
        # Generate random images as fallback
        for _ in range(num_images):
            synthetic = np.random.rand(1, 3, img_size, img_size).astype(np.float32)
            images.append(synthetic)
    
    logger.info(f"Loaded {len(images)} calibration images")
    return images


def quantize_model(
    model_path: Path,
    output_path: Path,
    img_size: int = 416,
    num_calibration_images: int = 200
):
    """
    Quantize ONNX model to INT8.
    
    Args:
        model_path: Path to FP32 ONNX model
        output_path: Path for quantized INT8 model
        img_size: Input image size (default: 416 for RPi)
        num_calibration_images: Number of calibration samples
    """
    try:
        import onnx
        from onnxruntime.quantization import quantize_static, QuantType, CalibrationDataReader as BaseReader
    except ImportError:
        logger.error("onnxruntime not installed. Install with: pip install onnxruntime")
        return False
    
    try:
        logger.info(f"Loading model: {model_path}")
        model = onnx.load(str(model_path))
        
        # Get input name
        input_name = model.graph.input[0].name
        logger.info(f"Model input name: {input_name}")
        
        # Load calibration images
        logger.info(f"Loading {num_calibration_images} calibration images...")
        calibration_images = load_calibration_images(num_calibration_images, img_size)
        
        # Create calibration data reader
        calibration_reader = CalibrationDataReader(
            calibration_images=calibration_images,
            input_name=input_name,
            input_shape=(1, 3, img_size, img_size)
        )
        
        # Quantize
        logger.info(f"Quantizing to INT8...")
        logger.info(f"Output: {output_path}")
        
        quantize_static(
            model_input=str(model_path),
            model_output=str(output_path),
            calibration_data_reader=calibration_reader,
            quant_format=QuantType.QOperator,
            per_channel=False,
            reduce_range=True,  # Better for ARM CPUs
            activation_type=QuantType.QUInt8,
            weight_type=QuantType.QInt8
        )
        
        logger.info("✓ Quantization complete")
        
        # Compare sizes
        original_size = model_path.stat().st_size / (1024 * 1024)
        quantized_size = output_path.stat().st_size / (1024 * 1024)
        reduction = (1 - quantized_size / original_size) * 100
        
        print("\n" + "="*70)
        print("QUANTIZATION RESULTS")
        print("="*70)
        print(f"Original (FP32):  {original_size:.2f} MB")
        print(f"Quantized (INT8): {quantized_size:.2f} MB")
        print(f"Size reduction:   {reduction:.1f}%")
        print("="*70)
        print("\nExpected performance on Raspberry Pi 4:")
        print(f"  FP32 {img_size}px:  8-12 FPS")
        print(f"  INT8 {img_size}px:  18-25 FPS  ← Recommended")
        print("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"Quantization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Quantize ONNX model to INT8 for Raspberry Pi')
    parser.add_argument('--model', type=str, help='Path to ONNX model (auto-detected if not specified)')
    parser.add_argument('--output', type=str, help='Output path for quantized model')
    parser.add_argument('--size', type=int, default=416, help='Input image size (default: 416)')
    parser.add_argument('--calibration-images', type=int, default=200, help='Number of calibration images (default: 200)')
    
    args = parser.parse_args()
    
    # Find model
    if args.model:
        model_path = Path(args.model)
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            sys.exit(1)
    else:
        model_path = find_onnx_model()
        if model_path is None:
            sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = model_path.parent / f"tvd_yolo26n_{args.size}_int8.onnx"
    
    # Quantize
    success = quantize_model(
        model_path=model_path,
        output_path=output_path,
        img_size=args.size,
        num_calibration_images=args.calibration_images
    )
    
    if success:
        print("\nNext steps:")
        print(f"  1. Copy to Raspberry Pi: scp {output_path} pi@raspberrypi:~/")
        print(f"  2. Test on RPi: python run.py --benchmark")
        print(f"  3. Run pipeline: python run.py --no-display")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
