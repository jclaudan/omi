import logging
import os

import jwt
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET', '')


def verify_token(id_token: str) -> str:
    if not _SUPABASE_JWT_SECRET:
        logger.error('SUPABASE_JWT_SECRET not configured')
        raise HTTPException(status_code=500, detail='Supabase auth not configured')
    try:
        decoded = jwt.decode(
            id_token,
            _SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience='authenticated',
        )
        uid = decoded.get('sub')
        if not uid:
            raise ValueError('No sub in Supabase JWT')
        return uid
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except (jwt.InvalidTokenError, ValueError) as e:
        logger.error(f'Error verifying Supabase JWT: {e}')
        raise HTTPException(status_code=401, detail='Invalid authentication credentials')
