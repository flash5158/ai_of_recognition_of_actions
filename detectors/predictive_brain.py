import numpy as np
from collections import deque
import time

class PredictiveBrain:
    """
    Advanced State Tracker for a single unique ID.
    Handles:
    - Velocity Calculation (Speed + Direction)
    - Trajectory Smoothing
    - Intent Prediction (e.g. "Running", "Loitering", "Aggressive Approach")
    - Anomaly Detection (Sudden stops, rapid acceleration)
    """
    def __init__(self, track_id, max_history=30):
        self.id = track_id
        self.max_history = max_history
        
        # History buffers (Time, X_center, Y_center)
        self.history = deque(maxlen=max_history) 
        self.velocities = deque(maxlen=max_history)
        
        # State
        self.is_running = False
        self.is_loitering = False
        self.first_seen = time.time()
        self.last_seen = time.time()
        
        # Config
        self.run_threshold = 15.0 # Pixels per frame (approx, depends on scale)
        self.loiter_radius = 50.0 # Pixels
        self.loiter_time_threshold = 5.0 # Seconds
        
    def update(self, box, timestamp=None):
        """
        Update state with new bounding box [x1, y1, x2, y2].
        """
        if timestamp is None:
            timestamp = time.time()
            
        self.last_seen = timestamp
            
        # 1. Calculate Center
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        
        # 2. Calculate Velocity
        vx, vy = 0, 0
        speed = 0
        
        if len(self.history) > 0:
            last_t, last_x, last_y = self.history[-1]
            dt = timestamp - last_t
            
            if dt > 0:
                # Pixels per second would be better, but per frame is stable for now if FPS is constant.
                # Let's use raw difference for simplicity in short bursts, or dt normalized.
                # To be robust against FPS jitter, we use dt.
                vx = (cx - last_x) / dt
                vy = (cy - last_y) / dt
                speed = np.sqrt(vx**2 + vy**2)
        
        self.history.append((timestamp, cx, cy))
        self.velocities.append(speed)
        
        # 3. Analyze Patterns
        self._analyze_intent(speed)
        
        return {
            "speed": speed,
            "vx": vx,
            "vy": vy,
            "is_running": self.is_running,
            "is_loitering": self.is_loitering
        }
        
    def _analyze_intent(self, current_speed):
        # --- RUNNING DETECTION ---
        # Simple threshold on current speed or smoothed speed
        # Normalize speed: 640 width -> speed 100 is fast.
        # If input is 640x360.
        
        avg_speed = np.mean(self.velocities) if self.velocities else 0
        
        # Heuristic: Running if speed > threshold
        # We need to calibrate this. Let's assume 300px/sec is "fast" in 640px width.
        # Adjusted for 640px width: 150px/sec is brisk walk, 300+ is run.
        if avg_speed > 200: 
            self.is_running = True
        else:
            self.is_running = False
            
        # --- LOITERING DETECTION ---
        # Check variance of position over last N seconds
        if time.time() - self.first_seen > self.loiter_time_threshold:
            # Get points in last X seconds
            recent_points = [p for p in self.history if p[0] > (time.time() - self.loiter_time_threshold)]
            if len(recent_points) > 10:
                xs = [p[1] for p in recent_points]
                ys = [p[2] for p in recent_points]
                
                # Check spatial spread
                spread = np.sqrt(np.var(xs) + np.var(ys)) # Std dev magnitude roughly
                
                if spread < self.loiter_radius: # Stayed within small area
                    self.is_loitering = True
                else:
                    self.is_loitering = False
