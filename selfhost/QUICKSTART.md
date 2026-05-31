# 🚀 Omi OSS+ Quick Start Guide

Complete guide to running the Omi OSS+ stack locally with Docker Compose.

## Prerequisites

### Windows 10
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- PowerShell 5.0+ (usually pre-installed)
- 8GB+ RAM recommended
- WSL 2 backend enabled

### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Enable docker without sudo (optional)
sudo usermod -aG docker $USER
newgrp docker
```

### macOS
- [Docker Desktop for macOS](https://www.docker.com/products/docker-desktop)
- 8GB+ RAM recommended

## Quick Start

### Windows 10

```powershell
# Navigate to selfhost directory
cd selfhost

# Make scripts executable (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Start OSS+ stack
.\start-ossp.ps1

# In another PowerShell window, view logs
.\logs-ossp.ps1

# Stop services
.\stop-ossp.ps1
```

### Linux / macOS

```bash
# Navigate to selfhost directory
cd selfhost

# Make scripts executable (first time only)
chmod +x start-ossp.sh stop-ossp.sh logs-ossp.sh

# Start OSS+ stack
./start-ossp.sh

# In another terminal, view logs
./logs-ossp.sh

# Stop services
./stop-ossp.sh
```

## What Gets Started

The `docker-compose.yml` starts these services:

| Service | Port | Purpose |
|---------|------|---------|
| **PostgreSQL/Supabase** | 5432, 8000, 3000 | Database + API + Studio UI |
| **Qdrant** | 6333 | Vector similarity search |
| **MinIO** | 9000, 9001 | S3-compatible object storage |
| **Faster-Whisper** | 8001, 8002 | Speech-to-text (HTTP + WebSocket) |
| **Ollama** | 11434 | Local LLM inference |
| **Redis** | 6379 | Caching layer |

## Service URLs

### Development Dashboards
- **Supabase Studio**: http://localhost:3000
- **MinIO Console**: http://localhost:9001

### APIs
- **PostgREST**: http://localhost:8000
- **Qdrant**: http://localhost:6333
- **Faster-Whisper**: http://localhost:8001
- **Ollama**: http://localhost:11434
- **Redis**: localhost:6379

### Direct Database Access
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d omi

# Default password: postgres (change in .env)
```

## Configuration

### Automatic .env Generation

When you first run `start-ossp.sh` or `start-ossp.ps1`, it automatically:
1. Copies `.env.template` to `.env`
2. Generates secure random secrets for:
   - JWT token signing
   - Data encryption
3. Sets default credentials for services

### Manual Configuration

Edit `.env` to customize:

```bash
# Database
DB_PASSWORD=your-secure-password
DB_HOST=localhost

# Supabase
SUPABASE_URL=http://localhost:8000

# MinIO Storage
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your-password

# Faster-Whisper
WHISPER_MODEL=base|small|medium|large
WHISPER_DEVICE=cpu|cuda|metal

# Ollama LLM
OLLAMA_MODEL=llama2|mistral|neural-chat
OLLAMA_BASE_URL=http://localhost:11434

# Backend API
OMI_DB_BACKEND=supabase
OMI_AUTH_BACKEND=supabase
OMI_STORAGE_BACKEND=minio
```

## Database Migrations

After starting for the first time, run migrations:

### Linux/macOS
```bash
# Run all migrations in order
for file in ./supabase/migrations/00*.sql; do
  psql -h localhost -U postgres -d omi -f "$file"
done
```

### Windows (PowerShell)
```powershell
Get-ChildItem ./supabase/migrations/00*.sql | ForEach-Object {
  & psql -h localhost -U postgres -d omi -f $_.FullName
}
```

Or use Supabase Studio UI:
1. Go to http://localhost:3000
2. Login with default credentials (check `.env`)
3. Run SQL in the editor

## Script Usage

### start-ossp.sh / start-ossp.ps1

