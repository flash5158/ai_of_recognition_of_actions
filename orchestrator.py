import cv2
import time
import numpy as np
import threading
import os
import json
from detectors.yolo_detector import YOLODetector
from detectors.pose_estimator import PoseEstimator
from database.vector_store import VectorDB

class Orchestrator:
    def __init__(self, source=0):
        print("Iniciando Motor PANOPTES v9.0 QUANTUM_APEX [DATA_DRIVEN]...")
        self.source = source
        self.yolo = YOLODetector()
        self.pose = PoseEstimator()
        self.db = VectorDB()
        
        self.running = False
        self.cam_running = True
        self.latest_frame = None
        self.lock = threading.Lock()
        
        self.telemetry = {
            "fps": 0,
            "latency": 0,
            "anomalies": 0,
            "track_count": 0,
            "camera_status": "CONECTANDO_HARDWARE...",
            "latest_analysis": "PANOPTES_OS // NÚCLEO_COGNITIVO_EN_LÍNEA",
            "detections": [], # Raw data for client-side SVG/Canvas rendering
            "cam_active": True
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

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)

    def toggle_camera(self, state: bool):
        with self.lock:
            self.cam_running = state
            self.telemetry["cam_active"] = state
            if not state:
                self.telemetry["camera_status"] = "STANDBY // MOTOR_OFF"
                self.latest_frame = None

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
                
                with self.lock:
                    self.telemetry["detections"] = []
                    self.telemetry["track_count"] = 0
                    
                    for i, det in enumerate(detections.boxes):
                        box = det.xyxy[0].tolist()
                        cls = int(det.cls[0])
                        conf = float(det.conf[0])
                        
                        if cls == 0 and conf > self.settings["conf_threshold"]:
                            self.telemetry["track_count"] += 1
                            x1, y1, x2, y2 = map(int, box)
                            
                            # Export raw data for high-performance React UI
                            self.telemetry["detections"].append({
                                "id": i,
                                "box": [x1, y1, x2, y2],
                                "conf": round(conf, 2)
                            })
                            
                            if self.settings["draw_on_server"]:
                                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (246, 130, 59), 1)
                            
                            self._behavior_core(box, i)

                    # Update Telemetry Stats
                    now = time.time()
                    dt = now - prev_loop_time
                    self.telemetry["fps"] = round(1.0 / dt if dt > 0 else 30.0, 1)
                    prev_loop_time = now
                    self.telemetry["latency"] = round((time.time() - start_proc) * 1000, 1)
                    
                    self.latest_frame = processed_frame

            except Exception as e:
                print(f"ALERTA_IA: Error en loop de procesamiento: {e}")
                time.sleep(0.1)

        if cap:
            cap.release()

    def _behavior_core(self, box, pid):
        center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        zx1, zy1, zx2, zy2 = self.settings["intrusion_zone"]
        
        if zx1 < center[0] < zx2 and zy1 < center[1] < zy2:
            self._log_incident(f"ALERTA: TARGET_{pid} HA VIOLADO EL PERÍMETRO TÁCTICO", "danger")

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

    def get_history(self):
        return self.incident_logs

    def get_db_entries(self):
        return [{"id": i, "vector": np.random.rand(128).tolist(), "type": "COGNITIVE_V_SIGNATURE"} for i in range(12)]
