# OSS+ Self-Hosted Setup Guide

## Quick Start

```powershell
.\selfhost\start-oss-plus.ps1
```

This will:
1. Check for `.env.selfhosted` file
2. Create from `.env.example` if missing
3. Start all services (Supabase, Qdrant, MinIO, STT, Redis, etc.)

## Configuration Options

### Option 1: Local Ollama (Recommended for Self-Hosted)

Best for: Privacy, no API costs, complete control.

**Step 1: .env.selfhosted**
```bash
# Local LLM
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# Keep these empty for user override
OPENROUTER_API_KEY=
```

**Step 2: docker-compose.yml**
Uncomment the `ollama` service around line 110

**Step 3: Start**
```powershell
.\selfhost\start-oss-plus.ps1
docker compose logs -f ollama  # Watch Ollama download models
```

**Step 4: User Onboarding (APK)**
- When user completes onboarding, choose: **Ollama (Local)**
- No API key needed
- Runs entirely local ✅

### Option 2: OpenRouter (Cloud Models, Per-User Cost)

Best for: Latest models, shared infrastructure, pay-as-you-go.

**Step 1: Get OpenRouter API Key**
1. Go to https://openrouter.ai/keys
2. Create API key
3. Copy it

**Step 2: .env.selfhosted**
```bash
# Cloud LLM (Optional - users can provide their own)
OPENROUTER_API_KEY=

# Make sure Ollama is commented out
# OLLAMA_BASE_URL=
# OLLAMA_MODEL=
```

**Step 3: Start**
```powershell
.\selfhost\start-oss-plus.ps1
```

**Step 4: User Onboarding (APK)**
- When user completes onboarding, choose: **OpenRouter (Cloud)**
- Paste their API key (from https://openrouter.ai/keys)
- Their account is used, they pay per request ✅

### Option 3: Hybrid (Ollama Default + OpenRouter Override)

Best for: Users who want local-first, with cloud option for advanced models.

**Step 1: .env.selfhosted**
```bash
# Local fallback
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# Cloud override (optional)
OPENROUTER_API_KEY=
```

**Step 2: docker-compose.yml**
Uncomment the `ollama` service

**Step 3: Start**
```powershell
.\selfhost\start-oss-plus.ps1
```

**Step 4: User Onboarding (APK)**
- Users choosing **Ollama** → use local models (free)
- Users choosing **OpenRouter** → can provide their own API key (pay-per-request)
- No API key in backend = users can't force cloud models if Ollama isn't working ⚠️

## Startup Checklist

```bash
# 1. Check all services are healthy
docker compose ps

# 2. Check logs for errors
docker compose logs omi-backend    # Backend API
docker compose logs ollama          # LLM (if enabled)
docker compose logs faster-whisper  # Speech-to-text

# 3. Test API health
curl http://localhost:8080/health

# 4. Access services
- Backend API: http://localhost:8080
- MinIO Console: http://localhost:9001
- Qdrant: http://localhost:6333
```

## User Onboarding Flow

```
1. APK starts → Selects "OSS+" mode
2. Configures services (Supabase, STT, MinIO, etc.)
3. **Chooses LLM Provider:**
   - Ollama (Local) → No extra setup
   - OpenRouter (Cloud) → Enters their API key
4. Creates Supabase account
5. Choice + key stored in backend Supabase
6. Done! All future API calls use their chosen provider
```

## Troubleshooting

### Backend can't find Ollama
```bash
# Check Ollama is running
docker compose logs ollama

# Check network connectivity
docker compose exec omi-backend ping ollama

# If not working, comment out OLLAMA_BASE_URL in .env.selfhosted
```

### OpenRouter API key not working
```bash
# Verify the key is valid
curl -H "Authorization: Bearer sk_..." https://openrouter.io/api/v1/models

# Check backend logs
docker compose logs omi-backend | grep -i openrouter
```

### User's config not persisting
```bash
# Check Supabase migrations ran
docker compose logs postgrest

# Check user_profiles table has oss_llm_config column
# (Should be added by migration 015_oss_llm_config.sql)
```

## Production Notes

- **Backup Supabase data regularly** — it stores all user configs
- **Monitor Ollama memory usage** — large models can consume >20GB RAM
- **Set resource limits** in docker-compose if needed:
  ```yaml
  ollama:
    deploy:
      resources:
        limits:
          memory: 16G
  ```
- **Use GPU for Ollama** (optional) — requires nvidia-container-toolkit
  ```yaml
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  ```

## Cost Estimation

### Ollama (Self-Hosted)
- **Infrastructure cost:** Server/GPU + internet
- **Per-request cost:** Free (runs locally)
- **Best for:** Privacy-sensitive deployments, offline capability

### OpenRouter (Cloud)
- **Per-request cost:** ~$0.001 - $0.02 per 1K tokens (varies by model)
- **Avg conversation:** 3K tokens = $0.003 - $0.06 per conversation
- **Best for:** Minimal infrastructure, no GPU required, latest models

## Support

If you encounter issues:
1. Check logs: `docker compose logs -f`
2. Verify .env.selfhosted has required values
3. Ensure all services are healthy: `docker compose ps`
4. Rebuild images if stuck: `docker compose build --no-cache`
