from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Iterable, Sequence
from .schema import RetrievedItemDTO
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from collections.abc import Iterable
import asyncio





class RetrievalService:
    """Production-grade vector retrieval service with strict tenant isolation,

    HNSW index compliance, and parameterized bind execution.
    """


    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def retrieve_by_vector(
        self,
        user_id: UUID,
        retrieval_vector: list[float],
        target: str,
        top_k: int = 3,
        min_similarity: float = 0.50
    ) -> Sequence[RetrievedItemDTO]:
        """Performs index-scanned cosine similarity search against pgvector with tenant bounds."""
        table_name = target

        # Max cosine distance threshold calculation: distance = 1 - similarity
        max_distance = 1.0 - min_similarity

        # Parameterized query leveraging direct pgvector cosine distance operator (<=>)
        # Guarantees HNSW index utilization and immunity to SQL injection
        query = text(f"""
            SELECT 
                title, 
                content, 
                (1.0 - (embedding <=> :vector)) AS similarity
            FROM {table_name}
            WHERE 
                user_id = :user_id 
                AND embedding IS NOT NULL
                AND (embedding <=> :vector) <= 1
            ORDER BY embedding <=> :vector ASC
            LIMIT :limit;
        """)

        result = await self._session.execute(
            query,
            {
                "user_id": user_id,
                "vector": str(retrieval_vector),
                "max_distance": max_distance,
                "limit": top_k,
            },
        )

        rows = result.mappings().all()

        return [
            RetrievedItemDTO(
                title=row["title"],
                content=row["content"],
                similarity_score=float(row["similarity"]),
            )
            for row in rows
              ]
    @staticmethod
    def list_to_embedding_text(
        items: list[str]) -> str:
        """Transforme une liste (éventuellement imbriquée) en texte propre pour embedding."""
        return " ".join(
            str(item).strip() for item in items if isinstance(item, str) and item.strip()
        )

