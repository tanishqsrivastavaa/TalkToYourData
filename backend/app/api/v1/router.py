"""API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1 import auth, conversations, documents, health, livekit_token

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(conversations.router)
router.include_router(livekit_token.router)
