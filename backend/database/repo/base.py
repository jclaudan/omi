"""
Repository protocol (abstract interfaces) for the OSS+ data layer.

Each protocol mirrors the Firestore-based functions in database/*.py so
Supabase Postgres implementations can be swapped in transparently via
the factory module.

Conventions
-----------
- Methods return plain dict / list[dict] (same as the Firestore versions).
- `uid` is always the first argument.
- Soft-delete: `deleted=True` flag — implementations must filter these out
  in list queries unless `include_deleted=True` is passed.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ConversationRepo(Protocol):
    def upsert_conversation(self, uid: str, conversation_data: dict) -> None: ...
    def get_conversation(self, uid: str, conversation_id: str) -> Optional[Dict[str, Any]]: ...
    def get_conversations(
        self,
        uid: str,
        limit: int = 100,
        offset: int = 0,
        include_discarded: bool = False,
    ) -> List[Dict[str, Any]]: ...
    def update_conversation(self, uid: str, conversation_id: str, updates: dict) -> None: ...
    def delete_conversation(self, uid: str, conversation_id: str) -> None: ...
    def conversation_exists(self, uid: str, conversation_id: str) -> bool: ...


@runtime_checkable
class MemoryRepo(Protocol):
    def upsert_memory(self, uid: str, memory_data: dict) -> None: ...
    def get_memory(self, uid: str, memory_id: str) -> Optional[Dict[str, Any]]: ...
    def get_memories(
        self,
        uid: str,
        limit: int = 100,
        offset: int = 0,
        visibility: Optional[str] = None,
    ) -> List[Dict[str, Any]]: ...
    def update_memory(self, uid: str, memory_id: str, updates: dict) -> None: ...
    def delete_memory(self, uid: str, memory_id: str) -> None: ...


@runtime_checkable
class ActionItemRepo(Protocol):
    def create_action_item(self, uid: str, action_item_data: dict) -> str: ...
    def get_action_item(self, uid: str, action_item_id: str) -> Optional[Dict[str, Any]]: ...
    def get_action_items(
        self,
        uid: str,
        completed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]: ...
    def update_action_item(self, uid: str, action_item_id: str, updates: dict) -> None: ...
    def delete_action_item(self, uid: str, action_item_id: str) -> None: ...
