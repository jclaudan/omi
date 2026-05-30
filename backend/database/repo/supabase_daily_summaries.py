"""
Supabase implementation for daily summaries.
Replaces Firestore users/{uid}/daily_summaries sub-collection.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'daily_summaries'


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
            logger.warning('supabase daily_summaries GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase daily_summaries GET error: %s', exc)
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
        logger.error('supabase daily_summaries UPSERT error: %s', exc)
        return False


def _patch(uid: str, summary_id: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{summary_id}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase daily_summaries PATCH error: %s', exc)
        return False


def _delete(uid: str, summary_id: str) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{summary_id}'},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase daily_summaries DELETE error: %s', exc)
        return False


def create_daily_summary(uid: str, summary_data: dict) -> str:
    """Create a new daily summary."""
    row = {**summary_data, 'uid': uid}
    _upsert(row)
    return summary_data.get('id', '')


def get_daily_summary(uid: str, summary_id: str) -> Optional[Dict[str, Any]]:
    """Get a single daily summary by ID."""
    rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{summary_id}', 'limit': '1'})
    return rows[0] if rows else None


def get_daily_summary_by_date(uid: str, date: str) -> Optional[Dict[str, Any]]:
    """Get a daily summary by date (YYYY-MM-DD format)."""
    rows = _get({'uid': f'eq.{uid}', 'date': f'eq.{date}', 'limit': '1'})
    return rows[0] if rows else None


def get_daily_summaries(
    uid: str,
    limit: int = 30,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get list of daily summaries for a user, ordered by date descending."""
    params = {'uid': f'eq.{uid}', 'order': 'date.desc'}

    if start_date:
        params['date'] = f'gte.{start_date}'
    if end_date:
        if 'date' in params:
            # Both start and end - need to use and logic
            params['and'] = f"(date.gte.{start_date},date.lte.{end_date})"
        else:
            params['date'] = f'lte.{end_date}'

    params['limit'] = str(limit)
    params['offset'] = str(offset)

    return _get(params)


def delete_daily_summary(uid: str, summary_id: str) -> bool:
    """Delete a daily summary."""
    return _delete(uid, summary_id)


def set_daily_summary_visibility(uid: str, summary_id: str, visibility: str) -> bool:
    """Set visibility of a daily summary."""
    return _patch(uid, summary_id, {'visibility': visibility})


def get_summaries_count(uid: str) -> int:
    """Get total count of daily summaries for a user."""
    if not _is_configured():
        return 0
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'count=exact'},
                params={'uid': f'eq.{uid}', 'select': 'id'},
            )
            if resp.status_code == 200:
                count = resp.headers.get('content-range', '').split('/')[-1]
                return int(count) if count else 0
    except Exception as exc:
        logger.error('supabase daily_summaries count error: %s', exc)
    return 0
