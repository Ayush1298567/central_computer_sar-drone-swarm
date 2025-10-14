import pytest
from datetime import datetime

from app.core.database import SessionLocal
from app.models.mission import Mission, MissionLog, MissionDrone
from app.models.drone import Drone, DroneStateHistory


@pytest.mark.timeout(180)
def test_mission_create_persist_and_log(tmp_path, monkeypatch):
    db = SessionLocal()
    try:
        m = Mission(
            mission_id="m_test_1",
            name="Test Mission",
            description="",
            status="active",
            center_lat=0.0,
            center_lng=0.0,
            search_area={}
        )
        db.add(m)
        db.commit()
        got = db.query(Mission).filter(Mission.mission_id == "m_test_1").first()
        assert got is not None
    finally:
        db.close()


@pytest.mark.timeout(180)
def test_drone_state_history_write(tmp_path):
    db = SessionLocal()
    try:
        # minimal drone row
        d = Drone(drone_id="d_state_1", name="D", model="X")
        db.add(d)
        db.commit()
        d_id = db.query(Drone).filter(Drone.drone_id == "d_state_1").first().id
        snap = DroneStateHistory(drone_id=d_id, status="online")
        db.add(snap)
        db.commit()
        assert db.query(DroneStateHistory).count() >= 1
    finally:
        db.close()


@pytest.mark.timeout(180)
def test_mission_logs_append_and_history_api(monkeypatch):
    # import endpoint functions directly and pass db session
    from app.api.api_v1.endpoints.missions import get_mission_logs, get_mission_history
    db = SessionLocal()
    try:
        m = Mission(mission_id="m_hist_1", name="Hist", status="planning", center_lat=0.0, center_lng=0.0, search_area={})
        db.add(m)
        db.commit()

        mid = db.query(Mission).filter(Mission.mission_id == "m_hist_1").first().id
        db.add(MissionLog(mission_id=mid, event_type="state_update", message="start"))
        db.add(MissionLog(mission_id=mid, event_type="state_update", message="tick"))
        db.commit()

        res_logs = get_mission_logs("m_hist_1", skip=0, limit=10, db=db)
        assert res_logs["count"] >= 2

        # no telemetry rows yet; should be empty
        res_hist = get_mission_history("m_hist_1", skip=0, limit=10, db=db)
        assert res_hist["count"] == 0
    finally:
        db.close()


@pytest.mark.timeout(180)
def test_reload_in_progress_assignments(monkeypatch):
    from app.services.real_mission_execution import real_mission_execution_engine
    db = SessionLocal()
    try:
        # create mission active
        m = Mission(mission_id="m_reload_1", name="Reload", status="active", center_lat=0.0, center_lng=0.0, search_area={})
        d = Drone(drone_id="d_reload_1", name="D", model="X")
        db.add(m)
        db.add(d)
        db.commit()
        m_db = db.query(Mission).filter(Mission.mission_id == "m_reload_1").first()
        d_db = db.query(Drone).filter(Drone.drone_id == "d_reload_1").first()
        db.add(MissionDrone(mission_id=m_db.id, drone_id=d_db.id))
        db.commit()

        # run reload method
        import asyncio
        asyncio.get_event_loop().run_until_complete(real_mission_execution_engine.reload_in_progress())
        # verify in active_executions
        assert str(m_db.id) in real_mission_execution_engine.active_executions
    finally:
        db.close()


