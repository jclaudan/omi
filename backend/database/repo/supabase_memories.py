"""
Supabase Postgres implementation of MemoryRepo.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'memories'


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


class SupabaseMemoryRepo:
    """MemoryRepo backed by Supabase Postgres REST API."""

    def upsert_memory(self, uid: str, memory_data: dict) -> None:
        _post({**memory_data, 'uid': uid})

    def get_memory(self, uid: str, memory_id: str) -> Optional[Dict[str, Any]]:
        rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{memory_id}', 'deleted': 'eq.false', 'limit': '1'})
        return rows[0] if rows else None

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
        return _get(params)

    def update_memory(self, uid: str, memory_id: str, updates: dict) -> None:
        _patch(uid, memory_id, updates)

    def delete_memory(self, uid: str, memory_id: str) -> None:
        _patch(uid, memory_id, {'deleted': True})
