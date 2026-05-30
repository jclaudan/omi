from google.cloud.firestore_v1 import FieldFilter

import os
from ._client import db

_SUPABASE = os.environ.get('OMI_DB_BACKEND', 'firestore').lower() == 'supabase'


def create(task_data: dict):
    if _SUPABASE:
        return
    task_id = task_data['id']
    task_ref = db.collection('tasks').document(task_id)
    task_ref.set(task_data)


def update(task_id: str, task_data: dict):
    if _SUPABASE:
        return
    task_ref = db.collection('tasks').document(task_id)
    task_ref.update(task_data)


def get_task_by_action_request(action: str, request_id: str):
    if _SUPABASE:
        return None
    query = (
        db.collection('tasks')
        .where(filter=FieldFilter('action', '==', action))
        .where(filter=FieldFilter('request_id', '==', request_id))
        .limit(1)
    )
    tasks = [item.to_dict() for item in query.stream()]
    if len(tasks) > 0:
        return tasks[0]

    return None
