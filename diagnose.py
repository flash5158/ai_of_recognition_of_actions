import cv2
import sys

print(f"Python: {sys.version}")

try:
    import mediapipe as mp
    print("MediaPipe imported successfully")
    try:
        mp.solutions.pose.Pose()
        print("MediaPipe Pose initialized successfully")
    except Exception as e:
        print(f"MediaPipe Pose ERROR: {e}")
except ImportError as e:
    print(f"MediaPipe Import ERROR: {e}")

print("Testing Camera...")
for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            print(f"Camera {i}: WORKING ({frame.shape})")
        else:
            print(f"Camera {i}: OPENED BUT NO FRAME")
        cap.release()
    else:
        print(f"Camera {i}: NOT DETECTED")
