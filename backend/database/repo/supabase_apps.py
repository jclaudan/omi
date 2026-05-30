"""
Supabase implementation for the apps (plugins) system.

Replaces Firestore plugins_data/ global collection.
All app types work in OSS+ mode:
  - Prompt apps (memory_prompt, chat_prompt)     — run entirely in the backend
  - Webhook apps (external_integration.webhook_url) — backend calls the URL
  - Public apps from the Omi repo              — can be seeded via migration

No approval process in self-hosted mode: approved defaults to True.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'apps'
_ENABLED_TABLE = 'user_enabled_apps'


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _get(params: dict) -> list:
    if not _is_configured():
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'return=representation'},
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning('supabase apps GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase apps GET error: %s', exc)
    return []


def _upsert(data: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'resolution=merge-duplicates'},
                json=data,
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.error('supabase apps UPSERT error: %s', exc)
        return False


def _patch(app_id: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'id': f'eq.{app_id}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase apps PATCH error: %s', exc)
        return False


def _app_row_to_dict(row: dict) -> dict:
    """Flatten metadata into the dict so the App model works unchanged."""
    result = {**row}
    result.update(row.get('metadata') or {})
    return result


def _app_data_to_row(app_data: dict) -> dict:
    """Convert app dict to Supabase row, mapping known columns and putting the rest in metadata."""
    known = {
        'id', 'uid', 'name', 'description', 'author', 'category', 'image',
        'capabilities', 'private', 'approved', 'status', 'disabled',
        'external_integration', 'memory_prompt', 'chat_prompt', 'persona_prompt',
        'installs', 'rating_avg', 'rating_count', 'is_popular', 'created_at', 'updated_at',
    }
    row = {k: v for k, v in app_data.items() if k in known}
    extra = {k: v for k, v in app_data.items() if k not in known and k != 'metadata'}
    if extra:
        row['metadata'] = extra
    # In self-hosted mode, all apps are approved by default
    row.setdefault('approved', True)
    row.setdefault('status', 'approved')
    return row


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_app_by_id(app_id: str) -> Optional[Dict[str, Any]]:
    rows = _get({'id': f'eq.{app_id}', 'deleted': 'eq.false', 'limit': '1'})
    return _app_row_to_dict(rows[0]) if rows else None


def get_public_approved_apps() -> List[Dict[str, Any]]:
    rows = _get({'approved': 'eq.true', 'private': 'eq.false', 'deleted': 'eq.false', 'order': 'created_at.desc'})
    return [_app_row_to_dict(r) for r in rows]


def get_private_apps(uid: str) -> List[Dict[str, Any]]:
    rows = _get({'uid': f'eq.{uid}', 'private': 'eq.true', 'deleted': 'eq.false'})
    return [_app_row_to_dict(r) for r in rows]


def search_apps(
    uid: str,
    category: Optional[str] = None,
    capability: Optional[str] = None,
    my_apps: bool = False,
    enabled_app_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    params: dict = {'deleted': 'eq.false', 'order': 'created_at.desc'}

    if my_apps:
        params['uid'] = f'eq.{uid}'
    elif enabled_app_ids is not None:
        if not enabled_app_ids:
            return []
        id_list = ','.join(enabled_app_ids)
        params['id'] = f'in.({id_list})'
    else:
        params['approved'] = 'eq.true'
        params['private'] = 'eq.false'

    if category and not my_apps:
        params['category'] = f'eq.{category}'

    rows = _get(params)
    apps = [_app_row_to_dict(r) for r in rows]

    if capability and not my_apps:
        apps = [a for a in apps if capability in (a.get('capabilities') or [])]
    if my_apps and category:
        apps = [a for a in apps if a.get('category') == category]
    if my_apps and capability:
        apps = [a for a in apps if capability in (a.get('capabilities') or [])]

    return apps


def get_audio_apps_count(app_ids: List[str]) -> int:
    if not app_ids:
        return 0
    id_list = ','.join(app_ids)
    rows = _get({'id': f'in.({id_list})', 'deleted': 'eq.false', 'select': 'id'})
    return sum(
        1 for r in rows
        if (r.get('external_integration') or {}).get('triggers_on') == 'audio_bytes'
    )


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def add_app(app_data: dict) -> None:
    _upsert(_app_data_to_row(app_data))


def upsert_app(app_data: dict) -> None:
    _upsert(_app_data_to_row(app_data))


def update_app(app_data: dict) -> None:
    app_id = app_data.get('id')
    if not app_id:
        return
    row = _app_data_to_row(app_data)
    row.pop('id', None)
    _patch(app_id, row)


def delete_app(app_id: str) -> None:
    _patch(app_id, {'deleted': True})


def update_app_visibility(app_id: str, private: bool) -> None:
    _patch(app_id, {'private': private})


def change_app_approval(app_id: str, approved: bool) -> None:
    _patch(app_id, {'approved': approved, 'status': 'approved' if approved else 'rejected'})


# ---------------------------------------------------------------------------
# User enabled apps
# ---------------------------------------------------------------------------

def get_enabled_app_ids(uid: str) -> List[str]:
    if not _is_configured():
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{_ENABLED_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'return=representation'},
                params={'uid': f'eq.{uid}', 'select': 'app_id'},
            )
            if resp.status_code == 200:
                return [r['app_id'] for r in resp.json()]
    except Exception as exc:
        logger.error('supabase user_enabled_apps GET error: %s', exc)
    return []


def enable_app(uid: str, app_id: str) -> None:
    if not _is_configured():
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(
                f'{_SUPABASE_URL}/rest/v1/{_ENABLED_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'resolution=ignore-duplicates'},
                json={'uid': uid, 'app_id': app_id},
            )
    except Exception as exc:
        logger.error('supabase user_enabled_apps POST error: %s', exc)


def disable_app(uid: str, app_id: str) -> None:
    if not _is_configured():
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            client.delete(
                f'{_SUPABASE_URL}/rest/v1/{_ENABLED_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'app_id': f'eq.{app_id}'},
            )
    except Exception as exc:
        logger.error('supabase user_enabled_apps DELETE error: %s', exc)


# ---------------------------------------------------------------------------
# Personas (special apps with 'persona' capability)
# ---------------------------------------------------------------------------

def get_persona_by_id(persona_id: str) -> Optional[Dict[str, Any]]:
    rows = _get({'id': f'eq.{persona_id}', 'deleted': 'eq.false', 'limit': '1'})
    return _app_row_to_dict(rows[0]) if rows else None


def get_persona_by_username(username: str) -> Optional[Dict[str, Any]]:
    rows = _get({
        'username': f'eq.{username}',
        'capabilities': 'cs.["persona"]',
        'deleted': 'eq.false',
        'limit': '1'
    })
    return _app_row_to_dict(rows[0]) if rows else None


def get_personas_by_username(username: str) -> List[Dict[str, Any]]:
    rows = _get({
        'username': f'eq.{username}',
        'deleted': 'eq.false'
    })
    return [_app_row_to_dict(r) for r in rows]


def get_persona_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    rows = _get({
        'uid': f'eq.{uid}',
        'capabilities': 'cs.["persona"]',
        'deleted': 'eq.false',
        'limit': '1'
    })
    return _app_row_to_dict(rows[0]) if rows else None


def get_user_persona_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    rows = _get({
        'uid': f'eq.{uid}',
        'category': 'eq.personality-emulation',
        'capabilities': 'cs.["persona"]',
        'deleted': 'eq.false',
        'limit': '1'
    })
    if rows:
        persona = _app_row_to_dict(rows[0])
        return {'id': persona.get('id'), **persona}
    return None


def get_persona_by_twitter_handle(handle: str) -> Optional[Dict[str, Any]]:
    rows = _get({
        'category': 'eq.personality-emulation',
        'deleted': 'eq.false'
    })
    for row in rows:
        if row.get('metadata', {}).get('twitter', {}).get('username') == handle:
            return _app_row_to_dict(row)
    return None


def get_persona_by_username_twitter_handle(username: str, handle: str) -> Optional[Dict[str, Any]]:
    rows = _get({
        'username': f'eq.{username}',
        'category': 'eq.personality-emulation',
        'deleted': 'eq.false'
    })
    for row in rows:
        if row.get('metadata', {}).get('twitter', {}).get('username') == handle:
            return _app_row_to_dict(row)
    return None


def get_omi_personas_by_uid(uid: str) -> List[Dict[str, Any]]:
    rows = _get({
        'uid': f'eq.{uid}',
        'capabilities': 'cs.["persona"]',
        'deleted': 'eq.false'
    })
    personas = []
    for row in rows:
        persona = _app_row_to_dict(row)
        if 'omi' in persona.get('connected_accounts', []):
            personas.append(persona)
    return personas


def get_omi_persona_apps_by_uid(uid: str) -> List[Dict[str, Any]]:
    rows = _get({
        'uid': f'eq.{uid}',
        'category': 'eq.personality-emulation',
        'deleted': 'eq.false'
    })
    return [_app_row_to_dict(r) for r in rows]


def delete_persona(persona_id: str) -> None:
    _patch(persona_id, {'deleted': True})


def update_persona(persona_data: dict) -> None:
    update_app(persona_data)


def migrate_app_owner_id(new_id: str, old_id: str) -> None:
    """Migrate all apps from old_id to new_id (used when user ID changes)."""
    if not _is_configured():
        return
    try:
        rows = _get({'uid': f'eq.{old_id}'})
        for row in rows:
            _patch(row['id'], {'uid': new_id})
    except Exception as exc:
        logger.error('supabase migrate_app_owner_id error: %s', exc)


# ---------------------------------------------------------------------------
# API Keys (not implemented in OSS+ mode — would need separate key_hash table)
# ---------------------------------------------------------------------------

def create_api_key(app_id: str, api_key_data: dict) -> Optional[Dict[str, Any]]:
    # API keys would need a separate table in Supabase
    # For now, stub out in OSS+ mode
    logger.warning('api key creation not implemented in OSS+ mode')
    return api_key_data


def get_api_key_by_hash(app_id: str, hashed_key: str) -> Optional[Dict[str, Any]]:
    logger.warning('api key lookup not implemented in OSS+ mode')
    return None


def list_api_keys(app_id: str) -> List[Dict[str, Any]]:
    logger.warning('api key listing not implemented in OSS+ mode')
    return []


def delete_api_key(app_id: str, key_id: str) -> bool:
    logger.warning('api key deletion not implemented in OSS+ mode')
    return True


# ---------------------------------------------------------------------------
# Reviews (not implemented in OSS+ mode — no approval process)
# ---------------------------------------------------------------------------

def set_app_review(app_id: str, uid: str, review: dict) -> None:
    # Reviews would need a separate reviews sub-collection
    # In OSS+ mode, skip
    logger.warning('app reviews not implemented in OSS+ mode')


# ---------------------------------------------------------------------------
# Testers (not implemented in OSS+ mode — no app testing program)
# ---------------------------------------------------------------------------

def add_tester(data: dict) -> None:
    logger.warning('tester management not implemented in OSS+ mode')


def add_app_access_for_tester(app_id: str, uid: str) -> None:
    logger.warning('tester access not implemented in OSS+ mode')


def remove_app_access_for_tester(app_id: str, uid: str) -> None:
    logger.warning('tester access not implemented in OSS+ mode')


def remove_tester(uid: str) -> None:
    logger.warning('tester removal not implemented in OSS+ mode')


def can_tester_access_app(app_id: str, uid: str) -> bool:
    return False


def is_tester(uid: str) -> bool:
    return False


def get_apps_for_tester(uid: str) -> List[Dict[str, Any]]:
    return []
