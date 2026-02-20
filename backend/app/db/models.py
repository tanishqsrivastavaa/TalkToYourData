"""SQLModel table definitions for the application."""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, text
from sqlmodel import Field, Relationship, SQLModel


# ── helpers ──────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── User ─────────────────────────────────────────────────────────


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=_uuid, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=320)
    hashed_password: str
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )

    # relationships
    documents: list["Document"] = Relationship(back_populates="owner")
    conversations: list["Conversation"] = Relationship(back_populates="owner")


# ── Document & Chunks ────────────────────────────────────────────


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=_uuid, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=512)
    content_type: str = Field(max_length=128, default="application/pdf")
    uploaded_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )

    # relationships
    owner: User | None = Relationship(back_populates="documents")
    chunks: list["DocumentChunk"] = Relationship(back_populates="document")


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"

    id: uuid.UUID = Field(default_factory=_uuid, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="documents.id", index=True)
    content: str
    chunk_index: int = Field(default=0)
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(1536)),  # OpenAI text-embedding-3-small dimension
    )

    # relationships
    document: Document | None = Relationship(back_populates="chunks")


# ── Conversation & Messages ──────────────────────────────────────


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = Field(default_factory=_uuid, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(default="New Conversation", max_length=256)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )

    # relationships
    owner: User | None = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=_uuid, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column_kwargs={"server_default": text("now()")},
    )

    # relationships
    conversation: Conversation | None = Relationship(back_populates="messages")
