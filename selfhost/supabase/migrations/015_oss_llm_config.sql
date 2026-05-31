-- OSS+ LLM Configuration
-- Stores user's LLM provider preference (openrouter or ollama) and API keys + model selections

alter table public.profiles
    add column if not exists oss_llm_config jsonb default '{"provider": "ollama"}' not null;

-- oss_llm_config structure:
-- {
--   "provider": "ollama" | "openrouter",
--   "openrouter_api_key": "sk_..." (optional, only for openrouter),
--   "openrouter_llm_model": "gpt-4-turbo" (optional, defaults to gpt-4-turbo),
--   "openrouter_embedding_model": "text-embedding-3-large" (optional, defaults to text-embedding-3-large)
-- }

-- Update default config to include model fields
update public.profiles
set oss_llm_config = '{"provider": "ollama", "openrouter_llm_model": "gpt-4-turbo", "openrouter_embedding_model": "text-embedding-3-large"}'::jsonb
where oss_llm_config = '{"provider": "ollama"}' or oss_llm_config is null;
