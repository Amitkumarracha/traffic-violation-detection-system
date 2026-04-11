#!/usr/bin/env python3
"""
ONNX Model Export Script

Exports trained PyTorch model to ONNX format for deployment.
Searches for best.pt in multiple locations and exports to exports/ folder.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def find_model_checkpoint() -> Path:
    """Find the trained model checkpoint"""
    # Search paths in order of preference
    search_paths = [
        Path("model/checkpoints/best_model_20260406_173815.pt"),
        Path("model/checkpoints/best.pt"),
        Path("model_training/models/best.pt"),
        Path("model_training/exports/best.pt"),
        Path("runs/train/weights/best.pt"),
    ]
    
    for path in search_paths:
        if path.exists():
            logger.info(f"Found model: {path}")
            return path
    
    logger.error("No trained model found!")
    logger.info("Searched paths:")
    for path in search_paths:
        logger.info(f"  - {path}")
    
    return None


def export_to_onnx(model_path: Path, output_dir: Path = Path("exports"), img_size: int = 640):
    """
    Export PyTorch model to ONNX format.
    
    Args:
        model_path: Path to .pt model file
        output_dir: Output directory for ONNX file
        img_size: Input image size (default: 640)
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Install with: pip install ultralytics")
        return None
    
    try:
        logger.info(f"Loading model from: {model_path}")
        model = YOLO(str(model_path))
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename with timestamp
        date_str = datetime.now().strftime('%Y%m%d')
        output_name = f"tvd_yolo26n_{img_size}_{date_str}.onnx"
        output_path = output_dir / output_name
        
        logger.info(f"Exporting to ONNX: {output_path}")
        logger.info(f"Image size: {img_size}×{img_size}")
        
        # Export to ONNX
        model.export(
            format='onnx',
            imgsz=img_size,
            simplify=True,  # Simplify ONNX model
            opset=12,       # ONNX opset version
            dynamic=False   # Fixed input size for better performance
        )
        
        # Move exported file to desired location
        exported_file = model_path.parent / f"{model_path.stem}.onnx"
        if exported_file.exists():
            import shutil
            shutil.move(str(exported_file), str(output_path))
            logger.info(f"✓ ONNX export complete: {output_path}")
            logger.info(f"  Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
            return output_path
        else:
            logger.error("Export failed - ONNX file not found")
            return None
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Export PyTorch model to ONNX')
    parser.add_argument('--model', type=str, help='Path to .pt model file (auto-detected if not specified)')
    parser.add_argument('--output', type=str, default='exports', help='Output directory (default: exports)')
    parser.add_argument('--size', type=int, default=640, help='Input image size (default: 640)')
    
    args = parser.parse_args()
    
    # Find model
    if args.model:
        model_path = Path(args.model)
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            sys.exit(1)
    else:
        model_path = find_model_checkpoint()
        if model_path is None:
            sys.exit(1)
    
    # Export
    output_path = export_to_onnx(
        model_path=model_path,
        output_dir=Path(args.output),
        img_size=args.size
    )
    
    if output_path:
        print("\n" + "="*60)
        print("EXPORT SUCCESSFUL")
        print("="*60)
        print(f"ONNX model: {output_path}")
        print(f"Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
        print(f"Image size: {args.size}×{args.size}")
        print("="*60)
        print("\nNext steps:")
        print(f"  1. Test: python run.py --mode test --source 0")
        print(f"  2. Benchmark: python run.py --benchmark")
        print(f"  3. Quantize for RPi: python scripts/quantize_for_rpi.py")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
