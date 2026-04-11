#!/usr/bin/env python3
"""
Production-Ready Startup Script

Automatically starts the complete system with web interface.
Opens browser automatically to the dashboard.
"""

import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def start_api_server():
    """Start the API server with frontend"""
    import uvicorn
    from backend.api.app import app
    
    print("🚀 Starting API Server with Web Dashboard...")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

def start_detection_pipeline():
    """Start the detection pipeline"""
    from backend.pipeline.main_pipeline import TrafficViolationPipeline
    
    print("🎥 Starting Detection Pipeline...")
    print("📹 Camera will open automatically")
    print("Press 'q' in the camera window to stop")
    print()
    
    try:
        pipeline = TrafficViolationPipeline(
            camera_source=0,
            show_display=True
        )
        pipeline.start()
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline stopped by user")
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")

def open_browser():
    """Open browser after a delay"""
    time.sleep(3)  # Wait for server to start
    print("🌐 Opening web browser...")
    webbrowser.open('http://localhost:8000')

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start Traffic Violation Detection System')
    parser.add_argument('--mode', choices=['web', 'pipeline', 'full'], default='full',
                       help='Startup mode (default: full)')
    parser.add_argument('--no-browser', action='store_true',
                       help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    print()
    print("=" * 70)
    print("🚦 TRAFFIC VIOLATION DETECTION SYSTEM")
    print("=" * 70)
    print()
    
    if args.mode == 'web':
        # Web dashboard only
        if not args.no_browser:
            threading.Thread(target=open_browser, daemon=True).start()
        start_api_server()
        
    elif args.mode == 'pipeline':
        # Detection pipeline only
        start_detection_pipeline()
        
    else:  # full
        # Both web dashboard and detection pipeline
        print("🎯 Starting FULL SYSTEM (Web Dashboard + Detection Pipeline)")
        print()
        
        # Start API server in background thread
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Open browser
        if not args.no_browser:
            threading.Thread(target=open_browser, daemon=True).start()
        
        # Wait a bit for API to start
        time.sleep(2)
        
        # Start detection pipeline in main thread
        start_detection_pipeline()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  System stopped by user")
        print("=" * 70)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
