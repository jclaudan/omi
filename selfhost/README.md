# 🏠 Omi Self-Hosted (OSS+) Setup

Complete infrastructure for running Omi entirely self-hosted with open-source components.

## 📋 Contents

### Directory Structure
```
selfhost/
├── docker-compose.yml          # Complete OSS+ stack definition
├── .env.template              # Configuration template
├── start-ossp.ps1            # Windows: Start services
├── start-ossp.sh             # Linux/macOS: Start services
├── stop-ossp.ps1             # Windows: Stop services
├── stop-ossp.sh              # Linux/macOS: Stop services
├── logs-ossp.ps1             # Windows: View logs
├── logs-ossp.sh              # Linux/macOS: View logs
├── supabase/
│   ├── migrations/           # PostgreSQL schema migrations
│   └── rls-policies/         # Row-level security policies
├── QUICKSTART.md             # 5-minute setup guide
└── README.md                 # This file
```

## 🚀 Quick Start

### Windows 10
```powershell
cd selfhost
.\start-ossp.ps1
```

### Linux / macOS
```bash
cd selfhost
./start-ossp.sh
```

For detailed setup: [**QUICKSTART.md**](./QUICKSTART.md)

## 📦 Services Included

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| **Supabase** | supabase/supabase:latest | PostgreSQL DB + API | 5432, 8000, 3000 |
| **Qdrant** | qdrant/qdrant:latest | Vector similarity search | 6333 |
| **MinIO** | minio/minio:latest | S3-compatible storage | 9000, 9001 |
| **Faster-Whisper** | faster-whisper-server | Speech-to-text | 8001, 8002 |
| **Ollama** | ollama/ollama:latest | Local LLM inference | 11434 |
| **Redis** | redis:7-alpine | Caching layer | 6379 |

## 🔧 Available Commands

### Start OSS+
```bash
# Windows
.\start-ossp.ps1 [-NoLogs]

# Linux/macOS
./start-ossp.sh [--no-logs]
```
Automatically generates `.env` with secure defaults on first run.

### Stop OSS+
```bash
# Windows
.\stop-ossp.ps1 [-Remove]

# Linux/macOS
./stop-ossp.sh [--remove]
```
Use `-Remove` to delete volumes (caution: deletes all data).

### View Logs
```bash
# Windows
.\logs-ossp.ps1 [-Service supabase] [-Lines 100] [-Follow]

# Linux/macOS
./logs-ossp.sh [-s supabase] [-n 100] [-f]
```
Available services: supabase, qdrant, minio, faster-whisper, ollama, redis

## 🌐 Service URLs

### Administration
- **Supabase Studio**: http://localhost:3000 (Database UI)
- **MinIO Console**: http://localhost:9001 (Storage UI)

### APIs
- **PostgREST**: http://localhost:8000 (Database REST API)
- **Qdrant**: http://localhost:6333 (Vector DB API)
- **Faster-Whisper**: http://localhost:8001 (STT API)
- **Ollama**: http://localhost:11434 (LLM API)

### Databases
- **PostgreSQL**: localhost:5432 (use `psql` client)
- **Redis**: localhost:6379 (use `redis-cli` client)

## 📝 Configuration

### Automatic
When you first run the start script:
1. Creates `.env` from `.env.template`
2. Generates secure random secrets:
   - JWT tokens for Supabase
   - Encryption keys for data protection
3. Sets reasonable defaults for all services

### Manual
Edit `.env` to customize:
```bash
# Database password
DB_PASSWORD=your-secure-password

# Storage credentials
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your-password

# LLM model
OLLAMA_MODEL=llama2|mistral|neural-chat

# Speech-to-text model
WHISPER_MODEL=base|small|medium|large

# Backend API
API_BASE_URL=http://your-server:8080
```

## 🗄️ Database Migrations

Run migrations after first startup:

### Windows (PowerShell)
```powershell
Get-ChildItem ./supabase/migrations/00*.sql | ForEach-Object {
  & psql -h localhost -U postgres -d omi -f $_.FullName
}
```

### Linux/macOS
```bash
for file in ./supabase/migrations/00*.sql; do
  psql -h localhost -U postgres -d omi -f "$file"
done
```

Or use Supabase Studio UI at http://localhost:3000

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│           Omi Mobile App / Web UI               │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │  Backend API       │
        │  (Python/FastAPI)  │
        └─┬───────────────────┘
          │
    ┌─────┴──────────┬──────────────┬──────────────┐
    │                │              │              │
