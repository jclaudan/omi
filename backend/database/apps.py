import os
from datetime import datetime, timezone
from typing import List

from google.cloud.firestore_v1.base_query import BaseCompositeFilter, FieldFilter
from google.cloud.firestore import ArrayUnion, ArrayRemove

from ulid import ULID

from models.app import UsageHistoryType
from ._client import db
import logging

logger = logging.getLogger(__name__)

_SUPABASE = os.environ.get('OMI_DB_BACKEND', 'firestore').lower() == 'supabase'

# *****************************
# ********** CRUD *************
# *****************************

apps_collection = 'plugins_data'
app_analytics_collection = 'plugins'
testers_collection = 'testers'


def get_app_by_id_db(app_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_app_by_id
        return get_app_by_id(app_id)
    app_ref = db.collection(apps_collection).document(app_id)
    doc = app_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_audio_apps_count(app_ids: List[str]):
    if not app_ids or len(app_ids) == 0:
        return 0
    if _SUPABASE:
        from database.repo.supabase_apps import get_audio_apps_count
        return get_audio_apps_count(app_ids)
    filters = [FieldFilter('id', 'in', app_ids), FieldFilter('external_integration.triggers_on', '==', 'audio_bytes')]
    apps_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).count().get()
    return apps_ref[0][0].value


def get_private_apps_db(uid: str) -> List:
    if _SUPABASE:
        from database.repo.supabase_apps import get_private_apps
        return get_private_apps(uid)
    filters = [FieldFilter('uid', '==', uid), FieldFilter('private', '==', True)]
    private_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    data = [doc.to_dict() for doc in private_apps]
    return data


# This returns public unapproved apps of all users
def get_unapproved_public_apps_db() -> List:
    if _SUPABASE:
        # In OSS+ mode, all apps are approved by default
        return []
    filters = [FieldFilter('approved', '==', False), FieldFilter('private', '==', False)]
    public_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    return [doc.to_dict() for doc in public_apps]


def get_public_approved_apps_db() -> List:
    if _SUPABASE:
        from database.repo.supabase_apps import get_public_approved_apps
        return get_public_approved_apps()
    filters = [FieldFilter('approved', '==', True), FieldFilter('private', '==', False)]
    public_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    return [doc.to_dict() for doc in public_apps]


def get_popular_apps_db() -> List:
    if _SUPABASE:
        from database.repo.supabase_apps import search_apps
        # In OSS+, return popular public apps
        return search_apps(uid=None, my_apps=False, enabled_app_ids=None)
    filters = [FieldFilter('approved', '==', True), FieldFilter('is_popular', '==', True)]
    popular_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    return [doc.to_dict() for doc in popular_apps]


def set_app_popular_db(app_id: str, popular: bool):
    if _SUPABASE:
        from database.repo.supabase_apps import update_app
        update_app({'id': app_id, 'is_popular': popular})
        return
    app_ref = db.collection(apps_collection).document(app_id)
    app_ref.update({'is_popular': popular})


