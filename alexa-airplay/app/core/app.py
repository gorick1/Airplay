"""
Alexa Music Controller – main orchestrator
Wires together the HA client, device manager, and web UI.
"""

import asyncio
import logging

from .ha_integration import HAClient
from .device_manager import DeviceManager
from .web_ui import WebUIServer

logger = logging.getLogger(__name__)


class AlexaMusicController:
    """Main application: discovers Echo devices and lets the user
    send playback commands via the HA media_player service."""

    def __init__(self):
        self.ha = HAClient()
        self.device_manager = DeviceManager(self.ha)
        self.web_ui = WebUIServer(self.ha, self.device_manager)
        self.running = False

    async def start(self):
        """Launch all services concurrently."""
        self.running = True
        logger.info("Starting Alexa Music Controller...")

        web_task = asyncio.create_task(self.web_ui.start())
        device_task = asyncio.create_task(self.device_manager.start())

        await asyncio.gather(web_task, device_task)

    async def shutdown(self):
        logger.info("Shutting down Alexa Music Controller...")
        self.running = False
        await self.device_manager.stop()
        await self.web_ui.stop()
        await self.ha.close()
        logger.info("Shutdown complete")
