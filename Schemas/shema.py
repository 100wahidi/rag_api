from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str="bear token"


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    # id:int  should be insereted in SQLModel database for users storing 
    username: str
    email: str | None = None
    role: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class UserSIDB(BaseModel):
    name: str | None = None
    password: str | None = None
    Education: str | None = None
    number: str | None = None
    address: str | None = None
    email_address: str | None = None

class UserLIDB(BaseModel):
    name: str | None = None
    password: str | None = None

class AliceData(BaseModel):
    name:str | None 
    profiles:str | None 
    experiences:str | None 
    skills:str | None
    languages:str | None 
    education:str | None


