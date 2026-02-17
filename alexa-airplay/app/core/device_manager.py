"""
Device Manager
Discovers media_player entities from Home Assistant and
provides a curated list of controllable Echo/Alexa devices.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from .ha_integration import HAClient

logger = logging.getLogger(__name__)

# Strings that identify an Alexa/Echo device in HA
_ECHO_MARKERS = (
    "echo", "alexa", "fire_tv", "fire tv", "amazon",
    "show", "dot", "studio", "plus", "pop", "sub",
)


class DeviceManager:
    """Discovers and caches Alexa media_player entities from HA."""

    def __init__(self, ha_client: HAClient):
        self.ha = ha_client
        self.devices: Dict[str, Dict] = {}   # entity_id -> state dict
        self.running = False

    # ── lifecycle ─────────────────────────────────────────────
    async def start(self):
        """Background loop: refresh device list every 30 s."""
        self.running = True
        logger.info("Device Manager started")
        while self.running:
            await self.refresh()
            await asyncio.sleep(30)

    async def stop(self):
        self.running = False
        logger.info("Device Manager stopped")

    # ── discovery ─────────────────────────────────────────────
    async def refresh(self) -> List[Dict]:
        """Query HA for all media_player entities, return the list."""
        try:
            all_players = await self.ha.get_all_media_players()
            self.devices = {p["entity_id"]: p for p in all_players}
            logger.info("Discovered %d media_player(s) in HA", len(self.devices))
            return all_players
        except Exception as e:
            logger.error("Failed to refresh devices: %s", e)
            return []

    def get_all(self) -> List[Dict]:
        """Return cached media_player list in a frontend-friendly format."""
        out = []
        for eid, state in self.devices.items():
            attrs = state.get("attributes", {})
            out.append({
                "entity_id": eid,
                "friendly_name": attrs.get("friendly_name", eid),
                "state": state.get("state", "unknown"),
                "volume": attrs.get("volume_level"),
                "media_title": attrs.get("media_title"),
                "media_artist": attrs.get("media_artist"),
                "source": attrs.get("source"),
                "is_echo": self._looks_like_echo(eid, attrs),
                "supported_features": attrs.get("supported_features", 0),
            })
        return out

    def get_echo_devices(self) -> List[Dict]:
        """Return only devices that look like Echo/Alexa."""
        return [d for d in self.get_all() if d["is_echo"]]

    # ── helpers ───────────────────────────────────────────────
    @staticmethod
    def _looks_like_echo(entity_id: str, attrs: dict) -> bool:
        """Heuristic: does this entity look like an Alexa device?"""
        text = (
            entity_id
            + " "
            + attrs.get("friendly_name", "")
            + " "
            + attrs.get("source", "")
        ).lower()
        return any(m in text for m in _ECHO_MARKERS)
