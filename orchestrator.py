import cv2
import time
import numpy as np
import threading
import os
import json
import logging
from detectors.yolo_detector import YOLODetector
from detectors.pose_estimator import PoseEstimator
from detectors.action_classifier import ActionClassifier
from detectors.embedding import EmbeddingExtractor
from detectors.emotion_detector import EmotionDetector
from database.vector_store import VectorDB
from database.ingest_worker import IngestWorker
import base64

class Orchestrator:
    def __init__(self, source=0):
        logging.getLogger("panoptes.orchestrator").info("Iniciando Motor CHALAS AI RECOGNITION v1.0 [BEHAVIORAL_ANALYSIS]...")
        self.source = source
        self.yolo = YOLODetector()
        self.pose = PoseEstimator()
        self.action_classifier = ActionClassifier()
        self.emotion_detector = EmotionDetector()
        self.embedding = EmbeddingExtractor(dim=128)
        self.db = VectorDB()
        # Start background ingest worker (offloads DB IO)
        try:
            self.ingest_worker = IngestWorker(self.db)
        except Exception:
            self.ingest_worker = None
        
        self.running = False
        self.cam_running = True # Force ON at startup
        self.latest_frame = None
        self.lock = threading.Lock()
        
        self.telemetry = {
            "fps": 0,
            "latency": 0,
            "anomalies": 0,
            "track_count": 0,
            "camera_status": "INICIANDO_SISTEMA...",
            "latest_analysis": "SISTEMA LISTO // ESPERANDO OBJETIVO",
            "detections": [], # Raw data for client-side SVG/Canvas rendering
            "cam_active": False,
            "db_mode": self.db.mode, # "MILVUS" or "SQLITE"
            "db_active": self.db.active or (self.db.mode == "SQLITE")
        }
        
        self.settings = {
            "conf_threshold": 0.40,
            "loitering_time": 5.0,
            "intrusion_zone": [300, 200, 980, 520],
            "draw_on_server": True # FORCE ON: Ensure AI overlay is visible in video stream
        }
        
        self.incident_logs = []
        
        # Optimization: Emotion Cache
        self.frame_count = 0
        self.cached_emotions = []

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.cam_running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("INFO: Orchestrator stopped.")

    def _try_open_camera_with_timeout(self, idx: int, timeout: float = 3.0):
        """
        Attempt to open camera with timeout to prevent deadlock.
        Returns: VideoCapture object if successful, None if timeout/failure
        """
        result = {'cap': None, 'opened': False}
        
        def _open():
            try:
                print(f"[CAM_INIT] Attempting VideoCapture({idx})...")
                cap = cv2.VideoCapture(idx)
                result['cap'] = cap
                result['opened'] = cap.isOpened()
                print(f"[CAM_INIT] Device {idx}: isOpened={result['opened']}")
            except Exception as e:
                print(f"[CAM_INIT] Device {idx} exception: {e}")
        
        thread = threading.Thread(target=_open, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print(f"[CAM_INIT] Device {idx} TIMEOUT after {timeout}s - likely blocked/in-use")
            return None
        
        if result['opened']:
            print(f"[CAM_INIT] ✅ Device {idx} opened successfully")
            return result['cap']
        else:
            print(f"[CAM_INIT] ❌ Device {idx} failed to open")
            if result['cap']:
                result['cap'].release()
            return None

    def _read_frame_with_timeout(self, cap, timeout: float = 2.0):
        """
        Read frame from camera with timeout to prevent deadlock.
        Returns: (success: bool, frame: np.ndarray or None)
        """
        result = {'ret': False, 'frame': None, 'done': False}
        
        def _read():
            try:
                ret, frame = cap.read()
                result['ret'] = ret
                result['frame'] = frame
                result['done'] = True
            except Exception as e:
                print(f"[CAM_READ] Exception during read: {e}")
                result['done'] = True
        
        thread = threading.Thread(target=_read, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if not result['done']:
            print(f"[CAM_READ] ⏱️ Frame read TIMEOUT after {timeout}s - camera blocked!")
            return False, None
        
        return result['ret'], result['frame']

    def toggle_camera(self, state: bool):
        print(f"DEBUG: toggle_camera requesting lock for state={state}")
        with self.lock:
            print("DEBUG: toggle_camera ACQUIRED lock")
            self.cam_running = state
            # NOTE: We do NOT force self.telemetry["cam_active"] here.
            # We let the _process_loop update it when it actually acquires/releases the camera.
            # This prevents "fake active" states.
            if not state:
                self.telemetry["camera_status"] = "DETENIENDO_MOTOR..."
                # We leave latest_frame until loop clears it or we overwrite it, 
                # but clearing it here gives immediate 'frozen' feedback if desirable.
                # Let's not clear it yet to avoid black flash.
        print("DEBUG: toggle_camera RELEASED lock")

    def _process_loop(self):
        cap = None
        current_idx = self.source
        prev_loop_time = time.time()
        
        while self.running:
            if not self.cam_running:
                if cap:
                    cap.release()
                    cap = None
                time.sleep(0.5)
                continue

            if cap is None or not cap.isOpened():
                print("[LOOP] Camera not open, attempting initialization...")
                cam_opened = False
                
                # Try devices with timeout to prevent deadlock
                for idx in [current_idx, 0, 1, 2]:
                    print(f"[LOOP] Trying device {idx} with 3s timeout...")
                    cap = self._try_open_camera_with_timeout(idx, timeout=3.0)
                    
                    if cap and cap.isOpened():
                        current_idx = idx
                        self.telemetry["camera_status"] = f"CONECTADA [DEV_{idx}]"
                        cam_opened = True
                        print(f"[LOOP] ✅ Camera {idx} connected successfully!")
                        break
                    elif cap:
                        # Cap was returned but not opened, release it
                        cap.release()
                        cap = None
                
                if not cam_opened:
                    print("[LOOP] ❌ All camera devices failed/timeout. Retrying in 2s...")
                    self.telemetry["camera_status"] = "ERROR: SOFTWARE_BLOCK_OR_NO_CAM"
                    # self.cam_running = False  <-- STOP DISABLING IT
                    time.sleep(2.0)
                    continue

            # --- FRAME READING LOOP ---
            print(f"[LOOP] 🟢 Camera Loop Start.")
            
            empty_frame_count = 0
            
            while self.cam_running and cap and cap.isOpened():
                start_time = time.time()
                start_proc = time.time()
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    empty_frame_count += 1
                    if empty_frame_count % 30 == 0:
                        print(f"[LOOP] ⚠️ Camera is OPEN but returning EMPTY frames (Count: {empty_frame_count}). Possible Privacy Block.")
                        self.telemetry["camera_status"] = "ERROR: PERMISO_DENEGADO_MACOS?"
                    
                    time.sleep(0.1)
                    continue
                
                # Reset counter on success
                empty_frame_count = 0
                self.telemetry["camera_status"] = "ONLINE_NORMAL"


                # Log successful frame every 100 frames to avoid spam
                if int(time.time() * 30) % 100 == 0:
                    print(f"[LOOP] ✅ Frame captured: {frame.shape}")

                # --- PILELINE IA REAL ---
                self.frame_count += 1
                
                # 1. Object Detection (YOLO)
                detections = self.yolo.detect(frame)
                
                # 2. Emotion Detection (Optimized: Every 4 frames)
                if self.frame_count % 4 == 0:
                    try:
                        self.cached_emotions = self.emotion_detector.detect(frame)
                    except Exception as e:
                        print(f"WARN: Emotion detection failed: {e}")
                        self.cached_emotions = []

                # Copy frame for processing (only if server drawing is needed)
                processed_frame = frame.copy()
                if self.settings["draw_on_server"]:
                    processed_frame = self.pose.find_pose(processed_frame, draw=True)

                # Get pose landmarks once per frame (lightweight if mediapipe initialized)
                lm_list = self.pose.get_position(frame, draw=False)
                
                # Collect telemetry updates and DB inserts locally to avoid long lock holds
                local_inserts = []
                # print("DEBUG: process_loop requesting lock")
                with self.lock:
                    # print("DEBUG: process_loop ACQUIRED lock")
                    self.telemetry["detections"] = []
                    self.telemetry["track_count"] = 0

                    for i, det in enumerate(detections.boxes):
                        # defensively extract box/cls/conf — some boxes implementations may vary
                        try:
                            box = det.xyxy[0].tolist()
                            cls = int(det.cls[0])
                            conf = float(det.conf[0])
                        except Exception:
                            # skip malformed detection
                            continue

                        if cls == 0 and conf > self.settings["conf_threshold"]:
                            self.telemetry["track_count"] += 1
                            x1, y1, x2, y2 = map(int, box)

                            # Action Recognition
                            action_label = "DESCONOCIDO"
                            if lm_list:
                                action_label = self.action_classifier.classify(lm_list)

                            # Emotion Matching
                            emotion_label = "NEUTRAL"
                            emotion_conf = 0.0
                            
                            # Find matching face
                            # Simple heuristic: Face center is within body box and in top 1/3 of body
                            for face in self.cached_emotions:
                                f_box = face["box"] # [x, y, w, h]
                                fx, fy = f_box[0] + f_box[2]/2, f_box[1] + f_box[3]/2
                                
                                # Check if face center is inside person box
                                if x1 < fx < x2 and y1 < fy < y2:
                                    emotion_label = face["emotion"]
                                    emotion_conf = face["conf"]
                                    break

                            # Export raw data for high-performance React UI
                            self.telemetry["detections"].append({
                                "id": i,
                                "box": [x1, y1, x2, y2],
                                "conf": round(conf, 2),
                                "action": action_label,
                                "emotion": emotion_label, # Add emotion to telemetry
                                "emotion_conf": round(emotion_conf, 2),
                                "landmarks": lm_list if lm_list else [] # Export skeleton
                            })
                            
                            # Actualizar texto de análisis en tiempo real
                            if emotion_label != "NEUTRAL":
                                self.telemetry["latest_analysis"] = f"SUJETO DETECTADO: {action_label} | EMOCION: {emotion_label}"
                            else:
                                self.telemetry["latest_analysis"] = f"SUJETO DETECTADO: {action_label}"

                            if self.settings["draw_on_server"]:
                                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (246, 130, 59), 1)

                            self._behavior_core(box, i)

                            # Queue DB insert (do it outside the lock). Use deterministic embedding.
                            try:
                                vector = self.embedding.embed(frame, [x1, y1, x2, y2], lm_list)
                            except Exception:
                                vector = None

                            local_inserts.append({
                                "person_id": i,
                                "timestamp": time.time(),
                                "vector": vector,
                                "metadata": {"conf": conf, "class": "persona"}
                            })

                # Enqueue DB inserts outside the lock to avoid blocking the main loop
                if local_inserts and self.running and getattr(self, 'ingest_worker', None):
                    for entry in local_inserts:
                        try:
                            self.ingest_worker.enqueue(entry)
                        except Exception:
                            pass

                # Update Telemetry Stats (always update regardless of DB state)
                now = time.time()
                dt = now - prev_loop_time
                self.telemetry["fps"] = round(1.0 / dt if dt > 0 else 30.0, 1)
                prev_loop_time = now
                self.telemetry["latency"] = round((time.time() - start_proc) * 1000, 1)

                self.latest_frame = processed_frame
                
                # SYNC: Ensure telemetry reflects true hardware status
                with self.lock:
                    self.telemetry["cam_active"] = True

            # except Exception as e:
            #     print(f"ALERTA_IA: Error en loop de procesamiento: {e}")
            #     time.sleep(0.1)
            
        # End of loop
        if cap:
            cap.release()
        self.telemetry["cam_active"] = False

    def _behavior_core(self, box, pid):
        center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        zx1, zy1, zx2, zy2 = self.settings["intrusion_zone"]
        
        if zx1 < center[0] < zx2 and zy1 < center[1] < zy2:
            self._log_incident(f"ALERTA: OBJETIVO_{pid} EN ZONA RESTRINGIDA", "danger")

    def _log_incident(self, msg, severity):
        now = time.time()
        if self.incident_logs and self.incident_logs[-1]["msg"] == msg and (now - self.incident_logs[-1]["unix"] < 5):
            return
        
        entry = {
            "id": len(self.incident_logs) + 1,
            "time": time.strftime("%H:%M:%S"),
            "unix": now,
            "msg": msg,
            "type": severity
        }
        self.incident_logs.append(entry)
        self.telemetry["anomalies"] += 1
        self.telemetry["latest_analysis"] = msg

    def get_frame(self):
        with self.lock:
            if self.latest_frame is None: return None
            ret, buffer = cv2.imencode('.jpg', self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes()

    def _clean_data(self, data):
        """
        Recursively convert numpy types to native Python types for JSON serialization.
        """
        if isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data(v) for v in data]
        elif isinstance(data, (np.integer, np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.floating, np.float64, np.float32)):
            return float(data)
        elif isinstance(data, np.ndarray):
            return self._clean_data(data.tolist())
        else:
            return data

    def get_telemetry(self):
        data = self.telemetry.copy()
        data["logs"] = self.incident_logs[-15:]
        
        # WS Video Pivot: Embed frame directly
        with self.lock:
            if self.latest_frame is not None and self.cam_running:
                try:
                    # Optimize for WS transmission: Resize & Compress
                    small_frame = cv2.resize(self.latest_frame, (640, 360))
                    ret, buffer = cv2.imencode('.jpg', small_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    if ret:
                        b64_str = base64.b64encode(buffer).decode('utf-8')
                        data["frame"] = b64_str
                    else:
                        print("ERROR: Frame encode returned False")
                except Exception as e:
                    print(f"Frame encoding error: {e}")
            else:
                # If cam is running but no frame, send placeholder or nothing
                # data["frame"] = "" 
                pass
                    
        return self._clean_data(data)

    def get_vault_data(self, limit=50):
        # Browse the collection for historical data.
        # We use an empty filter to match all entries if supported, or a fallback query.
        try:
            if self.db and (self.db.active or self.db.mode == "SQLITE"):
                return self.db.query(expr="", limit=limit)
            return []
        except Exception:
            return []

    def get_analytics_summary(self):
        logs = self.incident_logs
        return {
            "total_incidents": len(logs),
            "danger_count": len([l for l in logs if l["type"] == "danger"]),
            "warning_count": len([l for l in logs if l["type"] == "warning"]),
            "activity_trend": [len([l for l in logs if l["unix"] > (time.time() - (i*3600))]) for i in range(24)]
        }

    def get_history(self):
        return self.incident_logs
