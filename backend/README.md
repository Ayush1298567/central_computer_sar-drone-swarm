# SAR Central Computer - Backend

## Setup

```
python -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements_core_runtime.txt
pip install -r backend/requirements.txt
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --reload
```

## Auth
- JWT access 15m, refresh 7d
- Roles: admin, operator, viewer

## Discovery
- mDNS (stub), MAVLink UDP 14550 heartbeat, LoRa serial beacons

## Persistence
- `MissionLog`, `DroneStateHistory` with indices
- 1s background state writer; reload in-progress missions on startup

## CI
- GitHub Actions runs backend pytest coverage (>=70%) and frontend vitest (>=50%)


