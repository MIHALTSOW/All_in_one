from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int
    username: str


class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    created: datetime = datetime.utcnow()
    changed: datetime = datetime.utcnow()
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str
