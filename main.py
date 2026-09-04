import uvicorn
import asyncio
import torch
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from modules.core.security import Settings
from modules.core.llm import AsyncGroqProvider
from modules.core.logs import setup_logger
from modules.core.dependencies import make_engine, make_sessionmaker
from modules.authentication.router import router as auth_router
from modules.extraction.router import router as extraction_router
from modules.retrieving.router import router as retrieval_router
from modules.generation.router import router as generation_router
from modules.uploading.router import router as uploading_router
from modules.injection.router import router as injection_router



settings = Settings()
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB engine/sessionmaker [async] and store in app.state
    engine = make_engine(settings.PG_DB_URL)
    app.state.async_session = make_sessionmaker(engine)
    app.state.db_engine = engine

    # 1. Optimize thread scheduling: Prevent PyTorch from spawning excess BLAS threads
    torch.set_num_threads(1)

    # 2. Allocate bounded worker pool (Single point of concurrency control)
    model_executor = ThreadPoolExecutor(
        max_workers=4, thread_name_prefix="ml-inference"
    )
    app.state.model_executor = model_executor

    # 4. Offload blocking model loading to background thread
    loop = asyncio.get_running_loop()
    embedding_model = await loop.run_in_executor(
        model_executor,
        lambda: SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2"),
    )

    app.state.embedding_model = embedding_model

     # initialize the generation service with Groq API key and model(to enhence availability)
    app.state.generation_model = AsyncGroqProvider(api_key=settings.GROQ_API_KEY)

    yield
    # shutdown[end_event]: dispose engine, stop executor, close async clients and any other resources
    await engine.dispose()
    app.state.model_executor.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
CORSMiddleware,
allow_origins=["*"], 
allow_credentials=True, # Allow credentials 
allow_methods=["*"], # Allow all HTTP methods
allow_headers=["*"], # Allow all HTTP headers
)


app.include_router(auth_router)
app.include_router(uploading_router)
app.include_router(extraction_router)
app.include_router(retrieval_router)
app.include_router(generation_router)
app.include_router(injection_router)




if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
