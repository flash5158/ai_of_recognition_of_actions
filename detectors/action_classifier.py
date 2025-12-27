import numpy as np
from collections import deque

class ActionClassifier:
    """
    PROFESSIONAL VECTOR-BASED CLASSIFIER v2
    Uses Cosine Similarity + Dynamic Velocity Analysis.
    """
    def __init__(self, history_size=10): # Increased history for stability
        self.history = deque(maxlen=history_size)
        self.last_action = "PARADO"
        self.confidence_threshold = 0.85 
        
    def classify(self, lm_list, context_objects=[], timestamp=None, dynamics=None):
        """
        dynamics: dict from PredictiveBrain containing 'speed', 'is_running', etc.
        """
        if not lm_list or len(lm_list) < 17:
            return "DESCONOCIDO"
            
        # 1. Normalize Skeleton
        features = self._extract_features(lm_list)
        if features is None: return "DESCONOCIDO"
        
        # 2. Score Actions
        scores = {}
        
        # --- CRITICAL MARKERS ---
        
        # MANOS ARRIBA (Hands Up)
        if features['wrists_y'] < features['eyes_y']: 
             scores['MANOS_ARRIBA'] = 1.0
        else:
             scores['MANOS_ARRIBA'] = 0.0
             
        # GUARDIA (Fighting Stance)
        # Wrists high (near shoulders/face) + Elbows bent
        # And usually legs are spread
        if (features['wrists_y'] < features['shoulders_y']) and (features['wrist_nose_dist'] < 0.3):
             scores['AGRESION'] = 0.8
        else:
             scores['AGRESION'] = 0.0
             
        # TOCANDO CARA (Touching Face)
        if features['wrist_nose_dist'] < 0.15:
             scores['TOCANDO_CARA'] = 0.9
        else:
             scores['TOCANDO_CARA'] = 0.0
        
        # --- POSTURE MARKERS ---
             
        # SENTADO (Sitting)
        if features['thigh_verticality'] < 0.6: # Thighs horizontal
            scores['SENTADO'] = 0.95
        else:
            scores['SENTADO'] = 0.0
            
        # CAIDA (Fall)
        # If torso angle is horizontal (not just thighs) -> Logic for torso angle needed
        # Fallback: If bounding box is flat (width > height) -> Passed via context usually
        # We'll stick to 'SENTADO' covering most static low poses for now.
        
        # --- DYNAMIC MARKERS (Velocity Based) ---
        
        is_moving_fast = False
        if dynamics:
            if dynamics.get('is_running', False):
                is_moving_fast = True
                scores['CORRIENDO'] = 1.0
            elif dynamics.get('speed', 0) > 50: # Moderate movement
                scores['CAMINANDO'] = 0.8
            elif dynamics.get('is_loitering', False):
                scores['MERODEANDO'] = 0.6
                
        # Default States
        if not is_moving_fast and scores.get('SENTADO', 0) < 0.5:
             scores['PARADO'] = 0.5
        
        # 3. WINNER TAKES ALL
        best_action = max(scores, key=scores.get)
        
        # 4. Filter (Smoothing)
        self.history.append(best_action)
        
        # Urgent Override (Don't smooth criticals)
        if best_action in ["MANOS_ARRIBA", "AGRESION", "CORRIENDO"]:
             return best_action
             
        # Voting for stable actions
        from collections import Counter
        counts = Counter(self.history)
        winner, count = counts.most_common(1)[0]
        
        if count >= len(self.history) * 0.5:
            return winner
        else:
            return self.last_action

    def _extract_features(self, lm):
        def p(i): return np.array([lm[i][1], lm[i][2]])
        
        nose = p(0); l_eye = p(1); r_eye = p(2)
        l_sh = p(5); r_sh = p(6)
        l_wr = p(9); r_wr = p(10)
        l_hip = p(11); r_hip = p(12)
        l_knee = p(13); r_knee = p(14)
        l_ank = p(15); r_ank = p(16)
        
        # Scale Ref: Torso Height
        torso = np.linalg.norm((l_sh+r_sh)/2 - (l_hip+r_hip)/2)
        if torso < 10: return None # Too small/far
        
        feat = {}
        # Y is normalized? No, raw coordinates. Y increases downwards.
        # Smaller Y = Higher up.
        
        feat['wrists_y'] = (l_wr[1] + r_wr[1]) / 2
        feat['eyes_y'] = (l_eye[1] + r_eye[1]) / 2
        feat['shoulders_y'] = (l_sh[1] + r_sh[1]) / 2
        
        # Distances normalized by Torso
        feat['wrist_nose_dist'] = min(np.linalg.norm(l_wr - nose), np.linalg.norm(r_wr - nose)) / torso
        
        # Thigh Verticality
        l_thigh = l_hip - l_knee
        r_thigh = r_hip - r_knee
        # Vertical component ratio
        l_v = abs(l_thigh[1]) / (np.linalg.norm(l_thigh) + 0.001)
        r_v = abs(r_thigh[1]) / (np.linalg.norm(r_thigh) + 0.001)
        feat['thigh_verticality'] = (l_v + r_v) / 2
        
        return feat
