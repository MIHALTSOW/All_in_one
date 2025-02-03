# Валидация данных при помощи pydantic. Т.е. тут описываются поля и их типы, по которым будет проходить сериализация и десериализация. Тут мы не создаем модели для БД.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class UserWithoutPassword(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    created_on: datetime
    updated_on: datetime
    disabled: bool | None = False


class UserSchema(UserWithoutPassword):
    hashed_password: str
