import cv2
import time

print("🔍 Testing Camera Access...")
try:
    # Try index 0 and 1
    for idx in [0, 1]:
        print(f"Attempting to open camera {idx}...")
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            print(f"✅ Camera {idx} IS ACCESSIBLE.")
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame captured: {frame.shape}")
            else:
                print("❌ Camera opened but returned NO frame.")
            cap.release()
        else:
            print(f"❌ Camera {idx} failed to open.")
except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
