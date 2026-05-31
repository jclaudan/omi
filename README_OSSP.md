# 🚀 Omi OSS+ — Open Source Self-Hosted Edition

> **Omi without the cloud dependencies.** Run Omi completely self-hosted with Supabase, Qdrant, MinIO, and Ollama. Full privacy, full control, zero proprietary APIs required.

## What is OSS+?

OSS+ (Open Source+) is a fully self-hosted alternative to Omi Cloud that replaces all proprietary services with open-source equivalents:

| Component | Cloud Mode | OSS+ Mode |
|-----------|-----------|-----------|
| **Database** | Firebase | Supabase (PostgreSQL) |
| **Authentication** | Firebase Auth | Supabase JWT |
| **Storage** | Google Cloud Storage | MinIO (S3-compatible) |
| **Vector Search** | Pinecone | Qdrant |
| **Speech-to-Text** | Deepgram API | Faster-Whisper (self-hosted) |
| **LLM** | OpenAI/Gemini/Claude | Ollama (local) or any OpenAI-compatible |

**Result**: Zero cloud API keys required. Full data ownership. Complete privacy. Run entirely on your infrastructure.

---

## 🎯 Key Features

✅ **Same Features as Cloud Mode**
- Voice recording & transcription
- AI-powered conversation analysis
- Memory extraction & search
- Goal tracking & progress
- App marketplace
- Chat with custom apps
- Daily summaries
- Full encryption support

✅ **Self-Hosted Advantages**
- All data stays on your servers
- No API rate limits
- No monthly subscription costs
- Customizable and extensible
- GDPR/compliance friendly
- No vendor lock-in

✅ **Open Source Stack**
- PostgreSQL (via Supabase)
- Qdrant (vector similarity search)
- MinIO (object storage)
- Faster-Whisper (speech recognition)
- Ollama (local LLM)
- All components can be swapped

---

## ⚡ Quick Start

### Prerequisites

- Docker & Docker Compose (or deploy manually)
- 8GB+ RAM recommended
- 50GB+ disk space (depending on usage)
- Linux/macOS/Windows with Docker

### 1. Clone & Setup

```bash
git clone https://github.com/jclaudan/omi.git
cd omi
git checkout feat/use-only-opensource-alternative

# Copy example env file
cp .env.template .env
```

### 2. Configure Environment

Edit `.env` with your settings:

```bash
# Mode selector
OMI_DB_BACKEND=supabase              # Enable OSS+ mode
OMI_AUTH_BACKEND=supabase            # Use Supabase auth
OMI_STORAGE_BACKEND=minio            # Use MinIO storage

# Supabase
SUPABASE_URL=http://localhost:8000   # Local Supabase instance
SUPABASE_ANON_KEY=<your-key>
SUPABASE_SERVICE_ROLE_KEY=<your-key>

# LLM (pick one)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
# Don't set OPENAI_API_KEY to force Ollama use

# Optional: keep for Cloud features
# OPENAI_API_KEY=...
# GEMINI_API_KEY=...
```

### 3. Start Services

```bash
# Full stack (coming soon)
docker-compose up -d

# Or use existing Docker setup
docker run -d \
  -e OMI_DB_BACKEND=supabase \
  -e OMI_AUTH_BACKEND=supabase \
  your-image:latest
```

### 4. Initialize Database

```bash
# Run migrations
psql -h localhost -U postgres -d omi < selfhost/supabase/migrations/001_profiles.sql
psql -h localhost -U postgres -d omi < selfhost/supabase/migrations/002_core_schema.sql
# ... run all migrations 001-014
```

### 5. Access the App

- **Mobile App**: Configure to point to your backend
- **Web Interface**: `http://localhost:3000` (if deployed)
- **API**: `http://localhost:8080`

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│           Mobile App / Web UI                   │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼─────────┐
         │  Backend API     │
         │  (FastAPI)       │
         └─┬────────────────┘
           │
     ┌─────┴──────────┬──────────────┬──────────────┐
     │                │              │              │
┌────▼────┐    ┌─────▼────┐   ┌─────▼────┐  ┌─────▼────┐
│Supabase │    │  Qdrant  │   │  MinIO   │  │Faster-   │
│(DB)     │    │(Vectors) │   │(Storage) │  │Whisper   │
└────┬────┘    └──────────┘   └──────────┘  └──────────┘
     │
