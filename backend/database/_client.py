import hashlib
import json
import os
import uuid

_OMI_DB_BACKEND = os.environ.get('OMI_DB_BACKEND', 'firestore').lower()

if _OMI_DB_BACKEND == 'supabase':
    # Firestore not needed in Supabase mode — provide a clear-error sentinel.
    # Any code that accidentally bypasses the Supabase dispatch and touches `db`
    # will get an immediate, actionable error instead of a silent auth failure.
    class _NoFirestore:
        def __getattr__(self, name: str):
            raise RuntimeError(
                f"Firestore attribute '{name}' accessed in OMI_DB_BACKEND=supabase mode. "
                "The Supabase dispatch did not cover this code path — please report this as a bug."
            )

    db = _NoFirestore()

else:
    from google.cloud import firestore as _firestore

    if os.environ.get('SERVICE_ACCOUNT_JSON'):
        service_account_info = json.loads(os.environ['SERVICE_ACCOUNT_JSON'])
        with open('google-credentials.json', 'w') as f:
            json.dump(service_account_info, f)

    db = _firestore.Client()


def get_users_uid():
    users_ref = db.collection('users')
    return [str(doc.id) for doc in users_ref.stream()]


def document_id_from_seed(seed: str) -> uuid.UUID:
    """Avoid repeating the same data"""
    seed_hash = hashlib.sha256(seed.encode('utf-8')).digest()
    generated_uuid = uuid.UUID(bytes=seed_hash[:16], version=4)
    return str(generated_uuid)
