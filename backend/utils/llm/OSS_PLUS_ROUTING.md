# OSS+ Per-User LLM Routing

## Overview

In OSS+ self-hosted mode, users can choose their LLM provider during onboarding:
- **Ollama** (local, self-hosted, free)
- **OpenRouter** (cloud, latest models, user's API key)

The backend reads each user's choice from Supabase and routes LLM calls accordingly.

## Architecture

### 1. User Configuration (Stored in Supabase)

When a user completes OSS+ onboarding:
```json
{
  "oss_llm_config": {
    "provider": "openrouter" | "ollama",
    "openrouter_api_key": "sk_..." // optional, only for openrouter
  }
}
```

### 2. Backend Routing Logic

**clients.py** — Main LLM client factory:
- `get_llm_mini_for_user(uid)` — Get ChatOpenAI client for a specific user
- `get_embeddings_for_user(uid)` — Get embeddings client for a specific user
- `generate_embedding(content, uid)` — Generate embedding respecting user's config

**chat_file.py** — File upload feature:
- `get_async_openai_for_user(uid)` — Get AsyncOpenAI client for a specific user
- `FileChatTool._get_client()` — Caches the client per session

### 3. Routing Priority

When obtaining a client for a user in OSS+ mode:

1. **Read user's config from Supabase** via `_get_user_oss_llm_config(uid)`
2. **If user has config:**
   - OpenRouter + valid API key → use user's OpenRouter client
   - Ollama → use Ollama client (if `OLLAMA_BASE_URL` configured)
3. **Fallback to environment defaults:**
   - If `OLLAMA_BASE_URL` is set → use Ollama
   - If `OPENROUTER_API_KEY` is set → use OpenRouter (shared key)
4. **Error if nothing available**

### 4. Environment Configuration

For OSS+ docker-compose (.env.selfhosted):

```bash
# Either configure Ollama (local):
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# Or configure OpenRouter (shared across users):
OPENROUTER_API_KEY=sk_...

# Or both (Ollama takes priority, users can override to OpenRouter)
```

## Migration Guide

### For Routers That Need Per-User Routing

**Before:**
```python
from utils.llm.clients import get_llm, llm_mini
llm = get_llm('conv_action_items')
embeddings = embeddings.embed_documents([...])
```

**After (if uid available):**
```python
from utils.llm.clients import get_llm_mini_for_user, get_embeddings_for_user

uid: str = Depends(get_current_user_uid)
llm = get_llm_mini_for_user(uid)
embeddings = get_embeddings_for_user(uid)
```

### For File Chat Feature

Already migrated — `FileChatTool` automatically uses per-user routing:
```python
tool = FileChatTool(uid, chat_session_id)
# Internally calls get_async_openai_for_user(uid)
```

## Testing

### Test user with Ollama:
1. User configures: `provider=ollama` in onboarding
2. User's calls use local Ollama

### Test user with OpenRouter:
1. User configures: `provider=openrouter, api_key=sk_...` in onboarding
2. User's calls use their OpenRouter account

### Mixed users:
```
User A → Ollama (local)
User B → OpenRouter (their API key)
User C → OpenRouter (shared backend key, if no user config)
```

## Caching

- **Supabase config:** Read once per request (no caching, fresh on each call)
- **OpenAI clients:** Not cached (created fresh per request in OSS+ per-user mode)
  - If caching is needed in production, implement `LRUCache(maxsize=256, ttl=3600)` per uid
- **Default clients:** Cached globally (`llm_mini`, `embeddings`)

## Future Improvements

- [ ] Cache user configs per request (context-local, not global)
- [ ] Support per-user Ollama instances (different URLs per user)
- [ ] Admin dashboard to manage user LLM quotas
- [ ] Cost tracking per LLM provider
- [ ] Rate limiting by provider
