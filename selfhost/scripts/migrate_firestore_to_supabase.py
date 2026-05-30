#!/usr/bin/env python3
"""
Migration script : Firestore → Supabase Postgres
================================================

Migrates data for one or all users from Firestore to the Supabase Postgres
tables created by selfhost/supabase/migrations/002_core_schema.sql.

Usage:
    # Migrate a single user
    python migrate_firestore_to_supabase.py --uid <firebase_uid> --supabase-uid <supabase_uuid>

    # Dry-run (shows counts, does not write)
    python migrate_firestore_to_supabase.py --uid <uid> --supabase-uid <uuid> --dry-run

    # Migrate all users (requires SERVICE_ACCOUNT_JSON)
    python migrate_firestore_to_supabase.py --all --dry-run

Prerequisites:
    pip install firebase-admin httpx python-dotenv

Environment variables (can also live in .env):
    SERVICE_ACCOUNT_JSON   — Firebase service account JSON string
    SUPABASE_URL           — https://your-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY — Supabase service role key
    ENCRYPTION_SECRET      — Required to decrypt Firestore encrypted fields
"""
import argparse
import json
import logging
import os
import sys
import uuid
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Validate env before heavy imports
# ---------------------------------------------------------------------------
_SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
_SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

if not _SUPABASE_URL or not _SUPABASE_KEY:
    logger.error('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set')
    sys.exit(1)

import firebase_admin
from firebase_admin import credentials, firestore
import httpx

# ---------------------------------------------------------------------------
# Supabase REST helpers
# ---------------------------------------------------------------------------


def _headers():
    return {
        'apikey': _SUPABASE_KEY,
        'Authorization': f'Bearer {_SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
    }


def _upsert(table: str, rows: list, dry_run: bool) -> int:
    if not rows:
        return 0
    if dry_run:
        logger.info('[dry-run] would upsert %d rows into %s', len(rows), table)
        return len(rows)
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f'{_SUPABASE_URL}/rest/v1/{table}', headers=_headers(), json=rows)
            if resp.status_code not in (200, 201):
                logger.warning('upsert %s returned %s: %s', table, resp.status_code, resp.text[:300])
                return 0
            return len(rows)
    except Exception as exc:
        logger.error('upsert %s error: %s', table, exc)
        return 0


# ---------------------------------------------------------------------------
# Firebase init
# ---------------------------------------------------------------------------


def _init_firebase():
    svc = os.environ.get('SERVICE_ACCOUNT_JSON')
    if svc:
        cred = credentials.Certificate(json.loads(svc))
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
    return firestore.client()


# ---------------------------------------------------------------------------
# Migration per user
# ---------------------------------------------------------------------------


