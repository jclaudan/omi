"""
Daily Summaries database module

Structure:
users/{uid}/daily_summaries/{summary_id}
    ├── id: str
    ├── date: str (YYYY-MM-DD)
    ├── created_at: timestamp
    ├── headline: str
    ├── overview: str
    ├── day_emoji: str
    ├── highlights: List[TopicHighlight]
    ├── action_items: List[ActionItemSummary]
    ├── people_mentioned: List[PersonMentioned]
    ├── memorable_moments: List[MemorabeMoment]
    ├── stats: DayStats
    ├── tomorrow_focus: str
    └── overall_sentiment: str
"""

import os
from typing import List, Optional
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore
from ._client import db
from . import redis_db

DAILY_SUMMARIES_COLLECTION = 'daily_summaries'

_SUPABASE = os.environ.get('OMI_DB_BACKEND', 'firestore').lower() == 'supabase'


def create_daily_summary(uid: str, summary_data: dict) -> str:
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import create_daily_summary as create_summary_supabase
        return create_summary_supabase(uid, summary_data)

    """
    Create a new daily summary document.

    Args:
        uid: User ID
        summary_data: Dictionary containing the summary data

    Returns:
        The summary ID
    """
    user_ref = db.collection('users').document(uid)
    summary_ref = user_ref.collection(DAILY_SUMMARIES_COLLECTION).document(summary_data['id'])
    summary_ref.set(summary_data)
    return summary_data['id']


def get_daily_summary(uid: str, summary_id: str) -> Optional[dict]:
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import get_daily_summary as get_summary_supabase
        return get_summary_supabase(uid, summary_id)

    """
    Get a single daily summary by ID.

    Args:
        uid: User ID
        summary_id: Summary document ID

    Returns:
        Summary data dict or None if not found
    """
    user_ref = db.collection('users').document(uid)
    summary_ref = user_ref.collection(DAILY_SUMMARIES_COLLECTION).document(summary_id)
    doc = summary_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def get_daily_summary_by_date(uid: str, date: str) -> Optional[dict]:
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import get_daily_summary_by_date as get_summary_by_date_supabase
        return get_summary_by_date_supabase(uid, date)

    """
    Get a daily summary by date (YYYY-MM-DD format).

    Args:
        uid: User ID
        date: Date string in YYYY-MM-DD format

    Returns:
        Summary data dict or None if not found
    """
    user_ref = db.collection('users').document(uid)
    query = user_ref.collection(DAILY_SUMMARIES_COLLECTION).where(filter=FieldFilter('date', '==', date)).limit(1)

    docs = list(query.stream())
    if docs:
        return docs[0].to_dict()
    return None


def get_daily_summaries(
    uid: str,
    limit: int = 30,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[dict]:
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import get_daily_summaries as get_summaries_supabase
        return get_summaries_supabase(uid, limit, offset, start_date, end_date)

    """
    Get list of daily summaries for a user, ordered by date descending.

    Args:
        uid: User ID
        limit: Maximum number of summaries to return
        offset: Number of summaries to skip
        start_date: Filter summaries from this date (YYYY-MM-DD)
        end_date: Filter summaries until this date (YYYY-MM-DD)

    Returns:
        List of summary data dicts
    """
    user_ref = db.collection('users').document(uid)
    query = user_ref.collection(DAILY_SUMMARIES_COLLECTION)

    if start_date:
        query = query.where(filter=FieldFilter('date', '>=', start_date))
    if end_date:
        query = query.where(filter=FieldFilter('date', '<=', end_date))

    query = query.order_by('date', direction=firestore.Query.DESCENDING)
    query = query.limit(limit).offset(offset)

    summaries = [doc.to_dict() for doc in query.stream()]
    return summaries


def delete_daily_summary(uid: str, summary_id: str) -> bool:
    """
    Delete a daily summary.

    Args:
        uid: User ID
        summary_id: Summary document ID

    Returns:
        True if deleted successfully
    """
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import delete_daily_summary as delete_summary_supabase
        result = delete_summary_supabase(uid, summary_id)
        redis_db.remove_daily_summary_to_uid(summary_id)
        return result

    user_ref = db.collection('users').document(uid)
    summary_ref = user_ref.collection(DAILY_SUMMARIES_COLLECTION).document(summary_id)
    summary_ref.delete()
    redis_db.remove_daily_summary_to_uid(summary_id)
    return True


def set_daily_summary_visibility(uid: str, summary_id: str, visibility: str):
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import set_daily_summary_visibility as set_visibility_supabase
        set_visibility_supabase(uid, summary_id, visibility)
        return

    user_ref = db.collection('users').document(uid)
    summary_ref = user_ref.collection(DAILY_SUMMARIES_COLLECTION).document(summary_id)
    summary_ref.update({'visibility': visibility})


def get_summaries_count(uid: str) -> int:
    """
    Get total count of daily summaries for a user.

    Args:
        uid: User ID

    Returns:
        Count of summaries
    """
    if _SUPABASE:
        from database.repo.supabase_daily_summaries import get_summaries_count as get_count_supabase
        return get_count_supabase(uid)

    user_ref = db.collection('users').document(uid)
    count_query = user_ref.collection(DAILY_SUMMARIES_COLLECTION).count()
    result = count_query.get()
    return result[0][0].value
