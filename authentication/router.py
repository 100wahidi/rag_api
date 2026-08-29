from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Alice
from core.dependencies import get_db
from authentication.service import (ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, verify_password)
from .schema import UserSIDB, Token
from typing import Annotated
from datetime import timedelta
import uuid


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/sign_in")
async def create_user(user: UserSIDB, session: Annotated[AsyncSession, Depends(get_db)]):
    db_user = Alice(
        user_id=uuid.uuid4(),
        name=user.name,
        hashed_password=get_password_hash(user.password),
        Education=user.Education,
        number=user.number,
        adress=user.address,
        email_adress=user.email_address
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db))->Token:
    result = await db.execute(select(Alice).where(Alice.name == f'{form_data.username}'))
    user = result.scalar_one_or_none()
    hashed_password = user.hashed_password if user else None

    if not hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not found hashed"
        )
    is_valid = verify_password(form_data.password, hashed_password)
    if is_valid:
        token = create_access_token({"data":user.name},timedelta(ACCESS_TOKEN_EXPIRE_MINUTES))

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid name or password 1"
        )
    return Token(access_token=token, token_type="bearer")
 