import time
import threading
import torch
import logging
from ultralytics import YOLO
from core.shared_state import SharedState
from core.behavior import BehaviorEngine

class InferenceEngine:
    def __init__(self, model_path="yolo11n-pose.pt"):
        self.running = False
        self.shared = SharedState()
        self.behavior = BehaviorEngine()
        self.thread = None
        self.model_path = model_path
        self.model = None
        
        # Hardware Acceleration Check
        if torch.backends.mps.is_available():
            self.device = "mps"
            print("[BRAIN] 🚀 MPS (Apple Metal) Acceleration ENABLED")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print("[BRAIN] 🚀 CUDA Acceleration ENABLED")
        else:
            self.device = "cpu"
            print("[BRAIN] ⚠️ Running on CPU")

    def load_model(self):
        try:
            # Verbose=False prevents log spam
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            # Warmup
            print("[BRAIN] Warming up model...")
            self.model.predict("https://ultralytics.com/images/bus.jpg", verbose=False, device=self.device)
            print("[BRAIN] Model Ready.")
        except Exception as e:
            print(f"[BRAIN] Model Load Failed: {e}")

    def start(self):
        if self.running: return
        self.load_model()
        self.running = True
        self.thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _inference_loop(self):
        last_processed_id = -1
        
        while self.running:
            # 1. Get Frame
            frame, frame_id = self.shared.get_frame_for_ai()
            
            # 2. Skip if no new frame
            if frame is None or frame_id == last_processed_id:
                time.sleep(0.01) # Poll interval
                continue
                
            last_processed_id = frame_id
            start_time = time.time()
            
            # 3. Resize for Speed (Standard 640 for YOLO)
            # Actually YOLO handles this, but manual resize avoids transfer overhead if frame is massive (4K)
            # Assuming webcam is 720p/1080p, let's let YOLO handle it or resize to 640x360 explicit?
            # Explicit resize often faster.
            # h, w = frame.shape[:2]
            # input_frame = cv2.resize(frame, (640, 640)) 
            
            try:
                # 4. Inference
                # device=self.device is critical
                # verbose=False
                results = self.model.track(
                    frame, 
                    persist=True, 
                    verbose=False, 
                    device=self.device, 
                    tracker="bytetrack.yaml",
                    conf=0.4
                )
                
                # 5. Parse Results
                detections = self._parse_results(results, frame.shape)
                
                # 6. Push Update
                fps = 1.0 / (time.time() - start_time + 0.0001)
                self.shared.update_detections(detections, fps)
                
            except Exception as e:
                print(f"[BRAIN] Inference Error: {e}")
                time.sleep(0.1)

    def _parse_results(self, results, shape):
        h, w = shape[:2]
        output = []
        
        if not results: return output
        
        r = results[0]
        if r.boxes is None or r.boxes.id is None:
            return output
            
        boxes = r.boxes.xyxyn.cpu().numpy() # Normalized 0-1
        ids = r.boxes.id.int().cpu().numpy()
        
        # Keypoints
        kpts = None
        if r.keypoints is not None:
             kpts = r.keypoints.xyn.cpu().numpy() # Normalized 0-1
             
        for i, (box, track_id) in enumerate(zip(boxes, ids)):
            kp = kpts[i] if kpts is not None else []
            t_id = int(track_id)
            
            # --- BEHAVIOR & SMOOTHING ---
            timestamp = time.time()
            # Normalize keypoints for behavior? Behavior expects raw or norm?
            # My behavior engine expects raw/norm consistent usage. 
            # ActionClassifier.classify uses logic like 'wrists < nose'. 
            # If norm 0-1 (y increases down), nose is e.g. 0.2, wrist 0.5.
            # My ActionClassifier logic: if l_wr[1] < nose[1] => Wrist ABOVE nose.
            # So normalize is fine.
            
            final_box, action = self.behavior.process(t_id, kp, box, timestamp)
            
            final_box = final_box.tolist()
            # Calculate Pixels for Frontend (640x360 default reference or actual scale?)
            # The frontend likely expects pixels relative to the video frame or a specific size.
            # We have h, w from parse_results(results, frame.shape)
            x1 = int(final_box[0] * w)
            y1 = int(final_box[1] * h)
            x2 = int(final_box[2] * w)
            y2 = int(final_box[3] * h)
            
            output.append({
                "id": t_id,
                "box_norm": final_box, 
                "box": [x1, y1, x2, y2], # RESTORED for Frontend
                "keypoints_norm": kp.tolist() if len(kp) > 0 else [],
                "action": action,
                "timestamp": timestamp
            })
            
        return output
