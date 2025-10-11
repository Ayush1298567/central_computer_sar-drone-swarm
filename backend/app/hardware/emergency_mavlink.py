# backend/app/hardware/emergency_mavlink.py
"""
Lightweight emergency MAVLink wrapper.
Lazy-loads pymavlink only when actually used (emergency).
Provides: arm(), disarm(), return_to_launch(), land()
This file must NOT be imported at normal startup unless emergency flags used.
"""

from dataclasses import dataclass
from typing import Optional
import logging
logger = logging.getLogger(__name__)

@dataclass
class MAVConfig:
    connection_string: str  # e.g., "udp:127.0.0.1:14550" or "/dev/ttyAMA0"
    baud: int = 57600
    timeout: float = 5.0

# internal holder for connection
_mav = None
_mav_config: Optional[MAVConfig] = None

def _lazy_init(config: MAVConfig):
    global _mav, _mav_config
    if _mav is not None:
        return
    try:
        from pymavlink import mavutil  # lazy import
    except Exception as e:
        logger.error("pymavlink not available: %s", e)
        raise RuntimeError("pymavlink not available") from e

    _mav_config = config
    logger.info("Connecting to MAVLink: %s", config.connection_string)
    _mav = mavutil.mavlink_connection(config.connection_string, baud=config.baud, source_system=255)
    # Wait for heartbeat (blocking with timeout)
    _mav.wait_heartbeat(timeout=config.timeout)
    logger.info("MAVLink heartbeat received from system %s", getattr(_mav, 'target_system', 'unknown'))

def _ensure_mav(config: MAVConfig):
    if _mav is None:
        _lazy_init(config)

def arm(config: MAVConfig):
    _ensure_mav(config)
    logger.warning("EMERGENCY: arming vehicle via MAVLink")
    # Use mavutil to send arm (wrapped)
    _mav.mav.command_long_send(
        _mav.target_system, _mav.target_component,
        400, 0, 1, 0, 0, 0, 0, 0, 0
    )

def disarm(config: MAVConfig):
    _ensure_mav(config)
    logger.warning("EMERGENCY: disarming vehicle via MAVLink")
    _mav.mav.command_long_send(
        _mav.target_system, _mav.target_component,
        400, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )

def return_to_launch(config: MAVConfig):
    _ensure_mav(config)
    logger.warning("EMERGENCY: Return to Launch via MAVLink")
    # MAV_CMD_NAV_RETURN_TO_LAUNCH = 20 per mavlink
    _mav.mav.command_long_send(
        _mav.target_system, _mav.target_component,
        192, 0, 0, 0, 0, 0, 0, 0, 0
    )

def land(config: MAVConfig):
    _ensure_mav(config)
    logger.warning("EMERGENCY: Land via MAVLink")
    _mav.mav.command_long_send(
        _mav.target_system, _mav.target_component,
        21, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )

