"""
Supabase implementation for goals and goal history.
Replaces Firestore users/{uid}/goals and users/{uid}/goals/{goal_id}/goal_history sub-collections.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_GOALS_TABLE = 'goals'
_HISTORY_TABLE = 'goal_history'


def _get_goals(params: dict) -> list:
    if not _is_configured():
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{_GOALS_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'return=representation'},
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning('supabase goals GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase goals GET error: %s', exc)
    return []


def _get_history(params: dict) -> list:
    if not _is_configured():
        return []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f'{_SUPABASE_URL}/rest/v1/{_HISTORY_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'return=representation'},
                params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning('supabase goal_history GET %s: %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error('supabase goal_history GET error: %s', exc)
    return []


def _upsert_goal(data: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/{_GOALS_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'resolution=merge-duplicates'},
                json=data,
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.error('supabase goals UPSERT error: %s', exc)
        return False


def _patch_goal(uid: str, goal_id: str, updates: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.patch(
                f'{_SUPABASE_URL}/rest/v1/{_GOALS_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{goal_id}'},
                json={**updates, 'updated_at': datetime.now(timezone.utc).isoformat()},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase goals PATCH error: %s', exc)
        return False


def _delete_goal(uid: str, goal_id: str) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(
                f'{_SUPABASE_URL}/rest/v1/{_GOALS_TABLE}',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{goal_id}'},
            )
            return resp.status_code in (200, 204)
    except Exception as exc:
        logger.error('supabase goals DELETE error: %s', exc)
        return False


def _upsert_history(data: dict) -> bool:
    if not _is_configured():
        return False
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f'{_SUPABASE_URL}/rest/v1/{_HISTORY_TABLE}',
                headers={**_rest_headers(), 'Prefer': 'resolution=merge-duplicates'},
                json=data,
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.error('supabase goal_history UPSERT error: %s', exc)
        return False


# --- Goals CRUD ---

def get_user_goal(uid: str) -> Optional[Dict[str, Any]]:
    """Get the current active goal for a user (returns first active goal)."""
    rows = _get_goals({'uid': f'eq.{uid}', 'is_active': 'eq.true', 'order': 'created_at.asc', 'limit': '1'})
    return rows[0] if rows else None


def get_user_goals(uid: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Get all active goals for a user."""
    rows = _get_goals({
        'uid': f'eq.{uid}',
        'is_active': 'eq.true',
        'order': 'created_at.asc',
        'limit': str(limit)
    })
    return rows


def create_goal(uid: str, goal_data: Dict[str, Any], max_goals: int = 4) -> Dict[str, Any]:
    """Create a new goal for a user. Supports up to max_goals active goals."""
    # Check current active goal count
    active_goals = _get_goals({'uid': f'eq.{uid}', 'is_active': 'eq.true'})

    # If at max, deactivate the oldest one
    if len(active_goals) >= max_goals:
        oldest = min(active_goals, key=lambda x: x.get('created_at', ''))
        _patch_goal(uid, oldest['id'], {'is_active': False, 'ended_at': datetime.now(timezone.utc).isoformat()})

    # Create new goal
    goal_data['uid'] = uid
    goal_data['is_active'] = True
    goal_data['created_at'] = datetime.now(timezone.utc).isoformat()
    goal_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    _upsert_goal(goal_data)
    return goal_data


def update_goal(uid: str, goal_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing goal."""
    if _patch_goal(uid, goal_id, updates):
        return get_user_goal(uid)  # Return updated goal
    return None


def update_goal_progress(uid: str, goal_id: str, current_value: float) -> Optional[Dict[str, Any]]:
    """Update the current progress value of a goal."""
    if _patch_goal(uid, goal_id, {'current_value': current_value}):
        save_goal_progress_history(uid, goal_id, current_value)
        return get_user_goal(uid)
    return None


def delete_goal(uid: str, goal_id: str) -> bool:
    """Delete a goal."""
    return _delete_goal(uid, goal_id)


def get_all_goals(uid: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all goals for a user."""
    params = {'uid': f'eq.{uid}', 'order': 'created_at.desc'}
    if not include_inactive:
        params['is_active'] = 'eq.true'
    return _get_goals(params)


# --- Goal History ---

def save_goal_progress_history(uid: str, goal_id: str, value: float) -> None:
    """Save a progress data point to history."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    history_data = {
        'uid': uid,
        'goal_id': goal_id,
        'date': today,
        'value': value,
        'recorded_at': datetime.now(timezone.utc).isoformat(),
    }
    _upsert_history(history_data)


def get_goal_history(uid: str, goal_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get progress history for a goal."""
    rows = _get_history({
        'uid': f'eq.{uid}',
        'goal_id': f'eq.{goal_id}',
        'order': 'date.desc',
        'limit': str(days)
    })
    return rows
