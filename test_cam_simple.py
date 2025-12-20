
import cv2
import time
import os

def test_camera():
    print("DIAGNOSTIC: Attempting to open camera (index 0)...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("FAIL: Could not open video device 0.")
        return False
    
    print("SUCCESS: Camera opened. Reading warm-up frames...")
    
    # Read a few frames to let auto-exposure settle
    for i in range(15):
        ret, frame = cap.read()
        if not ret:
            print(f"WARN: Frame {i} failed to read.")
        else:
            time.sleep(0.1)
            
    # Capture validation frame
    ret, frame = cap.read()
    cap.release()
    
    if ret and frame is not None and frame.size > 0:
        filename = f"cam_test_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)
        print(f"SUCCESS: Frame captured and saved to {filename}")
        print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
        return True
    else:
        print("FAIL: Camera opened but returned invalid/empty frame.")
        return False

if __name__ == "__main__":
    test_camera()
