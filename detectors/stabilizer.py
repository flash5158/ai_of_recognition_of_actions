import numpy as np

class BoxStabilizer:
    """
    Stabilizes bounding boxes using Exponential Moving Average (EMA).
    Reduces jitter (shaking) and abrupt size changes.
    """
    def __init__(self, alpha=0.6):
        # Alpha: Smoothing factor.
        # 0.1 = Very smooth (slow reaction)
        # 0.9 = Very reactive (more jitter)
        # 0.6 is a good balance for human movement.
        self.alpha = alpha
        self.tracks = {} # {id: [x1, y1, x2, y2]}
        
    def update(self, track_id, box):
        """
        Update the box for a track_id.
        box: [x1, y1, x2, y2]
        Returns: Smoothed box [x1, y1, x2, y2] (integers)
        """
        if track_id not in self.tracks:
            self.tracks[track_id] = np.array(box, dtype=np.float32)
            return box
            
        current = np.array(box, dtype=np.float32)
        previous = self.tracks[track_id]
        
        # EMA Formula: New = alpha * Current + (1 - alpha) * Previous
        smoothed = self.alpha * current + (1 - self.alpha) * previous
        
        self.tracks[track_id] = smoothed
        
        return smoothed.astype(int).tolist()
    
    def remove(self, track_id):
        if track_id in self.tracks:
            del self.tracks[track_id]
