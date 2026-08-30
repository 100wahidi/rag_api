from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, insert
from modules.core.dependencies import get_db
from modules.authentication.service import get_current_user
from .schema import RetrievedProjects, RetrievedExperiences
from modules.core.database import Alice, experience, project
from typing import Annotated
from modules.core.logs import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/uploading", tags=["uploading projects and experiences"])


@router.post("/add_project")
async def register(user_projects :RetrievedProjects,  session :Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
    # get current user_id
    user = await session.execute(select(Alice).where(Alice.name == username))
    user_id = user.scalar_one().user_id
    records = [project(id=uuid4(), title=user_project.title, content=user_project.content,user_id=user_id).model_dump() for user_project in user_projects.projects]
    # iserting projects into the database with the current user_id
    stat = insert(project)
    await session.execute(stat,records)    
    await session.commit()
    logger.info("Projects added successfully")

@router.post("/add_experience")
async def register(user_experiences :RetrievedExperiences,  session :Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
    # get current user_id
    user = await session.execute(select(Alice).where(Alice.name == username))
    user_id = user.scalar_one().user_id
    # inserting experiences into the database with the current user_id
    stat = insert(experience)
    await session.execute(stat,[experience(id=uuid4(), title=user_experience.title, content=user_experience.content, embedding=None, created_at=None, user_id=user_id).model_dump() for user_experience in user_experiences.experiences])    
    await session.commit()