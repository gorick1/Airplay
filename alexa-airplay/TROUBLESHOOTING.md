# Troubleshooting Guide - Alexa AirPlay Bridge

Comprehensive troubleshooting for common issues and their solutions.

## Quick Diagnostics

Run this script to check your setup:

```bash
#!/bin/bash
echo "=== Alexa AirPlay Bridge Diagnostics ==="
echo ""
echo "1. Checking addon status..."
curl -s http://localhost:8000/health | jq . || echo "❌ Addon not responding"

echo ""
echo "2. Checking devices..."
curl -s http://localhost:8000/api/devices | jq . || echo "❌ Cannot access devices"

echo ""
echo "3. Checking ports..."
netstat -tuln | grep -E "5000|5353|8000" || echo "❌ Ports not listening"

echo ""
echo "4. Checking network..."
ping -c 1 8.8.8.8 > /dev/null && echo "✅ Internet connected" || echo "❌ No internet"

echo ""
echo "5. Checking mDNS..."
avahi-browse -a | grep -i echo || echo "⚠️  No Echo devices found on mDNS"
```

---

## Category: Startup Issues

### Addon won't start (Red indicator)

#### Symptom
- Add-ons page shows red indicator
- "Failed to start" or similar message

#### Solution Steps

1. **Check for port conflicts**:
   ```bash
   # SSH into Home Assistant
   ssh root@your-ha-ip
   
   # Check if ports are in use
   netstat -tuln | grep -E "5000|5353|8000"
   ```
   
   If ports show as LISTENING:
   - Another addon using same ports
   - Change addon port in config.json
   - Restart addon

2. **Check Docker image**:
   ```bash
   # View last 50 log lines
   docker logs ha-addon-alexa-airplay --tail 50
   ```
   
   Look for:
   - `Image not found` → Pull image again
   - `Permission denied` → Restart Home Assistant
   - `Out of disk space` → Free up disk space

3. **Check system resources**:
   ```bash
   # Check disk space
   df -h
   
   # Should have >200MB free
   # If <100MB, free up space and restart
   ```

4. **Full restart**:
   ```bash
   # SSH into Home Assistant
   ha core restart
   
   # Wait 3 minutes
   # Then start addon again
   ```

#### If Still Failing
- Check system logs: `journalctl -u addon_* -n 50`
- Check Docker logs: `docker logs --tail 100 ha-addon-alexa-airplay`
- Take system diagnostics: Home Assistant > Settings > System > Diagnostics

---

### Addon crashes after starting (Keeps restarting)

#### Symptom
- Addon starts but crashes within seconds
- Repeatedly tries to restart

#### Check Crash Reason

1. **View addon logs**:
   - Home Assistant > Add-ons > Amazon Echo AirPlay Bridge > Logs
   - Look for error before crash

2. **Common crash causes**:

| Error | Solution |
|-------|----------|
| `MemoryError` | Addon out of memory - restart Home Assistant |
| `SIGKILL` | Out of memory killer - check free memory |
| `Module not found` | Wait for Python packages to install (first start) |
| `SIGTERM` | Home Assistant stopping it - wait full startup |
| `Address already in use` | Port conflict - change ports |

3. **If module not found on first start**:
   - This is normal for first startup
   - Wait 5 minutes for packages to install
   - Check logs for "Successfully installed"
   - Then restart addon

4. **If memory issues**:
   ```bash
   # Check available memory
   free -m
   
   # Should have >256MB free
   # If not, restart system to free up
   ```

5. **Manual restart with wait**:
   - Stop addon (wait 10 seconds)
   - Start addon
   - Wait 2 full minutes
   - Check logs continuously

---

## Category: Authentication Issues

### "Not Authenticated" message in Web UI

#### Symptom
- Web UI shows "Not Authenticated with Amazon"
- No devices appear
- OAuth button doesn't work

#### Solution Steps

1. **Verify Amazon credentials saved**:
   - Web UI → Configuration section
   - Check Client ID field is populated
   - Click "Save Configuration"
   - See confirmation message

2. **Check if authorized before**:
   - Was "Authorization Successful" shown?
   - If yes, tokens may have expired
   - Continue to re-authorization

3. **Re-authorize**:
   - Web UI → Setup section
   - Click "Authorize Amazon" button
   - Log in with Amazon account
   - See "✓ Authorization Successful"
   - Tokens saved, devices should appear

4. **If OAuth window doesn't open**:
   - Check browser pop-up blocker
   - Add `your-ha-ip:8000` to exceptions
   - Try different browser
   - Try incognito/private window

