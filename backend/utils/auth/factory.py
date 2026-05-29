import logging
import os

logger = logging.getLogger(__name__)

_AUTH_BACKEND = os.environ.get('OMI_AUTH_BACKEND', 'firebase')

if _AUTH_BACKEND == 'supabase':
    from utils.auth.supabase_auth import verify_token
else:
    from utils.auth.firebase_auth import verify_token

__all__ = ['verify_token']
