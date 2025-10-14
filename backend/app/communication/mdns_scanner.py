import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class MDNSScanner:
    """Minimal async mDNS scanner stub.
    In production, replace with zeroconf listener that calls the callback.
    """

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, on_discovered: Callable[[str, str, dict], None]):
        self._running = True

        async def _loop():
            while self._running:
                # This stub does not actively discover; real impl should hook zeroconf
                await asyncio.sleep(10)

        self._task = asyncio.create_task(_loop())
        logger.info("mDNS scanner started (stub)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("mDNS scanner stopped")

"""
mDNS scanner to discover services advertising _drone._tcp.local
"""
import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
    from zeroconf import ServiceStateChange
    ZC_AVAILABLE = True
except Exception:
    ZC_AVAILABLE = False


class MDNSScanner:
    def __init__(self, service_type: str = "_drone._tcp.local."):
        self.service_type = service_type
        self._azc: Optional[AsyncZeroconf] = None
        self._browser: Optional[AsyncServiceBrowser] = None
        self._running = False

    async def start(self, on_discovered: Callable[[str, str, dict], None]):
        if not ZC_AVAILABLE:
            logger.warning("zeroconf not available; skipping mDNS scanning")
            return False
        if self._running:
            return True
        self._running = True

        self._azc = AsyncZeroconf()

        def _handler(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                try:
                    info = zeroconf.get_service_info(service_type, name)
                    if not info:
                        return
                    host = info.server.rstrip('.')
                    props = {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in (info.properties or {}).items()}
                    on_discovered(name, host, props)
                except Exception:
                    logger.exception("mDNS discovery handler error")

        self._browser = AsyncServiceBrowser(self._azc.zeroconf, self.service_type, handlers=[_handler])
        logger.info("mDNS scanner started for %s", self.service_type)
        return True

    async def stop(self):
        self._running = False
        try:
            if self._browser:
                await self._browser.async_cancel()
            if self._azc:
                await self._azc.async_close()
        finally:
            self._browser = None
            self._azc = None
            logger.info("mDNS scanner stopped")

