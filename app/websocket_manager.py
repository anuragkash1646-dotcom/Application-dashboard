"""
WebSocket Manager Module
Manages multi-client WebSocket connections, shared simulation state,
background ticker for automated protocol step progression, and
real-time synchronization of client actions.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

from app.protocol_simulator import (
    ProtocolEvent,
    SimulationState,
    generate_web_sequence,
    generate_smtp_sequence,
    generate_hls_sequence,
)

logger = logging.getLogger("websocket_manager")
logging.basicConfig(level=logging.INFO)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.state: SimulationState = SimulationState()
        self._ticker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        # Initialize with default web sequence so dashboard opens with rich data ready
        self._load_initial_demo()

    def _load_initial_demo(self) -> None:
        events = generate_web_sequence("https://example.com/index.html")
        self.state.activity_type = "web"
        self.state.events = events
        self.state.total_steps = len(events)
        self.state.current_step = 1
        self.state.is_playing = False
        self.state.activity_log.append({
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "text": "Initial demo loaded: Web Browsing (https://example.com/index.html)",
            "type": "system"
        })

    def _add_log(self, text: str, log_type: str = "action") -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "text": text,
            "type": log_type
        }
        self.state.activity_log.append(entry)
        # Keep recent 50 logs
        if len(self.state.activity_log) > 50:
            self.state.activity_log.pop(0)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active clients: {len(self.active_connections)}")
        # Send initial full state snapshot to the newly connected client
        await websocket.send_text(self.get_state_json())

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Active clients: {len(self.active_connections)}")

    def get_state_json(self) -> str:
        return json.dumps({
            "type": "state_update",
            "state": self.state.model_dump()
        })

    async def broadcast_state(self) -> None:
        if not self.active_connections:
            return
        payload = self.get_state_json()
        disconnected: Set[WebSocket] = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                disconnected.add(ws)
        for ws in disconnected:
            self.active_connections.discard(ws)

    def _sync_hls_buffer(self) -> None:
        if self.state.activity_type == "hls" and 1 <= self.state.current_step <= len(self.state.events):
            cur_event = self.state.events[self.state.current_step - 1]
            if "buffer_health_sec" in cur_event.metadata:
                self.state.hls_buffer_sec = float(cur_event.metadata["buffer_health_sec"])

    def _stop_ticker(self) -> None:
        if self._ticker_task and not self._ticker_task.done():
            self._ticker_task.cancel()
            self._ticker_task = None

    def _start_ticker(self) -> None:
        self._stop_ticker()
        self._ticker_task = asyncio.create_task(self._ticker_loop())

    async def _ticker_loop(self) -> None:
        try:
            while self.state.is_playing:
                # Interval delay: 1.5s scaled by playback speed (bounded between 0.2s and 5.0s)
                speed = max(0.2, min(5.0, self.state.playback_speed))
                delay = 1.5 / speed
                await asyncio.sleep(delay)

                async with self._lock:
                    if not self.state.is_playing:
                        break
                    if self.state.current_step < self.state.total_steps:
                        self.state.current_step += 1
                        self._sync_hls_buffer()
                        await self.broadcast_state()
                    else:
                        self.state.is_playing = False
                        self._add_log("Simulation playback reached final event.", "system")
                        await self.broadcast_state()
                        break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ticker loop exception: {e}")

    # ================= User Actions =================

    async def handle_action(self, action_data: Dict[str, Any]) -> None:
        action = action_data.get("action")
        async with self._lock:
            if action == "start_web":
                url = action_data.get("url", "https://example.com/index.html")
                events = generate_web_sequence(url)
                self.state.activity_type = "web"
                self.state.events = events
                self.state.total_steps = len(events)
                self.state.current_step = 1
                self.state.is_playing = True
                self.state.hls_buffer_sec = 0.0
                self._add_log(f"User requested URL: {url}", "action")
                self._start_ticker()

            elif action == "start_smtp":
                sender = action_data.get("sender", "alice@example.com")
                recipient = action_data.get("recipient", "bob@example.com")
                subject = action_data.get("subject", "Project Update")
                body = action_data.get("body", "Test email payload")
                events = generate_smtp_sequence(sender, recipient, subject, body)
                self.state.activity_type = "smtp"
                self.state.events = events
                self.state.total_steps = len(events)
                self.state.current_step = 1
                self.state.is_playing = True
                self.state.hls_buffer_sec = 0.0
                self._add_log(f"Dispatched email to {recipient} (Subject: '{subject}')", "action")
                self._start_ticker()

            elif action == "start_hls":
                stream = action_data.get("stream", "live/stream1")
                bitrate = action_data.get("bitrate", "720p")
                events = generate_hls_sequence(stream, bitrate)
                self.state.activity_type = "hls"
                self.state.events = events
                self.state.total_steps = len(events)
                self.state.current_step = 1
                self.state.is_playing = True
                self.state.hls_buffer_sec = 0.0
                self._sync_hls_buffer()
                self._add_log(f"Initiated HLS stream: {stream} ({bitrate})", "action")
                self._start_ticker()

            elif action == "pause":
                self.state.is_playing = False
                self._stop_ticker()
                self._add_log(f"Simulation paused at packet #{self.state.current_step}", "control")

            elif action == "resume":
                if self.state.total_steps > 0:
                    if self.state.current_step >= self.state.total_steps:
                        self.state.current_step = 1
                    self.state.is_playing = True
                    self._add_log(f"Simulation resumed from packet #{self.state.current_step}", "control")
                    self._start_ticker()

            elif action == "step_next":
                self.state.is_playing = False
                self._stop_ticker()
                if self.state.current_step < self.state.total_steps:
                    self.state.current_step += 1
                    self._sync_hls_buffer()
                    self._add_log(f"Advanced step forward to packet #{self.state.current_step}", "control")

            elif action == "step_prev":
                self.state.is_playing = False
                self._stop_ticker()
                if self.state.current_step > 1:
                    self.state.current_step -= 1
                    self._sync_hls_buffer()
                    self._add_log(f"Stepped back to packet #{self.state.current_step}", "control")

            elif action == "replay":
                if self.state.total_steps > 0:
                    self.state.current_step = 1
                    self.state.is_playing = True
                    self.state.hls_buffer_sec = 0.0
                    self._sync_hls_buffer()
                    self._add_log("Replayed simulation from packet #1", "control")
                    self._start_ticker()

            elif action == "jump_to_step":
                target_step = int(action_data.get("step", 1))
                if 1 <= target_step <= self.state.total_steps:
                    self.state.is_playing = False
                    self._stop_ticker()
                    self.state.current_step = target_step
                    self._sync_hls_buffer()
                    self._add_log(f"Jumped directly to packet #{target_step}", "control")

            elif action == "set_speed":
                speed = float(action_data.get("speed", 1.0))
                self.state.playback_speed = max(0.2, min(5.0, speed))
                self._add_log(f"Playback speed changed to {self.state.playback_speed}x", "control")

        # Broadcast state update to all connected clients
        await self.broadcast_state()


# Global singleton instance for the app
manager = ConnectionManager()
