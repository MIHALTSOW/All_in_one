# Тут указываются зависимости нашего проекта. Т.е. будем прописывать необходимую проверку данных. Для дальнейшего использования в представлениях.


from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.dependencies import get_db
from .models import TokenForRegistrationTelegram, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


async def get_user(username: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | Literal[False]:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif data is None:
        return None
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp_access": int(expire.timestamp())})
    encoded_jwt = jwt.encode(
        to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif data is None:
        return None
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp_refresh": int(expire.timestamp())})
    encoded_jwt = jwt.encode(
        to_encode, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decoded_token(token: str) -> dict:
    try:
        decoded_token = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token
    except jwt.InvalidTokenError as invalid_token:
        raise HTTPException(
            status_code=400, detail="Invalid token"
        ) from invalid_token


def verify_refresh_token(decoded_token: dict) -> bool:
    exp_refresh = decoded_token.get("exp_refresh")
    if exp_refresh is None:
        return False
    if datetime.now(timezone.utc).timestamp() > exp_refresh:
        return False
    return True


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError):
        raise credentials_exception from None
    user = await get_user(username=username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def check_registration_token(
    registration_token: str, db: AsyncSession = Depends(get_db)
) -> str:
    search_user = await db.execute(
        select(TokenForRegistrationTelegram).where(
            TokenForRegistrationTelegram.registration_token
            == registration_token
        )
    )
    token_data = search_user.scalar_one_or_none()
    if not token_data:
        raise HTTPException(
            status_code=400, detail="Invalid registration token"
        )
    return str(token_data.registration_token)
