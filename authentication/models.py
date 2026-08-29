from typing import Optional
import uuid
from sqlmodel import Field, SQLModel



class Alice(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} # < new
    user_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    name: Optional[str] = None
    hashed_password: Optional[str] = None
    number: Optional[int] = None
    email_adress: Optional[str] = None
    Education: Optional[str] = None
    adress: Optional[str] = None
