# backend/tests/test_drone_registry.py
import os
import tempfile
import json
import pytest

from app.communication.drone_registry import DroneRegistry, get_registry

@pytest.mark.timeout(180)
def test_register_and_persistence(tmp_path):
    persist_path = tmp_path / "registry.json"
    r = DroneRegistry(persist_path=str(persist_path))
    r.register_pi_host("d1", "http://127.0.0.1:8000", meta={"note":"t1"})
    assert r.get_pi_host("d1") == "http://127.0.0.1:8000"
    assert r.get_status("d1") == "online"
    # reload from disk
    r2 = DroneRegistry(persist_path=str(persist_path))
    assert r2.get_pi_host("d1") == "http://127.0.0.1:8000"
    assert "d1" in r2.list_drones()

@pytest.mark.timeout(180)
def test_unregister_and_errors(tmp_path):
    r = DroneRegistry(persist_path=str(tmp_path/"r.json"))
    r.register_pi_host("d2", "http://a:1")
    assert r.unregister("d2") is True
    with pytest.raises(KeyError):
        r.set_status("d2", "offline")
