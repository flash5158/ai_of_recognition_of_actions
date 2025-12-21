import sys
import time
print("Step 1: Imports start...")
try:
    import cv2
    print("Step 1: cv2 imported")
    import numpy as np
    print("Step 1: numpy imported")
    from ultralytics import YOLO
    print("Step 1: ultralytics imported")
    import mediapipe as mp
    print("Step 1: mediapipe imported")
    from pymilvus import connections
    print("Step 1: milvus imported")
except Exception as e:
    print(f"Step 1 ERROR: {e}")
    sys.exit(1)

print("Step 2: Model Loading...")
try:
    print("Loading YOLO...")
    model = YOLO("yolo11n.pt")
    print("YOLO Loaded")
    
    print("Loading Pose...")
    pose_model = YOLO("yolo11n-pose.pt")
    print("Pose Loaded")
except Exception as e:
    print(f"Step 2 ERROR: {e}")
    sys.exit(1)

print("Step 3: MediaPipe...")
try:
    mp_face = mp.solutions.face_mesh
    print("MediaPipe Solutions Access OK")
except Exception as e:
    print(f"Step 3 ERROR: {e}")
    sys.exit(1)

print("DONE")
