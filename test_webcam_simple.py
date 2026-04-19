#!/usr/bin/env python3
"""
Simple webcam test without complex detection
Just opens camera and shows feed
"""

import cv2
import sys

def main():
    print("=" * 60)
    print("  Simple Webcam Test")
    print("=" * 60)
    print("\nOpening webcam...")
    
    # Try to open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ ERROR: Cannot open webcam!")
        print("\nTroubleshooting:")
        print("  1. Check if another app is using the camera")
        print("  2. Try camera index 1: python test_webcam_simple.py 1")
        print("  3. Check camera permissions in Windows Settings")
        return 1
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    print(f"✅ Camera opened successfully!")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps:.1f}")
    print("\nControls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to take screenshot")
    print("\nShowing camera feed...")
    print("=" * 60)
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            
            # Add frame counter overlay
            cv2.putText(
                frame,
                f"Frame: {frame_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            
            # Show frame
            cv2.imshow("Webcam Test - Traffic Violation Detection", frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n✅ Quit requested")
                break
            elif key == ord('s'):
                filename = f"screenshot_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Screenshot saved: {filename}")
    
    except KeyboardInterrupt:
        print("\n✅ Interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        print("\n" + "=" * 60)
        print("  Session Summary")
        print("=" * 60)
        print(f"  Total frames: {frame_count}")
        print("=" * 60)
        print("\n✅ Camera closed successfully")
    
    return 0


if __name__ == "__main__":
    # Allow camera index as command line argument
    camera_id = 0
    if len(sys.argv) > 1:
        try:
            camera_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid camera ID: {sys.argv[1]}")
            print("Usage: python test_webcam_simple.py [camera_id]")
            sys.exit(1)
    
    sys.exit(main())