5. **If OAuth fails (error page)**:
   - Common error: "Invalid redirect URI"
   - Fix: Update Amazon Security Profile
   - Must match exactly: `http://your-ip:8000/oauth/callback`
   - Try using HTTPS if available

#### Debug OAuth Issues

```bash
# SSH into Home Assistant
# Check token files
ls -la /data/config/

# Look for files like: amazon_token_*
# If missing, OAuth never completed

# Check addon logs for auth errors
docker logs ha-addon-alexa-airplay | grep -i "oauth\|auth\|token"
```

---

### Authorization fails with "Invalid Request"

#### Cause
Redirect URI in Amazon settings doesn't match addon callback.

#### Fix

1. Go to Amazon Developer Console
2. Find your Security Profile
3. Click "Web Settings"
4. In "Redirect URLs" make sure:
   - `http://192.168.1.100:8000/oauth/callback` (if on local network)
   - OR `https://yourdomain.com:8000/oauth/callback` (if remote)
5. Exact match - no extra slashes or spaces
6. Click "Save"
7. Try authorization again

---

### Tokens expire after a few hours

#### Symptom
- Works initially
- After several hours, devices stop appearing
- "Not Authenticated" returns

#### Cause
Access tokens expire and refresh failed.

#### Solution

1. **Automatic refresh should handle this**
   - Check addon logs for "Token refreshed"
   - If not showing, refresh issue

2. **Manual re-authorization**:
   - Web UI > Click "Authorize Amazon" again
   - Should be quick if already logged in
   - New tokens will be obtained

3. **If automatic refresh fails**:
   - Ensure Refresh Token saved properly
   - Check: `/data/config/amazon_tokens.json`
   - Should show both access_token and refresh_token
   - If only access_token, re-authorize

---

## Category: Device Discovery Issues

### No devices appearing in Web UI

#### Symptom
- "No devices found"
- Web UI device list empty
- Even though authenticated

#### Checklist

- [ ] Authenticated with Amazon (see "Authorization Successful")
- [ ] Wait 30+ seconds for discovery
- [ ] Check addon running (green indicator)
- [ ] Refresh Web UI page (Ctrl+R)
- [ ] Verify Echo devices in Alexa app (Devices tab)

#### Solution Steps

1. **Wait for discovery**:
   - Device discovery runs every 30 seconds
   - First discovery may take 30-60 seconds
   - Refresh page and wait

2. **Force device refresh**:
   - Stop addon (wait 5 seconds)
   - Start addon
   - Wait 60 seconds
   - Check logs for "Retrieved X devices"

3. **Verify Amazon account**:
   - Open Alexa app
   - Go to Devices
   - Ensure devices listed there
   - If not, add devices to account first

4. **Check account region**:
   - Amazon API only sees devices in same region
   - Addon region = your Amazon account region
   - Check: Developer Console > Settings > Location

5. **Enable debug logging**:
   - Addon Configuration > Toggle "Debug Logging"
   - Restart addon
   - Check logs for:
     ```
     Retrieved 3 devices from Amazon
     Creating virtual device: ...
     ```

#### Debug Device Discovery

```bash
# Check how many devices retrieved
docker logs ha-addon-alexa-airplay | grep "Retrieved.*devices"

# Check for specific errors
docker logs ha-addon-alexa-airplay | grep -i "error\|failed\|exception"

# Check device data file
cat /data/config/devices.json 2>/dev/null
```

---

### Devices appear in Web UI but not in AirPlay menu

#### Symptom
- Web UI lists devices correctly
- iPhone/macOS doesn't show devices in AirPlay menu
- mDNS not broadcasting

#### Solution Steps

1. **Check mDNS broadcasting**:
   ```bash
   # From your computer on same network
   # macOS/Linux:
   dns-sd -B _airplay._tcp local
   
   # Should list your devices
   ```

2. **Check ports open**:
   ```bash
   # Ensure ports accessible
   nc -zv your-ha-ip 5353  # mDNS
   nc -zv your-ha-ip 5000  # AirPlay
   nc -zv your-ha-ip 8000  # Web UI
   ```

3. **Restart mDNS**:
   - Stop addon
   - Wait 10 seconds  
   - Start addon
   - Wait 30 seconds for mDNS re-broadcast
   - Try AirPlay menu again

4. **Check iOS/macOS network**:
   - On device, forget WiFi network
   - Rejoin WiFi network
   - Open Apple Music
   - Check AirPlay menu again

5. **If mDNS still not working**:
   - Check firewall: `ufw status`
   - Allow UDP 5353: `ufw allow 5353/udp`
   - Restart addon

