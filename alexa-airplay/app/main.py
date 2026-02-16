#!/usr/bin/env python3
"""
Alexa AirPlay Bridge - Main Application
Bridges Amazon Echo devices to virtual AirPlay receivers
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("alexa-airplay")

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from core.app import AirPlayBridge
from core.config import load_config


async def main():
    """Main application entry point"""
    try:
        logger.info("Initializing Alexa AirPlay Bridge...")
        
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded - Redirect URI: {config.amazon_redirect_uri}")
        
        # Initialize the bridge
        bridge = AirPlayBridge(config)
        
        # Start the bridge
        logger.info("Starting AirPlay Bridge services...")
        await bridge.start()
        
        # Keep running
        logger.info("Alexa AirPlay Bridge is running")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
