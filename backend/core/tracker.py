#!/usr/bin/env python3
"""
Multi-Object Vehicle Tracker
Wraps DeepSort for real-time vehicle tracking and velocity estimation
"""

import numpy as np
from typing import List, Tuple, NamedTuple, Optional, Dict
from collections import defaultdict, deque
from pathlib import Path

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    DEEPSORT_AVAILABLE = True
except ImportError:
    try:
        from deep_sort_realtime.deep_sort import DeepSort
        DEEPSORT_AVAILABLE = True
    except ImportError:
        DEEPSORT_AVAILABLE = False
        raise ImportError(
            "deep-sort-realtime is required. Install with: pip install deep-sort-realtime"
        )


# ==============================================
# CONSTANTS & CLASS DEFINITIONS
# ==============================================

class TrackedObject(NamedTuple):
    """Single tracked object"""
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    x1: int                # Pixel coordinates
    y1: int
    x2: int
    y2: int
    center_x: int         # Centroid
    center_y: int
    is_confirmed: bool    # Track confirmed?
    age: int              # Frames since detection


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def compute_centroid(x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int]:
    """
    Compute bounding box centroid
    
    Args:
        x1, y1: Top-left corner
        x2, y2: Bottom-right corner
    
    Returns:
        (center_x, center_y)
    """
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return cx, cy


