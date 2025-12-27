import numpy as np
import time
from collections import deque, Counter

class RollingAverage:
    def __init__(self, window_size=5):
        self.window = deque(maxlen=window_size)
    
    def update(self, value):
        self.window.append(value)
        return np.mean(self.window, axis=0)

class StateDecay:
    def __init__(self, decay_seconds=0.5):
        self.decay = decay_seconds
        self.last_seen = 0.0
        self.current_state = "NEUTRAL"
        
    def update(self, proposed_state, timestamp):
        # Immediate transition to High Priority states
        if proposed_state in ["MANOS_ARRIBA", "AGRESION", "GOLPE"]:
             self.current_state = proposed_state
             self.last_seen = timestamp
             return proposed_state
             
        # Decay Check
        if (timestamp - self.last_seen) < self.decay:
            # Keep holding the high priority state
            if self.current_state != "NEUTRAL":
                 return self.current_state
        
        # Otherwise accept proposed (likely NEUTRAL or common state)
        self.current_state = proposed_state
        self.last_seen = timestamp
        return proposed_state

class BehaviorEngine:
    def __init__(self):
        self.track_data = {} # {id: {'params'...}}
        
    def process(self, detection_id, keypoints, box, timestamp):
        """
        Main entry point for behavior logic per person.
        Returns: (smoothed_box, action_label)
        """
        # Init Track State
        if detection_id not in self.track_data:
            self.track_data[detection_id] = {
                "box_avg": RollingAverage(window_size=5),
                "kpts_avg": RollingAverage(window_size=5),
                "decay": StateDecay(decay_seconds=0.5),
                "classifier": ActionClassifier()
            }
            
        t = self.track_data[detection_id]
        
        # 1. Smooth Data
        smooth_box = t["box_avg"].update(np.array(box))
        smooth_kpts = None
        if len(keypoints) > 0:
            smooth_kpts = t["kpts_avg"].update(np.array(keypoints))
            
        # 2. Classify
        raw_action = "NEUTRAL"
        if smooth_kpts is not None:
            raw_action = t["classifier"].classify(smooth_kpts)
            
        # 3. Apply State Decay (Anti-Freeze)
        final_action = t["decay"].update(raw_action, timestamp)
        
        return smooth_box, final_action

class ActionClassifier:
    def classify(self, lm):
        # lm is (17, 2) or (17, 3) normalized
        if len(lm) < 17: return "NEUTRAL"
        
        # Helpers
        def p(i): return np.array([lm[i][0], lm[i][1]]) # X, Y
        
        nose = p(0)
        l_wr = p(9); r_wr = p(10)
        l_sh = p(5); r_sh = p(6)
        
        # 1. Manos Arriba (Wrists above nose)
        # Note: Y increases downwards in screen coords. So Above means Y < Noise_Y
        if (l_wr[1] < nose[1]) and (r_wr[1] < nose[1]):
            return "MANOS_ARRIBA"
            
        # 2. Agresion (Fighting Stance) - Wrists near shoulders/face
        # Distance check
        torso_scale = np.linalg.norm(l_sh - r_sh) * 2 # Approximate torso height ref
        if torso_scale == 0: torso_scale = 1.0
        
        d_l = np.linalg.norm(l_wr - nose)
        d_r = np.linalg.norm(r_wr - nose)
        
        if (d_l < 0.3 * torso_scale) or (d_r < 0.3 * torso_scale):
             # Also check they are NOT down at hips (handled by distance to nose)
             return "AGRESION"
             
        return "NEUTRAL"
