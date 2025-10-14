import pytest

from app.communication.drone_registry import DroneRegistry


@pytest.mark.timeout(180)
def test_registry_db_optional_sqlalchemy_disabled(tmp_path, monkeypatch):
    # Force disabled
    monkeypatch.setenv("SQLALCHEMY_ENABLED", "false")
    reg = DroneRegistry(persist_path=str(tmp_path / "reg.json"))
    reg.register_pi_host("d1", "http://pi")
    # Should be safe no-op
    reg.sync_to_db()
    reg.load_from_db()
    assert "d1" in reg.list_drones()


@pytest.mark.timeout(180)
def test_registry_db_with_sqlite_memory(monkeypatch, tmp_path):
    # Enable but use in-memory sqlite
    monkeypatch.setenv("SQLALCHEMY_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db"))

    reg = DroneRegistry(persist_path=str(tmp_path / "reg.json"))
    reg.register_pi_host("d1", "http://pi")
    reg.set_status("d1", "online")

    # Sync to DB and reload to new registry to verify
    reg.sync_to_db()

    reg2 = DroneRegistry(persist_path=str(tmp_path / "reg2.json"))
    reg2.load_from_db()
    assert "d1" in reg2.list_drones()
    assert reg2.get_status("d1") == "online"