┌────▼────────────────────────────────────────────┐
│        PostgreSQL + Encryption at Rest          │
└─────────────────────────────────────────────────┘

Optional:
┌──────────────────┐
│  Ollama (Local)  │
│  LLM Inference   │
└──────────────────┘
```

---

## 🔧 Configuration Reference

### Database (Supabase)

```bash
OMI_DB_BACKEND=supabase           # Enable Supabase mode
SUPABASE_URL=http://supabase:8000
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

**What's included**:
- PostgreSQL database
- PostgREST API
- Real-time subscriptions
- Row-level security (RLS)

### Authentication

```bash
OMI_AUTH_BACKEND=supabase         # Supabase JWT auth
```

**Default credentials**: Check your Supabase instance.

### Storage

```bash
OMI_STORAGE_BACKEND=minio         # MinIO object storage
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

**What's stored**:
- User conversation audio
- Photos from conversations
- Voice samples for speaker identification

### Vector Database (Qdrant)

```bash
QDRANT_URL=http://qdrant:6333     # Qdrant similarity search
```

**What's indexed**:
- Memory vectors (for semantic search)
- Conversation embeddings
- Action item summaries

### Speech-to-Text (Faster-Whisper)

```bash
FASTER_WHISPER_WS_URL=ws://faster-whisper-ws:8002  # Streaming
FASTER_WHISPER_URL=http://faster-whisper:8001      # Batch
```

**Models supported**:
- Tiny, small, medium, large (configurable)
- Multi-language support
- GPU acceleration (CUDA/Metal)

### LLM (Ollama or Cloud)

```bash
# Option 1: Local Ollama (recommended)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2

