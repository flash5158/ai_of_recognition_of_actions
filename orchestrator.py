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
from database.vector_store import VectorDB
from database.ingest_worker import IngestWorker

class Orchestrator:
    def __init__(self, source=0):
        logging.getLogger("panoptes.orchestrator").info("Iniciando Motor CHALAS AI RECOGNITION v1.0 [BEHAVIORAL_ANALYSIS]...")
        self.source = source
        self.yolo = YOLODetector()
        self.pose = PoseEstimator()
        self.action_classifier = ActionClassifier()
        self.embedding = EmbeddingExtractor(dim=128)
        self.db = VectorDB()
        # Start background ingest worker (offloads DB IO)
        try:
            self.ingest_worker = IngestWorker(self.db)
        except Exception:
            self.ingest_worker = None
        
        self.running = False
        self.cam_running = False # Start offline to prevent startup hang
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
            "draw_on_server": False # PRO: Client-side rendering is 10x faster
        }
        
        self.incident_logs = []

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()

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
                for idx in [current_idx, 0, 1, 2]:
                    cap = cv2.VideoCapture(idx)
                    if cap.isOpened():
                        current_idx = idx
                        self.telemetry["camera_status"] = f"CONECTADA [DEV_{idx}]"
                        break
                if not cap or not cap.isOpened():
                    self.telemetry["camera_status"] = "ERROR: SIN_ACCESO_A_WEBCAM"
                    time.sleep(2)
                    continue

            try:
                start_proc = time.time()
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                # --- PILELINE IA REAL ---
                detections = self.yolo.detect(frame)
                
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
                                # We need to map which landmarks belong to this person box. 
                                # For simplicity in single-person scenarios we use the full list, 
                                # but in multi-person we might need more complex matching. 
                                # Assuming the pose estimator returns the 'most prominent' person or we simply pass the full frame logic.
                                # Since PoseEstimator in this codebase seems to wrap MP Pose (single person by default in standard MP unless configured),
                                # we will use the single result for the current detected box if it overlaps.
                                # Optimization: Just classify the robust single pose result for now.
                                action_label = self.action_classifier.classify(lm_list)

                            # Export raw data for high-performance React UI
                            self.telemetry["detections"].append({
                                "id": i,
                                "box": [x1, y1, x2, y2],
                                "conf": round(conf, 2),
                                "action": action_label
                            })
                            
                            # Actualizar texto de análisis en tiempo real
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

            except Exception as e:
                print(f"ALERTA_IA: Error en loop de procesamiento: {e}")
                time.sleep(0.1)
                
            # If loop is running but we hit exception, we are still trying to be active
            
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

    def get_telemetry(self):
        data = self.telemetry.copy()
        data["logs"] = self.incident_logs[-15:]
        return data

    def get_vault_data(self, limit=50):
        # Browse the collection for historical data.
        # We use an empty filter to match all entries if supported, or a fallback query.
        try:
            res = self.db.client.query(
                collection_name=self.db.collection_name,
                filter="",
                limit=limit,
                output_fields=["id", "person_id", "timestamp", "metadata"]
            )
            return res
        except:
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
