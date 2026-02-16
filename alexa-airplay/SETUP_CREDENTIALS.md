# Amazon Credentials Setup Guide

## Overview
The Alexa AirPlay Bridge addon uses Login with Amazon (LWA) OAuth to access your Echo devices. You'll need to create an Amazon Developer security profile and configure it in the addon.

## Step 1: Create an Amazon Developer Account
1. Go to [Amazon Developer Console](https://developer.amazon.com/)
2. Click "Sign In" and create an account or log in
3. Accept any terms of service

## Step 2: Create a Security Profile
1. Go to [AVS Developer Console](https://developer.amazon.com/en-US/alexa/console/ask)
2. Click "Create Skill" or navigate to "Products" → "Create Product"
3. Choose a name for your skill (e.g., "Alexa AirPlay Bridge")
4. Select the appropriate product type
5. In the security profile section:
   - Click "Create a new profile"
   - Enter a profile name
   - Accept the terms and create

## Step 3: Get Your Credentials
1. From the security profile, go to **Settings**
2. Under **Client ID and Client Secret**, you'll find:
   - **Client ID**: Copy this
   - **Client Secret**: Click "Show" and copy this
   
## Step 4: Set Up the Addon
### Option A: Through Home Assistant UI (Recommended)
1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Alexa AirPlay Bridge**
3. Click the **Configuration** card at the top of the page
4. Enter:
   - **Client ID**: Paste your Client ID from step 3
   - **Client Secret**: Paste your Client Secret from step 3
   - **OAuth Redirect URI**: This is auto-filled - copy it
5. Click "Save Configuration"

### Option B: Through the Web UI
1. Open the Alexa AirPlay Bridge Web UI
2. Scroll to the **Amazon Configuration** section
3. Enter your Client ID and Client Secret
4. Copy the **OAuth Redirect URI** (pre-filled)
5. Click "💾 Save Configuration"

## Step 5: Register the Redirect URI
1. Go back to [Amazon Developer Console](https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit/register-a-product-and-create-security-profile.html)
2. Find your security profile → **Settings**
3. Under **Web Settings**, enter your **Allowed Return URLs**:
   - Add the OAuth Redirect URI from Step 4
   - If using Home Assistant Ingress: `https://home.garrettorick.com/api/hassio_ingress/iw_xxxxxxxxxxxx/oauth/callback`
   - If local only: `http://localhost:8000/oauth/callback`
4. **Save**

## Step 6: Authorize the Addon
1. Restart the Alexa AirPlay Bridge addon
2. Open the addon Web UI
3. Click "🔐 Authorize Amazon" button
4. Log in with your Amazon account
5. Grant permissions to the addon
6. You should see "Authorization Successful!" message

## Troubleshooting

**"Authorization failed: Unexpected non-whitespace character after JSON"**
- Make sure the OAuth Redirect URI in Amazon Developer Console **exactly** matches the one in the addon configuration

**"400 Bad Request" from Amazon**
- Verify the redirect URI is registered in your security profile's "Allowed Return URLs"
- Check that there are no extra spaces or special characters

**"No devices found"**
- Make sure you're authorized
- Your Amazon account must have at least one Echo device
- Ensure the addon has internet access to reach Amazon's API

## Security Notes
- Your Client Secret is sensitive - never share it or commit it to version control
- The addon stores credentials locally in encrypted Home Assistant storage
- OAuth tokens are refreshed automatically as needed

