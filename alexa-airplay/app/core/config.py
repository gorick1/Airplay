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
        
        # Amazon credentials - try environment first, then load from file
        self.amazon_client_id = os.getenv("AMAZON_CLIENT_ID", "")
        self.amazon_client_secret = os.getenv("AMAZON_CLIENT_SECRET", "")
        self.amazon_redirect_uri = os.getenv("AMAZON_REDIRECT_URI", "")
        self.external_base_url = os.getenv("EXTERNAL_BASE_URL", "")
        
        # AirPlay settings
        self.airplay_port = int(os.getenv("AIRPLAY_PORT", "5001"))
        self.airplay_mdns_port = 5353
        self.web_port = int(os.getenv("WEB_PORT", "8099"))
        
        # Home Assistant
        self.ha_token = os.getenv("HA_TOKEN", "")
        self.ha_url = os.getenv("HA_URL", "http://supervisor")
        
        # Debug
        self.debug = os.getenv("LOG_LEVEL", "INFO") == "DEBUG"
        
        # Load from config file if it exists
        self._load_from_file()
        
        # Also load from addon options if available (overwrites env vars)
        self._load_from_addon_options()
    
    def _load_from_addon_options(self):
        """Load configuration from Home Assistant addon options file"""
        options_file = Path("/data/options.json")
        logger.debug(f"Checking for addon options file: {options_file}")
        if options_file.exists():
            try:
                with open(options_file, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded addon options: {list(data.keys())}")
                    # Map addon options to config attributes
                    if 'amazon_client_id' in data and data['amazon_client_id']:
                        logger.info(f"Setting amazon_client_id from addon options")
                        self.amazon_client_id = data['amazon_client_id']
                    if 'amazon_client_secret' in data and data['amazon_client_secret']:
                        logger.info(f"Setting amazon_client_secret from addon options")
                        self.amazon_client_secret = data['amazon_client_secret']
                    if 'amazon_redirect_uri' in data and data['amazon_redirect_uri']:
                        logger.info(f"Setting amazon_redirect_uri from addon options")
                        self.amazon_redirect_uri = data['amazon_redirect_uri']
                    if 'external_base_url' in data and data['external_base_url']:
                        logger.info(f"Setting external_base_url from addon options")
                        self.external_base_url = data['external_base_url']
                    if 'airplay_port' in data:
                        logger.info(f"Setting airplay_port from addon options: {data['airplay_port']}")
                        self.airplay_port = int(data['airplay_port'])
                logger.info(f"Loaded addon options from {options_file}")
            except Exception as e:
                logger.warning(f"Failed to load addon options: {e}")
        else:
            logger.debug(f"Addon options file not found: {options_file}")
    
    def _load_from_file(self):
        """Load configuration from file"""
        config_file = self.config_dir / "config.json"
        logger.debug(f"Attempting to load config from: {config_file}")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded config data: {list(data.keys())}")
                    for key, value in data.items():
                        if hasattr(self, key):
                            old_val = getattr(self, key, None)
                            setattr(self, key, value)
                            logger.debug(f"Set {key}: {old_val} -> {value if key != 'amazon_client_secret' else '***'}")
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
                "amazon_redirect_uri": self.amazon_redirect_uri,
                "external_base_url": self.external_base_url,
                "airplay_port": self.airplay_port,
                "web_port": self.web_port,
                "ha_url": self.ha_url,
            }
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Saved configuration to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def save_tokens(self, access_token: str, refresh_token: str, expiry_ts: float):
        """Persist OAuth tokens to a separate file so they survive restarts"""
        token_file = self.config_dir / "tokens.json"
        try:
            token_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expiry_ts": expiry_ts,
            }
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.info("Saved OAuth tokens to disk")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    def load_tokens(self) -> Optional[Dict[str, Any]]:
        """Load persisted OAuth tokens"""
        token_file = self.config_dir / "tokens.json"
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                logger.info("Loaded persisted OAuth tokens from disk")
                return data
            except Exception as e:
                logger.warning(f"Failed to load tokens: {e}")
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for web UI"""
        return {
            "amazon_client_id": self.amazon_client_id,
            "amazon_client_secret": self.amazon_client_secret,  # UI needs to show current secret
            "amazon_redirect_uri": self.amazon_redirect_uri,
            "external_base_url": self.external_base_url,
            "airplay_port": self.airplay_port,
            "web_port": self.web_port,
            "debug": self.debug,
            "config_dir": str(self.config_dir),
            "data_dir": str(self.data_dir),
        }


def load_config() -> Config:
    """Load and return configuration"""
    return Config()
