"""
Communication Protocols Package
Implements various wireless communication protocols for drone connections
"""

from .base_connection import BaseConnection, ConnectionStatus
# Lazy optional imports to avoid heavy deps during lightweight runs/tests
try:
    from .wifi_connection import WiFiConnection  # type: ignore
except Exception:  # pragma: no cover
    WiFiConnection = None  # type: ignore

try:
    from .lora_connection import LoRaConnection  # type: ignore
except Exception:  # pragma: no cover
    LoRaConnection = None  # type: ignore

try:
    from .mavlink_connection import MAVLinkConnection  # type: ignore
except Exception:  # pragma: no cover
    MAVLinkConnection = None  # type: ignore

try:
    from .websocket_connection import WebSocketDroneConnection  # type: ignore
except Exception:  # pragma: no cover
    WebSocketDroneConnection = None  # type: ignore

__all__ = [
    'BaseConnection',
    'ConnectionStatus',
    'WiFiConnection',
    'LoRaConnection',
    'MAVLinkConnection',
    'WebSocketDroneConnection'
]
