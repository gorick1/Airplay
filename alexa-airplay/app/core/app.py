"""
Main AirPlay Bridge Application
Orchestrates all components and services
"""

import asyncio
import logging
from typing import Optional, List, Dict
from pathlib import Path

from .config import Config
from .amazon_api import AmazonAPIClient
from .airplay_server import AirPlayServer
from .web_ui import WebUIServer
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)


class AirPlayBridge:
    """Main application class orchestrating all services"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        
        # Initialize components
        self.amazon_client = AmazonAPIClient(config)
        self.device_manager = DeviceManager(config, self.amazon_client)
        self.airplay_server = AirPlayServer(config, self.device_manager)
        self.web_ui = WebUIServer(config, self.amazon_client, self.device_manager)
        
        self.running = False
    
    async def start(self):
        """Start all services"""
        try:
            self.logger.info("Starting AirPlay Bridge services...")
            self.running = True
            
            # Start web UI server
            self.logger.info("Starting Web UI server...")
            web_task = asyncio.create_task(self.web_ui.start())
            
            # Start device manager
            self.logger.info("Starting Device Manager...")
            device_task = asyncio.create_task(self.device_manager.start())
            
            # Start AirPlay server
            self.logger.info("Starting AirPlay Server...")
            airplay_task = asyncio.create_task(self.airplay_server.start())
            
            # Wait for all tasks
            await asyncio.gather(web_task, device_task, airplay_task)
            
        except Exception as e:
            self.logger.error(f"Error during startup: {e}", exc_info=True)
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Shutdown all services"""
        self.logger.info("Shutting down AirPlay Bridge...")
        self.running = False
        
        try:
            await self.airplay_server.stop()
        except Exception as e:
            self.logger.error(f"Error shutting down AirPlay server: {e}")
        
        try:
            await self.device_manager.stop()
        except Exception as e:
            self.logger.error(f"Error shutting down device manager: {e}")
        
        try:
            await self.web_ui.stop()
        except Exception as e:
            self.logger.error(f"Error shutting down web UI: {e}")
        
        self.logger.info("Shutdown complete")
