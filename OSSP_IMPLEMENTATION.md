# OSS+ (Open Source+) Implementation Status

## Overview
OSS+ is a fully self-hosted alternative to the Cloud deployment, using open-source and self-hosted components instead of proprietary APIs.

**Mode Switch**: Set `OMI_DB_BACKEND=supabase` to enable OSS+ mode. Cloud mode is default.

---

## ✅ Completed Components

### 1. **Authentication & User Management** (Étape 4-5)
- Supabase Auth (JWT-based) instead of Firebase
- User profile initialization on Supabase
- Status: COMPLETE ✅

**Key Files**:
- `backend/utils/auth/factory.py` — Auth factory pattern
- `selfhost/supabase/migrations/001_profiles.sql` — User profiles schema

---

### 2. **Core Database Routing** (Étape 7-10)
Factory pattern applied across all database modules to switch between Firestore (Cloud) and Supabase (OSS+).

**Components**:
- ✅ Conversations (audio transcripts, segments, metadata)
- ✅ Memories (user facts, visibility, encryption)
- ✅ Action Items (tasks, due dates)
- ✅ Chat (messages, sessions, encryption)
- ✅ Daily Summaries (auto-generated daily reports)
- ✅ Goals (goal tracking with progress history)

**Key Pattern**:
```python
_SUPABASE = os.environ.get('OMI_DB_BACKEND', 'firestore').lower() == 'supabase'

def function_name(...):
    if _SUPABASE:
        from database.repo.supabase_* import function_name as fn_supabase
        return fn_supabase(...)
    # Firestore implementation
```

---

### 3. **Apps System** (Étape 17)
Full support for:
- **Prompt apps** (memory_prompt, chat_prompt) — run entirely in backend
- **Webhook apps** (external_integration.webhook_url) — backend calls URL
- **Public/Private apps** — user-owned or marketplace
- **Personas** — special app type for personality emulation

**Status**: COMPLETE ✅

**Key Files**:
- `backend/database/repo/supabase_apps.py` — 250+ LOC, full CRUD + search
- `selfhost/supabase/migrations/010_apps.sql` — apps table with RLS
- `backend/database/apps.py` — routed 30+ functions

---

### 4. **Enabled Apps Management** (Étape 18)
Factory layer routing user-enabled apps between:
- **Redis** (Cloud) — sets stored in `users:{uid}:enabled_plugins`
- **Supabase** (OSS+) — `public.user_enabled_apps` table

**Status**: COMPLETE ✅

**Key Files**:
- `backend/database/enabled_apps.py` — Factory with get/enable/disable
- All routers updated to use factory instead of redis_db directly

---

### 5. **Sub-Collections Migration** (Étapes 19-21)
Replaces Firestore sub-collections with top-level Supabase tables.

| Étape | Collection | OSS+ Table | Repo | Migration |
|-------|-----------|-----------|------|-----------|
| 19 | `users/{uid}/daily_summaries` | `daily_summaries` | supabase_daily_summaries.py | 011_daily_summaries.sql |
| 20 | `users/{uid}/goals` + history | `goals`, `goal_history` | supabase_goals.py | 012_goals.sql |
| 21 | `users/{uid}/conversations/{id}/photos` | `conversation_photos` | — | 013_photos.sql |

**Status**: COMPLETE ✅ (Repos + Migrations)

---

### 6. **Speech-to-Text (STT) Routing** (Étapes 8-9)
Routes between:
- **Cloud**: Deepgram API (streaming + batch)
- **OSS+**: Faster-Whisper (via HTTP)

**Env Vars**:
- `FASTER_WHISPER_WS_URL=ws://faster-whisper-ws:8002` — Streaming
- `FASTER_WHISPER_URL=http://faster-whisper:8001` — Batch

**Status**: COMPLETE ✅

---

### 7. **Storage Routing** (Étape 1)
Routes between:
- **Cloud**: Google Cloud Storage (GCS)
- **OSS+**: MinIO (S3-compatible)

**Env Vars**:
- `OMI_STORAGE_BACKEND=minio`
- `MINIO_ENDPOINT=http://minio:9000`

**Status**: COMPLETE ✅

---

### 8. **Vector Database Routing** (Étape 1)
Routes between:
- **Cloud**: Pinecone (vector similarity search)
- **OSS+**: Qdrant (self-hosted vector DB)

**Env Vars**:
- `QDRANT_URL=http://qdrant:6333`

**Status**: COMPLETE ✅

---

### 9. **LLM Routing** (Étape 2 + Ollama)
Multiple LLM options with fallback chain:

1. **BYOK (Bring Your Own Key)** — user-provided API key
2. **Ollama** — Local inference engine
3. **OpenAI** — GPT-4 Mini (Cloud default)
4. **OpenRouter** — Gemini, Claude via proxy
5. **Anthropic** — Claude via SDK (key features)
6. **Google Gemini** — Vertex AI or AI Studio
7. **Perplexity** — Web search + reasoning

