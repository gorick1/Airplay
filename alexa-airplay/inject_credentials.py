#!/usr/bin/env python3
"""
Inject Amazon credentials into addon config
Use this as a workaround if the web UI is not working
"""

import json
import sys
from pathlib import Path

def inject_credentials(client_id: str, client_secret: str, redirect_uri: str = None):
    """Inject credentials into config file"""
    
    config_dir = Path("/data/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / "config.json"
    
    # Default redirect URI for Home Assistant Ingress
    if not redirect_uri:
        redirect_uri = "https://home.garrettorick.com/api/hassio_ingress/YOUR_INGRESS_TOKEN/oauth/callback"
    
    config_data = {
        "amazon_client_id": client_id,
        "amazon_client_secret": client_secret,
        "amazon_redirect_uri": redirect_uri,
        "airplay_port": 5001,
        "web_port": 8000,
        "ha_url": "http://supervisor"
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✓ Credentials saved to {config_file}")
        print(f"✓ Client ID: {client_id[:20]}...")
        print(f"✓ Client Secret: {'*' * 10}...")
        print(f"✓ Redirect URI: {redirect_uri}")
        print("\nRestart the addon to apply changes:")
        print("  ha addon restart ha_alexa_airplay_addon")
        return True
    except Exception as e:
        print(f"✗ Error saving credentials: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 inject_credentials.py <client_id> <client_secret> [redirect_uri]")
        print()
        print("Example:")
        print('  python3 inject_credentials.py "amzn1.application-oa2-client.xxx" "your_secret"')
        sys.exit(1)
    
    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    redirect_uri = sys.argv[3] if len(sys.argv) > 3 else None
    
    inject_credentials(client_id, client_secret, redirect_uri)
