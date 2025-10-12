# Architecture - short
```mermaid
flowchart LR
  UI[Operator GUI] --> Central[Central Computer]
  Central -->|Mission JSON (HTTP/Redis)| Pi[Raspberry Pi on drone]
  Pi -->|MAVLink| FC[Flight Controller]
  Pi -->|Telemetry (Redis)| Central
  Central -. Emergency MAVLink (lazy) .-> FC
  Central -->|Prometheus scrape| Metrics[Prometheus]
  Metrics --> Grafana[Grafana Dashboards]
```

## Monitoring & Health
- /api/v1/metrics exposes Prometheus text format (counters/gauges)
- /api/v1/health exposes basic JSON health: {status, drones_online, ai_enabled}
- Optional alerting hooks route to stdout/webhook placeholders

## Config Flags
- AI_ENABLED: enable AI endpoints
- REDIS_ENABLED, REDIS_URL: enable Redis telemetry subscribe
- SQLALCHEMY_ENABLED: enable optional registry DB persistence

