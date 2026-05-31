"""
Supabase implementation for user profiles, integrations, and people.

Replaces Firestore users/{uid} document and sub-collections:
  - integrations/{app_key}      → user_integrations table
  - task_integrations/{app_key} → user_task_integrations table
  - people/{person_id}          → people table (already exists from Etape 7)

In OSS+ self-hosted mode, subscriptions are treated as always-valid (no paywall).
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from utils.oss_supabase_client import _SUPABASE_URL, _is_configured, _rest_headers

logger = logging.getLogger(__name__)

_ENCRYPT_USER = os.getenv('SUPABASE_ENCRYPT_USER', 'false').lower() == 'true'

# ---------------------------------------------------------------------------
# Generic REST helpers
# ---------------------------------------------------------------------------


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
                headers={**_rest_headers(), 'Prefer': 'resolution=merge-duplicates'},
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


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

_OSS_SUBSCRIPTION = {
    'plan': 'pro',
    'status': 'active',
    'type': 'oss_plus',
    'is_oss': True,
}


def _profile_row_to_dict(row: dict) -> dict:
    """Convert a profiles row to a Firestore-compatible user dict."""
    out: dict = {
        'uid': str(row.get('id', '')),
        'name': row.get('name', ''),
        'email': row.get('email', ''),
        'language': row.get('language', 'en'),
        'store_recording_permission': row.get('store_recording_permission', False),
        'private_cloud_sync_enabled': row.get('private_cloud_sync_enabled', True),
        'data_protection_level': row.get('data_protection_level', 'standard'),
        'stripe_customer_id': row.get('stripe_customer_id'),
        'subscription': row.get('subscription') or _OSS_SUBSCRIPTION,
        'byok': row.get('byok') or {},
        'transcription_preferences': row.get('transcription_prefs') or {},
        'notification_settings': row.get('notification_settings') or {},
        'assistant_settings': row.get('assistant_settings') or {},
        'ai_user_profile': row.get('ai_profile') or {},
        'speaker_embedding': row.get('speaker_embedding'),
    }
    # Merge any extra metadata fields
    out.update(row.get('metadata') or {})
    return out


def get_user_profile(uid: str) -> dict:
    rows = _get('profiles', {'id': f'eq.{uid}', 'limit': '1'})
    if not rows:
        return {}
    return _profile_row_to_dict(rows[0])


def is_exists_user(uid: str) -> bool:
    rows = _get('profiles', {'id': f'eq.{uid}', 'select': 'id', 'limit': '1'})
    return bool(rows)


def upsert_user_profile(uid: str, data: dict) -> None:
    """Upsert a user profile. Maps Firestore fields to Supabase columns."""
    row: dict = {'id': uid}
    for fs_key, col in [
        ('name', 'name'),
        ('email', 'email'),
        ('language', 'language'),
        ('store_recording_permission', 'store_recording_permission'),
        ('private_cloud_sync_enabled', 'private_cloud_sync_enabled'),
        ('data_protection_level', 'data_protection_level'),
        ('stripe_customer_id', 'stripe_customer_id'),
    ]:
        if fs_key in data:
            row[col] = data[fs_key]

    for fs_key, col in [
        ('subscription', 'subscription'),
        ('byok', 'byok'),
        ('transcription_preferences', 'transcription_prefs'),
        ('notification_settings', 'notification_settings'),
        ('assistant_settings', 'assistant_settings'),
        ('ai_user_profile', 'ai_profile'),
        ('speaker_embedding', 'speaker_embedding'),
    ]:
        if fs_key in data:
            row[col] = data[fs_key]

    # Remaining fields go to metadata
    known = {
        'name',
        'email',
        'language',
        'store_recording_permission',
        'private_cloud_sync_enabled',
        'data_protection_level',
        'stripe_customer_id',
        'subscription',
        'byok',
        'transcription_preferences',
        'notification_settings',
        'assistant_settings',
        'ai_user_profile',
        'speaker_embedding',
    }
    extra = {k: v for k, v in data.items() if k not in known}
    if extra:
        row['metadata'] = extra

    _post('profiles', row)


def patch_user_field(uid: str, field: str, value: Any) -> None:
    """Update a single typed column on the profiles table."""
    _patch('profiles', {'id': f'eq.{uid}'}, {field: value})


def patch_user_metadata(uid: str, key: str, value: Any) -> None:
    """Merge a key into the metadata JSONB column."""
    if not _is_configured():
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            # Use Postgres jsonb_set via RPC or plain PATCH with jsonb merge
            client.patch(
                f'{_SUPABASE_URL}/rest/v1/profiles',
                headers=_rest_headers(),
                params={'id': f'eq.{uid}'},
                json={'metadata': {key: value}},
            )
    except Exception as exc:
        logger.error('supabase profiles patch_metadata error: %s', exc)


def get_user_field(uid: str, field: str, default: Any = None) -> Any:
    """Read a single field from the profiles row."""
    rows = _get('profiles', {'id': f'eq.{uid}', 'select': field, 'limit': '1'})
    if not rows:
        return default
    return rows[0].get(field, default)


# ---------------------------------------------------------------------------
# Speaker embeddings (user's own embedding stored on profiles)
# ---------------------------------------------------------------------------


def get_user_speaker_embedding(uid: str) -> Optional[list]:
    return get_user_field(uid, 'speaker_embedding')


def set_user_speaker_embedding(uid: str, embedding: list) -> None:
    patch_user_field(uid, 'speaker_embedding', embedding)


def set_user_oss_llm_config(uid: str, config: dict) -> None:
    """Set the OSS+ LLM provider configuration for a user."""
    patch_user_field(uid, 'oss_llm_config', config)


# ---------------------------------------------------------------------------
# People (already in `people` table from Etape 7, read via REST)
# ---------------------------------------------------------------------------


def get_people(uid: str) -> List[dict]:
    return _get('people', {'uid': f'eq.{uid}', 'order': 'created_at.desc'})


def get_person(uid: str, person_id: str) -> Optional[dict]:
    rows = _get('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}', 'limit': '1'})
    return rows[0] if rows else None


def get_people_by_ids(uid: str, person_ids: list) -> List[dict]:
    if not person_ids:
        return []
    id_list = ','.join(str(pid) for pid in person_ids)
    return _get('people', {'uid': f'eq.{uid}', 'id': f'in.({id_list})'})


def get_person_by_name(uid: str, name: str) -> Optional[dict]:
    rows = _get('people', {'uid': f'eq.{uid}', 'name': f'ilike.{name}', 'limit': '1'})
    return rows[0] if rows else None


def create_person(uid: str, data: dict) -> None:
    _post('people', {**data, 'uid': uid})


def update_person(uid: str, person_id: str, name: str) -> None:
    _patch('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'}, {'name': name})


def delete_person(uid: str, person_id: str) -> None:
    if not _is_configured():
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            client.delete(
                f'{_SUPABASE_URL}/rest/v1/people',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'id': f'eq.{person_id}'},
            )
    except Exception as exc:
        logger.error('supabase people DELETE error: %s', exc)


def patch_person(uid: str, person_id: str, updates: dict) -> None:
    _patch('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'}, updates)


def get_person_speaker_embedding(uid: str, person_id: str) -> Optional[list]:
    rows = _get('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}', 'select': 'speaker_embedding', 'limit': '1'})
    if not rows:
        return None
    return rows[0].get('speaker_embedding')


def set_person_speaker_embedding(uid: str, person_id: str, embedding: list) -> None:
    _patch('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'}, {'speaker_embedding': embedding})


def clear_person_speaker_embedding(uid: str, person_id: str) -> None:
    _patch('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'}, {'speaker_embedding': None})


def add_person_speech_sample(uid: str, person_id: str, sample_path: str, transcript: str) -> None:
    """Append a speech sample to the person's speech_samples array."""
    rows = _get(
        'people',
        {
            'uid': f'eq.{uid}',
            'id': f'eq.{person_id}',
            'select': 'speech_samples,speech_sample_transcripts,speech_samples_version',
            'limit': '1',
        },
    )
    if not rows:
        return
    row = rows[0]
    samples = list(row.get('speech_samples') or [])
    transcripts = list(row.get('speech_sample_transcripts') or [])
    version = row.get('speech_samples_version', 1)
    samples.append(sample_path)
    transcripts.append(transcript)
    _patch(
        'people',
        {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'},
        {
            'speech_samples': samples,
            'speech_sample_transcripts': transcripts,
            'speech_samples_version': version,
        },
    )


def get_person_speech_samples_count(uid: str, person_id: str) -> int:
    rows = _get('people', {'uid': f'eq.{uid}', 'id': f'eq.{person_id}', 'select': 'speech_samples', 'limit': '1'})
    if not rows:
        return 0
    return len(rows[0].get('speech_samples') or [])


def remove_person_speech_sample(uid: str, person_id: str, sample_path: str) -> None:
    rows = _get(
        'people',
        {
            'uid': f'eq.{uid}',
            'id': f'eq.{person_id}',
            'select': 'speech_samples,speech_sample_transcripts',
            'limit': '1',
        },
    )
    if not rows:
        return
    samples = list(rows[0].get('speech_samples') or [])
    transcripts = list(rows[0].get('speech_sample_transcripts') or [])
    try:
        idx = samples.index(sample_path)
        samples.pop(idx)
        if idx < len(transcripts):
            transcripts.pop(idx)
    except ValueError:
        pass
    _patch(
        'people',
        {'uid': f'eq.{uid}', 'id': f'eq.{person_id}'},
        {
            'speech_samples': samples,
            'speech_sample_transcripts': transcripts,
        },
    )


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------


def get_integration(uid: str, app_key: str) -> Optional[dict]:
    rows = _get('user_integrations', {'uid': f'eq.{uid}', 'app_key': f'eq.{app_key}', 'limit': '1'})
    if not rows:
        return None
    return rows[0].get('data')


def set_integration(uid: str, app_key: str, data: dict) -> None:
    _post('user_integrations', {'uid': uid, 'app_key': app_key, 'data': data})


def delete_integration(uid: str, app_key: str) -> None:
    if not _is_configured():
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            client.delete(
                f'{_SUPABASE_URL}/rest/v1/user_integrations',
                headers=_rest_headers(),
                params={'uid': f'eq.{uid}', 'app_key': f'eq.{app_key}'},
            )
    except Exception as exc:
        logger.error('supabase user_integrations DELETE error: %s', exc)


# ---------------------------------------------------------------------------
# Task integrations
# ---------------------------------------------------------------------------


def get_task_integration(uid: str, app_key: str) -> Optional[dict]:
    rows = _get('user_task_integrations', {'uid': f'eq.{uid}', 'app_key': f'eq.{app_key}', 'limit': '1'})
    if not rows:
        return None
    return rows[0].get('data')


def set_task_integration(uid: str, app_key: str, data: dict) -> None:
    _post('user_task_integrations', {'uid': uid, 'app_key': app_key, 'data': data})


def get_default_task_integration(uid: str) -> Optional[str]:
    return get_user_field(uid, 'metadata', {}).get('default_task_integration')


def set_default_task_integration(uid: str, app_key: str) -> None:
    patch_user_metadata(uid, 'default_task_integration', app_key)
