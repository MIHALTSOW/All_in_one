# Эндпоинты. Т.е. тут указывается путь для получения данных из БД. Т.е. тут мы указываем маршруты по которым фронт будет получать нужные данные.

from datetime import timedelta

import jwt
from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Request
from jwt import decode
from sqlalchemy.exc import IntegrityError

from all_in_one.modules.auth.dependencies import (
    authenticate_user,
    check_registration_token,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    refresh_access_token,
    refresh_refresh_token,
    verify_refresh_token,
)
from all_in_one.modules.auth.models import User

from ...core.config import settings
from ...core.dependencies import get_db
from ..auth.schemas import (
    Login,
    Token,
    TokenWithCookie,
    UserOutputInfo,
    UserRegistration,
    UserWithoutPassword,
)

router = APIRouter()


@router.get("/api/token")
async def get_token_info(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is missing")

    try:
        dict_from_refresh_token = decode(refresh_token)
    except jwt.ExpiredSignatureError as time_out:
        raise HTTPException(
            status_code=400, detail="Token time out"
        ) from time_out
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=400, detail="Invalid refresh token"
        ) from error
    if verify_refresh_token(refresh_token=refresh_token):
        new_access_token = create_access_token(dict_from_refresh_token)
    else:
        refresh_token = create_refresh_token(data=dict_from_refresh_token)
        new_access_token = create_access_token(data=dict_from_refresh_token)

    return {
        "success": "Token refreshed",
        "access_token": new_access_token,
        "refresh_token": refresh_token,
    }


@router.post("/api/token/", response_model=Token)
async def login_for_access_token(
    form_data: Login = Body(...), db=Depends(get_db)
) -> Token:
    user = await authenticate_user(
        db=db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password"
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAY)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/api/registration/", response_model=UserOutputInfo)
async def create_user(
    user_data: UserRegistration = Body(..., description="User data"),
    registration_token: str = Depends(check_registration_token),
    db=Depends(get_db),
):
    hash_password = get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password,
        full_name=user_data.full_name,
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Username or email already exists"
        ) from err
    return UserOutputInfo(
        success="Registration successful",
        access_token=create_access_token(data={"sub": user_data.username}),
        registration_token=registration_token,
        user_data=UserWithoutPassword.from_orm(new_user),
    )
