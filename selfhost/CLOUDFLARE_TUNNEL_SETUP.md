# Cloudflare Tunnel Setup Guide - OSS+ Self-Hosted

## 📚 Overview

Cloudflare Tunnel allows you to expose your local OSS+ stack to the internet **without opening ports** on your firewall.

**This is OPTIONAL** - you can continue using local IP access without it.

## 🚀 Quick Start

### Step 1: Get Cloudflare Tunnel Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Select "Edit Cloudflared config" template
4. Authorize and copy the token

### Step 2: Configure .env

```bash
cd selfhost/
cp .env.example .env
```

Edit `.env` and add your token:
```env
CLOUDFLARE_TUNNEL_TOKEN=your_token_here
```

### Step 3: Start with Tunnel

```bash
# Start all services with Cloudflare Tunnel
docker compose --profile tunnel up -d

# View logs to get your public URL
docker logs omi-cloudflare-tunnel
```

### Step 4: Update App Configuration

Once tunnel is running, you'll see a URL like:
```
https://your-tunnel-url.trycloudflare.com
```

**Update your Flutter app's API URL** to this tunnel URL.

## 🔧 Usage Modes

### MODE 1: Local IP (Default - No Tunnel)

**Use this for local development:**

```bash
# Start services WITHOUT tunnel
docker compose up -d

# Your API is at:
# http://<YOUR_LOCAL_IP>:8000
```

**In Flutter app .env:**
```env
API_BASE_URL=http://192.168.1.50:8000
```

**Requirements:**
- ✅ Phone on same WiFi
- ✅ No firewall blocking
- ✅ Simple setup

---

### MODE 2: Cloudflare Tunnel (Public URL)

**Use this for:**
- Remote testing
- Public deployment
- Different networks
- Production use

```bash
# Start with tunnel enabled
docker compose --profile tunnel up -d

# Wait for tunnel to start (30-60 seconds)
docker logs omi-cloudflare-tunnel
```

**In Flutter app .env:**
```env
API_BASE_URL=https://your-tunnel-url.trycloudflare.com
```

**Requirements:**
- ✅ Cloudflare account (free)
- ✅ Valid tunnel token
- ✅ Works from anywhere

---

## 🛑 Troubleshooting

### Tunnel not starting?

```bash
# Check logs
docker logs omi-cloudflare-tunnel

# Verify token is valid
echo $CLOUDFLARE_TUNNEL_TOKEN

# Restart tunnel
docker restart omi-cloudflare-tunnel
```

### Can't reach the tunnel URL?

```bash
# Test PostgREST is running
curl http://localhost:8000/

# Check tunnel is connected
docker ps | grep cloudflare
```

### Getting 502 errors?

The tunnel container might need time to initialize:
```bash
# Wait 30 seconds and try again
sleep 30
curl https://your-tunnel-url.trycloudflare.com
```

## 📱 Flutter App Configuration

**For LOCAL IP:**
```dart
// lib/env/dev_env.dart
const apiBaseUrl = 'http://192.168.1.50:8000';
```

**For CLOUDFLARE TUNNEL:**
```dart
// lib/env/prod_env.dart  
const apiBaseUrl = 'https://your-tunnel-url.trycloudflare.com';
```

Or set it via `.prod.env` file and use `Env.apiBaseUrl`

## 🔐 Security Notes

- ✅ Cloudflare Tunnel encrypts all traffic
- ✅ No ports exposed on your router
- ✅ Token is for tunnel only (limited scope)
- ❌ Don't commit `.env` with your token to git
- 🔑 Add `.env` to `.gitignore`

## 📞 Support

For Cloudflare Tunnel issues:
- https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

For OSS+ support:
- Check project documentation
