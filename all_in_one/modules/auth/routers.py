# Эндпоинты. Т.е. тут указывается путь для получения данных из БД. Т.е. тут мы указываем маршруты по которым фронт будет получать нужные данные.

from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from all_in_one.modules.auth.dependencies import (
    authenticate_user,
    check_registration_token,
    create_access_token,
    create_dict_for_token_user,
    create_refresh_token,
    decoded_token,
    get_password_hash,
    get_user,
    verify_refresh_token,
)
from all_in_one.modules.auth.models import TokenForRegistrationTelegram, User

from ...core.config import settings
from ...core.dependencies import get_db
from ..auth.schemas import (
    CheckStatus,
    Login,
    Token,
    UserOutputInfo,
    UserRegistration,
    UserWithoutPassword,
)

router = APIRouter()


@router.get("/api/token/", response_model=UserOutputInfo)
async def get_token_info(request: Request, db=Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is missing")

    decoded_refresh_token = decoded_token(token=refresh_token)
    token_check = verify_refresh_token(decoded_token=decoded_refresh_token)

    if token_check is False:
        new_refresh_token = create_refresh_token(decoded_refresh_token)
        new_access_token = create_access_token(decoded_refresh_token)
    else:
        new_access_token = create_access_token(decoded_refresh_token)
        new_refresh_token = refresh_token

    username = decoded_refresh_token.get("sub")

    if username is None:
        raise HTTPException(
            status_code=400, detail="User not found in the token"
        )

    user_info = await get_user(username=username, db=db)
    user_data = jsonable_encoder(UserWithoutPassword.model_validate(user_info))

    response = JSONResponse(
        content={
            "success": "Token refreshed",
            "access_token": new_access_token,
            "user_data": user_data,
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return response


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
        await (
            db.query(TokenForRegistrationTelegram)
            .filter(
                TokenForRegistrationTelegram.registration_token
                == registration_token
            )
            .delete()
        )
        await db.commit()

    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Username or email already exists"
        ) from err
    return UserOutputInfo(
        success="Registration successful",
        access_token=create_access_token(data={"sub": user_data.username}),
        user_data=UserWithoutPassword.from_orm(new_user),
    )


@router.post("/api/login/", response_model=UserOutputInfo)
async def login(user: Login = Body(...), db: AsyncSession = Depends(get_db)):
    await authenticate_user(
        db=db, username=user.username, password=user.password
    )
    user_info = await get_user(username=user.username, db=db)
    user_data = jsonable_encoder(UserWithoutPassword.model_validate(user_info))

    code_token = create_dict_for_token_user(username=user.username)

    new_refresh_token = create_refresh_token(data=code_token)
    new_access_token = create_access_token(data=code_token)

    response = JSONResponse(
        content={
            "success": "Login successful",
            "access_token": new_access_token,
            "user_data": user_data,
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return response


@router.post("/api/logout/", response_model=CheckStatus)
def logout(request: Request):
    response = JSONResponse(content={"success": "Logout successful"})
    response.delete_cookie(key="refresh_token")
    return response
