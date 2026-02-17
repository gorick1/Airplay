#!/usr/bin/env python3
"""
Alexa Music Controller – entry point
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("alexa-controller")

sys.path.insert(0, str(Path(__file__).parent))

from core.app import AlexaMusicController


async def main():
    controller = AlexaMusicController()
    try:
        logger.info("Initializing Alexa Music Controller...")
        await controller.start()
        # keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        await controller.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
