from typing import Any, Optional
from pgvector.sqlalchemy import HALFVEC
from datetime import datetime
import uuid
from sqlmodel import Field, SQLModel



class Alice(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    name: Optional[str] = None
    hashed_password: Optional[str] = None
    number: Optional[int] = None
    email_adress: Optional[str] = None
    Education: Optional[str] = None
    adress: Optional[str] = None



class experience(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True)
    title: Optional[str] = None
    content: Optional[str] = None
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class project(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True)
    title: Optional[str] = None
    content: Optional[str] = None
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class documents(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: Optional[str] = None
    content: Optional[str] = None
    embedding: Optional[Any] = Field(default=None, sa_type=HALFVEC(1536))
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

