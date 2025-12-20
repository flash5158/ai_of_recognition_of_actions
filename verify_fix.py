import sys
import os

print(f"Python: {sys.version}")

try:
    from detectors.pose_estimator import PoseEstimator
    print("Imported PoseEstimator class")
    
    pe = PoseEstimator()
    if pe.pose_model:
        print("SUCCESS: PoseEstimator initialized with YOLOv11-Pose.")
    else:
        print("FAILURE: PoseEstimator failed to load YOLO model.")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
