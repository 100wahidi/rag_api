import uvicorn
import uuid
from datetime import timedelta
from typing import Annotated
from typing import AsyncGenerator
from fastapi import Depends, FastAPI, HTTPException, status,FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.shema import Token, UserSIDB, AliceData
from Secrets.variables import Settings
from sqlmodel import select
from authentication.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password, get_current_user,)
from database.tables import Alice, documents
from database.utils import make_engine, make_sessionmaker
from sentence_transformers import SentenceTransformer
from Services.generation.schemas import ExperienceItem, RAGGenerationPayload
from Services.retrieval.retrieval_service import RetrievalService
from Services.extraction.extraction_service import ExtractionService
from Services.generation.generation_service import GenerationService
from logs import setup_logger
from concurrent.futures import ThreadPoolExecutor
import asyncio

http_bearer = HTTPBearer()
settings = Settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB engine/sessionmaker (example)
    engine = make_engine(settings.PG_DB_URL)
    app.state.async_session = make_sessionmaker(engine)
    app.state.db_engine = engine

    # create a small thread pool for blocking model ops
    app.state.model_executor = ThreadPoolExecutor(max_workers=4)
    # semaphore to limit concurrent sync model calls
    app.state.model_semaphore = asyncio.Semaphore(4)

    # Synchronous embedding model (SentenceTransformer) — load in thread to avoid blocking
    def _load_embedding_model():
        return SentenceTransformer("thenlper/gte-small")
    app.state.embedding_model = await asyncio.get_running_loop().run_in_executor(
        app.state.model_executor, _load_embedding_model
    )

         
    app.state.generation_model = GenerationService(api_key=settings.MISTRAL_API_KEY, model="mistral-large-latest")
    # optional: warm model (small call) in executor
    await asyncio.get_running_loop().run_in_executor(
        app.state.model_executor, lambda: app.state.embedding_model.encode(["warmup"])
    )

    yield
    # shutdown: dispose engine, stop executor, close async clients
    await engine.dispose()
    app.state.model_executor.shutdown(wait=True)
    # if async client: await app.state.llm.aclose()

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async_session = request.app.state.async_session
    async with async_session() as session:
        yield session

async def embed_text(request: Request, text: str) -> list[float]:
    loop = asyncio.get_running_loop()
    async with request.app.state.model_semaphore:
        return await loop.run_in_executor(
        request.app.state.model_executor,
        lambda: request.app.state.embedding_model.encode([text])[0].tolist()
        )

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
        adress=user.address,
        email_adress=user.email_address
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)


@app.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db))->Token:
    result = await db.execute(select(Alice).where(Alice.name == f'{form_data.username}'))
    user = result.scalar_one_or_none()
    hashed_password = user.hashed_password if user else None

    if not hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not found hashed"
        )
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
async def retrieve_metadata(exctaction :dict, request: Request, session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                experience_vector = await embed_text(request, str(exctaction.get("required_experiences")))
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_experiences = await RetrievalService(model="thenlper/gte-small").retrieve(username,session, experience_vector)
            return {"username": username, "best_experiences": [ExperienceItem(**exp) for exp in best_experiences]}

@app.post("/rag/retrieval/projects")
async def retrieve_projects(exctaction :dict, request: Request, session: Annotated[AsyncSession, Depends(get_db)], username: str = Depends(get_current_user)):
            try:
                project_vector = await embed_text(request, str(exctaction.get("technical_skills")))
            except Exception:
                 logger.exception("Embedding service failure")
                 raise HTTPException(status_code=503,detail="Embedding service unavailable")
                
            best_projects = await RetrievalService(model="thenlper/gte-small",target="projects").retrieve(username,session, project_vector)
            return {"username": username, "best_projects": best_projects}


@app.post("/rag/generation")
async def upload_file(
    generation_payload: RAGGenerationPayload,
    session: Annotated[AsyncSession, Depends(get_db)],
    username: str = Depends(get_current_user),
):  
    context_gen_service = GenerationService(api_key=settings.MISTRAL_API_KEY, model="mistral-large-latest")
    # since mistral llm is async, we can call it directly without blocking the event loop
    latex_cv = await context_gen_service.generate_cv(username, session, generation_payload.offer_extraction, generation_payload.best_experiences, generation_payload.best_projects)
    return {"username": username, "latex_cv": latex_cv}
    

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
