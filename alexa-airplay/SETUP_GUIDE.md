# Alexa AirPlay Bridge - Complete Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Amazon Developer Account Setup](#amazon-developer-account-setup)
3. [Home Assistant Addon Installation](#home-assistant-addon-installation)
4. [Initial Configuration](#initial-configuration)
5. [Verification & Testing](#verification--testing)
6. [Advanced Setup](#advanced-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need
- ✅ Home Assistant OS or Container (latest version)
- ✅ Amazon account (with Echo devices registered)
- ✅ Amazon Developer account (free)
- ✅ Apple Music subscription (or use any AirPlay-capable app)
- ✅ Network: All devices on same local network (or VPN for remote)
- ✅ Ports available: 5000, 5353 (UDP), 8000/TCP

### System Requirements
- **Minimum**: Raspberry Pi 3 or equivalent
- **Recommended**: Raspberry Pi 4, x86_64 system, or NAS with Docker
- **Memory**: 256 MB minimum (512 MB recommended)
- **Disk**: 100 MB free for addon

### Check Your Setup
Before starting, verify:
```bash
# From your Home Assistant system:

# Check Home Assistant version (2024.1.0+)
# Settings > About

# Check network access to addon ports
curl http://localhost:5000
curl http://localhost:8000

# Verify Echo devices are available
# Alexa app > Devices > Show all devices
```

---

## Amazon Developer Account Setup

### Step 1: Create Amazon Developer Account

1. Go to [developer.amazon.com](https://developer.amazon.com)
2. Click "Sign In" (top right)
3. Enter your Amazon account credentials
   - Use the SAME Amazon account that has your Echo devices
   - If you don't have one, click "Create account"
4. Accept terms and complete registration

### Step 2: Create a New App

1. After login, go to **Developer Console**
2. Click **Apps & Services** → **Alexa Skills Kit**
3. Click **"Create Skill"** button
   - Skill name: `Alexa AirPlay Bridge` (or any name)
   - Skill type: **Custom**
   - Hosting: **Alexa-hosted (Node.js)**
4. Click **Create Skill** button

### Step 3: Get OAuth Credentials

1. In Developer Console, click **"Register for AVS"**
   - Or go to: **Alexa Voice Service** in the menu
   
2. **Create new AVS product**:
   - Product type: **Alexa app**
   - Product name: `Alexa AirPlay Bridge`
   - Product description: `Bridges Echo devices to AirPlay`
   - Skip to Create button

3. After creation, you'll see a screen with:
   - **Product ID**: Save this
   - **Security Profile**: Click to expand

4. **In Security Profile section**:
   - Click **"Web Settings"**
   - Find your **Client ID** and **Client Secret**
   - Copy both - you'll need them!

### Step 4: Add Redirect URI

1. Still in Security Profile → Web Settings
2. Click **"Edit"**
3. In "Redirect URLs" section, add:
   ```
   http://<YOUR_HOMEASSISTANT_IP>:8000/oauth/callback
   ```
   
   Replace `<YOUR_HOMEASSISTANT_IP>` with:
   - Local IP: `192.168.1.100` (for local network)
   - Or if remote: `https://yourdomain.com:8000/oauth/callback`
4. Click **"Save"**

### ✅ Amazon Setup Complete!

You should now have:
- [ ] Amazon Developer Account created
- [ ] AVS Product created
- [ ] **Client ID** (saved somewhere safe)
- [ ] **Client Secret** (saved somewhere safe)
- [ ] Redirect URI added to security profile

---

## Home Assistant Addon Installation

### Option A: Install from Repository (Recommended)

1. Open Home Assistant
2. Go to: **Settings** → **Add-ons & Integrations** → **Add-ons**
3. Click the **menu icon** (⋮) → **Repositories**
4. Enter repository URL:
   ```
   https://github.com/yourusername/alexa-airplay-addon-repo
   ```
5. Click **Add**
6. Go back to Add-ons page
7. Find **"Amazon Echo AirPlay Bridge"**
8. Click to open addon page
9. Click **"INSTALL"** button
10. Wait for installation to complete (2-3 minutes)

### Option B: Manual Installation

1. SSH into your Home Assistant system:
   ```bash
   ssh root@<home-assistant-ip>
   ```

2. Navigate to addons directory:
   ```bash
   cd /usr/share/hassio/addons
   ```

3. Clone the addon:
   ```bash
   git clone https://github.com/yourusername/alexa-airplay-addon.git
   cd alexa-airplay-addon
   ```

4. Go back to Add-ons in Home Assistant
5. Click menu → **Check for updates**
6. Wait, then find "Amazon Echo AirPlay Bridge"
7. Install normally

### Verify Installation

1. Go to: **Settings** → **Add-ons & Integrations** → **Add-ons**
2. Find **"Amazon Echo AirPlay Bridge"**
3. Status should show **"Not running"** initially

---

## Initial Configuration

### Step 1: Start the Addon

1. Click on "Amazon Echo AirPlay Bridge" addon
2. Click the **START** button
3. Wait 30 seconds for startup
4. Check status - should show **"Running"** (green indicator)
5. View logs to confirm no errors

Expected log output:
```
Starting Alexa AirPlay Bridge addon...
Log level: INFO
AirPlay Port: 5000
Initializing Alexa AirPlay Bridge...
Configuration loaded: {...}
Starting AirPlay Bridge services...
Starting Web UI server...
Starting Device Manager...
Starting AirPlay Server...
Web UI started at http://0.0.0.0:8000
```

### Step 2: Access Web Configuration

1. Click the **"Open Web UI"** button (or navigate manually)
2. Browser opens to: `http://your-home-assistant:8000`
3. You should see the Alexa AirPlay Bridge setup page

### Step 3: Enter Amazon Credentials

1. **Scroll to "Configuration" section**
2. In **"Client ID"** field:
   - Paste your Client ID from Amazon Developer Console
3. In **"Client Secret"** field:
   - Paste your Client Secret from Amazon Developer Console
4. Click **"Save Configuration"** button
5. You should see: **"Configuration saved!"**

### Step 4: Authorize with Amazon

1. **Scroll to "Setup" section** (at top)
2. Click **"Authorize Amazon"** button
3. New window opens with Amazon login
4. **Log in** with your Amazon account (same as Echo devices)
5. You'll see permissions request
6. Click **"Allow"** to authorize
7. You should see: **"✓ Authorization Successful!"**
8. New window closes automatically

### Step 5: Verify Device Discovery

1. Back on Web UI, go to **"Virtual AirPlay Devices"** section
2. Wait 30 seconds
3. You should see your Echo devices listed:
   - Device name (e.g., "Living Room Echo")
   - Current status (e.g., "stopped")
   - If playing, artist name

Example output:
```
Living Room Echo
stopped

Kitchen Echo Dot
stopped

Bedroom Echo Show
stopped
```

If you don't see devices:
- ⏱️ Wait another 30 seconds (device discovery takes time)
- 🔄 Refresh the page
- ✅ See [Troubleshooting](#troubleshooting) if still not showing

---

## Verification & Testing

### Test 1: Check AirPlay Discovery (iOS)

**Equipment needed**: iPhone, iPad, or Mac with Apple Music

1. **iOS/iPadOS**:
   - Open Apple Music app
   - Play any song
   - Tap the **AirPlay icon** (speaker with triangle)
   - Look for your Echo device names

2. **macOS**:
   - Open Music app or iTunes
   - Play any song
   - Click **AirPlay icon** in menu bar
   - Look for Echo device names

3. **Expected result**: Your Echo devices should appear in the AirPlay menu
   - Example: "Echo Dot - Living Room"
   - Listed alongside other AirPlay speakers

### Test 2: Play Audio

If you see devices in AirPlay menu:

1. **Select your Echo device** from the AirPlay menu
2. **Music should start playing** on the Echo device
3. **Audio should come through** Echo speaker
4. **Controls should work**:
   - Tap pause - Echo pauses
   - Tap play - Echo resumes
   - Volume slider - Echo volume changes

### Test 3: Check Web UI Status

1. **Refresh Web UI** (the browser window with setup page)
2. Go to **"Virtual AirPlay Devices"** section
3. Device status should now show:
   - "playing" (while streaming)
   - Current track name and artist
   - Volume level (if available)

Example:
```
Living Room Echo
playing
The Weeknd - Blinding Lights
Volume: 60%
```

### Test 4: Verify All Controls Work

While audio is playing, test:

| Control | Action | Expected Result |
|---------|--------|-----------------|
| **Play** | Tap play button | Resumes if paused |
| **Pause** | Tap pause button | Audio stops |
| **Next** | Skip to next track | Song changes |
| **Previous** | Go to previous track | Song changes back |
| **Volume** | Adjust volume slider | Echo volume changes |
| **Shuffle** | Toggle shuffle button | Affects playback order |

---

## Advanced Setup

### Setup Remote Access (External Network)

If you want to use this outside your home network:

1. **Set up dynamic DNS**:
   - Get a domain name or use ddns service
   - Point it to your home IP address
   - See: https://www.howtogeek.com/66438/

2. **Update addon configuration**:
   - Edit Amazon Security Profile Redirect URI
   - Change from: `http://192.168.1.100:8000/oauth/callback`
   - To: `https://yourdomain.com:8000/oauth/callback`

3. **Enable HTTPS** (recommended):
   - Use reverse proxy (nginx, Caddy, etc.)
   - Or use Home Assistant cloud

4. **Update firewall**:
   - Forward port 8000 and 5000 to Home Assistant
   - Use strong passwords everywhere

### Setup Multiple Homes

If you have Echo devices in multiple homes:

1. For each home, repeat setup with:
   - Different Amazon Developer app credentials
   - Different Home Assistant instance (or different port)
   - Same Amazon account works for all

### Device Groups in Alexa App

To use device groups:

1. **Create group in Alexa app**:
   - Alexa app → Devices → Groups
   - Click "Create Group"
   - Add your Echo devices to group
   - Name it (e.g., "Living Room")
   - Save

2. **In Web UI**:
   - Device will appear as new virtual AirPlay device
   - Name will match your group name
   - Can stream to all devices in group simultaneously

### Custom Port Configuration

If ports 5000, 5353, or 8000 conflict:

1. **SSH into Home Assistant**:
   ```bash
   ssh root@192.168.1.100
   ```

2. **Edit addon config**:
   ```bash
   nano /usr/share/hassio/addons/alexa-airplay-addon/config.json
   ```

3. **Change ports** in "ports" section:
   ```json
   "ports": {
     "8001/tcp": 8001,
     "5001/tcp": 5001,
     "5353/udp": 5353
   }
   ```

4. **Save and restart addon**

5. **Update Amazon Security Profile** with new callback URL:
   ```
   http://your-ip:8001/oauth/callback
   ```

---

## Troubleshooting

### Problem: Addon won't start

**Check logs**:
1. Click addon
2. Click "Logs" tab
3. Look for error messages

**Common causes**:

| Error | Solution |
|-------|----------|
| `Port 5000 already in use` | Change port in config.json |
| `Permission denied /data` | Restart Home Assistant |
| `SSL certificate error` | Update system time - Settings > System > Date & time |
| `Module not found` | Wait 2 minutes for dependencies |

**Fix**: If stuck, try:
```bash
# SSH into Home Assistant
ssh root@your-ip

# Restart addon
ha addons restart alexa-airplay

# View real-time logs
ha addons logs alexa-airplay -f
```

### Problem: Devices not appearing in AirPlay

**Checklist**:
- ☐ Addon is running (green indicator)
- ☐ Web UI loads (http://your-ip:8000)
- ☐ Amazon credentials are saved
- ☐ Amazon authorization completed
- ☐ Web UI shows devices under "Virtual AirPlay Devices"
- ☐ iOS/macOS on same WiFi network
- ☐ Firewall not blocking port 5353 (mDNS)

**Try these fixes** (in order):

1. **Restart mDNS discovery**:
   ```bash
   # In Home Assistant terminal
   sudo mdns-publish -s _airplay._tcp local 5000
   ```

2. **Restart addon**:
   - Click addon
   - Click "Restart" button
   - Wait 30 seconds
   - Try AirPlay again

3. **Restart iOS device**:
   - Turn WiFi off
   - Wait 5 seconds
   - Turn WiFi back on
   - Try AirPlay menu again

4. **Check network**:
   ```bash
   # From Home Assistant
   ping your-echo-device-ip
   
   # Should respond with: bytes from ...
   # If not responding, device may be offline
   ```

5. **Enable debug logging**:
   - Click addon
   - Click "Configuration" tab
   - Toggle "Debug Logging"
   - Restart addon
   - Check logs for mDNS errors

### Problem: Audio doesn't play

**Checklist**:
- ☐ AirPlay device selected in Apple Music app
- ☐ Volume not muted on Echo device
- ☐ Echo device is on and connected to WiFi
- ☐ Echo device not already playing something else

**Try these fixes**:

1. **Check Echo device**:
   - Use Alexa app to test
   - Tap device → Music → Play something
   - If nothing plays, Echo has issues

2. **Check Home Assistant connectivity**:
   ```bash
   # From Echo device, ping Home Assistant
   ping home-assistant-ip
   ```

3. **Try different music source**:
   - Try Apple Music app
   - Try iTunes (if on Mac)
   - Try Podcasts app
   - If any works, app-specific issue

4. **Restart audio path**:
   - Stop playing
   - Switch to different AirPlay device
   - Switch back to original
   - Try playing again

5. **Check addon logs** for errors:
   ```
   ERROR: Failed to send audio
   ERROR: Device connection lost
   ERROR: API rate limit exceeded
   ```

### Problem: Amazon authentication fails

**When you see "Authorization Successful" but devices don't load**:

1. **Verify your Amazon account**:
   - Check same Amazon account as Echo devices
   - Alexa app → Devices → verify devices listed
   - Note: Apps will show under "Devices > Device types > Other"

2. **Check Client ID/Secret**:
   ```bash
   # SSH into Home Assistant
   cat /usr/share/hassio/addons/alexa-airplay-addon/data/config/config.json
   ```

3. **Re-authorize**:
   - Delete current tokens (force re-auth):
   ```bash
   rm /usr/share/hassio/addons/alexa-airplay-addon/data/config/*.token
   ```
   - Restart addon
   - Click "Authorize Amazon" again

4. **Check Amazon API access**:
   - Visit: https://developer.amazon.com
   - Verify your app shows under "AVS Products"
   - Verify security profile shows your Client ID

### Problem: Slow response/Lag

**Symptoms**: Plays, pauses, volume changes take 2+ seconds

**Causes**:
- WiFi interference
- Network congestion
- Home Assistant under heavy load
- Amazon API rate limiting

**Solutions**:

1. **Use wired Ethernet** if possible:
   - Connect Home Assistant via cable
   - Much more reliable than WiFi

2. **Check WiFi quality**:
   - Move router closer to devices
   - Check for interference (microwaves, cordless phones)
   - Switch to less congested WiFi channel

3. **Monitor Home Assistant CPU**:
   - Settings > System > Diagnostics
   - Check CPU % usage
   - If >90%, disable other addons

4. **Check network bandwidth**:
   ```bash
   # Monitor network usage
   watch -n 1 "netstat -i"
   ```

### Problem: Crashes or random restarts

**Check logs for**:
- `Memory Error`
- `Out of memory`
- `Segmentation fault`
- `Killed` (Out of memory killer)

**Solutions**:

1. **Increase memory available**:
   - Add more RAM to system (if possible)
   - Disable other memory-heavy addons

2. **Check for resource leaks**:
   - Monitor memory over time
   - Enable debug logging to find culprit

3. **Restart addon scheduler**:
   - Addon will auto-restart on crash
   - Check logs to see if pattern

4. **Contact support** with:
   - Logs (Settings > Diagnostics > Download logs)
   - System info (raspberry Pi model, RAM, etc.)
   - Steps to reproduce

---

## Support

### Getting Help

1. **Check this guide again** - Most issues covered above
2. **Enable debug logging** - Provides detailed error info
3. **Check addon logs** - Click addon > View logs tab
4. **Visit issues page** - Similar problems may have solutions
5. **Open new issue** with:
   - Your Home Assistant version
   - Addon version
   - Relevant log snippets (remove private info)
   - Steps to reproduce

### Reporting Bugs

Include when reporting:
```
Home Assistant Version: 2024.1.0
Addon Version: 1.0.0
Echo Device Model: Echo Dot (4th Gen)
Network: WiFi 5GHz
Issue: [description]

Steps to reproduce:
1. [first step]
2. [second step]
3. [etc]

Expected behavior: [what should happen]
Actual behavior: [what actually happens]

Logs (last 50 lines):
[paste relevant logs]
```

---

## Next Steps

After successful setup:

1. ✅ Test with all your Echo devices
2. ✅ Create device groups in Alexa app for multi-room audio
3. ✅ Add custom port mappings if needed
4. ✅ Enable remote access if desired
5. ✅ Set up automations in Home Assistant if needed

**Enjoy streaming Apple Music to your Echo devices! 🎵**
