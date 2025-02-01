# Валидация данных при помощи pydantic. Т.е. тут описываются поля и их типы, по которым будет проходить сериализация и десериализация. Тут мы не создаем модели для БД.

from datetime import datetime

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    created: datetime = Field(
        default_factory=datetime.utcnow,
        alias="created_at",
        description="The creation date of the user",
    )
    changed: datetime = Field(
        default_factory=datetime.utcnow,
        alias="changed_at",
        description="The last change date of the user",
    )
    disabled: bool | None = False


class UserInDB(User):
    hashed_password: str
