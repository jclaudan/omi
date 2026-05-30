"""
Supabase Postgres implementation of ConversationRepo.

Uses the Supabase REST API via httpx — no extra Python packages needed.
Env vars: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _SUPABASE_SERVICE_KEY, _is_configured, _rest_headers

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


class SupabaseConversationRepo:
    """ConversationRepo backed by Supabase Postgres REST API."""

    def upsert_conversation(self, uid: str, conversation_data: dict) -> None:
        data = {**conversation_data, 'uid': uid}
        # Strip heavy / volatile fields that live elsewhere
        data.pop('audio_base64_url', None)
        data.pop('photos', None)
        _post(data)

    def get_conversation(self, uid: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{conversation_id}', 'limit': '1'})
        return rows[0] if rows else None

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
        return _get(params)

    def update_conversation(self, uid: str, conversation_id: str, updates: dict) -> None:
        _patch(uid, conversation_id, updates)

    def delete_conversation(self, uid: str, conversation_id: str) -> None:
        _patch(uid, conversation_id, {'deleted': True})

    def conversation_exists(self, uid: str, conversation_id: str) -> bool:
        return self.get_conversation(uid, conversation_id) is not None
