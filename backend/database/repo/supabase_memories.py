"""
Supabase Postgres implementation of MemoryRepo.

Memory content is encrypted at rest using AES-256-GCM (ENCRYPTION_SECRET env var).
Disable via SUPABASE_ENCRYPT_MEMORIES=false.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'memories'
_ENCRYPT_MEMORIES = os.getenv('SUPABASE_ENCRYPT_MEMORIES', 'true').lower() != 'false'


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
            logger.warning('supabase memories GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase memories GET error: %s', exc)
    return []


def _post(data: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                json=data,
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.error('supabase memories POST error: %s', exc)
        return False


def _delete_by_uid(uid: str) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.delete(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}'},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase memories DELETE all error: %s', exc)
        return False


def _patch(uid: str, mid: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{mid}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase memories PATCH error: %s', exc)
        return False


def _encrypt_content(content: str, uid: str) -> str:
    from utils import encryption as _enc

    return _enc.encrypt(content, uid)


def _decrypt_content(cipher: str, uid: str) -> str:
    try:
        from utils import encryption as _enc

        return _enc.decrypt(cipher, uid)
    except Exception:
        logger.error('supabase: failed to decrypt memory content for uid=%s', uid)
        return ''


def _apply_memory_encryption(data: dict, uid: str) -> dict:
    if not _ENCRYPT_MEMORIES:
        return data
    if 'content' not in data or not isinstance(data['content'], str):
        return data
    data = {**data}
    data['content'] = _encrypt_content(data['content'], uid)
    data['content_encrypted'] = True
    return data


def _apply_memory_decryption(row: dict, uid: str) -> dict:
    if not row or not row.get('content_encrypted'):
        return row
    cipher = row.get('content', '')
    if isinstance(cipher, str) and cipher:
        row = {**row, 'content': _decrypt_content(cipher, uid)}
    return row


class SupabaseMemoryRepo:
    """MemoryRepo backed by Supabase Postgres REST API."""

    def upsert_memory(self, uid: str, memory_data: dict) -> None:
        data = _apply_memory_encryption({**memory_data, 'uid': uid}, uid)
        _post(data)

    def save_memories_batch(self, uid: str, memories: List[dict]) -> None:
        for memory in memories:
            self.upsert_memory(uid, memory)

    def get_memory(self, uid: str, memory_id: str) -> Optional[Dict[str, Any]]:
        rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{memory_id}', 'deleted': 'eq.false', 'limit': '1'})
        row = rows[0] if rows else None
        return _apply_memory_decryption(row, uid) if row else None

    def get_memories(
        self,
        uid: str,
        limit: int = 100,
        offset: int = 0,
        visibility: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: dict = {
            'uid': f'eq.{uid}',
            'deleted': 'eq.false',
            'order': 'created_at.desc',
            'limit': str(limit),
            'offset': str(offset),
        }
        if visibility:
            params['visibility'] = f'eq.{visibility}'
        rows = _get(params)
        return [_apply_memory_decryption(r, uid) for r in rows]

    def get_memories_by_ids(self, uid: str, memory_ids: List[str]) -> List[Dict[str, Any]]:
        if not memory_ids:
            return []
        id_list = ','.join(str(mid) for mid in memory_ids)
        rows = _get({'uid': f'eq.{uid}', 'id': f'in.({id_list})', 'deleted': 'eq.false'})
        return [_apply_memory_decryption(r, uid) for r in rows]

    def get_memory_ids_for_conversation(self, uid: str, conversation_id: str) -> List[str]:
        rows = _get(
            {'uid': f'eq.{uid}', 'conversation_id': f'eq.{conversation_id}', 'deleted': 'eq.false', 'select': 'id'}
        )
        return [r['id'] for r in rows if 'id' in r]

    def update_memory(self, uid: str, memory_id: str, updates: dict) -> None:
        _patch(uid, memory_id, updates)

    def delete_memory(self, uid: str, memory_id: str) -> None:
        _patch(uid, memory_id, {'deleted': True})

    def delete_all_memories(self, uid: str) -> None:
        _delete_by_uid(uid)
