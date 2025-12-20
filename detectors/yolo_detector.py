import cv2
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path="yolo11n.pt"):
        """
        Initialize the YOLO detector.
        Uses the nano model by default for speed.
        """
        self.model = YOLO(model_path)
    
    def detect(self, frame):
        """
        Detect objects in a frame.
        Returns a list of detections using the Ultralytics results object.
        """
        # Run inference with defensive handling — return an empty-like result on failure
        try:
            results = self.model(frame, verbose=False)
            return results[0]  # Return the first result (single frame)
        except Exception:
            class _EmptyResult:
                def __init__(self):
                    self.boxes = []

            return _EmptyResult()
