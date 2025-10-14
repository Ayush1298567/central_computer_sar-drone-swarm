"""
Communication Package for SAR Drone System

Lightweight initializer: avoid importing heavy protocol implementations at
package import time to prevent unnecessary dependencies during tests.
"""

from .drone_connection_hub import DroneConnectionHub

# Lazy optional protocol imports to avoid heavy deps at import time
try:
    from .protocols.wifi_connection import WiFiConnection  # type: ignore
except Exception:  # pragma: no cover
    WiFiConnection = None  # type: ignore
try:
    from .protocols.lora_connection import LoRaConnection  # type: ignore
except Exception:  # pragma: no cover
    LoRaConnection = None  # type: ignore
try:
    from .protocols.mavlink_connection import MAVLinkConnection  # type: ignore
except Exception:  # pragma: no cover
    MAVLinkConnection = None  # type: ignore
try:
    from .protocols.websocket_connection import WebSocketDroneConnection  # type: ignore
except Exception:  # pragma: no cover
    WebSocketDroneConnection = None  # type: ignore

from .drone_registry import DroneRegistry

__all__ = [
    'DroneConnectionHub',
    'WiFiConnection',
    'LoRaConnection',
    'MAVLinkConnection',
    'WebSocketDroneConnection',
    'DroneRegistry',
]
