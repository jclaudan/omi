"""OSS+ configuration endpoints — LLM provider selection, API keys, etc."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from utils.other.endpoints import get_current_user_uid
from database.repo.supabase_users import get_user_profile, set_user_oss_llm_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/oss', tags=['oss_config'])


class LlmConfig(BaseModel):
    provider: str
    openrouter_api_key: Optional[str] = None


@router.post('/configure-llm')
def configure_llm(
    config: LlmConfig,
    uid: str = Depends(get_current_user_uid),
):
    """Store user's LLM provider preference and API keys in Supabase."""
    if config.provider not in ['openrouter', 'ollama']:
        return {'error': 'provider must be "openrouter" or "ollama"'}

    profile = get_user_profile(uid)
    if not profile:
        return {'error': 'user profile not found'}

    oss_config = {'provider': config.provider}
    if config.provider == 'openrouter' and config.openrouter_api_key:
        oss_config['openrouter_api_key'] = config.openrouter_api_key

    set_user_oss_llm_config(uid, oss_config)
    logger.info(f'[OSS] User {uid} configured LLM provider: {config.provider}')
    return {'success': True, 'provider': config.provider}


@router.get('/llm-config')
def get_llm_config(uid: str = Depends(get_current_user_uid)):
    """Get the current user's LLM configuration."""
    profile = get_user_profile(uid)
    if not profile:
        return {'error': 'user profile not found'}

    config = profile.get('oss_llm_config', {'provider': 'ollama'})
    safe_config = {'provider': config.get('provider', 'ollama')}
    return safe_config
