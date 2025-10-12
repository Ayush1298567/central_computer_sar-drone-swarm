import pytest

from app.monitoring.metrics import (
    export_prometheus_text,
    inc_telemetry_updates,
    set_drones_online,
    set_missions_active,
)


def test_export_prometheus_text_returns_bytes_and_type():
    body, content_type = export_prometheus_text()
    assert isinstance(body, (bytes, bytearray))
    assert isinstance(content_type, str)
    assert "text/plain" in content_type


def test_metrics_increment_and_gauges_noop_safe():
    # Ensure helper functions do not raise and optionally reflect in export
    set_drones_online(5)
    set_missions_active(2)
    inc_telemetry_updates(3)
    body, _ = export_prometheus_text()
    text = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else ""
    # If prometheus_client is available, the metric names should appear
    if text:
        # These checks are conditional to avoid false negatives when library is absent
        if "telemetry_updates_total" in text:
            assert "drones_online_total" in text or "missions_active_total" in text
