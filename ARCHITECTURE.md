# Architecture - short
```mermaid
flowchart LR
  UI[Operator GUI] --> Central[Central Computer]
  Central -->|Mission JSON (HTTP/Redis)| Pi[Raspberry Pi on drone]
  Pi -->|MAVLink| FC[Flight Controller]
  Pi -->|Telemetry (Redis)| Central
  Central -. Emergency MAVLink (lazy) .-> FC
```

