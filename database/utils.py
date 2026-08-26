# create once at startup; SQLAlchemy 1.4+/2.0 style
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

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




