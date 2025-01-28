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
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str
