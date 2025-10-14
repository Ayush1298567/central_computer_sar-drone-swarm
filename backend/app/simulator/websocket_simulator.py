"""
Lightweight WebSocket-based drone simulator for demos and tests.
Emits telemetry every second and listens for mission/command messages.
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import websockets

logger = logging.getLogger(__name__)


@dataclass
class SimDrone:
  drone_id: str
  lat: float
  lon: float
  alt: float
  battery: float = 100.0
  status: str = "idle"

  def step(self) -> None:
    # Simple motion and battery drain
    self.lat += 0.00005
    self.lon += 0.00003
    self.alt = max(10.0, self.alt + 0.0)
    self.battery = max(0.0, self.battery - 0.05)
    self.status = "flying" if self.battery > 0 else "offline"


class WebSocketDroneSimulator:
  def __init__(self, ws_url: str, drone: SimDrone):
    self.ws_url = ws_url
    self.drone = drone
    self._ws: Optional[websockets.WebSocketClientProtocol] = None
    self._task: Optional[asyncio.Task] = None
    self._stop = asyncio.Event()

  async def start(self) -> None:
    self._stop.clear()
    self._task = asyncio.create_task(self._run())

  async def stop(self) -> None:
    self._stop.set()
    if self._task:
      try:
        await asyncio.wait_for(self._task, timeout=2.0)
      except Exception:
        pass

  async def _run(self) -> None:
    try:
      self._ws = await websockets.connect(self.ws_url)
      await self._handshake()
      while not self._stop.is_set():
        self.drone.step()
        msg = {
          "type": "telemetry",
          "payload": {
            "drones": [
              {
                "id": self.drone.drone_id,
                "lat": self.drone.lat,
                "lon": self.drone.lon,
                "alt": self.drone.alt,
                "battery": self.drone.battery,
                "status": self.drone.status,
                "last_seen": datetime.utcnow().isoformat(),
              }
            ]
          },
        }
        try:
          await self._ws.send(json.dumps(msg))
        except Exception:
          logger.exception("simulator send failed")
          break
        # Drain inbound messages
        await self._drain_incoming()
        try:
          await asyncio.wait_for(self._stop.wait(), timeout=1.0)
        except asyncio.TimeoutError:
          pass
    except Exception:
      logger.exception("simulator connection failed")
    finally:
      try:
        if self._ws:
          await self._ws.close()
      except Exception:
        pass

  async def _handshake(self) -> None:
    hello = {
      "type": "subscribe",
      "payload": {"topics": ["telemetry", "mission_updates", "drone_commands"]},
    }
    await self._ws.send(json.dumps(hello))

  async def _drain_incoming(self) -> None:
    try:
      while True:
        data = await asyncio.wait_for(self._ws.recv(), timeout=0.01)
        try:
          msg = json.loads(data)
          if msg.get("type") == "drone_command":
            cmd = msg.get("payload", {}).get("command")
            if cmd == "rtl":
              self.drone.status = "returning"
            elif cmd == "land":
              self.drone.status = "landing"
        except Exception:
          pass
    except asyncio.TimeoutError:
      return

