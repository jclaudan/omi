"""
Repository factory — returns the right implementation based on OMI_DB_BACKEND.

Usage:
    from database.repo.factory import get_conversation_repo, get_memory_repo, get_action_item_repo

    repo = get_conversation_repo()
    repo.upsert_conversation(uid, data)

OMI_DB_BACKEND values:
    firestore  (default) — delegates to the existing database.conversations / memories / action_items modules
    supabase            — uses Supabase Postgres REST API via database.repo.supabase_*
"""

import os

_BACKEND = os.environ.get('OMI_DB_BACKEND', 'firestore').lower()


class _FirestoreConversationAdapter:
    """Thin adapter so existing Firestore functions satisfy ConversationRepo protocol."""

    def upsert_conversation(self, uid: str, conversation_data: dict) -> None:
        import database.conversations as _c

        _c.upsert_conversation(uid, conversation_data)

    def get_conversation(self, uid: str, conversation_id: str):
        import database.conversations as _c

        return _c.get_conversation(uid, conversation_id)

    def get_conversations(self, uid: str, limit: int = 100, offset: int = 0, include_discarded: bool = False):
        import database.conversations as _c

        return _c.get_conversations(uid, limit=limit, offset=offset, include_discarded=include_discarded)

    def update_conversation(self, uid: str, conversation_id: str, updates: dict) -> None:
        import database.conversations as _c

        _c.update_conversation(uid, conversation_id, updates)

    def delete_conversation(self, uid: str, conversation_id: str) -> None:
        import database.conversations as _c

        _c.delete_conversation(uid, conversation_id)

    def conversation_exists(self, uid: str, conversation_id: str) -> bool:
        import database.conversations as _c

        return _c.get_conversation(uid, conversation_id) is not None


class _FirestoreMemoryAdapter:
    def upsert_memory(self, uid: str, memory_data: dict) -> None:
        import database.memories as _m

        _m.upsert_memory(uid, memory_data)

    def get_memory(self, uid: str, memory_id: str):
        import database.memories as _m

        return _m.get_memory(uid, memory_id)

    def get_memories(self, uid: str, limit: int = 100, offset: int = 0, visibility=None):
        import database.memories as _m

        return _m.get_memories(uid, limit=limit, offset=offset)

    def update_memory(self, uid: str, memory_id: str, updates: dict) -> None:
        import database.memories as _m

        _m.update_memory(uid, memory_id, updates)

    def delete_memory(self, uid: str, memory_id: str) -> None:
        import database.memories as _m

        _m.delete_memory(uid, memory_id)


class _FirestoreActionItemAdapter:
    def create_action_item(self, uid: str, action_item_data: dict) -> str:
        import database.action_items as _a

        return _a.create_action_item(uid, action_item_data)

    def get_action_item(self, uid: str, action_item_id: str):
        import database.action_items as _a

        return _a.get_action_item(uid, action_item_id)

    def get_action_items(self, uid: str, completed=None, limit: int = 100, offset: int = 0):
        import database.action_items as _a

        return _a.get_action_items(uid, completed=completed, limit=limit, offset=offset)

    def update_action_item(self, uid: str, action_item_id: str, updates: dict) -> None:
        import database.action_items as _a

        _a.update_action_item(uid, action_item_id, updates)

    def delete_action_item(self, uid: str, action_item_id: str) -> None:
        import database.action_items as _a

        _a.delete_action_item(uid, action_item_id)


def get_conversation_repo():
    if _BACKEND == 'supabase':
        from database.repo.supabase_conversations import SupabaseConversationRepo

        return SupabaseConversationRepo()
    return _FirestoreConversationAdapter()


def get_memory_repo():
    if _BACKEND == 'supabase':
        from database.repo.supabase_memories import SupabaseMemoryRepo

        return SupabaseMemoryRepo()
    return _FirestoreMemoryAdapter()


def get_action_item_repo():
    if _BACKEND == 'supabase':
        from database.repo.supabase_action_items import SupabaseActionItemRepo

        return SupabaseActionItemRepo()
    return _FirestoreActionItemAdapter()
