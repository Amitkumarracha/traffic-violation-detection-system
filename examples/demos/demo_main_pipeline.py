"""
Demonstrations for TrafficViolationPipeline

Examples:
    1. Basic real-time detection from webcam
    2. Video file playback mode (testing)
    3. Headless mode for Raspberry Pi
    4. Stats monitoring
    5. Custom callback for violations
    6. Performance profiling
"""

import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline import TrafficViolationPipeline


# ============================================================================
# DEMO 1: Basic Real-Time Detection from Webcam
# ============================================================================

def demo_1_basic_webcam():
    """
    Basic usage: Capture from webcam with display.
    
    Press 'q' to quit.
    """
    logger.info("=" * 70)
    logger.info("DEMO 1: Basic Real-Time Detection from Webcam")
    logger.info("=" * 70)
    
    # Create pipeline
    pipeline = TrafficViolationPipeline(
        camera_source=0,  # Webcam
        show_display=True
    )
    
    # Start (blocks until 'q' pressed or ctrl+c)
    pipeline.start()


# ============================================================================
# DEMO 2: Video File Testing Mode
# ============================================================================

def demo_2_video_file_testing():
    """
    Test mode: Process pre-recorded video file.
    
    Useful for:
        - Testing without camera
        - Replaying recorded violations
        - Benchmarking performance
    
    Requires: traffic_video.mp4 or similar
    """
    logger.info("=" * 70)
    logger.info("DEMO 2: Video File Testing Mode")
    logger.info("=" * 70)
    
    video_file = "traffic_video.mp4"
    
    # Check if video exists
    if not Path(video_file).exists():
        logger.warning(f"Video file not found: {video_file}")
        logger.info("To use this demo:")
        logger.info("  1. Place a video file in the project root")
        logger.info("  2. Name it 'traffic_video.mp4'")
        logger.info("  3. Run this demo again")
        return
    
    # Create pipeline with video file
    pipeline = TrafficViolationPipeline(
        camera_source=video_file,
        show_display=True
    )
    
    # Start
    pipeline.start()


# ============================================================================
# DEMO 3: Headless Mode for Raspberry Pi
# ============================================================================

def demo_3_headless_raspberry_pi():
    """
    Headless mode: No display output, pure detection.
    
    Use cases:
        - Raspberry Pi without monitor
        - Remote deployment
        - Batch processing
    
    Run time: 60 seconds then auto-stop
    """
    logger.info("=" * 70)
    logger.info("DEMO 3: Headless Mode (Raspberry Pi)")
    logger.info("=" * 70)
    
    # Create pipeline without display
    pipeline = TrafficViolationPipeline(
        camera_source=0,
        show_display=False  # No display
    )
    
    try:
        # Start all threads
        pipeline.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


# ============================================================================
# DEMO 4: Stats Monitoring & Callback
# ============================================================================

def demo_4_stats_monitoring():
    """
    Monitor pipeline statistics in real-time.
    
    Demonstration:
        - Create pipeline
        - Start in background
        - Poll stats every 10 seconds
        - Stop after 60 seconds
    """
    logger.info("=" * 70)
    logger.info("DEMO 4: Stats Monitoring & Periodic Reporting")
    logger.info("=" * 70)
    
    import threading
    
    # Create pipeline
    pipeline = TrafficViolationPipeline(
        camera_source=0,
        show_display=False
    )
    
    # Flag to signal monitoring thread
    monitoring = True
    
    def monitor_stats():
        """Background thread to monitor stats"""
        while monitoring:
            try:
                stats = pipeline.get_stats()
                
                logger.info(f"STATS UPDATE:")
                logger.info(f"  Uptime: {stats['uptime_seconds']}s")
                logger.info(f"  FPS: {stats['avg_fps']:.1f}")
                logger.info(f"  Total Frames: {stats['total_frames']}")
                logger.info(f"  Violations: {stats['violations_detected']}")
                logger.info(f"  False Positives: {stats['false_positives_rejected']}")
                logger.info(f"  Plates Read: {stats['plates_read']}")
                logger.info(f"  SRGAN Uses: {stats['srgan_activations']}")
                logger.info(f"  Queue Sizes: {stats['queue_sizes']}")
                
                time.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Monitor error: {e}")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_stats, daemon=True)
    monitor_thread.start()
    
    try:
        # Run for 60 seconds
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        monitoring = False
        pipeline.stop()
        
        # Final stats
        final_stats = pipeline.get_stats()
        logger.info("")
        logger.info("FINAL STATISTICS:")
        logger.info(f"  Total Uptime: {final_stats['uptime_seconds']}s")
        logger.info(f"  Average FPS: {final_stats['avg_fps']:.1f}")
        logger.info(f"  Total Frames Processed: {final_stats['total_frames']}")
        logger.info(f"  Total Violations: {final_stats['violations_detected']}")
        logger.info(f"  False Positives Rejected: {final_stats['false_positives_rejected']}")
        logger.info(f"  Plates Successfully Read: {final_stats['plates_read']}")
        logger.info(f"  SRGAN Activations: {final_stats['srgan_activations']}")


# ============================================================================
# DEMO 5: Performance Profiling
# ============================================================================

