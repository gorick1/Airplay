"""
AirPlay Protocol Handler
Handles RTSP, RTP, and audio streaming
"""

import asyncio
import logging
from typing import Optional, Dict
import struct
import socket

logger = logging.getLogger(__name__)


class RTSPServer:
    """RTSP (Real Time Streaming Protocol) server for AirPlay"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.running = False
        self.server = None
    
    async def start(self):
        """Start RTSP server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            self.running = True
            logger.info(f"RTSP server listening on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
        except Exception as e:
            logger.error(f"Error starting RTSP server: {e}")
    
    async def stop(self):
        """Stop RTSP server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("RTSP server stopped")
    
    async def handle_client(self, reader, writer):
        """Handle incoming RTSP client connection"""
        try:
            # Read RTSP request
            request = await reader.readuntil(b'\r\n\r\n')
            logger.debug(f"RTSP Request received: {len(request)} bytes")
            
            # Parse request
            lines = request.decode('utf-8', errors='ignore').split('\r\n')
            if not lines:
                return
            
            request_line = lines[0].split()
            if len(request_line) < 3:
                return
            
            method = request_line[0]
            uri = request_line[1]
            
            # Route to appropriate handler
            if method == 'OPTIONS':
                await self.handle_options(writer)
            elif method == 'DESCRIBE':
                await self.handle_describe(writer, uri)
            elif method == 'SETUP':
                await self.handle_setup(writer, uri)
            elif method == 'PLAY':
                await self.handle_play(writer)
            elif method == 'PAUSE':
                await self.handle_pause(writer)
            elif method == 'TEARDOWN':
                await self.handle_teardown(writer)
            else:
                await self.send_response(writer, "501 Not Implemented")
        except Exception as e:
            logger.error(f"Error handling RTSP client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def send_response(self, writer, response: str):
        """Send RTSP response"""
        response_bytes = f"{response}\r\n\r\n".encode('utf-8')
        writer.write(response_bytes)
        await writer.drain()
    
    async def handle_options(self, writer):
        """Handle OPTIONS request"""
        response = """RTSP/1.0 200 OK
Public: OPTIONS, DESCRIBE, SETUP, PLAY, PAUSE, TEARDOWN, GET_PARAMETER, SET_PARAMETER"""
        await self.send_response(writer, response)
    
    async def handle_describe(self, writer, uri: str):
        """Handle DESCRIBE request"""
        # Return SDP (Session Description Protocol)
        sdp = """v=0
o=- 0 0 IN IP4 0.0.0.0
s=AirPlay Stream
c=IN IP4 0.0.0.0
t=0 0
a=tool:airplay-bridge/1.0
a=rtpmap:96 L16/44100/2
m=audio 0 RTP/AVP 96"""
        response = f"RTSP/1.0 200 OK\nContent-Type: application/sdp\nContent-Length: {len(sdp)}"
        await self.send_response(writer, response)
        writer.write(sdp.encode('utf-8'))
        await writer.drain()
    
    async def handle_setup(self, writer, uri: str):
        """Handle SETUP request"""
        response = "RTSP/1.0 200 OK\nTransport: RTP/AVP/UDP;unicast"
        await self.send_response(writer, response)
    
    async def handle_play(self, writer):
        """Handle PLAY request"""
        response = "RTSP/1.0 200 OK\nRange: npt=0-"
        await self.send_response(writer, response)
    
    async def handle_pause(self, writer):
        """Handle PAUSE request"""
        response = "RTSP/1.0 200 OK"
        await self.send_response(writer, response)
    
    async def handle_teardown(self, writer):
        """Handle TEARDOWN request"""
        response = "RTSP/1.0 200 OK"
        await self.send_response(writer, response)


class AudioStreamHandler:
    """Handles audio streaming and buffering"""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer = []
        self.running = False
    
    def add_audio_data(self, data: bytes):
        """Add audio data to buffer"""
        self.buffer.append(data)
    
    def get_audio_data(self, frames: int) -> bytes:
        """Get audio data from buffer"""
        if not self.buffer:
            return b'\x00' * (frames * self.channels * 2)
        
        data = b''.join(self.buffer)
        self.buffer = []
        
        # Return requested amount
        frame_size = self.channels * 2  # Assuming 16-bit audio
        return data[:frames * frame_size]