---

### Devices in AirPlay but marked as "unavailable"

#### Symptom
- AirPlay menu shows devices
- When trying to select, device grayed out or unavailable
- Cannot start streaming

#### Cause
Device connectivity issue or permission problem.

#### Solution

1. **Check device online**:
   ```bash
   # Try to reach device
   ping device-ip
   
   # Should respond
   # If not responding, device offline
   ```

2. **Check permissions**:
   - Alexa app > Device > Click device
   - Ensure your account has access
   - Not shared with restricted permissions

3. **Restart Echo device**:
   - Unplug device for 10 seconds
   - Plug back in
   - Wait 30 seconds for startup
   - Try again

4. **Restart addon**:
   - Stop addon
   - Wait 10 seconds
   - Start addon
   - Wait 60 seconds
   - Try AirPlay again

---

## Category: Streaming Issues

### AirPlay shows device but audio won't play

#### Symptom
- Select device in AirPlay menu
- "Connecting..."
- Connection fails or plays but no sound

#### Solution Steps

1. **Check Echo volume**:
   - Use Alexa app or physical device button
   - Volume should be >0
   - Not muted

2. **Check Apple Music app**:
   - Try different app (iTunes, Podcasts, etc.)
   - If other apps work, Music app issue
   - Try restarting Music app

3. **Test with simple audio**:
   - Apple Music > Try different song
   - Podcasts app > Try episode
   - If multiple fail, audio system issue

4. **Check network connectivity**:
   - From Home Assistant:
   ```bash
   ping echo-device-ip  # Should respond
   curl http://echo-device-ip:5000  # Check port
   ```

5. **Check addon logs for errors**:
   ```
   ERROR: Failed to stream audio
   ERROR: Connection refused
   ERROR: Timeout sending data
   ```

6. **Restart audio path**:
   - Pause on iOS
   - Switch to different AirPlay device
   - Switch back
   - Resume playback

---

### Audio drops out or stutters

#### Symptom
- Audio plays but cuts out frequently
- Playback stutters
- Very high latency

#### Cause Analysis

| Symptom | Likely Cause |
|---------|--------------|
| Drops every 10s | Network loss - WiFi issue |
| Constant stuttering | Insufficient bandwidth |
| Large delay before playing | Buffer issue - network congestion |

#### Solutions

1. **For WiFi issues**:
   - Move device closer to router
   - Try 5GHz WiFi instead of 2.4GHz
   - Check signal strength: `-40dBm` or better
   - Reduce network congestion

2. **For bandwidth issues**:
   - Close other bandwidth-heavy apps
   - Run speed test: `speedtest-cli`
   - Minimum 2 Mbps per stream

3. **Use wired connection** (best):
   - If Home Assistant on WiFi, switch to Ethernet
   - Much more reliable than WiFi

4. **Increase buffering**:
   - Addon config > Adjust latency parameters
   - May help on congested networks

---

### Connection drops mid-stream

#### Symptom
- Playing fine, then stops
- "Disconnected" error in Music app
- Must reconnect AirPlay

#### Cause
Device or network timeout / connectivity loss.

#### Solution

1. **Check network stability**:
   ```bash
   # Ping Home Assistant continuously
   ping -c 30 home-assistant-ip
   
   # Look for: "% packet loss"
   # >5% loss indicates network issue
   ```

2. **Check Echo device**:
   - Alexa app > Check device status
   - Should show "Online"
   - If Offline, restart device

3. **Check Amazon API connectivity**:
   - Logs for: "API error" or "timeout"
   - Rate limiting possible
   - Wait 60 seconds and retry

4. **Increase connection timeout**:
   - Addon advanced config
   - Set longer timeout/keepalive
   - May help with unreliable networks

---

## Category: Performance Issues

### Slow response to controls

#### Symptom
- Play/pause takes 2+ seconds
- Volume adjustment laggy
- Skip/next delayed

#### Cause
Network latency or addon resource constrained.

#### Solution

1. **Check network latency**:
   ```bash
   # Time request to addon
   time curl http://localhost:8000/api/devices > /dev/null
   
   # Should be <200ms
   # If >500ms, network issue
   ```

2. **Use wired Ethernet**:
   - WiFi has higher latency
   - Connect Home Assistant via cable
   - Much more responsive

3. **Check Home Assistant CPU**:
   - Settings > System > Diagnostics
   - CPU usage should be <50% normally
   - If >80%, disable other addons

4. **Check memory usage**:
   - Addon should use <200MB
   - If higher, memory leak
   - Restart addon

