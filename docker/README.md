# Omi Self-Hosted

Self-host Omi with open-source replacements for all cloud dependencies.

## What's replaced

| Cloud service | Self-hosted alternative | Status |
|---|---|---|
| Google Cloud Storage | **MinIO** (S3-compatible) | ✅ Implemented |
| Pinecone | **Qdrant** (vector database) | ✅ Implemented |
| Deepgram (batch STT) | **Faster-Whisper** (OpenAI Whisper) | ✅ Implemented |
| Redis | **Redis** (self-hosted) | ✅ Already supported |
| Firebase Auth | Firebase (still required) | 🔜 Future |
| Firestore | Firestore (still required) | 🔜 Future |

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.selfhosted.example .env.selfhosted

# Edit .env.selfhosted — minimum required:
#   OPENAI_API_KEY=...
#   FIREBASE_* and SERVICE_ACCOUNT_JSON=...
#   MINIO_ROOT_PASSWORD=<strong password>

# 2. Start all services
docker compose up -d

# 3. Check status
docker compose ps
docker compose logs -f omi-backend

# 4. Access
# MinIO console: http://localhost:9001  (minioadmin / your password)
# Qdrant dashboard: http://localhost:6333/dashboard
# Backend API: http://localhost:8080
# Pusher WS: ws://localhost:8081
```

## Services

| Service | Port | Purpose |
|---|---|---|
| minio | 9000 (API), 9001 (UI) | Object storage |
| qdrant | 6333 (REST), 6334 (gRPC) | Vector search |
| redis | 6379 | Cache / rate-limiting |
| faster-whisper | 8001 | Speech-to-text |
| diarizer | 8004 | Speaker identification |
| omi-backend | 8080 | Main API |
| omi-pusher | 8081 | Real-time WebSocket hub |

## GPU Acceleration (optional)

For faster transcription, run Whisper on GPU:

```bash
# .env.selfhosted
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
WHISPER_MODEL_SIZE=large-v3
```

Add to docker-compose.yml under `faster-whisper`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## Whisper model sizes

| Model | RAM | Speed | Accuracy |
|---|---|---|---|
| tiny | ~1 GB | Fastest | Low |
| base | ~1 GB | Fast | OK |
| small | ~2 GB | Good | Good |
| medium | ~5 GB | Slower | Very good |
| large-v3 | ~10 GB | Slow (GPU needed) | Best |

## Streaming STT

Faster-Whisper is used for **batch** transcription (pre-recorded audio).
For **live streaming** transcription, Deepgram is still used if `DEEPGRAM_API_KEY` is set.
To run fully without Deepgram, leave `DEEPGRAM_API_KEY` empty — the backend will fall back
to batching audio and transcribing with Faster-Whisper.

## Data persistence

All data is stored in named Docker volumes:

- `minio-data` — uploaded files and audio
- `qdrant-data` — vector embeddings  
- `redis-data` — cache
- `whisper-models` — downloaded Whisper model weights
- `diarizer-models` — Pyannote model weights

## Backup

```bash
# Stop services
docker compose stop

# Back up volumes
docker run --rm -v minio-data:/data -v $(pwd)/backup:/backup alpine \
  tar czf /backup/minio-$(date +%Y%m%d).tar.gz /data

docker run --rm -v qdrant-data:/data -v $(pwd)/backup:/backup alpine \
  tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz /data

# Restart
docker compose start
```

## Troubleshooting

**MinIO buckets not created:**
```bash
docker compose restart minio-init
docker compose logs minio-init
```

**Whisper model download slow on first start:**
Models are cached in the `whisper-models` volume — only downloaded once.

**Diarizer takes 2+ minutes to start:**
Normal — pyannote models download on first boot. Subsequent starts are fast.

**Backend can't connect to Qdrant:**
```bash
curl http://localhost:6333/health   # Should return {"title":"qdrant","version":"..."}
```
