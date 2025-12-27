import threading
import time
import numpy as np

class SharedState:
    """
    Thread-safe Singleton for sharing state between:
    1. Vision Thread (Writes High-FPS Video Frames)
    2. Brain Thread (Reads Frames, Writes Detections)
    3. Main/Server Thread (Reads both for Visualization)
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SharedState, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        
        self.lock = threading.Lock()
        
        # VIDEO STATE
        self.latest_frame = None
        self.frame_id = 0 # Monotonic counter to detect new frames
        self.frame_timestamp = 0.0
        
        # AI STATE
        self.latest_detections = [] # List of dicts
        self.ai_timestamp = 0.0
        self.inference_fps = 0.0
        
        # SYSTEM STATE
        self.cam_active = False
        self.system_status = "INITIALIZING"
        
        self._initialized = True

    def update_frame(self, frame):
        """Called by Vision Thread (60 FPS)"""
        with self.lock:
            self.latest_frame = frame
            self.frame_id += 1
            self.frame_timestamp = time.time()
            self.cam_active = True

    def get_frame_for_ai(self):
        """Called by Brain Thread"""
        with self.lock:
            if self.latest_frame is None: return None, -1
            # Return copy to avoid race conditions during resize/processing?
            # Actually, read-only access is fine if we don't modify it.
            # But let's copy to be safe if AI modifies it.
            return self.latest_frame.copy(), self.frame_id

    def update_detections(self, detections, fps):
        """Called by Brain Thread"""
        with self.lock:
            self.latest_detections = detections
            self.ai_timestamp = time.time()
            self.inference_fps = fps

    def get_snapshot(self):
        """Called by Visualizer/Server (UI Thread)"""
        with self.lock:
            if self.latest_frame is None: return None
            return {
                "frame": self.latest_frame.copy(), # Costly? optimization possible
                "detections": self.latest_detections, # Reference copy
                "fps": self.inference_fps,
                "status": self.system_status,
                "cam_active": self.cam_active
            }
