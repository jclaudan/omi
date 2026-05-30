"""
Supabase Postgres implementation of ConversationRepo.

Uses the Supabase REST API via httpx — no extra Python packages needed.
Env vars: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Transcript segments are encrypted at rest using the same AES-256-GCM key
derivation as the Firestore backend (ENCRYPTION_SECRET env var).
Enable by setting SUPABASE_ENCRYPT_SEGMENTS=true (default: true when key is available).
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _SUPABASE_SERVICE_KEY, _is_configured, _rest_headers

_ENCRYPT_SEGMENTS = os.getenv('SUPABASE_ENCRYPT_SEGMENTS', 'true').lower() != 'false'

logger = logging.getLogger(__name__)

_TABLE = 'conversations'


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
            logger.warning('supabase conversations GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase conversations GET error: %s', exc)
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
        logger.error('supabase conversations POST error: %s', exc)
        return False


def _patch(uid: str, cid: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{cid}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase conversations PATCH error: %s', exc)
        return False


def _encrypt_segments(segments: list, uid: str) -> str:
    """Serialize and encrypt transcript_segments. Returns cipher string."""
    from utils import encryption as _enc

    return _enc.encrypt(json.dumps(segments), uid)


def _decrypt_segments(cipher: str, uid: str) -> list:
    """Decrypt and deserialize transcript_segments. Returns list on error."""
    try:
        from utils import encryption as _enc

        return json.loads(_enc.decrypt(cipher, uid))
    except Exception:
        logger.error('supabase: failed to decrypt transcript_segments for uid=%s', uid)
        return []


def _apply_encryption(data: dict, uid: str) -> dict:
    """Encrypt transcript_segments in-place if configured."""
    if not _ENCRYPT_SEGMENTS:
        return data
    if 'transcript_segments' not in data or not isinstance(data['transcript_segments'], list):
        return data
    data = {**data}
    data['transcript_segments'] = _encrypt_segments(data['transcript_segments'], uid)
    data['transcript_segments_encrypted'] = True
    return data


def _apply_decryption(row: dict, uid: str) -> dict:
    """Decrypt transcript_segments in a row returned from Supabase."""
    if not row or not row.get('transcript_segments_encrypted'):
        return row
    cipher = row.get('transcript_segments', '')
    if isinstance(cipher, str) and cipher:
        row = {**row, 'transcript_segments': _decrypt_segments(cipher, uid)}
    return row


class SupabaseConversationRepo:
    """ConversationRepo backed by Supabase Postgres REST API."""

    def upsert_conversation(self, uid: str, conversation_data: dict) -> None:
        data = {**conversation_data, 'uid': uid}
        # Strip heavy / volatile fields that live elsewhere
        data.pop('audio_base64_url', None)
        data.pop('photos', None)
        data = _apply_encryption(data, uid)
        _post(data)

    def get_conversation(self, uid: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{conversation_id}', 'limit': '1'})
        row = rows[0] if rows else None
        return _apply_decryption(row, uid) if row else None

    def get_conversations(
        self,
        uid: str,
        limit: int = 100,
        offset: int = 0,
        include_discarded: bool = False,
    ) -> List[Dict[str, Any]]:
        params: dict = {
            'uid': f'eq.{uid}',
            'deleted': 'eq.false',
            'order': 'created_at.desc',
            'limit': str(limit),
            'offset': str(offset),
        }
        if not include_discarded:
            params['discarded'] = 'eq.false'
        rows = _get(params)
        return [_apply_decryption(r, uid) for r in rows]

    def update_conversation(self, uid: str, conversation_id: str, updates: dict) -> None:
        if 'transcript_segments' in updates and isinstance(updates['transcript_segments'], list):
            updates = _apply_encryption(dict(updates), uid)
        _patch(uid, conversation_id, updates)

    def delete_conversation(self, uid: str, conversation_id: str) -> None:
        _patch(uid, conversation_id, {'deleted': True})

    def conversation_exists(self, uid: str, conversation_id: str) -> bool:
        return self.get_conversation(uid, conversation_id) is not None

    def get_conversations_count(self, uid: str, include_discarded: bool = False, statuses: List[str] = []) -> int:
        if not _is_configured():
            return 0
        try:
            params: dict = {'uid': f'eq.{uid}', 'deleted': 'eq.false', 'select': 'id'}
            if not include_discarded:
                params['discarded'] = 'eq.false'
            if statuses:
                params['status'] = f'in.({",".join(statuses)})'
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                    headers={**_rest_headers(), 'Prefer': 'count=exact'},
                    params={**params, 'limit': '0'},
                )
                cr = resp.headers.get('Content-Range', '')
                if '/' in cr:
                    return int(cr.split('/')[-1])
        except Exception as exc:
            logger.error('supabase conversations count error: %s', exc)
        return 0

    def get_conversations_by_id(self, uid: str, conversation_ids: List[str]) -> List[Dict[str, Any]]:
        if not conversation_ids:
            return []
        id_list = ','.join(str(cid) for cid in conversation_ids)
        rows = _get({'uid': f'eq.{uid}', 'id': f'in.({id_list})', 'deleted': 'eq.false', 'discarded': 'eq.false'})
        return [_apply_decryption(r, uid) for r in rows]

    def get_by_status(self, uid: str, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        rows = _get(
            {
                'uid': f'eq.{uid}',
                'status': f'eq.{status}',
                'deleted': 'eq.false',
                'order': 'created_at.desc',
                'limit': str(limit),
            }
        )
        return [_apply_decryption(r, uid) for r in rows]
