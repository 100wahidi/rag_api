from fastapi import APIRouter, Request
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from .generation import GenerationService
from .schema import RAGGenerationPayload
from typing import Annotated
from modules.core.logs import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/rag", tags=["retrival augmented generation"])

async def get_service(request:Request):
    generation_service = request.app.state.generation_model
    return generation_service

@router.post("/rag/generation")
async def upload_file(
    request: Request,
    generation_payload: RAGGenerationPayload,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user),
):  
    # Access the generation model from the FastAPI app state
    Client_llm = await get_service(request)
    # since mistral llm is async, we can call it directly without blocking the event loop
    latex_cv = await GenerationService(
        Client=Client_llm.get_llm_client(),
        model=Client_llm.handlel_llm()
    ).generate_cv(username, session, generation_payload.offer_extraction,generation_payload.best_experiences, generation_payload.best_projects)
    
    return {"username": username, "latex_cv": latex_cv}
