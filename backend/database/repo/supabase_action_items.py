"""
Supabase Postgres implementation of ActionItemRepo.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'action_items'


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
            logger.warning('supabase action_items GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase action_items GET error: %s', exc)
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
        logger.error('supabase action_items POST error: %s', exc)
        return False


def _patch(uid: str, aid: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{aid}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase action_items PATCH error: %s', exc)
        return False


class SupabaseActionItemRepo:
    """ActionItemRepo backed by Supabase Postgres REST API."""

    def create_action_item(self, uid: str, action_item_data: dict) -> str:
        item_id = action_item_data.get('id') or str(uuid.uuid4())
        data = {**action_item_data, 'id': item_id, 'uid': uid}
        _post(data)
        return item_id

    def get_action_item(self, uid: str, action_item_id: str) -> Optional[Dict[str, Any]]:
        rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{action_item_id}', 'deleted': 'eq.false', 'limit': '1'})
        return rows[0] if rows else None

    def get_action_items(
        self,
        uid: str,
        completed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        params: dict = {
            'uid': f'eq.{uid}',
            'deleted': 'eq.false',
            'order': 'created_at.desc',
            'limit': str(limit),
            'offset': str(offset),
        }
        if completed is not None:
            params['completed'] = f'eq.{str(completed).lower()}'
        return _get(params)

    def update_action_item(self, uid: str, action_item_id: str, updates: dict) -> None:
        _patch(uid, action_item_id, updates)

    def delete_action_item(self, uid: str, action_item_id: str) -> None:
        _patch(uid, action_item_id, {'deleted': True})
