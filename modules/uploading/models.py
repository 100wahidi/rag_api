from typing import Optional
import uuid
from sqlmodel import Field, SQLModel
from datetime import datetime


class experience(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    title: Optional[str] = None
    content: Optional[str] = None
    # embedding default value is Null
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class project(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    title: Optional[str] = None
    content: Optional[str] = None
    # embedding as Null 
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, foreign_key="alice.user_id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class Alice(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} # < new
    user_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    name: Optional[str] = None
    hashed_password: Optional[str] = None
    number: Optional[int] = None
    email_adress: Optional[str] = None
    Education: Optional[str] = None
    adress: Optional[str] = None