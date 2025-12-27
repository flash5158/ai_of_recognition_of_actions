import cv2
import time
import threading
import logging
from core.shared_state import SharedState

class VisionThread:
    def __init__(self, source=0):
        self.source = source
        self.running = False
        self.cap = None
        self.shared = SharedState()
        self.thread = None
        self.lock = threading.Lock()
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logging.getLogger("panoptes.vision").info(f"VisionThread started on source {self.source}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self._release_camera()

    def _release_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def _init_camera(self):
        try:
            logging.getLogger("panoptes.vision").info(f"Connecting to camera {self.source}...")
            cap = cv2.VideoCapture(self.source)
            if not cap.isOpened():
                return None
            
            # Request High FPS
            cap.set(cv2.CAP_PROP_FPS, 60) 
            # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return cap
        except Exception as e:
            print(f"[VISION] Error init camera: {e}")
            return None

    def _capture_loop(self):
        while self.running:
            # 1. Check Camera
            if self.cap is None or not self.cap.isOpened():
                self.cap = self._init_camera()
                if self.cap is None:
                    time.sleep(2.0) # Retry delay
                    continue
            
            # 2. Capture
            ret, frame = self.cap.read()
            if not ret:
                print("[VISION] Frame drop / Camera disconnect")
                self._release_camera()
                time.sleep(1.0)
                continue
            
            # 3. Push to Shared State (Fast)
            self.shared.update_frame(frame)
            
            # 4. Yield slightly to prevent CPU hogging (1ms), relying on blocking read() usually
            # But read() blocks until frame arrives, so we don't need sleep if camera is sync.
            # However, for safety in tight loops:
            # time.sleep(0.001) 
