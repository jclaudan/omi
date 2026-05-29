import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import List

from utils.llm.clients import embeddings
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
import logging

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 3072

_COL_CONVERSATIONS = 'omi_conversations'
_COL_MEMORIES = 'omi_memories'
_COL_SCREEN_ACTIVITY = 'omi_screen_activity'
_COL_ACTION_ITEMS = 'omi_action_items'
_COL_X_POSTS = 'omi_x_posts'

_qdrant = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY') or None,
    timeout=30,
)


def _str_to_uuid(s: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


def _ensure_collection(name: str) -> None:
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


def _qdrant_upsert(collection: str, point_id: str, vector: List[float], payload: dict) -> None:
    _qdrant.upsert(
        collection_name=collection,
        points=[PointStruct(id=_str_to_uuid(point_id), vector=vector, payload=payload)],
    )


def _qdrant_search(collection: str, vector: List[float], must_filters: list, limit: int, with_payload: bool = True) -> list:
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
# Conversation vectors
# ===========================================================================

def upsert_vector(uid: str, conversation_id: str, vector: List[float]):
    payload = {'uid': uid, 'memory_id': conversation_id, 'created_at': int(datetime.now(timezone.utc).timestamp())}
    _qdrant_upsert(_COL_CONVERSATIONS, f'{uid}-{conversation_id}', vector, payload)
    logger.info(f'qdrant upsert_vector uid={uid} conv={conversation_id}')


def upsert_vector2(uid: str, conversation_id: str, vector: List[float], metadata: dict):
    payload = {'uid': uid, 'memory_id': conversation_id, 'created_at': int(datetime.now(timezone.utc).timestamp())}
    payload.update(metadata)
    _qdrant_upsert(_COL_CONVERSATIONS, f'{uid}-{conversation_id}', vector, payload)


def update_vector_metadata(uid: str, conversation_id: str, metadata: dict):
    payload = dict(metadata)
    payload['uid'] = uid
    payload['memory_id'] = conversation_id
    _qdrant.set_payload(
        collection_name=_COL_CONVERSATIONS,
        payload=payload,
        points=[_str_to_uuid(f'{uid}-{conversation_id}')],
    )


def upsert_vectors(uid: str, vectors: List[List[float]], conversation_ids: List[str]):
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


def query_vectors(query: str, uid: str, starts_at: int = None, ends_at: int = None, k: int = 5) -> List[str]:
    xq = embeddings.embed_query(query)
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    if starts_at is not None:
        must.append(FieldCondition(key='created_at', range=Range(gte=starts_at, lte=ends_at)))
    hits = _qdrant_search(_COL_CONVERSATIONS, xq, must, limit=k, with_payload=True)
    return [h.payload.get('memory_id') for h in hits if h.payload.get('memory_id')]


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
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    should = []
    if people:
        should.append(FieldCondition(key='people', match=MatchAny(any=people)))
    if topics:
        should.append(FieldCondition(key='topics', match=MatchAny(any=topics)))
    if entities:
        should.append(FieldCondition(key='entities', match=MatchAny(any=entities)))
    if dates_filter and len(dates_filter) == 2 and dates_filter[0] and dates_filter[1]:
        must.append(FieldCondition(
            key='created_at',
            range=Range(gte=int(dates_filter[0].timestamp()), lte=int(dates_filter[1].timestamp())),
        ))
    f = Filter(must=must, should=should if should else None)
    hits = _qdrant.search(collection_name=_COL_CONVERSATIONS, query_vector=vector, query_filter=f, limit=1000, with_payload=True)
    if not hits:
        hits = _qdrant.search(collection_name=_COL_CONVERSATIONS, query_vector=vector, query_filter=Filter(must=must), limit=20, with_payload=True)

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


def delete_vector(uid: str, conversation_id: str):
    _qdrant_delete(_COL_CONVERSATIONS, [f'{uid}-{conversation_id}'])
    logger.info(f'qdrant delete_vector uid={uid} conv={conversation_id}')


# ===========================================================================
# Memory vectors
# ===========================================================================

def upsert_memory_vector(uid: str, memory_id: str, content: str, category: str):
    vector = embeddings.embed_query(content)
    payload = {'uid': uid, 'memory_id': memory_id, 'category': category, 'created_at': int(datetime.now(timezone.utc).timestamp())}
    _qdrant_upsert(_COL_MEMORIES, f'{uid}-{memory_id}', vector, payload)
    logger.info(f'qdrant upsert_memory_vector uid={uid} memory={memory_id}')
    return vector


def upsert_memory_vectors_batch(uid: str, items: List[dict]) -> int:
    if not items:
        return 0
    vectors = embeddings.embed_documents([item['content'] for item in items])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    points = [
        PointStruct(
            id=_str_to_uuid(f'{uid}-{item["memory_id"]}'),
            vector=vectors[i],
            payload={'uid': uid, 'memory_id': item['memory_id'], 'category': item['category'], 'created_at': now_ts},
        )
        for i, item in enumerate(items)
    ]
    _qdrant.upsert(collection_name=_COL_MEMORIES, points=points)
    logger.info(f'qdrant upsert_memory_vectors_batch uid={uid} count={len(points)}')
    return len(points)


def find_similar_memories(uid: str, content: str, threshold: float = 0.85, limit: int = 5) -> List[dict]:
    vector = embeddings.embed_query(content)
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    hits = _qdrant_search(_COL_MEMORIES, vector, must, limit=limit)
    return [
        {'memory_id': h.payload.get('memory_id'), 'category': h.payload.get('category'), 'score': h.score}
        for h in hits if h.score >= threshold
    ]


def check_memory_duplicate(uid: str, content: str, threshold: float = 0.85) -> dict | None:
    similar = find_similar_memories(uid, content, threshold=threshold, limit=1)
    if similar:
        logger.warning(f'Found duplicate memory: {similar[0]}')
        return similar[0]
    return None


def search_memories_by_vector(uid: str, query: str, limit: int = 10) -> List[str]:
    vector = embeddings.embed_query(query)
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    hits = _qdrant_search(_COL_MEMORIES, vector, must, limit=limit)
    return [h.payload.get('memory_id') for h in hits if h.payload.get('memory_id')]


def delete_memory_vector(uid: str, memory_id: str):
    _qdrant_delete(_COL_MEMORIES, [f'{uid}-{memory_id}'])
    logger.info(f'qdrant delete_memory_vector uid={uid} memory={memory_id}')


# ===========================================================================
# X post vectors
# ===========================================================================

def upsert_x_post_vectors_batch(uid: str, items: List[dict]) -> int:
    items = [it for it in items if (it.get('content') or '').strip()]
    if not items:
        return 0
    vectors = embeddings.embed_documents([it['content'] for it in items])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    points = [
        PointStruct(
            id=_str_to_uuid(f'{uid}-x-{it["post_id"]}'),
            vector=vectors[i],
            payload={'uid': uid, 'post_id': str(it['post_id']), 'kind': it.get('kind', 'tweet'), 'created_at': now_ts},
        )
        for i, it in enumerate(items)
    ]
    _qdrant.upsert(collection_name=_COL_X_POSTS, points=points)
    logger.info(f'qdrant upsert_x_post_vectors_batch uid={uid} count={len(points)}')
    return len(points)


def find_similar_x_posts(uid: str, content: str, limit: int = 10) -> List[dict]:
    vector = embeddings.embed_query(content)
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    hits = _qdrant_search(_COL_X_POSTS, vector, must, limit=limit)
    return [{'post_id': h.payload.get('post_id'), 'kind': h.payload.get('kind'), 'score': h.score} for h in hits]


# ===========================================================================
# Screen activity vectors
# ===========================================================================

def upsert_screen_activity_vectors(uid: str, rows: List[dict]) -> int:
    points = []
    for row in rows:
        embedding = row.get('embedding')
        if not embedding:
            continue
        ts = row.get('timestamp', 0)
        if isinstance(ts, str):
            ts = int(datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp())
        points.append(PointStruct(
            id=_str_to_uuid(f'{uid}-sa-{row["id"]}'),
            vector=embedding,
            payload={'uid': uid, 'screenshot_id': str(row['id']), 'timestamp': int(ts), 'appName': row.get('appName', '')},
        ))
    if not points:
        return 0
    for i in range(0, len(points), 100):
        _qdrant.upsert(collection_name=_COL_SCREEN_ACTIVITY, points=points[i:i + 100])
    logger.info(f'qdrant upsert_screen_activity_vectors uid={uid} count={len(points)}')
    return len(points)


def search_screen_activity_vectors(uid: str, query_vector: List[float], start_date: int = None, end_date: int = None, app_filter: str = None, k: int = 10) -> List[dict]:
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
        {'screenshot_id': h.payload.get('screenshot_id'), 'timestamp': h.payload.get('timestamp'), 'appName': h.payload.get('appName'), 'score': h.score}
        for h in hits
    ]


