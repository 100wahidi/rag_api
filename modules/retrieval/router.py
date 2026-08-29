from fastapi import APIRouter, Request
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from .retrieval import RetrievalService
from .schema import ExperienceItem
from typing import Annotated
from modules.core.logs import setup_logger
import asyncio

logger = setup_logger(__name__)

router = APIRouter(prefix="/rag", tags=["retrival augmented generation"])


# Embedding function to get embeddings 
async def embed_text(request: Request, text: str) -> list[float]:
    loop = asyncio.get_running_loop()
    async with request.app.state.model_semaphore:
        return await loop.run_in_executor(
        request.app.state.model_executor,
        lambda: request.app.state.embedding_model.encode([text])[0].tolist()
        )

 # retrieve best experiences based on the extracted 
@router.post("/rag/retrieval/experiences")
async def retrieve_metadata(exctaction :dict, request: Request, session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                experience_vector = await embed_text(request, str(exctaction.get("required_experiences")))
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_experiences = await RetrievalService(model="thenlper/gte-small",target="experience").retrieve(username,session, experience_vector)
            return {"username": username, "best_experiences": [ExperienceItem(**exp) for exp in best_experiences]}


# retrieve best projects based on the extracted :
@router.post("/rag/retrieval/projects")
async def retrieve_projects(exctaction :dict, request: Request, session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                project_vector = await embed_text(request, str(exctaction.get("technical_skills")))
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_projects = await RetrievalService(model="thenlper/gte-small",target="project").retrieve(username,session, project_vector)
            return {"username": username, "best_projects": best_projects}
