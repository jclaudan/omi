import logging
import os

import httpx

logger = logging.getLogger(__name__)

_SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
_SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')


def _is_configured() -> bool:
    return bool(_SUPABASE_URL and _SUPABASE_SERVICE_KEY)


def _rest_headers() -> dict:
    return {
        'apikey': _SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {_SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation',
    }


def upsert_profile(uid: str, email: str) -> bool:
    """Insert or update a row in public.profiles using the Supabase REST API.

    Returns True on success, False if Supabase is not configured or on error.
    Fail-open: errors are logged but never bubble up to callers.
    """
    if not _is_configured():
        logger.debug('oss_supabase_client: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — skipping profile upsert')
        return False

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/profiles',
                headers=_rest_headers(),
                json={'id': uid, 'email': email},
            )
            if resp.status_code in (200, 201):
                return True
            logger.warning('oss_supabase_client: profile upsert returned %s: %s', resp.status_code, resp.text[:200])
            return False
    except Exception as exc:
        logger.error('oss_supabase_client: profile upsert error: %s', exc)
        return False


def get_profile(uid: str) -> dict | None:
    """Fetch a profile row by user ID. Returns the dict or None."""
    if not _is_configured():
        return None

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/profiles',
                headers={
                    'apikey': _SUPABASE_SERVICE_KEY,
                    'Authorization': f'Bearer {_SUPABASE_SERVICE_KEY}',
                },
                params={'id': f'eq.{uid}', 'limit': '1'},
            )
            if resp.status_code == 200:
                rows = resp.json()
                return rows[0] if rows else None
            logger.warning('oss_supabase_client: get_profile returned %s', resp.status_code)
            return None
    except Exception as exc:
        logger.error('oss_supabase_client: get_profile error: %s', exc)
        return None
