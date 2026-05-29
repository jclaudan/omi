import os
import logging

logger = logging.getLogger(__name__)

# Legacy namespace constants (Pinecone-era, kept for backward compat with callers)
MEMORIES_NAMESPACE = 'ns2'
SCREEN_ACTIVITY_NAMESPACE = 'ns3'
ACTION_ITEMS_NAMESPACE = 'ns4'
X_POSTS_NAMESPACE = 'ns_x'

# ---------------------------------------------------------------------------
# Backend selection — add a new backend: create database/backends/vector_db_<name>.py
# and export the same public functions, then add an elif branch below.
# ---------------------------------------------------------------------------

if os.getenv('QDRANT_URL'):
    from database.backends.vector_db_qdrant import (
        upsert_vector, upsert_vector2, update_vector_metadata, upsert_vectors,
        query_vectors, query_vectors_by_metadata, delete_vector,
        upsert_memory_vector, upsert_memory_vectors_batch, find_similar_memories,
        check_memory_duplicate, search_memories_by_vector, delete_memory_vector,
        upsert_x_post_vectors_batch, find_similar_x_posts,
        upsert_screen_activity_vectors, search_screen_activity_vectors, delete_screen_activity_vectors,
        upsert_action_item_vector, upsert_action_item_vectors_batch,
        search_action_items_by_vector, find_similar_action_items,
        delete_action_item_vector, delete_action_item_vectors_batch,
    )
    index = None  # kept for callers that check `if index is None`

elif os.getenv('PINECONE_API_KEY'):
    from database.backends.vector_db_pinecone import (
        upsert_vector, upsert_vector2, update_vector_metadata, upsert_vectors,
        query_vectors, query_vectors_by_metadata, delete_vector,
        upsert_memory_vector, upsert_memory_vectors_batch, find_similar_memories,
        check_memory_duplicate, search_memories_by_vector, delete_memory_vector,
        upsert_x_post_vectors_batch, find_similar_x_posts,
        upsert_screen_activity_vectors, search_screen_activity_vectors, delete_screen_activity_vectors,
        upsert_action_item_vector, upsert_action_item_vectors_batch,
        search_action_items_by_vector, find_similar_action_items,
        delete_action_item_vector, delete_action_item_vectors_batch,
        index,
    )

else:
    logger.warning('vector_db: no backend configured (set QDRANT_URL or PINECONE_API_KEY)')
    index = None

    def upsert_vector(*a, **kw): pass
    def upsert_vector2(*a, **kw): pass
    def update_vector_metadata(*a, **kw): pass
    def upsert_vectors(*a, **kw): pass
    def query_vectors(*a, **kw): return []
    def query_vectors_by_metadata(*a, **kw): return []
    def delete_vector(*a, **kw): pass
    def upsert_memory_vector(*a, **kw): return None
    def upsert_memory_vectors_batch(*a, **kw): return 0
    def find_similar_memories(*a, **kw): return []
    def check_memory_duplicate(*a, **kw): return None
    def search_memories_by_vector(*a, **kw): return []
    def delete_memory_vector(*a, **kw): pass
    def upsert_x_post_vectors_batch(*a, **kw): return 0
    def find_similar_x_posts(*a, **kw): return []
    def upsert_screen_activity_vectors(*a, **kw): return 0
    def search_screen_activity_vectors(*a, **kw): return []
    def delete_screen_activity_vectors(*a, **kw): pass
    def upsert_action_item_vector(*a, **kw): return None
    def upsert_action_item_vectors_batch(*a, **kw): return 0
    def search_action_items_by_vector(*a, **kw): return []
    def find_similar_action_items(*a, **kw): return []
    def delete_action_item_vector(*a, **kw): pass
    def delete_action_item_vectors_batch(*a, **kw): pass
