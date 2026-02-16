#!/usr/bin/env python3
"""
Main entry point for the Alexa AirPlay Bridge addon.
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# Setup directories
CONFIG_DIR = Path("/data/config")
LOG_DIR = Path("/data/logs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "addon.log")
    ]
)
logger = logging.getLogger(__name__)

# Environment setup
os.environ.setdefault("ADDON_DIR", "/app")
os.environ.setdefault("DATA_DIR", "/data")
os.environ.setdefault("CONFIG_DIR", str(CONFIG_DIR))
os.environ.setdefault("LOG_DIR", str(LOG_DIR))
os.environ.setdefault("LOG_LEVEL", log_level)
os.environ.setdefault("AIRPLAY_PORT", "5001")
os.environ.setdefault("HA_URL", "http://supervisor")
os.environ.setdefault("HA_TOKEN", os.getenv("SUPERVISOR_TOKEN", ""))

logger.info("=" * 60)
logger.info("Starting Alexa AirPlay Bridge addon...")
logger.info(f"Log level: {log_level}")
logger.info(f"AirPlay Port: {os.getenv('AIRPLAY_PORT')}")
logger.info(f"Data directory: /data")
logger.info("=" * 60)

try:
    # Add the app directory to Python path
    sys.path.insert(0, "/app")
    
    # Import and run the app
    from core.app import AirPlayBridge
    from core.config import Config
    
    async def main():
        # Load configuration
        config = Config()
        
        # Create and start app
        app = AirPlayBridge(config)
        await app.start()
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    # Run the async main loop
    asyncio.run(main())
    
except KeyboardInterrupt:
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)
except Exception as e:
    logger.exception(f"Fatal error: {e}")
    sys.exit(1)
