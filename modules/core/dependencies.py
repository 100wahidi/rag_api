from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Request
from typing import AsyncGenerator
from fastapi import Request, HTTPException, status
from modules.generation.LatexCompiler import LatexCompiler


def make_engine(db_url: str):
    return create_async_engine(
        db_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        connect_args={"statement_cache_size": 0},
    )

def make_sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async_session = request.app.state.async_session
    async with async_session() as session:
        yield session


def get_compiler_engine(request: Request) -> LatexCompiler:
    """Extracts the verified LatexCompiler singleton bound to app.state during lifespan."""
    compiler: LatexCompiler | None = getattr(request.app.state, "latex_compiler", None)
    if compiler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LaTeX compiler engine is not initialized on this instance.",
        )
    return compiler