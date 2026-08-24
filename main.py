import uvicorn
import uuid
from datetime import timedelta
from typing import Any, Annotated, Dict
from sentence_transformers import SentenceTransformer
from fastapi import Depends, FastAPI, HTTPException, status,FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select, SQLModel, text
from authentication.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    )
from database.SQLModel import Alice, documents
from Schemas.shema import Token, UserSIDB, AliceData
from Secrets.variables import Settings
from Services.generation.pdf_compiler import ExperienceItem
from Services.retrieval.retrieval_service import RetrievalService
from Services.extraction.extraction_service import ExtractionService
from Services.parsing.parsing_service import EmbeddingService
from Services.generation.generation_service import GenerationService
from logs import setup_logger



app = FastAPI()
http_bearer = HTTPBearer()
settings = Settings()
logger = setup_logger()

engine = create_async_engine(
    settings.PG_DB_URL,
    connect_args={"statement_cache_size": 0}
)    

@asynccontextmanager
async def lifespan(app):
    app.state.embedding_model = SentenceTransformer("thenlper/gte-small")
    yield


async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        logger.info("strating connection to the database")
        yield session
        logger.info("ending connection to database ")
    await session.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
CORSMiddleware,
allow_origins=[settings.ORIGINS], # List of allowed origins
allow_credentials=True, # Allow credentials such as cookies and authorization headers
allow_methods=["*"], # Allow all HTTP methods
allow_headers=["*"], # Allow all HTTP headers
)
       

@app.post("/sign_in")
async def create_user(user: UserSIDB, session: Annotated[AsyncSession, Depends(get_db)]):
    db_user = Alice(
        user_id=uuid.uuid4(),
        name=user.name,
        hashed_password=get_password_hash(user.password),
        Education=user.Education,
        number=user.number,
        address=user.address,
        email_address=user.email_address,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
    
@app.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db))->Token:
    result = await db.execute(select(Alice).where(Alice.name == f'{form_data.username}'))
    user = result.scalar_one_or_none()
    print(user)
    hashed_password = user.hashed_password if user else None

    if not hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not found hashed"
        )
    print(hashed_password, form_data.password)
    is_valid = verify_password(form_data.password, hashed_password)
    if is_valid:
        token = create_access_token({"data":user.name},timedelta(ACCESS_TOKEN_EXPIRE_MINUTES))

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or password 1"
        )
    return Token(access_token=token, token_type="bearer")
 

@app.post("/register_user_metadata")
async def register(metadata :AliceData,  session :Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
    user_db = await session.execute(select(Alice.user_id).where(Alice.name == username))
    user_id = user_db.scalar_one_or_none()
    user_metadata = documents(title=metadata.name, content=metadata.experiences, embedding=None, created_at=None, user_id=user_id)
    session.add(user_metadata)    
    await session.commit()
    await session.refresh(user_metadata)
    return user_metadata
             
      
@app.post("/rag/extraction")
async def process_offer(offer_passage: str, username: str = Depends(get_current_user)):

    try:
        text_extraction = ExtractionService(api_key=settings.MISTRAL_API_KEY).extract(offer_passage)
    except Exception:
        logger.exception("Offer parsing failure")
        raise HTTPException(status_code=503,detail="Parser unavailable")

    if not text_extraction:
        raise HTTPException(status_code=400,detail="Unable to parse offer")
    logger.info("Offer successfully parsed user=%s",username)
    return {"username": username,"offer_key_insights": text_extraction}


@app.post("/rag/retrieval/experiences")
async def retrieve_metadata(exctaction :dict,session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                experience_vector = await EmbeddingService().embed(str(exctaction.get("required_experiences")))
                print(experience_vector)
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_experiences = await RetrievalService(model="thenlper/gte-small").retrieve(username,session, experience_vector)
            print(best_experiences)
            return {"username": username, "best_experiences": [ExperienceItem(**exp) for exp in best_experiences]}

@app.post("/rag/retrieval/projects")
async def retrieve_projects(exctaction :dict,session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                project_vector = await EmbeddingService().embed(str(exctaction.get("skills"))+","+
                                                                str(exctaction.get("required_experiences")))
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_projects = await RetrievalService(model="thenlper/gte-small",target="projects").retrieve(username,session, project_vector)
            return {"username": username, "best_projects": best_projects}


@app.post("/rag/generation")
async def upload_file(
    offer_extraction: dict[str, Any],
    best_experiences: Dict,
    best_projects: Dict,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user),
):
    latex_cv = await GenerationService(
        api_key=settings.MISTRAL_API_KEY,
        model="mistral-large-latest",
    ).generate_cv(username, session, offer_extraction, best_experiences, best_projects)
    print(latex_cv)



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