def search_apps_db(
    uid: str,
    category: str | None = None,
    capability: str | None = None,
    my_apps: bool = False,
    installed_apps: bool = False,
    enabled_app_ids: List[str] | None = None,
) -> List:
    """
    Optimized search function that applies filters at database level.
    Uses smart filter ordering to minimize data fetched from Firestore.

    Note: Rating filter is NOT applied here as rating_avg is calculated from Redis,
    not stored in Firestore. Apply rating filter after fetching from DB.

    Args:
        uid: User ID for private apps and filtering
        category: Filter by category ID
        capability: Filter by capability ID
        my_apps: Only return user's own apps
        installed_apps: Only return user's enabled apps
        enabled_app_ids: Pre-fetched list of enabled app IDs (for installed_apps filter)

    Returns:
        List of app dictionaries matching the filters
    """
    if _SUPABASE:
        from database.repo.supabase_apps import search_apps
        apps = search_apps(
            uid=uid,
            category=category,
            capability=capability,
            my_apps=my_apps,
            enabled_app_ids=enabled_app_ids if installed_apps else None
        )
        # For installed_apps with > 30 enabled apps, add user's own apps
        if installed_apps and enabled_app_ids and len(enabled_app_ids) > 30:
            enabled_set = set(enabled_app_ids)
            apps = [app for app in apps if app.get('id') in enabled_set]
            # Also fetch user's own apps
            user_apps = search_apps(uid=uid, category=category, capability=capability, my_apps=True)
            existing_ids = {app.get('id') for app in apps}
            for user_app in user_apps:
                if user_app.get('id') in enabled_set and user_app.get('id') not in existing_ids:
                    apps.append(user_app)
        return apps

    filters = []

    # 1. Apply most restrictive filter first
    if my_apps:
        filters.append(FieldFilter('uid', '==', uid))

    elif installed_apps:
        if not enabled_app_ids or len(enabled_app_ids) == 0:
            # User has no enabled apps
            return []

        if len(enabled_app_ids) > 30:
            # Firestore 'in' limited to 30 items
            # Query public approved apps first, then add user's own apps
            filters.append(FieldFilter('approved', '==', True))
            filters.append(FieldFilter('private', '==', False))
        else:
            # Query by specific IDs
            filters.append(FieldFilter('id', 'in', enabled_app_ids))

    else:
        # Default: Public approved apps
        filters.append(FieldFilter('approved', '==', True))
        filters.append(FieldFilter('private', '==', False))

    # 2. Add category filter
    if category and not my_apps:  # Don't add if already filtering by my_apps
        filters.append(FieldFilter('category', '==', category))

    # 3. Add capability filter
    if capability and not my_apps:
        filters.append(FieldFilter('capabilities', 'array_contains', capability))

    # Execute query with all filters
    if filters:
        query = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters))
        apps = [doc.to_dict() for doc in query.stream()]
    else:
        apps = []

    # For installed_apps with > 30 enabled apps, we need to also fetch user's own apps
    # because the main query only returns approved+public apps
    if installed_apps and enabled_app_ids and len(enabled_app_ids) > 30:
        enabled_set = set(enabled_app_ids)
        # Filter to only enabled apps from the public approved set
        apps = [app for app in apps if app.get('id') in enabled_set]

        # Also fetch user's own enabled apps (which may be private or unapproved)
        user_apps_filter = FieldFilter('uid', '==', uid)
        user_apps_query = db.collection(apps_collection).where(filter=user_apps_filter)
        user_apps = [doc.to_dict() for doc in user_apps_query.stream()]

        # Add user's own enabled apps that aren't already in the list
        existing_ids = {app.get('id') for app in apps}
        for user_app in user_apps:
            if user_app.get('id') in enabled_set and user_app.get('id') not in existing_ids:
                apps.append(user_app)

    # Post-filter for category if my_apps is enabled
    if my_apps and category:
        apps = [app for app in apps if app.get('category') == category]

    # Post-filter for capability if my_apps is enabled
    if my_apps and capability:
        apps = [app for app in apps if capability in app.get('capabilities', [])]

    return apps


# This returns public unapproved apps for a user
def get_public_unapproved_apps_db(uid: str) -> List:
    if _SUPABASE:
        # In OSS+ mode, all apps are approved by default
        return []
    filters = [FieldFilter('approved', '==', False), FieldFilter('uid', '==', uid), FieldFilter('private', '==', False)]
    public_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    return [doc.to_dict() for doc in public_apps]


def get_apps_for_tester_db(uid: str) -> List:
    if _SUPABASE:
        from database.repo.supabase_apps import get_apps_for_tester
        return get_apps_for_tester(uid)
    tester_ref = db.collection(testers_collection).document(uid)
    doc = tester_ref.get()
    if doc.exists:
        apps = doc.to_dict().get('apps', [])
        if not apps:
            return []
        filters = [FieldFilter('approved', '==', False), FieldFilter('id', 'in', apps)]
        public_apps = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
        return [doc.to_dict() for doc in public_apps]
    return []


