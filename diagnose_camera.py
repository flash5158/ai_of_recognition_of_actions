import cv2
import sys
import platform

def diagnose_cameras():
    print("="*60)
    print("PANOPTES CAMERA DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"OpenCV: {cv2.__version__}")
    print("-" * 60)

    working_indices = []
    
    # Try indices 0 to 5
    for i in range(5):
        print(f"Testing Camera Index [{i}]...", end=" ")
        
        # On macOS, specific backends might be needed. 
        # CAP_AVFOUNDATION is standard for macOS.
        if platform.system() == 'Darwin':
            cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
        else:
            cap = cv2.VideoCapture(i)
            
        if not cap.isOpened():
            print("FAILED (Could not open)")
            continue
            
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            h, w = frame.shape[:2]
            print(f"SUCCESS! Resolution: {w}x{h}")
            working_indices.append(i)
        else:
            print("OPENED BUT NO FRAME (Possible Permission Issue)")
            
        cap.release()

    print("-" * 60)
    if working_indices:
        print(f"✅ WORKING CAMERAS FOUND AT INDICES: {working_indices}")
        print("Update your configuration to use one of these indices.")
    else:
        print("❌ NO WORKING CAMERAS FOUND.")
        print("Troubleshooting steps:")
        if platform.system() == 'Darwin':
            print("1. macOS Privacy: Go to System Settings > Privacy & Security > Camera.")
            print("2. Ensure Terminal / VSCode / Python has access enabled.")
            print("3. Restart your terminal/IDE after granting permissions.")
    print("="*60)

if __name__ == "__main__":
    diagnose_cameras()