┌───▼────┐    ┌─────▼────┐  ┌─────▼────┐  ┌─────▼────┐
│Supabase│    │  Qdrant  │  │  MinIO   │  │Faster-   │
│ (DB)   │    │(Vectors) │  │(Storage) │  │Whisper   │
└────┬────┘    └──────────┘  └──────────┘  └─────┬────┘
     │                                           │
     │         ┌─────────────────────────┐       │
     │         │  Ollama (Local LLM)     │       │
     │         └─────────────────────────┘       │
     │                                           │
┌────▼─────────────────────────────────────────▼───┐
│        PostgreSQL + Encryption at Rest           │
│        Redis Cache + Row-Level Security          │
└──────────────────────────────────────────────────┘
```

## 🔐 Security Features

### Row-Level Security (RLS)
- Users can only access their own data
- Database enforces policies at table level
- See `supabase/rls-policies/` for details

### Encryption at Rest
- Messages encrypted with AES-256-GCM
- Per-user encryption keys (HKDF-SHA256)
- Enable with `DATA_PROTECTION_LEVEL=enhanced`

### Network Security
- All services on isolated Docker network
- No direct internet exposure
- Use firewall rules for production

## 💾 Data Persistence

Data is stored in Docker named volumes:
- `supabase_data` - PostgreSQL database files
- `qdrant_data` - Vector DB indexes
- `minio_data` - Object storage
- `ollama_data` - LLM models
- `whisper_models` - Speech-to-text models
- `redis_data` - Cache data

**Backing up data:**
```bash
docker run --rm -v supabase_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz /data
```

**Restoring data:**
```bash
docker run --rm -v supabase_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/backup.tar.gz -C /
```

## ⚙️ Resource Requirements

### Minimum (Development)
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB SSD

### Recommended (Testing)
- CPU: 4-8 cores
- RAM: 16GB
- Disk: 100GB SSD

### Production
- CPU: 16+ cores
- RAM: 64GB+
- Disk: 500GB+ SSD
- GPU: For Ollama acceleration (optional)

## 🐛 Troubleshooting

### Services won't start
1. Check Docker is running: `docker ps`
2. View logs: `./logs-ossp.sh` (or `.\logs-ossp.ps1`)
3. Verify ports aren't in use: `netstat -an | grep LISTEN`

### Port conflicts
Edit `docker-compose.yml` to use different ports:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead of 5432
```

### Out of disk space
```bash
docker system prune -a      # Clean unused images
docker volume prune         # Clean unused volumes
```

### Services are slow
- Allocate more RAM in Docker Desktop settings
- Check disk I/O: `docker stats`
- Review service logs for errors

## 📚 Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute setup guide
- **[OSSP_IMPLEMENTATION.md](../OSSP_IMPLEMENTATION.md)** - Technical architecture
- **[README_OSSP.md](../README_OSSP.md)** - Complete feature guide
- **[APK_BUILD_STATUS.md](../APK_BUILD_STATUS.md)** - Mobile app build info

## 🔄 Common Workflows

### First-time setup
```bash
./start-ossp.sh              # Start all services
# Run migrations via Supabase Studio UI
# Configure Omi app to point to http://localhost:8080
```

### Development work
```bash
./start-ossp.sh --no-logs    # Start in background
./logs-ossp.sh -s supabase   # Check specific service
# Make changes
./logs-ossp.sh -s backend -f # Follow backend logs
```

### Cleanup & restart
```bash
./stop-ossp.sh               # Stop services (keep data)
# Debug, make changes
./start-ossp.sh              # Start again
```

### Full reset
```bash
./stop-ossp.sh --remove      # Delete everything
# Remove .env
./start-ossp.sh              # Fresh start with new .env
```

## 🚢 Deployment

For production deployment:
1. Read [OSSP_IMPLEMENTATION.md](../OSSP_IMPLEMENTATION.md)
2. Use environment-specific configurations
3. Set up:
   - SSL/TLS certificates (nginx reverse proxy)
   - Database backups (pg_dump)
   - Monitoring (Prometheus/Grafana)
   - High availability setup

## 📞 Support

Need help?
1. Check [QUICKSTART.md](./QUICKSTART.md)
2. View service logs: `./logs-ossp.sh`
3. Search [OSSP_IMPLEMENTATION.md](../OSSP_IMPLEMENTATION.md)
4. Open a GitHub issue with logs and details

## 📜 License

Omi is open source. See LICENSE file in repository root.

---

**Ready to self-host Omi? Start with [QUICKSTART.md](./QUICKSTART.md)! 🚀**
