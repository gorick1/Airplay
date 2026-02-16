"""
Device Manager
Manages virtual AirPlay device creation and Alexa device mapping
"""

import asyncio
import json
import logging
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

DEVICES_FILE = "/data/config/devices.json"


class PlaybackState(Enum):
    """Playback state enum"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


@dataclass
class VirtualDevice:
    """Virtual AirPlay device"""
    id: str
    name: str
    alexa_device_id: str
    type: str  # "device" or "group"
    state: PlaybackState = PlaybackState.STOPPED
    volume: int = 50
    current_track: Optional[str] = None
    artist: Optional[str] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "alexa_device_id": self.alexa_device_id,
            "type": self.type,
            "state": self.state.value,
            "volume": self.volume,
            "current_track": self.current_track,
            "artist": self.artist,
        }


class DeviceManager:
    """Manages virtual AirPlay devices and Alexa integration"""
    
    def __init__(self, config, amazon_client):
        self.config = config
        self.amazon_client = amazon_client
        self.devices: Dict[str, VirtualDevice] = {}
        self.running = False
        self.update_interval = 30  # seconds
        self._load_devices()
    
    # ── persistence ───────────────────────────────────────────
    def _load_devices(self):
        """Load manually-added devices from disk."""
        try:
            if os.path.exists(DEVICES_FILE):
                with open(DEVICES_FILE, "r") as f:
                    data = json.load(f)
                for d in data:
                    dev = VirtualDevice(
                        id=d["id"],
                        name=d["name"],
                        alexa_device_id=d.get("alexa_device_id", ""),
                        type=d.get("type", "device"),
                    )
                    self.devices[dev.id] = dev
                logger.info(f"Loaded {len(self.devices)} device(s) from disk")
        except Exception as e:
            logger.error(f"Failed to load devices from disk: {e}")

    def _save_devices(self):
        """Persist devices to disk."""
        try:
            os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
            data = [d.to_dict() for d in self.devices.values()]
            with open(DEVICES_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} device(s) to disk")
        except Exception as e:
            logger.error(f"Failed to save devices to disk: {e}")

    # ── manual device management ──────────────────────────────
    def add_manual_device(self, name: str) -> VirtualDevice:
        """Add a device by name (manual entry)."""
        # Create a safe ID from the name
        safe = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        device_id = f"airplay_{safe}"

        # Avoid duplicates
        if device_id in self.devices:
            logger.info(f"Device already exists: {name} ({device_id})")
            return self.devices[device_id]

        device = VirtualDevice(
            id=device_id,
            name=name,
            alexa_device_id=safe,
            type="device",
        )
        self.devices[device_id] = device
        self._save_devices()
        logger.info(f"Added manual device: {name} ({device_id})")
        return device

    def remove_device(self, device_id: str) -> bool:
        """Remove a single device by ID."""
        if device_id in self.devices:
            del self.devices[device_id]
            self._save_devices()
            logger.info(f"Removed device: {device_id}")
            return True
        return False

    def remove_all_devices(self) -> int:
        """Remove all devices. Returns count removed."""
        count = len(self.devices)
        self.devices.clear()
        self._save_devices()
        logger.info(f"Removed all {count} device(s)")
        return count
    
    async def start(self):
        """Start device manager"""
        self.running = True
        logger.info(
            "Device Manager started – %d device(s) loaded from disk",
            len(self.devices),
        )
        # Keep the loop alive so the task isn't collected, but there's
        # nothing to poll since devices are added manually.
        while self.running:
            await asyncio.sleep(60)
    
    async def stop(self):
        """Stop device manager"""
        self.running = False
        logger.info("Device Manager stopped")
    
    async def refresh_devices(self):
        """Reload devices from disk (manual-entry model)."""
        self._load_devices()
        logger.info(f"Refreshed devices from disk – {len(self.devices)} device(s)")
    
    def get_device(self, device_id: str) -> Optional[VirtualDevice]:
        """Get a device by ID"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[VirtualDevice]:
        """Get all virtual devices"""
        return list(self.devices.values())
    
    async def set_playback_state(self, device_id: str, state: PlaybackState) -> bool:
        """Set playback state"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        device.state = state
        logger.debug(f"Device {device.name} state: {state.value}")
        return True
    
    async def set_volume(self, device_id: str, volume: int) -> bool:
        """Set device volume"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        volume = max(0, min(100, volume))  # Clamp to 0-100
        device.volume = volume
        logger.debug(f"Device {device.name} volume: {volume}")
        return True
    
    async def set_metadata(self, device_id: str, track: str, artist: str) -> bool:
        """Set track metadata"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        device.current_track = track
        device.artist = artist
        logger.debug(f"Device {device.name} playing: {artist} - {track}")
        return True
