import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List

from utils.llm.clients import embeddings
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend selection
#
# Priority: Qdrant (self-hosted) > Pinecone (cloud)
# Set QDRANT_URL to use the open-source backend.
# ---------------------------------------------------------------------------

_QDRANT_URL = os.getenv('QDRANT_URL')
_QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

# Embedding dimension for text-embedding-3-large (OpenAI default)
# Also matches Gemini embedding-001 (3072-dim used in ns3 / screen activity)
_EMBEDDING_DIM = 3072

# Qdrant collection names (one per Pinecone namespace)
_COL_CONVERSATIONS = 'omi_conversations'       # ns1
_COL_MEMORIES = 'omi_memories'                 # ns2
_COL_SCREEN_ACTIVITY = 'omi_screen_activity'   # ns3
_COL_ACTION_ITEMS = 'omi_action_items'         # ns4
_COL_X_POSTS = 'omi_x_posts'                  # ns_x

# Legacy namespace constants kept for callers that reference them
MEMORIES_NAMESPACE = 'ns2'
SCREEN_ACTIVITY_NAMESPACE = 'ns3'
ACTION_ITEMS_NAMESPACE = 'ns4'
X_POSTS_NAMESPACE = 'ns_x'


def _str_to_uuid(s: str) -> str:
    """Deterministic UUID from any string — Qdrant requires UUID or uint64 IDs."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


if _QDRANT_URL:
    # -----------------------------------------------------------------------
    # Qdrant backend
    # -----------------------------------------------------------------------
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchAny,
        MatchValue,
        PointStruct,
        Range,
        VectorParams,
    )

    _qdrant = QdrantClient(url=_QDRANT_URL, api_key=_QDRANT_API_KEY or None, timeout=30)

    def _ensure_collection(name: str) -> None:
        """Create collection if it does not exist yet."""
        existing = {c.name for c in _qdrant.get_collections().collections}
        if name not in existing:
            _qdrant.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=_EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info(f'qdrant: created collection {name}')

    for _col in [_COL_CONVERSATIONS, _COL_MEMORIES, _COL_SCREEN_ACTIVITY, _COL_ACTION_ITEMS, _COL_X_POSTS]:
        try:
            _ensure_collection(_col)
        except Exception as _e:
            logger.warning(f'qdrant: could not ensure collection {_col}: {_e}')

    index = None  # kept for callers that check `if index is None`
    logger.info(f'vector_db: using Qdrant at {_QDRANT_URL}')

elif os.getenv('PINECONE_API_KEY'):
    from pinecone import Pinecone

    _pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY', ''))
    index = _pc.Index(os.getenv('PINECONE_INDEX_NAME', ''))
    _qdrant = None
    logger.info('vector_db: using Pinecone')

else:
    index = None
    _qdrant = None
    logger.warning('vector_db: no vector DB configured (QDRANT_URL or PINECONE_API_KEY required)')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_qdrant() -> bool:
    return _qdrant is not None


def _qdrant_upsert(collection: str, point_id: str, vector: List[float], payload: dict) -> None:
    _qdrant.upsert(
        collection_name=collection,
        points=[PointStruct(id=_str_to_uuid(point_id), vector=vector, payload=payload)],
    )


def _qdrant_search(
    collection: str,
    vector: List[float],
    must_filters: list,
    limit: int,
    with_payload: bool = True,
) -> list:
    f = Filter(must=must_filters) if must_filters else None
    return _qdrant.search(
        collection_name=collection,
        query_vector=vector,
        query_filter=f,
        limit=limit,
        with_payload=with_payload,
    )


def _qdrant_delete(collection: str, point_ids: List[str]) -> None:
    from qdrant_client.models import PointIdsList

    _qdrant.delete(
        collection_name=collection,
        points_selector=PointIdsList(points=[_str_to_uuid(pid) for pid in point_ids]),
    )


# ===========================================================================
# Conversation vectors  (ns1 / omi_conversations)
# ===========================================================================

def _get_data(uid: str, conversation_id: str, vector: List[float]):
    return {
        'id': f'{uid}-{conversation_id}',
        'values': vector,
        'metadata': {
            'uid': uid,
            'memory_id': conversation_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        },
    }


def upsert_vector(uid: str, conversation_id: str, vector: List[float]):
    if _is_qdrant():
        payload = {
            'uid': uid,
            'memory_id': conversation_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        }
        _qdrant_upsert(_COL_CONVERSATIONS, f'{uid}-{conversation_id}', vector, payload)
        logger.info(f'qdrant upsert_vector uid={uid} conv={conversation_id}')
        return
    if index is None:
        return
    res = index.upsert(vectors=[_get_data(uid, conversation_id, vector)], namespace='ns1')
    logger.info(f'upsert_vector {res}')


def upsert_vector2(uid: str, conversation_id: str, vector: List[float], metadata: dict):
    if _is_qdrant():
        payload = {
            'uid': uid,
            'memory_id': conversation_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        }
        payload.update(metadata)
        _qdrant_upsert(_COL_CONVERSATIONS, f'{uid}-{conversation_id}', vector, payload)
        return
    if index is None:
        return
    data = _get_data(uid, conversation_id, vector)
    data['metadata'].update(metadata)
    res = index.upsert(vectors=[data], namespace='ns1')
    logger.info(f'upsert_vector {res}')


def update_vector_metadata(uid: str, conversation_id: str, metadata: dict):
    if _is_qdrant():
        payload = dict(metadata)
        payload['uid'] = uid
        payload['memory_id'] = conversation_id
        _qdrant.set_payload(
            collection_name=_COL_CONVERSATIONS,
            payload=payload,
            points=[_str_to_uuid(f'{uid}-{conversation_id}')],
        )
        return
    if index is None:
        return
    metadata['uid'] = uid
    metadata['memory_id'] = conversation_id
    return index.update(f'{uid}-{conversation_id}', set_metadata=metadata, namespace='ns1')


def upsert_vectors(uid: str, vectors: List[List[float]], conversation_ids: List[str]):
    if _is_qdrant():
        now_ts = int(datetime.now(timezone.utc).timestamp())
        points = [
            PointStruct(
                id=_str_to_uuid(f'{uid}-{cid}'),
                vector=vec,
                payload={'uid': uid, 'memory_id': cid, 'created_at': now_ts},
            )
            for cid, vec in zip(conversation_ids, vectors)
        ]
        _qdrant.upsert(collection_name=_COL_CONVERSATIONS, points=points)
        return
    if index is None:
        return
    data = [_get_data(uid, cid, vector) for cid, vector in zip(conversation_ids, vectors)]
    res = index.upsert(vectors=data, namespace='ns1')
    logger.info(f'upsert_vectors {res}')


def query_vectors(query: str, uid: str, starts_at: int = None, ends_at: int = None, k: int = 5) -> List[str]:
    if _is_qdrant():
        xq = embeddings.embed_query(query)
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        if starts_at is not None:
            must.append(FieldCondition(key='created_at', range=Range(gte=starts_at, lte=ends_at)))
        hits = _qdrant_search(_COL_CONVERSATIONS, xq, must, limit=k, with_payload=True)
        return [h.payload.get('memory_id') for h in hits if h.payload.get('memory_id')]

    if index is None:
        return []
    filter_data = {'uid': uid}
    if starts_at is not None:
        filter_data['created_at'] = {'$gte': starts_at, '$lte': ends_at}
    xq = embeddings.embed_query(query)
    xc = index.query(vector=xq, top_k=k, include_metadata=False, filter=filter_data, namespace='ns1')
    return [item['id'].replace(f'{uid}-', '') for item in xc['matches']]


def query_vectors_by_metadata(
    uid: str,
    vector: List[float],
    dates_filter: List[datetime],
    people: List[str],
    topics: List[str],
    entities: List[str],
    dates: List[str],
    limit: int = 5,
) -> List[str]:
    if _is_qdrant():
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        should = []
        if people:
            should.append(FieldCondition(key='people', match=MatchAny(any=people)))
        if topics:
            should.append(FieldCondition(key='topics', match=MatchAny(any=topics)))
        if entities:
            should.append(FieldCondition(key='entities', match=MatchAny(any=entities)))
        if dates_filter and len(dates_filter) == 2 and dates_filter[0] and dates_filter[1]:
            must.append(
                FieldCondition(
                    key='created_at',
                    range=Range(
                        gte=int(dates_filter[0].timestamp()),
                        lte=int(dates_filter[1].timestamp()),
                    ),
                )
            )
        f = Filter(must=must, should=should if should else None)
        hits = _qdrant.search(
            collection_name=_COL_CONVERSATIONS,
            query_vector=vector,
            query_filter=f,
            limit=1000,
            with_payload=True,
        )
        if not hits:
            # Retry without should filters
            hits = _qdrant.search(
                collection_name=_COL_CONVERSATIONS,
                query_vector=vector,
                query_filter=Filter(must=must),
                limit=20,
                with_payload=True,
            )

        conversation_id_to_matches: dict = defaultdict(int)
        conversation_ids = []
        for h in hits:
            cid = h.payload.get('memory_id')
            if not cid:
                continue
            conversation_ids.append(cid)
            meta = h.payload
            for topic in topics:
                if topic in meta.get('topics', []):
                    conversation_id_to_matches[cid] += 1
            for entity in entities:
                if entity in meta.get('entities', []):
                    conversation_id_to_matches[cid] += 1
            for person in people:
                if person in meta.get('people_mentioned', []):
                    conversation_id_to_matches[cid] += 1

        conversation_ids.sort(key=lambda x: conversation_id_to_matches[x], reverse=True)
        return conversation_ids[:limit] if len(conversation_ids) > limit else conversation_ids

    if index is None:
        return []
    filter_data = {
        '$and': [
            {'uid': {'$eq': uid}},
        ]
    }
    if people or topics or entities or dates:
        filter_data['$and'].append(
            {
                '$or': [
                    {'people': {'$in': people}},
                    {'topics': {'$in': topics}},
                    {'entities': {'$in': entities}},
                ]
            }
        )
    if dates_filter and len(dates_filter) == 2 and dates_filter[0] and dates_filter[1]:
        logger.info(f'dates_filter {dates_filter}')
        filter_data['$and'].append(
            {'created_at': {'$gte': int(dates_filter[0].timestamp()), '$lte': int(dates_filter[1].timestamp())}}
        )

    xc = index.query(
        vector=vector, filter=filter_data, namespace='ns1', include_values=False, include_metadata=True, top_k=1000
    )
    if not xc['matches']:
        if len(filter_data['$and']) == 3:
            filter_data['$and'].pop(1)
            logger.warning(f'query_vectors_by_metadata retrying without structured filters: {json.dumps(filter_data)}')
            xc = index.query(
                vector=vector,
                filter=filter_data,
                namespace='ns1',
                include_values=False,
                include_metadata=True,
                top_k=20,
            )
        else:
            return []

    conversation_id_to_matches = defaultdict(int)
    for item in xc['matches']:
        metadata = item['metadata']
        conversation_id = metadata['memory_id']
        for topic in topics:
            if topic in metadata.get('topics', []):
                conversation_id_to_matches[conversation_id] += 1
        for entity in entities:
            if entity in metadata.get('entities', []):
                conversation_id_to_matches[conversation_id] += 1
        for person in people:
            if person in metadata.get('people_mentioned', []):
                conversation_id_to_matches[conversation_id] += 1

    conversations_id = [item['id'].replace(f'{uid}-', '') for item in xc['matches']]
    conversations_id.sort(key=lambda x: conversation_id_to_matches[x], reverse=True)
    return conversations_id[:limit] if len(conversations_id) > limit else conversations_id


def delete_vector(uid: str, conversation_id: str):
    """Delete a conversation vector."""
    if _is_qdrant():
        _qdrant_delete(_COL_CONVERSATIONS, [f'{uid}-{conversation_id}'])
        logger.info(f'qdrant delete_vector uid={uid} conv={conversation_id}')
        return
    if index is None:
        return
    vector_id = f'{uid}-{conversation_id}'
    result = index.delete(ids=[vector_id], namespace='ns1')
    logger.info(f'delete_vector {vector_id} {result}')


# ===========================================================================
# Memory vectors  (ns2 / omi_memories)
# ===========================================================================

def upsert_memory_vector(uid: str, memory_id: str, content: str, category: str):
    """Upsert a memory embedding."""
    if _is_qdrant():
        vector = embeddings.embed_query(content)
        payload = {
            'uid': uid,
            'memory_id': memory_id,
            'category': category,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        }
        _qdrant_upsert(_COL_MEMORIES, f'{uid}-{memory_id}', vector, payload)
        logger.info(f'qdrant upsert_memory_vector uid={uid} memory={memory_id}')
        return vector

    if index is None:
        logger.warning('Pinecone index not initialized, skipping memory vector upsert')
        return None

    vector = embeddings.embed_query(content)
    data = {
        'id': f'{uid}-{memory_id}',
        'values': vector,
        'metadata': {
            'uid': uid,
            'memory_id': memory_id,
            'category': category,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        },
    }
    res = index.upsert(vectors=[data], namespace=MEMORIES_NAMESPACE)
    logger.info(f'upsert_memory_vector {memory_id} {res}')
    return vector


def upsert_memory_vectors_batch(uid: str, items: List[dict]) -> int:
    """Batch upsert memory embeddings."""
    if _is_qdrant():
        if not items:
            return 0
        contents = [item['content'] for item in items]
        vectors = embeddings.embed_documents(contents)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        points = [
            PointStruct(
                id=_str_to_uuid(f'{uid}-{item["memory_id"]}'),
                vector=vectors[i],
                payload={
                    'uid': uid,
                    'memory_id': item['memory_id'],
                    'category': item['category'],
                    'created_at': now_ts,
                },
            )
            for i, item in enumerate(items)
        ]
        _qdrant.upsert(collection_name=_COL_MEMORIES, points=points)
        logger.info(f'qdrant upsert_memory_vectors_batch uid={uid} count={len(points)}')
        return len(points)

    if index is None:
        logger.warning('Pinecone index not initialized, skipping memory vector batch upsert')
        return 0
    if not items:
        return 0
    contents = [item['content'] for item in items]
    vectors = embeddings.embed_documents(contents)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = [
        {
            'id': f"{uid}-{item['memory_id']}",
            'values': vectors[i],
            'metadata': {
                'uid': uid,
                'memory_id': item['memory_id'],
                'category': item['category'],
                'created_at': now_ts,
            },
        }
        for i, item in enumerate(items)
    ]
    res = index.upsert(vectors=payload, namespace=MEMORIES_NAMESPACE)
    logger.info(f'upsert_memory_vectors_batch count={len(payload)} {res}')
    return len(payload)


def find_similar_memories(uid: str, content: str, threshold: float = 0.85, limit: int = 5) -> List[dict]:
    """Find memories similar to the given content."""
    if _is_qdrant():
        vector = embeddings.embed_query(content)
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        hits = _qdrant_search(_COL_MEMORIES, vector, must, limit=limit)
        results = []
        for h in hits:
            if h.score >= threshold:
                results.append(
                    {
                        'memory_id': h.payload.get('memory_id'),
                        'category': h.payload.get('category'),
                        'score': h.score,
                    }
                )
        return results

    if index is None:
        logger.warning('Pinecone index not initialized, skipping similarity search')
        return []
    vector = embeddings.embed_query(content)
    filter_data = {'uid': uid}
    xc = index.query(
        vector=vector, top_k=limit, include_metadata=True, filter=filter_data, namespace=MEMORIES_NAMESPACE
    )
    results = []
    for match in xc.get('matches', []):
        if match['score'] >= threshold:
            results.append(
                {
                    'memory_id': match['metadata'].get('memory_id'),
                    'category': match['metadata'].get('category'),
                    'score': match['score'],
                }
            )
    return results


def check_memory_duplicate(uid: str, content: str, threshold: float = 0.85) -> dict | None:
    """Check if a similar memory already exists."""
    similar = find_similar_memories(uid, content, threshold=threshold, limit=1)
    if similar:
        logger.warning(f'Found duplicate memory: {similar[0]}')
        return similar[0]
    return None


def search_memories_by_vector(uid: str, query: str, limit: int = 10) -> List[str]:
    """Semantic search for memories. Returns memory_ids ordered by relevance."""
    if _is_qdrant():
        vector = embeddings.embed_query(query)
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        hits = _qdrant_search(_COL_MEMORIES, vector, must, limit=limit)
        return [h.payload.get('memory_id') for h in hits if h.payload.get('memory_id')]

    if index is None:
        logger.warning('Pinecone index not initialized, skipping memory search')
        return []
    vector = embeddings.embed_query(query)
    filter_data = {'uid': uid}
    xc = index.query(
        vector=vector, top_k=limit, include_metadata=True, filter=filter_data, namespace=MEMORIES_NAMESPACE
    )
    return [match['metadata'].get('memory_id') for match in xc.get('matches', [])]


def delete_memory_vector(uid: str, memory_id: str):
    """Delete a memory vector."""
    if _is_qdrant():
        _qdrant_delete(_COL_MEMORIES, [f'{uid}-{memory_id}'])
        logger.info(f'qdrant delete_memory_vector uid={uid} memory={memory_id}')
        return

    if index is None:
        logger.warning('Pinecone index not initialized, skipping memory vector delete')
        return
    vector_id = f'{uid}-{memory_id}'
    result = index.delete(ids=[vector_id], namespace=MEMORIES_NAMESPACE)
    logger.info(f'delete_memory_vector {vector_id} {result}')


# ===========================================================================
# X (Twitter) Post vectors  (ns_x / omi_x_posts)
# ===========================================================================


def upsert_x_post_vectors_batch(uid: str, items: List[dict]) -> int:
    """Upsert X post embeddings. Each item: {'post_id', 'content', 'kind'}.
    Returns the number of vectors written."""
    items = [it for it in items if (it.get('content') or '').strip()]
    if not items:
        return 0

    if _is_qdrant():
        vectors = embeddings.embed_documents([it['content'] for it in items])
        now_ts = int(datetime.now(timezone.utc).timestamp())
        points = [
            PointStruct(
                id=_str_to_uuid(f'{uid}-x-{it["post_id"]}'),
                vector=vectors[i],
                payload={
                    'uid': uid,
                    'post_id': str(it['post_id']),
                    'kind': it.get('kind', 'tweet'),
                    'created_at': now_ts,
                },
            )
            for i, it in enumerate(items)
        ]
        _qdrant.upsert(collection_name=_COL_X_POSTS, points=points)
        logger.info(f'qdrant upsert_x_post_vectors_batch uid={uid} count={len(points)}')
        return len(points)

    if index is None:
        logger.warning('Pinecone index not initialized, skipping x_post vector batch upsert')
        return 0
    vectors = embeddings.embed_documents([it['content'] for it in items])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = [
        {
            'id': f"{uid}-x-{it['post_id']}",
            'values': vectors[i],
            'metadata': {
                'uid': uid,
                'post_id': str(it['post_id']),
                'kind': it.get('kind', 'tweet'),
                'created_at': now_ts,
            },
        }
        for i, it in enumerate(items)
    ]
    res = index.upsert(vectors=payload, namespace=X_POSTS_NAMESPACE)
    logger.info(f'upsert_x_post_vectors_batch count={len(payload)} {res}')
    return len(payload)


def find_similar_x_posts(uid: str, content: str, limit: int = 10) -> List[dict]:
    """Semantic search over the user's X posts. Returns [{post_id, kind, score}]."""
    if _is_qdrant():
        vector = embeddings.embed_query(content)
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        hits = _qdrant_search(_COL_X_POSTS, vector, must, limit=limit)
        return [
            {
                'post_id': h.payload.get('post_id'),
                'kind': h.payload.get('kind'),
                'score': h.score,
            }
            for h in hits
        ]

    if index is None:
        logger.warning('Pinecone index not initialized, skipping x_post similarity search')
        return []
    vector = embeddings.embed_query(content)
    xc = index.query(
        vector=vector, top_k=limit, include_metadata=True, filter={'uid': uid}, namespace=X_POSTS_NAMESPACE
    )
    return [
        {
            'post_id': m['metadata'].get('post_id'),
            'kind': m['metadata'].get('kind'),
            'score': m['score'],
        }
        for m in xc.get('matches', [])
    ]


