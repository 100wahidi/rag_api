from fastapi import APIRouter, Request
from fastapi import Depends, HTTPException, status
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from .retrieval import RetrievalService
from .models import Alice
from .schema import ExtractedExperience, ExtractedSkills
from typing import Annotated
from modules.core.logs import setup_logger
import asyncio

logger = setup_logger(__name__)

router = APIRouter(prefix="/rag/retrieval", tags=["retrival augmented generation"])


# 1. Optimized embedding helper
async def embed_text(request: Request, text: str) -> List[float]:
    """Generates embedding vector in a threadpool to prevent blocking the async event loop."""
    model = request.app.state.embedding_model
    executor = request.app.state.model_executor
    loop = asyncio.get_running_loop()

    # Pass string directly without batch wrapping; normalize for cosine similarity
    vector = await loop.run_in_executor(
        executor,
        lambda: model.encode(text, normalize_embeddings=True).tolist()
    )
    return vector


# 2. Optimized retrieval route
@router.post("/experiences")
async def retrieve_metadata(
    required_experiences: ExtractedExperience,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # Fast indexed user lookup with graceful 404
    user_stmt = select(Alice.user_id).where(Alice.name == username)
    user_result = await session.execute(user_stmt)
    user_id = user_result.scalar_one_or_none()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )

    try:
        experiences_string = RetrievalService(session).list_to_embedding_text(required_experiences.retrieved_experiences)      
        experience_vector = await embed_text(request, experiences_string)

    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service unavailable."
        )

    # Fast direct user_id retrieval without table joins
    best_experiences = await RetrievalService(session).retrieve_by_vector(
        user_id=user_id,
        retrieval_vector=experience_vector,
        target="experience",
        top_k=3
    )

    return {
        "username": username,
        "best_experiences": best_experiences
    }



# 2. Optimized retrieval route
@router.post("/projects")
async def retrieve_metadata(
    required_skills: ExtractedSkills,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # Fast indexed user lookup with graceful 404
    user_stmt = select(Alice.user_id).where(Alice.name == username)
    user_result = await session.execute(user_stmt)
    user_id = user_result.scalar_one_or_none()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )

    try:
        experiences_string = RetrievalService(session).list_to_embedding_text(required_skills.retrieved_skills)      
        experience_vector = await embed_text(request, experiences_string)

    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service unavailable."
        )

    # Fast direct user_id retrieval without table joins
    best_experiences = await RetrievalService(session).retrieve_by_vector(
        user_id=user_id,
        retrieval_vector=experience_vector,
        target="project",
        top_k=3
    )

    return {
        "username": username,
        "best_experiences": best_experiences
    }