def delete_screen_activity_vectors(uid: str, ids: List[int]):
    _qdrant_delete(_COL_SCREEN_ACTIVITY, [f'{uid}-sa-{sid}' for sid in ids])


# ===========================================================================
# Action item vectors
# ===========================================================================

def upsert_action_item_vector(uid: str, action_item_id: str, description: str):
    vector = embeddings.embed_query(description)
    payload = {'uid': uid, 'action_item_id': action_item_id, 'created_at': int(datetime.now(timezone.utc).timestamp())}
    _qdrant_upsert(_COL_ACTION_ITEMS, f'{uid}-ai-{action_item_id}', vector, payload)
    logger.info(f'qdrant upsert_action_item_vector uid={uid} ai={action_item_id}')
    return vector


def upsert_action_item_vectors_batch(uid: str, items: List[dict]) -> int:
    if not items:
        return 0
    vectors = embeddings.embed_documents([item['description'] for item in items])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    points = [
        PointStruct(
            id=_str_to_uuid(f'{uid}-ai-{item["action_item_id"]}'),
            vector=vectors[i],
            payload={'uid': uid, 'action_item_id': item['action_item_id'], 'created_at': now_ts},
        )
        for i, item in enumerate(items)
    ]
    _qdrant.upsert(collection_name=_COL_ACTION_ITEMS, points=points)
    logger.info(f'qdrant upsert_action_item_vectors_batch uid={uid} count={len(points)}')
    return len(points)


