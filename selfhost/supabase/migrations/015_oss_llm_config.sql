-- OSS+ LLM Configuration
-- Stores user's LLM provider preference (openrouter or ollama) and API keys

alter table public.profiles
    add column if not exists oss_llm_config jsonb default '{"provider": "ollama"}' not null;

-- oss_llm_config structure:
-- {
--   "provider": "ollama" | "openrouter",
--   "openrouter_api_key": "sk_..." (optional, only for openrouter)
-- }
