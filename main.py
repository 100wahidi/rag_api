import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from modules.core.logs import setup_logger
from modules.core.security import Settings
from modules.core.llm import Llm
from modules.core.dependencies import make_engine, make_sessionmaker
from modules.authentication.router import router as auth_router
from modules.extraction.router import router as extraction_router
from modules.retrieval.router import router as retrieval_router
from modules.generation.router import router as generation_router
from modules.uploading.router import router as uploading_router



settings = Settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB engine/sessionmaker [async] and store in app.state
    engine = make_engine(settings.PG_DB_URL)
    app.state.async_session = make_sessionmaker(engine)
    app.state.db_engine = engine

    # create a small thread pool for blocking model [mitigate sync model calls blocking the event loop]
    app.state.model_executor = ThreadPoolExecutor(max_workers=4)
    # semaphore to limit concurrent sync model calls
    app.state.model_semaphore = asyncio.Semaphore(4)

    # calling the model loading in a separate thread to avoid blocking the event loop 
    def _load_embedding_model():
        return SentenceTransformer("thenlper/gte-small")
    app.state.embedding_model = await asyncio.get_running_loop().run_in_executor(
        app.state.model_executor, _load_embedding_model
    )

    # initialize the generation service with Mistral API key and model(to enhence availability)
    app.state.generation_model = Llm(api_key=settings.MISTRAL_API_KEY)

    yield
    # shutdown[end_event]: dispose engine, stop executor, close async clients and any other resources
    await engine.dispose()
    app.state.model_executor.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
CORSMiddleware,
allow_origins=[settings.ORIGINS], 
allow_credentials=True, # Allow credentials 
allow_methods=["*"], # Allow all HTTP methods
allow_headers=["*"], # Allow all HTTP headers
)


app.include_router(auth_router)
app.include_router(uploading_router)
app.include_router(extraction_router)
app.include_router(retrieval_router)
app.include_router(generation_router)



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
