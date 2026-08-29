import uuid
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    # id:int  should be insereted in SQLModel database for users storing 
    username: str
    email: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class UserSIDB(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    Education: Optional[str] = None
    number: Optional[int] = None
    address: Optional[str] = None
    email_address: Optional[str] = None


class UserLIDB(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None


class UserDB(BaseModel):
    user_id: uuid.UUID
    name: Optional[str]
    hashed_password: Optional[str]
    phone_number: Optional[str]
    diplomas: Optional[str]
    email: Optional[str]

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    user_id: uuid.UUID
    name: Optional[str]
    phone_number: Optional[str]
    diplomas: Optional[str]
    email: Optional[str]
    model_config = {"from_attributes": True}