def compute_iou(box1: Tuple[int, int, int, int], 
                box2: Tuple[int, int, int, int]) -> float:
    """
    Compute Intersection over Union (IoU) between two boxes
    
    Args:
        box1, box2: (x1, y1, x2, y2) format
    
    Returns:
        IoU value (0-1)
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    # Intersection
    xi_min = max(x1_min, x2_min)
    yi_min = max(y1_min, y2_min)
    xi_max = min(x1_max, x2_max)
    yi_max = min(y1_max, y2_max)
    
    inter_area = max(0, xi_max - xi_min) * max(0, yi_max - yi_min)
    
    # Union
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area


# ==============================================
# VEHICLE TRACKER CLASS
# ==============================================

class VehicleTracker:
    """
    Multi-object vehicle tracker using DeepSort
    Tracks vehicles across frames and estimates motion
    """
    
    def __init__(
        self,
        max_age: int = 30,
        n_init: int = 3,
        model_name: str = "osnet_x0_25_msmt17",
    ):
        """
        Initialize vehicle tracker
        
        Args:
            max_age: Frames to keep track without detection
            n_init: Frames needed before track is confirmed
            model_name: Deep learning model for feature extraction
        """
        if not DEEPSORT_AVAILABLE:
            raise RuntimeError("deep-sort-realtime is not installed")
        
        self.max_age = max_age
        self.n_init = n_init
        
        # Initialize DeepSort tracker
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            nms_max_overlap=0.5,
            model_name=model_name,
            embedder_gpu=False,  # Use CPU for embedder
        )
        
        # Track centroid history for speed/direction estimation
        self.track_history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=30)  # Keep last 30 centroids
        )
        
        # Track metadata
        self.track_metadata: Dict[int, dict] = {}
        
        # Statistics
        self.frame_count = 0
        self.active_tracks = set()
        
        print(f"✅ VehicleTracker initialized")
        print(f"   Max age: {max_age} frames")
        print(f"   N init: {n_init} frames")
        print(f"   Model: {model_name}")

    def update(
        self,
        detections: List,  # List of Detection namedtuples from detector
        frame: np.ndarray,
    ) -> List[TrackedObject]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of Detection namedtuples
            frame: Current frame (H, W, 3)
        
        Returns:
            List of TrackedObject with confirmed tracks
        """
        self.frame_count += 1
        
        # Convert detections to deep_sort format
        detections_ds = []
        detection_classes = {}
        
        for det in detections:
            # Compute width and height
            w = det.x2 - det.x1
            h = det.y2 - det.y1
            
            # DeepSort format: [x, y, w, h]
            bbox = [det.x1, det.y1, w, h]
            
            # Confidence score
            conf = det.confidence
            
            detections_ds.append((bbox, conf, det.class_id))
            detection_classes[len(detections_ds) - 1] = (
                det.class_id,
                det.class_name,
                det.confidence,
                det.x1,
                det.y1,
                det.x2,
                det.y2,
            )
        
        # Run tracker
        tracks = self.tracker.update_tracks(detections_ds, frame=frame)
        
        # Convert to TrackedObject format
        tracked_objects = []
        self.active_tracks.clear()
        
        for track in tracks:
            # Get bounding box
            bbox = track.bbox
            x1, y1, w, h = bbox
            x1, y1, w, h = int(x1), int(y1), int(w), int(h)
            x2, y2 = x1 + w, y1 + h
            
            # Get track ID
            track_id = track.track_id
            
            # Get detection info from matched detection
            class_id = 0
            class_name = "unknown"
            confidence = 0.0
            
            if track.det_conf is not None:
                # Extract from detection
                if hasattr(track, '_det_idx') and track._det_idx in detection_classes:
                    class_id, class_name, confidence, _, _, _, _ = \
                        detection_classes[track._det_idx]
            else:
                # Use stored metadata
                if track_id in self.track_metadata:
                    metadata = self.track_metadata[track_id]
                    class_id = metadata['class_id']
                    class_name = metadata['class_name']
                    confidence = metadata['confidence']
            
            # Compute centroid
            cx, cy = compute_centroid(x1, y1, x2, y2)
            
            # Update track history
            self.track_history[track_id].append((cx, cy))
            
            # Store metadata
            self.track_metadata[track_id] = {
                'class_id': class_id,
                'class_name': class_name,
                'confidence': confidence,
            }
            
            # Create tracked object
            tracked_obj = TrackedObject(
                track_id=track_id,
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                center_x=cx,
                center_y=cy,
                is_confirmed=track.is_confirmed(),
                age=track.time_since_update,
            )
            
            # Only return confirmed tracks
            if track.is_confirmed():
                tracked_objects.append(tracked_obj)
                self.active_tracks.add(track_id)
            
            # Clean up history for lost tracks
            if track.time_since_update > self.max_age:
                if track_id in self.track_history:
                    del self.track_history[track_id]
                if track_id in self.track_metadata:
                    del self.track_metadata[track_id]
        
        return tracked_objects

    def get_track_history(
        self,
        track_id: int,
        max_frames: int = 10,
    ) -> List[Tuple[int, int]]:
        """
        Get centroid history for a track
        
        Args:
            track_id: Track ID
            max_frames: Maximum frames to return
        
        Returns:
            List of (cx, cy) centroids, most recent last
        """
        if track_id not in self.track_history:
            return []
        
        history = list(self.track_history[track_id])
        
        if max_frames > 0:
            history = history[-max_frames:]
        
        return history

    def estimate_speed(
        self,
        track_id: int,
        fps: float = 30.0,
        pixels_per_meter: float = 50.0,
    ) -> Optional[float]:
        """
        Estimate vehicle speed from track history
        
        Args:
            track_id: Track ID
            fps: Frames per second
            pixels_per_meter: Camera calibration (pixels per meter in real world)
        
        Returns:
            Speed in km/h, or None if insufficient history
        """
        history = self.get_track_history(track_id, max_frames=10)
        
        if len(history) < 2:
            return None
        
        # Calculate total displacement
        x1, y1 = history[0]
        x2, y2 = history[-1]
        
        pixel_distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        real_distance = pixel_distance / pixels_per_meter  # meters
        
        # Time elapsed
        time_frames = len(history) - 1
        time_seconds = time_frames / fps
        
        if time_seconds == 0:
            return None
        
        # Speed in m/s
        speed_ms = real_distance / time_seconds
        
        # Convert to km/h
        speed_kmh = speed_ms * 3.6
        
        return speed_kmh

    def get_direction_vector(
        self,
        track_id: int,
        normalize: bool = True,
    ) -> Optional[Tuple[float, float]]:
        """
        Get direction vector from track history
        
        Args:
            track_id: Track ID
            normalize: Whether to normalize the vector
        
        Returns:
            (dx, dy) direction vector, or None if insufficient history
        """
        history = self.get_track_history(track_id, max_frames=10)
        
        if len(history) < 2:
            return None
        
        # Get start and end positions
        x1, y1 = history[0]
        x2, y2 = history[-1]
        
        dx = x2 - x1
        dy = y2 - y1
        
        if normalize:
            magnitude = np.sqrt(dx ** 2 + dy ** 2)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
        
        return (dx, dy)

    def get_track_velocity(
        self,
        track_id: int,
        fps: float = 30.0,
    ) -> Optional[Tuple[float, float]]:
        """
        Get velocity vector (pixels per frame)
        
        Args:
            track_id: Track ID
            fps: Frames per second
        
        Returns:
            (vx, vy) velocity in pixels/frame
        """
        history = self.get_track_history(track_id, max_frames=5)
        
        if len(history) < 2:
            return None
        
        x1, y1 = history[0]
        x2, y2 = history[-1]
        
        frames = len(history) - 1
        
        vx = (x2 - x1) / frames if frames > 0 else 0
        vy = (y2 - y1) / frames if frames > 0 else 0
        
        return (vx, vy)

    def predict_position(
        self,
        track_id: int,
        frames_ahead: int = 5,
    ) -> Optional[Tuple[int, int]]:
        """
        Predict future position of a track
        
        Args:
            track_id: Track ID
            frames_ahead: Number of frames to predict
        
        Returns:
            Predicted (x, y) position
        """
        velocity = self.get_track_velocity(track_id)
        if velocity is None:
            return None
        
        history = self.get_track_history(track_id, max_frames=1)
        if not history:
            return None
        
        x, y = history[-1]
        vx, vy = velocity
        
        pred_x = int(x + vx * frames_ahead)
        pred_y = int(y + vy * frames_ahead)
        
        return (pred_x, pred_y)

    def is_moving(
        self,
        track_id: int,
        min_velocity: float = 1.0,
    ) -> bool:
        """
        Check if track is moving (not stationary)
        
        Args:
            track_id: Track ID
            min_velocity: Minimum velocity threshold (pixels/frame)
        
        Returns:
            True if moving, False if stationary
        """
        velocity = self.get_track_velocity(track_id)
        if velocity is None:
            return False
        
        vx, vy = velocity
        speed = np.sqrt(vx ** 2 + vy ** 2)
        
        return speed >= min_velocity

    def calculate_motion_angle(
        self,
        track_id: int,
    ) -> Optional[float]:
        """
        Calculate motion direction in degrees (0-360)
        0° = right, 90° = down, 180° = left, 270° = up
        
        Args:
            track_id: Track ID
        
        Returns:
            Angle in degrees, or None if no motion
        """
        direction = self.get_direction_vector(track_id, normalize=False)
        if direction is None:
            return None
        
        dx, dy = direction
        angle = np.arctan2(dy, dx) * 180 / np.pi
        
        # Convert to 0-360 range
        if angle < 0:
            angle += 360
        
        return angle

    def get_stats(self) -> dict:
        """Get tracker statistics"""
        return {
            "frame_count": self.frame_count,
            "active_tracks": len(self.active_tracks),
            "max_age": self.max_age,
            "n_init": self.n_init,
        }

    def print_stats(self):
        """Pretty-print tracker statistics"""
        stats = self.get_stats()
        
        print("""
╔════════════════════════════════════════════════════╗
║          TRACKER STATISTICS                        ║
╚════════════════════════════════════════════════════╝
""")
        print(f"Frame Count:           {stats['frame_count']}")
        print(f"Active Tracks:         {stats['active_tracks']}")
        print(f"Max Age:               {stats['max_age']} frames")
        print(f"N Init:                {stats['n_init']} frames")
        print("""
════════════════════════════════════════════════════╗
        """)


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def print_tracked_objects(tracked_objects: List[TrackedObject]):
    """Pretty-print tracked objects"""
    if not tracked_objects:
        print("No tracked objects")
        return
    
    print(f"\n📍 Tracked Objects ({len(tracked_objects)}):")
    for obj in tracked_objects:
        status = "✅" if obj.is_confirmed else "⏳"
        print(
            f"  {status} ID={obj.track_id:3d} {obj.class_name:20} "
            f"conf={obj.confidence:.2f} pos=({obj.center_x},{obj.center_y}) "
            f"age={obj.age}"
        )


