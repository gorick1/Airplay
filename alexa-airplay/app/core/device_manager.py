"""
Device Manager
Manages virtual AirPlay device creation and Alexa device mapping
"""

import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


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
    
    async def start(self):
        """Start device manager"""
        self.running = True
        logger.info("Device Manager started")
        
        # Periodically discover and update devices
        while self.running:
            try:
                await self.refresh_devices()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in device refresh loop: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop device manager"""
        self.running = False
        logger.info("Device Manager stopped")
    
    async def refresh_devices(self):
        """Discover and refresh Alexa devices"""
        try:
            if not self.amazon_client.authenticated:
                logger.debug("Not authenticated, skipping device refresh")
                return
            
            alexa_devices = await self.amazon_client.get_devices()
            
            # Create virtual devices for each Alexa device
            for device in alexa_devices:
                device_id = device.get("id")
                device_name = device.get("name", f"Device {device_id}")
                device_type = device.get("type", "device")
                
                # Create or update virtual device
                virtual_id = f"airplay_{device_id}"
                if virtual_id not in self.devices:
                    virtual_device = VirtualDevice(
                        id=virtual_id,
                        name=device_name,
                        alexa_device_id=device_id,
                        type="device"
                    )
                    self.devices[virtual_id] = virtual_device
                    logger.info(f"Created virtual device: {device_name}")
            
            logger.debug(f"Device Manager: {len(self.devices)} virtual devices active")
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
    
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
