"""
Main FastAPI Application
Endpoints:
- GET /health: Status health check returning {"status": "ok"}
- GET /: Web visualizer dashboard (HTML5 SPA)
- WS /ws: Real-time WebSocket connection for synchronized protocol simulation
"""

import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.websocket_manager import manager

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Application Layer Activity & Protocol Visualizer",
    description="Interactive educational Computer Networks Layer-7 protocol visualizer",
    version="1.0.0",
)

# CORS middleware for open local or hosted access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directory path
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files at /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint required by spec."""
    return {"status": "ok"}


@app.get("/")
async def get_index():
    """Serves the primary single-page application dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "ok", "message": "Dashboard UI under initialization"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint supporting client connection, disconnection,
    and handling real-time interactive simulation actions.
    """
    await manager.connect(websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                await manager.handle_action(data)
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON over WebSocket: {raw_text}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
        manager.disconnect(websocket)
