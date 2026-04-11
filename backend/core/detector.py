#!/usr/bin/env python3
"""
YOLO26n Traffic Violation Detector
ONNX-based inference for real-time detection on CPU/GPU/TPU
"""

import numpy as np
import time
from typing import List, Tuple, NamedTuple, Optional
from pathlib import Path
from dataclasses import dataclass
import cv2

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    raise ImportError(
        "onnxruntime is required. Install with: pip install onnxruntime"
    )


# ==============================================
# CONSTANTS & CLASS DEFINITIONS
# ==============================================

CLASS_NAMES = [
    "with_helmet",
    "without_helmet",
    "number_plate",
    "riding",
    "triple_ride",
    "traffic_violation",
    "motorcycle",
    "vehicle",
]

CLASS_COLORS = {
    "with_helmet": (0, 255, 0),           # Green
    "without_helmet": (0, 0, 255),        # Red
    "number_plate": (0, 255, 255),        # Yellow
    "riding": (255, 0, 0),                # Blue (BGR)
    "triple_ride": (0, 165, 255),         # Orange
    "traffic_violation": (0, 0, 255),     # Red
    "motorcycle": (255, 255, 0),          # Cyan
    "vehicle": (128, 0, 128),             # Purple
}

DANGER_CLASSES = {
    "without_helmet",
    "triple_ride",
    "traffic_violation",
}


class Detection(NamedTuple):
    """Single detection result"""
    class_id: int
    class_name: str
    confidence: float
    x1: int         # Pixel coordinates
    y1: int
    x2: int
    y2: int
    center_x: int
    center_y: int
    width: int
    height: int
    is_danger: bool


# ==============================================
# DETECTOR CLASS
# ==============================================

