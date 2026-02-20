"""LiveKit token generation endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    room_name: str = "default-room"


class TokenResponse(BaseModel):
    token: str
    url: str


@router.post("/token", response_model=TokenResponse)
async def generate_livekit_token(
    body: TokenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> TokenResponse:
    """Generate a LiveKit participant token for the authenticated user."""
    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(str(current_user.id))
        .with_name(current_user.email)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=body.room_name,
            )
        )
    )
    return TokenResponse(
        token=token.to_jwt(),
        url=settings.livekit_url,
    )