def demo_5_performance_profiling():
    """
    Profile pipeline performance with detailed timing.
    
    Measures:
        - Queue depths over time
        - Thread utilization
        - Frame processing rate
        - Violation detection rate
    
    Duration: 30 seconds
    """
    logger.info("=" * 70)
    logger.info("DEMO 5: Performance Profiling")
    logger.info("=" * 70)
    
    import threading
    
    # Create pipeline
    pipeline = TrafficViolationPipeline(
        camera_source=0,
        show_display=False
    )
    
    # Metrics collection
    metrics = {
        'samples': [],
        'stop': False
    }
    
    def collect_metrics():
        """Background thread to collect metrics"""
        while not metrics['stop']:
            try:
                stats = pipeline.get_stats()
                
                metric = {
                    'time': time.time(),
                    'avg_fps': stats['avg_fps'],
                    'total_frames': stats['total_frames'],
                    'violations': stats['violations_detected'],
                    'queue_sizes': stats['queue_sizes'].copy()
                }
                metrics['samples'].append(metric)
                
                # Print live
                logger.info(
                    f"FPS: {metric['avg_fps']:6.1f} | "
                    f"Frames: {metric['total_frames']:5d} | "
                    f"Violations: {metric['violations']:3d} | "
                    f"Queues: {metric['queue_sizes']}"
                )
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Metric collection error: {e}")
    
    # Start metric collection
    metric_thread = threading.Thread(target=collect_metrics, daemon=True)
    metric_thread.start()
    
    try:
        # Run for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        metrics['stop'] = True
        pipeline.stop()
        
        # Analyze metrics
        if len(metrics['samples']) > 0:
            logger.info("")
            logger.info("PERFORMANCE ANALYSIS:")
            
            # FPS statistics
            fps_values = [m['avg_fps'] for m in metrics['samples']]
            logger.info(f"  Average FPS: {sum(fps_values) / len(fps_values):.1f}")
            logger.info(f"  Min FPS: {min(fps_values):.1f}")
            logger.info(f"  Max FPS: {max(fps_values):.1f}")
            
            # Violation rate
            final_violations = metrics['samples'][-1]['violations']
            elapsed = metrics['samples'][-1]['time'] - metrics['samples'][0]['time']
            logger.info(f"  Violations Per Hour: {final_violations / elapsed * 3600:.1f}")
            
            # Queue behavior
            logger.info("  Max Queue Sizes:")
            for queue_name in ['capture', 'infer', 'result', 'cloud']:
                max_size = max(
                    [m['queue_sizes'].get(queue_name, 0) for m in metrics['samples']]
                )
                logger.info(f"    {queue_name}: {max_size}")


# ============================================================================
# DEMO 6: Multi-Source Testing
# ============================================================================

def demo_6_camera_source_options():
    """
    Demonstrate different camera source options.
    
    Options:
        - 0: Default webcam
        - 1: External USB camera
        - 'video.mp4': Pre-recorded video file
    """
    logger.info("=" * 70)
    logger.info("DEMO 6: Camera Source Options")
    logger.info("=" * 70)
    
    print("\nAvailable camera sources:")
    print("  1. Webcam (source=0)")
    print("  2. External USB camera (source=1)")
    print("  3. Pre-recorded video (source='video.mp4')")
    print("\nNote: Modify the source variable below to select")
    
    # Try webcam first
    sources = [0, 1]
    
    for source in sources:
        logger.info(f"\nTrying camera source: {source}")
        
        try:
            pipeline = TrafficViolationPipeline(
                camera_source=source,
                show_display=True
            )
            pipeline.start()
            break
        except Exception as e:
            logger.warning(f"Camera source {source} failed: {e}")
            continue


# ============================================================================
# MAIN MENU
# ============================================================================

def main():
    """Interactive demo menu"""
    
    print("\n")
    print("=" * 70)
    print("Traffic Violation Detection - Main Pipeline Demonstrations")
    print("=" * 70)
    print("\nAvailable Demos:")
    print("  1. Basic Real-Time Detection (Webcam)")
    print("  2. Video File Testing Mode")
    print("  3. Headless Mode (Raspberry Pi)")
    print("  4. Stats Monitoring & Reporting")
    print("  5. Performance Profiling")
    print("  6. Camera Source Options")
    print("  0. Exit")
    print("")
    
    choice = input("Select demo (0-6): ").strip()
    
    demos = {
        '1': demo_1_basic_webcam,
        '2': demo_2_video_file_testing,
        '3': demo_3_headless_raspberry_pi,
        '4': demo_4_stats_monitoring,
        '5': demo_5_performance_profiling,
        '6': demo_6_camera_source_options,
    }
    
    if choice in demos:
        try:
            demos[choice]()
        except KeyboardInterrupt:
            logger.info("\nDemo interrupted by user")
        except Exception as e:
            logger.error(f"Demo error: {e}")
            import traceback
            traceback.print_exc()
    elif choice == '0':
        logger.info("Exiting")
    else:
        logger.error("Invalid choice")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Traffic Violation Detection - Main Pipeline Demos'
    )
    parser.add_argument(
        '--demo',
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help='Run specific demo (1-6)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera source (default: 0 for webcam)'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        # Run specific demo
        demos = {
            1: demo_1_basic_webcam,
            2: demo_2_video_file_testing,
            3: demo_3_headless_raspberry_pi,
            4: demo_4_stats_monitoring,
            5: demo_5_performance_profiling,
            6: demo_6_camera_source_options,
        }
        demos[args.demo]()
    else:
        # Interactive menu
        main()