# ==============================================
# MAIN / TESTING
# ==============================================

if __name__ == "__main__":
    print("Testing VehicleTracker module...\n")
    
    # Initialize tracker
    tracker = VehicleTracker(max_age=30, n_init=3)
    tracker.print_stats()
    
    # Mock detection
    from backend.core import Detection
    
    mock_detections = [
        Detection(
            class_id=6, class_name="motorcycle", confidence=0.95,
            x1=100, y1=100, x2=200, y2=250,
            center_x=150, center_y=175,
            width=100, height=150, is_danger=False,
        ),
    ]
    
    # Simulate tracking over frames
    print("\nSimulating tracking over 10 frames...\n")
    
    for frame_idx in range(10):
        # Create dummy frame
        dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
        
        # Simulate motion (moving right)
        detections = []
        for det in mock_detections:
            offset = frame_idx * 5
            new_det = Detection(
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
                x1=det.x1 + offset,
                y1=det.y1,
                x2=det.x2 + offset,
                y2=det.y2,
                center_x=det.center_x + offset,
                center_y=det.center_y,
                width=det.width,
                height=det.height,
                is_danger=det.is_danger,
            )
            detections.append(new_det)
        
        # Update tracker
        tracked = tracker.update(detections, dummy_frame)
        
        if frame_idx % 3 == 0:
            print(f"Frame {frame_idx}:")
            print_tracked_objects(tracked)
        
        # Get stats for first track
        if tracked:
            track_id = tracked[0].track_id
            speed = tracker.estimate_speed(track_id, fps=30)
            direction = tracker.get_direction_vector(track_id)
            history = tracker.get_track_history(track_id)
            
            if frame_idx == 9:
                print(f"\nTrack {track_id} analytics:")
                print(f"  Speed: {speed:.2f} km/h" if speed else "  Speed: N/A")
                print(f"  Direction: {direction}" if direction else "  Direction: N/A")
                print(f"  History length: {len(history)}")
                print(f"  Last position: {history[-1] if history else 'N/A'}")
    
    print("\n✅ Tracker test complete!")
