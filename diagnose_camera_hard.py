import cv2
import time
import os

print("--- HARDWARE DIAGNOSTIC ---")
found_cam = False

for idx in [0, 1, 2, 3]:
    print(f"Testing Camera Index [{idx}]...")
    try:
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            print(f"❌ Index {idx}: Failed to open.")
            continue
        
        # Try to read multiple frames to let auto-exposure settle
        print(f"   Opening successful. Reading frames...")
        success = False
        for i in range(10):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"✅ Index {idx}: Frame captured! ({frame.shape})")
                
                # Save snapshot
                filename = f"snapshot_cam_{idx}.jpg"
                cv2.imwrite(filename, frame)
                print(f"   Saved {filename}")
                success = True
                found_cam = True
                break
            time.sleep(0.1)
        
        if not success:
             print(f"❌ Index {idx}: Opened but returned empty frames.")
             
        cap.release()
    except Exception as e:
        print(f"❌ Index {idx}: Exception {e}")

if not found_cam:
    print("\nXXX CRITICAL: NO WORKING CAMERA FOUND XXX")
    print("Possibilities:")
    print("1. macOS Permission denied for Terminal/VSCode.")
    print("2. Camera is used by another app.")
    print("3. Hardware failure.")
else:
    print("\n>>> CAMERA HARDWARE OK. Proceeding to fix software.")
