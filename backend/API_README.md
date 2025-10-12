# API - Monitoring & Health

## Endpoints
- GET `/api/v1/metrics`: Prometheus text format for scraping
- GET `/api/v1/health`: `{ "status": "ok", "drones_online": N, "ai_enabled": bool }`

## Config Flags
- `AI_ENABLED`: enables AI routes (`/api/v1/ai/*`)
- `REDIS_ENABLED`, `REDIS_URL`: enable Redis telemetry receiver subscription
- `SQLALCHEMY_ENABLED`: enable optional registry persistence to DB

## Notes
- All integrations are optional. If a library is missing, code paths no-op safely.
- Tests run fully in <3 minutes without external services; Redis and DB are monkeypatched or optional.
