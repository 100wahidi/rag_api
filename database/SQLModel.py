from typing import Any, Optional
from sqlmodel import Field, SQLModel
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from pgvector.sqlalchemy import HALFVEC
import asyncio
from datetime import datetime

engine = create_async_engine("postgresql+asyncpg://postgres.utngtvwpmsogstpxaqyd:Ro3TG9yJ8UMPY3Zw@aws-1-eu-west-2.pooler.supabase.com:6543/postgres")

class Alice(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True)
    name:str | None 
    hashed_password:str | None 
    job:str | None 
    Educationducation:str | None
    country:str | None
    region:str | None 

class MetaData(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True)
    name:str | None 
    profiles:str | None 
    experiences:str | None 
    skills:str | None
    languages:str | None 
    education:str | None

class documents(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title:str | None 
    content:str | None 
    embedding: Optional[Any] = Field(default=None, sa_type=HALFVEC(1536))
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

