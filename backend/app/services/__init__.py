"""
Services Package

This package contains all business logic services for the SAR drone system.
"""

# Avoid importing heavy services at package import time to keep tests light
try:
    from .mission_planner import MissionPlanner  # type: ignore
except Exception:  # pragma: no cover
    MissionPlanner = None  # type: ignore
try:
    from .conversational_mission_planner import ConversationalMissionPlanner  # type: ignore
except Exception:  # pragma: no cover
    ConversationalMissionPlanner = None  # type: ignore

__all__ = ['MissionPlanner', 'ConversationalMissionPlanner']