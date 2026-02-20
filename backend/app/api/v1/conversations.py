"""Conversation & message endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.deps import get_current_user
from app.db.engine import get_session
from app.db.models import Conversation, Message, User

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ── Schemas ──────────────────────────────────────────────────────


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class MessageCreate(BaseModel):
    role: str = "user"
    content: str


# ── Endpoints ────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: ConversationCreate,
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationResponse:
    """Start a new conversation."""
    conv = Conversation(user_id=current_user.id, title=body.title)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return ConversationResponse(
        id=str(conv.id),
        title=conv.title,
        created_at=conv.created_at.isoformat(),
    )


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ConversationResponse]:
    """List all conversations for the current user."""
    result = await session.exec(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())  # type: ignore[union-attr]
    )
    return [
        ConversationResponse(
            id=str(c.id),
            title=c.title,
            created_at=c.created_at.isoformat(),
        )
        for c in result.all()
    ]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[MessageResponse]:
    """Get all messages in a conversation."""
    # Verify ownership
    result = await session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_result = await session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())  # type: ignore[union-attr]
    )
    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in msg_result.all()
    ]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    """Add a message to a conversation."""
    # Verify ownership
    result = await session.exec(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg = Message(
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return MessageResponse(
        id=str(msg.id),
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at.isoformat(),
    )