# Option 2: Cloud APIs (if you have keys)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
```

**When to use**:
- `llama3.2`: General-purpose, ~7GB VRAM
- `mistral:latest`: Faster, lower quality
- `neural-chat`: Optimized for conversations
- `openai/gpt-4-turbo`: Via OpenRouter API proxy

---

## 📋 Database Migrations

All schemas are in `selfhost/supabase/migrations/`:

```
001_profiles.sql           ← User profiles
002_core_schema.sql        ← Conversations, memories, etc.
003-008.sql               ← Additional features
009_chat.sql              ← Chat messages & sessions
010_apps.sql              ← App marketplace
011_daily_summaries.sql   ← Auto-generated summaries
012_goals.sql             ← Goal tracking
013_photos.sql            ← Conversation photos
014_phone_numbers.sql     ← Phone verification
```

**Run in order**:
```bash
for file in selfhost/supabase/migrations/*.sql; do
  psql -h localhost -d omi -f "$file"
done
```

---

## 🔒 Security & Privacy

### Encryption at Rest
- Message text encrypted with AES-256-GCM
- Per-user encryption keys (HKDF-SHA256)
- Phone numbers hashed for queryable lookup
- Enable with: `DATA_PROTECTION_LEVEL=enhanced`

### Row-Level Security (RLS)
- All tables have RLS enabled
- Users can only access their own data
- Supabase JWT validates access

### Network Security
- Use HTTPS in production
- Firewall rules to restrict database access
- VPC/network isolation recommended
- Never expose services to public internet

### Backup & Recovery
- Daily automated backups recommended
- Encryption keys must be backed up separately
- Point-in-time recovery via PostgreSQL WAL

---

## 📈 Performance & Scaling

### Hardware Recommendations

**Minimum (single-user/testing)**:
- 2 CPU cores
- 4GB RAM
- 20GB SSD

**Recommended (5-10 concurrent users)**:
- 4-8 CPU cores
- 16GB RAM
- 100GB SSD
- GPU for Ollama (optional, for faster inference)

**Production (50+ concurrent users)**:
- 16+ CPU cores
- 64GB+ RAM
- 500GB+ SSD (with backups)
- Dedicated GPU for Ollama
- Database replication setup
- Load balancer in front

### Optimization Tips

1. **Database**: Enable connection pooling (PgBouncer)
2. **Vector DB**: Use appropriate index types for Qdrant
3. **LLM**: Use quantized models for lower VRAM
4. **Storage**: Enable compression for MinIO
5. **Caching**: Use Redis for session/cache layer

---

## 🛠️ Troubleshooting

### Database Connection Refused
```bash
# Check Supabase is running
docker-compose ps | grep supabase

# Test connection
psql -h localhost -U postgres -d postgres -c "SELECT 1"
```

### LLM/Ollama Not Responding
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Pull a model if needed
curl -X POST http://localhost:11434/api/pull -d '{"name":"llama3.2"}'
```

### Storage (MinIO) Issues
```bash
# Check MinIO web UI
open http://localhost:9001

# Verify credentials
minio-client ls s3/omi/
```

### Vector Search (Qdrant) Issues
```bash
# Check Qdrant API
curl http://localhost:6333/health

# View collections
curl http://localhost:6333/collections
```

### Speech-to-Text Failures
```bash
# Check Faster-Whisper health
curl http://localhost:8001/health

# Test with audio file
curl -X POST -H "Content-Type: audio/wav" \
  --data-binary @test.wav \
  http://localhost:8001/transcribe
```

---

## 🚀 Deployment

### Docker Compose (Coming Soon)
```bash
cd docker
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/base/
# See k8s/ directory for full manifests
```

### Manual Deployment
See `SELFHOST_SETUP.md` for step-by-step instructions on any platform.

---

## 📚 Documentation

- **[OSSP_IMPLEMENTATION.md](./OSSP_IMPLEMENTATION.md)** — Complete technical overview
- **[OSS_REMAINING_TASKS.md](./OSS_REMAINING_TASKS.md)** — What's left to build
- **[SELFHOST_SETUP.md](./SELFHOST_SETUP.md)** — Deployment guide (coming soon)
- **[OSS_SECURITY.md](./OSS_SECURITY.md)** — Security hardening guide (coming soon)
- **[OSS_CONFIG.md](./OSS_CONFIG.md)** — Configuration reference (coming soon)

---

## 🔄 Migrating from Cloud to OSS+

If you have an existing Omi Cloud account, you can migrate your data:

```bash
# 1. Export your Cloud data (Firebase backup)
firebase firestore:export gs://your-bucket/omi-backup

# 2. Run migration script (coming soon)
python scripts/migrate/firestore_to_supabase.py \
  --firebase-backup gs://your-bucket/omi-backup \
  --supabase-url http://localhost:8000 \
  --supabase-key <your-key>

# 3. Validate migration
python scripts/migrate/verify.py
```

**Data migrated**:
- User profiles & settings
- Conversations & segments
- Memories & metadata
- Chat messages
- Goals & progress
- Apps & preferences

---

## 🤝 Contributing

OSS+ is part of the main Omi project. To contribute:

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Follow the coding guidelines in `AGENTS.md`
4. Test your changes in OSS+ mode
5. Submit a PR to `feat/use-only-opensource-alternative`

---

## 📄 License

Omi OSS+ is part of the Omi project. See LICENSE file for details.

---

## ❓ FAQ

**Q: Do I need to buy API keys?**  
A: No. All components are self-hosted and open-source. No recurring costs.

**Q: Can I run this on a Raspberry Pi?**  
A: Yes, but performance will be limited. Consider using smaller LLM models (tiny, small).

**Q: What if I want to use GPT-4 instead of Ollama?**  
A: Set `OPENAI_API_KEY=...` and the system will automatically use it for LLM features.

**Q: Can I use different LLMs for different features?**  
A: Yes. The factory pattern in `backend/utils/llm/clients.py` supports mixing providers.

**Q: Is my data encrypted?**  
A: Yes. Messages are encrypted with AES-256-GCM at rest. Enable with `DATA_PROTECTION_LEVEL=enhanced`.

**Q: Can I switch back to Cloud mode?**  
A: Yes. Just change `OMI_DB_BACKEND=firestore` and point to your Cloud services.

**Q: What about backups?**  
A: Use PostgreSQL native backups: `pg_dump` for logical backups or WAL archiving for point-in-time recovery.

---

## 🆘 Support

- **GitHub Issues**: Report bugs on the main repository
- **Documentation**: Check OSSP_IMPLEMENTATION.md for technical details
- **Community**: Join discussions on GitHub Discussions (coming soon)

---

## 🗺️ Roadmap

- [x] Core database routing (Supabase)
- [x] Authentication (Supabase JWT)
- [x] Storage (MinIO)
- [x] Vector search (Qdrant)
- [x] STT (Faster-Whisper)
- [x] LLM (Ollama + cloud APIs)
- [ ] Docker Compose orchestration
- [ ] Data migration tools
- [ ] Admin dashboard
- [ ] HA setup & replication
- [ ] Kubernetes support

---

## 📱 Building and Installing the Android APK

### Prerequisites

- Flutter 3.35.3 (compatible with font_awesome_flutter)
- Android SDK with API level 35+
- JDK 17 or higher
- Android Debug Bridge (adb) for device installation

### Build the APK

**1. Set up Flutter 3.35.3**

```bash
# If not already installed
flutter version 3.35.3

# Or set PATH to the correct Flutter installation
export PATH="/path/to/flutter-3.35.3/bin:$PATH"
```

**2. Navigate to app directory**

```bash
cd app
```

**3. Get dependencies**

```bash
flutter pub get
```

**4. Build the APK**

```bash
flutter build apk --flavor dev
```

The APK will be generated at:
```
app/build/app/outputs/flutter-apk/app-dev-release.apk
```

### Install on Android Device

**Option A: Using ADB (Android Debug Bridge)**

1. **Connect your Android device** via USB or Wi-Fi
2. **Enable USB Debugging** on your device (Settings → Developer Options → USB Debugging)
3. **Verify connection**:
   ```bash
   adb devices
   ```
4. **Install the APK**:
   ```bash
   adb install app/build/app/outputs/flutter-apk/app-dev-release.apk
   ```

**Option B: Manual Installation (via USB)**

1. Connect your Android device via USB
2. Copy the APK to your device:
   ```bash
   adb push app/build/app/outputs/flutter-apk/app-dev-release.apk /sdcard/Download/
   ```
3. On your device:
   - Open Files → Downloads
   - Tap the APK file
   - Follow the installation prompts

**Option C: Via File Transfer**

1. Copy the APK file to your computer
2. Transfer it to your Android device via:
   - USB file transfer
   - Email
   - Cloud storage (Google Drive, OneDrive)
   - AirDrop (if applicable)
3. On your device, open the file with your app installer

### Configure OSS+ Mode in the App

After installation, launch the app:

1. **Mode Selection Screen** - Choose "OSS+ Self-Hosted"
2. **Server Configuration**:
   - Enter your server IP or hostname
   - For local testing: use your computer's IP on the same network
   - Example: `192.168.1.100:8080` (replace with your actual IP)
3. **Complete Onboarding**:
   - Create account with Supabase
   - Configure encryption settings
   - Set up speech profile

### Finding Your Server IP Address

**Windows (for testing from same machine)**:
```powershell
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**From another machine on same network**:
```bash
# Linux/macOS
hostname -I

# Windows
ipconfig /all
# Look for IPv4 Address
```

**For production/remote access**:
- Use your public IP or domain name
- Ensure backend is accessible (firewall rules, port forwarding)
- Use HTTPS in production

### Troubleshooting

**APK won't install**:
- Ensure API level 21+ (Android 5.0+)
- Check available storage (150+ MB free)
- Clear app cache: `adb shell pm clear com.friend.ios.dev`

**Can't connect to backend**:
- Verify network connectivity
- Check firewall rules
- Test with: `curl http://<your-ip>:8080`
- Ensure backend container is running: `docker compose ps`

**App crashes on startup**:
- Check logs: `adb logcat | grep omi`
- Ensure Supabase is accessible
- Verify `.env` configuration in backend

---

## 📊 Status

**Core Implementation**: ✅ 100% Complete  
**Database Routing**: ✅ 14 migrations, 9 repos  
**Deployment**: 🟡 In Progress  
**Documentation**: 🟡 In Progress  
**Testing**: 🔴 To Do

See [OSS_REMAINING_TASKS.md](./OSS_REMAINING_TASKS.md) for detailed progress.

---

**Ready to self-host Omi?** Start with the [Quick Start](#-quick-start) above!

For questions or issues, open a GitHub issue or check the documentation.
