"""
Enabled apps factory — routes between Redis (Cloud) and Supabase (OSS+).

In Cloud mode: Store/retrieve from Redis sets (users:{uid}:enabled_plugins)
In OSS+ mode: Store/retrieve from Supabase public.user_enabled_apps table
"""

import os
from typing import List

_SUPABASE = os.environ.get('OMI_DB_BACKEND', 'firestore').lower() == 'supabase'


def get_enabled_apps(uid: str) -> List[str]:
    """Get list of enabled app IDs for a user."""
    if _SUPABASE:
        from database.repo.supabase_apps import get_enabled_app_ids
        return get_enabled_app_ids(uid)
    # Cloud mode: Redis
    from database.redis_db import get_enabled_apps as get_enabled_apps_redis
    return get_enabled_apps_redis(uid)


def enable_app(uid: str, app_id: str) -> None:
    """Enable an app for a user."""
    if _SUPABASE:
        from database.repo.supabase_apps import enable_app as enable_app_supabase
        enable_app_supabase(uid, app_id)
    else:
        # Cloud mode: Redis
        from database.redis_db import enable_app as enable_app_redis
        enable_app_redis(uid, app_id)


def disable_app(uid: str, app_id: str) -> None:
    """Disable an app for a user."""
    if _SUPABASE:
        from database.repo.supabase_apps import disable_app as disable_app_supabase
        disable_app_supabase(uid, app_id)
    else:
        # Cloud mode: Redis
        from database.redis_db import disable_app as disable_app_redis
        disable_app_redis(uid, app_id)


def is_app_enabled(uid: str, app_id: str) -> bool:
    """Check if an app is enabled for a user."""
    if _SUPABASE:
        # Supabase: check in enabled list
        return app_id in get_enabled_apps(uid)
    # Cloud mode: Redis
    from database.redis_db import is_app_enabled as is_app_enabled_redis
    return is_app_enabled_redis(uid, app_id)