5. **Check Amazon API**:
   - Rate limiting may slow requests
   - Check logs for rate limit errors
   - Wait between commands

---

### High memory usage / Memory leak

#### Symptom
- Addon uses 200MB+ RAM
- Grows over time
- Eventually crashes

#### Solution

1. **Check current usage**:
   ```bash
   # Check addon memory
   docker stats ha-addon-alexa-airplay
   ```

2. **Identify leak source**:
   - Enable debug logging
   - Check logs for patterns
   - Note memory growth rate

3. **Restart addon** (temporary):
   - Clears memory
   - Fixes immediately (until leak grows again)
   - Stop addon
   - Wait 10 seconds
   - Start addon

4. **Report bug** if leak persists:
   - Include: memory usage over time graph
   - Include: logs with debug enabled
   - Include: steps to reproduce
   - Open issue on GitHub

---

## Category: Configuration Issues

### Web UI not loading

#### Symptom
- Cannot access http://your-ip:8000
- Page times out or refuses connection

#### Solution

1. **Check addon running**:
   - Home Assistant > Add-ons > Status should be green
   - If not running, start addon

2. **Check port 8000 accessible**:
   ```bash
   curl -v http://localhost:8000
   # Should connect (not refuse)
   ```

3. **Check firewall**:
   ```bash
   # Allow port 8000
   sudo ufw allow 8000/tcp
   
   # Verify
   sudo ufw status
   ```

4. **Check if port in use**:
   ```bash
   netstat -tuln | grep 8000
   
   # If shows LISTENING on different IP
   # Addon bound to wrong interface
   ```

5. **Try different machine**:
   - From another computer on network
   - Try: http://addon-hostname:8000
   - If works, network/DNS issue on first device

---

### Configuration won't save

#### Symptom
- Enter Client ID/Secret
- Click Save
- Nothing happens or error

#### Solution

1. **Check for validation errors**:
   - Browser console (F12)
   - Look for JavaScript errors
   - Try different browser

2. **Verify input format**:
   - Client ID should contain: `amzn1.application-`
   - No spaces before/after
   - Valid characters only

3. **Check permissions**:
   ```bash
   # Config directory writable
   ls -la /data/config/
   
   # Should show: drwxr-xr-x
   ```

4. **Manual config entry**:
   ```bash
   # SSH into Home Assistant
   cat > /data/config/config.json << EOF
   {
     "amazon_client_id": "your-id",
     "amazon_client_secret": "your-secret",
     "airplay_port": 5000
   }
   EOF
   
   # Restart addon
   ```

---

## Getting Help

### Collect Diagnostics

Before reporting issue, gather:

1. **Addon logs** (full output):
   - Home Assistant > Add-ons > Amazon Echo AirPlay Bridge
   - Click Logs
   - Select all, copy
   - Save to text file

2. **System info**:
   - Home Assistant version
   - Addon version
   - System type (RPi model, CPU, RAM, etc.)
   - Network type (WiFi/Ethernet)

3. **Reproduction steps**:
   - Exact steps to reproduce issue
   - Expected vs actual result
   - When it started happening

4. **Remove sensitive info**:
   - Remove Client ID/Secret
   - Remove OAuth tokens
   - Remove Amazon device IDs

### Report Issue

1. Check [existing issues](https://github.com/yourusername/alexa-airplay-addon/issues)
2. If similar found, add comment with your info
3. If new, click "New Issue"
4. Include:
   - Title: Brief description
   - Description: What's happening
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Logs (sanitized)
   - System info

### Community Help

- Check [Discussions](https://github.com/yourusername/alexa-airplay-addon/discussions)
- Search for similar issues
- Ask in Home Assistant Discord

---

## Quick Reference

### Emergency Reset

If addon broken and won't start:

```bash
# SSH into Home Assistant
ssh root@your-ha-ip

# Remove addon config (WARNING: loses settings)
rm -rf /usr/share/hassio/addons/alexa-airplay-addon/data/*

# Restart addon
ha addons restart alexa-airplay

# Reconfigure from Web UI
```

### Useful Commands

```bash
# View live logs
docker logs -f ha-addon-alexa-airplay

# Restart addon
docker restart ha-addon-alexa-airplay

# Check resources
docker stats ha-addon-alexa-airplay

# Enter addon shell
docker exec -it ha-addon-alexa-airplay bash

# Check addon file permissions
docker exec ha-addon-alexa-airplay \
  ls -la /data/config

# View all addon processes
docker top ha-addon-alexa-airplay
```

---

**Still stuck?** Open an [issue](https://github.com/yourusername/alexa-airplay-addon/issues) with diagnostics attached!
