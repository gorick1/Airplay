"""
AirPlay Server
Implements AirPlay receiver protocol using mDNS and RTSP
"""

import asyncio
import logging
from typing import Dict, Optional
from zeroconf import ServiceInfo, Zeroconf
import socket

logger = logging.getLogger(__name__)


class AirPlayServer:
    """AirPlay receiver server"""
    
    def __init__(self, config, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.zeroconf: Optional[Zeroconf] = None
        self.running = False
        self.services: Dict[str, ServiceInfo] = {}
    
    async def start(self):
        """Start AirPlay server"""
        try:
            self.running = True
            logger.info(f"Starting AirPlay server on port {self.config.airplay_port}")
            
            # Initialize mDNS
            self.zeroconf = Zeroconf()
            
            # Register services for each device
            await self.register_devices()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in AirPlay server: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop AirPlay server"""
        self.running = False
        logger.info("Stopping AirPlay server...")
        
        # Unregister all services
        for service_info in self.services.values():
            try:
                if self.zeroconf:
                    self.zeroconf.unregister_service(service_info)
            except Exception as e:
                logger.error(f"Error unregistering service: {e}")
        
        # Close Zeroconf
        if self.zeroconf:
            self.zeroconf.close()
        
        logger.info("AirPlay server stopped")
    
    async def register_devices(self):
        """Register virtual devices via mDNS"""
        try:
            await asyncio.sleep(1)  # Wait for devices to be discovered
            
            devices = self.device_manager.get_all_devices()
            logger.info(f"Registering {len(devices)} AirPlay devices via mDNS")
            
            for device in devices:
                await self.register_device(device)
        except Exception as e:
            logger.error(f"Error registering devices: {e}")
    
    async def register_device(self, device):
        """Register a single device via mDNS"""
        try:
            # Clean name for mDNS
            service_name = f"{device.name.replace(' ', '_')}_{device.id[-4:]}"
            
            # Get local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Create mDNS service info for AirPlay
            service_type = "_airplay._tcp.local."
            service_info = ServiceInfo(
                service_type,
                f"{service_name}{service_type}",
                addresses=[socket.inet_aton(local_ip)],
                port=self.config.airplay_port,
                properties={
                    "model": "AppleTV3,1",
                    "password": "false",
                    "flags": "0x4",
                    "features": "0x5A7FFFF7",
                    "deviceid": device.id,
                    "pk": "8D6D4CD3B59AB2C3BD36C3D2C3C3C3C3",
                },
                server=f"{hostname}.local.",
            )
            
            if self.zeroconf:
                self.zeroconf.register_service(service_info)
                self.services[device.id] = service_info
                logger.info(f"Registered AirPlay device: {device.name}")
        except Exception as e:
            logger.error(f"Error registering device {device.name}: {e}")
    
    async def handle_airplay_connection(self, reader, writer):
        """Handle incoming AirPlay connection"""
        try:
            # Read RTSP request
            data = await reader.read(4096)
            logger.debug(f"Received AirPlay request: {data[:200]}")
            
            # TODO: Parse RTSP and handle audio streaming
            # For now, respond with basic RTSP OK
            response = b"RTSP/1.0 200 OK\r\n\r\n"
            writer.write(response)
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling AirPlay connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
