# Эндпоинты. Т.е. тут указывается путь для получения данных из БД. Т.е. тут мы указываем маршруты по которым фронт будет получать нужные данные.


from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from all_in_one.core.security import oauth2_scheme
from all_in_one.modules.auth.dependencies import (
    authenticate_user,
    check_registration_token,
    create_access_token,
    create_dict_for_token_user,
    create_refresh_token,
    decoded_token,
    get_current_active_user,
    get_password_hash,
    get_user,
    is_token_revoked,
    verify_refresh_token,
)
from all_in_one.modules.auth.models import TokenForRegistrationTelegram, User

from ...core.dependencies import get_db
from ..auth.schemas import (
    CheckStatus,
    Login,
    Refresh_profile,
    Token,
    UserOutputInfo,
    UserRegistration,
    UserWithoutPassword,
)

router = APIRouter()


@router.get(
    "/api/token/",
    tags=["OAuth2"],
    name="Обновление токенов в реальном времени",
    description="По запросу с фронта получаем refresh token, проверяем его на действительность, если надо обновляем и возвращаем новый refresh и access токены, если refresh еще действителен, возвращаем его и дополнительно обновленный access токен, также будет возвращена вся информация по пользователю. Этот запрос нужен для обновления в реальном времени токенов пользователя. Refresh возвращаем в cookies.",
    response_model=UserOutputInfo,
)
async def refresh_token(request: Request, db=Depends(get_db)):
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


@router.post(
    "/token",
    tags=["OAuth2"],
    name="token for oauth2_scheme",
    description="Получение токена для корректной работы oauth2_scheme. Нужно для корректной проверки авторизации пользователя на сайте.",
    response_model=Token,
)
async def get_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)
) -> Token:
    user = await authenticate_user(
        db=db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/api/registration/",
    tags=["OAuth2"],
    name="Регистрация пользователя на сайте",
    description="Чтобы получить доступ к этой ссылке пользователю нужно получить ключ в telegram боте. Далее он получит ссылку на регистрацию. Затем будет проверка данного токена, если все хорошо, то пользователю будет доступна регистрация. Если он заполнит все необходимые поля и завершит регистрацию, то telegram токен будет автоматически удален из системы.",
    response_model=UserOutputInfo,
)
async def registration(
    user_data: UserRegistration = Body(..., description="User data"),
    registration_token: str = Query(..., description="Registration token"),
    db=Depends(get_db),
):
    hash_password = get_password_hash(user_data.password)

    if check_registration_token(registration_token, db):
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


@router.put(
    "/api/refresh-profile/",
    tags=["OAuth2"],
    name="Обновление профиля пользователя",
    description="По тем данным, которые введет пользователь будет проходить обновление полей его профиля. Если пользователь не хочет обновлять какое-либо поле, он просто не указывает его, т.е. вычеркиваем ключ и значение из request body. Все обновленные данные будут сохранены в БД.",
    response_model=UserWithoutPassword,
)
async def refresh_profile(
    user: User = Depends(get_current_active_user),
    refresh_field: Refresh_profile = Body(None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_field is None:
        return UserWithoutPassword.from_orm(user)

    if refresh_field.email:
        existing_user = await db.execute(
            select(User).filter(User.email == refresh_field.email)
        )
        if existing_user.scalar():
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = refresh_field.email

    if refresh_field.full_name:
        user.full_name = refresh_field.full_name

    if refresh_field.hashed_password:
        user.hashed_password = get_password_hash(refresh_field.hashed_password)

    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Uncorrect data") from err

    return UserWithoutPassword.from_orm(user)


@router.post(
    "/api/login/",
    tags=["OAuth2"],
    name="Логин пользователя на сайте",
    description="Авторизация пользователя на сайте",
    response_model=UserOutputInfo,
)
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


@router.post(
    "/api/logout/",
    tags=["OAuth2"],
    name="Выход пользователя с сайта",
    description="После выхода пользователя помещаем его токен в черный список, чтобы нельзя было повторно авторизоваться под тем же token. Пользователю придется заново заходить и получать новый токен.",
    response_model=CheckStatus,
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    token = request.headers.get("Authorization")

    if token:
        token_without_bearer = token.replace("Bearer ", "")
        await is_token_revoked(token=token_without_bearer, db=db)

    response = JSONResponse(content={"success": "Logout successful"})
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="strict"
    )
    return response