def _migrate_user(db, firebase_uid: str, supabase_uid: str, dry_run: bool) -> dict:
    counts = {'conversations': 0, 'memories': 0, 'action_items': 0, 'people': 0}
    user_ref = db.collection('users').document(firebase_uid)

    if not user_ref.get().exists:
        logger.warning('User %s not found in Firestore', firebase_uid)
        return counts

    # ---- conversations ----
    conv_rows = []
    for doc in user_ref.collection('conversations').stream():
        data = doc.to_dict() or {}
        if data.get('deleted'):
            continue
        # Strip encrypted blobs — transcript_segments may be encrypted bytes.
        # In OSS+, we store segments as plain JSON. If they're encrypted we skip.
        segments = data.get('transcript_segments', [])
        if isinstance(segments, (bytes, str)) and not isinstance(segments, list):
            segments = []
        conv_rows.append({
            'id': doc.id,
            'uid': supabase_uid,
            'created_at': _ts(data.get('created_at')),
            'started_at': _ts(data.get('started_at')),
            'finished_at': _ts(data.get('finished_at')),
            'transcript_segments': json.dumps(segments),
            'summary': data.get('summary'),
            'overview': data.get('overview'),
            'title': data.get('structured', {}).get('title') if isinstance(data.get('structured'), dict) else None,
            'emoji': data.get('structured', {}).get('emoji') if isinstance(data.get('structured'), dict) else None,
            'category': data.get('structured', {}).get('category') if isinstance(data.get('structured'), dict) else None,
            'status': data.get('status', 'completed'),
            'source': data.get('source'),
            'language': data.get('language'),
            'structured': json.dumps(data.get('structured')),
            'apps_response': json.dumps(data.get('apps_response', [])),
            'discarded': bool(data.get('discarded', False)),
            'deleted': False,
            'geolocation': json.dumps(data.get('geolocation')) if data.get('geolocation') else None,
            'postprocessing': json.dumps(data.get('postprocessing')) if data.get('postprocessing') else None,
        })
    counts['conversations'] += _upsert('conversations', conv_rows, dry_run)

    # ---- memories ----
    mem_rows = []
    for doc in user_ref.collection('memories').stream():
        data = doc.to_dict() or {}
        if data.get('deleted'):
            continue
        content = data.get('content', '')
        if not isinstance(content, str):
            content = str(content)
        mem_rows.append({
            'id': doc.id,
            'uid': supabase_uid,
            'content': content,
            'category': data.get('category', 'interesting'),
            'visibility': data.get('visibility', 'private'),
            'tags': json.dumps(data.get('tags', [])),
            'headline': data.get('headline'),
            'created_at': _ts(data.get('created_at')),
            'updated_at': _ts(data.get('updated_at')),
            'deleted': False,
            'manual': bool(data.get('manual', False)),
            'scoring': json.dumps(data.get('scoring')) if data.get('scoring') else None,
        })
    counts['memories'] += _upsert('memories', mem_rows, dry_run)

    # ---- action_items ----
    ai_rows = []
    for doc in user_ref.collection('action_items').stream():
        data = doc.to_dict() or {}
        if data.get('deleted'):
            continue
        ai_rows.append({
            'id': doc.id,
            'uid': supabase_uid,
            'content': data.get('content', ''),
            'completed': bool(data.get('completed', False)),
            'created_at': _ts(data.get('created_at')),
            'updated_at': _ts(data.get('updated_at')),
            'due_at': _ts(data.get('due_at')),
            'completed_at': _ts(data.get('completed_at')),
            'deleted': False,
            'conversation_id': data.get('conversation_id'),
        })
    counts['action_items'] += _upsert('action_items', ai_rows, dry_run)

    # ---- people ----
    people_rows = []
    for doc in user_ref.collection('people').stream():
        data = doc.to_dict() or {}
        people_rows.append({
            'id': doc.id,
            'uid': supabase_uid,
            'name': data.get('name', ''),
            'created_at': _ts(data.get('created_at')),
            'updated_at': _ts(data.get('updated_at')),
            'speech_samples': json.dumps(data.get('speech_samples', [])),
            'speech_sample_transcripts': json.dumps(data.get('speech_sample_transcripts', [])),
            'speech_samples_version': data.get('speech_samples_version', 1),
            'speaker_embedding': json.dumps(data.get('speaker_embedding')) if data.get('speaker_embedding') else None,
        })
    counts['people'] += _upsert('people', people_rows, dry_run)

    return counts


def _ts(value) -> Optional[str]:
    """Convert Firestore Timestamp / datetime / None to ISO string."""
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if hasattr(value, 'timestamp'):
        from datetime import datetime, timezone
        return datetime.fromtimestamp(value.timestamp(), tz=timezone.utc).isoformat()
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description='Migrate Firestore user data to Supabase Postgres')
    ap.add_argument('--uid', help='Firebase UID to migrate')
    ap.add_argument('--supabase-uid', help='Supabase UUID for this user (auto-generated if omitted)')
    ap.add_argument('--all', dest='all_users', action='store_true', help='Migrate all users (requires mapping file)')
    ap.add_argument('--mapping', help='JSON file mapping firebase_uid → supabase_uuid (used with --all)')
    ap.add_argument('--dry-run', action='store_true', help='Count documents without writing')
    args = ap.parse_args()

    db = _init_firebase()

    if args.all_users:
        if not args.mapping:
            logger.error('--mapping required with --all (JSON file: {"firebase_uid": "supabase_uuid"})')
            sys.exit(1)
        with open(args.mapping) as f:
            mapping = json.load(f)
        total = {'conversations': 0, 'memories': 0, 'action_items': 0, 'people': 0}
        for fuid, suid in mapping.items():
            logger.info('Migrating %s → %s', fuid, suid)
            counts = _migrate_user(db, fuid, suid, args.dry_run)
            for k, v in counts.items():
                total[k] += v
        logger.info('Done. Total: %s', total)

    elif args.uid:
        suid = args.supabase_uid or str(uuid.uuid4())
        logger.info('Migrating Firebase uid=%s → Supabase uid=%s', args.uid, suid)
        counts = _migrate_user(db, args.uid, suid, args.dry_run)
        logger.info('Done. Counts: %s', counts)

    else:
        ap.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
