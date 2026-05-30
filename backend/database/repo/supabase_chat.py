"""
Supabase implementation for chat messages and sessions.

Replaces Firestore sub-collections:
  - users/{uid}/messages        → chat_messages table
  - users/{uid}/chat_sessions   → chat_sessions  table
  - users/{uid}/files           → chat_files     table

Message text is encrypted at rest (same key as memories, toggled by SUPABASE_ENCRYPT_MEMORIES).
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_ENCRYPT = os.getenv('SUPABASE_ENCRYPT_MEMORIES', 'true').lower() != 'false'


def _get(table: str, params: dict) -> list:
    if not _is_configured():
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers={**_rest_headers(), 'Prefer': 'return=representation'},
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning('supabase %s GET %s: %s', table, resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase %s GET error: %s', table, exc)
    return []


def _post(table: str, data: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers=_rest_headers(),
                json=data,
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.error('supabase %s POST error: %s', table, exc)
        return False


def _patch(table: str, params: dict, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers=_rest_headers(),
                params=params,
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase %s PATCH error: %s', table, exc)
        return False


def _delete(table: str, params: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers=_rest_headers(),
                params=params,
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase %s DELETE error: %s', table, exc)
        return False


def _encrypt_text(text: str, uid: str) -> str:
    from utils import encryption as _enc

    return _enc.encrypt(text, uid)


def _decrypt_text(cipher: str, uid: str) -> str:
    try:
        from utils import encryption as _enc

        return _enc.decrypt(cipher, uid)
    except Exception:
        return ''


def _apply_msg_encrypt(data: dict, uid: str) -> dict:
    if not _ENCRYPT or 'text' not in data or not isinstance(data['text'], str):
        return data
    data = {**data, 'text': _encrypt_text(data['text'], uid), 'content_encrypted': True}
    return data


def _apply_msg_decrypt(row: dict, uid: str) -> dict:
    if not row or not row.get('content_encrypted'):
        return row
    cipher = row.get('text', '')
    if isinstance(cipher, str) and cipher:
        row = {**row, 'text': _decrypt_text(cipher, uid)}
    return row


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


def add_message(uid: str, message_data: dict) -> None:
    data = {**message_data, 'uid': uid}
    data.pop('memories', None)
    data.pop('data_protection_level', None)
    if not data.get('id'):
        data['id'] = str(uuid.uuid4())
    data = _apply_msg_encrypt(data, uid)
    _post('chat_messages', data)


def get_messages(
    uid: str,
    limit: int = 20,
    offset: int = 0,
    session_id: Optional[str] = None,
    app_id: Optional[str] = None,
) -> list:
    params: dict = {
        'uid': f'eq.{uid}',
        'deleted': 'eq.false',
        'order': 'created_at.asc',
        'limit': str(limit),
        'offset': str(offset),
    }
    if session_id:
        params['session_id'] = f'eq.{session_id}'
    if app_id:
        params['plugin_id'] = f'eq.{app_id}'
    rows = _get('chat_messages', params)
    return [_apply_msg_decrypt(r, uid) for r in rows]


def clear_chat(uid: str, session_id: Optional[str] = None) -> None:
    params: dict = {'uid': f'eq.{uid}'}
    if session_id:
        params['session_id'] = f'eq.{session_id}'
    _patch('chat_messages', params, {'deleted': True})


def get_message_count(uid: str) -> int:
    if not _is_configured():
        return 0
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/chat_messages',
                headers={**_rest_headers(), 'Prefer': 'count=exact'},
                params={'uid': f'eq.{uid}', 'deleted': 'eq.false', 'select': 'id', 'limit': '0'},
            )
            cr = resp.headers.get('Content-Range', '')
            if '/' in cr:
                return int(cr.split('/')[-1])
    except Exception as exc:
        logger.error('supabase chat_messages count error: %s', exc)
    return 0


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


def add_chat_session(uid: str, data: dict) -> None:
    _post('chat_sessions', {**data, 'uid': uid})


def get_chat_session(uid: str, app_id: Optional[str] = None) -> Optional[dict]:
    params: dict = {'uid': f'eq.{uid}', 'deleted': 'eq.false', 'order': 'created_at.desc', 'limit': '1'}
    if app_id:
        params['plugin_id'] = f'eq.{app_id}'
    rows = _get('chat_sessions', params)
    return rows[0] if rows else None


def get_chat_session_by_id(uid: str, session_id: str) -> Optional[dict]:
    rows = _get('chat_sessions', {'uid': f'eq.{uid}', 'id': f'eq.{session_id}', 'deleted': 'eq.false', 'limit': '1'})
    return rows[0] if rows else None


def get_all_chat_sessions(uid: str, limit: int = 50, offset: int = 0) -> list:
    return _get(
        'chat_sessions',
        {
            'uid': f'eq.{uid}',
            'deleted': 'eq.false',
            'order': 'updated_at.desc',
            'limit': str(limit),
            'offset': str(offset),
        },
    )


def delete_chat_session(uid: str, session_id: str) -> None:
    _patch('chat_sessions', {'uid': f'eq.{uid}', 'id': f'eq.{session_id}'}, {'deleted': True})
    _patch('chat_messages', {'uid': f'eq.{uid}', 'session_id': f'eq.{session_id}'}, {'deleted': True})


def update_chat_session(uid: str, session_id: str, updates: dict) -> None:
    _patch('chat_sessions', {'uid': f'eq.{uid}', 'id': f'eq.{session_id}'}, updates)
