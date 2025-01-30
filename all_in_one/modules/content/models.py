from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PhotoVideo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default=None, max_length=100)
    category: str = Field(default=None)
    photo_video_url: Optional[str] = Field(default=None, max_length=255)
    created_at: str = Field(default_factory=datetime.utcnow)
    updated_at: str = Field(default_factory=datetime.utcnow)
    likes: int = Field(default=None, ge=0)
