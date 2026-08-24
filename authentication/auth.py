from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials,HTTPBearer 
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
import jwt
from typing import Annotated
from datetime import datetime, timedelta, timezone
from Schemas.shema import User
from Secrets.variables import Settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from database.SQLModel import Alice


settings = Settings()
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
password_hash = PasswordHash((Argon2Hasher(),))
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(db: AsyncSession, name: str):
    result = await db.execute(select(Alice).where(Alice.name == name))
    user = result.scalar_one_or_none()
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("data")
    except jwt.PyJWTError:
            raise credentials_exception
    return username


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security))->str:
    token = credentials.credentials  # token from "Bearer <token>"
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    name = await payload.get("sub")
    return name


async def authenticate_user(
    name: str,
    password: str,
    db: AsyncSession
) -> str:
    # 1. Find user by name
    result = await db.execute(select(Alice).where(Alice.name == f'{name}'))
    user = result.scalar_one_or_none()
    hashed_password = user.hashed_password if user else None
    if not hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or password ❌"
        )
    try:
        is_valid = verify_password(password, hashed_password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or password ❌"
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or password ❌"
        )

    return user.user_id




