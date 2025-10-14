Phase 9 Completion Summary

Auth & RBAC
- JWT access (15m) and refresh (7d)
- Roles: admin/operator/viewer
- REST and WebSocket protected

Mission Persistence
- Models: MissionLog, DroneStateHistory
- 1s background writer, restart reload of active/paused missions
- History and Logs APIs

Discovery
- mDNS scanner (stub), MAVLink UDP 14550, LoRa serial beacons
- discovery_update WebSocket broadcast on updates

Tests
- Mission persistence & reload: new tests added
- Discovery mocks: mDNS start/stop, LoRa parsing and broadcast

CI/CD & Coverage
- GitHub Actions running backend pytest (coverage xml, >=70%)
- Frontend vitest with coverage (>=50%)
- Coverage artifacts uploaded

Impact
- Secure for supervised multi-user operation
- Survives restarts with mission state reload
- Auto-populates active drones across protocols


