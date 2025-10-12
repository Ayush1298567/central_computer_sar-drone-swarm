# backend/tests/test_emergency_protocols.py
import threading
import pytest

from app.services.emergency_protocols import (
    emergency_stop_all,
    return_to_home,
    start_kill_switch_monitor,
    evaluate_collision_avoidance,
    apply_collision_evasion,
)


@pytest.mark.timeout(180)
def test_emergency_stop_and_rtl(monkeypatch):
    calls = []

    def fake_send(cmd, params=None, cfg=None):
        calls.append((cmd, params or {}))
        return True

    monkeypatch.setattr("app.services.emergency_protocols.send_mavlink_command", fake_send)

    assert emergency_stop_all() is True
    assert return_to_home() is True

    cmds = [c[0] for c in calls]
    assert "emergency_disarm" in cmds
    assert "rtl" in cmds


@pytest.mark.timeout(180)
def test_kill_switch_monitor(monkeypatch):
    triggered = threading.Event()
    counter = {"n": 0}

    def read_state():
        # False for first few calls, then True once
        counter["n"] += 1
        return counter["n"] > 3

    def on_trigger():
        triggered.set()

    # Avoid invoking real MAVLink in the background thread
    monkeypatch.setattr(
        "app.services.emergency_protocols.emergency_stop_all",
        lambda cfg=None: True,
    )

    monitor = start_kill_switch_monitor(on_trigger=on_trigger, read_state=read_state, poll_interval=0.01)
    try:
        assert triggered.wait(1.0) is True
    finally:
        monitor.stop()


@pytest.mark.timeout(180)
def test_collision_avoidance(monkeypatch):
    # Front obstacle very close
    plan = evaluate_collision_avoidance({"front": 0.5, "back": 5, "left": 5, "right": 5, "up": 5, "down": 5}, min_distance_m=1.0)
    assert plan["action"] in ("avoid", "rtl")

    calls = []

    def fake_send(cmd, params=None, cfg=None):
        calls.append((cmd, params or {}))
        return True

    monkeypatch.setattr("app.services.emergency_protocols.send_mavlink_command", fake_send)

    assert apply_collision_evasion(plan) is True
    assert len(calls) == 1
    assert calls[0][0] in ("set_velocity", "rtl")