def search_action_items_by_vector(uid: str, query: str, limit: int = 10, min_score: float = 0.3) -> List[str]:
    vector = embeddings.embed_query(query)
    must = [FieldCondition(key='uid', match=MatchValue(value=uid))]
    hits = _qdrant_search(_COL_ACTION_ITEMS, vector, must, limit=limit)
    top_score = hits[0].score if hits else None
    kept = [h for h in hits if h.score >= min_score]
    logger.info(f'qdrant search_action_items uid={uid} matches={len(hits)} kept={len(kept)} top_score={top_score} min_score={min_score}')
    return [h.payload.get('action_item_id') for h in kept if h.payload.get('action_item_id')]


def find_similar_action_items(uid: str, query: str, threshold: float = 0.6, limit: int = 10) -> List[dict]:
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
            if aid:
                kept.append({'action_item_id': aid, 'score': h.score})
        logger.info(f'qdrant find_similar_action_items uid={uid} matches={len(hits)} kept={len(kept)} top_score={top_score} threshold={threshold}')
        return kept
    except Exception as e:
        logger.exception(f'find_similar_action_items failed uid={uid}: {e}')
        return []


def delete_action_item_vector(uid: str, action_item_id: str):
    _qdrant_delete(_COL_ACTION_ITEMS, [f'{uid}-ai-{action_item_id}'])
    logger.info(f'qdrant delete_action_item_vector uid={uid} ai={action_item_id}')


def delete_action_item_vectors_batch(uid: str, action_item_ids: List[str]):
    if not action_item_ids:
        return
    _qdrant_delete(_COL_ACTION_ITEMS, [f'{uid}-ai-{aid}' for aid in action_item_ids])
    logger.info(f'qdrant delete_action_item_vectors_batch uid={uid} count={len(action_item_ids)}')
