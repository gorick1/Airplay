"""
Configuration management for Alexa AirPlay Bridge
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the addon"""
    
    def __init__(self):
        self.config_dir = Path(os.getenv("CONFIG_DIR", "/data/config"))
        self.data_dir = Path(os.getenv("DATA_DIR", "/data"))
        self.log_dir = Path(os.getenv("LOG_DIR", "/data/logs"))
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Amazon credentials
        self.amazon_client_id = os.getenv("AMAZON_CLIENT_ID", "")
        self.amazon_client_secret = os.getenv("AMAZON_CLIENT_SECRET", "")
        self.amazon_redirect_uri = os.getenv("AMAZON_REDIRECT_URI", "http://localhost:8000/oauth/callback")
        
        # AirPlay settings
        self.airplay_port = int(os.getenv("AIRPLAY_PORT", "5000"))
        self.airplay_mdns_port = 5353
        self.web_port = 8000
        
        # Home Assistant
        self.ha_token = os.getenv("HA_TOKEN", "")
        self.ha_url = os.getenv("HA_URL", "http://supervisor")
        
        # Debug
        self.debug = os.getenv("LOG_LEVEL", "INFO") == "DEBUG"
        
        # Load from config file if it exists
        self._load_from_file()
    
    def _load_from_file(self):
        """Load configuration from file"""
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
    
    def save(self):
        """Save configuration to file"""
        config_file = self.config_dir / "config.json"
        try:
            config_data = {
                "amazon_client_id": self.amazon_client_id,
                "amazon_client_secret": self.amazon_client_secret,
                "airplay_port": self.airplay_port,
            }
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "amazon_client_id": self.amazon_client_id,
            "amazon_client_secret": "***" if self.amazon_client_secret else "",
            "airplay_port": self.airplay_port,
            "web_port": self.web_port,
            "debug": self.debug,
            "config_dir": str(self.config_dir),
            "data_dir": str(self.data_dir),
        }


def load_config() -> Config:
    """Load and return configuration"""
    return Config()
