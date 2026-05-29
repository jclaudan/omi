# Omi — Self-Hosted Open-Source Stack

Branch: `feat/use-only-opensource-alternative`

This branch replaces every paid/proprietary cloud service used by Omi with a self-hosted
open-source alternative. The goal is a fully local deployment: no API tokens, no per-request
billing, no data leaving your machine.

---

## What was replaced

| Original service | Replacement | Role |
|---|---|---|
| **Google Cloud Storage (GCS)** | **MinIO** | Object storage — audio files, speech profiles, memories recordings, desktop updates |
| **Pinecone** | **Qdrant** | Vector database — semantic search over conversations and memories |
| **Deepgram** (batch STT) | **Faster-Whisper** (HTTP service, port 8001) | Transcription of pre-recorded audio |
| **Deepgram** (streaming STT) | **Faster-Whisper-WS** (WebSocket service, port 8002) | Live audio transcription replacing Deepgram's WebSocket API |
| **Typesense cloud** | **Typesense** (self-hosted, port 8108) | Full-text search |
| **OpenAI / Anthropic** (LLM) | **Ollama** (optional, port 11434) | Local LLM inference — llama3.2, mistral, qwen2.5, phi4, etc. |

### Services kept as-is (not yet replaced)

| Service | Reason |
|---|---|
| **Firebase Auth** | Deep integration — see [Authentication](#authentication-status) below |
| **Firestore** | Primary document store — replacing requires a full DB migration |
| **Firebase FCM** | Push notifications to mobile devices |

---

## Architecture

```
                          ┌─────────────────┐
                          │   Mobile App    │ (Flutter)
                          └────────┬────────┘
                                   │ HTTPS / WebSocket
              ┌────────────────────▼────────────────────┐
              │              omi-backend  :8080          │
              │              omi-pusher   :8081          │
              └──┬────────┬────────┬────────┬───────────┘
                 │        │        │        │
         ┌───────▼┐  ┌────▼───┐ ┌──▼────┐ ┌▼──────────────┐
         │  Redis │  │ Qdrant │ │ MinIO │ │   Typesense   │
         │  :6379 │  │ :6333  │ │ :9000 │ │    :8108      │
         └────────┘  └────────┘ └───────┘ └───────────────┘
                 │
   ┌─────────────┴──────────────┐
   │                            │
┌──▼───────────────┐  ┌─────────▼───────────┐
│ faster-whisper   │  │ faster-whisper-ws   │
│ (batch)  :8001   │  │ (streaming) :8002   │
└──────────────────┘  └─────────────────────┘
   (+ diarizer :8004)   (+ ollama :11434 optional)
```

---

## Quick start

```bash
# 1. Copy and fill in the environment file
cp .env.selfhosted.example .env.selfhosted
# Edit .env.selfhosted — at minimum set FIREBASE_* and OPENAI_API_KEY (or Ollama)

# 2. Build and start all services
docker compose up -d

# 3. Check health
docker compose ps
```

---

## GPU acceleration (RTX 4090 / any NVIDIA GPU)

Whisper services default to CPU (`python:3.11-slim` image). Switch to GPU for 5-10x faster
transcription using the CUDA variants.

### Prerequisites

Install `nvidia-container-toolkit` on the Docker host:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list \
  | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Activation

In `.env.selfhosted`, set:
```env
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
WHISPER_MODEL_SIZE=large-v3          # large-v3 recommended with 10+ GB VRAM (RTX 4090 = 24 GB)
WHISPER_DOCKERFILE=docker/services/faster-whisper/Dockerfile.cuda
WHISPER_WS_DOCKERFILE=docker/services/faster-whisper-ws/Dockerfile.cuda
```

In `docker-compose.yml`, uncomment the `deploy:` blocks on both `faster-whisper` and
`faster-whisper-ws` services:
```yaml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Then rebuild and restart:
```bash
docker compose build faster-whisper faster-whisper-ws
docker compose up -d faster-whisper faster-whisper-ws
```

### GPU Dockerfiles

| Service | CPU Dockerfile | GPU Dockerfile |
|---|---|---|
| Batch STT | `docker/services/faster-whisper/Dockerfile` | `docker/services/faster-whisper/Dockerfile.cuda` |
| Streaming STT | `docker/services/faster-whisper-ws/Dockerfile` | `docker/services/faster-whisper-ws/Dockerfile.cuda` |

Both GPU Dockerfiles use `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04` as base image.

---

## Local LLM with Ollama (optional)

Ollama replaces OpenAI / Anthropic for all LLM calls (memory extraction, chat, summaries).

1. Uncomment the `ollama` service in `docker-compose.yml`
2. In `.env.selfhosted`, set:
   ```env
   OLLAMA_BASE_URL=http://ollama:11434
   OLLAMA_MODEL=llama3.2
   ```
3. Remove or leave `OPENAI_API_KEY` empty
4. Pull a model:
   ```bash
   docker compose exec ollama ollama pull llama3.2
   ```

Recommended models: `llama3.2` (fast), `mistral` (balanced), `qwen2.5` (multilingual),
`phi4` (compact, good quality).

For GPU-accelerated Ollama, uncomment the `deploy` block inside the `ollama` service definition.

---

## Service ports

| Service | Port | Admin UI |
|---|---|---|
| omi-backend | 8080 | — |
| omi-pusher | 8081 | — |
| MinIO S3 API | 9000 | http://localhost:9001 |
| Qdrant REST | 6333 | http://localhost:6333/dashboard |
| Redis | 6379 | — |
| Typesense | 8108 | — |
| Faster-Whisper (batch) | 8001 | http://localhost:8001/health |
| Faster-Whisper-WS (stream) | 8002 | http://localhost:8002/health |
| Diarizer | 8004 | — |
| Ollama (optional) | 11434 | — |

---

## Storage — MinIO bucket layout

Auto-created by the `minio-init` service on first start:

| Bucket | Original GCS bucket |
|---|---|
| `omi-speech-profiles` | Speech profile audio samples |
| `omi-memories-recordings` | Conversation recordings |
| `omi-private-cloud-sync` | Private cloud sync files |
| `omi-chat-files` | Chat file attachments |
| `omi-app-logos` | Plugin/app logo images (public) |
| `omi-app-thumbnails` | App thumbnails (public) |
| `omi-desktop-updates` | Desktop app auto-update files |
| `omi-postprocessing` | Temporary audio for post-processing |

---

## Authentication status

> **Firebase Auth is NOT yet replaced.**

### Current state

The entire auth chain is Firebase-dependent at every layer:

| Layer | Firebase dependency |
|---|---|
| **Mobile app** | `FirebaseAuth.instance` — token lifecycle, Google/Apple OAuth via Firebase |
| **Backend API** | `firebase_admin.auth.verify_id_token()` — every HTTP request verified against Firebase |
| **Backend DB** | Firestore — primary document store for users, conversations, memories |
| **Push notifications** | Firebase FCM |

A `custom_auth/signin.dart` file exists in the Flutter app with an email/password form, but
**it is a non-functional stub** — the submit handler prints the form data and shows a snackbar
without calling any auth backend. It was never wired up.

### What replacing auth would require

To make auth fully self-hosted, the following work is needed:

1. **Backend** — replace `firebase_admin.auth.verify_id_token()` in `backend/dependencies.py`
   with a self-issued JWT verified against a local secret or key pair.
2. **Backend** — replace `firebase_admin.auth.create_custom_token()` in `backend/routers/auth.py`.
3. **Backend** — replace all Firestore calls (`database/_client.py`) with a self-hosted DB
   (PostgreSQL + SQLAlchemy, or Supabase which includes auth + storage + Postgres).
4. **Mobile app** — replace `FirebaseAuth.instance` with a custom auth provider that signs
   into the self-hosted backend and stores a local JWT.
5. **Push notifications** — replace FCM with a self-hosted solution (e.g., Ntfy, Gotify,
   or Expo push without Firebase).

Supabase is the closest drop-in replacement: it covers Auth, Postgres (replaces Firestore),
Storage (replaces MinIO if desired), and Realtime (partially replaces Pusher/FCM).

---

## Files added / modified by this branch

```
docker-compose.yml                              # full self-hosted stack
.env.selfhosted.example                         # configuration template
docker/
  services/
    faster-whisper/
      Dockerfile                                # CPU batch STT
      Dockerfile.cuda                           # GPU batch STT (RTX 4090 / NVIDIA)
      main.py                                   # FastAPI STT service
      requirements.txt
    faster-whisper-ws/
      Dockerfile                                # CPU streaming STT
      Dockerfile.cuda                           # GPU streaming STT (RTX 4090 / NVIDIA)
      main.py                                   # WebSocket STT service
      requirements.txt
backend/
  utils/
    storage/                                    # MinIO adapter (replaces GCS)
    vector_db.py                                # Qdrant adapter (replaces Pinecone)
    stt/
      faster_whisper.py                         # Batch STT client
      faster_whisper_ws.py                      # Streaming STT client / Deepgram fallback
```
