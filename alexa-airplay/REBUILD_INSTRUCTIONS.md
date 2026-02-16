# Rebuilding the Addon After Code Changes

The 405 Method Not Allowed error means the running addon container is using old code that doesn't have the configuration endpoints properly set up.

## Quick Fix: Rebuild the Addon

To apply the latest code changes to your running addon, follow these steps:

### Option 1: Rebuild Using Local Repository (Recommended for Development)

1. In Home Assistant, go to **Settings → System → Developer Tools → Terminal** (via SSH Add-on)

2. Run:
```bash
cd /data/addons/ha-alexa-airplay-addon  # or your addon repository path
git pull origin main
ha addon update ha_alexa_airplay_addon
ha addon restart ha_alexa_airplay_addon
```

3. Wait 1-2 minutes for the addon to restart with the new code

### Option 2: Force Rebuild via Home Assistant UI

1. Go to **Settings → Add-ons → My add-ons → Alexa AirPlay Bridge**
2. Click the **three dots menu** and select **Rebuild**
3. Wait for the build to complete, then restart the addon

### Option 3: Rebuild from Source (If using the repository)

If you added the repo to Home Assistant:

1. Go to **Settings → Add-ons → Add-on Store** (or **three dots > Repositories**)
2. Search for "Alexa AirPlay" 
3. Click **Install**
4. Open the addon page
5. Click **Rebuild** (or the gear icon → **Rebuild**)
6. Wait for rebuild and restart

## What Changed

These commits fix the configuration saving issue:

- **202af90**: Improved error handling to show actual server errors
- **13b6522**: Added missing `amazon_redirect_uri` field to config response

The problem was:
1. The `/api/config` POST endpoint wasn't returning all required fields
2. Error messages weren't clear when something went wrong

## After Rebuild

Once the addon rebuilds and restarts:

1. Go to the addon's Web UI
2. Enter your Amazon credentials:
   - **Client ID**: From [Amazon Developer Console](https://developer.amazon.com)
   - **Client Secret**: From same console
   - **Redirect URI**: Copy the read-only value from the form to your Amazon Developer Console
3. Click **Save Configuration**
4. Click **Authorize Amazon**

## Troubleshooting

If you still get errors after rebuilding:

1. Check the addon logs: **Settings → Add-ons → Alexa AirPlay Bridge → Logs**
2. Look for any Python errors related to config saving
3. Ensure the `/data/config` directory exists and is writable

## Alternative: Inject Credentials Directly

If rebuilding doesn't work, you can manually create the config file:

```bash
cat > /data/config/config.json << 'EOF'
{
  "amazon_client_id": "amzn1.application-oa2-client.YOUR_CLIENT_ID",
  "amazon_client_secret": "YOUR_CLIENT_SECRET",
  "amazon_redirect_uri": "https://home.garrettorick.com/api/hassio_ingress/YOUR_INGRESS_TOKEN/oauth/callback",
  "airplay_port": 5001,
  "web_port": 8000,
  "ha_url": "http://supervisor"
}
EOF
```

Then restart the addon.
