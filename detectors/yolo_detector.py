import cv2
from ultralytics import YOLO
import numpy as np

class YOLODetector:
    def __init__(self, model_path="yolo11n.pt", device=None):
        """
        Initialize the YOLO detector.
        Uses the nano model by default for speed.
        """
        self.model = YOLO(model_path)
        
        if device:
            try:
                self.model.to(device)
                print(f"[YOLO] Testing device {device}...")
                # Test inference
                dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
                self.model(dummy_frame, verbose=False)
                print(f"[YOLO] Device {device} verified successfully.")
            except Exception as e:
                print(f"[YOLO] ⚠️ Failed on {device}: {e}")
                print("[YOLO] Falling back to CPU.")
                self.model.to("cpu")
    
    def detect(self, frame):
        """
        Detect objects in a frame.
        Returns a list of detections using the Ultralytics results object.
        """
        # Run inference with defensive handling — return an empty-like result on failure
        try:
            results = self.model(frame, verbose=False)
            return results[0]  # Return the first result (single frame)
        except Exception as e:
            print(f"[YOLO] Inference Error: {e}")
            class _EmptyResult:
                def __init__(self):
                    self.boxes = []

            return _EmptyResult()
