#!/usr/bin/env python3
"""
Create a dummy ONNX model for testing when no trained model is available.
This is just for testing the system - NOT for actual detection!
"""

import numpy as np
from pathlib import Path

try:
    import onnx
    from onnx import helper, TensorProto
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("onnx not installed. Install with: pip install onnx")

def create_dummy_yolo_model(output_path: str, img_size: int = 416):
    """
    Create a dummy YOLO-like ONNX model for testing.
    
    Input: (1, 3, img_size, img_size) - RGB image
    Output: (1, 25200, 13) - detections [x, y, w, h, conf, cls0...cls7]
    """
    if not ONNX_AVAILABLE:
        print("ERROR: onnx package not installed")
        return False
    
    print(f"Creating dummy YOLO model: {output_path}")
    print(f"Input size: {img_size}×{img_size}")
    
    # Define input
    input_tensor = helper.make_tensor_value_info(
        'images',
        TensorProto.FLOAT,
        [1, 3, img_size, img_size]
    )
    
    # Define output (YOLO format: [x, y, w, h, conf, cls0...cls7])
    # 25200 = 80×80 + 40×40 + 20×20 grid cells × 3 anchors
    output_tensor = helper.make_tensor_value_info(
        'output0',
        TensorProto.FLOAT,
        [1, 25200, 13]  # 13 = 4 (bbox) + 1 (conf) + 8 (classes)
    )
    
    # Create a simple identity-like node (just for structure)
    # In reality, this won't detect anything useful
    node = helper.make_node(
        'Identity',
        inputs=['images'],
        outputs=['intermediate']
    )
    
    # Create constant for output shape
    output_shape = helper.make_tensor(
        'output_shape',
        TensorProto.FLOAT,
        [1, 25200, 13],
        np.zeros((1, 25200, 13), dtype=np.float32).flatten().tolist()
    )
    
    # Create reshape node
    reshape_node = helper.make_node(
        'Constant',
        inputs=[],
        outputs=['output0'],
        value=output_shape
    )
    
    # Create graph
    graph = helper.make_graph(
        [node, reshape_node],
        'dummy_yolo',
        [input_tensor],
        [output_tensor]
    )
    
    # Create model
    model = helper.make_model(graph, producer_name='dummy_yolo_generator')
    model.opset_import[0].version = 11  # Use opset 11 for compatibility
    model.ir_version = 7  # IR version 7 for opset 11
    
    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    onnx.save(model, str(output_path))
    
    print(f"✓ Dummy model created: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("⚠️  WARNING: This is a DUMMY model for testing only!")
    print("   It will NOT detect actual violations.")
    print("   Train a real model or use a pre-trained one for production.")
    
    return True

if __name__ == '__main__':
    import sys
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Create dummy model
    output_path = exports_dir / "dummy_yolo_416.onnx"
    
    success = create_dummy_yolo_model(str(output_path), img_size=416)
    
    if success:
        print("\nNext steps:")
        print("  1. Test: python run.py --mode test --source 0")
        print("  2. For real detection, train a model or use pre-trained weights")
    else:
        print("\nFailed to create dummy model")
        print("Install onnx: pip install onnx")
        sys.exit(1)
