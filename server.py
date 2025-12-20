from fastapi import FastAPI, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import Orchestrator
import uvicorn
import asyncio
import time
import json
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logger = logging.getLogger("panoptes.server")
# Force unbuffered output
import sys
sys.stdout.reconfigure(line_buffering=True)

# Global Orchestrator
panoptes = Orchestrator(source=0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    panoptes.start()
    yield
    # Shutdown
    panoptes.stop()

app = FastAPI(title="PANOPTES QUANTUM API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Clients Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Enviar telemetría a alta frecuencia (30 FPS)
            data = panoptes.get_telemetry()
            await websocket.send_json(data)
            await asyncio.sleep(0.033)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # Log unexpected errors and ensure cleanup
        print(f"WS_ERROR: {e}")
        try:
            manager.disconnect(websocket)
        except Exception:
            pass
    finally:
        # defensive disconnect in case it's still connected
        try:
            manager.disconnect(websocket)
        except Exception:
            pass

def generate_frames():
    while True:
        frame_bytes = panoptes.get_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03) # Cap at 30 FPS for bandwidth stability

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/telemetry")
def get_telemetry():
    return panoptes.get_telemetry()

@app.post("/camera/toggle")
async def toggle_camera(request: Request):
    data = await request.json()
    enabled = data.get("enabled", True)
    panoptes.toggle_camera(enabled)
    return {"status": "success", "cam_active": enabled}

@app.post("/update_settings")
async def update_settings(request: Request):
    settings = await request.json()
    # Apply settings directly to the orchestrator mapping
    for key, value in settings.items():
        if key in panoptes.settings:
            panoptes.settings[key] = value
    return {"status": "success", "settings": panoptes.settings}

@app.get("/vault")
def get_vault_data(limit: int = 50):
    """
    Fetch historical detection data from the Milvus Intelligence Vault.
    """
    return panoptes.get_vault_data(limit=limit)

@app.get("/analytics")
def get_analytics():
    """
    Fetch system-wide behavior analytics and trends.
    """
    return panoptes.get_analytics_summary()

@app.get("/history")
def get_history():
    return panoptes.get_history()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