class Detector:
    """
    YOLO26n Traffic Violation Detector
    Loads and runs ONNX model for real-time inference
    """

    def __init__(
        self,
        model_path: str,
        inference_size: int = 640,
        num_threads: int = 4,
        confidence_threshold: float = 0.75,
        providers: Optional[List[str]] = None,
    ):
        """
        Initialize detector with ONNX model
        
        Args:
            model_path: Path to ONNX model file
            inference_size: Input image size (square)
            num_threads: Number of CPU threads for inference
            confidence_threshold: Minimum confidence to report detection
            providers: List of execution providers (e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider'])
        """
        if not ONNX_AVAILABLE:
            raise RuntimeError("onnxruntime is not installed")
        
        self.model_path = str(Path(model_path).expanduser().resolve())
        self.inference_size = inference_size
        self.num_threads = num_threads
        self.confidence_threshold = confidence_threshold
        
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Setup execution providers
        if providers is None:
            providers = ["CPUExecutionProvider"]
        
        # Configure session options
        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = num_threads
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        # Load model
        self.session = ort.InferenceSession(
            self.model_path,
            session_options,
            providers=providers,
        )
        
        # Get input/output info
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        print(f"✅ Model loaded from: {self.model_path}")
        print(f"   Input: {self.input_name}")
        print(f"   Output: {self.output_name}")
        print(f"   Inference size: {inference_size}x{inference_size}")
        print(f"   Num threads: {num_threads}")
        print(f"   Providers: {self.session.get_providers()}")
        
        # Warmup with dummy input (avoid first-frame lag)
        print("🔥 Warming up model...")
        self._warmup()
        print("✅ Warmup complete")

    def _warmup(self, n_warmup: int = 3):
        """Warmup model by running dummy inference"""
        dummy_input = np.random.randn(
            1, 3, self.inference_size, self.inference_size
        ).astype(np.float32)
        
        for _ in range(n_warmup):
            try:
                self.session.run(
                    [self.output_name],
                    {self.input_name: dummy_input},
                )
            except Exception as e:
                print(f"⚠️ Warmup warning: {e}")

    def preprocess(
        self, frame: np.ndarray
    ) -> Tuple[np.ndarray, float, int, int]:
        """
        Preprocess frame for inference
        Applies letterbox padding, resizing, normalization
        
        Args:
            frame: BGR numpy array from OpenCV (H, W, 3)
        
        Returns:
            Tuple of (tensor, scale_factor, pad_top, pad_left)
            - tensor: (1, 3, H, W) float32 in range 0-1, RGB
            - scale_factor: Scaling factor for coordinate conversion
            - pad_top: Top padding amount
            - pad_left: Left padding amount
        """
        h, w = frame.shape[:2]
        
        # Calculate letterbox scale
        scale = min(self.inference_size / w, self.inference_size / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize with aspect ratio preservation
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Calculate padding
        pad_left = (self.inference_size - new_w) // 2
        pad_top = (self.inference_size - new_h) // 2
        pad_right = self.inference_size - new_w - pad_left
        pad_bottom = self.inference_size - new_h - pad_top
        
        # Apply letterbox padding (gray background)
        padded = cv2.copyMakeBorder(
            resized,
            pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_CONSTANT,
            value=(128, 128, 128),
        )
        
        # BGR to RGB
        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0-1
        normalized = rgb.astype(np.float32) / 255.0
        
        # Transpose to (1, 3, H, W) for ONNX
        tensor = normalized.transpose(2, 0, 1)[np.newaxis, :, :, :].astype(
            np.float32
        )
        
        return tensor, scale, pad_top, pad_left

    def infer(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on frame and return detections
        
        Args:
            frame: BGR numpy array (H, W, 3) from OpenCV
        
        Returns:
            List of Detection namedtuples
        """
        h, w = frame.shape[:2]
        
        # Preprocess
        tensor, scale, pad_top, pad_left = self.preprocess(frame)
        
        # Run inference
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: tensor},
        )
        
        # Parse outputs: (1, N, 6) -> [class_id, x_center, y_center, w, h, confidence]
        predictions = outputs[0][0]  # (N, 6)
        
        detections = []
        
        for pred in predictions:
            class_id, x_c_norm, y_c_norm, w_norm, h_norm, conf = pred
            
            # Filter by confidence
            if conf < self.confidence_threshold:
                continue
            
            class_id = int(class_id)
            class_name = CLASS_NAMES[class_id]
            
            # Convert normalized coords to pixel coords
            # First remove padding
            x_c_padded_px = x_c_norm * self.inference_size
            y_c_padded_px = y_c_norm * self.inference_size
            w_padded_px = w_norm * self.inference_size
            h_padded_px = h_norm * self.inference_size
            
            # Remove padding effect
            x_c_px = (x_c_padded_px - pad_left) / scale
            y_c_px = (y_c_padded_px - pad_top) / scale
            w_px = w_padded_px / scale
            h_px = h_padded_px / scale
            
            # Convert to corner coordinates
            x1 = max(0, int(x_c_px - w_px / 2))
            y1 = max(0, int(y_c_px - h_px / 2))
            x2 = min(w, int(x_c_px + w_px / 2))
            y2 = min(h, int(y_c_px + h_px / 2))
            
            detection = Detection(
                class_id=class_id,
                class_name=class_name,
                confidence=float(conf),
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                center_x=int(x_c_px),
                center_y=int(y_c_px),
                width=int(w_px),
                height=int(h_px),
                is_danger=class_name in DANGER_CLASSES,
            )
            
            detections.append(detection)
        
        return detections

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        line_thickness: int = 2,
        font_scale: float = 0.7,
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: BGR numpy array (H, W, 3)
            detections: List of Detection objects
            line_thickness: Thickness of drawn lines
            font_scale: Scale of text font
        
        Returns:
            Annotated BGR frame
        """
        annotated = frame.copy()
        
        for detection in detections:
            # Get color
            color = CLASS_COLORS.get(detection.class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(
                annotated,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                color,
                line_thickness,
            )
            
            # Draw label
            label = f"{detection.class_name} {detection.confidence:.2f}"
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
            )
            
            # Label background
            cv2.rectangle(
                annotated,
                (detection.x1, detection.y1 - label_size[1] - baseline),
                (detection.x1 + label_size[0], detection.y1),
                color,
                -1,  # Filled
            )
            
            # Label text
            cv2.putText(
                annotated,
                label,
                (detection.x1, detection.y1 - baseline),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),  # White text
                1,
            )
            
            # Draw center point for danger violations
            if detection.is_danger:
                cv2.circle(
                    annotated,
                    (detection.center_x, detection.center_y),
                    5,
                    (0, 0, 255),  # Red dot
                    -1,
                )
        
        return annotated

    def benchmark(
        self, n_frames: int = 100, image_size: Optional[int] = None
    ) -> dict:
        """
        Benchmark model inference performance
        
        Args:
            n_frames: Number of frames to benchmark
            image_size: Size of test images (default: inference_size)
        
        Returns:
            Dict with timing statistics
        """
        if image_size is None:
            image_size = self.inference_size
        
        # Create dummy frames
        dummy_frame = np.random.randint(0, 256, (image_size, image_size, 3), dtype=np.uint8)
        
        print(f"\n📊 Benchmarking {n_frames} frames...")
        print(f"   Frame size: {image_size}x{image_size}")
        
        # Warmup
        for _ in range(5):
            _ = self.infer(dummy_frame)
        
        # Benchmark
        times = []
        for i in range(n_frames):
            start = time.time()
            _ = self.infer(dummy_frame)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
            
            if (i + 1) % 20 == 0:
                print(f"   Progress: {i + 1}/{n_frames}")
        
        times = np.array(times)
        
        results = {
            "total_frames": n_frames,
            "min_ms": float(np.min(times)),
            "max_ms": float(np.max(times)),
            "mean_ms": float(np.mean(times)),
            "median_ms": float(np.median(times)),
            "std_ms": float(np.std(times)),
            "fps_mean": float(1000.0 / np.mean(times)),
            "fps_min": float(1000.0 / np.max(times)),
            "fps_max": float(1000.0 / np.min(times)),
        }
        
        print(f"\n✅ Benchmark Results:")
        print(f"   Mean: {results['mean_ms']:.2f} ms ({results['fps_mean']:.1f} FPS)")
        print(f"   Median: {results['median_ms']:.2f} ms")
        print(f"   Range: {results['min_ms']:.2f} - {results['max_ms']:.2f} ms")
        print(f"   Std Dev: {results['std_ms']:.2f} ms")
        print(f"   FPS Range: {results['fps_min']:.1f} - {results['fps_max']:.1f}")
        
        return results

    def get_stats(self) -> dict:
        """Get detector configuration and stats"""
        return {
            "model_path": self.model_path,
            "inference_size": self.inference_size,
            "num_threads": self.num_threads,
            "confidence_threshold": self.confidence_threshold,
            "num_classes": len(CLASS_NAMES),
            "classes": CLASS_NAMES,
            "providers": self.session.get_providers(),
            "input_name": self.input_name,
            "output_name": self.output_name,
        }

    def print_stats(self):
        """Pretty-print detector statistics"""
        stats = self.get_stats()
        
        print("""
╔════════════════════════════════════════════════════╗
║          DETECTOR CONFIGURATION                    ║
╚════════════════════════════════════════════════════╝
""")
        print(f"Model:                 {Path(stats['model_path']).name}")
        print(f"Inference Size:        {stats['inference_size']}x{stats['inference_size']}")
        print(f"Num Threads:           {stats['num_threads']}")
        print(f"Confidence Threshold:  {stats['confidence_threshold']}")
        print(f"Num Classes:           {stats['num_classes']}")
        print(f"Classes:               {', '.join(stats['classes'])}")
        print(f"Providers:             {', '.join(stats['providers'])}")
        print("""
════════════════════════════════════════════════════╗
        """)


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def get_danger_detections(detections: List[Detection]) -> List[Detection]:
    """Filter detections to only danger classes"""
    return [d for d in detections if d.is_danger]


def print_detections(detections: List[Detection]):
    """Pretty-print detections"""
    if not detections:
        print("No detections")
        return
    
    print(f"\n📊 Detections ({len(detections)}):")
    for i, det in enumerate(detections, 1):
        danger_marker = "⚠️" if det.is_danger else "✅"
        print(
            f"  {i}. {danger_marker} {det.class_name:20} "
            f"conf={det.confidence:.2f} "
            f"pos=({det.x1},{det.y1})-({det.x2},{det.y2})"
        )


# ==============================================
# MAIN / TESTING
# ==============================================

if __name__ == "__main__":
    from backend.config import get_platform_config
    
    print("Testing Detector module...\n")
    
    # Load from config
    config = get_platform_config()
    
    # Initialize detector
    detector = Detector(
        model_path=config.model_path,
        inference_size=config.inference_size,
        num_threads=config.num_threads,
        confidence_threshold=config.confidence_threshold,
    )
    
    # Print stats
    detector.print_stats()
    
    # Create test frame
    test_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    
    # Run inference
    print("\n🎯 Running inference on test frame...")
    detections = detector.infer(test_frame)
    print_detections(detections)
    
    # Draw and save
    annotated = detector.draw_detections(test_frame, detections)
    print(f"\n✅ Detector working correctly!")
    
    # Run benchmark
    print("\n" + "=" * 50)
    detector.benchmark(n_frames=50)