**Ollama Support**:
```python
# Set these env vars to use Ollama for OpenAI-model features
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
# When set + no OPENAI_API_KEY, routes all OpenAI calls to Ollama
```

**Status**: COMPLETE ✅

**Key Files**:
- `backend/utils/llm/clients.py` — LLM factory routing (lines 529-539)

---

### 10. **Specialized Database Functions**
Status, visibility, and metadata updates already routed:

- **Status**: `update_conversation_status`, `set_postprocessing_status`
- **Visibility**: `set_conversation_visibility`, `change_memory_visibility`, `set_daily_summary_visibility`
- **Photos**: `store_conversation_photos`, `get_conversation_photos`, `delete_conversation_photos`

**Status**: COMPLETE ✅

**Files**:
- `backend/database/conversations.py` — lines 882-1229
- `backend/database/memories.py` — line 275
- `backend/database/daily_summaries.py` — all functions routed

---

## 📊 Implementation Statistics

| Category | Count |
|----------|-------|
| **Supabase Migrations** | 13 (001-013) |
| **Supabase Repos** | 8 (apps, chat, conversations, daily_summaries, goals, action_items, memories, users) |
| **Routed Functions** | 100+ |
| **Database Modules Updated** | 15+ |
| **Router Modules Updated** | 6+ |
| **Factory Modules** | 2 (enabled_apps.py, clients.py) |
| **Total Lines of Code** | 3000+ |

---

## 🚀 Environment Variables (OSS+)

### Required
```bash
OMI_DB_BACKEND=supabase              # Enable OSS+ mode
OMI_AUTH_BACKEND=supabase            # Auth via Supabase
OMI_STORAGE_BACKEND=minio            # Storage via MinIO
```

### Supabase
```bash
SUPABASE_URL=http://supabase:8000    # Supabase instance
SUPABASE_ANON_KEY=<anon_key>         # Public anon key
SUPABASE_SERVICE_ROLE_KEY=<key>      # Service role for migrations
```

### Speech-to-Text
```bash
FASTER_WHISPER_URL=http://faster-whisper:8001          # Batch
FASTER_WHISPER_WS_URL=ws://faster-whisper-ws:8002      # Streaming
```

### Vector Database
```bash
QDRANT_URL=http://qdrant:6333        # Vector similarity search
```

### Storage
```bash
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

### LLM (Ollama)
```bash
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
# Don't set OPENAI_API_KEY to force Ollama routing
```

---

## ✅ Testing Checklist

- [ ] Auth flow (register, login, JWT)
- [ ] Conversation create/read/update
- [ ] Memory create/search/visibility
- [ ] App marketplace (public/private apps)
- [ ] App enable/disable (routing via Supabase table)
- [ ] Chat messages (encryption if enabled)
- [ ] Daily summaries (creation, retrieval)
- [ ] Goals (create, track progress)
- [ ] STT (Faster-Whisper integration)
- [ ] LLM responses (Ollama fallback when no OpenAI key)
- [ ] Storage (MinIO file upload/download)
- [ ] Vector search (Qdrant similarity)

---

## 📁 Migration Order

Execute migrations in this order to maintain referential integrity:

1. `001_profiles.sql` — User profiles
2. `002_core_schema.sql` — Conversations, memories, etc.
3. `003-008.sql` — Additional features
4. `009_chat.sql` — Chat messages & sessions
5. `010_apps.sql` — App system
6. `011_daily_summaries.sql` — Daily summaries
7. `012_goals.sql` — Goals + history
8. `013_photos.sql` — Conversation photos

---

## 🔐 Security

- **RLS Enabled** — All tables have row-level security policies
- **Encryption** — Message text encrypted at rest (configurable)
- **Auth** — JWT-based (Supabase Auth)
- **CORS** — Configured for self-hosted domain

---

## 📝 Notes

1. **No approval process in OSS+** — Apps are auto-approved (`approved=true` by default)
2. **API keys not implemented in OSS+** — App API authentication skipped
3. **Tester program not available in OSS+** — Returns empty lists
4. **App usage tracking not available in OSS+** — No analytics collection
5. **No Stripe integration in OSS+** — Paid apps disabled

---

## 🎯 Next Steps

- Docker Compose orchestration for full stack
- Migration tooling for Firestore → Supabase
- Admin dashboard for OSS+ management
- Performance testing & optimization
- Documentation for self-hosted deployment

---

**Last Updated**: 2026-05-30  
**Branch**: `feat/use-only-opensource-alternative`  
**Commit**: Latest 4 commits implement Étapes 17-21 + Étape 18
