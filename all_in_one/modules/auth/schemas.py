# Валидация данных при помощи pydantic. Т.е. тут описываются поля и их типы, по которым будет проходить сериализация и десериализация. Тут мы не создаем модели для БД.

from datetime import datetime

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class UserWithoutPassword(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    created_on: datetime
    updated_on: datetime
    disabled: bool | None = False

    class Config:
        from_attributes = True


class UserSchema(UserWithoutPassword):
    hashed_password: str


class UserOutputInfo(BaseModel):
    success: str
    access_token: str
    user_data: UserWithoutPassword


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str


class Refresh_profile(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    hashed_password: str | None = None


class CheckStatus(BaseModel):
    status: str


class Login(BaseModel):
    username: str
    password: str


class RegistrationToken(BaseModel):
    registration_token: str


class TokenWithCookie(BaseModel):
    success: str
    access_token: str
    refresh_token: str
    user_data: UserWithoutPassword
