# OSS+ Per-User LLM Routing — Complete Implementation

## What Was Built

Users can now **choose their LLM provider during OSS+ onboarding** and each user's choice is respected throughout the app.

```
Frontend (APK)
  └─> StepLlmProvider
      ├─> Option 1: OpenRouter (Cloud)
      │   └─> Enter API key
      └─> Option 2: Ollama (Local)
          └─> Use local models

      (Choice saved locally in SharedPreferences)
      
      └─> After Login
          └─> POST /v1/oss/configure-llm
              └─> Synced with Backend Supabase

Backend
  └─> Supabase profiles.oss_llm_config
      ├─> provider: "openrouter" | "ollama"
      ├─> openrouter_api_key: "sk_..." (if OpenRouter)
      └─> On every LLM call:
          ├─> Read user's config from Supabase
          ├─> If OpenRouter + valid key → use user's key
          ├─> If Ollama + available → use local Ollama
          └─> Else → use backend defaults
```

## Files Changed/Created

### Frontend (APK)
```
✅ app/lib/pages/onboarding/oss_plus/step_llm_provider.dart
   └─> New step with 2 buttons (OpenRouter/Ollama) + API key input
   
✅ app/lib/backend/preferences.dart
   └─> Added: ossLlmProvider, ossOpenrouterApiKey
   
✅ app/lib/backend/http/api/oss.dart
   └─> New: configureOssLlmProvider(), getOssLlmProvider()
   
✅ app/lib/pages/onboarding/oss_plus/wrapper.dart
   └─> Updated: +1 step (9 total), added StepLlmProvider import
   
✅ app/lib/pages/onboarding/oss_plus/step_auth.dart
   └─> Updated: After auth, sync user's LLM config to backend
```

### Backend (Python)
```
✅ backend/routers/oss_config.py (NEW)
   └─> POST /v1/oss/configure-llm
   └─> GET  /v1/oss/llm-config
   
✅ backend/database/repo/supabase_users.py
   └─> Added: set_user_oss_llm_config(uid, config)
   
✅ backend/utils/llm/clients.py
   ├─> Added: _get_user_oss_llm_config(uid) — reads from Supabase
   ├─> Added: _get_ollama_mini_client()
   ├─> Added: _get_openrouter_mini_client(api_key)
   ├─> Added: _get_llm_mini_client_for_user(uid) — per-user routing
   ├─> Added: get_llm_mini_for_user(uid) — PUBLIC API
   ├─> Added: _get_embeddings_for_user(uid) — per-user routing
   ├─> Added: get_embeddings_for_user(uid) — PUBLIC API
   ├─> Updated: generate_embedding(content, uid=None)
   └─> Updated: _get_llm_mini_client() — now calls for_user(uid=None)
   
✅ backend/utils/other/chat_file.py
   ├─> Updated: _get_async_openai_for_user(uid) — per-user OpenRouter
   ├─> Added: get_async_openai_for_user(uid) — PUBLIC API
   ├─> Updated: FileChatTool — uses per-user client via _get_client()
   └─> Updated: _ask_vision_stream() — uses self._get_client()
   
✅ backend/main.py
   ├─> Added: import oss_config
   └─> Added: app.include_router(oss_config.router)
```

### Database (Supabase)
```
✅ selfhost/supabase/migrations/015_oss_llm_config.sql
   └─> ALTER TABLE profiles ADD oss_llm_config JSONB
       └─> Stores: {provider, openrouter_api_key}
```

### Documentation
```
✅ backend/utils/llm/OSS_PLUS_ROUTING.md
   └─> Architecture, migration guide, testing notes
   
✅ selfhost/OSS_PLUS_SETUP.md
   └─> Setup guide for Ollama, OpenRouter, hybrid modes
```

## How to Test

### 1. Backend Setup

```bash
# Update .env.selfhosted with ONE or BOTH:

# Option A: Ollama (local, free)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama2

# Option B: OpenRouter (cloud, per-user)
OPENROUTER_API_KEY=sk_...

# Then uncomment `ollama` service in docker-compose.yml if using Ollama
```

### 2. Start Stack
```powershell
.\selfhost\start-oss-plus.ps1

# Wait for migrations to run
# Verify: SELECT * FROM profiles LIMIT 1 → should have oss_llm_config column
```

### 3. Test Onboarding (APK)

**Scenario A: Local Ollama**
1. Start OSS+ onboarding
2. Configure all services (Supabase, STT, MinIO, etc.)
3. **LLM Provider step** → Choose "Ollama (Local)"
4. Complete auth
5. Check Supabase: `users_profiles.oss_llm_config` should be `{"provider": "ollama"}`

**Scenario B: OpenRouter**
1. Start OSS+ onboarding
2. Configure all services
3. **LLM Provider step** → Choose "OpenRouter (Cloud)"
4. Enter API key (get from https://openrouter.io/keys)
5. Complete auth
6. Check Supabase: `oss_llm_config` should be `{"provider": "openrouter", "openrouter_api_key": "sk_..."}`

**Scenario C: Mixed Users**
1. Create two users with different choices
2. User A → Ollama
3. User B → OpenRouter
4. Both should work independently ✅

### 4. Test LLM Calls

Any feature that uses LLM (chat, memories, etc.) should:
- User A (Ollama) → calls use local models
- User B (OpenRouter) → calls use their API key

Check logs:
```bash
docker compose logs omi-backend | grep "LLM\|OSS"
# Should show: "Using OpenRouter (user config) for uid ..."
#           or "Using Ollama (user config) for uid ..."
```

### 5. Test File Chat (if implemented)

```bash
# POST /v2/messages with file_ids
# Should route to user's LLM provider

# User A: uses Ollama
# User B: uses OpenRouter
```

## Verification Checklist

- [ ] `.env.selfhosted` has `OLLAMA_BASE_URL` or `OPENROUTER_API_KEY` (or both)
- [ ] Docker stack starts: `docker compose ps` shows all healthy
- [ ] APK onboarding includes LLM choice step (step 5 of 8)
- [ ] After login, Supabase has `oss_llm_config` in user profile
- [ ] LLM calls respect user's choice (check logs)
- [ ] Multiple users can have different providers
- [ ] File chat (if available) uses per-user client

## Rollback Plan

If something breaks:

1. **Remove the step from APK:**
   ```dart
   // In wrapper.dart, remove StepLlmProvider from children
   // Reduces _totalSteps from 9 back to 8
   ```

2. **Use backend defaults:**
   ```python
   # clients.py will fallback to env vars
   # OLLAMA_BASE_URL → all users use Ollama
   # OPENROUTER_API_KEY → all users use OpenRouter
   ```

3. **Ignore user config:**
   ```python
   # In _get_llm_mini_client_for_user(), just use env defaults
   ```

## Future Enhancements

- [ ] **UI for changing provider after onboarding** — /settings → LLM Provider
- [ ] **Per-user Ollama URLs** — advanced users can point to their own Ollama
- [ ] **Cost dashboard** — track spending per user per provider
- [ ] **Admin panel** — manage user LLM quotas/limits
- [ ] **Fallback chains** — "Try OpenRouter, if fails use Ollama"
- [ ] **Caching** — LRUCache per uid to avoid re-reading Supabase

## Notes

- **No secrets in logs** — API keys are never logged, only `[REDACTED]`
- **Graceful degradation** — If Supabase is down, falls back to env defaults
- **Per-request routing** — No caching of user configs (always fresh from DB)
- **Backward compatible** — Existing code still works, just without user routing

---

**Status:** ✅ Implementation complete, ready for testing