**Windows:**
```powershell
.\start-ossp.ps1              # Start and follow logs
.\start-ossp.ps1 -NoLogs      # Start without logs
.\start-ossp.ps1 -Help        # Show help
```

**Linux/macOS:**
```bash
./start-ossp.sh               # Start and follow logs
./start-ossp.sh --no-logs     # Start without logs
./start-ossp.sh --help        # Show help
```

### stop-ossp.sh / stop-ossp.ps1

**Windows:**
```powershell
.\stop-ossp.ps1               # Stop containers (keep data)
.\stop-ossp.ps1 -Remove       # Stop and delete volumes
.\stop-ossp.ps1 -Help         # Show help
```

**Linux/macOS:**
```bash
./stop-ossp.sh                # Stop containers (keep data)
./stop-ossp.sh --remove       # Stop and delete volumes
./stop-ossp.sh --help         # Show help
```

### logs-ossp.sh / logs-ossp.ps1

**Windows:**
```powershell
.\logs-ossp.ps1                           # Show all logs
.\logs-ossp.ps1 -Service supabase         # Show Supabase logs
.\logs-ossp.ps1 -Service ollama -Follow   # Follow Ollama logs
.\logs-ossp.ps1 -Lines 50                 # Show last 50 lines
```

**Linux/macOS:**
```bash
./logs-ossp.sh                            # Show all logs
./logs-ossp.sh -s supabase                # Show Supabase logs
./logs-ossp.sh -s ollama -f               # Follow Ollama logs
./logs-ossp.sh -n 50                      # Show last 50 lines
```

**Available services:** supabase, qdrant, minio, faster-whisper, ollama, redis

## Health Checks

### Check Service Status

**Windows:**
```powershell
docker compose -f docker-compose.yml ps
```

**Linux/macOS:**
```bash
docker-compose -f docker-compose.yml ps
```

### Manual Health Checks

```bash
# Database
psql -h localhost -U postgres -c "SELECT 1"

# Qdrant
curl http://localhost:6333/health

# MinIO
curl http://localhost:9000/minio/health/live

# Faster-Whisper
curl http://localhost:8001/health

# Ollama
curl http://localhost:11434/api/tags

# Redis
redis-cli -h localhost ping
```

## Troubleshooting

### Services won't start

**Check Docker daemon:**
```bash
docker ps
docker logs omi-supabase
```

**Restart Docker:**
- Windows: Restart Docker Desktop
- Linux: `sudo systemctl restart docker`

### Port conflicts

If ports are already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead of 5432
```

Then update `.env`:
```bash
DB_PORT=5433
```

### Out of disk space

Clean up Docker:
```bash
docker system prune -a
```

Or remove old volumes:
```bash
# Windows
.\stop-ossp.ps1 -Remove

# Linux/macOS
./stop-ossp.sh --remove
```

### Services slow or crashing

**Allocate more resources:**
- Docker Desktop Settings → Resources
- Increase CPU and RAM allocation

**Check logs:**
```bash
# Windows
.\logs-ossp.ps1 -Service ollama -Follow

# Linux/macOS
./logs-ossp.sh -s ollama -f
```

## Building the Omi App

With OSS+ running, build the Android APK:

```bash
cd ../app
flutter build apk --flavor dev
```

Configure the app to point to your local OSS+ instance:
- Set `API_BASE_URL=http://<your-ip>:8080`
- Enable `OMI_DB_BACKEND=supabase` mode
- Configure Supabase URL in onboarding wizard

## Production Deployment

For production, see:
- [OSSP_IMPLEMENTATION.md](../OSSP_IMPLEMENTATION.md) - Technical overview
- [OSS_REMAINING_TASKS.md](../OSS_REMAINING_TASKS.md) - What's still needed
- [README_OSSP.md](../README_OSSP.md) - Full documentation

## Data Persistence

