from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Request
from typing import AsyncGenerator


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

