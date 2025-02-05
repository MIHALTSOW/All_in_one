# Эндпоинты. Т.е. тут указывается путь для получения данных из БД. Т.е. тут мы указываем маршруты по которым фронт будет получать нужные данные.

from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from all_in_one.modules.auth.dependencies import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
)

from ...core.config import settings
from ...core.dependencies import get_db
from ..auth.schemas import (
    Token,
    UserOutputInfo,
    UserRegistration,
    UserWithoutPassword,
)

router = APIRouter()


@router.post("/api/token/", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)
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
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=refresh_token_expires,
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.put("/api/registration/", response_model=UserOutputInfo)
async def change_user_info(
    user_data: UserRegistration = Body(..., description="Change user data"),
):
    

