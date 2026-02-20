"""Document management endpoints — upload, list, delete."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.deps import get_current_user
from app.db.engine import get_session
from app.db.models import Document, DocumentChunk, User

router = APIRouter(prefix="/documents", tags=["documents"])


# ── Schemas ──────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    uploaded_at: str
    chunk_count: int


# ── Endpoints ────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile,
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    """Upload a PDF or Markdown file.

    The file is parsed, chunked, and stored. Embedding happens here as a
    placeholder — the real embedding logic will live in Phase 3's
    ``modules.rag.ingest`` service.
    """
    if file.content_type not in (
        "application/pdf",
        "text/markdown",
        "text/plain",
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, Markdown, and plain-text files are supported",
        )

    raw_bytes = await file.read()
    text_content = _extract_text(raw_bytes, file.content_type or "text/plain")
    text_chunks = _chunk_text(text_content)

    doc = Document(
        user_id=current_user.id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )
    session.add(doc)
    await session.flush()  # get doc.id

    for idx, chunk in enumerate(text_chunks):
        session.add(
            DocumentChunk(
                document_id=doc.id,
                content=chunk,
                chunk_index=idx,
                # embedding will be filled by Phase 3 ingestion pipeline
            )
        )

    await session.commit()
    await session.refresh(doc)

    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        content_type=doc.content_type,
        uploaded_at=doc.uploaded_at.isoformat(),
        chunk_count=len(text_chunks),
    )


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[DocumentResponse]:
    """Return all documents belonging to the current user."""
    result = await session.exec(
        select(Document).where(Document.user_id == current_user.id)
    )
    docs = result.all()
    response = []
    for doc in docs:
        chunk_result = await session.exec(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        chunks = chunk_result.all()
        response.append(
            DocumentResponse(
                id=str(doc.id),
                filename=doc.filename,
                content_type=doc.content_type,
                uploaded_at=doc.uploaded_at.isoformat(),
                chunk_count=len(chunks),
            )
        )
    return response


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    session: Annotated[SQLModelAsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a document and all its chunks."""
    result = await session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.first()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # delete chunks first
    chunk_result = await session.exec(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    for chunk in chunk_result.all():
        await session.delete(chunk)

    await session.delete(doc)
    await session.commit()


# ── Private helpers ──────────────────────────────────────────────


def _extract_text(raw: bytes, content_type: str) -> str:
    """Extract plaintext from file bytes.

    Full PDF parsing via pypdf will be added in Phase 3. For now PDFs
    fall back to a basic decode attempt.
    """
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return raw.decode("utf-8", errors="replace")
    return raw.decode("utf-8", errors="replace")


def _chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[str]:
    """Split *text* into overlapping chunks of ~chunk_size words."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks
