#!/usr/bin/env python3
"""
Universal Launcher for Traffic Violation Detection System

Single entry point for ALL platforms (Windows/Linux/Raspberry Pi).

Usage:
    python run.py                           # Run pipeline with webcam
    python run.py --mode api                # Start API server only
    python run.py --mode full               # Pipeline + API
    python run.py --source video.mp4        # Test with video file
    python run.py --benchmark               # Benchmark model
    python run.py --no-display              # Headless mode (RPi)
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner(mode: str, platform_config):
    """Print startup banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════╗
║      Traffic Violation Detection System  v1.0           ║
╠══════════════════════════════════════════════════════════╣
║  Platform : {platform_config.device_name:<42} ║
║  Model    : YOLOv26n  |  mAP50: 85.9%                   ║
║  Mode     : {mode:<46} ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_pipeline(args, platform_config):
    """Run real-time detection pipeline"""
    try:
        from backend.pipeline.main_pipeline import TrafficViolationPipeline
        
        logger.info("Starting pipeline...")
        
        pipeline = TrafficViolationPipeline(
            camera_source=args.source,
            show_display=not args.no_display
        )
        
        pipeline.start()
        
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()


def run_api(args, platform_config):
    """Run API server only"""
    try:
        import uvicorn
        from backend.api.app import app
        
        logger.info(f"Starting API server on {args.host}:{args.port}")
        logger.info(f"API docs: http://{args.host}:{args.port}/docs")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"API server error: {e}")
        import traceback
        traceback.print_exc()


def run_full(args, platform_config):
    """Run pipeline + API simultaneously"""
    import threading
    
    try:
        from backend.pipeline.main_pipeline import TrafficViolationPipeline
        import uvicorn
        from backend.api.app import app
        
        logger.info("Starting full system (pipeline + API)...")
        
        # Start pipeline in background thread
        pipeline = TrafficViolationPipeline(
            camera_source=args.source,
            show_display=not args.no_display
        )
        
        pipeline_thread = threading.Thread(
            target=pipeline.start,
            daemon=True
        )
        pipeline_thread.start()
        
        # Start API in main thread
        logger.info(f"API server: http://{args.host}:{args.port}/docs")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        traceback.print_exc()


def run_test(args, platform_config):
    """Run detector-only test (no tracking/OCR)"""
    try:
        from backend.core.detector import Detector
        import cv2
        import time
        
        logger.info("Running detector-only test...")
        
        # Initialize detector
        detector = Detector(
            model_path=platform_config.model_path,
            inference_size=platform_config.inference_size,
            num_threads=platform_config.num_threads,
            confidence_threshold=platform_config.confidence_threshold
        )
        
        # Open video source
        cap = cv2.VideoCapture(args.source if isinstance(args.source, str) else int(args.source))
        
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {args.source}")
            return
        
        frame_count = 0
        start_time = time.time()
        
        logger.info("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            detections = detector.infer(frame)
            
            # Draw detections
            annotated = detector.draw_detections(frame, detections)
            
            # Show FPS
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            cv2.putText(
                annotated,
                f"FPS: {fps:.1f} | Detections: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # Display
            if not args.no_display:
                cv2.imshow('Detector Test', annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Print summary
        total_time = time.time() - start_time
        logger.info(f"\nTest Summary:")
        logger.info(f"  Frames processed: {frame_count}")
        logger.info(f"  Total time: {total_time:.1f}s")
        logger.info(f"  Average FPS: {frame_count / total_time:.1f}")
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()


def run_benchmark(args, platform_config):
    """Benchmark model performance"""
    try:
        from backend.core.detector import Detector
        
        logger.info("Running benchmark...")
        
        detector = Detector(
            model_path=platform_config.model_path,
            inference_size=platform_config.inference_size,
            num_threads=platform_config.num_threads,
            confidence_threshold=platform_config.confidence_threshold
        )
        
        results = detector.benchmark(n_frames=200)
        
        print("\n" + "="*60)
        print("BENCHMARK RESULTS")
        print("="*60)
        print(f"Platform      : {platform_config.device_name}")
        print(f"Model         : {Path(platform_config.model_path).name}")
        print(f"Inference size: {platform_config.inference_size}×{platform_config.inference_size}")
        print(f"Threads       : {platform_config.num_threads}")
        print(f"Frames tested : {results['n_frames']}")
        print(f"Average time  : {results['avg_ms']:.1f} ms/frame")
        print(f"FPS           : {results['fps']:.1f}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Traffic Violation Detection System - Universal Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Run pipeline with webcam
  python run.py --mode api               # Start API server only
  python run.py --mode full              # Pipeline + API
  python run.py --source video.mp4       # Test with video file
  python run.py --benchmark              # Benchmark model
  python run.py --no-display             # Headless mode (RPi)
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['pipeline', 'api', 'full', 'test'],
        default='pipeline',
        help='Execution mode (default: pipeline)'
    )
    
    parser.add_argument(
        '--source',
        default=0,
        help='Camera source: 0 for webcam, or video file path (default: 0)'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Headless mode - no display output (for Raspberry Pi)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='API server host (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port (default: 8000)'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run model benchmark and exit'
    )
    
    args = parser.parse_args()
    
    # Convert source to int if it's a digit
    if isinstance(args.source, str) and args.source.isdigit():
        args.source = int(args.source)
    
    # Load platform config
    try:
        from backend.config.platform_detector import get_platform_config
        platform_config = get_platform_config()
    except Exception as e:
        logger.error(f"Failed to load platform config: {e}")
        sys.exit(1)
    
    # Print banner
    mode_name = 'benchmark' if args.benchmark else args.mode
    print_banner(mode_name, platform_config)
    
    # Run requested mode
    try:
        if args.benchmark:
            run_benchmark(args, platform_config)
        elif args.mode == 'pipeline':
            run_pipeline(args, platform_config)
        elif args.mode == 'api':
            run_api(args, platform_config)
        elif args.mode == 'full':
            run_full(args, platform_config)
        elif args.mode == 'test':
            run_test(args, platform_config)
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