# ===========================================================================
# Screen activity vectors  (ns3 / omi_screen_activity)
# ===========================================================================

def upsert_screen_activity_vectors(uid: str, rows: List[dict]) -> int:
    """Batch upsert screenshot embeddings."""
    if _is_qdrant():
        points = []
        for row in rows:
            embedding = row.get('embedding')
            if not embedding:
                continue
            ts = row.get('timestamp', 0)
            if isinstance(ts, str):
                ts = int(datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp())
            points.append(
                PointStruct(
                    id=_str_to_uuid(f'{uid}-sa-{row["id"]}'),
                    vector=embedding,
                    payload={
                        'uid': uid,
                        'screenshot_id': str(row['id']),
                        'timestamp': int(ts),
                        'appName': row.get('appName', ''),
                    },
                )
            )
        if not points:
            return 0
        # Qdrant recommends batches ≤ 100
        for i in range(0, len(points), 100):
            _qdrant.upsert(collection_name=_COL_SCREEN_ACTIVITY, points=points[i : i + 100])
        logger.info(f'qdrant upsert_screen_activity_vectors uid={uid} count={len(points)}')
        return len(points)

    if index is None:
        logger.warning('Pinecone index not initialized, skipping screen activity vector upsert')
        return 0
    vectors = []
    for row in rows:
        embedding = row.get('embedding')
        if not embedding:
            continue
        vectors.append(
            {
                'id': f'{uid}-sa-{row["id"]}',
                'values': embedding,
                'metadata': {
                    'uid': uid,
                    'screenshot_id': str(row['id']),
                    'timestamp': (
                        int(datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00')).timestamp())
                        if isinstance(row['timestamp'], str)
                        else int(row['timestamp'])
                    ),
                    'appName': row.get('appName', ''),
                },
            }
        )
    if not vectors:
        return 0
    upserted = 0
    for i in range(0, len(vectors), 100):
        chunk = vectors[i : i + 100]
        index.upsert(vectors=chunk, namespace=SCREEN_ACTIVITY_NAMESPACE)
        upserted += len(chunk)
    logger.info(f'upsert_screen_activity_vectors uid={uid} count={upserted}')
    return upserted


def search_screen_activity_vectors(
    uid: str,
    query_vector: List[float],
    start_date: int = None,
    end_date: int = None,
    app_filter: str = None,
    k: int = 10,
) -> List[dict]:
    """Vector search across screenshot embeddings."""
    if _is_qdrant():
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        if start_date and end_date:
            must.append(FieldCondition(key='timestamp', range=Range(gte=start_date, lte=end_date)))
        elif start_date:
            must.append(FieldCondition(key='timestamp', range=Range(gte=start_date)))
        elif end_date:
            must.append(FieldCondition(key='timestamp', range=Range(lte=end_date)))
        if app_filter:
            must.append(FieldCondition(key='appName', match=MatchValue(value=app_filter)))
        hits = _qdrant_search(_COL_SCREEN_ACTIVITY, query_vector, must, limit=k)
        return [
            {
                'screenshot_id': h.payload.get('screenshot_id'),
                'timestamp': h.payload.get('timestamp'),
                'appName': h.payload.get('appName'),
                'score': h.score,
            }
            for h in hits
        ]

    if index is None:
        logger.warning('Pinecone index not initialized, skipping screen activity search')
        return []
    filter_data = {'uid': uid}
    if start_date and end_date:
        filter_data['timestamp'] = {'$gte': start_date, '$lte': end_date}
    elif start_date:
        filter_data['timestamp'] = {'$gte': start_date}
    elif end_date:
        filter_data['timestamp'] = {'$lte': end_date}
    if app_filter:
        filter_data['appName'] = app_filter
    xc = index.query(
        vector=query_vector,
        top_k=k,
        include_metadata=True,
        filter=filter_data,
        namespace=SCREEN_ACTIVITY_NAMESPACE,
    )
    return [
        {
            'screenshot_id': match['metadata'].get('screenshot_id'),
            'timestamp': match['metadata'].get('timestamp'),
            'appName': match['metadata'].get('appName'),
            'score': match['score'],
        }
        for match in xc.get('matches', [])
    ]


def delete_screen_activity_vectors(uid: str, ids: List[int]):
    """Delete screen activity vectors by screenshot IDs."""
    if _is_qdrant():
        _qdrant_delete(_COL_SCREEN_ACTIVITY, [f'{uid}-sa-{sid}' for sid in ids])
        return
    if index is None:
        return
    vector_ids = [f'{uid}-sa-{sid}' for sid in ids]
    index.delete(ids=vector_ids, namespace=SCREEN_ACTIVITY_NAMESPACE)


# ===========================================================================
# Action item vectors  (ns4 / omi_action_items)
# ===========================================================================

def upsert_action_item_vector(uid: str, action_item_id: str, description: str):
    if _is_qdrant():
        vector = embeddings.embed_query(description)
        payload = {
            'uid': uid,
            'action_item_id': action_item_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        }
        _qdrant_upsert(_COL_ACTION_ITEMS, f'{uid}-ai-{action_item_id}', vector, payload)
        logger.info(f'qdrant upsert_action_item_vector uid={uid} ai={action_item_id}')
        return vector

    if index is None:
        logger.warning('Pinecone index not initialized, skipping action item vector upsert')
        return None
    vector = embeddings.embed_query(description)
    data = {
        'id': f'{uid}-ai-{action_item_id}',
        'values': vector,
        'metadata': {
            'uid': uid,
            'action_item_id': action_item_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        },
    }
    res = index.upsert(vectors=[data], namespace=ACTION_ITEMS_NAMESPACE)
    logger.info(f'upsert_action_item_vector {action_item_id} {res}')
    return vector


def upsert_action_item_vectors_batch(uid: str, items: List[dict]) -> int:
    if _is_qdrant():
        if not items:
            return 0
        descriptions = [item['description'] for item in items]
        vectors = embeddings.embed_documents(descriptions)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        points = [
            PointStruct(
                id=_str_to_uuid(f'{uid}-ai-{item["action_item_id"]}'),
                vector=vectors[i],
                payload={
                    'uid': uid,
                    'action_item_id': item['action_item_id'],
                    'created_at': now_ts,
                },
            )
            for i, item in enumerate(items)
        ]
        _qdrant.upsert(collection_name=_COL_ACTION_ITEMS, points=points)
        logger.info(f'qdrant upsert_action_item_vectors_batch uid={uid} count={len(points)}')
        return len(points)

    if index is None:
        logger.warning('Pinecone index not initialized, skipping action item vector batch upsert')
        return 0
    if not items:
        return 0
    descriptions = [item['description'] for item in items]
    vectors = embeddings.embed_documents(descriptions)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = [
        {
            'id': f"{uid}-ai-{item['action_item_id']}",
            'values': vectors[i],
            'metadata': {
                'uid': uid,
                'action_item_id': item['action_item_id'],
                'created_at': now_ts,
            },
        }
        for i, item in enumerate(items)
    ]
    res = index.upsert(vectors=payload, namespace=ACTION_ITEMS_NAMESPACE)
    logger.info(f'upsert_action_item_vectors_batch count={len(payload)} {res}')
    return len(payload)


def search_action_items_by_vector(uid: str, query: str, limit: int = 10, min_score: float = 0.3) -> List[str]:
    if _is_qdrant():
        vector = embeddings.embed_query(query)
        must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
        hits = _qdrant_search(_COL_ACTION_ITEMS, vector, must, limit=limit)
        top_score = hits[0].score if hits else None
        kept = [h for h in hits if h.score >= min_score]
        logger.info(
            f'qdrant search_action_items uid={uid} matches={len(hits)} kept={len(kept)} '
            f'top_score={top_score} min_score={min_score}'
        )
        return [h.payload.get('action_item_id') for h in kept if h.payload.get('action_item_id')]

    if index is None:
        logger.warning('Pinecone index not initialized, skipping action item search')
        return []
    vector = embeddings.embed_query(query)
    filter_data = {'uid': uid}
    xc = index.query(
        vector=vector, top_k=limit, include_metadata=True, filter=filter_data, namespace=ACTION_ITEMS_NAMESPACE
    )
    matches = xc.get('matches', [])
    top_score = matches[0]['score'] if matches else None
    kept = [m for m in matches if m.get('score', 0.0) >= min_score]
    logger.info(
        f'search_action_items_by_vector uid={uid} matches={len(matches)} kept={len(kept)} '
        f'top_score={top_score} min_score={min_score}'
    )
    return [m['metadata'].get('action_item_id') for m in kept]


def find_similar_action_items(uid: str, query: str, threshold: float = 0.6, limit: int = 10) -> List[dict]:
    """Find action items semantically similar to the given query text."""
    if _is_qdrant():
        try:
            vector = embeddings.embed_query(query)
            must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
            hits = _qdrant_search(_COL_ACTION_ITEMS, vector, must, limit=limit)
            kept = []
            top_score = hits[0].score if hits else None
            for h in hits:
                if h.score < threshold:
                    continue
                aid = h.payload.get('action_item_id')
                if not aid:
                    continue
                kept.append({'action_item_id': aid, 'score': h.score})
            logger.info(
                f'qdrant find_similar_action_items uid={uid} matches={len(hits)} '
                f'kept={len(kept)} top_score={top_score} threshold={threshold}'
            )
            return kept
        except Exception as e:
            logger.exception(f'find_similar_action_items failed uid={uid}: {e}')
            return []

    if index is None:
        return []
    try:
        vector = embeddings.embed_query(query)
        xc = index.query(
            vector=vector,
            top_k=limit,
            include_metadata=True,
            filter={'uid': uid},
            namespace=ACTION_ITEMS_NAMESPACE,
        )
        matches = xc.get('matches', [])
        kept = []
        dropped_no_id = 0
        for m in matches:
            if m.get('score', 0.0) < threshold:
                continue
            aid = m.get('metadata', {}).get('action_item_id')
            if not aid:
                dropped_no_id += 1
                continue
            kept.append({'action_item_id': aid, 'score': m.get('score', 0.0)})
        top_score = matches[0]['score'] if matches else None
        logger.info(
            f'find_similar_action_items uid={uid} matches={len(matches)} '
            f'kept={len(kept)} dropped_no_id={dropped_no_id} '
            f'top_score={top_score} threshold={threshold}'
        )
        return kept
    except Exception as e:
        logger.exception(f'find_similar_action_items failed uid={uid}: {e}')
        return []


def delete_action_item_vector(uid: str, action_item_id: str):
    if _is_qdrant():
        _qdrant_delete(_COL_ACTION_ITEMS, [f'{uid}-ai-{action_item_id}'])
        logger.info(f'qdrant delete_action_item_vector uid={uid} ai={action_item_id}')
        return

    if index is None:
        logger.warning('Pinecone index not initialized, skipping action item vector delete')
        return
    vector_id = f'{uid}-ai-{action_item_id}'
    result = index.delete(ids=[vector_id], namespace=ACTION_ITEMS_NAMESPACE)
    logger.info(f'delete_action_item_vector {vector_id} {result}')


def delete_action_item_vectors_batch(uid: str, action_item_ids: List[str]):
    if _is_qdrant():
        if not action_item_ids:
            return
        _qdrant_delete(_COL_ACTION_ITEMS, [f'{uid}-ai-{aid}' for aid in action_item_ids])
        logger.info(f'qdrant delete_action_item_vectors_batch uid={uid} count={len(action_item_ids)}')
        return

    if index is None:
        return
    if not action_item_ids:
        return
    vector_ids = [f'{uid}-ai-{aid}' for aid in action_item_ids]
    index.delete(ids=vector_ids, namespace=ACTION_ITEMS_NAMESPACE)
    logger.info(f'delete_action_item_vectors_batch count={len(vector_ids)}')
