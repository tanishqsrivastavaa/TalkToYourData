"""RAG service for retrieving relevant document context."""

import uuid
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.config import settings
from app.db.models import DocumentChunk


class RAGService:
    """Service for performing RAG retrieval using pgvector."""

    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for the given text using OpenAI."""
        response = await self.openai.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def retrieve_context(
        self,
        session: SQLModelAsyncSession,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.7,
    ) -> tuple[str, int]:
        """
        Retrieve relevant document chunks using vector similarity search.

        Args:
            session: Database session
            user_id: User ID to scope the search
            query: User's query text
            top_k: Number of top results to return
            similarity_threshold: Minimum cosine similarity (0-1)

        Returns:
            Tuple of (concatenated context string, number of chunks found)
        """
        # Generate embedding for the query
        query_embedding = await self.generate_embedding(query)

        # Perform vector similarity search using pgvector
        # Using cosine similarity: 1 - (embedding <=> query_embedding)
        sql = text("""
            SELECT 
                dc.content,
                dc.chunk_index,
                d.filename,
                1 - (dc.embedding <=> :query_embedding::vector) as similarity
            FROM document_chunks dc
            INNER JOIN documents d ON dc.document_id = d.id
            WHERE d.user_id = :user_id
                AND dc.embedding IS NOT NULL
                AND 1 - (dc.embedding <=> :query_embedding::vector) >= :threshold
            ORDER BY similarity DESC
            LIMIT :top_k
        """)

        result = await session.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "user_id": str(user_id),
                "threshold": similarity_threshold,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()

        if not rows:
            return "", 0

        # Format the context
        context_parts = []
        for row in rows:
            content, chunk_index, filename, similarity = row
            context_parts.append(
                f"[From {filename}, chunk {chunk_index}, similarity: {similarity:.2f}]\n{content}"
            )

        context = "\n\n---\n\n".join(context_parts)
        return context, len(rows)


# Singleton instance
rag_service = RAGService()
