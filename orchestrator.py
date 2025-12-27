import time
import cv2
import threading
import logging
from core.shared_state import SharedState
from core.vision_thread import VisionThread
from core.inference_engine import InferenceEngine
from core.visualizer import Visualizer

class Orchestrator:
    def __init__(self, source=0):
        self.source = source
        self.shared = SharedState()
        self.vision = VisionThread(source=source)
        self.brain = InferenceEngine(model_path="yolo11n-pose.pt")
        self.visualizer = Visualizer()
        
        logging.getLogger("panoptes.orch").info("Orchestrator V2 (Parallel Core) Initialized")
        
        self.settings = {
            "conf_threshold": 0.40,
            "loitering_time": 5.0,
            "intrusion_zone": [300, 200, 980, 520],
            "draw_on_server": True
        }

    def start(self):
        logging.getLogger("panoptes.orch").info("Starting Engines...")
        self.vision.start()
        self.brain.start()

    def stop(self):
        logging.getLogger("panoptes.orch").info("Stopping Engines...")
        self.vision.stop()
        self.brain.stop()

    def get_frame(self):
        """
        Composition Root for Visualization.
        Fetches latest frame (low latency), fetches latest AI results (async),
        renders HUD, returns JPEG.
        """
        # 1. Get snapshot
        data = self.shared.get_snapshot()
        if data is None or data["frame"] is None:
            return None
            
        frame = data["frame"]
        detections = data["detections"]
        
        # 2. Render HUD (Cyberpunk Style)
        self.visualizer.draw_scene(frame, detections)
        
        # 3. Encode
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buffer.tobytes()

    def get_telemetry(self):
        """
        Returns system status for the dashboard.
        """
        data = self.shared.get_snapshot()
        if data is None:
            return {
                "fps": 0,
                "camera_status": "OFFLINE",
                "detections": []
            }
            
        return {
            "fps": int(data["fps"]),
            "camera_status": "ONLINE" if data["cam_active"] else "CONNECTING",
            "detections": data["detections"],
            # Legacy compatibility fields
            "anomalies": 0,
            "track_count": len(data["detections"]),
            "latest_analysis": "SISTEMA ACTIVO",
            "cam_active": data["cam_active"]
        }

    # Legacy Methods for Server Compatibility
    def toggle_camera(self, state: bool):
        if state:
            self.vision.start()
        else:
            self.vision.stop()
            
    def get_history(self):
        return []
        
    def get_analytics_summary(self):
        return {"total_incidents": 0}
        
    def get_vault_data(self, limit=50):
        return []