All data is stored in Docker volumes:
- `supabase_data` - PostgreSQL database
- `qdrant_data` - Vector DB
- `minio_data` - Object storage
- `ollama_data` - LLM models
- `whisper_models` - Whisper model cache
- `redis_data` - Cache data

**Important**: Running `stop-ossp.sh --remove` deletes these volumes!

To backup data:
```bash
# Create backup
docker run --rm -v supabase_data:/data -v $(pwd):/backup alpine tar czf /backup/supabase-backup.tar.gz /data

# Restore backup
docker run --rm -v supabase_data:/data -v $(pwd):/backup alpine tar xzf /backup/supabase-backup.tar.gz -C /
```

## Building and Installing the Android App

### 1. Set Up Flutter 3.35.3

The Android build requires Flutter 3.35.3 for compatibility with font_awesome_flutter.

**Windows (PowerShell)**:
```powershell
$env:Path = "C:\Users\shinsekai\development\flutter\bin;" + $env:Path
```

**Linux/macOS**:
```bash
export PATH="/path/to/flutter-3.35.3/bin:$PATH"
```

### 2. Build the APK

```bash
cd app
flutter clean
flutter pub get
flutter build apk --flavor dev
```

Output: `app/build/app/outputs/flutter-apk/app-dev-release.apk`

### 3. Install on Android Device

**Using ADB**:
```bash
# Connect device via USB and enable USB debugging
adb devices                 # Verify connection
adb install app/build/app/outputs/flutter-apk/app-dev-release.apk
```

**Or copy to device manually**:
- Transfer APK via USB, email, or cloud storage
- Open file on device to install

### 4. Configure OSS+ Mode

Launch the app and follow the onboarding:

1. Select "OSS+ Self-Hosted" mode
2. Enter server address: `<your-ip>:8080`
3. Complete setup wizard

**Finding your server IP**:
```powershell
# Windows
ipconfig

# Linux/macOS
hostname -I
```

### Complete OSS+ Setup Workflow

```bash
# 1. Start infrastructure
./start-ossp.sh              # Linux/macOS
# or
.\start-ossp.ps1            # Windows

# 2. Wait for services to be healthy (~30 seconds)

# 3. Build Android APK
export PATH="/path/to/flutter-3.35.3/bin:$PATH"  # Set Flutter path
cd ../app
flutter build apk --flavor dev

# 4. Install on device
adb install build/app/outputs/flutter-apk/app-dev-release.apk

# 5. Launch app and configure OSS+ mode
# Enter your server IP when prompted in the app

# 6. Check logs if needed
cd ../selfhost
.\logs-ossp.ps1             # Windows
./logs-ossp.sh              # Linux/macOS
```

## Troubleshooting

**Flutter build fails with "IconData" error**:
- Ensure Flutter 3.35.3 is in PATH
- Run: `flutter --version` (should show 3.35.3)

**APK installation fails**:
- Check Android version (5.0+ required)
- Verify USB debugging is enabled
- Try: `adb uninstall com.friend.ios.dev` then reinstall

**App can't connect to backend**:
- Verify services are running: `docker compose ps`
- Test connectivity: `curl http://<your-ip>:8000`
- Check device is on same network or has access to server

**App crashes on startup**:
- View logs: `adb logcat | grep -i omi`
- Ensure Supabase is healthy: `.\logs-ossp.ps1 -Service postgres`

## Next Steps

1. ✅ Start OSS+ stack: `start-ossp.sh` / `start-ossp.ps1`
2. ✅ Run database migrations
3. ✅ Build and install Android APK
4. ✅ Configure the Omi app to use local OSS+
5. ✅ Check [README_OSSP.md](../README_OSSP.md) for features and configuration

## Support

For issues:
1. Check logs: `logs-ossp.sh` / `logs-ossp.ps1`
2. Read [OSSP_IMPLEMENTATION.md](../OSSP_IMPLEMENTATION.md)
3. Open a GitHub issue with logs and error messages

---

**Happy self-hosting! 🎉**
