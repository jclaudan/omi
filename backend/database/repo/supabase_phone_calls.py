"""
Supabase implementation for verified phone numbers.
Replaces Firestore users/{uid}/phone_numbers sub-collection.
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_TABLE = 'phone_numbers'


def _hash_phone_number(phone_number: str) -> str:
    """Create a deterministic hash of a phone number for queryable lookup."""
    return hashlib.sha256(phone_number.encode('utf-8')).hexdigest()


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
            logger.warning('supabase phone_numbers GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase phone_numbers GET error: %s', exc)
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
        logger.error('supabase phone_numbers UPSERT error: %s', exc)
        return False


def _delete(uid: str, phone_id: str) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(
                f'{_SUPABASE_URL}/rest/v1/{_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{phone_id}'},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase phone_numbers DELETE error: %s', exc)
        return False


def upsert_phone_number(uid: str, phone_number_data: dict) -> None:
    """Create or update a verified phone number for a user."""
    data = {**phone_number_data, 'uid': uid}
    if phone_number_data.get('phone_number'):
        data['phone_number_hash'] = _hash_phone_number(phone_number_data['phone_number'])
    _upsert(data)


def get_phone_numbers(uid: str) -> List[Dict[str, Any]]:
    """Get all verified phone numbers for a user."""
    return _get({'uid': f'eq.{uid}'})


def get_phone_number(uid: str, phone_number_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific verified phone number."""
    rows = _get({'uid': f'eq.{uid}', 'id': f'eq.{phone_number_id}', 'limit': '1'})
    return rows[0] if rows else None


def get_phone_number_by_number(uid: str, phone_number: str) -> Optional[Dict[str, Any]]:
    """Get a verified phone number by the actual phone number string."""
    phone_hash = _hash_phone_number(phone_number)
    rows = _get({'uid': f'eq.{uid}', 'phone_number_hash': f'eq.{phone_hash}', 'limit': '1'})
    return rows[0] if rows else None


def delete_phone_number(uid: str, phone_number_id: str) -> bool:
    """Delete a verified phone number."""
    return _delete(uid, phone_number_id)
