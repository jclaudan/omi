"""Tests for database.repo.factory — verifies the factory returns the right
implementation based on OMI_DB_BACKEND, without hitting any real DB."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Stub heavy modules before importing anything from backend
os.environ.setdefault('ENCRYPTION_SECRET', 'test-secret-32byteslong!!!!!!!!')

# Patch firebase_admin so it doesn't need real credentials
firebase_stub = MagicMock()
sys.modules['firebase_admin'] = firebase_stub
sys.modules['firebase_admin.credentials'] = firebase_stub
sys.modules['firebase_admin.auth'] = firebase_stub
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.firestore_v1'] = MagicMock()


def _import_factory(backend: str):
    """Import factory with OMI_DB_BACKEND forced to `backend`."""
    import importlib

    with patch.dict(os.environ, {'OMI_DB_BACKEND': backend}):
        # factory reads the env var at module level; reload to pick up the override
        import database.repo.factory as mod

        importlib.reload(mod)
        return mod


class TestFactoryFirestore:
    def test_get_conversation_repo_returns_firestore_adapter(self):
        mod = _import_factory('firestore')
        repo = mod.get_conversation_repo()
        assert hasattr(repo, 'upsert_conversation')
        assert hasattr(repo, 'get_conversation')
        assert hasattr(repo, 'get_conversations')

    def test_get_memory_repo_returns_firestore_adapter(self):
        mod = _import_factory('firestore')
        repo = mod.get_memory_repo()
        assert hasattr(repo, 'upsert_memory')
        assert hasattr(repo, 'get_memories')

    def test_get_action_item_repo_returns_firestore_adapter(self):
        mod = _import_factory('firestore')
        repo = mod.get_action_item_repo()
        assert hasattr(repo, 'create_action_item')
        assert hasattr(repo, 'get_action_items')


class TestFactorySupabase:
    def test_get_conversation_repo_returns_supabase_impl(self):
        mod = _import_factory('supabase')
        repo = mod.get_conversation_repo()
        from database.repo.supabase_conversations import SupabaseConversationRepo

        assert isinstance(repo, SupabaseConversationRepo)

    def test_get_memory_repo_returns_supabase_impl(self):
        mod = _import_factory('supabase')
        repo = mod.get_memory_repo()
        from database.repo.supabase_memories import SupabaseMemoryRepo

        assert isinstance(repo, SupabaseMemoryRepo)

    def test_get_action_item_repo_returns_supabase_impl(self):
        mod = _import_factory('supabase')
        repo = mod.get_action_item_repo()
        from database.repo.supabase_action_items import SupabaseActionItemRepo

        assert isinstance(repo, SupabaseActionItemRepo)


class TestSupabaseRepoUnconfigured:
    """When SUPABASE_URL/KEY are missing, Supabase repos should fail-open."""

    def test_get_conversations_returns_empty_when_unconfigured(self):
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_SERVICE_ROLE_KEY': ''}):
            import importlib
            import utils.oss_supabase_client as cli

            importlib.reload(cli)
            from database.repo.supabase_conversations import SupabaseConversationRepo

            repo = SupabaseConversationRepo()
            result = repo.get_conversations('uid-123')
            assert result == []

    def test_get_memories_returns_empty_when_unconfigured(self):
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_SERVICE_ROLE_KEY': ''}):
            import importlib
            import utils.oss_supabase_client as cli

            importlib.reload(cli)
            from database.repo.supabase_memories import SupabaseMemoryRepo

            repo = SupabaseMemoryRepo()
            result = repo.get_memories('uid-123')
            assert result == []
