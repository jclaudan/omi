import logging

from fastapi import HTTPException
from firebase_admin import auth

logger = logging.getLogger(__name__)


def verify_token(id_token: str) -> str:
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']
    except Exception as e:
        logger.error(f'Error verifying Firebase ID token: {e}')
        raise HTTPException(status_code=401, detail='Invalid authentication credentials')