def add_app_to_db(app_data: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import add_app
        add_app(app_data)
        return
    app_ref = db.collection(apps_collection)
    app_ref.add(app_data, app_data['id'])


def upsert_app_to_db(app_data: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import upsert_app
        upsert_app(app_data)
        return
    app_ref = db.collection(apps_collection).document(app_data['id'])
    app_ref.set(app_data)


def update_app_in_db(app_data: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import update_app
        update_app(app_data)
        return
    app_ref = db.collection(apps_collection).document(app_data['id'])
    app_ref.update(app_data)


def delete_app_from_db(app_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import delete_app
        delete_app(app_id)
        return
    app_ref = db.collection(apps_collection).document(app_id)
    app_ref.delete()


def update_app_visibility_in_db(app_id: str, private: bool):
    if _SUPABASE:
        from database.repo.supabase_apps import update_app_visibility
        update_app_visibility(app_id, private)
        return
    app_ref = db.collection(apps_collection).document(app_id)
    if 'private' in app_id and not private:
        app = app_ref.get().to_dict()
        app_ref.delete()
        new_app_id = app_id.split('-private')[0] + '-' + str(ULID())
        app['id'] = new_app_id
        app['private'] = private
        app_ref = db.collection(apps_collection).document(new_app_id)
        app_ref.set(app)
    else:
        app_ref.update({'private': private})


def change_app_approval_status(app_id: str, approved: bool):
    if _SUPABASE:
        from database.repo.supabase_apps import change_app_approval
        change_app_approval(app_id, approved)
        return
    app_ref = db.collection(apps_collection).document(app_id)
    app_ref.update({'approved': approved, 'status': 'approved' if approved else 'rejected'})


def get_app_usage_history_db(app_id: str):
    usage = db.collection(app_analytics_collection).document(app_id).collection('usage_history').stream()
    return [doc.to_dict() for doc in usage]


def get_app_memory_created_integration_usage_count_db(app_id: str):
    usage = (
        db.collection(app_analytics_collection)
        .document(app_id)
        .collection('usage_history')
        .where(filter=FieldFilter('type', '==', UsageHistoryType.memory_created_external_integration))
        .count()
        .get()
    )
    return usage[0][0].value


def get_app_memory_prompt_usage_count_db(app_id: str):
    usage = (
        db.collection(app_analytics_collection)
        .document(app_id)
        .collection('usage_history')
        .where(filter=FieldFilter('type', '==', UsageHistoryType.memory_created_prompt))
        .count()
        .get()
    )
    return usage[0][0].value


def get_app_chat_message_sent_usage_count_db(app_id: str):
    usage = (
        db.collection(app_analytics_collection)
        .document(app_id)
        .collection('usage_history')
        .where(filter=FieldFilter('type', '==', UsageHistoryType.chat_message_sent))
        .count()
        .get()
    )
    return usage[0][0].value


def get_app_usage_count_db(app_id: str):
    usage = db.collection(app_analytics_collection).document(app_id).collection('usage_history').count().get()
    return usage[0][0].value


# ********************************
# *********** REVIEWS ************
# ********************************


def set_app_review_in_db(app_id: str, uid: str, review: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import set_app_review
        set_app_review(app_id, uid, review)
        return
    app_ref = db.collection(apps_collection).document(app_id).collection('reviews').document(uid)
    app_ref.set(review)


# ********************************
# ************ TESTER ************
# ********************************


def add_tester_db(data: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import add_tester
        add_tester(data)
        return
    app_ref = db.collection(testers_collection).document(data['uid'])
    app_ref.set(data)


def add_app_access_for_tester_db(app_id: str, uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import add_app_access_for_tester
        add_app_access_for_tester(app_id, uid)
        return
    app_ref = db.collection(testers_collection).document(uid)
    app_ref.update({'apps': ArrayUnion([app_id])})


def remove_app_access_for_tester_db(app_id: str, uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import remove_app_access_for_tester
        remove_app_access_for_tester(app_id, uid)
        return
    app_ref = db.collection(testers_collection).document(uid)
    app_ref.update({'apps': ArrayRemove([app_id])})


def remove_tester_db(uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import remove_tester
        remove_tester(uid)
        return
    app_ref = db.collection(testers_collection).document(uid)
    app_ref.delete()


def can_tester_access_app_db(app_id: str, uid: str) -> bool:
    if _SUPABASE:
        from database.repo.supabase_apps import can_tester_access_app
        return can_tester_access_app(app_id, uid)
    app_ref = db.collection(testers_collection).document(uid)
    doc = app_ref.get()
    if doc.exists:
        return app_id in doc.to_dict().get('apps', [])
    return False


def is_tester_db(uid: str) -> bool:
    if _SUPABASE:
        from database.repo.supabase_apps import is_tester
        return is_tester(uid)
    app_ref = db.collection(testers_collection).document(uid)
    return app_ref.get().exists


# ********************************
# *********** APPS USAGE *********
# ********************************


def record_app_usage(
    uid: str,
    app_id: str,
    usage_type: UsageHistoryType,
    conversation_id: str = None,
    message_id: str = None,
    timestamp: datetime = None,
):
    if _SUPABASE:
        return  # App usage tracking not available in OSS+ mode
    if not conversation_id and not message_id:
        raise ValueError('memory_id or message_id must be provided')

    data = {
        'uid': uid,
        'memory_id': conversation_id,
        'message_id': message_id,
        'timestamp': datetime.now(timezone.utc) if timestamp is None else timestamp,
        'type': usage_type,
    }

    db.collection(app_analytics_collection).document(app_id).collection('usage_history').document(
        conversation_id or message_id
    ).set(data)
    return data


# ********************************
# *********** PERSONAS ***********
# ********************************


def delete_persona_db(persona_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import delete_persona
        delete_persona(persona_id)
        return
    persona_ref = db.collection(apps_collection).document(persona_id)
    persona_ref.delete()


def get_personas_by_username_db(persona_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_personas_by_username
        return get_personas_by_username(persona_id)
    persona_ref = db.collection(apps_collection).where('username', '==', persona_id)
    docs = persona_ref.get()
    if not docs:
        return None
    return [{**doc.to_dict(), 'doc_id': doc.id} for doc in docs]


def get_persona_by_username_db(username: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_persona_by_username
        return get_persona_by_username(username)
    filters = [FieldFilter('username', '==', username), FieldFilter('capabilities', 'array_contains', 'persona')]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).limit(1)
    docs = persona_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return doc.to_dict()


def get_persona_by_id_db(persona_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_persona_by_id
        return get_persona_by_id(persona_id)
    persona_ref = db.collection(apps_collection).document(persona_id)
    doc = persona_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_persona_by_uid_db(uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_persona_by_uid
        return get_persona_by_uid(uid)
    filters = [FieldFilter('uid', '==', uid), FieldFilter('capabilities', 'array_contains', 'persona')]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).limit(1)
    docs = persona_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return doc.to_dict()


def get_user_persona_by_uid(uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_user_persona_by_uid
        return get_user_persona_by_uid(uid)
    filters = [
        FieldFilter('capabilities', 'array_contains', 'persona'),
        FieldFilter('category', '==', 'personality-emulation'),
        FieldFilter('uid', '==', uid),
    ]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).limit(1)
    docs = persona_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return {'id': doc.id, **doc.to_dict()}


def get_persona_by_twitter_handle_db(handle: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_persona_by_twitter_handle
        result = get_persona_by_twitter_handle(handle)
        return {'id': result.get('id'), **result} if result else None
    filters = [FieldFilter('category', '==', 'personality-emulation'), FieldFilter('twitter.username', '==', handle)]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).limit(1)
    docs = persona_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return {'id': doc.id, **doc.to_dict()}


def get_persona_by_username_twitter_handle_db(username: str, handle: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_persona_by_username_twitter_handle
        result = get_persona_by_username_twitter_handle(username, handle)
        return {'id': result.get('id'), **result} if result else None
    filters = [
        FieldFilter('username', '==', username),
        FieldFilter('category', '==', 'personality-emulation'),
        FieldFilter('twitter.username', '==', handle),
    ]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).limit(1)
    docs = persona_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return {'id': doc.id, **doc.to_dict()}


def get_omi_personas_by_uid_db(uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_omi_personas_by_uid
        return get_omi_personas_by_uid(uid)
    filters = [FieldFilter('uid', '==', uid), FieldFilter('capabilities', 'array_contains', 'persona')]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters))
    docs = persona_ref.get()
    if not docs:
        return []
    docs = [doc.to_dict() for doc in docs if 'omi' in doc.to_dict().get('connected_accounts', [])]
    return docs


def get_omi_persona_apps_by_uid_db(uid: str):
    if _SUPABASE:
        from database.repo.supabase_apps import get_omi_persona_apps_by_uid
        return get_omi_persona_apps_by_uid(uid)
    filters = [FieldFilter('uid', '==', uid), FieldFilter('category', '==', 'personality-emulation')]
    persona_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters))
    docs = persona_ref.get()
    if not docs:
        return []
    docs = [doc.to_dict() for doc in docs]
    return docs


def update_persona_in_db(persona_data: dict):
    if _SUPABASE:
        from database.repo.supabase_apps import update_persona
        update_persona(persona_data)
        return
    persona_ref = db.collection(apps_collection).document(persona_data['id'])
    persona_ref.update(persona_data)


def migrate_app_owner_id_db(new_id: str, old_id: str):
    if _SUPABASE:
        from database.repo.supabase_apps import migrate_app_owner_id
        migrate_app_owner_id(new_id, old_id)
        return
    filters = [FieldFilter('uid', '==', old_id)]
    apps_ref = db.collection(apps_collection).where(filter=BaseCompositeFilter('AND', filters)).stream()
    for app in apps_ref:
        app_ref = db.collection(apps_collection).document(app.id)
        app_ref.update({'uid': new_id})


def create_api_key_db(app_id: str, api_key_data: dict):
    """Create a new API key for an app in the database"""
    if _SUPABASE:
        from database.repo.supabase_apps import create_api_key
        return create_api_key(app_id, api_key_data)
    api_key_ref = db.collection(apps_collection).document(app_id).collection('api_keys').document(api_key_data['id'])
    api_key_ref.set(api_key_data)
    return api_key_data


def get_api_key_by_hash_db(app_id: str, hashed_key: str):
    """Get an API key by its hash value"""
    if _SUPABASE:
        from database.repo.supabase_apps import get_api_key_by_hash
        return get_api_key_by_hash(app_id, hashed_key)
    filters = [FieldFilter('hashed', '==', hashed_key)]
    api_keys_ref = (
        db.collection(apps_collection)
        .document(app_id)
        .collection('api_keys')
        .where(filter=BaseCompositeFilter('AND', filters))
        .limit(1)
    )
    docs = api_keys_ref.get()
    if not docs:
        return None
    doc = next(iter(docs), None)
    if not doc:
        return None
    return doc.to_dict()


def list_api_keys_db(app_id: str):
    """List all API keys for an app (excluding the hashed values)"""
    if _SUPABASE:
        from database.repo.supabase_apps import list_api_keys
        return list_api_keys(app_id)
    api_keys_ref = (
        db.collection(apps_collection)
        .document(app_id)
        .collection('api_keys')
        .order_by('created_at', direction='DESCENDING')
        .stream()
    )
    return [{k: v for k, v in doc.to_dict().items() if k != 'hashed'} for doc in api_keys_ref]


def delete_api_key_db(app_id: str, key_id: str):
    """Delete an API key"""
    if _SUPABASE:
        from database.repo.supabase_apps import delete_api_key
        return delete_api_key(app_id, key_id)
    api_key_ref = db.collection(apps_collection).document(app_id).collection('api_keys').document(key_id)
    api_key_ref.delete()
    return True
