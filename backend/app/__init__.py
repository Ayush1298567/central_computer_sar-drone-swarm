# SAR Mission Commander Backend Application
# Ensure an event loop exists on Windows main thread for tests that call get_event_loop()
try:
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
except Exception:
    pass
