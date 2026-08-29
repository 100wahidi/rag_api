from fastapi import APIRouter, Request
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from authentication.service import get_current_user
from .schema import RAGGenerationPayload
from typing import Annotated



router = APIRouter(prefix="/rag", tags=["retrival augmented generation"])


@router.post("/rag/generation")
async def upload_file(
    generation_payload: RAGGenerationPayload,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user),
):  
    context_gen_service: Request.state.generation_model
    # since mistral llm is async, we can call it directly without blocking the event loop
    latex_cv = await context_gen_service.generate_cv(username, session, generation_payload.offer_extraction, generation_payload.best_experiences, generation_payload.best_projects)
    return {"username": username, "latex_cv": latex_cv}
