# Installation Instructions

## Quick Start (Recommended)

### For Home Assistant OS Users

1. **Open Home Assistant**
   - Go to Settings > Add-ons & Integrations

2. **Add Repository**
   - Click menu (⋮) > Repositories
   - Paste: `https://github.com/yourusername/alexa-airplay-addon-repo`
   - Click Add

3. **Install Addon**
   - Find "Amazon Echo AirPlay Bridge"
   - Click Install
   - Wait 2-3 minutes

4. **Configure**
   - Get Amazon Developer credentials (see SETUP_GUIDE.md)
   - Start the addon
   - Open Web UI
   - Authorize with Amazon
   - Done!

---

## Manual Installation

### For Docker-Based Home Assistant

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/alexa-airplay-addon.git
   cd alexa-airplay-addon
   ```

2. **Build Docker Image**
   ```bash
   docker build -t alexa-airplay:latest .
   ```

3. **Run Container**
   ```bash
   docker run -d \
     --name alexa-airplay \
     --restart unless-stopped \
     -p 5000:5000 \
     -p 5353:5353/udp \
     -p 8000:8000 \
     -v alexa-airplay-config:/data \
     -e AMAZON_CLIENT_ID="your-client-id" \
     -e AMAZON_CLIENT_SECRET="your-client-secret" \
     -e LOG_LEVEL="INFO" \
     alexa-airplay:latest
   ```

4. **Access Web UI**
   - Open http://localhost:8000 in browser
   - Configure and authorize

---

## For Raspberry Pi

### Pi OS Installation

```bash
# SSH into Pi
ssh pi@your-pi-ip

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libssl-dev

# Clone addon
git clone https://github.com/yourusername/alexa-airplay-addon.git
cd alexa-airplay-addon

# Install Python packages
pip3 install -r requirements.txt

# Start addon
python3 app/main.py
```

---

## Requirements

### System
- Home Assistant OS 2024.1.0+
- OR Docker with docker-compose
- OR Raspberry Pi OS / Debian Linux

### Ports
- 5000/TCP - AirPlay RTSP
- 5353/UDP - mDNS discovery
- 8000/TCP - Web UI

### Resources
- 256MB RAM minimum
- 100MB disk space
- Stable network (WiFi or Ethernet)

### Network
- All devices on same local network (or VPN)
- mDNS support (usually enabled by default)
- No port blocking by firewall

---

## Troubleshooting Installation

### Port Already in Use
```bash
# Find what's using port 5000
lsof -i :5000

# Use different port
# Edit config.json: "airplay_port": 5001
```

### Permission Issues
```bash
# Ensure data directory writable
chmod 755 /data
chmod 755 /data/config
```

### Package Installation Failed
```bash
# Install missing system dependencies
sudo apt-get install build-essential python3-dev libssl-dev

# Retry addon start
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

---

## Next Steps

1. Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed configuration
2. Check [README.md](README.md) for feature overview
3. Use [API_REFERENCE.md](API_REFERENCE.md) for automation

---

**Installation complete! 🎉**

For help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or open an [issue](https://github.com/yourusername/alexa-airplay-addon/issues).
