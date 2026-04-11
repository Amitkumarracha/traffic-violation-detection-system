#!/usr/bin/env python3
"""
Platform Auto-Detection Module
Detects running platform and returns optimized configuration for inference
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sys

# Optional imports with graceful fallback
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import usb.core
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False


# ==============================================
# PLATFORM CONFIG DATACLASS
# ==============================================
@dataclass
class PlatformConfig:
    """Auto-detected platform configuration"""
    platform: str  # 'raspberry_pi' | 'laptop_cpu' | 'desktop_gpu'
    inference_size: int  # Image size for inference
    num_threads: int  # CPU threads to use
    use_coral: bool  # Coral USB TPU available
    max_fps_target: int  # Target FPS for real-time
    confidence_threshold: float  # Detection confidence cutoff
    model_path: str  # Path to ONNX model
    device_name: str  # Human-readable device name

    def __str__(self):
        return f"""
╔════════════════════════════════════════════════════╗
║          PLATFORM CONFIGURATION SUMMARY            ║
╚════════════════════════════════════════════════════╝
Platform:              {self.platform}
Device:                {self.device_name}
─────────────────────────────────────────────────────
Inference Size:        {self.inference_size}x{self.inference_size}
Target FPS:            {self.max_fps_target}
Confidence Threshold:  {self.confidence_threshold}
CPU Threads:           {self.num_threads}
Coral TPU:             {'✅ YES' if self.use_coral else '❌ NO'}
─────────────────────────────────────────────────────
Model Path:            {self.model_path}
═════════════════════════════════════════════════════
        """


# ==============================================
# PLATFORM DETECTION LOGIC
# ==============================================

def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi"""
    try:
        device_tree_path = Path("/proc/device-tree/model")
        if device_tree_path.exists():
            with open(device_tree_path, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")
                return "Raspberry Pi" in content
    except Exception:
        pass
    return False


def is_desktop_gpu_available() -> bool:
    """Check if CUDA GPU is available"""
    if not TORCH_AVAILABLE:
        return False
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def get_gpu_name() -> Optional[str]:
    """Get GPU device name if available"""
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return None
    try:
        return torch.cuda.get_device_name(0)
    except Exception:
        return None


def detect_coral_usb_tpu() -> bool:
    """Check if Coral USB TPU is connected"""
    if not USB_AVAILABLE:
        return False
    try:
        coral_vid = 0x1a6e
        coral_pid = 0x089a
        device = usb.core.find(idVendor=coral_vid, idProduct=coral_pid)
        return device is not None
    except Exception:
        return False


def get_platform_config(
    model_path: str = None,
) -> PlatformConfig:
    """
    Auto-detect platform and return optimized configuration
    
    Args:
        model_path: Path to ONNX model. If None, uses default location.
    
    Returns:
        PlatformConfig with auto-detected settings
    """
    
    # Resolve model path
    if model_path is None:
        home = Path.home()
        # Try multiple possible locations
        possible_paths = [
            home / "traffic_violation_detection" / "exports" / "tvd_yolo26n_640_20260331.onnx",
            home / "traffic_violation_detection" / "exports" / "dummy_yolo_416.onnx",
            home / "traffic_violation_detection" / "model_training" / "exports" / "tvd_yolo26n_640_20260331.onnx",
            Path("exports/tvd_yolo26n_640_20260331.onnx"),
            Path("exports/dummy_yolo_416.onnx"),
            Path("model_training/exports/tvd_yolo26n_640_20260331.onnx"),
        ]
        
        model_path = None
        for path in possible_paths:
            if path.exists():
                model_path = str(path.resolve())
                break
        
        if model_path is None:
            # Fallback to first path (will fail later with clear error)
            model_path = str(possible_paths[0])
    else:
        model_path = str(Path(model_path).expanduser().resolve())

    # Detect platform
    if is_raspberry_pi():
        platform = "raspberry_pi"
        device_name = "Raspberry Pi"
        inference_size = 320  # Smaller for RPi speed
        num_threads = 4
        max_fps_target = 10
    elif is_desktop_gpu_available():
        platform = "desktop_gpu"
        gpu_name = get_gpu_name() or "Unknown GPU"
        device_name = gpu_name
        inference_size = 640  # Full resolution for GPU
        num_threads = 8
        max_fps_target = 60
    else:
        platform = "laptop_cpu"
        device_name = "Laptop/CPU"
        inference_size = 416  # Balanced for CPU
        num_threads = 4
        max_fps_target = 30

    # Check for Coral TPU (works on any platform)
    use_coral = detect_coral_usb_tpu()

    # Confidence threshold same across all platforms
    confidence_threshold = 0.75

    return PlatformConfig(
        platform=platform,
        inference_size=inference_size,
        num_threads=num_threads,
        use_coral=use_coral,
        max_fps_target=max_fps_target,
        confidence_threshold=confidence_threshold,
        model_path=model_path,
        device_name=device_name,
    )


def print_platform_summary(config: Optional[PlatformConfig] = None):
    """
    Pretty-print the platform configuration
    
    Args:
        config: PlatformConfig to print. If None, auto-detects.
    """
    if config is None:
        config = get_platform_config()
    print(config)


def get_inference_config(model_path: str = None) -> dict:
    """
    Get inference configuration as dictionary
    Useful for passing to inference engine
    
    Args:
        model_path: Path to ONNX model
    
    Returns:
        Dict with inference settings
    """
    config = get_platform_config(model_path)
    
    return {
        "platform": config.platform,
        "inference_size": config.inference_size,
        "num_threads": config.num_threads,
        "use_coral": config.use_coral,
        "max_fps_target": config.max_fps_target,
        "confidence_threshold": config.confidence_threshold,
        "model_path": config.model_path,
        "device_name": config.device_name,
    }


# ==============================================
# MAIN / TESTING
# ==============================================

if __name__ == "__main__":
    print("Detecting platform configuration...\n")
    config = get_platform_config()
    print(config)
    print("\n✅ Configuration loaded successfully!")
