from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = Field(default=..., validation_alias="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", validation_alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ASYNC_DATABASE_URL: str = Field(
        default=..., validation_alias="ASYNC_DATABASE_URL"
    )
    SYNC_DATABASE_URL: str = Field(
        default=..., validation_alias="SYNC_DATABASE_URL"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
