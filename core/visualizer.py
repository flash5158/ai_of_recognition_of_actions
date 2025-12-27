import cv2
import numpy as np

class Visualizer:
    def __init__(self):
        self.colors = {
            "NEUTRAL": (0, 255, 255), # Cyan
            "MANOS_ARRIBA": (0, 0, 255), # Red
            "AGRESION": (0, 0, 255), # Red
            "GOLPE": (0, 0, 255), # Red
            "TEXT_BG": (0, 0, 0),
            "TEXT": (255, 255, 255),
            "SKELETON": (255, 0, 255) # Magenta
        }
        
    def draw_scene(self, frame, detections):
        """
        Main render function.
        frame: BGR uint8 numpy array (writable)
        detections: list of dicts from BehaviorEngine/Inference
        """
        h, w = frame.shape[:2]
        
        for det in detections:
            action = det.get('action', 'NEUTRAL')
            color = self.colors.get(action, self.colors["NEUTRAL"])
            
            # 1. Unpack & Scale Box
            box_norm = det.get('box_norm', [0,0,0,0])
            x1 = int(box_norm[0] * w)
            y1 = int(box_norm[1] * h)
            x2 = int(box_norm[2] * w)
            y2 = int(box_norm[3] * h)
            
            # Clamp
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            # 2. Draw Corners
            self._draw_corners(frame, (x1, y1, x2, y2), color)
            
            # 3. Draw Skeleton
            kpts_norm = det.get('keypoints_norm', []) # List of [x, y] or [x, y, conf]
            if len(kpts_norm) > 0:
                self._draw_skeleton(frame, kpts_norm, w, h)
                
            # 4. Draw HUD Label
            label = f"ID:{det.get('id', '?')} | {action}"
            self._draw_hud_label(frame, (x1, y1), label, color)
            
    def _draw_corners(self, img, box, color, length=20, thickness=2):
        x1, y1, x2, y2 = box
        # Top-Left
        cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
        cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)
        # Top-Right
        cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
        cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)
        # Bottom-Left
        cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
        cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)
        # Bottom-Right
        cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
        cv2.line(img, (x2, y2), (x2, y2 - length), color, thickness)

    def _draw_skeleton(self, img, kpts, w, h):
        # Kpts is list of [x, y] normalized
        # Standard COCO Skeleton Connectivity
        # 5-7 (L Arm), 7-9 (L Forearm)
        # 6-8 (R Arm), 8-10 (R Forearm)
        # 5-6 (Shoulders)
        # 11-12 (Hips)
        # 5-11 (L Side), 6-12 (R Side)
        # 11-13 (L Thigh), 13-15 (L Calf)
        # 12-14 (R Thigh), 14-16 (R Calf)
        
        connections = [
            (5,7), (7,9), (6,8), (8,10),
            (5,6), (11,12), (5,11), (6,12),
            (11,13), (13,15), (12,14), (14,16)
        ]
        
        # Convert to pixels
        px_pts = {}
        for i, pt in enumerate(kpts):
            if len(pt) >= 2 and pt[0] > 0 and pt[1] > 0: # Valid?
                px_pts[i] = (int(pt[0] * w), int(pt[1] * h))
                
        # Draw Lines
        for i, j in connections:
            if i in px_pts and j in px_pts:
                cv2.line(img, px_pts[i], px_pts[j], self.colors["SKELETON"], 2)
                
        # Draw Joints
        for i, pt in px_pts.items():
            if i > 4: # Skip face (0-4)
                cv2.circle(img, pt, 3, (255, 255, 255), -1)

    def _draw_hud_label(self, img, pos, text, color):
        x, y = pos
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.6
        thick = 2
        (fw, fh), _ = cv2.getTextSize(text, font, scale, thick)
        
        # BG
        cv2.rectangle(img, (x, y - fh - 10), (x + fw + 10, y), (0,0,0), -1)
        # Text
        cv2.putText(img, text, (x + 5, y - 5), font, scale, color, thick)
