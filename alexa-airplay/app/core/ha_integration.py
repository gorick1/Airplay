"""
Home Assistant Integration
Handles communication with Home Assistant Supervisor API
"""

import asyncio
import logging
import os
from typing import Dict, Optional
import aiohttp

logger = logging.getLogger(__name__)


class HAIntegration:
    """Integration with Home Assistant"""
    
    def __init__(self):
        self.token = os.getenv("SUPERVISOR_TOKEN", "")
        self.ha_url = os.getenv("HA_URL", "http://supervisor")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_status(self) -> Dict:
        """Get Home Assistant status"""
        try:
            await self.init_session()
            headers = {"Authorization": f"Bearer {self.token}"}
            
            async with self.session.get(
                f"{self.ha_url}/core/api/config",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Failed to get HA status: {resp.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting HA status: {e}")
            return {}
    
    async def call_service(self, domain: str, service: str, data: Dict = None) -> bool:
        """Call Home Assistant service"""
        try:
            await self.init_session()
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = data or {}
            
            async with self.session.post(
                f"{self.ha_url}/core/api/services/{domain}/{service}",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status == 200:
                    logger.debug(f"Service called: {domain}.{service}")
                    return True
                else:
                    logger.error(f"Failed to call service: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error calling service: {e}")
            return False
    
    async def notify(self, title: str, message: str, data: Dict = None) -> bool:
        """Send notification to Home Assistant"""
        notify_data = {
            "title": title,
            "message": message,
        }
        if data:
            notify_data.update(data)
        
        return await self.call_service("notify", "persistent_notification", notify_data)
    
    async def log_event(self, event_type: str, data: Dict = None) -> bool:
        """Log event to Home Assistant"""
        event_data = {
            "event_type": event_type,
            "data": data or {}
        }
        
        try:
            await self.init_session()
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{self.ha_url}/core/api/events/{event_type}",
                headers=headers,
                json=data or {}
            ) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False


# Global instance
ha_integration = HAIntegration()
