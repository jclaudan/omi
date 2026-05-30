import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dependencies import get_current_user_id
from utils.oss_supabase_client import upsert_profile, get_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/oss', tags=['oss'])


class ProfileInitRequest(BaseModel):
    email: str = ''


class ProfileResponse(BaseModel):
    uid: str
    email: str
    created: bool


@router.post('/profile/init', response_model=ProfileResponse)
def init_user_profile(
    body: ProfileInitRequest,
    uid: str = Depends(get_current_user_id),
):
    """Initialize or retrieve the OSS+ user profile in Supabase.

    Called by the Flutter app immediately after Supabase sign-up or sign-in.
    The PostgreSQL trigger already creates the row on sign-up; this endpoint
    provides a belt-and-suspenders upsert and returns the profile so the app
    can confirm the user is fully initialized.
    """
    existing = get_profile(uid)
    if existing:
        return ProfileResponse(uid=uid, email=existing.get('email', body.email), created=False)

    upsert_profile(uid, body.email)
    return ProfileResponse(uid=uid, email=body.email, created=True)
